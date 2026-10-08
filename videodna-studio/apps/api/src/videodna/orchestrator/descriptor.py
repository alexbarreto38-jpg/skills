"""Provider descriptors: what a provider can do, its limits and its cost model.

Loaded from `config/providers.yaml`. Numbers for real providers must come from
their official documentation/pricing pages — never guessed (spec §103). The
bundled mock providers use explicitly fictitious values.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from videodna.orchestrator.capabilities import Capability, ProviderKind

CostUnit = Literal["second", "minute", "image", "call", "1k_tokens", "credit"]


class CostModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unit: CostUnit = "call"
    amount: Decimal = Decimal(0)
    currency: str = "BRL"
    per_call: Decimal = Decimal(0)
    minimum: Decimal = Decimal(0)
    # {output height: multiplier}; the smallest key >= requested height wins.
    resolution_multipliers: dict[int, float] = Field(default_factory=dict)

    def multiplier_for(self, height: int | None) -> float:
        if not height or not self.resolution_multipliers:
            return 1.0
        for threshold in sorted(self.resolution_multipliers):
            if height <= threshold:
                return self.resolution_multipliers[threshold]
        return self.resolution_multipliers[max(self.resolution_multipliers)]

    def estimate(self, quantity: float, height: int | None = None) -> Decimal:
        if self.unit == "minute":
            quantity = quantity / 60.0
        variable = self.amount * Decimal(str(quantity)) * Decimal(str(self.multiplier_for(height)))
        total = max(self.minimum, self.per_call + variable)
        return total.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


class Limits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_duration_sec: float | None = None
    max_resolution_height: int | None = None
    max_images: int | None = None
    max_concurrency: int = 4
    timeout_sec: float | None = None


class LatencyModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_sec: float = 1.0
    per_unit_sec: float = 0.0

    def estimate(self, quantity: float) -> float:
        return self.base_sec + self.per_unit_sec * quantity


class ModelSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    default: bool = False
    capabilities: list[Capability] | None = None
    quality: dict[str, float] = Field(default_factory=dict)


class ProviderDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    kind: ProviderKind
    adapter: str  # "package.module:ClassName"
    description: str = ""
    mock: bool = False
    local: bool = False  # deterministic, runs on our own infra (FFmpeg etc.)
    enabled: bool = True
    priority: int = 50
    capabilities: list[Capability]
    features: list[str] = Field(default_factory=list)
    quality: dict[str, float] = Field(default_factory=dict)  # capability -> 0..1, "default"
    cost: CostModel = Field(default_factory=CostModel)
    cost_by_capability: dict[str, CostModel] = Field(default_factory=dict)
    limits: Limits = Field(default_factory=Limits)
    latency: LatencyModel = Field(default_factory=LatencyModel)
    models: list[ModelSpec] = Field(default_factory=list)
    prior_success_rate: float = 0.9
    requires_flag: str | None = None
    docs_url: str | None = None
    # Names of the environment variables holding this provider's secrets. Only
    # the names live here; values are read by the adapter on the server, never
    # stored in config and never sent to the browser.
    credentials_env: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _real_providers_cite_their_docs(self) -> ProviderDescriptor:
        # Limits and prices of a real vendor are copied from its official pages;
        # requiring the link keeps that source next to the numbers.
        if not (self.mock or self.local) and not self.docs_url:
            raise ValueError(f"provider {self.name}: real providers must set docs_url")
        return self

    def supports(self, capability: Capability) -> bool:
        return capability in self.capabilities

    def quality_for(self, capability: Capability) -> float:
        return float(self.quality.get(capability.value, self.quality.get("default", 0.5)))

    def cost_for(self, capability: Capability) -> CostModel:
        return self.cost_by_capability.get(capability.value, self.cost)

    def default_model(self, capability: Capability | None = None) -> str | None:
        candidates = [
            m
            for m in self.models
            if capability is None or m.capabilities is None or capability in m.capabilities
        ]
        if not candidates:
            return None
        return next((m.id for m in candidates if m.default), candidates[0].id)

    def chunks_for(self, duration_sec: float) -> int:
        limit = self.limits.max_duration_sec
        if not limit or duration_sec <= limit:
            return 1
        return math.ceil(duration_sec / limit)
