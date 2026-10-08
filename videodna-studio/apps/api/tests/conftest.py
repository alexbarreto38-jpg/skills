"""Test fixtures.

Every test gets an isolated runtime: a fresh database (SQLite by default,
PostgreSQL when TEST_DATABASE_URL is set), filesystem storage in a temp dir,
the inline job queue and AI_MOCK_MODE. No network, no API keys.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from videodna import config as config_module
from videodna import features as features_module
from videodna.api import deps as deps_module
from videodna.api.app import create_app
from videodna.config import Settings
from videodna.db.base import Base
from videodna.db.session import build_engine
from videodna.jobs import queue as queue_module
from videodna.media.ffmpeg import ffmpeg_available
from videodna.runtime import Runtime, build_runtime, configure_runtime


def _database_url(tmp_path: Path) -> str:
    return os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    values = {
        "APP_ENV": "test",
        "DATABASE_URL": _database_url(tmp_path),
        "STORAGE_BACKEND": "local",
        "STORAGE_LOCAL_ROOT": str(tmp_path / "storage"),
        "WORK_DIR": str(tmp_path / "work"),
        "QUEUE_BACKEND": "inline",
        "AI_MOCK_MODE": "true",
        "API_BASE_URL": "http://testserver",
        "PROVIDER_BACKOFF_BASE_SEC": "0",
        "PROVIDER_TIMEOUT_SEC": "60",
        "LOG_JSON": "false",
        "LOG_LEVEL": "WARNING",
        "RATE_LIMIT_PER_MINUTE": "100000",
        "RATE_LIMIT_EXPENSIVE_PER_MINUTE": "100000",
        "REDIS_URL": "",
        "MOCK_PROVIDER_FAILURES": "",
        "FEATURE_FLAGS": "",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    config_module.get_settings.cache_clear()
    features_module.get_feature_flags.cache_clear()
    deps_module._limiter.cache_clear()
    queue_module._default_queue.cache_clear()
    return config_module.get_settings()


@pytest.fixture
def runtime(settings: Settings) -> Iterator[Runtime]:
    engine = build_engine(settings.database_url)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    rt = build_runtime(settings, session_factory)
    configure_runtime(rt)
    queue_module.set_queue(queue_module.InlineQueue())
    yield rt
    queue_module.set_queue(None)
    configure_runtime(None)
    engine.dispose()


@pytest.fixture
def client(runtime: Runtime) -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def sample_video(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not ffmpeg_available():
        pytest.skip("ffmpeg/ffprobe not installed")
    from videodna.media.sample_video import generate_sample_video

    path = tmp_path_factory.mktemp("media") / "sample.mp4"
    return generate_sample_video(path)
