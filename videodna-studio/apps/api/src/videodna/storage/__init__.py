from __future__ import annotations

from functools import lru_cache

from videodna.config import Settings, get_settings
from videodna.storage.base import StorageBackend


def build_storage(settings: Settings) -> StorageBackend:
    if settings.storage_backend == "s3":
        from videodna.storage.s3 import S3Storage

        return S3Storage(settings)
    from videodna.storage.local import LocalStorage

    return LocalStorage(
        settings.storage_local_root,
        settings.api_base_url,
        settings.signing_secret.get_secret_value(),
    )


@lru_cache
def get_storage() -> StorageBackend:
    storage = build_storage(get_settings())
    storage.ensure_ready()
    return storage
