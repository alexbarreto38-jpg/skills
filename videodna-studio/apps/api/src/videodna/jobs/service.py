"""Job lifecycle: idempotent creation, atomic claiming, progress events.

Idempotency (spec §47/§85): every expensive operation is a Job with a unique
(project, kind, idempotency_key). Repeating the request returns the existing
job; a duplicated queue message cannot run it twice because claiming is an
atomic QUEUED -> PREPARING transition.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from videodna.db import models as m
from videodna.domain.enums import TERMINAL_JOB_STATUSES, JobKind, JobStatus, ProjectStatus
from videodna.errors import ErrorCode

SessionFactory = Callable[[], Session]


class JobCancelled(Exception):
    pass


def create_job(
    session: Session,
    *,
    project_id: uuid.UUID,
    kind: JobKind,
    idempotency_key: str,
    payload: dict[str, Any] | None = None,
    user_id: uuid.UUID | None = None,
    plan_id: uuid.UUID | None = None,
    message: str | None = None,
) -> tuple[m.Job, bool]:
    """Return (job, created). Safe under concurrent duplicate requests."""
    existing = session.scalar(
        select(m.Job).where(
            m.Job.project_id == project_id,
            m.Job.kind == kind,
            m.Job.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        if existing.status not in (JobStatus.FAILED, JobStatus.CANCELLED):
            return existing, False
        # A failed or cancelled run is history, not a reason to refuse a retry:
        # move it off the key so the retry gets a fresh job.
        existing.idempotency_key = f"{idempotency_key[:180]}#{existing.id.hex[:12]}"
        session.flush()
    cls = m.JOB_CLASS_BY_KIND[kind]
    job = cls(
        project_id=project_id,
        user_id=user_id,
        idempotency_key=idempotency_key,
        payload=payload or {},
        plan_id=plan_id,
        status=JobStatus.QUEUED,
        message=message or "Na fila",
    )
    try:
        with session.begin_nested():
            session.add(job)
            session.flush()
    except IntegrityError:
        existing = session.scalar(
            select(m.Job).where(
                m.Job.project_id == project_id,
                m.Job.kind == kind,
                m.Job.idempotency_key == idempotency_key,
            )
        )
        if existing is None:  # pragma: no cover - constraint violated by something else
            raise
        return existing, False
    session.add(
        m.JobEvent(job_id=job.id, seq=0, status=JobStatus.QUEUED.value, message=job.message)
    )
    return job, True


def claim_job(session_factory: SessionFactory, job_id: uuid.UUID) -> bool:
    now = datetime.now(UTC)
    with session_factory() as session:
        result = session.execute(
            update(m.Job)
            .where(
                m.Job.id == job_id,
                m.Job.status == JobStatus.QUEUED,
                m.Job.cancel_requested.is_(False),
            )
            .values(
                status=JobStatus.PREPARING,
                started_at=now,
                heartbeat_at=now,
                attempts=m.Job.attempts + 1,
                message="Preparando",
            )
            .execution_options(synchronize_session=False)
        )
        claimed = result.rowcount == 1
        if not claimed:
            # A job cancelled while still queued is closed here.
            session.execute(
                update(m.Job)
                .where(
                    m.Job.id == job_id,
                    m.Job.status == JobStatus.QUEUED,
                    m.Job.cancel_requested.is_(True),
                )
                .values(status=JobStatus.CANCELLED, finished_at=now, message="Cancelado")
                .execution_options(synchronize_session=False)
            )
        session.commit()
        return claimed


def request_cancel(session: Session, job: m.Job) -> m.Job:
    if job.status in TERMINAL_JOB_STATUSES:
        return job
    job.cancel_requested = True
    if job.status == JobStatus.QUEUED:
        job.status = JobStatus.CANCELLED
        job.finished_at = datetime.now(UTC)
        job.message = "Cancelado"
    return job


def _append_event(
    session: Session,
    job: m.Job,
    message: str,
    *,
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    seq = (
        session.scalar(select(func.max(m.JobEvent.seq)).where(m.JobEvent.job_id == job.id)) or 0
    ) + 1
    session.add(
        m.JobEvent(
            job_id=job.id,
            seq=seq,
            level=level,
            status=job.status.value,
            stage=job.stage,
            progress=job.progress,
            message=message[:500],
            data=data or {},
        )
    )


class JobReporter:
    """Writes progress in short, independent transactions so the API (and SSE)
    sees updates immediately, and checks for cancellation at every step."""

    def __init__(self, session_factory: SessionFactory, job_id: uuid.UUID) -> None:
        self._session_factory = session_factory
        self.job_id = job_id

    def progress(
        self,
        stage: str,
        progress: float,
        message: str,
        *,
        status: JobStatus | None = None,
        data: dict[str, Any] | None = None,
        level: str = "info",
    ) -> None:
        with self._session_factory() as session:
            job = session.get(m.Job, self.job_id)
            if job is None or job.cancel_requested:
                raise JobCancelled("cancel requested")
            if status is not None:
                job.status = status
            job.stage = stage
            job.progress = round(min(100.0, max(0.0, progress)), 2)
            job.message = message[:500]
            job.heartbeat_at = datetime.now(UTC)
            _append_event(session, job, message, level=level, data=data)
            session.commit()

    def log(self, message: str, *, level: str = "info", data: dict[str, Any] | None = None) -> None:
        with self._session_factory() as session:
            job = session.get(m.Job, self.job_id)
            if job is not None:
                _append_event(session, job, message, level=level, data=data)
                session.commit()

    def check_cancel(self) -> None:
        with self._session_factory() as session:
            cancelled = session.scalar(
                select(m.Job.cancel_requested).where(m.Job.id == self.job_id)
            )
        if cancelled:
            raise JobCancelled("cancel requested")

    def finish(
        self,
        status: JobStatus,
        *,
        message: str,
        result: dict[str, Any] | None = None,
        error_code: ErrorCode | None = None,
    ) -> None:
        with self._session_factory() as session:
            job = session.get(m.Job, self.job_id)
            if job is None:
                return
            job.status = status
            job.message = message[:500]
            job.finished_at = datetime.now(UTC)
            if status == JobStatus.COMPLETED:
                job.progress = 100.0
            if result is not None:
                job.result = result
            if error_code is not None:
                job.error_code = error_code.value
                job.error_message = message[:500]
            _append_event(
                session,
                job,
                message,
                level="error" if status == JobStatus.FAILED else "info",
                data={"errorCode": error_code.value} if error_code else None,
            )
            session.commit()


# A running job's worker refreshes heartbeat_at at least every HEARTBEAT_EVERY
# (jobs/runner.py). Silence for STALE_AFTER means the worker died mid-job:
# Docker stopped, the computer slept or restarted.
HEARTBEAT_EVERY = timedelta(seconds=20)
STALE_AFTER = timedelta(minutes=2)
INTERRUPTED_MESSAGE = (
    "O processamento foi interrompido (o VideoDNA foi fechado ou o computador reiniciou). "
    "Clique em tentar de novo."
)


def fail_stale_jobs(
    session: Session, *, project_id: uuid.UUID | None = None, now: datetime | None = None
) -> int:
    """Close jobs whose worker is gone, so the screen offers a retry instead of
    spinning forever. Returns how many were closed; the caller commits."""
    now = now or datetime.now(UTC)
    query = select(m.Job).where(
        m.Job.status.not_in([*TERMINAL_JOB_STATUSES, JobStatus.QUEUED]),
        m.Job.heartbeat_at < now - STALE_AFTER,
    )
    if project_id is not None:
        query = query.where(m.Job.project_id == project_id)
    jobs = list(session.scalars(query))
    for job in jobs:
        job.status = JobStatus.FAILED
        job.finished_at = now
        job.message = INTERRUPTED_MESSAGE
        job.error_code = ErrorCode.JOB_INTERRUPTED.value
        job.error_message = INTERRUPTED_MESSAGE
        _append_event(session, job, INTERRUPTED_MESSAGE, level="error")
        project = session.get(m.Project, job.project_id)
        if project is not None and project.status in (
            ProjectStatus.ANALYZING,
            ProjectStatus.GENERATING,
            ProjectStatus.UPLOADED,
        ):
            project.status = (
                ProjectStatus.READY if project.current_analysis_id else ProjectStatus.FAILED
            )
    if jobs:
        session.flush()
    return len(jobs)
