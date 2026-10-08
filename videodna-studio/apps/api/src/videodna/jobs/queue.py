"""Job queue backends.

* inline   — runs the job synchronously (tests).
* thread   — background thread inside the API process (local dev without Redis;
             not for production: media work belongs in workers).
* dramatiq — Redis-backed Dramatiq workers (default, production).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from videodna.config import get_settings
from videodna.logging_setup import get_logger

log = get_logger(__name__)


class JobQueue(ABC):
    @abstractmethod
    def enqueue(self, job_id: uuid.UUID) -> None: ...


class InlineQueue(JobQueue):
    def enqueue(self, job_id: uuid.UUID) -> None:
        from videodna.jobs.runner import run_job

        run_job(job_id)


class ThreadQueue(JobQueue):
    def __init__(self, workers: int = 2) -> None:
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="job")

    def enqueue(self, job_id: uuid.UUID) -> None:
        from videodna.jobs.runner import run_job

        future = self._pool.submit(run_job, job_id)
        future.add_done_callback(
            lambda f: f.exception() and log.error("job thread crashed", exc_info=f.exception())
        )


class DramatiqQueue(JobQueue):
    def enqueue(self, job_id: uuid.UUID) -> None:
        from videodna.jobs.dramatiq_app import process_job

        process_job.send(str(job_id))


_override: JobQueue | None = None


def set_queue(queue: JobQueue | None) -> None:
    global _override
    _override = queue


@lru_cache
def _default_queue() -> JobQueue:
    backend = get_settings().queue_backend
    if backend == "inline":
        return InlineQueue()
    if backend == "thread":
        return ThreadQueue()
    return DramatiqQueue()


def get_queue() -> JobQueue:
    return _override or _default_queue()
