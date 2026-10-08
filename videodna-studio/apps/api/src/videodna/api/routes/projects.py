from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response

from videodna.api import schemas as s
from videodna.api.deps import DbDep, RuntimeDep, UserDep, get_owned_project, rate_limit
from videodna.services import projects as svc

router = APIRouter(prefix="/projects", tags=["projects"], dependencies=[Depends(rate_limit)])


@router.post("", response_model=s.ProjectOut, status_code=201, summary="Criar projeto")
def create_project(
    req: s.ProjectCreate, db: DbDep, runtime: RuntimeDep, user: UserDep
) -> s.ProjectOut:
    project = svc.create_project(db, user, req)
    db.commit()
    return svc.project_out(db, runtime, project)


@router.get("", response_model=list[s.ProjectOut], summary="Listar projetos")
def list_projects(db: DbDep, runtime: RuntimeDep, user: UserDep) -> list[s.ProjectOut]:
    return [svc.project_out(db, runtime, p) for p in svc.list_projects(db, user)]


@router.get("/{project_id}", response_model=s.ProjectOut, summary="Detalhes do projeto")
def get_project(
    project_id: uuid.UUID, db: DbDep, runtime: RuntimeDep, user: UserDep
) -> s.ProjectOut:
    return svc.project_out(db, runtime, get_owned_project(db, user, project_id))


@router.patch("/{project_id}", response_model=s.ProjectOut, summary="Atualizar nome/locks/modo")
def update_project(
    project_id: uuid.UUID, req: s.ProjectUpdate, db: DbDep, runtime: RuntimeDep, user: UserDep
) -> s.ProjectOut:
    project = get_owned_project(db, user, project_id)
    svc.update_project(db, project, req)
    db.commit()
    return svc.project_out(db, runtime, project)


@router.delete("/{project_id}", status_code=204, summary="Excluir projeto e toda a mídia")
def delete_project(
    project_id: uuid.UUID, db: DbDep, runtime: RuntimeDep, user: UserDep
) -> Response:
    project = get_owned_project(db, user, project_id)
    svc.delete_project(db, runtime, project)
    db.commit()
    return Response(status_code=204)


@router.delete("/{project_id}/media", status_code=204, summary="Excluir apenas a mídia do projeto")
def delete_media(project_id: uuid.UUID, db: DbDep, runtime: RuntimeDep, user: UserDep) -> Response:
    project = get_owned_project(db, user, project_id)
    svc.delete_media(db, runtime, project)
    db.commit()
    return Response(status_code=204)


@router.post(
    "/{project_id}/duplicate",
    response_model=s.ProjectOut,
    status_code=201,
    summary="Duplicar projeto",
)
def duplicate_project(
    project_id: uuid.UUID, db: DbDep, runtime: RuntimeDep, user: UserDep
) -> s.ProjectOut:
    project = get_owned_project(db, user, project_id)
    clone = svc.duplicate_project(db, runtime, user, project)
    db.commit()
    return svc.project_out(db, runtime, clone)
