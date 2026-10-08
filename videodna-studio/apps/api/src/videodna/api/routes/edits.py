from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from videodna.api import schemas as s
from videodna.api.deps import DbDep, UserDep, get_owned_project, rate_limit
from videodna.db import models as m
from videodna.domain.enums import EditState
from videodna.domain.impact import ImpactReport
from videodna.services import editing

router = APIRouter(
    prefix="/projects/{project_id}", tags=["edits"], dependencies=[Depends(rate_limit)]
)


@router.get("/edits", response_model=s.EditHistoryOut, summary="Histórico de alterações")
def list_edits(
    project_id: uuid.UUID,
    db: DbDep,
    user: UserDep,
    state: Annotated[Literal["history", "all"], Query()] = "history",
) -> s.EditHistoryOut:
    project = get_owned_project(db, user, project_id)
    hist = editing.history(db, project)
    if state == "all":
        rows = db.scalars(
            select(m.EditOperation)
            .where(m.EditOperation.project_id == project.id)
            .order_by(m.EditOperation.sequence)
        ).all()
        hist.edits = [s.EditOut.model_validate(r) for r in rows]
    return hist


@router.post("/edits", response_model=s.EditResult, status_code=201, summary="Aplicar alteração")
def create_edit(project_id: uuid.UUID, req: s.EditCreate, db: DbDep, user: UserDep) -> s.EditResult:
    project = get_owned_project(db, user, project_id)
    row, impact = editing.create_edit(db, user, project, req)
    db.commit()
    return s.EditResult(
        edit=s.EditOut.model_validate(row), impact=impact, history=editing.history(db, project)
    )


@router.post(
    "/impact", response_model=ImpactReport, summary="Pré-visualizar o impacto (sem salvar)"
)
def preview_impact(
    project_id: uuid.UUID, req: s.EditCreate, db: DbDep, user: UserDep
) -> ImpactReport:
    project = get_owned_project(db, user, project_id)
    return editing.preview_impact(db, project, req)


@router.delete("/edits/{edit_id}", response_model=s.EditHistoryOut, summary="Remover uma alteração")
def delete_edit(
    project_id: uuid.UUID, edit_id: uuid.UUID, db: DbDep, user: UserDep
) -> s.EditHistoryOut:
    project = get_owned_project(db, user, project_id)
    editing.delete_edit(db, project, edit_id)
    db.commit()
    return editing.history(db, project)


@router.post("/edits/undo", response_model=s.EditResult, summary="Desfazer")
def undo(project_id: uuid.UUID, db: DbDep, user: UserDep) -> s.EditResult:
    project = get_owned_project(db, user, project_id)
    row = editing.undo(db, project)
    db.commit()
    return s.EditResult(
        edit=s.EditOut.model_validate(row) if row else None, history=editing.history(db, project)
    )


@router.post("/edits/redo", response_model=s.EditResult, summary="Refazer")
def redo(project_id: uuid.UUID, db: DbDep, user: UserDep) -> s.EditResult:
    project = get_owned_project(db, user, project_id)
    row = editing.redo(db, project)
    db.commit()
    return s.EditResult(
        edit=s.EditOut.model_validate(row) if row and row.state == EditState.ACTIVE else None,
        history=editing.history(db, project),
    )
