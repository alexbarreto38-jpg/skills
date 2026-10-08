"""Suggestion Engine (spec §19/§20).

Input: current Video DNA, the selected element, its scene context, the edit
history and the project locks. Output: 6–12 contextual options per category,
each with a visual card.

Suggestions are cached by a *context hash*: the same element in the same
context never triggers a second provider call, but changing the environment
(e.g. to a beach house) changes the hash, so wardrobe suggestions refresh.
"""

from __future__ import annotations

import tempfile
import uuid
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from videodna.db import models as m
from videodna.domain.edit_options import categories_for
from videodna.domain.enums import EntityType
from videodna.domain.settings import ProjectLocks
from videodna.domain.video_dna import Entity, VideoDNA
from videodna.errors import AppError, ErrorCode
from videodna.logging_setup import get_logger
from videodna.media.hashing import sha256_text
from videodna.orchestrator.capabilities import Capability
from videodna.orchestrator.gateway import UsageContext
from videodna.orchestrator.interfaces import (
    ImageGenerationRequest,
    SuggestionContext,
    SuggestionRequest,
)
from videodna.orchestrator.router import RoutingTask
from videodna.runtime import Runtime
from videodna.services.editing import active_ops
from videodna.services.projects import settings_of
from videodna.storage.base import suggestion_key

log = get_logger(__name__)
PAGE_SIZE = 8


def _owning(dna: VideoDNA, entity: Entity, entity_type: EntityType) -> Entity | None:
    current: Entity | None = entity
    while current is not None:
        if current.type == entity_type:
            return current
        current = dna.entity(current.parent_id) if current.parent_id else None
    return None


def _environment_for(dna: VideoDNA, entity: Entity) -> Entity | None:
    env = _owning(dna, entity, EntityType.ENVIRONMENT)
    if env:
        return env
    shot_ids = set(dna.shots_for_entity(entity.id))
    for scene in dna.scenes:
        if scene.environment_id and shot_ids & set(scene.shot_ids):
            return dna.entity(scene.environment_id)
    return next((e for e in dna.entities if e.type == EntityType.ENVIRONMENT), None)


def build_context(
    dna: VideoDNA, entity: Entity, locks: ProjectLocks, history: list[str]
) -> SuggestionContext:
    parent = dna.entity(entity.parent_id) if entity.parent_id else None
    character = _owning(dna, entity, EntityType.CHARACTER)
    environment = _environment_for(dna, entity)
    scene = next(
        (sc for sc in dna.scenes if environment and sc.environment_id == environment.id), None
    )
    verbs = sorted({a.verb for a in dna.actions_involving(entity.id)})
    return SuggestionContext(
        entity=entity,
        parent=parent,
        character=character,
        environment=environment,
        scene_summary=scene.summary if scene else None,
        narrative_summary=dna.narrative.summary if dna.narrative else None,
        history=history[-20:],
        locks=locks,
        actions=verbs,
    )


def context_hash(category: str, ctx: SuggestionContext) -> str:
    def fingerprint(e: Entity | None) -> str:
        if e is None:
            return "-"
        return f"{e.id}|{e.label}|{sorted((k, str(v)) for k, v in e.attributes.items())}"

    return sha256_text(
        category,
        fingerprint(ctx.entity),
        fingerprint(ctx.parent),
        fingerprint(ctx.character),
        fingerprint(ctx.environment),
        ",".join(ctx.actions),
        ctx.locks.model_dump_json(),
    )


def _history_labels(db: Session, project: m.Project) -> list[str]:
    return [
        f"{o.op.value} {o.entity_key or ''} {o.property or ''}".strip()
        for o in active_ops(db, project, project.current_analysis_id)
    ]


