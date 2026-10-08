"""Mock video editor/generator.

Produces a *real* re-encoded segment derived from the source: edited elements
are tinted along their tracks, environment-level strategies shift the global
palette, and a badge says what was simulated. That exercises per-shot
generation, timeline splicing, QA and assembly end to end — for free.
"""

from __future__ import annotations

from videodna.media.ffmpeg import escape_drawtext, find_font_file
from videodna.media.transcode import cut_segment, probe_duration
from videodna.orchestrator.adapters.mock.base import MockMixin
from videodna.orchestrator.adapters.mock.story import stable_noise
from videodna.orchestrator.capabilities import Capability
from videodna.orchestrator.interfaces import (
    ProviderUsageInfo,
    VideoEditorProvider,
    VideoEditRequest,
    VideoGenerationRequest,
    VideoGeneratorProvider,
    VideoResult,
)

_GLOBAL_CAPABILITIES = {
    Capability.VIDEO_BACKGROUND_REPLACE,
    Capability.VIDEO_SHOT_RECONSTRUCTION,
    Capability.VIDEO_FULL_GENERATION,
}


def _color_for(label: str, explicit: str | None) -> str:
    if explicit and explicit.startswith("#") and len(explicit) == 7:
        return explicit.lstrip("#")
    h = int(stable_noise(label) * 0xFFFFFF)
    return f"{h:06x}"


def build_filter(request: VideoEditRequest, provider: str) -> str:
    filters: list[str] = []
    if request.capability in _GLOBAL_CAPABILITIES:
        seed = "|".join(sorted(e.label for e in request.edits)) or "global"
        hue = 20 + int(140 * stable_noise(seed))
        filters.append(f"hue=h={hue}:s=1.12")
        if request.capability != Capability.VIDEO_BACKGROUND_REPLACE:
            filters.append("eq=contrast=1.06:saturation=1.18")

    for edit in request.edits:
        samples = [
            s for s in edit.track if request.start_time - 0.6 <= s.time <= request.end_time + 0.01
        ]
        color = _color_for(edit.label, edit.color_hex)
        for i, sample in enumerate(samples):
            t0 = max(0.0, sample.time - request.start_time)
            t1 = (
                samples[i + 1].time - request.start_time
                if i + 1 < len(samples)
                else request.end_time - request.start_time + 0.1
            )
            if t1 <= 0:
                continue
            b = sample.bbox
            enable = f"enable='between(t,{t0:.3f},{t1:.3f})'"
            box = f"x=iw*{b.x:.4f}:y=ih*{b.y:.4f}:w=iw*{b.w:.4f}:h=ih*{b.h:.4f}"
            filters.append(f"drawbox={box}:color=0x{color}@0.42:t=fill:{enable}")
            filters.append(f"drawbox={box}:color=0x{color}@0.9:t=2:{enable}")

    font = find_font_file()
    if font:
        stage = "reparo" if request.repair_hint else "tentativa"
        badge = f"MOCK · {provider} · {request.capability.value} · {stage} {request.attempt + 1}"
        filters.append(
            f"drawtext=fontfile='{font.as_posix()}':text='{escape_drawtext(badge)}':"
            "fontsize=h/30:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=6:x=10:y=10"
        )
        legend = " · ".join(e.label for e in request.edits)[:90]
        if legend:
            filters.append(
                f"drawtext=fontfile='{font.as_posix()}':text='{escape_drawtext(legend)}':"
                "fontsize=h/28:fontcolor=white:box=1:boxcolor=0x2f6fdb@0.6:boxborderw=6:"
                "x=10:y=h-text_h-14"
            )
    return ",".join(filters) or "null"


class MockVideoEditor(MockMixin, VideoEditorProvider):
    def edit_video(self, request: VideoEditRequest) -> VideoResult:
        self.failures.check()
        vf = build_filter(request, self.name)
        cut_segment(
            request.input_path,
            request.output_path,
            start=request.start_time - request.timeline_offset,
            end=request.end_time - request.timeline_offset,
            height=request.output_height,
            fps=request.fps,
            vf=vf,
        )
        seconds = request.end_time - request.start_time
        return VideoResult(
            path=request.output_path,
            duration_sec=probe_duration(request.output_path),
            height=request.output_height,
            usage=ProviderUsageInfo(
                model=request.model or self.descriptor.default_model(request.capability),
                seconds_generated=round(seconds, 3),
                credits=round(seconds * float(self.params.get("credits_per_second", 1.0)), 2),
            ),
        )


class MockVideoGenerator(MockMixin, VideoGeneratorProvider):
    def generate_video(self, request: VideoGenerationRequest) -> VideoResult:
        self.failures.check()
        vf = build_filter(request, self.name)
        cut_segment(
            request.input_path,
            request.output_path,
            start=request.start_time - request.timeline_offset,
            end=request.end_time - request.timeline_offset,
            height=request.output_height,
            fps=request.fps,
            vf=vf,
        )
        seconds = request.end_time - request.start_time
        return VideoResult(
            path=request.output_path,
            duration_sec=probe_duration(request.output_path),
            height=request.output_height,
            usage=ProviderUsageInfo(
                model=request.model or self.descriptor.default_model(request.capability),
                seconds_generated=round(seconds, 3),
                credits=round(seconds * float(self.params.get("credits_per_second", 2.0)), 2),
            ),
        )
