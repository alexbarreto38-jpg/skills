"""Mock understanding providers: multimodal analyzer, detector/OCR, speech."""

from __future__ import annotations

from videodna.domain.enums import EntityType, Importance
from videodna.domain.video_dna import (
    AudioSegment,
    BBox,
    CameraInfo,
    EntityAlternative,
    LightingInfo,
    Narrative,
    NarrativeBeat,
)
from videodna.orchestrator.adapters.mock.base import MockMixin
from videodna.orchestrator.adapters.mock.story import StoryTimeline, load_story, stable_noise
from videodna.orchestrator.interfaces import (
    ActionCandidate,
    Detection,
    EntityCandidate,
    ImageAnalysisRequest,
    ImageAnalysisResult,
    ImageAnalyzerProvider,
    ProviderUsageInfo,
    RelationshipCandidate,
    SceneCandidate,
    ShotAnnotation,
    SpeechProvider,
    SpeechRequest,
    SpeechResult,
    TextDetection,
    VideoAnalysisRequest,
    VideoAnalysisResult,
    VideoAnalyzerProvider,
)


class MockVideoAnalyzer(MockMixin, VideoAnalyzerProvider):
    def analyze_video(self, request: VideoAnalysisRequest) -> VideoAnalysisResult:
        self.failures.check()
        story = load_story(self.params.get("story", "boy_glass"))
        tl = StoryTimeline(story, request.technical.duration_sec, request.shots)

        beats = []
        for order, beat in enumerate(story["beats"]):
            start, end = tl.beat_span(beat["id"])
            beats.append(
                NarrativeBeat(
                    id=beat["id"],
                    order=order,
                    description=beat["description"],
                    abstract=beat["abstract"],
                    action_ids=beat.get("actions", []),
                    start_time=start,
                    end_time=end,
                )
            )
        entities_raw = story["entities"]
        narrative = Narrative(
            summary=story["narrative"]["summary"],
            logline=story["narrative"].get("logline"),
            tone=story["narrative"].get("tone"),
            roles=story["narrative"].get("roles", {}),
            beats=beats,
            essential_entity_ids=[e["key"] for e in entities_raw if e["importance"] == "ESSENTIAL"],
            replaceable_entity_ids=[
                e["key"]
                for e in entities_raw
                if e.get("replaceable", True) and e["importance"] != "ESSENTIAL"
            ],
            confidence=story["narrative"].get("confidence", 0.9),
        )

        entities = []
        for raw in entities_raw:
            shot_ids = tl.shots_for_beats(tl.entity_beats(raw["key"]))
            bbox_by_shot: dict[str, BBox] = {}
            for shot in request.shots:
                if shot.id not in shot_ids:
                    continue
                window = tl.entity_window(raw["key"], shot)
                if window and (box := tl.bbox_at(raw["key"], (window[0] + window[1]) / 2)):
                    bbox_by_shot[shot.id] = box
            alternatives = [
                EntityAlternative(**a)
                for a in raw.get("alternatives", [])
                if a["source"] == self.name and a["label"].lower() != raw["label"].lower()
            ]
            entities.append(
                EntityCandidate(
                    key=raw["key"],
                    type=EntityType(raw["type"]),
                    subtype=raw.get("subtype"),
                    label=raw["label"],
                    description=raw.get("description"),
                    parent_key=raw.get("parent"),
                    attributes=dict(raw.get("attributes", {})),
                    importance=Importance(raw["importance"]),
                    confidence=raw["confidence"],
                    replaceable=raw.get("replaceable", True),
                    derived_from=raw.get("derivedFrom"),
                    visible_shot_ids=shot_ids,
                    bbox_by_shot=bbox_by_shot,
                    alternatives=alternatives,
                )
            )

        actions = []
        for raw in story["actions"]:
            beat_ids = tl.resolve_beats(raw["beats"])
            start, end = tl.beats_span(beat_ids)
            actions.append(
                ActionCandidate(
                    key=raw["key"],
                    verb=raw["verb"],
                    label=raw["label"],
                    actor_key=raw.get("actor"),
                    target_keys=raw.get("targets", []),
                    result_keys=raw.get("results", []),
                    start_time=start,
                    end_time=end,
                    essential=raw.get("essential", False),
                    confidence=raw["confidence"],
                )
            )

        relationships = []
        for raw in story["relationships"]:
            start, end = tl.beats_span(tl.resolve_beats(raw["beats"]))
            relationships.append(
                RelationshipCandidate(
                    subject_key=raw["subject"],
                    predicate=raw["predicate"],
                    object_key=raw["object"],
                    start_time=start,
                    end_time=end,
                    confidence=raw["confidence"],
                )
            )

        scenes = [
            SceneCandidate(
                key=raw["key"],
                label=raw["label"],
                shot_ids=[s.id for s in request.shots],
                environment_key=raw.get("environment"),
                summary=raw.get("summary"),
            )
            for raw in story["scenes"]
        ]

        cameras = story["camera"]
        lighting = story["lighting"]
        annotations = []
        for shot in request.shots:
            beat_index = tl.beat_order.index(tl.beat_at((shot.start_time + shot.end_time) / 2))
            annotations.append(
                ShotAnnotation(
                    shot_id=shot.id,
                    camera=CameraInfo.model_validate(cameras[beat_index % len(cameras)]),
                    lighting=LightingInfo.model_validate(lighting),
                )
            )

        return VideoAnalysisResult(
            narrative=narrative,
            entities=entities,
            actions=actions,
            relationships=relationships,
            scenes=scenes,
            shot_annotations=annotations,
            confidence=narrative.confidence,
            usage=ProviderUsageInfo(
                model=self.descriptor.default_model(),
                tokens=1500 + 260 * len(request.keyframes),
                seconds_generated=None,
            ),
        )