def get_suggestions(
    db: Session,
    runtime: Runtime,
    user: m.User,
    project: m.Project,
    current: VideoDNA,
    entity_key: str,
    category: str,
    page: int = 0,
) -> tuple[list[m.Suggestion], bool]:
    entity = current.entity(entity_key)
    if entity is None:
        raise AppError(ErrorCode.NOT_FOUND, "Elemento não encontrado.")
    allowed = {c.id for c in categories_for(entity)}
    if category not in allowed:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"Categoria '{category}' não se aplica a este elemento.",
            details={"allowed": sorted(allowed)},
        )
    ctx = build_context(current, entity, settings_of(project).locks, _history_labels(db, project))
    digest = context_hash(category, ctx)
    cached = db.scalars(
        select(m.Suggestion)
        .where(
            m.Suggestion.analysis_id == project.current_analysis_id,
            m.Suggestion.entity_key == entity_key,
            m.Suggestion.category == category,
            m.Suggestion.context_hash == digest,
            m.Suggestion.page == page,
        )
        .order_by(m.Suggestion.rank)
    ).all()
    if cached:
        return list(cached), True

    previous = db.scalars(
        select(m.Suggestion.label).where(
            m.Suggestion.analysis_id == project.current_analysis_id,
            m.Suggestion.entity_key == entity_key,
            m.Suggestion.category == category,
            m.Suggestion.context_hash == digest,
            m.Suggestion.page < page,
        )
    ).all()
    usage = UsageContext(project_id=project.id, user_id=user.id)
    outcome = runtime.orchestrator.run(
        RoutingTask(capability=Capability.TEXT_SUGGESTIONS, quantity=1),
        lambda adapter, decision: adapter.suggest(
            SuggestionRequest(
                category=category,
                context=ctx,
                count=PAGE_SIZE,
                page=page,
                exclude_labels=list(previous),
            )
        ),
        operation="suggestions",
        context=usage,
    )
    rows: list[m.Suggestion] = []
    for rank, cand in enumerate(outcome.result.suggestions):
        row = m.Suggestion(
            id=uuid.uuid4(),
            project_id=project.id,
            analysis_id=project.current_analysis_id,
            entity_key=entity_key,
            category=category,
            context_hash=digest,
            page=page,
            rank=rank,
            label=cand.label,
            description=cand.description,
            op=cand.op,
            property=cand.property,
            value=cand.value,
            tags=cand.tags,
            score=cand.score,
            provider=outcome.decision.provider,
        )
        row.preview_key = _card(runtime, project, row, cand.preview_hint, usage)
        db.add(row)
        rows.append(row)
    db.flush()
    return rows, False


def next_page(db: Session, project: m.Project, entity_key: str, category: str) -> int:
    current_max = db.scalar(
        select(func.max(m.Suggestion.page)).where(
            m.Suggestion.analysis_id == project.current_analysis_id,
            m.Suggestion.entity_key == entity_key,
            m.Suggestion.category == category,
        )
    )
    return 0 if current_max is None else current_max + 1


def _card(
    runtime: Runtime, project: m.Project, row: m.Suggestion, hint: dict, usage: UsageContext
) -> str | None:
    """Visual card for the suggestion. Generated eagerly only when the routed
    image provider is free for this purpose (illustrative cards); a paid
    provider would make this lazy, so browsing options never costs money."""
    task = RoutingTask(capability=Capability.IMAGE_GENERATE, quantity=1)
    try:
        decision = runtime.orchestrator.route(task)
    except AppError:
        return None
    if decision.estimated_cost > Decimal(0):
        return None
    with tempfile.TemporaryDirectory(prefix="card-") as tmp:
        try:
            outcome = runtime.orchestrator.run(
                task,
                lambda adapter, d: adapter.generate_image(
                    ImageGenerationRequest(
                        prompt=row.label,
                        purpose="suggestion_card",
                        hint=hint,
                        output_path=Path(tmp) / str(row.id),
                    )
                ),
                operation="suggestions.card",
                context=usage,
                decision=decision,
            )
        except AppError:
            log.warning("suggestion card generation failed", extra={"suggestion_id": str(row.id)})
            return None
        result = outcome.result
        ext = ".svg" if result.content_type == "image/svg+xml" else ".jpg"
        key = suggestion_key(project.id, row.id, ext)
        runtime.storage.put_file(key, result.path, result.content_type)
        return key
