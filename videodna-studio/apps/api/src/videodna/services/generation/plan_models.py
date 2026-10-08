"""Generation Plan document (stored as JSON on GenerationPlan.plan)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from videodna.domain.enums import QualityMode, RenderKind, Strategy
from videodna.domain.impact import Dependency, ImpactReport
from videodna.domain.operations import OperationSpec
from videodna.domain.settings import ProjectLocks


class _Model(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
        json_schema_serialization_defaults_required=True,
    )


class PlannedEdit(_Model):
    operation_id: str
    entity_key: str | None
    entity_label: str
    change_kind: str
    description: str


class PreStep(_Model):
    kind: str  # SEGMENTATION
    entity_keys: list[str]
    provider: str | None = None
    model: str | None = None
    estimated_cost: float = 0.0


class GenerationStep(_Model):
    strategy: Strategy
    capability: str
    provider: str
    model: str | None = None
    chunks: int = 1
    edit_operation_ids: list[str]
    required_features: list[str] = Field(default_factory=list)
    estimated_cost: float
    estimated_latency_sec: float
    routing: dict[str, Any] = Field(default_factory=dict)


class ShotPlan(_Model):
    shot_key: str
    index: int
    start_time: float
    end_time: float
    duration: float
    strategy: Strategy
    complexity: int = 0
    edits: list[PlannedEdit] = Field(default_factory=list)
    steps: list[GenerationStep] = Field(default_factory=list)
    pre_steps: list[PreStep] = Field(default_factory=list)
    dependencies: list[Dependency] = Field(default_factory=list)
    reference_packs: list[str] = Field(default_factory=list)
    qa_provider: str | None = None
    qa_estimated_cost: float = 0.0
    estimated_cost: float = 0.0
    expected_duration_sec: float = 0.0


class ReferencePackPlan(_Model):
    id: str
    kind: str  # character | scene
    entity_key: str
    label: str
    description: str
    shot_keys: list[str]
    images: int
    provider: str | None = None
    estimated_cost: float = 0.0


class PlanWarning(_Model):
    code: str
    message: str
    blocking: bool = False
    entity_key: str | None = None


class CostLine(_Model):
    label: str
    provider: str | None = None
    amount: float


class PlanSummary(_Model):
    total_shots: int
    affected_shots: int
    passthrough_shots: int
    generations: int
    edit_count: int
    strategies: dict[str, int]


class GenerationPlanSpec(_Model):
    project_id: str
    analysis_id: str
    quality_mode: QualityMode
    render_kind: RenderKind
    output_height: int
    resolution_label: str
    locks: ProjectLocks
    operations: list[OperationSpec]
    summary: PlanSummary
    shots: list[ShotPlan]
    reference_packs: list[ReferencePackPlan] = Field(default_factory=list)
    impacts: list[ImpactReport] = Field(default_factory=list)
    warnings: list[PlanWarning] = Field(default_factory=list)
    blocking: bool = False
    max_retries: int
    estimated_cost: float
    estimated_cost_with_repairs: float
    currency: str
    expected_duration_sec: float
    cost_breakdown: list[CostLine] = Field(default_factory=list)
    providers: list[str] = Field(default_factory=list)
    ops_fingerprint: str
