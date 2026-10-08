"""ORM models.

The original Video DNA is stored twice on purpose:

* `VideoAnalysis.dna` — the immutable JSON snapshot (source of truth for
  `apply_operations`, cheap to version and diff);
* normalized rows (`Scene`, `Shot`, `Entity`, `EntityTrack`, `Action`,
  `Relationship`) — for querying, ownership checks and stable row ids that the
  API exposes (`/entities/{entityId}`).

Both are written in the same transaction by `services.analysis.persistence`.

Entity kinds (Character, Wardrobe, Environment, SceneObject...) and job kinds
(AnalysisJob, GenerationJob...) use single-table inheritance: one table, typed
classes, no joins (ADR 0004).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from videodna.db.base import Base, JSONType, Timestamps, UUIDPk, utcnow
from videodna.domain.enums import (
    AnalysisStatus,
    CostKind,
    EditOpType,
    EditSource,
    EditState,
    EntityType,
    Importance,
    JobKind,
    JobStatus,
    OutputKind,
    PlanStatus,
    ProjectStatus,
    QAIssueStatus,
    QAIssueType,
    QASeverity,
    QualityMode,
    RenderKind,
    SourceVideoStatus,
    UsageStatus,
)


def enum_col(enum_cls: type[StrEnum], **kwargs: Any):
    return mapped_column(
        Enum(
            enum_cls,
            native_enum=False,
            length=32,
            values_callable=lambda e: [m.value for m in e],
            validate_strings=True,
        ),
        **kwargs,
    )


def fk(target: str, *, nullable: bool = False, ondelete: str = "CASCADE", index: bool = True):
    return mapped_column(
        Uuid, ForeignKey(target, ondelete=ondelete), nullable=nullable, index=index
    )


Money = Numeric(14, 4)


# --- users & projects -------------------------------------------------------


class User(UUIDPk, Timestamps, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(120))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Optional spending cap in the base currency. NULL = unlimited.
    budget_limit: Mapped[Decimal | None] = mapped_column(Money)

    projects: Mapped[list[Project]] = relationship(back_populates="owner")


class Project(UUIDPk, Timestamps, Base):
    __tablename__ = "projects"

    owner_id: Mapped[uuid.UUID] = fk("users.id")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = enum_col(ProjectStatus, default=ProjectStatus.DRAFT)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    # Not a FK: avoids a project <-> analysis cycle; integrity kept by services.
    current_analysis_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    duplicated_from_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)

    owner: Mapped[User] = relationship(back_populates="projects")
    source_videos: Mapped[list[SourceVideo]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )


class SourceVideo(UUIDPk, Timestamps, Base):
    __tablename__ = "source_videos"

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[SourceVideoStatus] = enum_col(
        SourceVideoStatus, default=SourceVideoStatus.PENDING_UPLOAD
    )
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    technical: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    proxy_key: Mapped[str | None] = mapped_column(String(512))
    poster_key: Mapped[str | None] = mapped_column(String(512))
    duration_sec: Mapped[float | None] = mapped_column(Float)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    fps: Mapped[float | None] = mapped_column(Float)
    # Multipart upload session (S3 UploadId or local session id).
    upload_id: Mapped[str | None] = mapped_column(String(255), index=True)
    upload_part_size: Mapped[int | None] = mapped_column(Integer)
    upload_part_count: Mapped[int | None] = mapped_column(Integer)
    rights_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rights_statement: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(64))
    retention_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship(back_populates="source_videos")


# --- analysis ------------------------------------------------------------------


class VideoAnalysis(UUIDPk, Timestamps, Base):
    __tablename__ = "video_analyses"

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    source_video_id: Mapped[uuid.UUID] = fk("source_videos.id")
    status: Mapped[AnalysisStatus] = enum_col(AnalysisStatus, default=AnalysisStatus.PENDING)
    pipeline_version: Mapped[str] = mapped_column(String(32), nullable=False)
    mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dna_schema_version: Mapped[str | None] = mapped_column(String(16))
    # The original, immutable Video DNA (camelCase JSON).
    dna: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    summary: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    reused_from_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    low_confidence_count: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Scene(UUIDPk, Base):
    __tablename__ = "scenes"
    __table_args__ = (UniqueConstraint("analysis_id", "key"),)

    analysis_id: Mapped[uuid.UUID] = fk("video_analyses.id")
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    environment_key: Mapped[str | None] = mapped_column(String(64))
    graph: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)


class Shot(UUIDPk, Base):
    __tablename__ = "shots"
    __table_args__ = (UniqueConstraint("analysis_id", "key"),)

    analysis_id: Mapped[uuid.UUID] = fk("video_analyses.id")
    scene_id: Mapped[uuid.UUID | None] = fk("scenes.id", nullable=True)
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    start_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    end_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    transition_in: Mapped[str] = mapped_column(String(16), default="cut")
    camera: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    lighting: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    dominant_colors: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    keyframes: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    thumbnail_key: Mapped[str | None] = mapped_column(String(512))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)


class Entity(UUIDPk, Timestamps, Base):
    __tablename__ = "entities"
    __table_args__ = (
        UniqueConstraint("analysis_id", "key"),
        Index("ix_entities_project_type", "project_id", "type"),
    )

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    analysis_id: Mapped[uuid.UUID] = fk("video_analyses.id")
    scene_id: Mapped[uuid.UUID | None] = fk("scenes.id", nullable=True, ondelete="SET NULL")
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[EntityType] = enum_col(EntityType, nullable=False)
    subtype: Mapped[str | None] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    parent_key: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    importance: Mapped[Importance] = enum_col(Importance, default=Importance.DECORATIVE)
    editable: Mapped[bool] = mapped_column(Boolean, default=True)
    replaceable: Mapped[bool] = mapped_column(Boolean, default=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    # `metadata` is reserved by SQLAlchemy's declarative API.
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONType, default=dict)

    __mapper_args__ = {"polymorphic_on": "type"}

    tracks: Mapped[list[EntityTrack]] = relationship(
        back_populates="entity", cascade="all, delete-orphan", passive_deletes=True
    )


class Character(Entity):
    __mapper_args__ = {"polymorphic_identity": EntityType.CHARACTER}


class Hair(Entity):
    __mapper_args__ = {"polymorphic_identity": EntityType.HAIR}


class Wardrobe(Entity):
    __mapper_args__ = {"polymorphic_identity": EntityType.WARDROBE}


class Accessory(Entity):
    __mapper_args__ = {"polymorphic_identity": EntityType.ACCESSORY}


class SceneObject(Entity):
    """Spec "Object" (named to avoid shadowing a builtin-looking name)."""

    __mapper_args__ = {"polymorphic_identity": EntityType.OBJECT}


class Furniture(Entity):
    __mapper_args__ = {"polymorphic_identity": EntityType.FURNITURE}


class Environment(Entity):
    __mapper_args__ = {"polymorphic_identity": EntityType.ENVIRONMENT}


class EnvironmentPart(Entity):
    __mapper_args__ = {"polymorphic_identity": EntityType.ENVIRONMENT_PART}


class Lighting(Entity):
    __mapper_args__ = {"polymorphic_identity": EntityType.LIGHTING}


class TextElement(Entity):
    __mapper_args__ = {"polymorphic_identity": EntityType.TEXT}


class AudioElement(Entity):
    __mapper_args__ = {"polymorphic_identity": EntityType.AUDIO}


ENTITY_CLASS_BY_TYPE: dict[EntityType, type[Entity]] = {
    EntityType.CHARACTER: Character,
    EntityType.HAIR: Hair,
    EntityType.WARDROBE: Wardrobe,
    EntityType.ACCESSORY: Accessory,
    EntityType.OBJECT: SceneObject,
    EntityType.FURNITURE: Furniture,
    EntityType.ENVIRONMENT: Environment,
    EntityType.ENVIRONMENT_PART: EnvironmentPart,
    EntityType.LIGHTING: Lighting,
    EntityType.TEXT: TextElement,
    EntityType.AUDIO: AudioElement,
}


class EntityTrack(UUIDPk, Base):
    __tablename__ = "entity_tracks"
    __table_args__ = (UniqueConstraint("analysis_id", "key"),)

    analysis_id: Mapped[uuid.UUID] = fk("video_analyses.id")
    entity_id: Mapped[uuid.UUID] = fk("entities.id")
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_key: Mapped[str] = mapped_column(String(64), nullable=False)
    shot_key: Mapped[str] = mapped_column(String(64), nullable=False)
    start_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    end_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    # [{time, frame, bbox{x,y,w,h}, visibility, occluded, confidence, maskKey}]
    samples: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    entity: Mapped[Entity] = relationship(back_populates="tracks")


class Action(UUIDPk, Base):
    __tablename__ = "actions"
    __table_args__ = (UniqueConstraint("analysis_id", "key"),)

    analysis_id: Mapped[uuid.UUID] = fk("video_analyses.id")
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    verb: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_key: Mapped[str | None] = mapped_column(String(64))
    target_keys: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    shot_keys: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    essential: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONType, default=dict)


class Relationship(UUIDPk, Base):
    __tablename__ = "relationships"
    __table_args__ = (UniqueConstraint("analysis_id", "key"),)

    analysis_id: Mapped[uuid.UUID] = fk("video_analyses.id")
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    scene_key: Mapped[str | None] = mapped_column(String(64))
    subject_key: Mapped[str] = mapped_column(String(64), nullable=False)
    predicate: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str] = mapped_column(String(64), nullable=False)
    start_time: Mapped[float | None] = mapped_column(Float)
    end_time: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


# --- editing -------------------------------------------------------------------


class EditOperation(UUIDPk, Timestamps, Base):
    __tablename__ = "edit_operations"
    __table_args__ = (
        UniqueConstraint("project_id", "sequence"),
        Index("ix_edit_operations_project_state", "project_id", "state"),
    )

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    analysis_id: Mapped[uuid.UUID] = fk("video_analyses.id")
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    entity_key: Mapped[str | None] = mapped_column(String(64))
    op: Mapped[EditOpType] = enum_col(EditOpType, nullable=False)
    property: Mapped[str | None] = mapped_column(String(128))
    previous_value: Mapped[Any] = mapped_column(JSONType)
    new_value: Mapped[Any] = mapped_column(JSONType)
    instruction: Mapped[str | None] = mapped_column(Text)
    source: Mapped[EditSource] = enum_col(EditSource, default=EditSource.MANUAL)
    suggestion_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    state: Mapped[EditState] = enum_col(EditState, default=EditState.ACTIVE)
    impact: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    created_by_id: Mapped[uuid.UUID | None] = fk(
        "users.id", nullable=True, ondelete="SET NULL", index=False
    )


class Suggestion(UUIDPk, Base):
    __tablename__ = "suggestions"
    __table_args__ = (
        Index(
            "ix_suggestions_lookup", "analysis_id", "entity_key", "category", "context_hash", "page"
        ),
    )

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    analysis_id: Mapped[uuid.UUID] = fk("video_analyses.id")
    entity_key: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    context_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    page: Mapped[int] = mapped_column(Integer, default=0)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    op: Mapped[EditOpType] = enum_col(EditOpType, nullable=False)
    property: Mapped[str | None] = mapped_column(String(128))
    value: Mapped[Any] = mapped_column(JSONType)
    tags: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    preview_key: Mapped[str | None] = mapped_column(String(512))
    provider: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# --- generation ----------------------------------------------------------------


class GenerationPlan(UUIDPk, Timestamps, Base):
    __tablename__ = "generation_plans"

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    analysis_id: Mapped[uuid.UUID] = fk("video_analyses.id")
    status: Mapped[PlanStatus] = enum_col(PlanStatus, default=PlanStatus.DRAFT)
    quality_mode: Mapped[QualityMode] = enum_col(QualityMode, default=QualityMode.BALANCED)
    render_kind: Mapped[RenderKind] = enum_col(RenderKind, default=RenderKind.PREVIEW)
    ops_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    plan: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    estimated_cost: Mapped[Decimal] = mapped_column(Money, default=Decimal(0))
    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    expected_duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    blocking: Mapped[bool] = mapped_column(Boolean, default=False)


class Job(UUIDPk, Timestamps, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("project_id", "kind", "idempotency_key", name="uq_jobs_idempotency"),
        Index("ix_jobs_project_status", "project_id", "status"),
    )

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    user_id: Mapped[uuid.UUID | None] = fk("users.id", nullable=True, ondelete="SET NULL")
    kind: Mapped[JobKind] = enum_col(JobKind, nullable=False)
    status: Mapped[JobStatus] = enum_col(JobStatus, default=JobStatus.QUEUED)
    stage: Mapped[str | None] = mapped_column(String(64))
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    message: Mapped[str | None] = mapped_column(String(500))
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    result: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(500))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    plan_id: Mapped[uuid.UUID | None] = fk(
        "generation_plans.id", nullable=True, ondelete="SET NULL"
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __mapper_args__ = {"polymorphic_on": "kind"}


class IngestJob(Job):
    __mapper_args__ = {"polymorphic_identity": JobKind.INGEST}


class AnalysisJob(Job):
    __mapper_args__ = {"polymorphic_identity": JobKind.ANALYSIS}


class PreviewJob(Job):
    __mapper_args__ = {"polymorphic_identity": JobKind.PREVIEW}


class GenerationJob(Job):
    __mapper_args__ = {"polymorphic_identity": JobKind.GENERATION}


JOB_CLASS_BY_KIND: dict[JobKind, type[Job]] = {
    JobKind.INGEST: IngestJob,
    JobKind.ANALYSIS: AnalysisJob,
    JobKind.PREVIEW: PreviewJob,
    JobKind.GENERATION: GenerationJob,
}


class JobEvent(Base):
    __tablename__ = "job_events"
    __table_args__ = (UniqueConstraint("job_id", "seq"),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    job_id: Mapped[uuid.UUID] = fk("jobs.id")
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[str] = mapped_column(String(16), default="info")
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(64))
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    message: Mapped[str | None] = mapped_column(String(500))
    data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GenerationOutput(UUIDPk, Base):
    __tablename__ = "generation_outputs"

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    job_id: Mapped[uuid.UUID | None] = fk("jobs.id", nullable=True)
    version_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    kind: Mapped[OutputKind] = enum_col(OutputKind, nullable=False)
    shot_key: Mapped[str | None] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_sec: Mapped[float | None] = mapped_column(Float)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(128))
    # sourceAssetId, generationId, providers, date, transformations (spec §53).
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class QAReport(UUIDPk, Base):
    __tablename__ = "qa_reports"

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    job_id: Mapped[uuid.UUID] = fk("jobs.id")
    shot_key: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str | None] = mapped_column(Text)
    checks: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    issues: Mapped[list[QAIssue]] = relationship(
        back_populates="report", cascade="all, delete-orphan", passive_deletes=True
    )


class QAIssue(UUIDPk, Timestamps, Base):
    __tablename__ = "qa_issues"

    report_id: Mapped[uuid.UUID] = fk("qa_reports.id")
    project_id: Mapped[uuid.UUID] = fk("projects.id")
    job_id: Mapped[uuid.UUID] = fk("jobs.id")
    shot_key: Mapped[str] = mapped_column(String(64), nullable=False)
    issue_type: Mapped[QAIssueType] = enum_col(QAIssueType, nullable=False)
    severity: Mapped[QASeverity] = enum_col(QASeverity, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_entity_key: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[QAIssueStatus] = enum_col(QAIssueStatus, default=QAIssueStatus.OPEN)
    repair_attempts: Mapped[int] = mapped_column(Integer, default=0)

    report: Mapped[QAReport] = relationship(back_populates="issues")


class ProjectVersion(UUIDPk, Base):
    __tablename__ = "project_versions"
    __table_args__ = (UniqueConstraint("project_id", "number"),)

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    analysis_id: Mapped[uuid.UUID] = fk("video_analyses.id")
    operations: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    job_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    output_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# --- cost & observability ---------------------------------------------------------


class ProviderUsage(UUIDPk, Base):
    __tablename__ = "provider_usage"
    __table_args__ = (Index("ix_provider_usage_provider_capability", "provider", "capability"),)

    project_id: Mapped[uuid.UUID | None] = fk("projects.id", nullable=True)
    user_id: Mapped[uuid.UUID | None] = fk("users.id", nullable=True, ondelete="SET NULL")
    job_id: Mapped[uuid.UUID | None] = fk("jobs.id", nullable=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128))
    capability: Mapped[str] = mapped_column(String(64), nullable=False)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[UsageStatus] = enum_col(UsageStatus, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64))
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Money)
    actual_cost: Mapped[Decimal | None] = mapped_column(Money)
    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    tokens: Mapped[int | None] = mapped_column(Integer)
    credits: Mapped[float | None] = mapped_column(Float)
    seconds_generated: Mapped[float | None] = mapped_column(Float)
    shot_key: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class CostEntry(UUIDPk, Base):
    __tablename__ = "cost_entries"

    project_id: Mapped[uuid.UUID] = fk("projects.id")
    user_id: Mapped[uuid.UUID | None] = fk("users.id", nullable=True, ondelete="SET NULL")
    job_id: Mapped[uuid.UUID | None] = fk("jobs.id", nullable=True)
    plan_id: Mapped[uuid.UUID | None] = fk(
        "generation_plans.id", nullable=True, ondelete="SET NULL"
    )
    provider_usage_id: Mapped[uuid.UUID | None] = fk(
        "provider_usage.id", nullable=True, ondelete="SET NULL"
    )
    kind: Mapped[CostKind] = enum_col(CostKind, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128))
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str] = mapped_column(String(32), default="call")
    seconds_generated: Mapped[float | None] = mapped_column(Float)
    tokens: Mapped[int | None] = mapped_column(Integer)
    credits: Mapped[float | None] = mapped_column(Float)
    shot_key: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
