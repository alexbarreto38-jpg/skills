"""Shot detection (stage B).

One decoding pass over a downscaled copy collects ffmpeg's per-frame scene
score and `blackdetect` intervals.

A fixed threshold alone is brittle: hard cuts between shots of similar
brightness score as low as ~0.15, while fast motion can score ~0.1 on every
frame. So a frame is a cut when it is either above the hard threshold, or a
clear local peak — several times the average score of its neighbours and
above a small absolute floor (the same idea as PySceneDetect's adaptive
detector). Shots always cover the full duration contiguously, which keeps
per-shot generation and re-assembly frame-exact.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from videodna.domain.enums import TransitionType
from videodna.media.ffmpeg import run_ffmpeg

_PTS_RE = re.compile(r"pts_time:\s*([0-9.]+)")
_SCORE_RE = re.compile(r"lavfi\.scene_score=([0-9.]+)")
_BLACK_RE = re.compile(r"black_start:\s*([0-9.]+)\s+black_end:\s*([0-9.]+)")

ADAPTIVE_RATIO = 3.0
ADAPTIVE_FLOOR = 0.08
ADAPTIVE_WINDOW = 4


@dataclass(frozen=True)
class ShotBoundary:
    index: int
    start_time: float
    end_time: float
    start_frame: int
    end_frame: int
    transition_in: TransitionType

    @property
    def duration(self) -> float:
        return round(self.end_time - self.start_time, 3)


def scan(path: Path) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """Return ([(time, scene_score)], [(black_start, black_end)])."""
    vf = (
        "scale=320:-2,"
        "blackdetect=d=0.1:pix_th=0.10,"
        "select='gte(scene,0)',"
        "metadata=print:key=lavfi.scene_score"
    )
    proc = run_ffmpeg(["-i", str(path), "-an", "-vf", vf, "-f", "null", "-"])
    stderr = proc.stderr.decode("utf-8", "replace")
    scores: list[tuple[float, float]] = []
    pending_time: float | None = None
    for line in stderr.splitlines():
        if "Parsed_metadata" not in line:
            continue
        if (m := _PTS_RE.search(line)) is not None:
            pending_time = float(m.group(1))
        elif (m := _SCORE_RE.search(line)) is not None and pending_time is not None:
            scores.append((pending_time, float(m.group(1))))
            pending_time = None
    blacks = [(float(a), float(b)) for a, b in _BLACK_RE.findall(stderr)]
    return scores, blacks


def pick_cuts(
    scores: list[tuple[float, float]],
    *,
    threshold: float,
    ratio: float = ADAPTIVE_RATIO,
    floor: float = ADAPTIVE_FLOOR,
    window: int = ADAPTIVE_WINDOW,
) -> list[float]:
    cuts: list[float] = []
    values = [s for _, s in scores]
    for i, (time, score) in enumerate(scores):
        if i == 0:
            continue  # the first frame has no predecessor
        neighbours = values[max(0, i - window) : i] + values[i + 1 : i + 1 + window]
        local = sum(neighbours) / len(neighbours) if neighbours else 0.0
        if score >= threshold or (score >= floor and score >= ratio * local + 0.01):
            cuts.append(time)
    return cuts


def build_shots(
    duration: float,
    fps: float,
    cuts: list[float],
    blacks: list[tuple[float, float]],
    min_duration: float,
) -> list[ShotBoundary]:
    """Pure: turn cut times + black intervals into contiguous shots."""
    candidates: list[tuple[float, TransitionType]] = []
    for start, end in blacks:
        if start <= 0.05 or end >= duration - 0.05:
            continue  # fade-in at the start / fade-out at the end is not a cut
        candidates.append((round((start + end) / 2, 3), TransitionType.FADE))
    for t in cuts:
        in_black = any(start - 0.2 <= t <= end + 0.2 for start, end in blacks)
        if not in_black and min_duration <= t <= duration - min_duration:
            candidates.append((round(t, 3), TransitionType.CUT))
    candidates.sort()

    accepted: list[tuple[float, TransitionType]] = []
    for t, kind in candidates:
        last = accepted[-1][0] if accepted else 0.0
        if t - last >= min_duration and duration - t >= min_duration:
            accepted.append((t, kind))

    edges = [(0.0, TransitionType.NONE), *accepted]
    shots: list[ShotBoundary] = []
    for i, (start, kind) in enumerate(edges):
        end = edges[i + 1][0] if i + 1 < len(edges) else duration
        start_frame = round(start * fps)
        end_frame = max(start_frame, round(end * fps) - 1)
        shots.append(
            ShotBoundary(
                index=i,
                start_time=round(start, 3),
                end_time=round(end, 3),
                start_frame=start_frame,
                end_frame=end_frame,
                transition_in=kind,
            )
        )
    return shots


def detect_shots(
    path: Path, duration: float, fps: float, *, threshold: float = 0.3, min_duration: float = 0.4
) -> list[ShotBoundary]:
    scores, blacks = scan(path)
    return build_shots(duration, fps, pick_cuts(scores, threshold=threshold), blacks, min_duration)
