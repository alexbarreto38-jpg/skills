"""Edit operations service: create / undo / redo / delete, current DNA.

    OriginalVideoDNA + EditOperations(ACTIVE) = CurrentVideoDNA      (spec §39)

* undo  -> the newest ACTIVE op becomes UNDONE
* redo  -> the oldest UNDONE op becomes ACTIVE again
* a new op after an undo DISCARDS the redo stack (standard editor semantics)
* delete -> DISCARDED (kept for audit, never applied)
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from videodna.api import schemas as s
from videodna.db import models as m
from videodna.domain.enums import EditOpType, EditState
from videodna.domain.impact import ImpactReport, analyze_operation
from videodna.domain.operations import (
    OperationError,
    OperationSpec,
    added_entity_key,
    apply_operations,
    pin_added_entity_key,
    validate_operation,
)
from videodna.domain.video_dna import VideoDNA
from videodna.errors import ELEMENT_GONE, SUGGESTION_GONE, AppError, ErrorCode, NotFound
from videodna.services.analysis.persistence import dna_from_json
from videodna.services.projects import settings_of


def require_analysis(db: Session, project: m.Project) -> m.VideoAnalysis:
    if project.current_analysis_id is None:
        raise AppError(ErrorCode.ANALYSIS_REQUIRED)
    analysis = db.get(m.VideoAnalysis, project.current_analysis_id)
    if analysis is None or not analysis.dna:
        raise AppError(ErrorCode.ANALYSIS_REQUIRED)
    return analysis


def original_dna(analysis: m.VideoAnalysis) -> VideoDNA:
    return dna_from_json(analysis.dna)


def active_ops(db: Session, project: m.Project, analysis_id: uuid.UUID) -> list[m.EditOperation]:
    return list(
        db.scalars(
            select(m.EditOperation)
            .where(
                m.EditOperation.project_id == project.id,
                m.EditOperation.analysis_id == analysis_id,
                m.EditOperation.state == EditState.ACTIVE,
            )
            .order_by(m.EditOperation.sequence)
        )
    )


def to_spec(row: m.EditOperation) -> OperationSpec:
    return OperationSpec(
        id=str(row.id),
        sequence=row.sequence,
        entity_id=row.entity_key,
        op=row.op,
        property=row.property,
        new_value=row.new_value,
        previous_value=row.previous_value,
        instruction=row.instruction,
        source=row.source,
    )


def current_state(
    db: Session, project: m.Project
) -> tuple[m.VideoAnalysis, VideoDNA, VideoDNA, list[m.EditOperation]]:
    analysis = require_analysis(db, project)
    original = original_dna(analysis)
    ops = active_ops(db, project, analysis.id)
    current = apply_operations(original, [to_spec(o) for o in ops])
    return analysis, original, current, ops


def history(db: Session, project: m.Project) -> s.EditHistoryOut:
    rows = list(
        db.scalars(
            select(m.EditOperation)
            .where(
                m.EditOperation.project_id == project.id,
                m.EditOperation.analysis_id == project.current_analysis_id,
                m.EditOperation.state.in_([EditState.ACTIVE, EditState.UNDONE]),
            )
            .order_by(m.EditOperation.sequence)
        )
    )
    return s.EditHistoryOut(
        edits=[s.EditOut.model_validate(r) for r in rows],
        can_undo=any(r.state == EditState.ACTIVE for r in rows),
        can_redo=any(r.state == EditState.UNDONE for r in rows),
    )


def _resolve_entity_key(db: Session, analysis: m.VideoAnalysis, req: s.EditCreate) -> str | None:
    if req.entity_id is not None:
        row = db.get(m.Entity, req.entity_id)
        if row is None or row.analysis_id != analysis.id:
            raise NotFound(ELEMENT_GONE)
        return row.key
    return req.entity_key


def _previous_value(current: VideoDNA, spec: OperationSpec) -> Any:
    entity = current.entity(spec.entity_id) if spec.entity_id else None
    if entity is None:
        return None
    if spec.op == EditOpType.SET_ATTRIBUTE:
        return entity.attributes.get(spec.property or "")
    if spec.op == EditOpType.CORRECT:
        prop = spec.property or ""
        if prop.startswith("attributes."):
            return entity.attributes.get(prop.removeprefix("attributes."))
        value = getattr(entity, prop, None)
        return value.value if hasattr(value, "value") else value
    return {"label": entity.label, "attributes": entity.attributes}


def build_spec(
    db: Session, project: m.Project, req: s.EditCreate
) -> tuple[m.VideoAnalysis, VideoDNA, VideoDNA, list[m.EditOperation], OperationSpec]:
    analysis, original, current, ops = current_state(db, project)
    entity_key = _resolve_entity_key(db, analysis, req)
    next_seq = (
        db.scalar(
            select(func.max(m.EditOperation.sequence)).where(
                m.EditOperation.project_id == project.id
            )
        )
        or 0
    ) + 1
    spec = OperationSpec(
        id=str(uuid.uuid4()),
        sequence=next_seq,
        entity_id=entity_key,
        op=req.op,
        property=req.property,
        new_value=req.new_value,
        instruction=(req.instruction or None),
        source=req.source,
    )
    try:
        validate_operation(current, spec)
    except OperationError as exc:
        raise AppError(ErrorCode.VALIDATION_ERROR, str(exc)) from exc
    spec.previous_value = _previous_value(current, spec)
    spec = pin_added_entity_key(current, spec)
    return analysis, original, current, ops, spec


def preview_impact(db: Session, project: m.Project, req: s.EditCreate) -> ImpactReport:
    _, original, _, ops, spec = build_spec(db, project, req)
    after = apply_operations(original, [*map(to_spec, ops), spec])
    return analyze_operation(original, after, spec, settings_of(project).locks)


def create_edit(
    db: Session, user: m.User, project: m.Project, req: s.EditCreate
) -> tuple[m.EditOperation, ImpactReport]:
    analysis, original, _, ops, spec = build_spec(db, project, req)
    if req.suggestion_id is not None:
        suggestion = db.get(m.Suggestion, req.suggestion_id)
        if suggestion is None or suggestion.project_id != project.id:
            raise NotFound(SUGGESTION_GONE)
    after = apply_operations(original, [*map(to_spec, ops), spec])
    impact = analyze_operation(original, after, spec, settings_of(project).locks)

    # A new edit after undo discards the redo stack.
    db.execute(
        update(m.EditOperation)
        .where(m.EditOperation.project_id == project.id, m.EditOperation.state == EditState.UNDONE)
        .values(state=EditState.DISCARDED)
    )
    row = m.EditOperation(
        id=uuid.UUID(spec.id),
        project_id=project.id,
        analysis_id=analysis.id,
        sequence=spec.sequence,
        entity_key=spec.entity_id,
        op=spec.op,
        property=spec.property,
        previous_value=spec.previous_value,
        new_value=spec.new_value,
        instruction=spec.instruction,
        source=spec.source,
        suggestion_id=req.suggestion_id,
        state=EditState.ACTIVE,
        impact=impact.model_dump(mode="json", by_alias=True),
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    return row, impact


def undo(db: Session, project: m.Project) -> m.EditOperation | None:
    row = db.scalars(
        select(m.EditOperation)
        .where(
            m.EditOperation.project_id == project.id,
            m.EditOperation.analysis_id == project.current_analysis_id,
            m.EditOperation.state == EditState.ACTIVE,
        )
        .order_by(m.EditOperation.sequence.desc())
    ).first()
    if row is not None:
        row.state = EditState.UNDONE
        db.flush()
    return row


def redo(db: Session, project: m.Project) -> m.EditOperation | None:
    row = db.scalars(
        select(m.EditOperation)
        .where(
            m.EditOperation.project_id == project.id,
            m.EditOperation.analysis_id == project.current_analysis_id,
            m.EditOperation.state == EditState.UNDONE,
        )
        .order_by(m.EditOperation.sequence.asc())
    ).first()
    if row is not None:
        row.state = EditState.ACTIVE
        db.flush()
    return row


def delete_edit(db: Session, project: m.Project, edit_id: uuid.UUID) -> m.EditOperation:
    row = db.get(m.EditOperation, edit_id)
    if row is None or row.project_id != project.id:
        raise NotFound("Esta mudança já foi removida. Atualize a página (F5).")
    row.state = EditState.DISCARDED
    # Edits made to an element this operation added cannot outlive it.
    added_key = added_entity_key(to_spec(row))
    if added_key:
        db.execute(
            update(m.EditOperation)
            .where(
                m.EditOperation.project_id == project.id,
                m.EditOperation.entity_key == added_key,
                m.EditOperation.state.in_([EditState.ACTIVE, EditState.UNDONE]),
            )
            .values(state=EditState.DISCARDED)
        )
    db.flush()
    return row
