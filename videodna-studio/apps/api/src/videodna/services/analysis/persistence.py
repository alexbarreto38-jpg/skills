"""Writes a Video DNA: the immutable JSON snapshot + normalized rows, atomically."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from videodna.db import models as m
from videodna.domain.enums import AnalysisStatus
from videodna.domain.video_dna import VideoDNA


def dna_to_json(dna: VideoDNA) -> dict:
    return dna.model_dump(mode="json", by_alias=True)


def dna_from_json(data: dict) -> VideoDNA:
    return VideoDNA.model_validate(data)


def summarize(dna: VideoDNA) -> dict:
    by_type: dict[str, int] = {}
    for e in dna.entities:
        by_type[e.type.value] = by_type.get(e.type.value, 0) + 1
    return {
        "durationSec": dna.technical.duration_sec,
        "scenes": len(dna.scenes),
        "shots": len(dna.shots),
        "entities": len(dna.entities),
        "entitiesByType": by_type,
        "actions": len(dna.actions),
        "relationships": len(dna.relationships),
        "tracks": len(dna.tracks),
        "needsReview": sum(1 for e in dna.entities if e.needs_review),
        "onScreenText": len(dna.on_screen_text),
        "hasSpeech": dna.audio.has_speech,
    }


def persist_dna(session: Session, analysis: m.VideoAnalysis, dna: VideoDNA) -> None:
    aid = analysis.id
    for model in (m.EntityTrack, m.Action, m.Relationship, m.Entity, m.Shot, m.Scene):
        session.execute(delete(model).where(model.analysis_id == aid))
    session.flush()

    scene_rows: dict[str, m.Scene] = {}
    for sc in dna.scenes:
        row = m.Scene(
            analysis_id=aid,
            key=sc.id,
            index=sc.index,
            label=sc.label,
            start_time=sc.start_time,
            end_time=sc.end_time,
            summary=sc.summary,
            environment_key=sc.environment_id,
            graph={"relationshipIds": sc.relationship_ids, "shotIds": sc.shot_ids},
        )
        session.add(row)
        scene_rows[sc.id] = row
    session.flush()

    for shot in dna.shots:
        session.add(
            m.Shot(
                analysis_id=aid,
                scene_id=scene_rows[shot.scene_id].id if shot.scene_id in scene_rows else None,
                key=shot.id,
                index=shot.index,
                start_time=shot.start_time,
                end_time=shot.end_time,
                start_frame=shot.start_frame,
                end_frame=shot.end_frame,
                transition_in=shot.transition_in.value,
                camera=shot.camera.model_dump(mode="json", by_alias=True),
                lighting=shot.lighting.model_dump(mode="json", by_alias=True),
                dominant_colors=shot.dominant_colors,
                keyframes=[k.model_dump(mode="json", by_alias=True) for k in shot.keyframes],
                thumbnail_key=shot.thumbnail_key,
                confidence=shot.confidence,
            )
        )

    shot_scene = {s.id: s.scene_id for s in dna.shots}
    entity_rows: dict[str, m.Entity] = {}
    for e in dna.entities:
        first_scene = next(
            (shot_scene.get(a.shot_id) for a in e.appearances if shot_scene.get(a.shot_id)), None
        )
        cls = m.ENTITY_CLASS_BY_TYPE[e.type]
        row = cls(
            project_id=analysis.project_id,
            analysis_id=aid,
            scene_id=scene_rows[first_scene].id if first_scene in scene_rows else None,
            key=e.id,
            subtype=e.subtype,
            label=e.label,
            description=e.description,
            parent_key=e.parent_id,
            confidence=e.confidence,
            importance=e.importance,
            editable=e.editable,
            replaceable=e.replaceable,
            needs_review=e.needs_review,
            attributes=e.attributes,
            meta={
                "alternatives": [a.model_dump(mode="json", by_alias=True) for a in e.alternatives],
                "sources": e.sources,
                "derivedFrom": e.derived_from,
                "appearances": [a.model_dump(mode="json", by_alias=True) for a in e.appearances],
            },
        )
        session.add(row)
        entity_rows[e.id] = row
    session.flush()

    for t in dna.tracks:
        session.add(
            m.EntityTrack(
                analysis_id=aid,
                entity_id=entity_rows[t.entity_id].id,
                key=t.id,
                entity_key=t.entity_id,
                shot_key=t.shot_id,
                start_frame=t.start_frame,
                end_frame=t.end_frame,
                start_time=t.start_time,
                end_time=t.end_time,
                samples=[s.model_dump(mode="json", by_alias=True) for s in t.samples],
                confidence=t.confidence,
            )
        )
    for a in dna.actions:
        session.add(
            m.Action(
                analysis_id=aid,
                key=a.id,
                verb=a.verb,
                label=a.label,
                actor_key=a.actor_id,
                target_keys=a.target_ids,
                shot_keys=a.shot_ids,
                start_time=a.start_time,
                end_time=a.end_time,
                essential=a.essential,
                confidence=a.confidence,
                meta={"physics": a.physics, "results": a.result_entity_ids},
            )
        )
    for r in dna.relationships:
        session.add(
            m.Relationship(
                analysis_id=aid,
                key=r.id,
                scene_key=r.scene_id,
                subject_key=r.subject_id,
                predicate=r.predicate,
                object_key=r.object_id,
                start_time=r.start_time,
                end_time=r.end_time,
                confidence=r.confidence,
            )
        )

    analysis.dna = dna_to_json(dna)
    analysis.dna_schema_version = dna.schema_version
    analysis.summary = summarize(dna)
    analysis.low_confidence_count = analysis.summary["needsReview"]
    analysis.status = AnalysisStatus.COMPLETED
    analysis.completed_at = datetime.now(UTC)
    session.flush()
