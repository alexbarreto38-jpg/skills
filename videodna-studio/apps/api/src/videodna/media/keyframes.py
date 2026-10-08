"""Keyframe strategy (stage C).

Analyzing every frame with a multimodal model is unaffordable. We extract a
small, deliberate set: start/middle/end of each shot plus an interval sample
for long shots, capped globally. A second pass can add "event" keyframes at
times where the analysis found something (an entity entering, an action).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from videodna.media.ffmpeg import run_ffmpeg
from videodna.media.shots import ShotBoundary


@dataclass(frozen=True)
class KeyframePick:
    shot_index: int
    time: float
    frame: int
    reason: str


def select_keyframes(
    shots: list[ShotBoundary],
    fps: float,
    *,
    interval_sec: float = 4.0,
    max_total: int = 120,
) -> list[KeyframePick]:
    picks: list[KeyframePick] = []
    edge = 1.0 / max(fps, 1.0)
    for shot in shots:
        dur = shot.end_time - shot.start_time
        times = [(shot.start_time + min(0.1, dur / 4), "shot_start")]
        times.append((shot.start_time + dur / 2, "shot_mid"))
        if dur > 1.0:
            times.append((shot.end_time - min(0.15, dur / 4) - edge, "shot_end"))
        t = shot.start_time + interval_sec
        while t < shot.end_time - interval_sec / 2:
            times.append((t, "interval"))
            t += interval_sec
        for time, reason in sorted(times):
            picks.append(KeyframePick(shot.index, round(time, 3), round(time * fps), reason))

    if len(picks) <= max_total:
        return picks
    # Over budget: keep every shot's mid frame first, then fill evenly.
    mids = [p for p in picks if p.reason == "shot_mid"]
    if len(mids) >= max_total:
        step = len(mids) / max_total
        return [mids[int(i * step)] for i in range(max_total)]
    rest = [p for p in picks if p.reason != "shot_mid"]
    step = len(rest) / (max_total - len(mids))
    chosen = mids + [rest[int(i * step)] for i in range(max_total - len(mids))]
    return sorted(chosen, key=lambda p: p.time)


def extract_frame(video: Path, time: float, dest: Path, width: int = 640) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-ss",
            f"{max(0.0, time):.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-vf",
            f"scale={width}:-2",
            "-q:v",
            "3",
            str(dest),
        ],
        timeout=120,
    )
    return dest
