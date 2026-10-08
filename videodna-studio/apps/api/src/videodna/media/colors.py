"""Deterministic color/brightness measurements from keyframes (no AI needed)."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from videodna.media.ffmpeg import run_ffmpeg

_W, _H = 24, 14


def _pixels(image: Path) -> list[tuple[int, int, int]]:
    proc = run_ffmpeg(
        [
            "-i",
            str(image),
            "-vf",
            f"scale={_W}:{_H}",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        timeout=60,
    )
    raw = proc.stdout
    return [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw) - 2, 3)]


def measure(image: Path, top: int = 4) -> tuple[list[str], float]:
    """Return (dominant colors as hex, brightness 0..1)."""
    pixels = _pixels(image)
    if not pixels:
        return [], 0.0
    buckets: Counter[tuple[int, int, int]] = Counter()
    sums: dict[tuple[int, int, int], list[int]] = {}
    for r, g, b in pixels:
        key = (r // 64, g // 64, b // 64)
        buckets[key] += 1
        acc = sums.setdefault(key, [0, 0, 0])
        acc[0] += r
        acc[1] += g
        acc[2] += b
    colors = []
    for key, count in buckets.most_common(top):
        r, g, b = (v // count for v in sums[key])
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    luma = sum(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in pixels) / len(pixels)
    return colors, round(luma / 255.0, 3)


def merge_palettes(palettes: list[list[str]], top: int = 5) -> list[str]:
    counter: Counter[str] = Counter()
    for palette in palettes:
        for rank, color in enumerate(palette):
            counter[color] += max(1, 4 - rank)
    return [c for c, _ in counter.most_common(top)]
