"""AIProviderRouter — chooses a provider/model per task.

Inputs: task capability, quality mode, duration, resolution, required features
and exclusions. Considered: enablement, health, limits, estimated cost, latency,
historical success rate (from our own ProviderUsage data, blended with a prior)
and priority. The decision is explained (`reasons`, ranked `candidates`) so the
Generation Plan can show *why* a provider was picked.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from videodna.config import Settings
from videodna.domain.enums import QualityMode
from videodna.errors import AppError, ErrorCode
from videodna.orchestrator.capabilities import Capability
from videodna.orchestrator.descriptor import ProviderDescriptor
from videodna.orchestrator.interfaces import HealthStatus
from videodna.orchestrator.registry import ProviderRegistry

# (successes, total) observed for (provider, capability)
StatsLookup = Callable[[str, str], tuple[int, int]]

WEIGHTS: dict[QualityMode, dict[str, float]] = {
    QualityMode.ECONOMY: {"cost": 0.55, "quality": 0.2, "success": 0.2, "latency": 0.05},
    QualityMode.BALANCED: {"cost": 0.3, "quality": 0.4, "success": 0.2, "latency": 0.1},
    QualityMode.MAX: {"cost": 0.02, "quality": 0.7, "success": 0.25, "latency": 0.03},
}
# Minimum quality a mode expects. Candidates below it are penalized — but still
# usable when nothing meets the bar (better a weaker result than no result).
QUALITY_FLOOR: dict[QualityMode, float] = {
    QualityMode.ECONOMY: 0.0,
    QualityMode.BALANCED: 0.7,
    QualityMode.MAX: 0.8,
}
_FLOOR_PENALTY = 0.3
# Our own history overrides the prior once there is enough of it.
_MIN_SAMPLES = 10
_LOW_SUCCESS = 0.5
_LOW_SUCCESS_PENALTY = 0.25
_PRIOR_WEIGHT = 20  # observations the prior is worth


@dataclass(frozen=True)
class RoutingTask:
    capability: Capability
    quality_mode: QualityMode = QualityMode.BALANCED
    duration_sec: float = 0.0
    quantity: float | None = None  # billing units; defaults to duration
    output_height: int | None = None
    required_features: frozenset[str] = frozenset()
    exclude: frozenset[str] = frozenset()
    edit_count: int = 1


@dataclass
class Candidate:
    provider: str
    model: str | None
    eligible: bool
    rejection: str | None = None
    score: float = 0.0
    quality: float = 0.0
    success_rate: float = 0.0
    estimated_cost: Decimal = Decimal(0)
    estimated_latency_sec: float = 0.0
    chunks: int = 1
    degraded: bool = False
    samples: int = 0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "eligible": self.eligible,
            "rejection": self.rejection,
            "notes": self.notes,
            "score": round(self.score, 4),
            "quality": self.quality,
            "successRate": round(self.success_rate, 4),
            "estimatedCost": float(self.estimated_cost),
            "estimatedLatencySec": round(self.estimated_latency_sec, 2),
            "chunks": self.chunks,
        }


@dataclass
class RoutingDecision:
    provider: str
    model: str | None
    capability: Capability
    quality_mode: QualityMode
    estimated_cost: Decimal
    currency: str
    estimated_latency_sec: float
    chunks: int
    score: float
    reasons: list[str] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "capability": self.capability.value,
            "qualityMode": self.quality_mode.value,
            "estimatedCost": float(self.estimated_cost),
            "currency": self.currency,
            "estimatedLatencySec": round(self.estimated_latency_sec, 2),
            "chunks": self.chunks,
            "score": round(self.score, 4),
            "reasons": self.reasons,
            "candidates": [c.to_dict() for c in self.candidates],
        }


class AIProviderRouter:
    def __init__(
        self,
        registry: ProviderRegistry,
        settings: Settings,
        stats: StatsLookup | None = None,
    ) -> None:
        self.registry = registry
        self.settings = settings
        self._stats = stats or (lambda _p, _c: (0, 0))
        self._fx = settings.fx_rates()

    # --- public ----------------------------------------------------------------

    def route(self, task: RoutingTask) -> RoutingDecision:
        evaluated = [self._evaluate(d, task) for d in self.registry.candidates(task.capability)]
        eligible = [c for c in evaluated if c.eligible]
        if not eligible:
            raise AppError(
                ErrorCode.NO_PROVIDER_AVAILABLE,
                details={
                    "capability": task.capability.value,
                    "candidates": [c.to_dict() for c in evaluated],
                },
            )
        self._score(eligible, task.quality_mode)
        ranked = sorted(eligible, key=lambda c: c.score, reverse=True)
        best = ranked[0]
        descriptor = self.registry.descriptor(best.provider)
        reasons = [
            f"modo {task.quality_mode.value}: pesos {WEIGHTS[task.quality_mode]}",
            f"qualidade {best.quality:.2f}, sucesso histórico {best.success_rate:.0%}",
            f"custo estimado {best.estimated_cost:.2f} {self.settings.cost_currency}",
        ]
        if best.chunks > 1:
            reasons.append(
                f"shot dividido em {best.chunks} partes "
                f"(limite {descriptor.limits.max_duration_sec}s)"
            )
        if len(ranked) > 1:
            reasons.append(f"alternativa: {ranked[1].provider} (score {ranked[1].score:.3f})")
        ordered = ranked + [c for c in evaluated if not c.eligible]
        return RoutingDecision(
            provider=best.provider,
            model=best.model,
            capability=task.capability,
            quality_mode=task.quality_mode,
            estimated_cost=best.estimated_cost,
            currency=self.settings.cost_currency,
            estimated_latency_sec=best.estimated_latency_sec,
            chunks=best.chunks,
            score=best.score,
            reasons=reasons,
            candidates=ordered,
        )

    def fallback(self, task: RoutingTask, failed: RoutingDecision) -> RoutingDecision:
        """Re-route after a failure. Re-evaluates everything (capabilities, cost,
        limits) instead of blindly taking the runner-up, and refuses a fallback
        that would cost much more than what the user approved."""
        retry_task = RoutingTask(
            capability=task.capability,
            quality_mode=task.quality_mode,
            duration_sec=task.duration_sec,
            quantity=task.quantity,
            output_height=task.output_height,
            required_features=task.required_features,
            exclude=task.exclude | {failed.provider},
            edit_count=task.edit_count,
        )
        decision = self.route(retry_task)
        ceiling = failed.estimated_cost * Decimal(str(1 + self.settings.fallback_max_cost_increase))
        if failed.estimated_cost > 0 and decision.estimated_cost > ceiling:
            raise AppError(
                ErrorCode.NO_PROVIDER_AVAILABLE,
                "O provider alternativo custaria bem mais do que o estimado; "
                "a geração foi interrompida para sua aprovação.",
                details={
                    "failedProvider": failed.provider,
                    "fallbackProvider": decision.provider,
                    "estimatedCost": float(failed.estimated_cost),
                    "fallbackCost": float(decision.estimated_cost),
                },
            )
        decision.reasons.insert(0, f"fallback após falha de {failed.provider}")
        return decision

    def estimate(self, task: RoutingTask) -> Decimal:
        return self.route(task).estimated_cost

    # --- internals -------------------------------------------------------------

    def _evaluate(self, d: ProviderDescriptor, task: RoutingTask) -> Candidate:
        model = d.default_model(task.capability)
        cand = Candidate(provider=d.name, model=model, eligible=False)
        available, reason = self.registry.availability(d)
        if not available:
            cand.rejection = reason
            return cand
        if d.name in task.exclude:
            cand.rejection = "excluído (falha anterior)"
            return cand
        health = self.registry.health(d.name)
        if health == HealthStatus.DOWN:
            cand.rejection = "provider fora do ar"
            return cand
        missing = sorted(task.required_features - set(d.features))
        if missing:
            cand.rejection = f"não suporta: {', '.join(missing)}"
            return cand
        limits = d.limits
        max_height = limits.max_resolution_height
        if max_height and task.output_height and task.output_height > max_height:
            cand.rejection = f"resolução máxima {max_height}p"
            return cand
        chunks = d.chunks_for(task.duration_sec)
        if chunks > 1 and "chunking" not in d.features:
            cand.rejection = f"duração máxima {limits.max_duration_sec}s"
            return cand
        max_edits = d.params.get("max_edits_per_call")
        if max_edits and task.edit_count > int(max_edits):
            cand.rejection = f"no máximo {max_edits} alterações por chamada"
            return cand

        cost_model = d.cost_for(task.capability)
        rate = self._fx.get(cost_model.currency.upper())
        if rate is None:
            cand.rejection = f"sem taxa de câmbio configurada para {cost_model.currency}"
            return cand
        quantity = task.quantity if task.quantity is not None else task.duration_sec
        cost = cost_model.estimate(quantity, task.output_height)
        if chunks > 1 and cost_model.per_call:
            cost += cost_model.per_call * (chunks - 1)
        cand.estimated_cost = (cost * Decimal(str(rate))).quantize(Decimal("0.0001"))
        cand.estimated_latency_sec = d.latency.estimate(quantity)
        cand.quality = d.quality_for(task.capability)
        successes, total = self._stats(d.name, task.capability.value)
        prior = d.prior_success_rate
        cand.success_rate = (successes + prior * _PRIOR_WEIGHT) / (total + _PRIOR_WEIGHT)
        cand.samples = total
        cand.chunks = chunks
        cand.eligible = True
        if health == HealthStatus.DEGRADED:
            cand.degraded = True
            cand.notes.append("provider degradado (penalizado)")
        return cand

    @staticmethod
    def _score(cands: list[Candidate], mode: QualityMode) -> None:
        """Cost and latency are scored as ratios to the best candidate (cheapest = 1.0,
        twice the price = 0.5), so two candidates are not pushed to the 0/1 extremes.

        Cost is *effective* cost — price divided by success rate — because a cheap
        provider that fails half the time costs double once retries are paid for."""
        weights = WEIGHTS[mode]
        floor = QUALITY_FLOOR[mode]

        def effective(c: Candidate) -> float:
            return float(c.estimated_cost) / max(c.success_rate, 0.05)

        min_cost = min(effective(c) for c in cands)
        min_lat = min(c.estimated_latency_sec for c in cands)
        anyone_meets_floor = any(c.quality >= floor for c in cands)

        def ratio(best: float, value: float) -> float:
            if value <= 0:
                return 1.0
            return max(0.0, min(1.0, best / value)) if best > 0 else 0.0

        for c in cands:
            cost = effective(c)
            cost_score = 1.0 if cost <= 0 or cost == min_cost else ratio(min_cost, cost)
            score = (
                weights["cost"] * cost_score
                + weights["quality"] * c.quality
                + weights["success"] * c.success_rate
                + weights["latency"] * ratio(min_lat, c.estimated_latency_sec)
            )
            if c.quality < floor and anyone_meets_floor:
                score -= _FLOOR_PENALTY
                c.notes.append(f"abaixo da qualidade mínima do modo ({floor:.2f})")
            if c.degraded:
                score -= 0.15
            if c.samples >= _MIN_SAMPLES and c.success_rate < _LOW_SUCCESS:
                score -= _LOW_SUCCESS_PENALTY
                c.notes.append(
                    f"taxa de sucesso baixa ({c.success_rate:.0%} em {c.samples} chamadas)"
                )
            c.score = score
