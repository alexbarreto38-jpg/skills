"""API contract (request/response models).

This module plus the domain models it references (VideoDNA, ImpactReport,
GenerationPlanSpec...) *is* the OpenAPI contract the TypeScript client is
generated from. Field names are camelCase on the wire.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel

from videodna.domain.enums import (
    AnalysisStatus,
    EditOpType,
    EditSource,
    EditState,
    EntityType,
    Importance,
    JobKind,
    JobStatus,
    OutputKind,
    ProjectStatus,
    QAIssueStatus,
    QASeverity,
    QualityMode,
    RenderKind,
    SourceVideoStatus,
)
from videodna.domain.impact import ImpactReport
from videodna.domain.settings import ProjectSettings
from videodna.domain.video_dna import Appearance, Entity, EntityAlternative, VideoDNA


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        serialize_by_alias=True,
        json_schema_serialization_defaults_required=True,
    )


# --- errors ----------------------------------------------------------------------


class ErrorBody(ApiModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


class ErrorResponse(ApiModel):
    error: ErrorBody


# --- auth ----------------------------------------------------------------------------


class RegisterRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=120)


class LoginRequest(ApiModel):
    email: EmailStr
    password: str


class UserOut(ApiModel):
    id: uuid.UUID
    email: str
    display_name: str | None = None
    is_admin: bool = False


class TokenResponse(ApiModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


# --- jobs --------------------------------------------------------------------------------


class JobOut(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    kind: JobKind
    status: JobStatus
    stage: str | None = None
    progress: float = 0.0
    message: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    plan_id: uuid.UUID | None = None
    attempts: int = 0
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class JobEventOut(ApiModel):
    seq: int
    status: str
    stage: str | None = None
    progress: float
    message: str | None = None
    level: str = "info"
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


# --- projects & media ------------------------------------------------------------------


class ProjectCreate(ApiModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    settings: ProjectSettings | None = None


class ProjectUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    settings: ProjectSettings | None = None


class SourceVideoOut(ApiModel):
    id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int
    status: SourceVideoStatus
    duration_sec: float | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    error_code: str | None = None
    rights_confirmed_at: datetime | None = None
    proxy_url: str | None = None
    poster_url: str | None = None
    retention_until: datetime | None = None


class AnalysisOut(ApiModel):
    id: uuid.UUID
    status: AnalysisStatus
    pipeline_version: str
    mock: bool
    summary: dict[str, Any] = Field(default_factory=dict)
    low_confidence_count: int = 0
    reused_from_id: uuid.UUID | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ProjectOut(ApiModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    status: ProjectStatus
    settings: ProjectSettings
    created_at: datetime
    updated_at: datetime
    source_video: SourceVideoOut | None = None
    analysis: AnalysisOut | None = None
    active_job: JobOut | None = None
    latest_output_id: uuid.UUID | None = None
    edit_count: int = 0
    total_cost: float = 0.0
    currency: str = "BRL"


# --- uploads ---------------------------------------------------------------------------


class UploadInitRequest(ApiModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    size_bytes: int = Field(gt=0)
    rights_confirmed: bool
    rights_statement: str | None = Field(default=None, max_length=1000)


class UploadPartUrl(ApiModel):
    part_number: int
    url: str


class UploadInitResponse(ApiModel):
    upload_id: str
    source_video_id: uuid.UUID
    part_size: int
    part_count: int
    parts: list[UploadPartUrl]
    expires_in_sec: int


class UploadedPart(ApiModel):
    part_number: int
    etag: str
    size: int | None = None


class UploadStatusResponse(ApiModel):
    upload_id: str
    source_video_id: uuid.UUID
    part_count: int
    part_size: int
    uploaded_parts: list[UploadedPart]
    parts: list[UploadPartUrl]


class UploadCompleteRequest(ApiModel):
    parts: list[UploadedPart]
    analyze: bool = True


class UploadCompleteResponse(ApiModel):
    source_video: SourceVideoOut
    job: JobOut | None = None


class AnalyzeRequest(ApiModel):
    force: bool = False


# --- entities & DNA ------------------------------------------------------------------------


class EditCategoryOut(ApiModel):
    id: str
    label: str
    op: EditOpType
    property: str | None = None
    display: Literal["cards", "swatches"] = "cards"


class EntityOut(ApiModel):
    id: uuid.UUID
    key: str
    type: EntityType
    subtype: str | None = None
    label: str
    description: str | None = None
    parent_key: str | None = None
    confidence: float
    importance: Importance
    editable: bool
    replaceable: bool
    needs_review: bool
    attributes: dict[str, Any] = Field(default_factory=dict)
    alternatives: list[EntityAlternative] = Field(default_factory=list)
    appearances: list[Appearance] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    current: Entity | None = None
    categories: list[EditCategoryOut] = Field(default_factory=list)
    quick_actions: list[str] = Field(default_factory=list)


class VideoDNAResponse(ApiModel):
    analysis_id: uuid.UUID
    view: Literal["original", "current"]
    edit_count: int
    dna: VideoDNA
    asset_urls: dict[str, str] = Field(default_factory=dict)


class EntityCorrection(ApiModel):
    """Manual correction of an uncertain analysis ("Copo / Taça?")."""

    property: Literal["label", "type", "subtype", "importance", "description"]
    value: Any


# --- edits ------------------------------------------------------------------------------------


class EditCreate(ApiModel):
    entity_key: str | None = None
    entity_id: uuid.UUID | None = None
    op: EditOpType
    property: str | None = Field(default=None, max_length=128)
    new_value: Any = None
    instruction: str | None = Field(default=None, max_length=2000)
    source: EditSource = EditSource.MANUAL
    suggestion_id: uuid.UUID | None = None


class EditOut(ApiModel):
    id: uuid.UUID
    sequence: int
    entity_key: str | None = None
    op: EditOpType
    property: str | None = None
    previous_value: Any = None
    new_value: Any = None
    instruction: str | None = None
    source: EditSource
    state: EditState
    impact: dict[str, Any] = Field(default_factory=dict)
    suggestion_id: uuid.UUID | None = None
    created_at: datetime


class EditHistoryOut(ApiModel):
    edits: list[EditOut]
    can_undo: bool
    can_redo: bool


class EditResult(ApiModel):
    edit: EditOut | None = None
    impact: ImpactReport | None = None
    history: EditHistoryOut


# --- suggestions ------------------------------------------------------------------------------


class SuggestionOut(ApiModel):
    id: uuid.UUID
    entity_key: str
    category: str
    label: str
    description: str | None = None
    op: EditOpType
    property: str | None = None
    value: Any = None
    tags: list[str] = Field(default_factory=list)
    score: float
    page: int
    rank: int
    preview_url: str | None = None
    provider: str | None = None


class SuggestionList(ApiModel):
    entity_key: str
    category: str
    page: int
    cached: bool
    items: list[SuggestionOut]


# --- plans & generation ---------------------------------------------------------------------


class PlanRequest(ApiModel):
    quality_mode: QualityMode | None = None
    render_kind: RenderKind = RenderKind.PREVIEW


class PlanOut(ApiModel):
    id: uuid.UUID | None = None
    status: str
    quality_mode: QualityMode
    render_kind: RenderKind
    estimated_cost: float
    currency: str
    expected_duration_sec: float
    blocking: bool
    stale: bool = False
    ops_fingerprint: str
    plan: dict[str, Any]
    created_at: datetime | None = None


class GenerateRequest(ApiModel):
    plan_id: uuid.UUID
    idempotency_key: str | None = Field(default=None, max_length=200)
    accept_warnings: bool = False


class PreviewRequest(ApiModel):
    shot_key: str | None = None


# --- outputs, QA, versions ----------------------------------------------------------------


class OutputOut(ApiModel):
    id: uuid.UUID
    job_id: uuid.UUID | None = None
    kind: OutputKind
    shot_key: str | None = None
    url: str = ""
    download_url: str | None = None
    content_type: str
    duration_sec: float | None = None
    width: int | None = None
    height: int | None = None
    size_bytes: int | None = None
    attempt: int = 0
    provider: str | None = None
    model: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class QAIssueOut(ApiModel):
    id: uuid.UUID
    shot_key: str
    issue_type: str
    severity: QASeverity
    start_time: float
    end_time: float
    description: str
    affected_entity_key: str | None = None
    status: QAIssueStatus
    repair_attempts: int


class QAReportOut(ApiModel):
    id: uuid.UUID
    shot_key: str
    attempt: int
    provider: str
    passed: bool
    score: float
    summary: str | None = None
    checks: list[dict[str, Any]] = Field(default_factory=list)
    issues: list[QAIssueOut] = Field(default_factory=list)
    created_at: datetime


class VersionCreate(ApiModel):
    name: str = Field(min_length=1, max_length=200)


class VersionOut(ApiModel):
    id: uuid.UUID
    number: int
    name: str
    operation_count: int
    job_id: uuid.UUID | None = None
    output_id: uuid.UUID | None = None
    created_at: datetime


class CostSummaryOut(ApiModel):
    currency: str
    estimated_total: float
    actual_total: float
    by_provider: list[dict[str, Any]]
    by_job: list[dict[str, Any]]
    seconds_generated: float


# --- config ---------------------------------------------------------------------------------


class AppConfigOut(ApiModel):
    app_name: str
    mock_mode: bool
    environment: str
    currency: str
    low_confidence_threshold: float
    quality_modes: list[QualityMode]
    default_quality_mode: QualityMode
    features: dict[str, bool]
    upload_max_bytes: int
    upload_allowed_content_types: list[str]
    video_max_duration_sec: float
    rights_statement: str


class ProviderOut(ApiModel):
    name: str
    kind: str
    description: str
    mock: bool
    local: bool
    enabled: bool
    disabled_reason: str | None = None
    priority: int
    capabilities: list[str]
    features: list[str]
    health: str | None = None
    models: list[str]


class MetricsOut(ApiModel):
    currency: str
    projects: int
    videos_processed: int
    analyses_completed: int
    generations: dict[str, int]
    total_cost: float
    avg_generation_sec: float | None = None
    retries: int
    qa_failures: int
    providers: list[dict[str, Any]]
    cost_by_day: list[dict[str, Any]]


def money(value: Decimal | float | None) -> float:
    return round(float(value or 0), 2)
