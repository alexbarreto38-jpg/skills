"""Projects: CRUD, privacy-preserving deletion and duplication."""

from __future__ import annotations

import json
import uuid
from decimal import Decimal

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from videodna.api import schemas as s
from videodna.db import models as m
from videodna.domain.enums import (
    TERMINAL_JOB_STATUSES,
    CostKind,
    EditState,
    JobKind,
    OutputKind,
    ProjectStatus,
    SourceVideoStatus,
)
from videodna.domain.settings import ProjectSettings
from videodna.errors import AppError, ErrorCode
from videodna.logging_setup import get_logger
from videodna.runtime import Runtime
from videodna.services.analysis.persistence import dna_from_json, persist_dna
from videodna.services.media_urls import signed
from videodna.storage.base import project_prefix

log = get_logger(__name__)


def settings_of(project: m.Project) -> ProjectSettings:
    return ProjectSettings.model_validate(project.settings or {})


def create_project(db: Session, user: m.User, data: s.ProjectCreate) -> m.Project:
    project = m.Project(
        owner_id=user.id,
        name=data.name.strip(),
        description=data.description,
        settings=(data.settings or ProjectSettings()).model_dump(mode="json", by_alias=True),
        status=ProjectStatus.DRAFT,
    )
    db.add(project)
    db.flush()
    return project


def update_project(db: Session, project: m.Project, data: s.ProjectUpdate) -> m.Project:
    if data.name is not None:
        project.name = data.name.strip()
    if data.description is not None:
        project.description = data.description
    if data.settings is not None:
        project.settings = data.settings.model_dump(mode="json", by_alias=True)
    db.flush()
    return project


def latest_source(db: Session, project_id: uuid.UUID) -> m.SourceVideo | None:
    return db.scalars(
        select(m.SourceVideo)
        .where(
            m.SourceVideo.project_id == project_id,
            m.SourceVideo.status != SourceVideoStatus.DELETED,
        )
        .order_by(m.SourceVideo.created_at.desc())
    ).first()


def source_out(runtime: Runtime, source: m.SourceVideo) -> s.SourceVideoOut:
    out = s.SourceVideoOut.model_validate(source)
    out.proxy_url = signed(runtime, source.proxy_key, content_type="video/mp4")
    out.poster_url = signed(runtime, source.poster_key, content_type="image/jpeg")
    return out


def project_out(db: Session, runtime: Runtime, project: m.Project) -> s.ProjectOut:
    source = latest_source(db, project.id)
    analysis = (
        db.get(m.VideoAnalysis, project.current_analysis_id)
        if project.current_analysis_id
        else None
    )
    active = db.scalars(
        select(m.Job)
        .where(m.Job.project_id == project.id, m.Job.status.not_in(TERMINAL_JOB_STATUSES))
        .order_by(m.Job.created_at.desc())
    ).first()
    if active is None:
        latest_analysis_job = db.scalars(
            select(m.Job)
            .where(m.Job.project_id == project.id, m.Job.kind == JobKind.ANALYSIS)
            .order_by(m.Job.created_at.desc())
        ).first()
        if latest_analysis_job is not None and project.status == ProjectStatus.FAILED:
            active = latest_analysis_job
    latest_output = db.scalars(
        select(m.GenerationOutput.id)
        .where(
            m.GenerationOutput.project_id == project.id,
            m.GenerationOutput.kind.in_([OutputKind.FINAL, OutputKind.PREVIEW]),
        )
        .order_by(m.GenerationOutput.created_at.desc())
    ).first()
    edit_count = db.scalar(
        select(func.count())
        .select_from(m.EditOperation)
        .where(m.EditOperation.project_id == project.id, m.EditOperation.state == EditState.ACTIVE)
    )
    total = db.scalar(
        select(func.coalesce(func.sum(m.CostEntry.amount), 0)).where(
            m.CostEntry.project_id == project.id, m.CostEntry.kind == CostKind.ACTUAL
        )
    )
    return s.ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        settings=settings_of(project),
        created_at=project.created_at,
        updated_at=project.updated_at,
        source_video=source_out(runtime, source) if source else None,
        analysis=s.AnalysisOut.model_validate(analysis) if analysis else None,
        active_job=s.JobOut.model_validate(active) if active else None,
        latest_output_id=latest_output,
        edit_count=edit_count or 0,
        total_cost=round(float(total or Decimal(0)), 2),
        currency=runtime.settings.cost_currency,
    )


def list_projects(db: Session, user: m.User) -> list[m.Project]:
    return list(
        db.scalars(
            select(m.Project)
            .where(m.Project.owner_id == user.id)
            .order_by(m.Project.updated_at.desc())
        )
    )


