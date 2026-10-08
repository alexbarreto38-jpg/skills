from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
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
from videodna.domain.edit_options import categories_for, quick_actions_for
from videodna.domain.enums import EditOpType, EditSource, EntityType, JobKind
from videodna.domain.video_dna import Entity, VideoDNA
from videodna.errors import AppError, ErrorCode, NotFound
from videodna.jobs.queue import get_queue
from videodna.jobs.service import create_job
from videodna.runtime import Runtime
from videodna.services import editing
from videodna.services.media_urls import signed
from videodna.services.projects import latest_source

router = APIRouter(tags=["analysis"], dependencies=[Depends(rate_limit)])


@router.post(
    "/projects/{project_id}/analyze",
    response_model=s.JobOut,
    status_code=202,
    dependencies=[Depends(expensive_rate_limit)],
    summary="Analisar o vídeo (idempotente)",
)
def analyze(
    project_id: uuid.UUID,
    db: DbDep,
    user: UserDep,
    req: s.AnalyzeRequest | None = None,
) -> s.JobOut:
    project = get_owned_project(db, user, project_id)
    source = latest_source(db, project.id)
    if source is None:
        raise AppError(ErrorCode.UPLOAD_INCOMPLETE, "Envie um vídeo antes de analisar.")
    force = bool(req and req.force)
    key = f"analysis:{source.id}" + (f":force:{uuid.uuid4().hex[:8]}" if force else "")
    job, created = create_job(
        db,
        project_id=project.id,
        kind=JobKind.ANALYSIS,
        idempotency_key=key,
        payload={"sourceVideoId": str(source.id), "force": force},
        user_id=user.id,
        message="Na fila para análise",
    )
    db.commit()
    if created:
        get_queue().enqueue(job.id)
        db.refresh(job)
    return s.JobOut.model_validate(job)


@router.get(
    "/projects/{project_id}/analysis",
    response_model=s.AnalysisOut,
    summary="Status da análise atual",
)
def get_analysis(project_id: uuid.UUID, db: DbDep, user: UserDep) -> s.AnalysisOut:
    project = get_owned_project(db, user, project_id)
    analysis = editing.require_analysis(db, project)
    return s.AnalysisOut.model_validate(analysis)


def _asset_urls(runtime: Runtime, dna: VideoDNA) -> dict[str, str]:
    urls: dict[str, str] = {}
    for shot in dna.shots:
        for key in [shot.thumbnail_key, *(k.asset_key for k in shot.keyframes)]:
            if key and key not in urls:
                urls[key] = signed(runtime, key, content_type="image/jpeg") or ""
    return urls


@router.get(
    "/projects/{project_id}/video-dna",
    response_model=s.VideoDNAResponse,
    summary="Video DNA (original ou atual = original + operações)",
)
def get_video_dna(
    project_id: uuid.UUID,
    db: DbDep,
    runtime: RuntimeDep,
    user: UserDep,
    view: Annotated[Literal["original", "current"], Query()] = "current",
) -> s.VideoDNAResponse:
    project = get_owned_project(db, user, project_id)
    analysis, original, current, ops = editing.current_state(db, project)
    dna = current if view == "current" else original
    return s.VideoDNAResponse(
        analysis_id=analysis.id,
        view=view,
        edit_count=len(ops),
        dna=dna,
        asset_urls=_asset_urls(runtime, dna),
    )


def _entity_out(row: m.Entity, current: Entity | None) -> s.EntityOut:
    meta = row.meta or {}
    target = current or Entity(
        id=row.key,
        type=row.type,
        label=row.label,
        confidence=row.confidence,
        attributes=row.attributes,
    )
    return s.EntityOut(
        id=row.id,
        key=row.key,
        type=row.type,
        subtype=row.subtype,
        label=row.label,
        description=row.description,
        parent_key=row.parent_key,
        confidence=row.confidence,
        importance=row.importance,
        editable=row.editable,
        replaceable=row.replaceable,
        needs_review=row.needs_review,
        attributes=row.attributes or {},
        alternatives=meta.get("alternatives", []),
        appearances=meta.get("appearances", []),
        sources=meta.get("sources", []),
        current=current,
        categories=[
            s.EditCategoryOut(
                id=c.id, label=c.label, op=c.op, property=c.property, display=c.display
            )
            for c in categories_for(target)
        ],
        quick_actions=quick_actions_for(target),
    )


@router.get(
    "/projects/{project_id}/entities",
    response_model=list[s.EntityOut],
    summary="Elementos detectados (personagens, objetos, cenário...)",
)
def list_entities(
    project_id: uuid.UUID,
    db: DbDep,
    user: UserDep,
    type: Annotated[EntityType | None, Query()] = None,
    needs_review: Annotated[bool | None, Query(alias="needsReview")] = None,
) -> list[s.EntityOut]:
    project = get_owned_project(db, user, project_id)
    analysis, _, current, _ = editing.current_state(db, project)
    query = select(m.Entity).where(m.Entity.analysis_id == analysis.id)
    if type is not None:
        query = query.where(m.Entity.type == type)
    rows = db.scalars(query.order_by(m.Entity.key)).all()
    out = [_entity_out(r, current.entity(r.key)) for r in rows]
    if needs_review is not None:
        out = [
            e
            for e in out
            if (e.current.needs_review if e.current else e.needs_review) == needs_review
        ]
    return out


def _owned_entity(db, user, entity_id: uuid.UUID) -> tuple[m.Entity, m.Project]:
    row = db.get(m.Entity, entity_id)
    if row is None:
        raise NotFound("Elemento")
    project = get_owned_project(db, user, row.project_id)
    if row.analysis_id != project.current_analysis_id:
        raise NotFound("Elemento")
    return row, project


@router.get("/entities/{entity_id}", response_model=s.EntityOut, summary="Detalhe do elemento")
def get_entity(entity_id: uuid.UUID, db: DbDep, user: UserDep) -> s.EntityOut:
    row, project = _owned_entity(db, user, entity_id)
    _, _, current, _ = editing.current_state(db, project)
    return _entity_out(row, current.entity(row.key))


@router.patch(
    "/entities/{entity_id}",
    response_model=s.EntityOut,
    summary="Corrigir a análise de um elemento (vira uma operação CORRECT)",
)
def correct_entity(
    entity_id: uuid.UUID, req: s.EntityCorrection, db: DbDep, user: UserDep
) -> s.EntityOut:
    row, project = _owned_entity(db, user, entity_id)
    editing.create_edit(
        db,
        user,
        project,
        s.EditCreate(
            entity_key=row.key,
            op=EditOpType.CORRECT,
            property=req.property,
            new_value=req.value,
            source=EditSource.MANUAL,
        ),
    )
    db.commit()
    _, _, current, _ = editing.current_state(db, project)
    return _entity_out(row, current.entity(row.key))
