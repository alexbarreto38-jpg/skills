"""Video DNA assembly: merges deterministic media analysis with provider outputs.

No single model is trusted blindly (spec §3/§98):
* the multimodal analyzer proposes entities, actions and the narrative;
* the detector re-grounds them on keyframes — when it *disagrees* on a label
  the disagreement is kept as an alternative ("Copo / Taça?") and the element
  is flagged for review if it matters for the story;
* elements below the confidence threshold are flagged, never hidden;
* dangling references from a provider are dropped with a warning instead of
  producing an inconsistent DNA.
"""

from __future__ import annotations

import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime

from videodna.domain.enums import EntityType, Importance
from videodna.domain.video_dna import (
    DNA_SCHEMA_VERSION,
    Action,
    AnalysisProvenance,
    Appearance,
    AudioAnalysis,
    Entity,
    EntityAlternative,
    EntityTrack,
    OnScreenText,
    ProviderRun,
    Relationship,
    Scene,
    Shot,
    TechnicalMetadata,
    VideoDNA,
)
from videodna.domain.vocabulary import PREDICATES, VERBS, normalize_verb
from videodna.media.colors import merge_palettes
from videodna.orchestrator.interfaces import (
    ImageAnalysisResult,
    SpeechResult,
    TrackResult,
    VideoAnalysisResult,
)

DISAGREEMENT_MIN_CONFIDENCE = 0.5


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if c.isalnum() or c == " ").strip()


def labels_agree(a: str, b: str) -> bool:
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return True
    if na == nb or na in nb or nb in na:
        return True
    wa, wb = set(na.split()), set(nb.split())
    return bool(wa & wb - {"de", "do", "da", "com", "e"})


@dataclass
class AssemblyInput:
    source_video_id: str
    content_hash: str | None
    technical: TechnicalMetadata
    shots: list[Shot]
    analysis: VideoAnalysisResult
    analyzer_provider: str
    detections: ImageAnalysisResult | None = None
    detector_provider: str | None = None
    tracks: list[TrackResult] = field(default_factory=list)
    tracker_provider: str | None = None
    speech: SpeechResult | None = None
    provider_runs: list[ProviderRun] = field(default_factory=list)
    pipeline_version: str = "1.0.0"
    mock: bool = False
    low_confidence_threshold: float = 0.6
    reused_from_analysis_id: str | None = None


def _overlapping_shots(shots: list[Shot], start: float, end: float) -> list[str]:
    """Shots an interval meaningfully overlaps. Boundary jitter of a few frames
    (container priming, rounding) must not drag an action into the neighbour shot."""
    out = [
        s.id
        for s in shots
        if min(end, s.end_time) - max(start, s.start_time) > min(0.25, 0.3 * s.duration)
    ]
    if not out:  # an instant event inside one shot
        mid = (start + end) / 2
        out = [s.id for s in shots if s.start_time <= mid < s.end_time]
    return out


