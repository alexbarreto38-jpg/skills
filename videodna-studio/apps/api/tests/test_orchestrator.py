"""AI Router, provider registry and provider-adapter contract tests (spec §87):
capability, timeout, retry, cost parsing and error normalization."""

from __future__ import annotations

import time
from decimal import Decimal

import pytest
from sqlalchemy import select

from videodna.config import Settings
from videodna.db import models as m
from videodna.domain.enums import QualityMode
from videodna.errors import AppError, ErrorCode
from videodna.features import FeatureFlags
from videodna.orchestrator.capabilities import KINDS_FOR_CAPABILITY, Capability
from videodna.orchestrator.descriptor import CostModel, ProviderDescriptor
from videodna.orchestrator.errors import ProviderError, normalize_exception
from videodna.orchestrator.gateway import AIOrchestrator, UsageContext
from videodna.orchestrator.interfaces import (
    INTERFACE_FOR_KIND,
    HealthStatus,
    ProviderResult,
    ProviderUsageInfo,
)
from videodna.orchestrator.registry import ProviderRegistry, load_descriptors
from videodna.orchestrator.resilience import InvocationFailed, invoke
from videodna.orchestrator.router import AIProviderRouter, RoutingTask


def _registry(settings: Settings, **overrides) -> ProviderRegistry:
    descriptors = load_descriptors(settings.providers_config_path)
    for d in descriptors:
        for key, value in overrides.get(d.name, {}).items():
            setattr(d, key, value)
    return ProviderRegistry(descriptors, settings, FeatureFlags({}, overrides.get("_flags", {})))


def test_every_registered_adapter_implements_its_interface(settings):
    registry = _registry(settings)
    for descriptor in registry.descriptors():
        adapter = registry.adapter(descriptor.name)
        assert isinstance(adapter, INTERFACE_FOR_KIND[descriptor.kind]), descriptor.name
        for capability in descriptor.capabilities:
            assert descriptor.kind in KINDS_FOR_CAPABILITY[capability], (
                descriptor.name,
                capability,
            )
        assert adapter.health_check() == HealthStatus.HEALTHY


def test_every_capability_used_by_the_pipeline_has_a_provider(settings):
    registry = _registry(settings)
    covered = {c for d in registry.descriptors() for c in d.capabilities}
    assert set(Capability) <= covered


def test_mock_mode_disables_real_providers_and_vice_versa(settings):
    registry = _registry(settings)
    real = registry.descriptors()[0].model_copy(
        update={"name": "real", "mock": False, "local": False}
    )
    assert registry.availability(real)[0] is False
    settings.ai_mock_mode = False
    try:
        assert registry.availability(registry.descriptor("mock-edit-lite"))[0] is False
        assert registry.availability(registry.descriptor("ffmpeg-qa"))[0] is True  # local stays on
    finally:
        settings.ai_mock_mode = True


def test_real_provider_needs_docs_and_its_credentials(settings, monkeypatch):
    base = {
        "name": "acme-v2v",
        "kind": "video_editor",
        "adapter": "videodna.orchestrator.adapters.mock.video:MockVideoEditor",
        "capabilities": ["video.background_replace"],
        "credentials_env": ["ACME_API_KEY"],
    }
    with pytest.raises(ValueError, match="docs_url"):
        ProviderDescriptor.model_validate(base)
    real = ProviderDescriptor.model_validate({**base, "docs_url": "https://example.com/docs"})

    settings.ai_mock_mode = False
    try:
        registry = _registry(settings)
        monkeypatch.delenv("ACME_API_KEY", raising=False)
        assert registry.availability(real) == (False, "credencial ausente: ACME_API_KEY")
        monkeypatch.setenv("ACME_API_KEY", "test-key")
        assert registry.availability(real) == (True, None)
    finally:
        settings.ai_mock_mode = True


@pytest.mark.parametrize(
    "mode,capability,expected",
    [
        (QualityMode.ECONOMY, Capability.VIDEO_LOCALIZED_EDIT, "mock-edit-lite"),
        (QualityMode.BALANCED, Capability.VIDEO_LOCALIZED_EDIT, "mock-edit-pro"),
        (QualityMode.MAX, Capability.VIDEO_ATTRIBUTE_EDIT, "mock-edit-pro"),
        (QualityMode.BALANCED, Capability.VIDEO_ATTRIBUTE_EDIT, "mock-edit-lite"),
        (QualityMode.MAX, Capability.VIDEO_BACKGROUND_REPLACE, "mock-v2v"),
    ],
)
def test_router_respects_quality_mode(settings, mode, capability, expected):
    router = AIProviderRouter(_registry(settings), settings)
    decision = router.route(
        RoutingTask(capability=capability, quality_mode=mode, duration_sec=3, output_height=720)
    )
    assert decision.provider == expected
    assert decision.reasons and decision.candidates


