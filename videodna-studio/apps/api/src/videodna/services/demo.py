"""Demo project: the zero-friction way to see the whole flow.

"Experimentar com um vídeo de exemplo" creates a project from the bundled
synthetic video (`media/sample_video.py`) and starts its analysis, so a
first-time user reaches the editor without having to find a video of their
own. The sample video tells the same story as the mock analysis fixture
(menino, copo, mãe), so in AI_MOCK_MODE everything on screen matches.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from videodna.db import models as m
from videodna.domain.settings import ProjectSettings
from videodna.errors import AppError, ErrorCode
from videodna.media.sample_video import generate_sample_video
from videodna.runtime import Runtime
from videodna.services.uploads import register_file

DEMO_NAME = "Exemplo — O menino e o copo"
DEMO_DESCRIPTION = (
    "Projeto de exemplo: um menino deixa um copo cair, o copo quebra e a mãe entra na sala."
)
DEMO_FILENAME = "exemplo-menino-e-o-copo.mp4"
DEMO_RIGHTS_STATEMENT = "Vídeo sintético de exemplo, gerado pelo próprio VideoDNA Studio."
# Bump when generate_sample_video changes, so cached copies are regenerated.
SAMPLE_VERSION = 1


def sample_video_path(runtime: Runtime) -> Path:
    """The sample video, generated once per machine and then reused."""
    cached = runtime.settings.work_dir / "samples" / f"menino-e-o-copo-v{SAMPLE_VERSION}.mp4"
    if not cached.exists():
        cached.parent.mkdir(parents=True, exist_ok=True)
        # Unique temp name: two first clicks at once must not write the same file.
        tmp = cached.with_name(f"{cached.stem}-{uuid.uuid4().hex}.mp4")
        try:
            generate_sample_video(tmp)
            tmp.replace(cached)
        finally:
            tmp.unlink(missing_ok=True)
    return cached


def create_demo_project(
    db: Session, runtime: Runtime, user: m.User, *, fresh: bool = False
) -> tuple[m.Project, m.Job | None, bool]:
    """Return (project, job to enqueue or None, reused).

    Without `fresh`, a second click opens the example the user already has
    instead of piling up copies.
    """
    if not runtime.settings.ai_mock_mode:
        # With real providers the sample would spend credits analysing coloured boxes.
        raise AppError(
            ErrorCode.CONFLICT, "O vídeo de exemplo só está disponível no modo demonstração."
        )
    # Serialise per user (a no-op on SQLite): a double click must not create two.
    db.execute(select(m.User.id).where(m.User.id == user.id).with_for_update())
    if not fresh:
        existing = db.scalars(
            select(m.Project)
            .where(m.Project.owner_id == user.id, m.Project.is_demo.is_(True))
            .order_by(m.Project.created_at.desc())
        ).first()
        if existing is not None:
            return existing, None, True
    project = m.Project(
        owner_id=user.id,
        name=DEMO_NAME,
        description=DEMO_DESCRIPTION,
        settings=ProjectSettings().model_dump(mode="json", by_alias=True),
        is_demo=True,
    )
    db.add(project)
    db.flush()
    _, job, created = register_file(
        db,
        runtime,
        user,
        project,
        path=sample_video_path(runtime),
        filename=DEMO_FILENAME,
        content_type="video/mp4",
        rights_statement=DEMO_RIGHTS_STATEMENT,
        analyze=True,
    )
    return project, (job if created else None), False
