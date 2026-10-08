"""Provider interfaces (ports).

Business logic depends on these abstract classes only:

    Business Logic -> Provider Interface -> Provider Adapter -> External API

Requests carry *local file paths* because workers download media to a temp
directory first; an adapter that needs a URL uploads the file (or asks the
storage layer for a signed URL) itself.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field

from videodna.config import Settings
from videodna.domain.enums import EditOpType, EntityType, Importance, QASeverity, QualityMode
from videodna.domain.settings import ProjectLocks
from videodna.domain.video_dna import (
    AudioSegment,
    BBox,
    CameraInfo,
    Entity,
    EntityAlternative,
    LightingInfo,
    Narrative,
    Shot,
    TechnicalMetadata,
    TrackSample,
)
from videodna.orchestrator.capabilities import Capability, ProviderKind
from videodna.orchestrator.descriptor import ProviderDescriptor


class _Msg(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class ProviderUsageInfo(_Msg):
    model: str | None = None
    tokens: int | None = None
    credits: float | None = None
    seconds_generated: float | None = None
    images: int | None = None
    # Cost as reported by the provider's own usage/billing response, if any.
    reported_cost: Decimal | None = None
    currency: str | None = None


class ProviderResult(_Msg):
    usage: ProviderUsageInfo = Field(default_factory=ProviderUsageInfo)


# --- analysis ------------------------------------------------------------------


class KeyframeInput(_Msg):
    id: str
    shot_id: str
    time: float
    path: Path


class VideoAnalysisRequest(_Msg):
    video_path: Path
    technical: TechnicalMetadata
    shots: list[Shot]
    keyframes: list[KeyframeInput]
    language: str = "pt-BR"
    hints: dict[str, Any] = Field(default_factory=dict)


class EntityCandidate(_Msg):
    key: str
    type: EntityType
    subtype: str | None = None
    label: str
    description: str | None = None
    parent_key: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    importance: Importance = Importance.DECORATIVE
    confidence: float
    editable: bool = True
    replaceable: bool = True
    derived_from: str | None = None
    visible_shot_ids: list[str] = Field(default_factory=list)
    bbox_by_shot: dict[str, BBox] = Field(default_factory=dict)
    alternatives: list[EntityAlternative] = Field(default_factory=list)


class ActionCandidate(_Msg):
    key: str
    verb: str
    label: str
    actor_key: str | None = None
    target_keys: list[str] = Field(default_factory=list)
    result_keys: list[str] = Field(default_factory=list)
    start_time: float
    end_time: float
    essential: bool = False
    confidence: float


class RelationshipCandidate(_Msg):
    subject_key: str
    predicate: str
    object_key: str
    start_time: float | None = None
    end_time: float | None = None
    confidence: float


class SceneCandidate(_Msg):
    key: str
    label: str
    shot_ids: list[str]
    environment_key: str | None = None
    summary: str | None = None


class ShotAnnotation(_Msg):
    shot_id: str
    camera: CameraInfo
    lighting: LightingInfo


class VideoAnalysisResult(ProviderResult):
    narrative: Narrative
    entities: list[EntityCandidate]
    actions: list[ActionCandidate] = Field(default_factory=list)
    relationships: list[RelationshipCandidate] = Field(default_factory=list)
    scenes: list[SceneCandidate] = Field(default_factory=list)
    shot_annotations: list[ShotAnnotation] = Field(default_factory=list)
    confidence: float = 0.0


class ImageAnalysisRequest(_Msg):
    keyframes: list[KeyframeInput]
    prompts: list[str] = Field(default_factory=list)  # labels to ground
    detect: bool = True
    ocr: bool = True
    # Timeline context; real detectors may ignore it.
    duration_sec: float = 0.0
    shots: list[Shot] = Field(default_factory=list)


class Detection(_Msg):
    keyframe_id: str
    shot_id: str
    time: float
    label: str
    bbox: BBox
    confidence: float
    entity_hint: str | None = None


class TextDetection(_Msg):
    keyframe_id: str
    time: float
    text: str
    kind: str = "other"
    bbox: BBox | None = None
    confidence: float


class ImageAnalysisResult(ProviderResult):
    detections: list[Detection] = Field(default_factory=list)
    texts: list[TextDetection] = Field(default_factory=list)


class SegmentationTarget(_Msg):
    entity_key: str
    bbox: BBox


class SegmentationRequest(_Msg):
    image_path: Path
    keyframe_id: str
    targets: list[SegmentationTarget]
    output_dir: Path


class MaskResult(_Msg):
    entity_key: str
    keyframe_id: str
    mask_path: Path
    area: float
    confidence: float


class SegmentationResult(ProviderResult):
    masks: list[MaskResult] = Field(default_factory=list)


class TrackSeed(_Msg):
    entity_key: str
    time: float
    bbox: BBox
    confidence: float = 1.0


class TrackingRequest(_Msg):
    video_path: Path
    shot: Shot
    fps: float
    seeds: list[TrackSeed]
    sample_interval_sec: float = 0.5


class TrackResult(_Msg):
    entity_key: str
    shot_id: str
    samples: list[TrackSample]
    confidence: float


class TrackingResult(ProviderResult):
    tracks: list[TrackResult] = Field(default_factory=list)


class SpeechRequest(_Msg):
    media_path: Path
    duration_sec: float
    language: str = "pt-BR"
    speaker_hints: list[str] = Field(default_factory=list)


class SpeechResult(ProviderResult):
    segments: list[AudioSegment] = Field(default_factory=list)
    language: str | None = None
    has_music: bool = False
    has_sfx: bool = False
    confidence: float = 0.0


# --- suggestions & images -------------------------------------------------------


class SuggestionContext(_Msg):
    entity: Entity
    parent: Entity | None = None
    character: Entity | None = None
    environment: Entity | None = None
    scene_summary: str | None = None
    narrative_summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    history: list[str] = Field(default_factory=list)
    locks: ProjectLocks = Field(default_factory=ProjectLocks)
    actions: list[str] = Field(default_factory=list)


class SuggestionRequest(_Msg):
    category: str
    context: SuggestionContext
    count: int = 8
    page: int = 0
    exclude_labels: list[str] = Field(default_factory=list)


class SuggestionCandidate(_Msg):
    label: str
    description: str | None = None
    op: EditOpType
    property: str | None = None
    value: Any = None
    tags: list[str] = Field(default_factory=list)
    score: float = 0.5
    preview_hint: dict[str, Any] = Field(default_factory=dict)


class SuggestionResult(ProviderResult):
    suggestions: list[SuggestionCandidate] = Field(default_factory=list)


class ImageGenerationRequest(_Msg):
    prompt: str
    purpose: str = "suggestion_card"  # suggestion_card | reference | preview
    width: int = 512
    height: int = 512
    hint: dict[str, Any] = Field(default_factory=dict)
    reference_paths: list[Path] = Field(default_factory=list)
    output_path: Path


class ImageEditRequest(_Msg):
    image_path: Path
    bbox: BBox | None = None
    mask_path: Path | None = None
    instruction: str
    label: str
    color_hex: str | None = None
    output_path: Path


class ImageResult(ProviderResult):
    path: Path
    content_type: str
    width: int | None = None
    height: int | None = None


# --- video editing / generation ---------------------------------------------------


class EditSpec(_Msg):
    entity_key: str | None
    entity_type: EntityType | None = None
    op: EditOpType
    property: str | None = None
    label: str
    new_value: Any = None
    color_hex: str | None = None
    instruction: str | None = None
    # Track samples on the *absolute* source timeline.
    track: list[TrackSample] = Field(default_factory=list)
    mask_paths: list[Path] = Field(default_factory=list)


class ReferencePack(_Msg):
    kind: str  # "character" | "scene"
    entity_key: str
    description: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    image_paths: list[Path] = Field(default_factory=list)


class VideoEditRequest(_Msg):
    capability: Capability
    input_path: Path
    # Absolute source time of the first frame of `input_path`.
    timeline_offset: float
    start_time: float  # absolute
    end_time: float  # absolute
    edits: list[EditSpec]
    references: list[ReferencePack] = Field(default_factory=list)
    constraints: ProjectLocks = Field(default_factory=ProjectLocks)
    quality_mode: QualityMode = QualityMode.BALANCED
    model: str | None = None
    output_path: Path
    output_height: int
    fps: float
    attempt: int = 0
    repair_hint: str | None = None
    instruction: str | None = None


class VideoGenerationRequest(VideoEditRequest):
    prompt: str = ""


class VideoResult(ProviderResult):
    path: Path
    duration_sec: float
    width: int | None = None
    height: int | None = None


class QARequest(_Msg):
    output_path: Path
    original_path: Path
    shot: Shot
    timeline_offset: float
    expected_entities: list[Entity] = Field(default_factory=list)
    edits: list[EditSpec] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    constraints: ProjectLocks = Field(default_factory=ProjectLocks)
    expected_height: int | None = None
    attempt: int = 0


class QAIssueCandidate(_Msg):
    issue_type: str
    severity: QASeverity
    start_time: float
    end_time: float
    description: str
    affected_entity_key: str | None = None


class QACheck(_Msg):
    name: str
    passed: bool
    detail: str | None = None


class QAResult(ProviderResult):
    passed: bool
    score: float
    summary: str
    issues: list[QAIssueCandidate] = Field(default_factory=list)
    checks: list[QACheck] = Field(default_factory=list)


# --- adapters ----------------------------------------------------------------------


class ProviderAdapter(ABC):  # noqa: B024 - concrete defaults, abstract per kind
    kind: ClassVar[ProviderKind]

    def __init__(self, descriptor: ProviderDescriptor, settings: Settings) -> None:
        self.descriptor = descriptor
        self.settings = settings
        self.params: dict[str, Any] = dict(descriptor.params)

    @property
    def name(self) -> str:
        return self.descriptor.name

    def credential(self, env_name: str) -> str:
        """Read a secret declared in `credentials_env` (server side only)."""
        if env_name not in self.descriptor.credentials_env:
            raise ValueError(f"{env_name} is not declared in credentials_env of {self.name}")
        value = os.environ.get(env_name)
        if not value:
            raise ValueError(f"{env_name} is not set for provider {self.name}")
        return value

    def health_check(self) -> HealthStatus:
        return HealthStatus.HEALTHY

    def estimate_cost(
        self, capability: Capability, quantity: float, height: int | None = None
    ) -> Decimal:
        return self.descriptor.cost_for(capability).estimate(quantity, height)

    def actual_cost(
        self,
        capability: Capability,
        usage: ProviderUsageInfo,
        quantity: float,
        height: int | None = None,
    ) -> tuple[Decimal, str]:
        """Parse the real cost from the provider's usage report.

        Adapters override this when the provider reports tokens/credits; the
        default trusts `reported_cost` and otherwise falls back to the estimate.
        """
        cost_model = self.descriptor.cost_for(capability)
        if usage.reported_cost is not None:
            return usage.reported_cost, usage.currency or cost_model.currency
        return self.estimate_cost(capability, quantity, height), cost_model.currency


class VideoAnalyzerProvider(ProviderAdapter):
    kind = ProviderKind.VIDEO_ANALYZER

    @abstractmethod
    def analyze_video(self, request: VideoAnalysisRequest) -> VideoAnalysisResult: ...


class ImageAnalyzerProvider(ProviderAdapter):
    kind = ProviderKind.IMAGE_ANALYZER

    @abstractmethod
    def analyze_images(self, request: ImageAnalysisRequest) -> ImageAnalysisResult: ...


class SegmentationProvider(ProviderAdapter):
    kind = ProviderKind.SEGMENTATION

    @abstractmethod
    def segment(self, request: SegmentationRequest) -> SegmentationResult: ...


class TrackingProvider(ProviderAdapter):
    kind = ProviderKind.TRACKING

    @abstractmethod
    def track(self, request: TrackingRequest) -> TrackingResult: ...


class SpeechProvider(ProviderAdapter):
    kind = ProviderKind.SPEECH

    @abstractmethod
    def transcribe(self, request: SpeechRequest) -> SpeechResult: ...


class SuggestionProvider(ProviderAdapter):
    kind = ProviderKind.SUGGESTION

    @abstractmethod
    def suggest(self, request: SuggestionRequest) -> SuggestionResult: ...


class ImageGeneratorProvider(ProviderAdapter):
    kind = ProviderKind.IMAGE_GENERATOR

    @abstractmethod
    def generate_image(self, request: ImageGenerationRequest) -> ImageResult: ...

    @abstractmethod
    def edit_image(self, request: ImageEditRequest) -> ImageResult: ...


class VideoEditorProvider(ProviderAdapter):
    kind = ProviderKind.VIDEO_EDITOR

    @abstractmethod
    def edit_video(self, request: VideoEditRequest) -> VideoResult: ...


class VideoGeneratorProvider(ProviderAdapter):
    kind = ProviderKind.VIDEO_GENERATOR

    @abstractmethod
    def generate_video(self, request: VideoGenerationRequest) -> VideoResult: ...


class QAProvider(ProviderAdapter):
    kind = ProviderKind.QA

    @abstractmethod
    def inspect(self, request: QARequest) -> QAResult: ...


INTERFACE_FOR_KIND: dict[ProviderKind, type[ProviderAdapter]] = {
    cls.kind: cls
    for cls in (
        VideoAnalyzerProvider,
        ImageAnalyzerProvider,
        SegmentationProvider,
        TrackingProvider,
        SpeechProvider,
        SuggestionProvider,
        ImageGeneratorProvider,
        VideoEditorProvider,
        VideoGeneratorProvider,
        QAProvider,
    )
}