def test_router_filters_by_features_limits_and_flags(settings):
    router = AIProviderRouter(_registry(settings), settings)
    task = RoutingTask(
        capability=Capability.VIDEO_SHOT_RECONSTRUCTION,
        duration_sec=3,
        required_features=frozenset({"motion_preservation"}),
    )
    decision = router.route(task)
    rejected = {c.provider: c.rejection for c in decision.candidates if not c.eligible}
    assert decision.provider == "mock-v2v" and "motion_preservation" in rejected["mock-gen"]

    too_many = RoutingTask(capability=Capability.VIDEO_LOCALIZED_EDIT, edit_count=5, duration_sec=2)
    assert router.route(too_many).provider == "mock-edit-pro"  # lite allows at most 3 edits

    flagged = AIProviderRouter(_registry(settings, _flags={"provider.mock-v2v": False}), settings)
    with pytest.raises(AppError) as exc:
        flagged.route(task)
    assert exc.value.code == ErrorCode.NO_PROVIDER_AVAILABLE


def test_router_chunks_long_shots_and_converts_currency(settings):
    registry = _registry(settings)
    router = AIProviderRouter(registry, settings)
    decision = router.route(
        RoutingTask(capability=Capability.VIDEO_SHOT_RECONSTRUCTION, duration_sec=25)
    )
    assert decision.chunks == 3  # mock-v2v: 10s per call

    registry.descriptor("mock-edit-lite").cost = CostModel(
        unit="second", amount=Decimal("0.1"), currency="USD"
    )
    no_rate = AIProviderRouter(registry, settings).route(
        RoutingTask(
            capability=Capability.VIDEO_ATTRIBUTE_EDIT,
            duration_sec=2,
            quality_mode=QualityMode.ECONOMY,
        )
    )
    assert no_rate.provider == "mock-edit-pro"  # USD price without a configured rate is unusable
    settings.fx_rates_to_base = "USD:5"
    try:
        converted = AIProviderRouter(registry, settings).route(
            RoutingTask(
                capability=Capability.VIDEO_ATTRIBUTE_EDIT,
                duration_sec=2,
                quality_mode=QualityMode.ECONOMY,
            )
        )
        assert converted.provider == "mock-edit-lite" and converted.estimated_cost == Decimal(
            "1.0000"
        )
    finally:
        settings.fx_rates_to_base = ""


def test_router_uses_historical_success_rate(settings):
    stats = {("mock-edit-pro", "video.localized_edit"): (2, 40)}  # 5% success observed
    router = AIProviderRouter(
        _registry(settings), settings, stats=lambda p, c: stats.get((p, c), (0, 0))
    )
    decision = router.route(RoutingTask(capability=Capability.VIDEO_LOCALIZED_EDIT, duration_sec=3))
    assert decision.provider == "mock-edit-lite"


def test_fallback_recomputes_and_refuses_expensive_alternatives(settings):
    router = AIProviderRouter(_registry(settings), settings)
    task = RoutingTask(capability=Capability.VIDEO_BACKGROUND_REPLACE, duration_sec=3)
    first = router.route(task)
    assert first.provider == "mock-edit-pro"
    with pytest.raises(AppError) as exc:
        router.fallback(task, first)  # v2v costs ~1.8x: above the 50% ceiling
    assert exc.value.details["fallbackProvider"] == "mock-v2v"
    settings.fallback_max_cost_increase = 2.0
    try:
        assert router.fallback(task, first).provider == "mock-v2v"
    finally:
        settings.fallback_max_cost_increase = 0.5


def test_degraded_providers_are_penalized_and_down_ones_skipped(settings):
    registry = _registry(settings)
    router = AIProviderRouter(registry, settings)
    task = RoutingTask(capability=Capability.VIDEO_LOCALIZED_EDIT, duration_sec=3)
    registry.set_health_override("mock-edit-pro", HealthStatus.DOWN)
    assert router.route(task).provider == "mock-edit-lite"
    registry.set_health_override("mock-edit-pro", None)


# --- resilience ----------------------------------------------------------------


