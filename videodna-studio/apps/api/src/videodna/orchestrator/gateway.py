"""AI Orchestrator gateway: the only way business code calls a provider.

    route (capability) -> adapter -> invoke (timeout/retry) -> record usage & cost
                                   \\-> on failure: re-route (fallback) once

Every attempt — success or failure — becomes a `ProviderUsage` row, and every
successful paid call a `CostEntry(ACTUAL)`. Those rows feed cost reporting,
the admin dashboard and the router's historical success rates.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Generic, TypeVar

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from videodna.config import Settings
from videodna.db import models as m
from videodna.domain.enums import CostKind, UsageStatus
from videodna.errors import AppError, ErrorCode
from videodna.logging_setup import get_logger
from videodna.orchestrator.errors import ProviderError
from videodna.orchestrator.interfaces import ProviderAdapter, ProviderResult
from videodna.orchestrator.registry import ProviderRegistry
from videodna.orchestrator.resilience import InvocationFailed, invoke
from videodna.orchestrator.router import AIProviderRouter, RoutingDecision, RoutingTask

T = TypeVar("T", bound=ProviderResult)
log = get_logger(__name__)

SessionFactory = Callable[[], Session]
_FALLBACK_CODES = {
    ErrorCode.PROVIDER_TIMEOUT,
    ErrorCode.PROVIDER_UNAVAILABLE,
    ErrorCode.PROVIDER_QUOTA,
    ErrorCode.PROVIDER_ERROR,
}


@dataclass
class UsageContext:
    project_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    plan_id: uuid.UUID | None = None
    shot_key: str | None = None


@dataclass
class OrchestratedResult(Generic[T]):
    result: T
    decision: RoutingDecision
    actual_cost: Decimal
    currency: str
    attempts: int


class ProviderStatsCache:
    """(successes, total) per provider+capability from our own usage history."""

    def __init__(self, session_factory: SessionFactory, window_days: int = 30) -> None:
        self._session_factory = session_factory
        self._window = timedelta(days=window_days)
        self._cache: dict[tuple[str, str], tuple[int, int]] | None = None

    def __call__(self, provider: str, capability: str) -> tuple[int, int]:
        if self._cache is None:
            self._cache = self._load()
        return self._cache.get((provider, capability), (0, 0))

    def _load(self) -> dict[tuple[str, str], tuple[int, int]]:
        since = datetime.now(UTC) - self._window
        with self._session_factory() as session:
            rows = session.execute(
                select(
                    m.ProviderUsage.provider,
                    m.ProviderUsage.capability,
                    func.sum(case((m.ProviderUsage.status == UsageStatus.SUCCESS, 1), else_=0)),
                    func.count(),
                )
                .where(m.ProviderUsage.created_at >= since)
                .group_by(m.ProviderUsage.provider, m.ProviderUsage.capability)
            ).all()
        return {(p, c): (int(s or 0), int(n)) for p, c, s, n in rows}


class AIOrchestrator:
    def __init__(
        self,
        registry: ProviderRegistry,
        settings: Settings,
        session_factory: SessionFactory,
        *,
        router: AIProviderRouter | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.registry = registry
        self.settings = settings
        self._session_factory = session_factory
        self.router = router or AIProviderRouter(
            registry, settings, stats=ProviderStatsCache(session_factory)
        )
        self._sleep = sleep

    def route(self, task: RoutingTask) -> RoutingDecision:
        return self.router.route(task)

    def run(
        self,
        task: RoutingTask,
        call: Callable[[ProviderAdapter, RoutingDecision], T],
        *,
        operation: str,
        context: UsageContext,
        decision: RoutingDecision | None = None,
        allow_fallback: bool = True,
    ) -> OrchestratedResult[T]:
        decision = decision or self.router.route(task)
        try:
            return self._attempt(task, decision, call, operation, context)
        except InvocationFailed as failure:
            if not allow_fallback or failure.error.code not in _FALLBACK_CODES:
                raise failure.error from None
            try:
                alternative = self.router.fallback(task, decision)
            except AppError as exc:
                log.warning(
                    "no acceptable fallback",
                    extra={"provider": decision.provider, "reason": exc.code.value},
                )
                raise failure.error from None
            log.info(
                "falling back to another provider",
                extra={
                    "from": decision.provider,
                    "to": alternative.provider,
                    "operation": operation,
                },
            )
            try:
                return self._attempt(task, alternative, call, operation, context)
            except InvocationFailed as second:
                raise second.error from None

    # --- internals ---------------------------------------------------------------

    def _attempt(
        self,
        task: RoutingTask,
        decision: RoutingDecision,
        call: Callable[[ProviderAdapter, RoutingDecision], T],
        operation: str,
        context: UsageContext,
    ) -> OrchestratedResult[T]:
        adapter = self.registry.adapter(decision.provider)
        descriptor = adapter.descriptor
        timeout = descriptor.limits.timeout_sec or self.settings.provider_timeout_sec
        kwargs = {}
        if self._sleep is not None:
            kwargs["sleep"] = self._sleep
        try:
            outcome = invoke(
                decision.provider,
                lambda: call(adapter, decision),
                timeout_sec=timeout,
                max_attempts=self.settings.provider_max_attempts,
                backoff_base_sec=self.settings.provider_backoff_base_sec,
                **kwargs,
            )
        except InvocationFailed as failure:
            for record in failure.attempts:
                self._record(
                    decision, operation, context, record.attempt, record.latency_ms, record.error
                )
            raise

        for record in outcome.attempts[:-1]:
            self._record(
                decision, operation, context, record.attempt, record.latency_ms, record.error
            )
        result = outcome.result
        quantity = task.quantity if task.quantity is not None else task.duration_sec
        cost, currency = adapter.actual_cost(
            task.capability, result.usage, quantity, task.output_height
        )
        rate = Decimal(str(self.settings.fx_rates().get(currency.upper(), 1.0)))
        cost_base = (cost * rate).quantize(Decimal("0.0001"))
        last = outcome.attempts[-1]
        self._record(
            decision,
            operation,
            context,
            last.attempt,
            last.latency_ms,
            None,
            result=result,
            cost=cost_base,
        )
        return OrchestratedResult(
            result=result,
            decision=decision,
            actual_cost=cost_base,
            currency=self.settings.cost_currency,
            attempts=len(outcome.attempts),
        )

    def _record(
        self,
        decision: RoutingDecision,
        operation: str,
        context: UsageContext,
        attempt: int,
        latency_ms: int,
        error: ProviderError | None,
        *,
        result: ProviderResult | None = None,
        cost: Decimal | None = None,
    ) -> None:
        usage = result.usage if result else None
        with self._session_factory() as session:
            row = m.ProviderUsage(
                project_id=context.project_id,
                user_id=context.user_id,
                job_id=context.job_id,
                provider=decision.provider,
                model=(usage.model if usage and usage.model else decision.model),
                capability=decision.capability.value,
                operation=operation,
                status=UsageStatus.FAILURE if error else UsageStatus.SUCCESS,
                error_code=error.code.value if error else None,
                attempt=attempt,
                latency_ms=latency_ms,
                estimated_cost=decision.estimated_cost,
                actual_cost=cost if not error else Decimal(0),
                currency=self.settings.cost_currency,
                tokens=usage.tokens if usage else None,
                credits=usage.credits if usage else None,
                seconds_generated=usage.seconds_generated if usage else None,
                shot_key=context.shot_key,
            )
            session.add(row)
            session.flush()
            if not error and context.project_id is not None and cost is not None:
                session.add(
                    m.CostEntry(
                        project_id=context.project_id,
                        user_id=context.user_id,
                        job_id=context.job_id,
                        plan_id=context.plan_id,
                        provider_usage_id=row.id,
                        kind=CostKind.ACTUAL,
                        provider=decision.provider,
                        model=row.model,
                        operation=operation,
                        amount=cost,
                        currency=self.settings.cost_currency,
                        quantity=float(usage.seconds_generated or usage.images or 1)
                        if usage
                        else 1.0,
                        unit=self.registry.descriptor(decision.provider)
                        .cost_for(decision.capability)
                        .unit,
                        seconds_generated=usage.seconds_generated if usage else None,
                        tokens=usage.tokens if usage else None,
                        credits=usage.credits if usage else None,
                        shot_key=context.shot_key,
                        description=operation,
                    )
                )
            session.commit()
