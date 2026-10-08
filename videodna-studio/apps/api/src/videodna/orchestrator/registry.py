"""Provider registry: the single place that knows which providers exist.

Business code never imports an adapter module. It asks the router for a
capability, and the router asks the registry for enabled, healthy providers.
"""

from __future__ import annotations

import importlib
import os
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from videodna.config import Settings, get_settings
from videodna.errors import AppError, ErrorCode
from videodna.features import FeatureFlags, get_feature_flags
from videodna.logging_setup import get_logger
from videodna.orchestrator.capabilities import KINDS_FOR_CAPABILITY, Capability, ProviderKind
from videodna.orchestrator.descriptor import ProviderDescriptor
from videodna.orchestrator.interfaces import INTERFACE_FOR_KIND, HealthStatus, ProviderAdapter

log = get_logger(__name__)

_HEALTH_TTL_SEC = 30.0


def load_descriptors(path: Path) -> list[ProviderDescriptor]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    descriptors = [ProviderDescriptor.model_validate(item) for item in raw.get("providers", [])]
    names = [d.name for d in descriptors]
    duplicates = {n for n in names if names.count(n) > 1}
    if duplicates:
        raise ValueError(f"duplicate provider names in {path}: {sorted(duplicates)}")
    for d in descriptors:
        wrong = [c.value for c in d.capabilities if d.kind not in KINDS_FOR_CAPABILITY[c]]
        if wrong:
            raise ValueError(f"provider {d.name} ({d.kind.value}) cannot serve {wrong}")
    return descriptors


def _parse_failures(csv: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for chunk in csv.split(","):
        if ":" in chunk:
            name, mode = chunk.split(":", 1)
            out[name.strip()] = mode.strip()
    return out


class ProviderRegistry:
    def __init__(
        self,
        descriptors: list[ProviderDescriptor],
        settings: Settings,
        flags: FeatureFlags,
    ) -> None:
        self.settings = settings
        self.flags = flags
        self._descriptors = {d.name: d for d in descriptors}
        self._adapters: dict[str, ProviderAdapter] = {}
        self._health: dict[str, tuple[float, HealthStatus]] = {}
        self._health_overrides: dict[str, HealthStatus] = {}
        self._lock = threading.Lock()
        failures = _parse_failures(settings.mock_provider_failures)
        for name, mode in failures.items():
            if name in self._descriptors:
                self._descriptors[name].params.setdefault("failure_mode", mode)

    @classmethod
    def from_settings(
        cls, settings: Settings | None = None, flags: FeatureFlags | None = None
    ) -> ProviderRegistry:
        settings = settings or get_settings()
        return cls(
            load_descriptors(settings.providers_config_path),
            settings,
            flags or get_feature_flags(),
        )

    # --- enablement ------------------------------------------------------------

    def availability(self, descriptor: ProviderDescriptor) -> tuple[bool, str | None]:
        if not descriptor.enabled:
            return False, "desabilitado na configuração"
        if self.settings.ai_mock_mode and not (descriptor.mock or descriptor.local):
            return False, "AI_MOCK_MODE ativo: apenas providers mock/locais"
        if not self.settings.ai_mock_mode and descriptor.mock:
            return False, "provider mock fora do modo mock"
        if not self.flags.is_enabled(f"provider.{descriptor.name}"):
            return False, f"feature flag provider.{descriptor.name} desligada"
        if descriptor.requires_flag and not self.flags.is_enabled(descriptor.requires_flag):
            return False, f"requer feature flag {descriptor.requires_flag}"
        missing = [name for name in descriptor.credentials_env if not os.environ.get(name)]
        if missing:
            return False, f"credencial ausente: {', '.join(missing)}"
        return True, None

    def descriptors(self) -> list[ProviderDescriptor]:
        return list(self._descriptors.values())

    def descriptor(self, name: str) -> ProviderDescriptor:
        try:
            return self._descriptors[name]
        except KeyError as exc:
            raise AppError(
                ErrorCode.NO_PROVIDER_AVAILABLE,
                "Um serviço de IA necessário não está configurado. "
                "Peça a quem instalou o VideoDNA Studio para revisar a configuração.",
                details={"provider": name},
            ) from exc

    def candidates(
        self, capability: Capability | None = None, kind: ProviderKind | None = None
    ) -> list[ProviderDescriptor]:
        return [
            d
            for d in self._descriptors.values()
            if (capability is None or d.supports(capability)) and (kind is None or d.kind == kind)
        ]

    # --- adapters ----------------------------------------------------------------

    def adapter(self, name: str) -> ProviderAdapter:
        with self._lock:
            if name in self._adapters:
                return self._adapters[name]
            descriptor = self.descriptor(name)
            module_name, _, class_name = descriptor.adapter.partition(":")
            cls = getattr(importlib.import_module(module_name), class_name)
            expected = INTERFACE_FOR_KIND[descriptor.kind]
            if not issubclass(cls, expected):
                raise TypeError(f"{descriptor.adapter} must implement {expected.__name__}")
            instance = cls(descriptor, self.settings)
            self._adapters[name] = instance
            return instance

    # --- health ------------------------------------------------------------------

    def set_health_override(self, name: str, status: HealthStatus | None) -> None:
        if status is None:
            self._health_overrides.pop(name, None)
        else:
            self._health_overrides[name] = status

    def health(self, name: str) -> HealthStatus:
        if name in self._health_overrides:
            return self._health_overrides[name]
        cached = self._health.get(name)
        now = time.monotonic()
        if cached and now - cached[0] < _HEALTH_TTL_SEC:
            return cached[1]
        try:
            status = self.adapter(name).health_check()
        except Exception:  # health checks must never take the router down
            log.exception("provider health check failed", extra={"provider": name})
            status = HealthStatus.DOWN
        self._health[name] = (now, status)
        return status

    def describe(self) -> list[dict[str, Any]]:
        out = []
        for d in self._descriptors.values():
            available, reason = self.availability(d)
            out.append(
                {
                    "name": d.name,
                    "kind": d.kind.value,
                    "description": d.description,
                    "mock": d.mock,
                    "local": d.local,
                    "enabled": available,
                    "disabledReason": reason,
                    "priority": d.priority,
                    "capabilities": [c.value for c in d.capabilities],
                    "features": d.features,
                    "limits": d.limits.model_dump(mode="json"),
                    "health": self.health(d.name).value if available else None,
                    "models": [m.id for m in d.models],
                    "docsUrl": d.docs_url,
                }
            )
        return out


@lru_cache
def get_registry() -> ProviderRegistry:
    return ProviderRegistry.from_settings()
