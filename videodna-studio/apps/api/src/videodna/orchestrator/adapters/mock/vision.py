"""Mock segmentation (box masks rendered with FFmpeg) and tracking
(interpolation between per-keyframe detections)."""

from __future__ import annotations

from videodna.domain.video_dna import BBox, TrackSample
from videodna.media.ffmpeg import run_ffmpeg
from videodna.media.transcode import probe_video_size
from videodna.orchestrator.adapters.mock.base import MockMixin
from videodna.orchestrator.interfaces import (
    MaskResult,
    ProviderUsageInfo,
    SegmentationProvider,
    SegmentationRequest,
    SegmentationResult,
    TrackingProvider,
    TrackingRequest,
    TrackingResult,
    TrackResult,
)


class MockSegmentation(MockMixin, SegmentationProvider):
    def segment(self, request: SegmentationRequest) -> SegmentationResult:
        self.failures.check()
        width, height = probe_video_size(request.image_path)
        request.output_dir.mkdir(parents=True, exist_ok=True)
        masks = []
        for target in request.targets:
            box = target.bbox
            dest = request.output_dir / f"{request.keyframe_id}_{target.entity_key}.png"
            run_ffmpeg(
                [
                    "-f",
                    "lavfi",
                    "-i",
                    f"color=c=black:s={width}x{height}:d=1",
                    "-vf",
                    (
                        f"drawbox=x={int(box.x * width)}:y={int(box.y * height)}:"
                        f"w={max(2, int(box.w * width))}:h={max(2, int(box.h * height))}:"
                        "color=white:t=fill,format=gray"
                    ),
                    "-frames:v",
                    "1",
                    str(dest),
                ],
                timeout=60,
            )
            masks.append(
                MaskResult(
                    entity_key=target.entity_key,
                    keyframe_id=request.keyframe_id,
                    mask_path=dest,
                    area=round(box.area * 0.82, 4),
                    confidence=0.9,
                )
            )
        return SegmentationResult(
            masks=masks,
            usage=ProviderUsageInfo(model=self.descriptor.default_model(), images=1),
        )


def _lerp_box(a: BBox, b: BBox, k: float) -> BBox:
    return BBox(
        x=round(a.x + (b.x - a.x) * k, 4),
        y=round(a.y + (b.y - a.y) * k, 4),
        w=round(a.w + (b.w - a.w) * k, 4),
        h=round(a.h + (b.h - a.h) * k, 4),
    )


class MockTracking(MockMixin, TrackingProvider):
    """Propagates detections across the shot. Like a real tracker it only knows
    what the seeds tell it: it tracks from the first to the last sighting and
    marks low-confidence sightings as (partially) occluded."""

    def track(self, request: TrackingRequest) -> TrackingResult:
        self.failures.check()
        shot = request.shot
        by_entity: dict[str, list] = {}
        for seed in sorted(request.seeds, key=lambda s: s.time):
            by_entity.setdefault(seed.entity_key, []).append(seed)

        tracks = []
        for key, seeds in by_entity.items():
            first, last = seeds[0].time, seeds[-1].time
            start = max(shot.start_time, first - request.sample_interval_sec)
            end = min(shot.end_time, last + request.sample_interval_sec)
            if first - shot.start_time <= 0.2:
                start = shot.start_time
            if shot.end_time - last <= 0.3:
                end = shot.end_time
            confidence = sum(s.confidence for s in seeds) / len(seeds)
            samples: list[TrackSample] = []
            t = start
            while t <= end + 1e-6:
                box = self._box_at(seeds, t)
                occluded = confidence < 0.6
                samples.append(
                    TrackSample(
                        time=round(t, 3),
                        frame=round(t * request.fps),
                        bbox=box,
                        visibility=0.45 if occluded else 1.0,
                        occluded=occluded,
                        confidence=round(min(0.99, confidence), 3),
                    )
                )
                t += request.sample_interval_sec
            if samples and samples[-1].time < end - 0.05:
                samples.append(
                    TrackSample(
                        time=round(end, 3),
                        frame=round(end * request.fps),
                        bbox=self._box_at(seeds, end),
                        confidence=round(min(0.99, confidence), 3),
                    )
                )
            tracks.append(
                TrackResult(
                    entity_key=key,
                    shot_id=shot.id,
                    samples=samples,
                    confidence=round(min(0.99, confidence), 3),
                )
            )
        return TrackingResult(
            tracks=tracks,
            usage=ProviderUsageInfo(model=self.descriptor.default_model(), seconds_generated=None),
        )

    @staticmethod
    def _box_at(seeds: list, t: float) -> BBox:
        if t <= seeds[0].time:
            return seeds[0].bbox
        for a, b in zip(seeds, seeds[1:], strict=False):
            if a.time <= t <= b.time:
                k = 0.0 if b.time == a.time else (t - a.time) / (b.time - a.time)
                return _lerp_box(a.bbox, b.bbox, k)
        return seeds[-1].bbox
