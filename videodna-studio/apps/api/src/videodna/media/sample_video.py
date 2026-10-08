"""Synthetic test video for the reference story (spec §79).

Six hard-cut shots whose durations match the beats of
`fixtures/stories/boy_glass.json`, each with a moving element (so shots are
not frozen) and a caption naming the beat, plus a tone track per shot. Useful
for demos, fixtures and end-to-end tests without shipping real footage.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from videodna.media.ffmpeg import escape_drawtext, escape_filter_path, find_font_file, run_ffmpeg
from videodna.media.transcode import concat_segments

SAMPLE_SHOTS: list[tuple[float, str, str, int]] = [
    # (fraction of total duration, background color, caption, tone Hz)
    (0.25, "0xd8c3a5", "1 · O menino segura o copo", 330),
    (0.15, "0x5d7fa3", "2 · O copo cai", 392),
    (0.12, "0x7a4e2d", "3 · O copo quebra", 440),
    (0.18, "0x5f7d6a", "4 · A mãe entra na sala", 262),
    (0.12, "0x8c6a9e", "5 · A mãe percebe o copo", 294),
    (0.18, "0xc77d3a", "6 · A mãe briga com o menino", 349),
]


def generate_sample_video(
    dest: Path,
    *,
    duration: float = 12.0,
    width: int = 1280,
    height: int = 720,
    fps: int = 25,
) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    font = find_font_file()
    with tempfile.TemporaryDirectory(prefix="videodna-sample-") as tmp:
        parts: list[Path] = []
        for i, (fraction, color, caption, tone) in enumerate(SAMPLE_SHOTS):
            seg_dur = round(duration * fraction, 3)
            filters = [
                # moving "character" block keeps every shot alive
                f"drawbox=x='(iw-160)*t/{seg_dur}':y=ih*0.45:w=160:h=220:color=white@0.85:t=fill",
                "drawbox=x=iw*0.08:y=ih*0.72:w=iw*0.84:h=ih*0.2:color=black@0.25:t=fill",
            ]
            if font:
                filters.append(
                    f"drawtext=fontfile={escape_filter_path(font)}:text='{escape_drawtext(caption)}':"
                    "fontsize=44:fontcolor=white:borderw=3:bordercolor=black@0.6:"
                    "x=(w-text_w)/2:y=h*0.1"
                )
            out = Path(tmp) / f"part{i}.mp4"
            run_ffmpeg(
                [
                    "-f",
                    "lavfi",
                    "-i",
                    f"color=c={color}:s={width}x{height}:r={fps}:d={seg_dur}",
                    "-f",
                    "lavfi",
                    "-i",
                    f"sine=frequency={tone}:sample_rate=44100:duration={seg_dur}",
                    "-vf",
                    ",".join(filters),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-pix_fmt",
                    "yuv420p",
                    "-r",
                    str(fps),
                    "-c:a",
                    "aac",
                    "-b:a",
                    "96k",
                    "-shortest",
                    str(out),
                ]
            )
            parts.append(out)
        concat_segments(parts, dest, fps=fps)
    return dest