class MockImageAnalyzer(MockMixin, ImageAnalyzerProvider):
    """Plays the role of an open-vocabulary detector + OCR. It deliberately
    disagrees with the multimodal analyzer on one label (copo vs taça) so the
    consensus logic has something real to resolve."""

    def analyze_images(self, request: ImageAnalysisRequest) -> ImageAnalysisResult:
        self.failures.check()
        story = load_story(self.params.get("story", "boy_glass"))
        tl = StoryTimeline(story, request.duration_sec, request.shots)
        detector = story.get("detector", {})
        relabel = detector.get("relabel", {})
        missed = set(detector.get("missed", []))

        detections: list[Detection] = []
        texts: list[TextDetection] = []
        for kf in request.keyframes:
            beat = tl.beat_at(kf.time)
            if request.detect:
                for key, raw in tl.entities.items():
                    if key in missed or beat not in tl.entity_beats(key):
                        continue
                    if raw["type"] in {"environment", "lighting"}:
                        continue
                    box = tl.bbox_at(key, kf.time)
                    if box is None:
                        continue
                    alt = relabel.get(key)
                    jitter = 0.97 + 0.03 * stable_noise(key, kf.id)
                    detections.append(
                        Detection(
                            keyframe_id=kf.id,
                            shot_id=kf.shot_id,
                            time=kf.time,
                            label=alt["label"] if alt else raw["label"],
                            bbox=box,
                            confidence=round((alt or raw)["confidence"] * jitter, 3),
                            entity_hint=key,
                        )
                    )
            if request.ocr:
                for raw in story.get("texts", []):
                    if beat in tl.resolve_beats(raw["beats"]):
                        texts.append(
                            TextDetection(
                                keyframe_id=kf.id,
                                time=kf.time,
                                text=raw["text"],
                                kind=raw["kind"],
                                bbox=BBox.model_validate(raw["bbox"]),
                                confidence=raw["confidence"],
                            )
                        )
        return ImageAnalysisResult(
            detections=detections,
            texts=texts,
            usage=ProviderUsageInfo(
                model=self.descriptor.default_model(), images=len(request.keyframes)
            ),
        )


class MockSpeech(MockMixin, SpeechProvider):
    def transcribe(self, request: SpeechRequest) -> SpeechResult:
        self.failures.check()
        story = load_story(self.params.get("story", "boy_glass"))
        audio = story.get("audio", {})
        segments = []
        for i, raw in enumerate(audio.get("segments", []), start=1):
            segments.append(
                AudioSegment(
                    id=f"AUDIO_SEG_{i:03d}",
                    kind=raw["kind"],
                    start_time=round(raw["start"] * request.duration_sec, 3),
                    end_time=round(raw["end"] * request.duration_sec, 3),
                    label=raw.get("label"),
                    transcript=raw.get("transcript"),
                    speaker_entity_id=raw.get("speaker"),
                    related_action_id=raw.get("action"),
                    confidence=raw["confidence"],
                )
            )
        kinds = {s.kind for s in segments}
        return SpeechResult(
            segments=segments,
            language=audio.get("language", request.language),
            has_music="music" in kinds,
            has_sfx="sfx" in kinds,
            confidence=0.85,
            usage=ProviderUsageInfo(model=self.descriptor.default_model(), seconds_generated=None),
        )
