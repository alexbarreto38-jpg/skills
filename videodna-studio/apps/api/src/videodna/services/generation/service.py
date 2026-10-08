"""Plan persistence, generation start (idempotent, budget-checked) and outputs."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from videodna.api import schemas as s
from videodna.db import models as m
from videodna.domain.enums import CostKind, JobKind, OutputKind, PlanStatus
from videodna.errors import PLAN_GONE, AppError, ErrorCode, NotFound
from videodna.jobs.service import create_job
from videodna.runtime import Runtime
from videodna.services.generation.plan_models import GenerationPlanSpec
from videodna.services.generation.planner import (
    build_plan,
    current_fingerprint,
    nothing_to_generate,
)
from videodna.services.media_urls import signed
from videodna.services.projects import settings_of

# The downloaded file lands in the user's Downloads folder: name it in Portuguese.
_FILE_WORD: dict[OutputKind, str] = {
    OutputKind.PREVIEW: "previa",
    OutputKind.FINAL: "final",
    OutputKind.SHOT_SEGMENT: "cena",
    OutputKind.IMAGE_PREVIEW: "foto",
    OutputKind.REFERENCE_IMAGE: "referencia",
    OutputKind.PROVENANCE: "origem",
}


def plan_to_out(
    spec: GenerationPlanSpec, row: m.GenerationPlan | None, *, stale: bool = False
) -> s.PlanOut:
    return s.PlanOut(
        id=row.id if row else None,
        status=row.status.value if row else "ESTIMATE",
        quality_mode=spec.quality_mode,
        render_kind=spec.render_kind,
        estimated_cost=spec.estimated_cost,
        currency=spec.currency,
        expected_duration_sec=spec.expected_duration_sec,
        blocking=spec.blocking,
        stale=stale,
        ops_fingerprint=spec.ops_fingerprint,
        plan=spec.model_dump(mode="json", by_alias=True),
        created_at=row.created_at if row else None,
    )


def create_plan(
    db: Session,
    runtime: Runtime,
    user: m.User,
    project: m.Project,
    req: s.PlanRequest,
    *,
    persist: bool = True,
) -> tuple[GenerationPlanSpec, m.GenerationPlan | None]:
    mode = req.quality_mode or settings_of(project).quality_mode
    spec = build_plan(db, runtime, user, project, quality_mode=mode, render_kind=req.render_kind)
    if not persist:
        return spec, None
    row = m.GenerationPlan(
        project_id=project.id,
        analysis_id=uuid.UUID(spec.analysis_id),
        status=PlanStatus.DRAFT,
        quality_mode=spec.quality_mode,
        render_kind=spec.render_kind,
        ops_fingerprint=spec.ops_fingerprint,
        plan=spec.model_dump(mode="json", by_alias=True),
        estimated_cost=Decimal(str(spec.estimated_cost)),
        currency=spec.currency,
        expected_duration_sec=spec.expected_duration_sec,
        blocking=spec.blocking,
    )
    db.add(row)
    db.flush()
    return spec, row


def get_plan(
    db: Session, project: m.Project, plan_id: uuid.UUID
) -> tuple[m.GenerationPlan, GenerationPlanSpec, bool]:
    row = db.get(m.GenerationPlan, plan_id)
    if row is None or row.project_id != project.id:
        raise NotFound(PLAN_GONE)
    spec = GenerationPlanSpec.model_validate(row.plan)
    stale = (
        current_fingerprint(db, project, row.quality_mode, row.render_kind) != row.ops_fingerprint
    )
    return row, spec, stale


def start_generation(
    db: Session,
    user: m.User,
    project: m.Project,
    plan_id: uuid.UUID,
    idempotency_key: str | None,
) -> tuple[m.Job, bool]:
    row, spec, stale = get_plan(db, project, plan_id)
    key = idempotency_key or f"generate:{row.id}"
    existing = db.scalar(
        select(m.Job).where(
            m.Job.project_id == project.id,
            m.Job.kind == JobKind.GENERATION,
            m.Job.idempotency_key == key,
        )
    )
    if existing is not None:
        return existing, False  # same request repeated: never generate twice
    if row.status != PlanStatus.DRAFT:
        raise AppError(
            ErrorCode.CONFLICT,
            "Este plano já foi usado para gerar um vídeo. "
            "Clique em “Revisar e gerar” para montar um novo.",
        )
    if stale:
        raise AppError(ErrorCode.PLAN_STALE)
    if nothing_to_generate(spec):
        raise AppError(ErrorCode.NOTHING_TO_GENERATE)
    if spec.blocking:
        blocking = [w.model_dump(mode="json", by_alias=True) for w in spec.warnings if w.blocking]
        code = (
            ErrorCode.INSUFFICIENT_CREDITS
            if any(w["code"] == "INSUFFICIENT_CREDITS" for w in blocking)
            else ErrorCode.PLAN_BLOCKED
        )
        raise AppError(code, details={"warnings": blocking})
    job, created = create_job(
        db,
        project_id=project.id,
        kind=JobKind.GENERATION,
        idempotency_key=key,
        payload={"planId": str(row.id)},
        user_id=user.id,
        plan_id=row.id,
        message="Na fila para geração",
    )
    if created:
        row.status = PlanStatus.EXECUTING
    db.flush()
    return job, created


def output_out(runtime: Runtime, row: m.GenerationOutput) -> s.OutputOut:
    ext = row.storage_key.rsplit(".", 1)[-1]
    out = s.OutputOut.model_validate(row, from_attributes=True)
    out.url = signed(runtime, row.storage_key, content_type=row.content_type) or ""
    out.download_url = signed(
        runtime,
        row.storage_key,
        download_name=f"videodna-{_FILE_WORD.get(row.kind, 'arquivo')}-{str(row.id)[:8]}.{ext}",
        content_type=row.content_type,
    )
    return out


def list_outputs(
    db: Session, project: m.Project, kind: OutputKind | None
) -> list[m.GenerationOutput]:
    query = select(m.GenerationOutput).where(m.GenerationOutput.project_id == project.id)
    if kind is not None:
        query = query.where(m.GenerationOutput.kind == kind)
    return list(db.scalars(query.order_by(m.GenerationOutput.created_at.desc()).limit(200)))


def cost_summary(db: Session, runtime: Runtime, project: m.Project) -> s.CostSummaryOut:
    def total(kind: CostKind) -> float:
        value = db.scalar(
            select(func.coalesce(func.sum(m.CostEntry.amount), 0)).where(
                m.CostEntry.project_id == project.id, m.CostEntry.kind == kind
            )
        )
        return round(float(value or 0), 4)

    by_provider = db.execute(
        select(m.CostEntry.provider, m.CostEntry.model, func.sum(m.CostEntry.amount), func.count())
        .where(m.CostEntry.project_id == project.id, m.CostEntry.kind == CostKind.ACTUAL)
        .group_by(m.CostEntry.provider, m.CostEntry.model)
    ).all()
    by_job = db.execute(
        select(m.CostEntry.job_id, m.CostEntry.kind, func.sum(m.CostEntry.amount))
        .where(m.CostEntry.project_id == project.id, m.CostEntry.job_id.is_not(None))
        .group_by(m.CostEntry.job_id, m.CostEntry.kind)
    ).all()
    jobs: dict[str, dict] = {}
    for job_id, kind, amount in by_job:
        entry = jobs.setdefault(
            str(job_id), {"jobId": str(job_id), "estimated": 0.0, "actual": 0.0}
        )
        entry["estimated" if kind == CostKind.ESTIMATE else "actual"] = round(float(amount or 0), 4)
    seconds = db.scalar(
        select(func.coalesce(func.sum(m.CostEntry.seconds_generated), 0)).where(
            m.CostEntry.project_id == project.id, m.CostEntry.kind == CostKind.ACTUAL
        )
    )
    return s.CostSummaryOut(
        currency=runtime.settings.cost_currency,
        estimated_total=total(CostKind.ESTIMATE),
        actual_total=total(CostKind.ACTUAL),
        by_provider=[
            {"provider": p, "model": mdl, "amount": round(float(a or 0), 4), "calls": int(n)}
            for p, mdl, a, n in by_provider
        ],
        by_job=list(jobs.values()),
        seconds_generated=round(float(seconds or 0), 2),
    )
