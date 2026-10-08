"""Feature flags (config/features.yaml + FEATURE_FLAGS env overrides)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from videodna.config import Settings, get_settings


class FeatureFlags:
    def __init__(self, definitions: dict[str, dict[str, Any]], overrides: dict[str, bool]):
        self._definitions = definitions
        self._overrides = overrides

    @classmethod
    def load(cls, path: Path, overrides_csv: str = "") -> FeatureFlags:
        definitions: dict[str, dict[str, Any]] = {}
        if path.exists():
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            definitions = dict(raw.get("flags", {}))
        overrides: dict[str, bool] = {}
        for chunk in overrides_csv.split(","):
            if "=" not in chunk:
                continue
            name, value = chunk.split("=", 1)
            overrides[name.strip()] = value.strip().lower() in {"1", "true", "yes", "on"}
        return cls(definitions, overrides)

    def is_enabled(self, name: str) -> bool:
        if name in self._overrides:
            return self._overrides[name]
        if name in self._definitions:
            return bool(self._definitions[name].get("default", False))
        # Providers are on unless a flag turns them off; unknown features are off.
        return name.startswith("provider.")

    def as_dict(self) -> dict[str, bool]:
        names = set(self._definitions) | set(self._overrides)
        return {name: self.is_enabled(name) for name in sorted(names)}

    def describe(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "enabled": self.is_enabled(name),
                "description": self._definitions.get(name, {}).get("description", ""),
            }
            for name in sorted(set(self._definitions) | set(self._overrides))
        ]


def build_feature_flags(settings: Settings) -> FeatureFlags:
    return FeatureFlags.load(settings.features_config_path, settings.feature_flags)


@lru_cache
def get_feature_flags() -> FeatureFlags:
    return build_feature_flags(get_settings())
