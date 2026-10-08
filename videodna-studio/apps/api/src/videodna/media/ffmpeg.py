"""Thin, safe wrappers around the ffmpeg/ffprobe binaries.

Arguments are always passed as a list (never through a shell). stderr is
captured and logged on failure; callers receive a normalized AppError.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from videodna.config import get_settings
from videodna.errors import AppError, ErrorCode
from videodna.logging_setup import get_logger

log = get_logger(__name__)


class FFmpegError(AppError):
    def __init__(self, message: str, *, stderr: str = "", code: ErrorCode | None = None) -> None:
        super().__init__(code or ErrorCode.MEDIA_PROCESSING_FAILED)
        self.stderr = stderr
        self.detail = message


def _run_tool(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
    """subprocess.run for ffmpeg/ffprobe, with a useful error when the binary is missing."""
    try:
        return subprocess.run(cmd, **kwargs)  # noqa: S603 - fixed binary, list args
    except (FileNotFoundError, PermissionError) as exc:
        raise AppError(
            ErrorCode.MEDIA_PROCESSING_FAILED,
            f"Não encontrei o programa {cmd[0]!r}, que processa os vídeos. Instale o FFmpeg "
            "(ele traz o ffmpeg e o ffprobe) ou ajuste FFMPEG_BIN / FFPROBE_BIN.",
        ) from exc


def ffmpeg_available() -> bool:
    settings = get_settings()
    return bool(shutil.which(settings.ffmpeg_bin) and shutil.which(settings.ffprobe_bin))


def run_ffmpeg(
    args: list[str],
    *,
    timeout: float | None = None,
    check: bool = True,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    settings = get_settings()
    cmd = [settings.ffmpeg_bin, "-hide_banner", "-nostdin", "-y", *args]
    if input_bytes is not None:
        cmd.remove("-nostdin")
    try:
        proc = _run_tool(
            cmd,
            capture_output=True,
            timeout=timeout or settings.ffmpeg_timeout_sec,
            input=input_bytes,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError("ffmpeg timed out") from exc
    if check and proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", "replace")[-4000:]
        log.error(
            "ffmpeg failed", extra={"returncode": proc.returncode, "stderr_tail": stderr[-800:]}
        )
        raise FFmpegError("ffmpeg failed", stderr=stderr)
    return proc


def ffprobe_json(path: Path, extra: list[str] | None = None) -> dict[str, Any]:
    settings = get_settings()
    cmd = [
        settings.ffprobe_bin,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        *(extra or []),
        str(path),
    ]
    try:
        proc = _run_tool(cmd, capture_output=True, timeout=120, check=False)
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError("ffprobe timed out", code=ErrorCode.INVALID_VIDEO) from exc
    if proc.returncode != 0:
        raise FFmpegError(
            "ffprobe could not read the file",
            stderr=proc.stderr.decode("utf-8", "replace")[-2000:],
            code=ErrorCode.INVALID_VIDEO,
        )
    try:
        return json.loads(proc.stdout or b"{}")
    except json.JSONDecodeError as exc:
        raise FFmpegError("ffprobe returned invalid JSON", code=ErrorCode.INVALID_VIDEO) from exc


def keyframe_times(path: Path, limit: int = 2000) -> list[float]:
    """Container keyframe (I-frame) timestamps — decodes only keyframes."""
    settings = get_settings()
    cmd = [
        settings.ffprobe_bin,
        "-v",
        "error",
        "-skip_frame",
        "nokey",
        "-select_streams",
        "v:0",
        "-show_entries",
        "frame=pts_time,best_effort_timestamp_time",
        "-of",
        "json",
        str(path),
    ]
    proc = _run_tool(cmd, capture_output=True, timeout=300, check=False)
    if proc.returncode != 0:
        return []
    frames = json.loads(proc.stdout or b"{}").get("frames", [])
    times: list[float] = []
    for frame in frames[:limit]:
        value = frame.get("pts_time") or frame.get("best_effort_timestamp_time")
        if value is not None:
            times.append(round(float(value), 3))
    return times


BUNDLED_FONT = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "DejaVuSans-Bold.ttf"


def find_font_file() -> Path | None:
    settings = get_settings()
    if settings.mock_font_file and settings.mock_font_file.exists():
        return settings.mock_font_file
    if BUNDLED_FONT.exists():
        return BUNDLED_FONT
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        if Path(candidate).exists():
            return Path(candidate)
    fc_match = shutil.which("fc-match")
    if fc_match:
        proc = _run_tool(
            [fc_match, "-f", "%{file}", "sans"], capture_output=True, timeout=10, check=False
        )
        path = Path(proc.stdout.decode().strip())
        if proc.returncode == 0 and path.exists():
            return path
    return None


def escape_filter_path(path: Path) -> str:
    """A file path as an *unquoted* option value inside a filtergraph.

    FFmpeg unescapes twice: the filtergraph parser (special: \\ ' [ ] , ;) and
    then the filter's option parser (special: \\ ' :). A Windows drive letter
    (`C:/...`) or a name like `D'Ávila` breaks the filter unless both levels are
    escaped, innermost first.
    """
    value = path.as_posix().replace("\\", "/")
    for special in "\\':":
        value = value.replace(special, "\\" + special)
    escaped = ""
    for ch in value:
        escaped += "\\" + ch if ch in "\\'[],;" else ch
    return escaped


def escape_drawtext(text: str) -> str:
    """Escape text for ffmpeg's drawtext `text=` option inside a filtergraph."""
    out = text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")
    return out.replace("%", "\\%").replace(",", "\\,")
