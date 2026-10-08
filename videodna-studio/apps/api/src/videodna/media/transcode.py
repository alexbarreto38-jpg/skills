"""Proxies, posters, segment cutting, splicing, concatenation and audio muxing.

Every segment the pipeline produces uses the same encoder settings
(`_video_args`), so concatenation can be a stream copy and the final timeline
stays frame-accurate.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from videodna.logging_setup import get_logger
from videodna.media.ffmpeg import FFmpegError, ffprobe_json, run_ffmpeg

log = get_logger(__name__)


def _scale_filter(resolution: int) -> str:
    """Scale so the *short* side is `resolution` ("720p" for a vertical phone video
    is 720x1280, not 406x720). Never upscale; keep aspect; even sizes for yuv420p."""
    return (
        f"scale='if(gte(iw,ih),-2,min({resolution},iw))'"
        f":'if(gte(iw,ih),min({resolution},ih),-2)':flags=bicubic"
    )


def _video_args(fps: float, crf: int = 21, preset: str = "veryfast") -> list[str]:
    return [
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-r",
        f"{fps:.6g}",
        "-video_track_timescale",
        "90000",
    ]


def make_proxy(src: Path, dest: Path, *, height: int = 720) -> Path:
    """Streaming-friendly 720p proxy for the editor (never load the original)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    video_args = [
        "-vf",
        _scale_filter(height),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
    ]
    tail = [
        "-movflags",
        "+faststart",
        # Drop private metadata (GPS, device) from derived files.
        "-map_metadata",
        "-1",
        str(dest),
    ]
    audio_args = ["-map", "0:a:0?", "-c:a", "aac", "-b:a", "128k"]
    try:
        run_ffmpeg(["-i", str(src), "-map", "0:v:0", *audio_args, *video_args, *tail])
    except FFmpegError:
        # A sound track FFmpeg cannot decode (e.g. a phone's spatial audio) must not
        # sink the whole analysis: the editor proxy works fine without sound.
        log.warning("proxy with audio failed; retrying without audio", extra={"src": src.name})
        run_ffmpeg(["-i", str(src), "-map", "0:v:0", "-an", *video_args, *tail])
    return dest


def make_poster(src: Path, dest: Path, *, time: float, width: int = 960) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-ss",
            f"{time:.3f}",
            "-i",
            str(src),
            "-frames:v",
            "1",
            "-vf",
            f"scale={width}:-2",
            "-q:v",
            "3",
            str(dest),
        ]
    )
    return dest


def extract_audio(src: Path, dest: Path) -> Path | None:
    """16 kHz mono WAV for speech providers; None if there is no audio."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = run_ffmpeg(["-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(dest)], check=False)
    return dest if proc.returncode == 0 and dest.exists() else None


def cut_segment(
    src: Path,
    dest: Path,
    *,
    start: float,
    end: float,
    height: int,
    fps: float,
    vf: str | None = None,
) -> Path:
    """Frame-accurate re-encoded cut [start, end) of `src` (video only)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    filters = [_scale_filter(height)]
    if vf:
        filters.append(vf)
    run_ffmpeg(
        [
            "-ss",
            f"{start:.3f}",
            "-i",
            str(src),
            "-t",
            f"{max(0.04, end - start):.3f}",
            "-an",
            "-vf",
            ",".join(filters),
            *_video_args(fps),
            "-map_metadata",
            "-1",
            str(dest),
        ]
    )
    return dest


def concat_segments(segments: list[Path], dest: Path, *, fps: float) -> Path:
    if not segments:
        raise FFmpegError("nothing to concatenate")
    dest.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(str(dest).encode()).hexdigest()[:8]
    listing = dest.parent / f".concat-{digest}.txt"
    listing.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in segments), encoding="utf-8"
    )
    try:
        proc = run_ffmpeg(
            ["-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(dest)],
            check=False,
        )
        if proc.returncode != 0:
            # Mismatched parameters: fall back to a re-encode.
            run_ffmpeg(
                [
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(listing),
                    *_video_args(fps),
                    str(dest),
                ]
            )
    finally:
        listing.unlink(missing_ok=True)
    return dest


def splice(
    base: Path,
    base_start: float,
    replacement: Path,
    rep_start: float,
    rep_end: float,
    dest: Path,
    *,
    height: int,
    fps: float,
) -> Path:
    """Replace [rep_start, rep_end) (absolute times) inside `base`, which starts at
    absolute time `base_start`. Used by localized repair."""
    base_duration = probe_duration(base)
    work = dest.parent / f".splice-{dest.stem}"
    work.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    rel_start = max(0.0, rep_start - base_start)
    rel_end = min(base_duration, rep_end - base_start)
    if rel_start > 0.04:
        parts.append(
            cut_segment(base, work / "pre.mp4", start=0.0, end=rel_start, height=height, fps=fps)
        )
    parts.append(replacement)
    if base_duration - rel_end > 0.04:
        parts.append(
            cut_segment(
                base, work / "post.mp4", start=rel_end, end=base_duration, height=height, fps=fps
            )
        )
    concat_segments(parts, dest, fps=fps)
    for p in work.iterdir():
        p.unlink(missing_ok=True)
    work.rmdir()
    return dest


def mux_final(
    video: Path,
    audio_source: Path | None,
    dest: Path,
    *,
    duration: float,
) -> Path:
    """Attach the original audio (LOCK AUDIO) and strip private metadata."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    args = ["-i", str(video)]
    if audio_source is not None:
        args += ["-i", str(audio_source), "-map", "0:v:0", "-map", "1:a:0?"]
    else:
        args += ["-map", "0:v:0"]
    args += [
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-t",
        f"{duration:.3f}",
        "-map_metadata",
        "-1",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    run_ffmpeg(args)
    return dest


def probe_duration(path: Path) -> float:
    data = ffprobe_json(path)
    fmt = data.get("format", {})
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    return float(video.get("duration") or fmt.get("duration") or 0.0)


def probe_video_size(path: Path) -> tuple[int, int]:
    data = ffprobe_json(path)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    return int(video.get("width") or 0), int(video.get("height") or 0)


def target_height(source_height: int, wanted: int) -> int:
    """Output resolution class (the short side, as in "720p"): never upscale, always even."""
    h = min(source_height, wanted)
    return h - (h % 2)
