"""Filesystem storage for development and tests.

Signed URLs point back at the API (`/media/{token}` and
`/storage/uploads/{uploadId}/parts/{n}`), which verifies the HMAC before
serving or accepting bytes — the browser flow is identical to S3's.
"""

from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path
from urllib.parse import quote

from videodna.storage.base import PartInfo, StorageBackend, validate_key
from videodna.storage.signing import sign


class LocalStorage(StorageBackend):
    name = "local"

    def __init__(self, root: Path, public_base_url: str, secret: str) -> None:
        self.root = root.resolve()
        self.public_base_url = public_base_url.rstrip("/")
        self._secret = secret

    def ensure_ready(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / ".multipart").mkdir(exist_ok=True)

    def path_for(self, key: str) -> Path:
        path = (self.root / validate_key(key)).resolve()
        if self.root not in path.parents:
            raise ValueError("key escapes storage root")
        return path

    # --- objects ---------------------------------------------------------------

    def put_file(self, key: str, path: Path, content_type: str) -> None:
        dest = self.path_for(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".tmp")
        shutil.copyfile(path, tmp)
        tmp.replace(dest)

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        dest = self.path_for(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(dest)

    def download(self, key: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.path_for(key), dest)
        return dest

    def exists(self, key: str) -> bool:
        return self.path_for(key).is_file()

    def size(self, key: str) -> int:
        return self.path_for(key).stat().st_size

    def delete(self, key: str) -> None:
        self.path_for(key).unlink(missing_ok=True)

    def delete_prefix(self, prefix: str) -> int:
        base = self.path_for(prefix.rstrip("/"))
        if not base.exists():
            return 0
        count = sum(1 for p in base.rglob("*") if p.is_file())
        shutil.rmtree(base, ignore_errors=True)
        return count

    def copy(self, src_key: str, dst_key: str) -> None:
        dest = self.path_for(dst_key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.path_for(src_key), dest)

    def list_keys(self, prefix: str) -> list[str]:
        base = self.path_for(prefix.rstrip("/"))
        if not base.exists():
            return []
        return sorted(
            p.relative_to(self.root).as_posix()
            for p in base.rglob("*")
            if p.is_file() and not p.name.endswith(".tmp")
        )

    def signed_get_url(
        self,
        key: str,
        *,
        ttl_sec: int,
        download_name: str | None = None,
        content_type: str | None = None,
    ) -> str:
        payload: dict = {"k": validate_key(key)}
        if download_name:
            payload["dn"] = download_name
        if content_type:
            payload["ct"] = content_type
        token = sign(payload, self._secret, ttl_sec)
        return f"{self.public_base_url}/media/{quote(token)}"

    # --- multipart ---------------------------------------------------------------

    def _session_dir(self, upload_id: str) -> Path:
        uuid.UUID(upload_id)  # reject anything that is not one of our ids
        return self.root / ".multipart" / upload_id

    def create_multipart(self, key: str, content_type: str) -> str:
        upload_id = str(uuid.uuid4())
        session = self._session_dir(upload_id)
        session.mkdir(parents=True)
        (session / "key").write_text(validate_key(key), encoding="utf-8")
        return upload_id

    def signed_part_url(self, key: str, upload_id: str, part_number: int, *, ttl_sec: int) -> str:
        token = sign({"u": upload_id, "n": part_number, "k": key}, self._secret, ttl_sec)
        return (
            f"{self.public_base_url}/storage/uploads/{upload_id}/parts/{part_number}"
            f"?token={quote(token)}"
        )

    def write_part(self, upload_id: str, part_number: int, data: bytes) -> str:
        session = self._session_dir(upload_id)
        if not session.exists():
            raise FileNotFoundError(upload_id)
        (session / f"{part_number:05d}.part").write_bytes(data)
        return hashlib.md5(data, usedforsecurity=False).hexdigest()

    def list_parts(self, key: str, upload_id: str) -> list[PartInfo]:
        session = self._session_dir(upload_id)
        if not session.exists():
            return []
        parts = []
        for part in sorted(session.glob("*.part")):
            data = part.read_bytes()
            parts.append(
                PartInfo(
                    part_number=int(part.stem),
                    etag=hashlib.md5(data, usedforsecurity=False).hexdigest(),
                    size=len(data),
                )
            )
        return parts

    def complete_multipart(self, key: str, upload_id: str, parts: list[tuple[int, str]]) -> None:
        session = self._session_dir(upload_id)
        stored = {p.part_number: p for p in self.list_parts(key, upload_id)}
        dest = self.path_for(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".tmp")
        with tmp.open("wb") as out:
            for number, etag in sorted(parts):
                info = stored.get(number)
                if info is None or info.etag.strip('"') != etag.strip('"'):
                    tmp.unlink(missing_ok=True)
                    raise ValueError(f"part {number} missing or etag mismatch")
                out.write((session / f"{number:05d}.part").read_bytes())
        tmp.replace(dest)
        shutil.rmtree(session, ignore_errors=True)

    def abort_multipart(self, key: str, upload_id: str) -> None:
        shutil.rmtree(self._session_dir(upload_id), ignore_errors=True)
