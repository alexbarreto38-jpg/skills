"""Technical analysis (stage A) and upload validation."""

from __future__ import annotations

from fractions import Fraction
from math import gcd
from pathlib import Path
from typing import Any

from videodna import wording
from videodna.config import Settings
from videodna.domain.video_dna import AudioStreamInfo, TechnicalMetadata
from videodna.errors import AppError, ErrorCode
from videodna.media.ffmpeg import ffprobe_json, keyframe_times

_NAMED_RATIOS = {
    "16:9": 16 / 9,
    "9:16": 9 / 16,
    "4:3": 4 / 3,
    "3:4": 3 / 4,
    "1:1": 1.0,
    "21:9": 21 / 9,
    "4:5": 4 / 5,
    "2.39:1": 2.39,
}


def _rate(value: str | None) -> float:
    if not value or value in {"0/0", "0"}:
        return 0.0
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return 0.0


def aspect_ratio_label(width: int, height: int) -> str:
    ratio = width / height
    for name, value in _NAMED_RATIOS.items():
        if abs(ratio - value) / value < 0.015:
            return name
    divisor = gcd(width, height) or 1
    return f"{width // divisor}:{height // divisor}"


def _rotation(stream: dict[str, Any]) -> int:
    for side in stream.get("side_data_list", []) or []:
        if "rotation" in side:
            return int(float(side["rotation"])) % 360
    tag = (stream.get("tags") or {}).get("rotate")
    return int(tag) % 360 if tag else 0


def probe(path: Path, *, with_keyframes: bool = True) -> TechnicalMetadata:
    data = ffprobe_json(path)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise AppError(
            ErrorCode.INVALID_VIDEO,
            "Este arquivo não tem imagem (parece ser só áudio). Envie um arquivo de vídeo.",
        )
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = data.get("format", {})

    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    rotation = _rotation(video)
    if rotation in {90, 270}:
        width, height = height, width
    if width <= 0 or height <= 0:
        raise AppError(
            ErrorCode.INVALID_VIDEO,
            "Não conseguimos ler o tamanho da imagem deste vídeo; ele pode estar corrompido. "
            "Salve o vídeo de novo em MP4 e envie outra vez.",
        )

    fps = _rate(video.get("avg_frame_rate")) or _rate(video.get("r_frame_rate"))
    duration = float(video.get("duration") or fmt.get("duration") or 0.0)
    if fps <= 0 or duration <= 0:
        raise AppError(
            ErrorCode.INVALID_VIDEO,
            "Não conseguimos ler a duração deste vídeo; ele pode estar corrompido. "
            "Salve o vídeo de novo em MP4 e envie outra vez.",
        )
    frame_count = int(video.get("nb_frames") or 0) or round(duration * fps)

    sar = video.get("sample_aspect_ratio") or "1:1"
    try:
        sar_value = float(Fraction(sar.replace(":", "/"))) if sar not in {"0:1", "N/A"} else 1.0
    except (ValueError, ZeroDivisionError):
        sar_value = 1.0
    display_ar = (width * sar_value) / height

    audio_info = None
    if audio is not None:
        audio_info = AudioStreamInfo(
            codec=audio.get("codec_name"),
            channels=int(audio["channels"]) if audio.get("channels") else None,
            sample_rate=int(audio["sample_rate"]) if audio.get("sample_rate") else None,
            bitrate=int(audio["bit_rate"]) if audio.get("bit_rate") else None,
        )

    return TechnicalMetadata(
        duration_sec=round(duration, 3),
        width=width,
        height=height,
        aspect_ratio=aspect_ratio_label(width, height),
        display_aspect_ratio=round(display_ar, 4),
        fps=round(fps, 3),
        frame_count=frame_count,
        video_codec=video.get("codec_name"),
        pixel_format=video.get("pix_fmt"),
        bitrate=int(fmt["bit_rate"]) if fmt.get("bit_rate") else None,
        container_format=fmt.get("format_name"),
        size_bytes=int(fmt["size"]) if fmt.get("size") else None,
        rotation=rotation,
        has_audio=audio is not None,
        audio=audio_info,
        keyframe_times=keyframe_times(path) if with_keyframes else [],
    )


def validate_technical(technical: TechnicalMetadata, settings: Settings) -> None:
    codec = (technical.video_codec or "").lower()
    if codec not in {c.lower() for c in settings.video_allowed_codecs}:
        raise AppError(
            ErrorCode.UNSUPPORTED_MEDIA,
            "Este vídeo foi gravado num formato que não aceitamos. "
            "Salve o vídeo de novo em MP4 e envie outra vez.",
            details={"codec": technical.video_codec, "allowed": settings.video_allowed_codecs},
        )
    if technical.duration_sec > settings.video_max_duration_sec:
        raise AppError(
            ErrorCode.VIDEO_TOO_LONG,
            f"O vídeo tem {wording.minutes(technical.duration_sec)} e o limite é "
            f"{wording.minutes(settings.video_max_duration_sec)}. "
            "Corte um trecho menor e envie de novo.",
            details={
                "durationSec": technical.duration_sec,
                "maxDurationSec": settings.video_max_duration_sec,
            },
        )
    if technical.duration_sec < settings.video_min_duration_sec:
        has = wording.duration(technical.duration_sec)
        needs = wording.duration(settings.video_min_duration_sec)
        raise AppError(
            ErrorCode.INVALID_VIDEO,
            f"O vídeo é curto demais para analisar (tem {has}). "
            f"Envie um vídeo com pelo menos {needs}.",
        )
