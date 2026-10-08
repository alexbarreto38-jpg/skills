from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from videodna.api import schemas as s
from videodna.api.deps import DbDep, UserDep, get_owned_project, rate_limit
from videodna.db import models as m
from videodna.services import versions as svc

router = APIRouter(
    prefix="/projects/{project_id}/versions", tags=["projects"], dependencies=[Depends(rate_limit)]
)


def _out(v: m.ProjectVersion) -> s.VersionOut:
    return s.VersionOut(
        id=v.id,
        number=v.number,
        name=v.name,
        operation_count=len(v.operations or []),
        job_id=v.job_id,
        output_id=v.output_id,
        created_at=v.created_at,
    )


@router.get("", response_model=list[s.VersionOut], summary="Versões do projeto")
def list_versions(project_id: uuid.UUID, db: DbDep, user: UserDep) -> list[s.VersionOut]:
    project = get_owned_project(db, user, project_id)
    return [_out(v) for v in svc.list_versions(db, project)]


@router.post("", response_model=s.VersionOut, status_code=201, summary="Salvar versão")
def create_version(
    project_id: uuid.UUID, req: s.VersionCreate, db: DbDep, user: UserDep
) -> s.VersionOut:
    project = get_owned_project(db, user, project_id)
    version = svc.create_version(db, project, req.name)
    db.commit()
    return _out(version)


@router.post("/{version_id}/restore", response_model=s.VersionOut, summary="Restaurar versão")
def restore_version(
    project_id: uuid.UUID, version_id: uuid.UUID, db: DbDep, user: UserDep
) -> s.VersionOut:
    project = get_owned_project(db, user, project_id)
    version = svc.restore_version(db, user, project, version_id)
    db.commit()
    return _out(version)
