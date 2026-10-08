"""Dramatiq broker + actor. Start workers with:

    uv run dramatiq videodna.jobs.dramatiq_app --processes 2 --threads 2

or `uv run videodna worker`.

Retries are disabled at the broker level on purpose: a job is retried by our
own logic (per provider call, per shot), and the atomic claim makes a
redelivered message a no-op instead of a second (billable) run.
"""

from __future__ import annotations

import uuid

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from videodna.config import get_settings
from videodna.logging_setup import configure_logging

_settings = get_settings()
configure_logging(_settings.log_level, _settings.log_json)

broker = RedisBroker(url=_settings.redis_url or "redis://localhost:6379/0")
dramatiq.set_broker(broker)


@dramatiq.actor(queue_name="videodna", max_retries=0, time_limit=6 * 60 * 60 * 1000)
def process_job(job_id: str) -> None:
    from videodna.jobs.runner import run_job

    run_job(uuid.UUID(job_id))
