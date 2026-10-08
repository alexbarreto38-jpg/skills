"""Frame previews: see a suggestion applied to a real keyframe before paying
for video generation (spec §20/§64)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from videodna.db import models as m
from videodna.domain.enums import EntityType, JobKind, OutputKind
from videodna.domain.operations import OperationSpec, apply_operations
from videodna.domain.video_dna import BBox, VideoDNA
from videodna.errors import SUGGESTION_GONE, AppError, ErrorCode
from videodna.jobs.runner import JobContext
from videodna.jobs.service import create_job
from videodna.orchestrator.capabilities import Capability
from videodna.orchestrator.interfaces import ImageEditRequest
from videodna.orchestrator.router import RoutingTask
from videodna.services.editing import current_state
from videodna.storage.base import job_key


def create_preview_job(
    db: Session, user: m.User, project: m.Project, suggestion: m.Suggestion, shot_key: str | None
) -> tuple[m.Job, bool]:
    return create_job(
        db,
        project_id=project.id,
        kind=JobKind.PREVIEW,
        idempotency_key=f"preview:{suggestion.id}:{shot_key or 'auto'}",
        payload={"suggestionId": str(suggestion.id), "shotKey": shot_key},
        user_id=user.id,
        message="Gerando preview",
    )


def _bbox_near(dna: VideoDNA, entity_key: str, time: float) -> BBox | None:
    best: tuple[float, BBox] | None = None
    for track in dna.tracks:
        if track.entity_id != entity_key:
            continue
        for sample in track.samples:
            distance = abs(sample.time - time)
            if best is None or distance < best[0]:
                best = (distance, sample.bbox)
    return best[1] if best else None


def _color(value: Any) -> str | None:
    if isinstance(value, dict):
        attrs = value.get("attributes", value)
        if isinstance(attrs, dict) and isinstance(attrs.get("colorHex"), str):
            return attrs["colorHex"]
        palette = attrs.get("palette") if isinstance(attrs, dict) else None
        if palette:
            return palette[-1]
    return None


def run_preview_job(ctx: JobContext) -> dict[str, Any]:
    storage = ctx.runtime.storage
    with ctx.session() as session:
        suggestion = session.get(m.Suggestion, uuid.UUID(ctx.payload["suggestionId"]))
        project = session.get(m.Project, ctx.project_id)
        if suggestion is None or project is None:
            raise AppError(ErrorCode.NOT_FOUND, SUGGESTION_GONE)
        _, _, current, ops = current_state(session, project)
        session.expunge_all()

    spec = OperationSpec(
        id="preview",
        sequence=10**9,
        entity_id=suggestion.entity_key,
        op=suggestion.op,
        property=suggestion.property,
        new_value=suggestion.value,
    )
    after = apply_operations(current, [spec])
    entity = after.entity(suggestion.entity_key)
    shot_ids = current.shots_for_entity(suggestion.entity_key)
    shot_key = ctx.payload.get("shotKey") or (shot_ids[0] if shot_ids else current.shots[0].id)
    shot = current.shot(shot_key)
    if shot is None or not shot.keyframes:
        raise AppError(
            ErrorCode.NOT_FOUND,
            "Esta cena não tem uma foto para a prévia. "
            "Aplique a mudança e veja o resultado em “Revisar e gerar”.",
        )
    keyframe = next((k for k in shot.keyframes if k.reason == "shot_mid"), shot.keyframes[0])
    ctx.reporter.progress("preview", 20, "Separando uma foto da cena")
    local = storage.download(keyframe.asset_key, ctx.workdir / "keyframe.jpg")

    environment_level = entity is not None and entity.type == EntityType.ENVIRONMENT
    bbox = None if environment_level else _bbox_near(current, suggestion.entity_key, keyframe.time)
    ctx.reporter.progress("preview", 50, "Aplicando a mudança na foto")
    outcome = ctx.runtime.orchestrator.run(
        RoutingTask(capability=Capability.IMAGE_EDIT, quantity=1),
        lambda adapter, decision: adapter.edit_image(
            ImageEditRequest(
                image_path=local,
                bbox=bbox,
                instruction=f"{suggestion.op.value}: {suggestion.label}",
                label=entity.label if entity else suggestion.label,
                color_hex=_color(suggestion.value),
                output_path=ctx.workdir / "preview",
            )
        ),
        operation="preview.frame",
        context=ctx.usage(shot_key),
    )
    result = outcome.result
    key = job_key(ctx.project_id, ctx.job_id, f"preview{result.path.suffix}")
    storage.put_file(key, result.path, result.content_type)
    with ctx.session() as session:
        output = m.GenerationOutput(
            project_id=ctx.project_id,
            job_id=ctx.job_id,
            kind=OutputKind.IMAGE_PREVIEW,
            shot_key=shot_key,
            storage_key=key,
            content_type=result.content_type,
            width=result.width,
            height=result.height,
            size_bytes=result.path.stat().st_size,
            provider=outcome.decision.provider,
            model=outcome.decision.model,
            provenance={
                "suggestionId": str(suggestion.id),
                "keyframe": keyframe.id,
                "editsApplied": len(ops) + 1,
            },
        )
        session.add(output)
        session.commit()
        output_id = output.id
    return {
        "outputId": str(output_id),
        "suggestionId": str(suggestion.id),
        "shotKey": shot_key,
        "cost": float(outcome.actual_cost),
        "_message": "Prévia pronta",
    }
