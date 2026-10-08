"""Fixed-window rate limiting (Redis when available, in-memory otherwise)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict

from videodna.config import Settings
from videodna.errors import AppError, ErrorCode
from videodna.logging_setup import get_logger

log = get_logger(__name__)


class RateLimiter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._memory: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
        self._lock = threading.Lock()
        self._redis = None
        if settings.redis_url and settings.queue_backend == "dramatiq":
            try:
                import redis

                self._redis = redis.Redis.from_url(settings.redis_url, socket_timeout=0.5)
            except Exception:  # pragma: no cover - optional
                self._redis = None

    def hit(self, bucket: str, limit: int, window_sec: int = 60) -> None:
        if limit <= 0:
            return
        window = int(time.time() // window_sec)
        key = f"rl:{bucket}:{window}"
        count = self._incr(key, window, window_sec)
        if count > limit:
            raise AppError(
                ErrorCode.RATE_LIMITED,
                details={"limit": limit, "windowSec": window_sec},
            )

    def _incr(self, key: str, window: int, window_sec: int) -> int:
        if self._redis is not None:
            try:
                pipe = self._redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, window_sec + 5)
                return int(pipe.execute()[0])
            except Exception:
                log.warning("redis rate limiter unavailable; falling back to memory")
                self._redis = None
        with self._lock:
            stored_window, count = self._memory[key]
            if stored_window != window:
                count = 0
            count += 1
            self._memory[key] = (window, count)
            if len(self._memory) > 50_000:
                self._memory.clear()
            return count