def test_invoke_times_out_and_normalizes():
    with pytest.raises(InvocationFailed) as exc:
        invoke("slow", lambda: time.sleep(0.5), timeout_sec=0.05, max_attempts=1)
    assert exc.value.error.code == ErrorCode.PROVIDER_TIMEOUT


def test_invoke_retries_retryable_errors_with_backoff():
    calls, sleeps = [], []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("503 service unavailable")
        return "ok"

    out = invoke(
        "p", flaky, timeout_sec=1, max_attempts=3, backoff_base_sec=0.1, sleep=sleeps.append
    )
    assert out.result == "ok" and len(out.attempts) == 3
    assert sleeps == [0.1, 0.2]


def test_invoke_does_not_retry_non_retryable_errors():
    calls = []

    def quota():
        calls.append(1)
        raise ProviderError(ErrorCode.PROVIDER_QUOTA, "p")

    with pytest.raises(InvocationFailed):
        invoke("p", quota, timeout_sec=1, max_attempts=3, sleep=lambda _: None)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "exc,code",
    [
        (TimeoutError("x"), ErrorCode.PROVIDER_TIMEOUT),
        (RuntimeError("HTTP 429 rate limit"), ErrorCode.PROVIDER_QUOTA),
        (ConnectionError("reset"), ErrorCode.PROVIDER_UNAVAILABLE),
        (RuntimeError("blocked by safety filter"), ErrorCode.PROVIDER_CONTENT_REJECTED),
        (ValueError("bad"), ErrorCode.PROVIDER_INVALID_REQUEST),
        (RuntimeError("???"), ErrorCode.PROVIDER_ERROR),
    ],
)
def test_error_normalization(exc, code):
    error = normalize_exception(exc, "p")
    assert error.code == code
    assert "safety" not in error.message  # raw provider text never reaches users


def test_cost_parsing_prefers_reported_cost(settings):
    adapter = _registry(settings).adapter("mock-edit-pro")
    reported = ProviderUsageInfo(reported_cost=Decimal("1.23"), currency="BRL")
    assert adapter.actual_cost(Capability.VIDEO_LOCALIZED_EDIT, reported, 3, 720) == (
        Decimal("1.23"),
        "BRL",
    )
    estimate, _ = adapter.actual_cost(Capability.VIDEO_LOCALIZED_EDIT, ProviderUsageInfo(), 3, 720)
    assert estimate == Decimal("2.9000")  # 0.20 per call + 0.90 * 3s


def test_cost_model_resolution_multipliers():
    model = CostModel(
        unit="second", amount=Decimal("1"), resolution_multipliers={720: 1.0, 1080: 1.5}
    )
    assert model.estimate(2, 720) == Decimal("2.0000")
    assert model.estimate(2, 1080) == Decimal("3.0000")
    assert model.estimate(2, 2160) == Decimal("3.0000")


# --- gateway: usage, cost ledger, fallback ------------------------------------------


def test_gateway_records_every_attempt_and_falls_back(runtime):
    settings = runtime.settings
    registry = _registry(settings)
    registry.descriptor("mock-edit-lite").params["failure_mode"] = "always_fail"
    orchestrator = AIOrchestrator(registry, settings, runtime.session_factory, sleep=lambda _: None)
    with runtime.session_factory() as session:
        user = m.User(email="g@exemplo.com.br")
        session.add(user)
        session.flush()
        project = m.Project(owner_id=user.id, name="p")
        session.add(project)
        session.commit()
        project_id = project.id

    task = RoutingTask(
        capability=Capability.VIDEO_ATTRIBUTE_EDIT, duration_sec=2, quality_mode=QualityMode.ECONOMY
    )
    settings.fallback_max_cost_increase = 5.0
    try:
        out = orchestrator.run(
            task,
            lambda adapter, d: (adapter.failures.check(), ProviderResult())[1],
            operation="test",
            context=UsageContext(project_id=project_id),
        )
    finally:
        settings.fallback_max_cost_increase = 0.5
    assert out.decision.provider == "mock-edit-pro"
    with runtime.session_factory() as session:
        usage = session.scalars(select(m.ProviderUsage).order_by(m.ProviderUsage.created_at)).all()
        assert [(u.provider, u.status.value) for u in usage] == [
            ("mock-edit-lite", "FAILURE"),
            ("mock-edit-lite", "FAILURE"),
            ("mock-edit-lite", "FAILURE"),
            ("mock-edit-pro", "SUCCESS"),
        ]
        costs = session.scalars(select(m.CostEntry)).all()
        assert len(costs) == 1 and costs[0].provider == "mock-edit-pro" and costs[0].amount > 0
