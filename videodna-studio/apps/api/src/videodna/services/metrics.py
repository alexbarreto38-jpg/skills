"""Internal dashboard metrics (spec §57/§61/§62)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from videodna.api import schemas as s
from videodna.db import models as m
from videodna.domain.enums import (
    AnalysisStatus,
    CostKind,
    JobKind,
    QAIssueStatus,
    SourceVideoStatus,
    UsageStatus,
)
from videodna.runtime import Runtime


def metrics(db: Session, runtime: Runtime, days: int = 30) -> s.MetricsOut:
    since = datetime.now(UTC) - timedelta(days=days)

    generation_counts = dict(
        db.execute(
            select(m.Job.status, func.count())
            .where(m.Job.kind == JobKind.GENERATION, m.Job.created_at >= since)
            .group_by(m.Job.status)
        ).all()
    )
    durations = db.execute(
        select(m.Job.started_at, m.Job.finished_at).where(
            m.Job.kind == JobKind.GENERATION,
            m.Job.finished_at.is_not(None),
            m.Job.started_at.is_not(None),
            m.Job.created_at >= since,
        )
    ).all()
    avg = (
        sum((f - s_).total_seconds() for s_, f in durations) / len(durations) if durations else None
    )

    provider_rows = db.execute(
        select(
            m.ProviderUsage.provider,
            m.ProviderUsage.capability,
            func.count(),
            func.sum(case((m.ProviderUsage.status == UsageStatus.SUCCESS, 1), else_=0)),
            func.avg(m.ProviderUsage.latency_ms),
            func.coalesce(func.sum(m.ProviderUsage.actual_cost), 0),
            func.sum(case((m.ProviderUsage.attempt > 1, 1), else_=0)),
        )
        .where(m.ProviderUsage.created_at >= since)
        .group_by(m.ProviderUsage.provider, m.ProviderUsage.capability)
        .order_by(m.ProviderUsage.provider)
    ).all()
    providers = [
        {
            "provider": p,
            "capability": c,
            "calls": int(n),
            "successRate": round(int(ok or 0) / int(n), 4) if n else None,
            "avgLatencyMs": round(float(lat or 0), 1),
            "cost": round(float(cost or 0), 4),
            "retries": int(retries or 0),
        }
        for p, c, n, ok, lat, cost, retries in provider_rows
    ]

    day = func.date(m.CostEntry.created_at)
    cost_by_day = [
        {"day": str(d), "amount": round(float(a or 0), 4)}
        for d, a in db.execute(
            select(day, func.sum(m.CostEntry.amount))
            .where(m.CostEntry.kind == CostKind.ACTUAL, m.CostEntry.created_at >= since)
            .group_by(day)
            .order_by(day)
        ).all()
    ]

    return s.MetricsOut(
        currency=runtime.settings.cost_currency,
        projects=db.scalar(select(func.count()).select_from(m.Project)) or 0,
        videos_processed=db.scalar(
            select(func.count())
            .select_from(m.SourceVideo)
            .where(m.SourceVideo.status == SourceVideoStatus.READY)
        )
        or 0,
        analyses_completed=db.scalar(
            select(func.count())
            .select_from(m.VideoAnalysis)
            .where(m.VideoAnalysis.status == AnalysisStatus.COMPLETED)
        )
        or 0,
        generations={
            str(k.value if hasattr(k, "value") else k): int(v) for k, v in generation_counts.items()
        },
        total_cost=round(
            float(
                db.scalar(
                    select(func.coalesce(func.sum(m.CostEntry.amount), 0)).where(
                        m.CostEntry.kind == CostKind.ACTUAL
                    )
                )
                or 0
            ),
            2,
        ),
        avg_generation_sec=round(avg, 1) if avg is not None else None,
        retries=db.scalar(
            select(func.count()).select_from(m.ProviderUsage).where(m.ProviderUsage.attempt > 1)
        )
        or 0,
        qa_failures=db.scalar(
            select(func.count())
            .select_from(m.QAIssue)
            .where(m.QAIssue.status.in_([QAIssueStatus.UNRESOLVED, QAIssueStatus.REPAIRED]))
        )
        or 0,
        providers=providers,
        cost_by_day=cost_by_day,
    )
