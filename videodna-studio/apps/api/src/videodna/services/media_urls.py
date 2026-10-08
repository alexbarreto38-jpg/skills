"""Signed URL helpers — the only way media leaves the backend."""

from __future__ import annotations

from videodna.runtime import Runtime


def signed(
    runtime: Runtime,
    key: str | None,
    *,
    download_name: str | None = None,
    content_type: str | None = None,
) -> str | None:
    if not key:
        return None
    return runtime.storage.signed_get_url(
        key,
        ttl_sec=runtime.settings.signed_url_ttl_sec,
        download_name=download_name,
        content_type=content_type,
    )
