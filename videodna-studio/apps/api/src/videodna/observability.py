"""Optional observability integrations (Sentry / OpenTelemetry).

Nothing is required: if SENTRY_DSN or OTEL_EXPORTER_OTLP_ENDPOINT is set *and*
the corresponding package is installed (`uv add sentry-sdk` /
`uv add opentelemetry-distro opentelemetry-exporter-otlp`), it is initialized;
otherwise this is a no-op. Structured logs, ProviderUsage and JobEvent rows
already carry the latency/error/cost data dashboards need.
"""

from __future__ import annotations

import importlib

from videodna.config import Settings
from videodna.logging_setup import get_logger

log = get_logger(__name__)


def init_observability(settings: Settings) -> None:
    if settings.sentry_dsn:
        try:
            sentry_sdk = importlib.import_module("sentry_sdk")
            sentry_sdk.init(
                dsn=settings.sentry_dsn.get_secret_value(),
                environment=settings.app_env,
                traces_sample_rate=0.1,
                send_default_pii=False,
            )
            log.info("sentry initialized")
        except ModuleNotFoundError:
            log.warning("SENTRY_DSN set but sentry-sdk is not installed")
    if settings.otel_exporter_otlp_endpoint:
        try:
            importlib.import_module("opentelemetry")
            log.info("OpenTelemetry endpoint configured; use opentelemetry-instrument to run")
        except ModuleNotFoundError:
            log.warning("OTEL endpoint set but opentelemetry is not installed")
