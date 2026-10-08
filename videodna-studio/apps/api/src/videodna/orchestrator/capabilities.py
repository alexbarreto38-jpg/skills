"""Provider kinds and capabilities.

A *kind* is the interface an adapter implements; a *capability* is a specific
task it can perform. Routing is always by capability, never by provider name.
"""

from __future__ import annotations

from enum import StrEnum


class ProviderKind(StrEnum):
    VIDEO_ANALYZER = "video_analyzer"
    IMAGE_ANALYZER = "image_analyzer"
    SEGMENTATION = "segmentation"
    TRACKING = "tracking"
    IMAGE_GENERATOR = "image_generator"
    VIDEO_EDITOR = "video_editor"
    VIDEO_GENERATOR = "video_generator"
    SPEECH = "speech"
    QA = "qa"
    SUGGESTION = "suggestion"


class Capability(StrEnum):
    # understanding
    VIDEO_UNDERSTANDING = "video.understanding"
    OBJECT_DETECTION = "object.detection"
    OBJECT_GROUNDING = "object.grounding"
    OCR = "ocr"
    SEGMENTATION_IMAGE = "segmentation.image"
    SEGMENTATION_VIDEO = "segmentation.video"
    TRACKING_MULTI_OBJECT = "tracking.multi_object"
    SPEECH_TRANSCRIPTION = "speech.transcription"
    # suggestions & images
    TEXT_SUGGESTIONS = "text.suggestions"
    IMAGE_GENERATE = "image.generate"
    IMAGE_EDIT = "image.edit"
    # video editing / generation (ordered from light to heavy)
    VIDEO_ATTRIBUTE_EDIT = "video.attribute_edit"
    VIDEO_LOCALIZED_EDIT = "video.localized_edit"
    VIDEO_BACKGROUND_REPLACE = "video.background_replace"
    VIDEO_SHOT_RECONSTRUCTION = "video.shot_reconstruction"
    VIDEO_FULL_GENERATION = "video.full_generation"
    # quality
    QA_VIDEO_INSPECTION = "qa.video_inspection"
    QA_TECHNICAL = "qa.technical"


_E, _G = ProviderKind.VIDEO_EDITOR, ProviderKind.VIDEO_GENERATOR

# Which provider kinds may serve each capability (a shot reconstruction can be
# done by a video-to-video editor *or* by a generator that accepts references).
KINDS_FOR_CAPABILITY: dict[Capability, frozenset[ProviderKind]] = {
    Capability.VIDEO_UNDERSTANDING: frozenset({ProviderKind.VIDEO_ANALYZER}),
    Capability.OBJECT_DETECTION: frozenset({ProviderKind.IMAGE_ANALYZER}),
    Capability.OBJECT_GROUNDING: frozenset({ProviderKind.IMAGE_ANALYZER}),
    Capability.OCR: frozenset({ProviderKind.IMAGE_ANALYZER}),
    Capability.SEGMENTATION_IMAGE: frozenset({ProviderKind.SEGMENTATION}),
    Capability.SEGMENTATION_VIDEO: frozenset({ProviderKind.SEGMENTATION}),
    Capability.TRACKING_MULTI_OBJECT: frozenset({ProviderKind.TRACKING}),
    Capability.SPEECH_TRANSCRIPTION: frozenset({ProviderKind.SPEECH}),
    Capability.TEXT_SUGGESTIONS: frozenset({ProviderKind.SUGGESTION}),
    Capability.IMAGE_GENERATE: frozenset({ProviderKind.IMAGE_GENERATOR}),
    Capability.IMAGE_EDIT: frozenset({ProviderKind.IMAGE_GENERATOR}),
    Capability.VIDEO_ATTRIBUTE_EDIT: frozenset({_E}),
    Capability.VIDEO_LOCALIZED_EDIT: frozenset({_E}),
    Capability.VIDEO_BACKGROUND_REPLACE: frozenset({_E}),
    Capability.VIDEO_SHOT_RECONSTRUCTION: frozenset({_E, _G}),
    Capability.VIDEO_FULL_GENERATION: frozenset({_G}),
    Capability.QA_VIDEO_INSPECTION: frozenset({ProviderKind.QA}),
    Capability.QA_TECHNICAL: frozenset({ProviderKind.QA}),
}

# Optional features a task may require from a provider.
FEATURE_PARTIAL_RANGE = "partial_range"  # can regenerate a sub-range of a shot
FEATURE_REFERENCE_IMAGES = "reference_images"  # accepts character/scene reference packs
FEATURE_MOTION_PRESERVATION = "motion_preservation"  # honours LOCK MOTION
FEATURE_CAMERA_PRESERVATION = "camera_preservation"  # honours LOCK CAMERA
FEATURE_MASK_INPUT = "mask_input"  # consumes segmentation masks / tracks
FEATURE_CHUNKING = "chunking"  # long shots can be split in sequential calls
