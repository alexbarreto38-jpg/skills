"""Media retention (spec §52): delete media past `retention_until`.

Run periodically (cron / scheduler) with `videodna cleanup-media`. Project
metadata and edit history are kept; media objects are removed.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from videodna.db import models as m
from videodna.domain.enums import SourceVideoStatus
from videodna.logging_setup import get_logger
from videodna.runtime import Runtime
from videodna.services.projects import delete_media

log = get_logger(__name__)


def cleanup_expired_media(
    runtime: Runtime, *, now: datetime | None = None, dry_run: bool = False
) -> int:
    now = now or datetime.now(UTC)
    removed_projects = 0
    with runtime.session_factory() as session:
        project_ids = {
            row.project_id
            for row in session.scalars(
                select(m.SourceVideo).where(
                    m.SourceVideo.retention_until.is_not(None),
                    m.SourceVideo.retention_until < now,
                    m.SourceVideo.status != SourceVideoStatus.DELETED,
                )
            )
        }
        for project_id in project_ids:
            project = session.get(m.Project, project_id)
            if project is None:
                continue
            log.info(
                "retention: deleting media",
                extra={"project_id": str(project_id), "dry_run": dry_run},
            )
            if not dry_run:
                delete_media(session, runtime, project)
            removed_projects += 1
        if not dry_run:
            session.commit()
    return removed_projects
