"""FastAPI dependencies: DB session, current user, runtime, rate limits."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from videodna.api.ratelimit import RateLimiter
from videodna.api.security import decode_access_token
from videodna.db import models as m
from videodna.errors import PROJECT_GONE, AppError, ErrorCode, NotFound
from videodna.runtime import Runtime, get_runtime


def runtime_dep() -> Runtime:
    return get_runtime()


RuntimeDep = Annotated[Runtime, Depends(runtime_dep)]


def get_db(runtime: RuntimeDep) -> Iterator[Session]:
    session = runtime.session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


DbDep = Annotated[Session, Depends(get_db)]


def ensure_dev_user(session: Session, email: str) -> m.User:
    user = session.scalar(select(m.User).where(m.User.email == email))
    if user is None:
        user = m.User(email=email, display_name="Dev", is_admin=True)
        session.add(user)
        session.commit()
    return user


def current_user(request: Request, db: DbDep, runtime: RuntimeDep) -> m.User:
    settings = runtime.settings
    header = request.headers.get("authorization", "")
    token = header[7:].strip() if header.lower().startswith("bearer ") else None
    if token:
        user_id = decode_access_token(token, settings)
        user = db.get(m.User, user_id) if user_id else None
        if user is None:
            raise AppError(ErrorCode.UNAUTHORIZED)
        return user
    if settings.auth_dev_autologin and not settings.is_production:
        return ensure_dev_user(db, settings.dev_user_email)
    raise AppError(ErrorCode.UNAUTHORIZED)


UserDep = Annotated[m.User, Depends(current_user)]


def require_admin(user: UserDep) -> m.User:
    if not user.is_admin:
        raise AppError(
            ErrorCode.FORBIDDEN,
            "Esta área é só para administradores. Volte para a lista de projetos.",
        )
    return user


AdminDep = Annotated[m.User, Depends(require_admin)]


@lru_cache
def _limiter() -> RateLimiter:
    return RateLimiter(get_runtime().settings)


def rate_limit(request: Request, user: UserDep, runtime: RuntimeDep) -> None:
    _limiter().hit(f"u:{user.id}", runtime.settings.rate_limit_per_minute)


def expensive_rate_limit(request: Request, user: UserDep, runtime: RuntimeDep) -> None:
    """For endpoints that start paid work (analysis, previews, generation)."""
    _limiter().hit(f"x:{user.id}", runtime.settings.rate_limit_expensive_per_minute)


def get_owned_project(db: Session, user: m.User, project_id: uuid.UUID) -> m.Project:
    """Project isolation: other users' projects are indistinguishable from
    missing ones (404, not 403)."""
    project = db.get(m.Project, project_id)
    if project is None or project.owner_id != user.id:
        raise NotFound(PROJECT_GONE)
    return project
