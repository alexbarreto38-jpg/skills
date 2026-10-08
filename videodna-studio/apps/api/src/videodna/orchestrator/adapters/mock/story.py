"""Maps the fixture story onto the *real* timeline of the uploaded video.

Technical data, shots and keyframes always come from FFmpeg; in mock mode only
the semantic layer (who/what/where) comes from the fixture, distributed over
the detected shots proportionally to the beat timings.
"""

from __future__ import annotations

import hashlib
import json
import math
from functools import lru_cache
from typing import Any

from videodna.config import DEFAULT_FIXTURES_DIR
from videodna.domain.video_dna import BBox, Shot


@lru_cache
def load_story(name: str = "boy_glass") -> dict[str, Any]:
    path = DEFAULT_FIXTURES_DIR / "stories" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def stable_noise(*parts: object) -> float:
    """Deterministic pseudo-random value in [0, 1)."""
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:4], "big") / 2**32


def _clamp_bbox(x: float, y: float, w: float, h: float) -> BBox:
    w = min(max(w, 0.005), 1.0)
    h = min(max(h, 0.005), 1.0)
    x = min(max(x, 0.0), 1.0 - w)
    y = min(max(y, 0.0), 1.0 - h)
    return BBox(x=round(x, 4), y=round(y, 4), w=round(w, 4), h=round(h, 4))


class StoryTimeline:
    def __init__(self, story: dict[str, Any], duration: float, shots: list[Shot]) -> None:
        self.story = story
        self.duration = duration
        self.shots = shots
        self.beats = {b["id"]: b for b in story["beats"]}
        self.beat_order = [b["id"] for b in story["beats"]]
        self.entities = {e["key"]: e for e in story["entities"]}

    # --- time ------------------------------------------------------------------

    def beat_span(self, beat_id: str) -> tuple[float, float]:
        beat = self.beats[beat_id]
        return round(beat["start"] * self.duration, 3), round(beat["end"] * self.duration, 3)

    def beats_span(self, beat_ids: list[str]) -> tuple[float, float]:
        spans = [self.beat_span(b) for b in beat_ids]
        return min(s for s, _ in spans), max(e for _, e in spans)

    def resolve_beats(self, value: str | list[str] | None) -> list[str]:
        if value in (None, "all"):
            return list(self.beat_order)
        return [b for b in self.beat_order if b in value]

    def beat_at(self, t: float) -> str:
        for beat_id in self.beat_order:
            start, end = self.beat_span(beat_id)
            if start <= t < end:
                return beat_id
        return self.beat_order[-1]

    def shots_overlapping(self, start: float, end: float) -> list[str]:
        out = []
        for shot in self.shots:
            overlap = min(end, shot.end_time) - max(start, shot.start_time)
            # Count a shot when the overlap is meaningful for *that* shot.
            if overlap > min(0.25, 0.3 * shot.duration):
                out.append(shot.id)
        if not out:  # very short beat inside a long shot
            mid = (start + end) / 2
            out = [s.id for s in self.shots if s.start_time <= mid < s.end_time]
        return out

    def shots_for_beats(self, beat_ids: list[str]) -> list[str]:
        ids: list[str] = []
        for beat_id in beat_ids:
            for shot_id in self.shots_overlapping(*self.beat_span(beat_id)):
                if shot_id not in ids:
                    ids.append(shot_id)
        order = {s.id: s.index for s in self.shots}
        return sorted(ids, key=lambda s: order[s])

    def entity_beats(self, key: str) -> list[str]:
        return self.resolve_beats(self.entities[key].get("beats"))

    def entity_window(self, key: str, shot: Shot) -> tuple[float, float] | None:
        """Visible interval of an entity inside one shot."""
        intervals = [self.beat_span(b) for b in self.entity_beats(key)]
        start = max(shot.start_time, min(s for s, _ in intervals))
        end = min(shot.end_time, max(e for _, e in intervals))
        if end - start <= 0.04:
            return None
        return round(start, 3), round(end, 3)

    # --- space -----------------------------------------------------------------

    def bbox_at(self, key: str, t: float) -> BBox | None:
        entity = self.entities[key]
        if "bbox" not in entity:
            return None
        beat_id = self.beat_at(t)
        path = (entity.get("bboxPath") or {}).get(beat_id)
        if path:
            start, end = self.beat_span(beat_id)
            k = 0.0 if end <= start else min(1.0, max(0.0, (t - start) / (end - start)))
            a, b = path
            box = {c: a[c] + (b[c] - a[c]) * k for c in ("x", "y", "w", "h")}
        else:
            box = dict((entity.get("bboxByBeat") or {}).get(beat_id) or entity["bbox"])
        # Small deterministic drift so tracks look alive without being random.
        drift = 0.006 * math.sin(t * 1.7 + stable_noise(key) * 6.28)
        return _clamp_bbox(box["x"] + drift, box["y"] + drift / 2, box["w"], box["h"])
