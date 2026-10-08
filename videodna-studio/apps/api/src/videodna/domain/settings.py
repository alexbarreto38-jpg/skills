"""Per-project creative settings: structural locks, quality mode, editor mode."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from videodna.domain.enums import QualityMode


class ProjectLocks(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_serialization_defaults_required=True,
    )

    story: bool = True  # LOCK STORY  — keep the narrative structure
    camera: bool = True  # LOCK CAMERA — angle, movement, distance, cuts
    motion: bool = True  # LOCK MOTION — poses, gestures, choreography
    audio: bool = True  # LOCK AUDIO  — keep original audio track
    timing: bool = True  # LOCK TIMING — duration and rhythm


class ProjectSettings(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_serialization_defaults_required=True,
    )

    locks: ProjectLocks = ProjectLocks()
    quality_mode: QualityMode = QualityMode.BALANCED
    # MANUAL is the MVP default; SMART/AUTO are behind feature flags.
    editor_mode: Literal["MANUAL", "SMART", "AUTO"] = "MANUAL"