def assemble_dna(data: AssemblyInput) -> VideoDNA:
    warnings: list[str] = []
    shots = [s.model_copy(deep=True) for s in data.shots]
    shot_by_id = {s.id: s for s in shots}
    result = data.analysis

    # --- shots: camera & lighting from the analyzer, brightness stays measured --
    for ann in result.shot_annotations:
        shot = shot_by_id.get(ann.shot_id)
        if shot is None:
            continue
        shot.camera = ann.camera
        measured = shot.lighting.brightness
        shot.lighting = ann.lighting.model_copy(update={"brightness": measured})

    # --- entities -----------------------------------------------------------------
    candidate_keys = {c.key for c in result.entities}
    entities: dict[str, Entity] = {}
    for cand in result.entities:
        parent = cand.parent_key if cand.parent_key in candidate_keys else None
        if cand.parent_key and parent is None:
            warnings.append(f"{cand.key}: pai desconhecido {cand.parent_key} ignorado")
        derived = cand.derived_from if cand.derived_from in candidate_keys else None
        entities[cand.key] = Entity(
            id=cand.key,
            type=cand.type,
            subtype=cand.subtype,
            label=cand.label,
            description=cand.description,
            parent_id=parent,
            attributes=dict(cand.attributes),
            importance=cand.importance,
            editable=cand.editable,
            replaceable=cand.replaceable,
            confidence=cand.confidence,
            alternatives=list(cand.alternatives),
            derived_from=derived,
            sources=[data.analyzer_provider],
        )

    # --- detector consensus -----------------------------------------------------------
    unmatched: dict[str, list] = defaultdict(list)
    if data.detections:
        by_entity: dict[str, list] = defaultdict(list)
        for det in data.detections.detections:
            if det.entity_hint and det.entity_hint in entities:
                by_entity[det.entity_hint].append(det)
            else:
                unmatched[_norm(det.label)].append(det)
        for key, dets in by_entity.items():
            entity = entities[key]
            entity.sources.append(data.detector_provider or "detector")
            agreeing = [d for d in dets if labels_agree(d.label, entity.label)]
            disagreeing = [d for d in dets if not labels_agree(d.label, entity.label)]
            if agreeing and not disagreeing:
                det_conf = max(d.confidence for d in agreeing)
                entity.confidence = round(
                    min(0.99, max(entity.confidence, (entity.confidence + det_conf) / 2 + 0.02)), 3
                )
            alt_best: dict[str, float] = {}
            for d in disagreeing:
                alt_best[d.label] = max(alt_best.get(d.label, 0.0), d.confidence)
            for label, conf in alt_best.items():
                if any(_norm(a.label) == _norm(label) for a in entity.alternatives):
                    continue
                entity.alternatives.append(
                    EntityAlternative(
                        label=label,
                        confidence=round(conf, 3),
                        source=data.detector_provider or "detector",
                    )
                )
            if alt_best:
                strongest = max(alt_best.values())
                entity.confidence = round(entity.confidence * (1 - 0.15 * strongest), 3)

    # Objects only the detector saw become new, unconfirmed elements.
    next_extra = 201
    for _, dets in sorted(unmatched.items()):
        best = max(dets, key=lambda d: d.confidence)
        if best.confidence < DISAGREEMENT_MIN_CONFIDENCE:
            continue
        key = f"OBJECT_{next_extra:03d}"
        next_extra += 1
        entities[key] = Entity(
            id=key,
            type=EntityType.OBJECT,
            label=best.label,
            importance=Importance.DECORATIVE,
            confidence=round(best.confidence * 0.9, 3),
            sources=[data.detector_provider or "detector"],
        )
        for d in dets:
            shot = shot_by_id.get(d.shot_id)
            if shot and not any(a.shot_id == shot.id for a in entities[key].appearances):
                entities[key].appearances.append(
                    Appearance(shot_id=shot.id, start_time=shot.start_time, end_time=shot.end_time)
                )

    # --- tracks & appearances -------------------------------------------------------
    tracks: list[EntityTrack] = []
    for i, tr in enumerate(data.tracks, start=1):
        if tr.entity_key not in entities or tr.shot_id not in shot_by_id or not tr.samples:
            continue
        track_id = f"TRACK_{i:04d}"
        tracks.append(
            EntityTrack(
                id=track_id,
                entity_id=tr.entity_key,
                shot_id=tr.shot_id,
                start_frame=tr.samples[0].frame,
                end_frame=tr.samples[-1].frame,
                start_time=tr.samples[0].time,
                end_time=tr.samples[-1].time,
                samples=tr.samples,
                confidence=tr.confidence,
                source=data.tracker_provider,
            )
        )
        entities[tr.entity_key].track_ids.append(track_id)
    if data.tracker_provider:
        for key in {t.entity_id for t in tracks}:
            entities[key].sources.append(data.tracker_provider)

    tracks_by_entity: dict[str, list[EntityTrack]] = defaultdict(list)
    for t in tracks:
        tracks_by_entity[t.entity_id].append(t)
    for cand in result.entities:
        entity = entities[cand.key]
        seen = {a.shot_id for a in entity.appearances}
        for t in tracks_by_entity.get(cand.key, []):
            if t.shot_id not in seen:
                entity.appearances.append(
                    Appearance(shot_id=t.shot_id, start_time=t.start_time, end_time=t.end_time)
                )
                seen.add(t.shot_id)
        for shot_id in cand.visible_shot_ids:
            shot = shot_by_id.get(shot_id)
            if shot and shot_id not in seen:
                entity.appearances.append(
                    Appearance(shot_id=shot_id, start_time=shot.start_time, end_time=shot.end_time)
                )
                seen.add(shot_id)
        entity.appearances.sort(key=lambda a: a.start_time)

    for entity in entities.values():
        entity.sources = list(dict.fromkeys(entity.sources))
        disputed = any(a.confidence >= DISAGREEMENT_MIN_CONFIDENCE for a in entity.alternatives)
        entity.needs_review = entity.confidence < data.low_confidence_threshold or (
            disputed and entity.importance != Importance.DECORATIVE
        )

    # --- scenes ---------------------------------------------------------------------
    scenes: list[Scene] = []
    for idx, sc in enumerate(result.scenes):
        shot_ids = [s for s in sc.shot_ids if s in shot_by_id]
        if not shot_ids:
            continue
        env = sc.environment_key if sc.environment_key in entities else None
        scenes.append(
            Scene(
                id=sc.key,
                index=idx,
                label=sc.label,
                start_time=min(shot_by_id[s].start_time for s in shot_ids),
                end_time=max(shot_by_id[s].end_time for s in shot_ids),
                shot_ids=shot_ids,
                environment_id=env,
                summary=sc.summary,
            )
        )
    assigned = {sid for sc in scenes for sid in sc.shot_ids}
    orphan = [s.id for s in shots if s.id not in assigned]
    if orphan:
        scenes.append(
            Scene(
                id=f"SCENE_{len(scenes) + 1:03d}",
                index=len(scenes),
                label="Cena sem classificação",
                start_time=min(shot_by_id[s].start_time for s in orphan),
                end_time=max(shot_by_id[s].end_time for s in orphan),
                shot_ids=orphan,
                confidence=0.4,
            )
        )
    for sc in scenes:
        for sid in sc.shot_ids:
            shot_by_id[sid].scene_id = sc.id

    # --- actions ----------------------------------------------------------------------
    actions: list[Action] = []
    for cand in result.actions:
        refs = [cand.actor_key, *cand.target_keys, *cand.result_keys]
        if any(r and r not in entities for r in refs):
            warnings.append(f"{cand.key}: referência a elemento desconhecido ignorada")
        verb = normalize_verb(cand.verb)
        spec = VERBS.get(verb)
        actions.append(
            Action(
                id=cand.key,
                verb=verb,
                label=cand.label,
                actor_id=cand.actor_key if cand.actor_key in entities else None,
                target_ids=[t for t in cand.target_keys if t in entities],
                result_entity_ids=[t for t in cand.result_keys if t in entities],
                start_time=cand.start_time,
                end_time=cand.end_time,
                shot_ids=_overlapping_shots(shots, cand.start_time, cand.end_time),
                essential=cand.essential,
                physics=list(spec.physics) if spec else [],
                confidence=cand.confidence,
            )
        )

    # --- relationships (scene graph) ------------------------------------------------
    relationships: list[Relationship] = []
    for i, cand in enumerate(result.relationships, start=1):
        if cand.subject_key not in entities or cand.object_key not in entities:
            warnings.append(f"relação {cand.subject_key}->{cand.object_key} ignorada")
            continue
        predicate = cand.predicate if cand.predicate in PREDICATES else cand.predicate.lower()
        start = cand.start_time if cand.start_time is not None else 0.0
        end = cand.end_time if cand.end_time is not None else data.technical.duration_sec
        rel_shots = _overlapping_shots(shots, start, end)
        scene_id = next((sc.id for sc in scenes if rel_shots and rel_shots[0] in sc.shot_ids), None)
        relationships.append(
            Relationship(
                id=f"REL_{i:03d}",
                subject_id=cand.subject_key,
                predicate=predicate,
                object_id=cand.object_key,
                scene_id=scene_id,
                start_time=cand.start_time,
                end_time=cand.end_time,
                shot_ids=rel_shots,
                confidence=cand.confidence,
            )
        )
    for sc in scenes:
        sc.relationship_ids = [r.id for r in relationships if r.scene_id == sc.id]

    # --- narrative ------------------------------------------------------------------
    narrative = result.narrative.model_copy(deep=True)
    narrative.roles = {k: v for k, v in narrative.roles.items() if v in entities}
    action_ids = {a.id for a in actions}
    for beat in narrative.beats:
        beat.action_ids = [a for a in beat.action_ids if a in action_ids]
    narrative.essential_entity_ids = [e for e in narrative.essential_entity_ids if e in entities]
    narrative.replaceable_entity_ids = [
        e for e in narrative.replaceable_entity_ids if e in entities
    ]

    # --- audio --------------------------------------------------------------------------
    audio = AudioAnalysis()
    if data.speech is not None:
        segments = []
        for seg in data.speech.segments:
            seg = seg.model_copy()
            if seg.speaker_entity_id and seg.speaker_entity_id not in entities:
                seg.speaker_entity_id = None
            if seg.related_action_id and seg.related_action_id not in action_ids:
                seg.related_action_id = None
            segments.append(seg)
        kinds = {s.kind for s in segments}
        audio = AudioAnalysis(
            has_speech="speech" in kinds,
            has_music=data.speech.has_music or "music" in kinds,
            has_sfx=data.speech.has_sfx or "sfx" in kinds,
            language=data.speech.language,
            segments=segments,
            confidence=data.speech.confidence,
        )

    # --- on-screen text (OCR) -------------------------------------------------------
    texts: list[OnScreenText] = []
    if data.detections:
        grouped: dict[str, list] = defaultdict(list)
        for det in data.detections.texts:
            grouped[det.text.strip()].append(det)
        for i, (text, dets) in enumerate(sorted(grouped.items()), start=1):
            times = sorted(d.time for d in dets)
            first_shot = next((s for s in shots if s.start_time <= times[-1] < s.end_time), None)
            texts.append(
                OnScreenText(
                    id=f"TEXT_{i:03d}",
                    text=text,
                    kind=dets[0].kind
                    if dets[0].kind in {"subtitle", "sign", "ui", "logo", "caption"}
                    else "other",
                    start_time=times[0],
                    end_time=first_shot.end_time if first_shot else times[-1],
                    bbox=dets[0].bbox,
                    confidence=max(d.confidence for d in dets),
                )
            )

    dna = VideoDNA(
        schema_version=DNA_SCHEMA_VERSION,
        source_video_id=data.source_video_id,
        content_hash=data.content_hash,
        technical=data.technical,
        scenes=scenes,
        shots=shots,
        entities=list(entities.values()),
        tracks=tracks,
        actions=actions,
        relationships=relationships,
        narrative=narrative,
        audio=audio,
        on_screen_text=texts,
        dominant_colors=merge_palettes([s.dominant_colors for s in shots]),
        analysis=AnalysisProvenance(
            pipeline_version=data.pipeline_version,
            mock=data.mock,
            created_at=datetime.now(UTC).isoformat(),
            low_confidence_threshold=data.low_confidence_threshold,
            providers=data.provider_runs,
            warnings=warnings,
            reused_from_analysis_id=data.reused_from_analysis_id,
        ),
    )
    return dna
