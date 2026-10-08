"""Deterministic technical QA (runs in every mode, costs nothing).

Checks what can be measured without a model: decodability, duration against
the expected shot (LOCK TIMING), output resolution, and black frames that the
original segment did not have.
"""

from __future__ import annotations

import re
from pathlib import Path

from videodna.domain.enums import QAIssueType, QASeverity
from videodna.errors import AppError
from videodna.media.ffmpeg import run_ffmpeg
from videodna.media.transcode import probe_duration, probe_video_size
from videodna.orchestrator.interfaces import (
    ProviderUsageInfo,
    QACheck,
    QAIssueCandidate,
    QAProvider,
    QARequest,
    QAResult,
)

_BLACK_RE = re.compile(r"black_start:\s*([0-9.]+)\s+black_end:\s*([0-9.]+)")


def _black_seconds(path: Path, start: float | None = None, duration: float | None = None) -> float:
    args: list[str] = []
    if start is not None:
        args += ["-ss", f"{start:.3f}"]
    args += ["-i", str(path)]
    if duration is not None:
        args += ["-t", f"{duration:.3f}"]
    args += ["-an", "-vf", "scale=320:-2,blackdetect=d=0.2:pix_th=0.10", "-f", "null", "-"]
    proc = run_ffmpeg(args, check=False)
    text = proc.stderr.decode("utf-8", "replace")
    return sum(float(b) - float(a) for a, b in _BLACK_RE.findall(text))


class TechnicalQAProvider(QAProvider):
    def inspect(self, request: QARequest) -> QAResult:
        shot = request.shot
        checks: list[QACheck] = []
        issues: list[QAIssueCandidate] = []
        try:
            duration = probe_duration(request.output_path)
            width, height = probe_video_size(request.output_path)
            checks.append(QACheck(name="decodificável", passed=True))
        except AppError:
            return QAResult(
                passed=False,
                score=0.0,
                summary="Saída não decodificável.",
                issues=[
                    QAIssueCandidate(
                        issue_type=QAIssueType.ARTIFACTS.value,
                        severity=QASeverity.CRITICAL,
                        start_time=shot.start_time,
                        end_time=shot.end_time,
                        description="O segmento gerado não pôde ser lido.",
                    )
                ],
                checks=[QACheck(name="decodificável", passed=False)],
            )

        fps = max(1.0, shot.end_frame - shot.start_frame + 1) / max(shot.duration, 0.04)
        tolerance = max(2.5 / fps, 0.08)
        duration_ok = abs(duration - shot.duration) <= tolerance
        checks.append(
            QACheck(
                name="duração",
                passed=duration_ok,
                detail=f"{duration:.3f}s vs {shot.duration:.3f}s",
            )
        )
        if not duration_ok:
            issues.append(
                QAIssueCandidate(
                    issue_type=QAIssueType.DURATION_MISMATCH.value,
                    severity=QASeverity.HIGH if request.constraints.timing else QASeverity.LOW,
                    start_time=shot.start_time,
                    end_time=shot.end_time,
                    description=(
                        f"Duração do segmento ({duration:.2f}s) difere do shot original "
                        f"({shot.duration:.2f}s)."
                    ),
                )
            )

        if request.expected_height:
            res_ok = abs(height - request.expected_height) <= 2
            checks.append(QACheck(name="resolução", passed=res_ok, detail=f"{width}x{height}"))
            if not res_ok:
                issues.append(
                    QAIssueCandidate(
                        issue_type=QAIssueType.RESOLUTION_MISMATCH.value,
                        severity=QASeverity.MEDIUM,
                        start_time=shot.start_time,
                        end_time=shot.end_time,
                        description=(
                            f"Resolução {width}x{height}, esperado {request.expected_height}p."
                        ),
                    )
                )

        black_out = _black_seconds(request.output_path)
        black_in = (
            _black_seconds(
                request.original_path,
                start=shot.start_time - request.timeline_offset,
                duration=shot.duration,
            )
            if black_out > 0.2
            else 0.0
        )
        black_ok = black_out - black_in <= 0.2
        checks.append(QACheck(name="quadros pretos", passed=black_ok, detail=f"{black_out:.2f}s"))
        if not black_ok:
            issues.append(
                QAIssueCandidate(
                    issue_type=QAIssueType.BLACK_FRAMES.value,
                    severity=QASeverity.HIGH,
                    start_time=shot.start_time,
                    end_time=shot.end_time,
                    description=f"{black_out - black_in:.2f}s de quadros pretos inesperados.",
                )
            )

        passed = not issues
        return QAResult(
            passed=passed,
            score=1.0 if passed else 0.5,
            summary="Verificação técnica OK." if passed else "Problemas técnicos encontrados.",
            issues=issues,
            checks=checks,
            usage=ProviderUsageInfo(model="ffmpeg"),
        )
