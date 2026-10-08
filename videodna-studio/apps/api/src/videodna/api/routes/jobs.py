"""Jobs and real-time progress.

`GET /jobs/{id}/events` is a Server-Sent Events stream: it replays events
after `Last-Event-ID` (or `?after=`), then pushes new ones as the worker writes
them, and closes once the job is terminal. Events live in the database, so the
stream survives API restarts and works with any number of API replicas.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Header, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from videodna.api import schemas as s
from videodna.api.deps import DbDep, RuntimeDep, UserDep, get_owned_project
from videodna.db import models as m
from videodna.domain.enums import TERMINAL_JOB_STATUSES, JobKind
from videodna.errors import JOB_GONE, NotFound
from videodna.jobs.service import fail_stale_jobs, request_cancel

router = APIRouter(tags=["jobs"])

_POLL_SEC = 0.5
_HEARTBEAT_SEC = 15.0


def _owned_job(db, user, job_id: uuid.UUID) -> m.Job:
    job = db.get(m.Job, job_id)
    if job is None:
        raise NotFound(JOB_GONE)
    get_owned_project(db, user, job.project_id)
    return job


@router.get("/jobs/{job_id}", response_model=s.JobOut, summary="Status do job")
def get_job(job_id: uuid.UUID, db: DbDep, user: UserDep) -> s.JobOut:
    job = _owned_job(db, user, job_id)
    if fail_stale_jobs(db, project_id=job.project_id):
        db.commit()
        db.refresh(job)
    return s.JobOut.model_validate(job)


@router.get(
    "/jobs/{job_id}/events/history",
    response_model=list[s.JobEventOut],
    summary="Eventos do job (polling)",
)
def job_events(
    job_id: uuid.UUID,
    db: DbDep,
    user: UserDep,
    after: Annotated[int, Query()] = -1,
) -> list[s.JobEventOut]:
    _owned_job(db, user, job_id)
    rows = db.scalars(
        select(m.JobEvent)
        .where(m.JobEvent.job_id == job_id, m.JobEvent.seq > after)
        .order_by(m.JobEvent.seq)
        .limit(500)
    ).all()
    return [s.JobEventOut.model_validate(r) for r in rows]


@router.get(
    "/jobs/{job_id}/events",
    summary="Progresso em tempo real (Server-Sent Events)",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
def stream_job_events(
    job_id: uuid.UUID,
    db: DbDep,
    runtime: RuntimeDep,
    user: UserDep,
    after: Annotated[int, Query()] = -1,
    last_event_id: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    _owned_job(db, user, job_id)
    start = int(last_event_id) if last_event_id and last_event_id.isdigit() else after

    def fetch(cursor: int) -> tuple[list[dict], bool]:
        with runtime.session_factory() as session:
            rows = session.scalars(
                select(m.JobEvent)
                .where(m.JobEvent.job_id == job_id, m.JobEvent.seq > cursor)
                .order_by(m.JobEvent.seq)
                .limit(200)
            ).all()
            job = session.get(m.Job, job_id)
            terminal = job is None or job.status in TERMINAL_JOB_STATUSES
            return [
                s.JobEventOut.model_validate(r).model_dump(mode="json", by_alias=True) for r in rows
            ], terminal

    async def stream():
        cursor = start
        idle = 0.0
        yield "retry: 2000\n\n"
        while True:
            events, terminal = await run_in_threadpool(fetch, cursor)
            for event in events:
                cursor = event["seq"]
                data = json.dumps(event, ensure_ascii=False)
                yield f"id: {cursor}\nevent: progress\ndata: {data}\n\n"
            if terminal and not events:
                yield "event: end\ndata: {}\n\n"
                return
            if events:
                idle = 0.0
            else:
                idle += _POLL_SEC
                if idle >= _HEARTBEAT_SEC:
                    idle = 0.0
                    yield ": keep-alive\n\n"
            await asyncio.sleep(_POLL_SEC)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/jobs/{job_id}/cancel", response_model=s.JobOut, summary="Cancelar job")
def cancel_job(job_id: uuid.UUID, db: DbDep, user: UserDep) -> s.JobOut:
    job = _owned_job(db, user, job_id)
    request_cancel(db, job)
    db.commit()
    return s.JobOut.model_validate(job)


@router.get("/projects/{project_id}/jobs", response_model=list[s.JobOut], summary="Jobs do projeto")
def project_jobs(
    project_id: uuid.UUID,
    db: DbDep,
    user: UserDep,
    kind: Annotated[JobKind | None, Query()] = None,
) -> list[s.JobOut]:
    project = get_owned_project(db, user, project_id)
    query = select(m.Job).where(m.Job.project_id == project.id)
    if kind is not None:
        query = query.where(m.Job.kind == kind)
    rows = db.scalars(query.order_by(m.Job.created_at.desc()).limit(100)).all()
    return [s.JobOut.model_validate(r) for r in rows]
