from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

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
from videodna.domain.enums import EditSource
from videodna.errors import AppError, ErrorCode, NotFound
from videodna.jobs.queue import get_queue
from videodna.runtime import Runtime
from videodna.services import editing
from videodna.services import suggestions as svc
from videodna.services.media_urls import signed
from videodna.services.previews import create_preview_job

router = APIRouter(tags=["suggestions"], dependencies=[Depends(rate_limit)])


def _out(runtime: Runtime, row: m.Suggestion) -> s.SuggestionOut:
    out = s.SuggestionOut.model_validate(row)
    content_type = "image/svg+xml" if (row.preview_key or "").endswith(".svg") else "image/jpeg"
    out.preview_url = signed(runtime, row.preview_key, content_type=content_type)
    return out


def _entity(db, user, entity_id: uuid.UUID) -> tuple[m.Entity, m.Project]:
    row = db.get(m.Entity, entity_id)
    if row is None:
        raise NotFound("Elemento")
    project = get_owned_project(db, user, row.project_id)
    if row.analysis_id != project.current_analysis_id:
        raise NotFound("Elemento")
    return row, project


@router.get(
    "/entities/{entity_id}/suggestions",
    response_model=s.SuggestionList,
    summary="Sugestões contextuais para um elemento (cacheadas)",
)
def get_suggestions(
    entity_id: uuid.UUID,
    db: DbDep,
    runtime: RuntimeDep,
    user: UserDep,
    category: Annotated[str, Query()],
    page: Annotated[int, Query(ge=0, le=20)] = 0,
) -> s.SuggestionList:
    row, project = _entity(db, user, entity_id)
    _, _, current, _ = editing.current_state(db, project)
    items, cached = svc.get_suggestions(
        db, runtime, user, project, current, row.key, category, page
    )
    db.commit()
    return s.SuggestionList(
        entity_key=row.key,
        category=category,
        page=page,
        cached=cached,
        items=[_out(runtime, i) for i in items],
    )


@router.post(
    "/entities/{entity_id}/suggestions/more",
    response_model=s.SuggestionList,
    summary="Gerar mais opções (próxima página)",
)
def more_suggestions(
    entity_id: uuid.UUID,
    db: DbDep,
    runtime: RuntimeDep,
    user: UserDep,
    category: Annotated[str, Query()],
) -> s.SuggestionList:
    row, project = _entity(db, user, entity_id)
    _, _, current, _ = editing.current_state(db, project)
    page = svc.next_page(db, project, row.key, category)
    if page > 20:
        raise AppError(ErrorCode.CONFLICT, "Limite de opções atingido para este elemento.")
    items, cached = svc.get_suggestions(
        db, runtime, user, project, current, row.key, category, page
    )
    db.commit()
    return s.SuggestionList(
        entity_key=row.key,
        category=category,
        page=page,
        cached=cached,
        items=[_out(runtime, i) for i in items],
    )


def _suggestion(db, user, suggestion_id: uuid.UUID) -> tuple[m.Suggestion, m.Project]:
    row = db.get(m.Suggestion, suggestion_id)
    if row is None:
        raise NotFound("Sugestão")
    project = get_owned_project(db, user, row.project_id)
    if row.analysis_id != project.current_analysis_id:
        raise NotFound("Sugestão")
    return row, project


@router.post(
    "/suggestions/{suggestion_id}/apply",
    response_model=s.EditResult,
    status_code=201,
    summary="Aplicar uma sugestão (cria a operação de edição)",
)
def apply_suggestion(
    suggestion_id: uuid.UUID,
    db: DbDep,
    user: UserDep,
    instruction: Annotated[str | None, Query(max_length=2000)] = None,
) -> s.EditResult:
    row, project = _suggestion(db, user, suggestion_id)
    edit, impact = editing.create_edit(
        db,
        user,
        project,
        s.EditCreate(
            entity_key=row.entity_key,
            op=row.op,
            property=row.property,
            new_value=row.value,
            instruction=instruction,
            source=EditSource.SUGGESTION,
            suggestion_id=row.id,
        ),
    )
    db.commit()
    return s.EditResult(
        edit=s.EditOut.model_validate(edit), impact=impact, history=editing.history(db, project)
    )


@router.post(
    "/suggestions/{suggestion_id}/preview",
    response_model=s.JobOut,
    status_code=202,
    dependencies=[Depends(expensive_rate_limit)],
    summary="Preview de frame (a sugestão aplicada a um keyframe real)",
)
def preview_suggestion(
    suggestion_id: uuid.UUID,
    db: DbDep,
    runtime: RuntimeDep,
    user: UserDep,
    req: s.PreviewRequest | None = None,
) -> s.JobOut:
    if not runtime.flags.is_enabled("frame_previews"):
        raise AppError(ErrorCode.FORBIDDEN, "Previews de frame estão desativados.")
    row, project = _suggestion(db, user, suggestion_id)
    job, created = create_preview_job(db, user, project, row, req.shot_key if req else None)
    db.commit()
    if created:
        get_queue().enqueue(job.id)
        db.refresh(job)
    return s.JobOut.model_validate(job)
