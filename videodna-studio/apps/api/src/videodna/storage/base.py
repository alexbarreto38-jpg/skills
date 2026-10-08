"""Storage abstraction (S3-compatible in production, filesystem in dev/tests).

All media is addressed by *keys* namespaced per project, and clients only ever
receive short-lived signed URLs — never raw keys or bucket credentials.
"""

from __future__ import annotations

import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

_SAFE_EXT = re.compile(r"^\.[a-z0-9]{1,8}$")


@dataclass(frozen=True)
class PartInfo:
    part_number: int
    etag: str
    size: int


class StorageBackend(ABC):
    name: str

    # --- objects ---------------------------------------------------------------
    @abstractmethod
    def put_file(self, key: str, path: Path, content_type: str) -> None: ...

    @abstractmethod
    def put_bytes(self, key: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    def download(self, key: str, dest: Path) -> Path: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def size(self, key: str) -> int: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def delete_prefix(self, prefix: str) -> int: ...

    @abstractmethod
    def copy(self, src_key: str, dst_key: str) -> None: ...

    @abstractmethod
    def list_keys(self, prefix: str) -> list[str]: ...

    @abstractmethod
    def signed_get_url(
        self,
        key: str,
        *,
        ttl_sec: int,
        download_name: str | None = None,
        content_type: str | None = None,
    ) -> str: ...

    # --- multipart upload ------------------------------------------------------
    @abstractmethod
    def create_multipart(self, key: str, content_type: str) -> str: ...

    @abstractmethod
    def signed_part_url(
        self, key: str, upload_id: str, part_number: int, *, ttl_sec: int
    ) -> str: ...

    @abstractmethod
    def list_parts(self, key: str, upload_id: str) -> list[PartInfo]: ...

    @abstractmethod
    def complete_multipart(
        self, key: str, upload_id: str, parts: list[tuple[int, str]]
    ) -> None: ...

    @abstractmethod
    def abort_multipart(self, key: str, upload_id: str) -> None: ...

    def ensure_ready(self) -> None:  # noqa: B027 - optional hook
        """Create buckets/directories if needed."""

    def healthy(self) -> bool:
        return True


# --- key layout ------------------------------------------------------------------


def safe_extension(filename: str, default: str = ".mp4") -> str:
    ext = Path(filename).suffix.lower()
    return ext if _SAFE_EXT.match(ext) else default


def source_key(project_id: uuid.UUID, source_id: uuid.UUID, filename: str) -> str:
    return f"projects/{project_id}/source/{source_id}/original{safe_extension(filename)}"


def source_asset_key(project_id: uuid.UUID, source_id: uuid.UUID, name: str) -> str:
    return f"projects/{project_id}/source/{source_id}/{name}"


def analysis_key(project_id: uuid.UUID, analysis_id: uuid.UUID, name: str) -> str:
    return f"projects/{project_id}/analysis/{analysis_id}/{name}"


def job_key(project_id: uuid.UUID, job_id: uuid.UUID, name: str) -> str:
    return f"projects/{project_id}/jobs/{job_id}/{name}"


def suggestion_key(project_id: uuid.UUID, suggestion_id: uuid.UUID, ext: str = ".svg") -> str:
    return f"projects/{project_id}/suggestions/{suggestion_id}{ext}"


def project_prefix(project_id: uuid.UUID) -> str:
    return f"projects/{project_id}/"


def validate_key(key: str) -> str:
    if (
        not key
        or key.startswith("/")
        or "\\" in key
        or any(p in {"..", "."} for p in key.split("/"))
    ):
        raise ValueError(f"invalid storage key: {key!r}")
    return key
