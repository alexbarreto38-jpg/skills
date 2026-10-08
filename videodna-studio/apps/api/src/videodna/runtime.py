"""Process-wide singletons (settings, storage, registry, orchestrator, queue).

Tests replace these by calling `configure_runtime(...)`.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from videodna.config import Settings, get_settings
from videodna.db.session import get_sessionmaker
from videodna.features import FeatureFlags, build_feature_flags
from videodna.orchestrator.gateway import AIOrchestrator
from videodna.orchestrator.registry import ProviderRegistry, load_descriptors
from videodna.storage import build_storage
from videodna.storage.base import StorageBackend


@dataclass
class Runtime:
    settings: Settings
    session_factory: sessionmaker[Session]
    storage: StorageBackend
    flags: FeatureFlags
    registry: ProviderRegistry
    orchestrator: AIOrchestrator


_runtime: Runtime | None = None


def build_runtime(
    settings: Settings | None = None,
    session_factory: sessionmaker[Session] | None = None,
    storage: StorageBackend | None = None,
) -> Runtime:
    settings = settings or get_settings()
    session_factory = session_factory or get_sessionmaker()
    storage = storage or build_storage(settings)
    storage.ensure_ready()
    flags = build_feature_flags(settings)
    registry = ProviderRegistry(load_descriptors(settings.providers_config_path), settings, flags)
    orchestrator = AIOrchestrator(registry, settings, session_factory)
    return Runtime(settings, session_factory, storage, flags, registry, orchestrator)


def configure_runtime(runtime: Runtime | None) -> None:
    global _runtime
    _runtime = runtime


def get_runtime() -> Runtime:
    global _runtime
    if _runtime is None:
        _runtime = build_runtime()
    return _runtime
