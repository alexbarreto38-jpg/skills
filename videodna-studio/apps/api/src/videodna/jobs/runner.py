"""Executes one job: claim -> handler -> finish, with a private temp workdir.

Workers download media into `work_dir/<job id>/` and delete it afterwards, so
the web process never holds large files (spec §50).
"""

from __future__ import annotations

import importlib
import shutil
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import update
from sqlalchemy.orm import Session

from videodna.db import models as m
from videodna.domain.enums import JobKind, JobStatus
from videodna.errors import AppError, ErrorCode
from videodna.jobs.service import (
    HEARTBEAT_EVERY,
    JobCancelled,
    JobReporter,
    SessionFactory,
    claim_job,
)
from videodna.logging_setup import bind_context, get_logger, reset_context
from videodna.orchestrator.gateway import UsageContext
from videodna.runtime import Runtime, get_runtime

log = get_logger(__name__)

HANDLERS: dict[JobKind, str] = {
    JobKind.INGEST: "videodna.services.analysis.pipeline:run_ingest_job",
    JobKind.ANALYSIS: "videodna.services.analysis.pipeline:run_analysis_job",
    JobKind.PREVIEW: "videodna.services.previews:run_preview_job",
    JobKind.GENERATION: "videodna.services.generation.runner:run_generation_job",
}


@dataclass
class JobContext:
    job_id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID | None
    kind: JobKind
    payload: dict[str, Any]
    plan_id: uuid.UUID | None
    runtime: Runtime
    reporter: JobReporter
    workdir: Path
    result: dict[str, Any] = field(default_factory=dict)

    def session(self) -> Session:
        return self.runtime.session_factory()

    def usage(self, shot_key: str | None = None) -> UsageContext:
        return UsageContext(
            project_id=self.project_id,
            user_id=self.user_id,
            job_id=self.job_id,
            plan_id=self.plan_id,
            shot_key=shot_key,
        )


def _handler(kind: JobKind) -> Callable[[JobContext], dict[str, Any] | None]:
    module_name, _, func = HANDLERS[kind].partition(":")
    return getattr(importlib.import_module(module_name), func)


class _Heartbeat:
    """Refreshes heartbeat_at while a job runs, even during long silent steps
    (an FFmpeg pass, a provider call), so a stale heartbeat reliably means the
    worker is gone (see jobs.service.fail_stale_jobs)."""

    def __init__(self, session_factory: SessionFactory, job_id: uuid.UUID) -> None:
        self._session_factory = session_factory
        self._job_id = job_id
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"heartbeat-{job_id}", daemon=True)

    def __enter__(self) -> _Heartbeat:
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop.wait(HEARTBEAT_EVERY.total_seconds()):
            try:
                with self._session_factory() as session:
                    session.execute(
                        update(m.Job)
                        .where(m.Job.id == self._job_id)
                        .values(heartbeat_at=datetime.now(UTC))
                    )
                    session.commit()
            except Exception:  # a missed beat must never break the job itself
                log.warning("heartbeat failed", exc_info=True)


def run_job(job_id: uuid.UUID, runtime: Runtime | None = None) -> None:
    runtime = runtime or get_runtime()
    token = bind_context(job_id=str(job_id))
    try:
        if not claim_job(runtime.session_factory, job_id):
            log.info("job not claimable (already running, finished or cancelled); skipping")
            return
        with runtime.session_factory() as session:
            job = session.get(m.Job, job_id)
            assert job is not None
            ctx_token = bind_context(project_id=str(job.project_id), job_kind=job.kind.value)
            workdir = runtime.settings.work_dir.resolve() / str(job_id)
            workdir.mkdir(parents=True, exist_ok=True)
            ctx = JobContext(
                job_id=job.id,
                project_id=job.project_id,
                user_id=job.user_id,
                kind=job.kind,
                payload=dict(job.payload or {}),
                plan_id=job.plan_id,
                runtime=runtime,
                reporter=JobReporter(runtime.session_factory, job.id),
                workdir=workdir,
            )
        try:
            with _Heartbeat(runtime.session_factory, job_id):
                result = _handler(ctx.kind)(ctx) or {}
            message = result.pop("_message", "Concluído")
            ctx.reporter.finish(JobStatus.COMPLETED, message=message, result=result)
            log.info("job completed")
        except JobCancelled:
            ctx.reporter.finish(JobStatus.CANCELLED, message="Cancelado pelo usuário")
            log.info("job cancelled")
        except AppError as exc:
            log.warning(
                "job failed", extra={"error_code": exc.code.value, "detail": str(exc)[:300]}
            )
            ctx.reporter.finish(JobStatus.FAILED, message=exc.message, error_code=exc.code)
        except Exception:
            log.exception("job crashed")
            ctx.reporter.finish(
                JobStatus.FAILED,
                message="Erro interno durante o processamento.",
                error_code=ErrorCode.INTERNAL_ERROR,
            )
        finally:
            reset_context(ctx_token)
            shutil.rmtree(workdir, ignore_errors=True)
    finally:
        reset_context(token)
