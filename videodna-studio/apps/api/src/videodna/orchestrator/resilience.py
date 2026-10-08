"""Timeouts, retries with backoff and error normalization around provider calls."""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from dataclasses import dataclass
from typing import Generic, TypeVar

from videodna.errors import ErrorCode
from videodna.logging_setup import get_logger
from videodna.orchestrator.errors import ProviderError, normalize_exception

T = TypeVar("T")
log = get_logger(__name__)

# Shared pool for enforcing timeouts. A timed-out call keeps running in its
# thread until the underlying client gives up, so real adapters must also set
# their own HTTP timeouts — this is the outer safety net, not the only one.
_EXECUTOR = ThreadPoolExecutor(max_workers=16, thread_name_prefix="provider-call")


@dataclass
class AttemptRecord:
    attempt: int
    latency_ms: int
    error: ProviderError | None


@dataclass
class Invocation(Generic[T]):
    result: T
    attempts: list[AttemptRecord]

    @property
    def latency_ms(self) -> int:
        return sum(a.latency_ms for a in self.attempts)


class InvocationFailed(Exception):
    def __init__(self, error: ProviderError, attempts: list[AttemptRecord]) -> None:
        super().__init__(str(error))
        self.error = error
        self.attempts = attempts


def invoke(
    provider: str,
    fn: Callable[[], T],
    *,
    timeout_sec: float,
    max_attempts: int = 3,
    backoff_base_sec: float = 0.5,
    sleep: Callable[[float], None] = time.sleep,
) -> Invocation[T]:
    attempts: list[AttemptRecord] = []
    for attempt in range(1, max(1, max_attempts) + 1):
        started = time.monotonic()
        future = _EXECUTOR.submit(fn)
        try:
            result = future.result(timeout=timeout_sec)
        except FuturesTimeout:
            future.cancel()
            error = ProviderError(
                ErrorCode.PROVIDER_TIMEOUT, provider, raw=f"timeout after {timeout_sec}s"
            )
        except Exception as exc:  # normalized below; raw text only goes to logs
            error = normalize_exception(exc, provider)
        else:
            attempts.append(AttemptRecord(attempt, _ms_since(started), None))
            return Invocation(result, attempts)

        attempts.append(AttemptRecord(attempt, _ms_since(started), error))
        log.warning(
            "provider call failed",
            extra={
                "provider": provider,
                "attempt": attempt,
                "error_code": error.code.value,
                "retryable": error.retryable,
                "raw_error": (error.raw or "")[:300],
            },
        )
        if not error.retryable or attempt >= max_attempts:
            raise InvocationFailed(error, attempts)
        sleep(backoff_base_sec * (2 ** (attempt - 1)))
    raise AssertionError("unreachable")  # pragma: no cover


def _ms_since(started: float) -> int:
    return int((time.monotonic() - started) * 1000)
