from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select

from videodna.api import schemas as s
from videodna.api.deps import (
    DbDep,
    RuntimeDep,
    UserDep,
    expensive_rate_limit,
    get_owned_project,
    rate_limit,
)
from videodna.db import models as m
from videodna.domain.enums import OutputKind
from videodna.errors import JOB_GONE, NotFound
from videodna.jobs.queue import get_queue
from videodna.services.generation import service as svc

router = APIRouter(tags=["generation"], dependencies=[Depends(rate_limit)])


@router.post(
    "/projects/{project_id}/generation-plan",
    response_model=s.PlanOut,
    status_code=201,
    summary="Criar o Generation Plan (estratégias, providers, custo estimado)",
)
def create_plan(
    project_id: uuid.UUID, req: s.PlanRequest, db: DbDep, runtime: RuntimeDep, user: UserDep
) -> s.PlanOut:
    project = get_owned_project(db, user, project_id)
    spec, row = svc.create_plan(db, runtime, user, project, req)
    db.commit()
    return svc.plan_to_out(spec, row)


@router.post(
    "/projects/{project_id}/cost-estimate",
    response_model=s.PlanOut,
    summary="Estimativa de custo rápida (plano não salvo)",
)
def cost_estimate(
    project_id: uuid.UUID, req: s.PlanRequest, db: DbDep, runtime: RuntimeDep, user: UserDep
) -> s.PlanOut:
    project = get_owned_project(db, user, project_id)
    spec, _ = svc.create_plan(db, runtime, user, project, req, persist=False)
    return svc.plan_to_out(spec, None)


@router.get(
    "/projects/{project_id}/generation-plans/{plan_id}",
    response_model=s.PlanOut,
    summary="Obter um plano (indica se ficou desatualizado)",
)
def get_plan(project_id: uuid.UUID, plan_id: uuid.UUID, db: DbDep, user: UserDep) -> s.PlanOut:
    project = get_owned_project(db, user, project_id)
    row, spec, stale = svc.get_plan(db, project, plan_id)
    return svc.plan_to_out(spec, row, stale=stale)


@router.post(
    "/projects/{project_id}/generate",
    response_model=s.JobOut,
    status_code=202,
    dependencies=[Depends(expensive_rate_limit)],
    summary="Executar um plano (idempotente: Idempotency-Key)",
)
def generate(
    project_id: uuid.UUID,
    req: s.GenerateRequest,
    db: DbDep,
    user: UserDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=200)] = None,
) -> s.JobOut:
    project = get_owned_project(db, user, project_id)
    job, created = svc.start_generation(
        db, user, project, req.plan_id, idempotency_key or req.idempotency_key
    )
    db.commit()
    if created:
        get_queue().enqueue(job.id)
        db.refresh(job)
    return s.JobOut.model_validate(job)


@router.get(
    "/projects/{project_id}/outputs",
    response_model=list[s.OutputOut],
    summary="Resultados gerados (vídeos, previews, segmentos)",
)
def list_outputs(
    project_id: uuid.UUID,
    db: DbDep,
    runtime: RuntimeDep,
    user: UserDep,
    kind: Annotated[OutputKind | None, Query()] = None,
) -> list[s.OutputOut]:
    project = get_owned_project(db, user, project_id)
    return [svc.output_out(runtime, r) for r in svc.list_outputs(db, project, kind)]


@router.get("/outputs/{output_id}", response_model=s.OutputOut, summary="Detalhe de um resultado")
def get_output(output_id: uuid.UUID, db: DbDep, runtime: RuntimeDep, user: UserDep) -> s.OutputOut:
    row = db.get(m.GenerationOutput, output_id)
    if row is None:
        raise NotFound("Este vídeo gerado não existe mais. Veja as outras versões ou gere de novo.")
    get_owned_project(db, user, row.project_id)
    return svc.output_out(runtime, row)


@router.get("/jobs/{job_id}/qa", response_model=list[s.QAReportOut], summary="Relatórios de QA")
def job_qa(job_id: uuid.UUID, db: DbDep, user: UserDep) -> list[s.QAReportOut]:
    job = db.get(m.Job, job_id)
    if job is None:
        raise NotFound(JOB_GONE)
    get_owned_project(db, user, job.project_id)
    reports = db.scalars(
        select(m.QAReport)
        .where(m.QAReport.job_id == job_id)
        .order_by(m.QAReport.shot_key, m.QAReport.attempt, m.QAReport.provider)
    ).all()
    return [s.QAReportOut.model_validate(r) for r in reports]


@router.get(
    "/projects/{project_id}/costs", response_model=s.CostSummaryOut, summary="Custos do projeto"
)
def project_costs(
    project_id: uuid.UUID, db: DbDep, runtime: RuntimeDep, user: UserDep
) -> s.CostSummaryOut:
    project = get_owned_project(db, user, project_id)
    return svc.cost_summary(db, runtime, project)
