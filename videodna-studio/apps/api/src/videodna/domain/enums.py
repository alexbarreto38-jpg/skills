"""Domain enumerations shared by the DNA schema, the database and the API."""

from __future__ import annotations

from enum import StrEnum


class EntityType(StrEnum):
    CHARACTER = "character"
    HAIR = "hair"
    WARDROBE = "wardrobe"
    ACCESSORY = "accessory"
    OBJECT = "object"
    FURNITURE = "furniture"
    ENVIRONMENT = "environment"
    ENVIRONMENT_PART = "environment_part"
    LIGHTING = "lighting"
    TEXT = "text"
    AUDIO = "audio"


# Persistent id prefixes: CHARACTER_001, HAIR_001, ...
ENTITY_KEY_PREFIX: dict[EntityType, str] = {
    EntityType.CHARACTER: "CHARACTER",
    EntityType.HAIR: "HAIR",
    EntityType.WARDROBE: "WARDROBE",
    EntityType.ACCESSORY: "ACCESSORY",
    EntityType.OBJECT: "OBJECT",
    EntityType.FURNITURE: "FURNITURE",
    EntityType.ENVIRONMENT: "ENVIRONMENT",
    EntityType.ENVIRONMENT_PART: "ENVPART",
    EntityType.LIGHTING: "LIGHTING",
    EntityType.TEXT: "TEXT",
    EntityType.AUDIO: "AUDIO",
}


class WardrobeSlot(StrEnum):
    UPPER = "upper"
    LOWER = "lower"
    FOOTWEAR = "footwear"
    FULL = "full"


class EnvironmentPartKind(StrEnum):
    WALL = "wall"
    FLOOR = "floor"
    CEILING = "ceiling"
    WINDOW = "window"
    WINDOW_VIEW = "window_view"
    DOOR = "door"
    DECORATION = "decoration"
    BACKGROUND = "background"


class Importance(StrEnum):
    ESSENTIAL = "ESSENTIAL"
    IMPORTANT = "IMPORTANT"
    DECORATIVE = "DECORATIVE"


class TransitionType(StrEnum):
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    NONE = "none"
    UNKNOWN = "unknown"


class QualityMode(StrEnum):
    ECONOMY = "ECONOMY"
    BALANCED = "BALANCED"
    MAX = "MAX"


class RenderKind(StrEnum):
    PREVIEW = "preview"
    FINAL = "final"


class EditOpType(StrEnum):
    SET_ATTRIBUTE = "SET_ATTRIBUTE"  # e.g. hair.style = cacheado
    CHANGE_APPEARANCE = "CHANGE_APPEARANCE"  # free-form look change of one element
    REPLACE = "REPLACE"  # copo -> prato, character swap
    REMOVE = "REMOVE"
    KEEP = "KEEP"  # explicit "do not touch"
    APPLY_PRESET = "APPLY_PRESET"  # environment preset
    ADD_ENTITY = "ADD_ENTITY"  # "garrafa de água em cima da mesa"
    CORRECT = "CORRECT"  # manual correction of the analysis, no generation needed
    INSTRUCTION = "INSTRUCTION"  # custom instruction attached to an element


class EditSource(StrEnum):
    MANUAL = "manual"
    SUGGESTION = "suggestion"
    AI = "ai"


class EditState(StrEnum):
    ACTIVE = "ACTIVE"
    UNDONE = "UNDONE"
    DISCARDED = "DISCARDED"