def delete_project(db: Session, runtime: Runtime, project: m.Project) -> int:
    """Hard delete: media first (storage prefix), then every row (FK cascade)."""
    running = db.scalar(
        select(func.count())
        .select_from(m.Job)
        .where(m.Job.project_id == project.id, m.Job.status.not_in(TERMINAL_JOB_STATUSES))
    )
    if running:
        db.execute(
            update(m.Job)
            .where(m.Job.project_id == project.id, m.Job.status.not_in(TERMINAL_JOB_STATUSES))
            .values(cancel_requested=True)
        )
    removed = runtime.storage.delete_prefix(project_prefix(project.id))
    db.execute(delete(m.Project).where(m.Project.id == project.id))
    log.info("project deleted", extra={"project_id": str(project.id), "objects_removed": removed})
    return removed


def delete_media(db: Session, runtime: Runtime, project: m.Project) -> int:
    """Remove all media (source, proxies, keyframes, outputs) but keep the
    project's metadata and edit history."""
    removed = runtime.storage.delete_prefix(project_prefix(project.id))
    for source in db.scalars(select(m.SourceVideo).where(m.SourceVideo.project_id == project.id)):
        source.status = SourceVideoStatus.DELETED
        source.proxy_key = None
        source.poster_key = None
    db.execute(delete(m.GenerationOutput).where(m.GenerationOutput.project_id == project.id))
    db.flush()
    return removed


def _remap(value: str | None, mapping: dict[str, str]) -> str | None:
    if value is None:
        return None
    for old, new in mapping.items():
        value = value.replace(old, new)
    return value


def duplicate_project(db: Session, runtime: Runtime, user: m.User, project: m.Project) -> m.Project:
    """Copy metadata, media, analysis rows and active edits into a new project.

    Media is copied (not shared) so deleting either project can never break
    the other — deletion is a privacy guarantee, not a best effort."""
    if project.current_analysis_id is None:
        raise AppError(ErrorCode.ANALYSIS_REQUIRED)
    clone = m.Project(
        owner_id=user.id,
        name=f"{project.name} (cópia)",
        description=project.description,
        settings=dict(project.settings or {}),
        status=ProjectStatus.READY,
        duplicated_from_id=project.id,
    )
    db.add(clone)
    db.flush()
    source = latest_source(db, project.id)
    analysis = db.get(m.VideoAnalysis, project.current_analysis_id)
    if source is None or analysis is None:
        raise AppError(ErrorCode.ANALYSIS_REQUIRED)
    new_source = m.SourceVideo(
        project_id=clone.id,
        **{
            c: getattr(source, c)
            for c in (
                "original_filename",
                "content_type",
                "size_bytes",
                "storage_key",
                "status",
                "content_hash",
                "technical",
                "proxy_key",
                "poster_key",
                "duration_sec",
                "width",
                "height",
                "fps",
                "rights_confirmed_at",
                "rights_statement",
                "retention_until",
            )
        },
    )
    db.add(new_source)
    db.flush()
    new_analysis = m.VideoAnalysis(
        project_id=clone.id,
        source_video_id=new_source.id,
        status=analysis.status,
        pipeline_version=analysis.pipeline_version,
        mock=analysis.mock,
        reused_from_id=analysis.id,
    )
    db.add(new_analysis)
    db.flush()

    old_root, new_root = f"projects/{project.id}", f"projects/{clone.id}"
    mapping = {
        f"{old_root}/source/{source.id}/": f"{new_root}/source/{new_source.id}/",
        f"{old_root}/analysis/{analysis.id}/": f"{new_root}/analysis/{new_analysis.id}/",
    }
    for old_prefix in mapping:
        for key in runtime.storage.list_keys(old_prefix):
            runtime.storage.copy(key, _remap(key, mapping))
    new_source.storage_key = _remap(source.storage_key, mapping)
    new_source.proxy_key = _remap(source.proxy_key, mapping)
    new_source.poster_key = _remap(source.poster_key, mapping)

    dna_text = _remap(json.dumps(analysis.dna), mapping)
    dna = dna_from_json(json.loads(dna_text)).model_copy(
        update={"source_video_id": str(new_source.id)}
    )
    persist_dna(db, new_analysis, dna)
    clone.current_analysis_id = new_analysis.id
    ops = db.scalars(
        select(m.EditOperation)
        .where(m.EditOperation.project_id == project.id, m.EditOperation.state == EditState.ACTIVE)
        .order_by(m.EditOperation.sequence)
    ).all()
    for i, op in enumerate(ops, start=1):
        db.add(
            m.EditOperation(
                project_id=clone.id,
                analysis_id=new_analysis.id,
                sequence=i,
                entity_key=op.entity_key,
                op=op.op,
                property=op.property,
                previous_value=op.previous_value,
                new_value=op.new_value,
                instruction=op.instruction,
                source=op.source,
                state=EditState.ACTIVE,
                impact=op.impact,
                created_by_id=user.id,
            )
        )
    db.flush()
    return clone
