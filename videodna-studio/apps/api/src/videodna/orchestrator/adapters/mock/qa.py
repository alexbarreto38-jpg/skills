"""Mock AI video inspector.

Deterministic so tests and demos are reproducible: the *first* attempt of a
shot whose edits involve physics (falling/breaking objects) reports the
replaced object disappearing mid-action — the classic failure of video edit
models — and the repair attempt passes. `persistent_failure: true` keeps
failing, to exercise the max-retry path.
"""

from __future__ import annotations

from videodna.domain.enums import DependencyType, EntityType, QAIssueType, QASeverity
from videodna.orchestrator.adapters.mock.base import MockMixin
from videodna.orchestrator.interfaces import (
    ProviderUsageInfo,
    QACheck,
    QAIssueCandidate,
    QAProvider,
    QARequest,
    QAResult,
)

_PHYSICS = {DependencyType.PHYSICS_MOTION.value, DependencyType.DESTRUCTION_FX.value}
_PHYSICAL_TYPES = {EntityType.OBJECT, EntityType.FURNITURE}
_CHECKS = [
    "personagens",
    "roupas",
    "objetos",
    "ação",
    "movimento",
    "continuidade",
    "cenário",
    "câmera",
    "anatomia",
    "flickering",
]


def _fmt(t: float) -> str:
    minutes, seconds = divmod(t, 60)
    return f"{int(minutes):02d}:{seconds:04.1f}"


class MockQAProvider(MockMixin, QAProvider):
    def inspect(self, request: QARequest) -> QAResult:
        self.failures.check()
        shot = request.shot
        issues: list[QAIssueCandidate] = []
        persistent = bool(self.params.get("persistent_failure"))
        physics = _PHYSICS & set(request.dependencies)
        if physics and (request.attempt == 0 or persistent):
            # The physical object (falling/breaking) is what disappears, not the shirt.
            target = next(
                (e for e in request.edits if e.entity_type in _PHYSICAL_TYPES and e.entity_key),
                next((e for e in request.edits if e.entity_key), None),
            )
            start = round(shot.start_time + 0.4 * shot.duration, 3)
            end = round(shot.start_time + 0.7 * shot.duration, 3)
            label = target.label if target else "objeto"
            issues.append(
                QAIssueCandidate(
                    issue_type=QAIssueType.ENTITY_DISAPPEARED.value,
                    severity=QASeverity.HIGH,
                    start_time=start,
                    end_time=end,
                    description=(
                        f"{label} desaparece entre {_fmt(start)} e {_fmt(end)} durante a ação."
                    ),
                    affected_entity_key=target.entity_key if target else None,
                )
            )
        failed_check = "objetos" if issues else None
        checks = [QACheck(name=name, passed=name != failed_check) for name in _CHECKS]
        passed = not issues
        return QAResult(
            passed=passed,
            score=0.93 if passed else 0.61,
            summary=(
                "Nenhuma inconsistência encontrada."
                if passed
                else f"{len(issues)} inconsistência(s) encontrada(s)."
            ),
            issues=issues,
            checks=checks,
            usage=ProviderUsageInfo(model=self.descriptor.default_model(), tokens=900),
        )
