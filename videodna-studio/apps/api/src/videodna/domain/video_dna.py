"""Video DNA — the structured, versioned representation of an analyzed video.

The DNA is assembled from several sources (deterministic media analysis plus one
or more AI providers), every claim carries a confidence score, and the original
DNA is immutable: edits are stored as operations and the *current* DNA is derived
(`domain.operations.apply_operations`).

Field names serialize as camelCase, which is also the API contract.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from videodna.domain.enums import EntityType, Importance, TransitionType

DNA_SCHEMA_VERSION = "1.0"


class DNAModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        serialize_by_alias=True,
        json_schema_serialization_defaults_required=True,
    )


# --- technical ---------------------------------------------------------------


class AudioStreamInfo(DNAModel):
    codec: str | None = None
    channels: int | None = None
    sample_rate: int | None = None
    bitrate: int | None = None


class TechnicalMetadata(DNAModel):
    duration_sec: float
    width: int
    height: int
    aspect_ratio: str
    display_aspect_ratio: float
    fps: float
    frame_count: int
    video_codec: str | None = None
    pixel_format: str | None = None
    bitrate: int | None = None
    container_format: str | None = None
    size_bytes: int | None = None
    rotation: int = 0
    has_audio: bool = False
    audio: AudioStreamInfo | None = None
    keyframe_times: list[float] = Field(default_factory=list)


# --- shots & scenes ----------------------------------------------------------


class BBox(DNAModel):
    """Normalized bounding box (0..1, origin top-left)."""

    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    w: float = Field(gt=0, le=1)
    h: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def _inside_frame(self) -> BBox:
        if self.x + self.w > 1.0001 or self.y + self.h > 1.0001:
            raise ValueError("bbox must stay inside the frame")
        return self

    @property
    def area(self) -> float:
        return self.w * self.h


class Keyframe(DNAModel):
    id: str
    time: float
    frame: int
    reason: Literal["shot_start", "shot_mid", "shot_end", "interval", "event"]
    asset_key: str | None = None
    width: int | None = None
    height: int | None = None


class CameraInfo(DNAModel):
    shot_size: Literal[
        "extreme_wide",
        "wide",
        "medium",
        "medium_close_up",
        "close_up",
        "extreme_close_up",
        "unknown",
    ] = "unknown"
    angle: Literal["eye_level", "high", "low", "overhead", "dutch", "unknown"] = "unknown"
    movement: Literal[
        "static", "pan", "tilt", "dolly", "truck", "zoom", "handheld", "tracking", "unknown"
    ] = "unknown"
    movement_intensity: float = Field(default=0.0, ge=0, le=1)
    confidence: float = Field(default=0.0, ge=0, le=1)


class LightingInfo(DNAModel):
    source: Literal["natural", "artificial", "mixed", "unknown"] = "unknown"
    time_of_day: str | None = None
    color_temperature: Literal["warm", "neutral", "cool", "unknown"] = "unknown"
    brightness: float | None = Field(default=None, ge=0, le=1)
    mood: str | None = None
    confidence: float = Field(default=0.0, ge=0, le=1)


class Shot(DNAModel):
    id: str
    index: int
    scene_id: str | None = None
    start_time: float
    end_time: float
    duration: float
    start_frame: int
    end_frame: int
    transition_in: TransitionType = TransitionType.CUT
    keyframes: list[Keyframe] = Field(default_factory=list)
    thumbnail_key: str | None = None
    camera: CameraInfo = Field(default_factory=CameraInfo)
    lighting: LightingInfo = Field(default_factory=LightingInfo)
    dominant_colors: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0, le=1)

    @model_validator(mode="after")
    def _ordered(self) -> Shot:
        if self.end_time <= self.start_time:
            raise ValueError(f"shot {self.id}: end_time must be after start_time")
        return self


class Scene(DNAModel):
    id: str
    index: int
    label: str
    start_time: float
    end_time: float
    shot_ids: list[str]
    environment_id: str | None = None
    summary: str | None = None
    relationship_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0, le=1)


# --- entities ----------------------------------------------------------------


class EntityAlternative(DNAModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    source: str


class Appearance(DNAModel):
    shot_id: str
    start_time: float
    end_time: float


class EntityEditState(DNAModel):
    """Overlay present only in the *current* (edited) DNA."""

    modified: bool = False
    removed: bool = False
    added: bool = False
    locked: bool = False
    operation_ids: list[str] = Field(default_factory=list)
    original_label: str | None = None
    original_attributes: dict[str, Any] | None = None
    instructions: list[str] = Field(default_factory=list)


class Entity(DNAModel):
    id: str
    type: EntityType
    subtype: str | None = None
    label: str
    description: str | None = None
    parent_id: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    importance: Importance = Importance.DECORATIVE
    editable: bool = True
    replaceable: bool = True
    confidence: float = Field(ge=0, le=1)
    needs_review: bool = False
    alternatives: list[EntityAlternative] = Field(default_factory=list)
    appearances: list[Appearance] = Field(default_factory=list)
    track_ids: list[str] = Field(default_factory=list)
    derived_from: str | None = None
    sources: list[str] = Field(default_factory=list)
    edit: EntityEditState | None = None


class TrackSample(DNAModel):
    time: float
    frame: int
    bbox: BBox
    visibility: float = Field(default=1.0, ge=0, le=1)
    occluded: bool = False
    confidence: float = Field(default=1.0, ge=0, le=1)
    mask_key: str | None = None


class EntityTrack(DNAModel):
    id: str
    entity_id: str
    shot_id: str
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    samples: list[TrackSample] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    source: str | None = None


# --- actions, relationships, narrative ----------------------------------------


class Action(DNAModel):
    id: str
    verb: str
    label: str
    actor_id: str | None = None
    target_ids: list[str] = Field(default_factory=list)
    start_time: float
    end_time: float
    shot_ids: list[str] = Field(default_factory=list)
    essential: bool = False
    physics: list[str] = Field(default_factory=list)
    result_entity_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class Relationship(DNAModel):
    id: str
    subject_id: str
    predicate: str
    object_id: str
    scene_id: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    shot_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class NarrativeBeat(DNAModel):
    id: str
    order: int
    description: str
    abstract: str
    action_ids: list[str] = Field(default_factory=list)
    start_time: float
    end_time: float
    essential: bool = True


class Narrative(DNAModel):
    summary: str
    logline: str | None = None
    tone: str | None = None
    roles: dict[str, str] = Field(default_factory=dict)
    beats: list[NarrativeBeat] = Field(default_factory=list)
    essential_entity_ids: list[str] = Field(default_factory=list)
    replaceable_entity_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


# --- audio & on-screen text ----------------------------------------------------


class AudioSegment(DNAModel):
    id: str
    kind: Literal["speech", "music", "sfx", "ambience", "silence"]
    start_time: float
    end_time: float
    label: str | None = None
    transcript: str | None = None
    speaker_entity_id: str | None = None
    related_action_id: str | None = None
    confidence: float = Field(ge=0, le=1)


class AudioAnalysis(DNAModel):
    has_speech: bool = False
    has_music: bool = False
    has_sfx: bool = False
    language: str | None = None
    segments: list[AudioSegment] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)


class OnScreenText(DNAModel):
    id: str
    text: str
    kind: Literal["subtitle", "sign", "ui", "logo", "caption", "other"]
    start_time: float
    end_time: float
    bbox: BBox | None = None
    confidence: float = Field(ge=0, le=1)
    # Never modified automatically — only when the user asks (spec §67).
    auto_modify: bool = False


# --- provenance ----------------------------------------------------------------


class ProviderRun(DNAModel):
    stage: str
    provider: str
    model: str | None = None
    duration_ms: int | None = None
    cost: float | None = None
    confidence: float | None = None


class AnalysisProvenance(DNAModel):
    pipeline_version: str
    mock: bool
    created_at: str
    low_confidence_threshold: float
    providers: list[ProviderRun] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    reused_from_analysis_id: str | None = None


# --- root --------------------------------------------------------------------


class VideoDNA(DNAModel):
    schema_version: str = DNA_SCHEMA_VERSION
    source_video_id: str
    content_hash: str | None = None
    technical: TechnicalMetadata
    scenes: list[Scene] = Field(default_factory=list)
    shots: list[Shot] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    tracks: list[EntityTrack] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    narrative: Narrative | None = None
    audio: AudioAnalysis = Field(default_factory=AudioAnalysis)
    on_screen_text: list[OnScreenText] = Field(default_factory=list)
    dominant_colors: list[str] = Field(default_factory=list)
    analysis: AnalysisProvenance

    @model_validator(mode="after")
    def _referential_integrity(self) -> VideoDNA:
        """Every id referenced inside the DNA must exist. A dangling reference would
        make dependency analysis silently skip an element."""
        entity_ids = {e.id for e in self.entities}
        shot_ids = {s.id for s in self.shots}
        scene_ids = {s.id for s in self.scenes}
        action_ids = {a.id for a in self.actions}
        track_ids = {t.id for t in self.tracks}
        errors: list[str] = []

        if len(entity_ids) != len(self.entities):
            errors.append("duplicate entity ids")
        if len(shot_ids) != len(self.shots):
            errors.append("duplicate shot ids")
        for e in self.entities:
            if e.parent_id and e.parent_id not in entity_ids:
                errors.append(f"{e.id}: unknown parent {e.parent_id}")
            if e.derived_from and e.derived_from not in entity_ids:
                errors.append(f"{e.id}: unknown derivedFrom {e.derived_from}")
            errors.extend(
                f"{e.id}: unknown shot {a.shot_id}"
                for a in e.appearances
                if a.shot_id not in shot_ids
            )
            errors.extend(f"{e.id}: unknown track {t}" for t in e.track_ids if t not in track_ids)
        for s in self.shots:
            if s.scene_id and s.scene_id not in scene_ids:
                errors.append(f"{s.id}: unknown scene {s.scene_id}")
        for sc in self.scenes:
            errors.extend(
                f"{sc.id}: unknown shot {sid}" for sid in sc.shot_ids if sid not in shot_ids
            )
            if sc.environment_id and sc.environment_id not in entity_ids:
                errors.append(f"{sc.id}: unknown environment {sc.environment_id}")
        for t in self.tracks:
            if t.entity_id not in entity_ids:
                errors.append(f"{t.id}: unknown entity {t.entity_id}")
            if t.shot_id not in shot_ids:
                errors.append(f"{t.id}: unknown shot {t.shot_id}")
        for a in self.actions:
            refs = [a.actor_id, *a.target_ids, *a.result_entity_ids]
            errors.extend(f"{a.id}: unknown entity {r}" for r in refs if r and r not in entity_ids)
            errors.extend(f"{a.id}: unknown shot {s}" for s in a.shot_ids if s not in shot_ids)
        for r in self.relationships:
            for ref in (r.subject_id, r.object_id):
                if ref not in entity_ids:
                    errors.append(f"{r.id}: unknown entity {ref}")
        if self.narrative:
            for b in self.narrative.beats:
                errors.extend(
                    f"{b.id}: unknown action {a}" for a in b.action_ids if a not in action_ids
                )
            for role, ref in self.narrative.roles.items():
                if ref not in entity_ids:
                    errors.append(f"narrative role {role}: unknown entity {ref}")
        if errors:
            raise ValueError("Video DNA referential integrity: " + "; ".join(errors[:20]))
        return self

    # --- convenience lookups (not serialized) --------------------------------

    def entity(self, entity_id: str) -> Entity | None:
        return next((e for e in self.entities if e.id == entity_id), None)

    def shot(self, shot_id: str) -> Shot | None:
        return next((s for s in self.shots if s.id == shot_id), None)

    def children_of(self, entity_id: str) -> list[Entity]:
        return [e for e in self.entities if e.parent_id == entity_id]

    def descendants_of(self, entity_id: str) -> list[Entity]:
        out: list[Entity] = []
        frontier = [entity_id]
        while frontier:
            current = frontier.pop()
            for child in self.children_of(current):
                out.append(child)
                frontier.append(child.id)
        return out

    def actions_involving(self, entity_id: str) -> list[Action]:
        return [
            a
            for a in self.actions
            if a.actor_id == entity_id
            or entity_id in a.target_ids
            or entity_id in a.result_entity_ids
        ]

    def relationships_involving(self, entity_id: str) -> list[Relationship]:
        return [r for r in self.relationships if entity_id in (r.subject_id, r.object_id)]

    def tracks_for(self, entity_id: str, shot_id: str | None = None) -> list[EntityTrack]:
        return [
            t
            for t in self.tracks
            if t.entity_id == entity_id and (shot_id is None or t.shot_id == shot_id)
        ]

    def shots_for_entity(self, entity_id: str) -> list[str]:
        entity = self.entity(entity_id)
        if entity is None:
            return []
        shots = {a.shot_id for a in entity.appearances}
        if not shots and entity.parent_id:
            return self.shots_for_entity(entity.parent_id)
        if not shots and entity.type == EntityType.ENVIRONMENT:
            shots = {
                sid for sc in self.scenes if sc.environment_id == entity.id for sid in sc.shot_ids
            }
        order = {s.id: s.index for s in self.shots}
        return sorted(shots, key=lambda s: order.get(s, 0))