class ImpactLevel(StrEnum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DependencyType(StrEnum):
    HAND_INTERACTION = "HAND_INTERACTION"
    PHYSICS_MOTION = "PHYSICS_MOTION"
    DESTRUCTION_FX = "DESTRUCTION_FX"
    CONTACT_SURFACE = "CONTACT_SURFACE"
    GAZE_TARGET = "GAZE_TARGET"
    OCCLUSION = "OCCLUSION"
    CONTINUITY = "CONTINUITY"
    DERIVED_ENTITY = "DERIVED_ENTITY"
    LIGHTING = "LIGHTING"
    STORY_ROLE = "STORY_ROLE"
    AUDIO_SFX = "AUDIO_SFX"
    CHILD_ELEMENTS = "CHILD_ELEMENTS"


class Strategy(StrEnum):
    """Per-shot generation strategy, in order of cost/heaviness."""

    PASSTHROUGH = "PASSTHROUGH"
    ATTRIBUTE_EDIT = "ATTRIBUTE_EDIT"
    LOCALIZED_EDIT = "LOCALIZED_EDIT"
    BACKGROUND_REPLACEMENT = "BACKGROUND_REPLACEMENT"
    SHOT_RECONSTRUCTION = "SHOT_RECONSTRUCTION"
    FULL_REGENERATION = "FULL_REGENERATION"


STRATEGY_ORDER: list[Strategy] = list(Strategy)


class JobKind(StrEnum):
    INGEST = "INGEST"
    ANALYSIS = "ANALYSIS"
    PREVIEW = "PREVIEW"
    GENERATION = "GENERATION"


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    ANALYZING = "ANALYZING"
    GENERATING = "GENERATING"
    QA = "QA"
    REPAIRING = "REPAIRING"
    ASSEMBLING = "ASSEMBLING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    @property
    def is_terminal(self) -> bool:
        return self in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}


TERMINAL_JOB_STATUSES = frozenset({JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED})


class ProjectStatus(StrEnum):
    DRAFT = "DRAFT"
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    ANALYZING = "ANALYZING"
    READY = "READY"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SourceVideoStatus(StrEnum):
    PENDING_UPLOAD = "PENDING_UPLOAD"
    UPLOADED = "UPLOADED"
    INGESTING = "INGESTING"
    READY = "READY"
    REJECTED = "REJECTED"
    DELETED = "DELETED"


class AnalysisStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PlanStatus(StrEnum):
    DRAFT = "DRAFT"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class OutputKind(StrEnum):
    FINAL = "FINAL"
    PREVIEW = "PREVIEW"
    SHOT_SEGMENT = "SHOT_SEGMENT"
    IMAGE_PREVIEW = "IMAGE_PREVIEW"
    REFERENCE_IMAGE = "REFERENCE_IMAGE"
    PROVENANCE = "PROVENANCE"


class QASeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


SEVERITY_RANK: dict[QASeverity, int] = {
    QASeverity.LOW: 0,
    QASeverity.MEDIUM: 1,
    QASeverity.HIGH: 2,
    QASeverity.CRITICAL: 3,
}


class QAIssueType(StrEnum):
    ENTITY_DISAPPEARED = "ENTITY_DISAPPEARED"
    ENTITY_DUPLICATED = "ENTITY_DUPLICATED"
    WARDROBE_CHANGED = "WARDROBE_CHANGED"
    FACE_CHANGED = "FACE_CHANGED"
    FLICKERING = "FLICKERING"
    ANATOMY = "ANATOMY"
    BACKGROUND_DRIFT = "BACKGROUND_DRIFT"
    INTERPENETRATION = "INTERPENETRATION"
    UNREQUESTED_CHANGE = "UNREQUESTED_CHANGE"
    ACTION_MISMATCH = "ACTION_MISMATCH"
    CAMERA_MISMATCH = "CAMERA_MISMATCH"
    DURATION_MISMATCH = "DURATION_MISMATCH"
    RESOLUTION_MISMATCH = "RESOLUTION_MISMATCH"
    BLACK_FRAMES = "BLACK_FRAMES"
    ARTIFACTS = "ARTIFACTS"


class QAIssueStatus(StrEnum):
    OPEN = "OPEN"
    REPAIRED = "REPAIRED"
    UNRESOLVED = "UNRESOLVED"
    ACCEPTED = "ACCEPTED"


class UsageStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class CostKind(StrEnum):
    ESTIMATE = "ESTIMATE"
    ACTUAL = "ACTUAL"
