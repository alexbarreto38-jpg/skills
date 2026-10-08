"""Provider error normalization."""

from __future__ import annotations

from videodna.errors import AppError, ErrorCode

RETRYABLE_CODES = frozenset(
    {ErrorCode.PROVIDER_TIMEOUT, ErrorCode.PROVIDER_UNAVAILABLE, ErrorCode.PROVIDER_ERROR}
)


class ProviderError(AppError):
    """Raised by adapters. `raw` is for server logs only, never for clients."""

    def __init__(
        self,
        code: ErrorCode,
        provider: str,
        *,
        raw: str | None = None,
        retryable: bool | None = None,
        message: str | None = None,
    ) -> None:
        super().__init__(code, message)
        self.provider = provider
        self.raw = raw
        self.retryable = code in RETRYABLE_CODES if retryable is None else retryable


def normalize_exception(exc: BaseException, provider: str) -> ProviderError:
    """Map arbitrary exceptions from SDKs/HTTP clients onto normalized codes."""
    if isinstance(exc, ProviderError):
        return exc
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    if isinstance(exc, TimeoutError) or "timeout" in name or "timed out" in text:
        return ProviderError(ErrorCode.PROVIDER_TIMEOUT, provider, raw=str(exc))
    if "quota" in text or "rate limit" in text or "429" in text or "insufficient" in text:
        return ProviderError(ErrorCode.PROVIDER_QUOTA, provider, raw=str(exc), retryable=False)
    if isinstance(exc, ConnectionError) or "connection" in name or "503" in text:
        return ProviderError(ErrorCode.PROVIDER_UNAVAILABLE, provider, raw=str(exc))
    if "safety" in text or "content policy" in text or "moderation" in text:
        return ProviderError(ErrorCode.PROVIDER_CONTENT_REJECTED, provider, raw=str(exc))
    if isinstance(exc, ValueError | TypeError) or "400" in text or "invalid" in text:
        return ProviderError(
            ErrorCode.PROVIDER_INVALID_REQUEST, provider, raw=str(exc), retryable=False
        )
    return ProviderError(ErrorCode.PROVIDER_ERROR, provider, raw=repr(exc))
