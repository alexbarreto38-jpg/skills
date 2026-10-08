"""Signed URL helpers — the only way media leaves the backend."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict

from videodna.runtime import Runtime

# The same URL is handed out again while it still has at least half its life
# left. A fresh signature on every request would change the editor's <video>
# src on each refetch — and a new src reloads the video and jumps back to 0:00.
_cache: OrderedDict[tuple, tuple[float, str]] = OrderedDict()
_lock = threading.Lock()
_MAX_ENTRIES = 4096


def signed(
    runtime: Runtime,
    key: str | None,
    *,
    download_name: str | None = None,
    content_type: str | None = None,
) -> str | None:
    if not key:
        return None
    ttl = runtime.settings.signed_url_ttl_sec
    cache_key = (id(runtime.storage), key, download_name, content_type, ttl)
    now = time.monotonic()
    with _lock:
        hit = _cache.get(cache_key)
        if hit and hit[0] > now:
            _cache.move_to_end(cache_key)
            return hit[1]
    url = runtime.storage.signed_get_url(
        key, ttl_sec=ttl, download_name=download_name, content_type=content_type
    )
    with _lock:
        _cache[cache_key] = (now + ttl / 2, url)
        _cache.move_to_end(cache_key)
        while len(_cache) > _MAX_ENTRIES:
            _cache.popitem(last=False)
    return url
