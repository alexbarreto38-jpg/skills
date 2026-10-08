"""Failure injection shared by mock adapters.

`failure_mode` (from providers.yaml params or MOCK_PROVIDER_FAILURES) lets tests
and demos exercise timeouts, retries, fallbacks and quota errors without any
real provider:

* ``timeout_once`` / ``unavailable_once`` — first call fails, then succeeds
* ``quota`` — every call fails with a non-retryable quota error
* ``always_fail`` — every call fails with a retryable error
* ``slow:<seconds>`` — every call sleeps first (to trip the router timeout)
"""

from __future__ import annotations

import threading
import time

from videodna.errors import ErrorCode
from videodna.orchestrator.errors import ProviderError


class MockFailures:
    def __init__(self, provider: str, mode: str | None) -> None:
        self.provider = provider
        self.mode = mode or ""
        self.calls = 0
        self._lock = threading.Lock()

    def check(self) -> None:
        with self._lock:
            self.calls += 1
            calls = self.calls
        mode = self.mode
        if not mode:
            return
        if mode == "timeout_once" and calls == 1:
            raise TimeoutError("mock provider timed out")
        if mode == "unavailable_once" and calls == 1:
            raise ConnectionError("mock provider returned 503")
        if mode == "quota":
            raise ProviderError(ErrorCode.PROVIDER_QUOTA, self.provider, raw="mock quota exceeded")
        if mode == "always_fail":
            raise ProviderError(ErrorCode.PROVIDER_UNAVAILABLE, self.provider, raw="mock outage")
        if mode.startswith("slow:"):
            time.sleep(float(mode.split(":", 1)[1]))


class MockMixin:
    """Mixed into every mock adapter (after ProviderAdapter.__init__)."""

    params: dict
    descriptor: object

    @property
    def failures(self) -> MockFailures:
        existing = getattr(self, "_failures", None)
        if existing is None:
            existing = MockFailures(self.descriptor.name, self.params.get("failure_mode"))  # type: ignore[attr-defined]
            self._failures = existing
        return existing
