"""Project versions: named snapshots of the edit operations (spec §40)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from videodna.db import models as m
from videodna.domain.enums import EditSource, EditState
from videodna.domain.operations import OperationSpec
from videodna.errors import NotFound
from videodna.services.editing import active_ops, require_analysis, to_spec
from videodna.services.projects import settings_of


def list_versions(db: Session, project: m.Project) -> list[m.ProjectVersion]:
    return list(
        db.scalars(
            select(m.ProjectVersion)
            .where(m.ProjectVersion.project_id == project.id)
            .order_by(m.ProjectVersion.number.desc())
        )
    )


def create_version(db: Session, project: m.Project, name: str) -> m.ProjectVersion:
    analysis = require_analysis(db, project)
    specs = [to_spec(o) for o in active_ops(db, project, analysis.id)]
    number = (
        db.scalar(
            select(func.max(m.ProjectVersion.number)).where(
                m.ProjectVersion.project_id == project.id
            )
        )
        or 0
    ) + 1
    version = m.ProjectVersion(
        project_id=project.id,
        number=number,
        name=name,
        analysis_id=analysis.id,
        operations=[s.model_dump(mode="json", by_alias=True) for s in specs],
        settings=settings_of(project).model_dump(mode="json", by_alias=True),
    )
    db.add(version)
    db.flush()
    return version


def restore_version(
    db: Session, user: m.User, project: m.Project, version_id: uuid.UUID
) -> m.ProjectVersion:
    """Restoring is itself undoable history: current ops are DISCARDED and the
    snapshot's ops are re-created as new ACTIVE operations."""
    version = db.get(m.ProjectVersion, version_id)
    if version is None or version.project_id != project.id:
        raise NotFound(
            "Esta versão não existe mais. Atualize a página (F5) para ver as versões atuais."
        )
    db.execute(
        update(m.EditOperation)
        .where(
            m.EditOperation.project_id == project.id,
            m.EditOperation.state.in_([EditState.ACTIVE, EditState.UNDONE]),
        )
        .values(state=EditState.DISCARDED)
    )
    next_seq = (
        db.scalar(
            select(func.max(m.EditOperation.sequence)).where(
                m.EditOperation.project_id == project.id
            )
        )
        or 0
    )
    for spec in (OperationSpec.model_validate(o) for o in version.operations):
        next_seq += 1
        db.add(
            m.EditOperation(
                project_id=project.id,
                analysis_id=version.analysis_id,
                sequence=next_seq,
                entity_key=spec.entity_id,
                op=spec.op,
                property=spec.property,
                previous_value=spec.previous_value,
                new_value=spec.new_value,
                instruction=spec.instruction,
                source=spec.source if spec.source else EditSource.MANUAL,
                state=EditState.ACTIVE,
                created_by_id=user.id,
            )
        )
    if version.settings:
        project.settings = dict(version.settings)
    project.current_analysis_id = version.analysis_id
    db.flush()
    return version
