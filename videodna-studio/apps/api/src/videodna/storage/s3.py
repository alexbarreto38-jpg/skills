"""S3-compatible storage (AWS S3, Cloudflare R2, MinIO)."""

from __future__ import annotations

import contextlib
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from videodna.config import Settings
from videodna.storage.base import PartInfo, StorageBackend, validate_key


class S3Storage(StorageBackend):
    name = "s3"

    def __init__(self, settings: Settings) -> None:
        self.bucket = settings.s3_bucket
        config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path" if settings.s3_force_path_style else "auto"},
            retries={"max_attempts": 5, "mode": "standard"},
        )
        credentials = {
            "aws_access_key_id": (
                settings.s3_access_key_id.get_secret_value() if settings.s3_access_key_id else None
            ),
            "aws_secret_access_key": (
                settings.s3_secret_access_key.get_secret_value()
                if settings.s3_secret_access_key
                else None
            ),
        }
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            config=config,
            **credentials,
        )
        # Presigned URLs must use the hostname the *browser* can reach.
        self._presign_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_public_endpoint_url or settings.s3_endpoint_url,
            region_name=settings.s3_region,
            config=config,
            **credentials,
        )

    def ensure_ready(self) -> None:
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self.bucket)

    def healthy(self) -> bool:
        try:
            self._client.head_bucket(Bucket=self.bucket)
            return True
        except Exception:
            return False

    def put_file(self, key: str, path: Path, content_type: str) -> None:
        self._client.upload_file(
            str(path), self.bucket, validate_key(key), ExtraArgs={"ContentType": content_type}
        )

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self.bucket, Key=validate_key(key), Body=data, ContentType=content_type
        )

    def download(self, key: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        self._client.download_file(self.bucket, validate_key(key), str(dest))
        return dest

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=validate_key(key))
            return True
        except ClientError:
            return False

    def size(self, key: str) -> int:
        head = self._client.head_object(Bucket=self.bucket, Key=validate_key(key))
        return int(head["ContentLength"])

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=validate_key(key))

    def delete_prefix(self, prefix: str) -> int:
        count = 0
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=validate_key(prefix)):
            objects = [{"Key": o["Key"]} for o in page.get("Contents", [])]
            if objects:
                self._client.delete_objects(Bucket=self.bucket, Delete={"Objects": objects})
                count += len(objects)
        return count

    def copy(self, src_key: str, dst_key: str) -> None:
        self._client.copy_object(
            Bucket=self.bucket,
            Key=validate_key(dst_key),
            CopySource={"Bucket": self.bucket, "Key": validate_key(src_key)},
        )

    def list_keys(self, prefix: str) -> list[str]:
        keys: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=validate_key(prefix)):
            keys.extend(o["Key"] for o in page.get("Contents", []))
        return keys

    def signed_get_url(
        self,
        key: str,
        *,
        ttl_sec: int,
        download_name: str | None = None,
        content_type: str | None = None,
    ) -> str:
        params = {"Bucket": self.bucket, "Key": validate_key(key)}
        if download_name:
            params["ResponseContentDisposition"] = f'attachment; filename="{download_name}"'
        if content_type:
            params["ResponseContentType"] = content_type
        return self._presign_client.generate_presigned_url(
            "get_object", Params=params, ExpiresIn=ttl_sec
        )

    def create_multipart(self, key: str, content_type: str) -> str:
        response = self._client.create_multipart_upload(
            Bucket=self.bucket, Key=validate_key(key), ContentType=content_type
        )
        return response["UploadId"]

    def signed_part_url(self, key: str, upload_id: str, part_number: int, *, ttl_sec: int) -> str:
        return self._presign_client.generate_presigned_url(
            "upload_part",
            Params={
                "Bucket": self.bucket,
                "Key": validate_key(key),
                "UploadId": upload_id,
                "PartNumber": part_number,
            },
            ExpiresIn=ttl_sec,
        )

    def list_parts(self, key: str, upload_id: str) -> list[PartInfo]:
        parts: list[PartInfo] = []
        paginator = self._client.get_paginator("list_parts")
        try:
            for page in paginator.paginate(
                Bucket=self.bucket, Key=validate_key(key), UploadId=upload_id
            ):
                parts.extend(
                    PartInfo(p["PartNumber"], p["ETag"].strip('"'), p["Size"])
                    for p in page.get("Parts", [])
                )
        except ClientError:
            return []
        return parts

    def complete_multipart(self, key: str, upload_id: str, parts: list[tuple[int, str]]) -> None:
        self._client.complete_multipart_upload(
            Bucket=self.bucket,
            Key=validate_key(key),
            UploadId=upload_id,
            MultipartUpload={
                "Parts": [
                    {"PartNumber": n, "ETag": f'"{etag.strip(chr(34))}"'}
                    for n, etag in sorted(parts)
                ]
            },
        )

    def abort_multipart(self, key: str, upload_id: str) -> None:
        with contextlib.suppress(ClientError):
            self._client.abort_multipart_upload(
                Bucket=self.bucket, Key=validate_key(key), UploadId=upload_id
            )
