"""Application settings.

Every tunable lives here and is read from environment variables (or a `.env` file).
Secrets are typed as `SecretStr` so they never end up in logs or reprs.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parent
API_ROOT = PACKAGE_ROOT.parent.parent
DEFAULT_CONFIG_DIR = API_ROOT / "config"
DEFAULT_FIXTURES_DIR = PACKAGE_ROOT / "fixtures"

_INSECURE_DEFAULT_SECRET = "dev-insecure-change-me-not-for-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # --- runtime -------------------------------------------------------------
    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "VideoDNA Studio"
    api_base_url: str = "http://localhost:8000"
    # Comma separated in env vars (NoDecode: not parsed as JSON before the validator).
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    log_level: str = "INFO"
    log_json: bool = True

    # --- database / queue ------------------------------------------------------
    database_url: str = "postgresql+psycopg://videodna:videodna@localhost:5432/videodna"
    database_echo: bool = False
    redis_url: str | None = "redis://localhost:6379/0"
    # inline: run jobs synchronously in-process (tests). thread: run in a background
    # thread of the API process (local dev without Redis). dramatiq: real workers.
    queue_backend: Literal["inline", "thread", "dramatiq"] = "dramatiq"

    # --- storage -------------------------------------------------------------
    storage_backend: Literal["local", "s3"] = "local"
    storage_local_root: Path = Path("./var/storage")
    s3_endpoint_url: str | None = None
    # Endpoint the *browser* uses for presigned URLs (MinIO is "minio:9000" inside
    # compose but "localhost:9000" from the host).
    s3_public_endpoint_url: str | None = None
    s3_region: str = "us-east-1"
    s3_bucket: str = "videodna"
    s3_access_key_id: SecretStr | None = None
    s3_secret_access_key: SecretStr | None = None
    s3_force_path_style: bool = True
    signed_url_ttl_sec: int = 3600
    work_dir: Path = Path("./var/work")

    # --- security --------------------------------------------------------------
    signing_secret: SecretStr = SecretStr(_INSECURE_DEFAULT_SECRET)
    jwt_secret: SecretStr = SecretStr(_INSECURE_DEFAULT_SECRET)
    jwt_ttl_minutes: int = 60 * 24
    # Requests without a token act as the seeded dev user. Refused in production.
    auth_dev_autologin: bool = True
    dev_user_email: str = "dev@videodna.local"
    rate_limit_per_minute: int = 120
    rate_limit_expensive_per_minute: int = 12

    # --- AI orchestrator -----------------------------------------------------
    ai_mock_mode: bool = True
    providers_config_path: Path = DEFAULT_CONFIG_DIR / "providers.yaml"
    features_config_path: Path = DEFAULT_CONFIG_DIR / "features.yaml"
    # Comma separated overrides, e.g. "smart_mode=true,provider.mock-gen=false".
    feature_flags: str = ""
    # Comma separated "<provider>:<mode>" failure injection for mock providers.
    mock_provider_failures: str = ""
    mock_font_file: Path | None = None
    provider_timeout_sec: float = 600.0
    provider_max_attempts: int = 3
    provider_backoff_base_sec: float = 0.5

    # --- upload / media validation ------------------------------------------
    upload_max_bytes: int = 2 * 1024**3
    upload_part_size: int = 16 * 1024**2
    upload_allowed_content_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "video/mp4",
            "video/quicktime",
            "video/webm",
            "video/x-matroska",
            "video/x-msvideo",
        ]
    )
    video_max_duration_sec: float = 600.0
    video_min_duration_sec: float = 0.5
    video_allowed_codecs: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["h264", "hevc", "vp8", "vp9", "av1", "mpeg4", "prores"]
    )
    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"
    ffmpeg_timeout_sec: float = 1800.0

    # --- analysis ------------------------------------------------------------
    analysis_pipeline_version: str = "1.0.0"
    analysis_low_confidence_threshold: float = 0.6
    analysis_max_keyframes: int = 120
    analysis_keyframe_interval_sec: float = 4.0
    shot_detection_threshold: float = 0.30
    shot_min_duration_sec: float = 0.4
    proxy_height: int = 720
    final_height: int = 1080

    # --- generation ----------------------------------------------------------
    generation_max_retries_economy: int = 1
    generation_max_retries_balanced: int = 2
    generation_max_retries_max: int = 3
    qa_repair_min_severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    cost_currency: str = "BRL"
    # "USD:5.40,EUR:6.10" — rates *you* configure; nothing is assumed.
    fx_rates_to_base: str = ""
    cost_overrun_tolerance: float = 0.25
    fallback_max_cost_increase: float = 0.5

    # --- privacy / retention -------------------------------------------------
    media_retention_days: int | None = 30

    # --- observability (optional integrations) -------------------------------
    sentry_dsn: SecretStr | None = None
    otel_exporter_otlp_endpoint: str | None = None

    @field_validator(
        "cors_origins", "upload_allowed_content_types", "video_allowed_codecs", mode="before"
    )
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Accept both `a,b,c` and a JSON list from environment variables."""
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [item.strip() for item in text.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def _refuse_insecure_production(self) -> Settings:
        if self.app_env == "production":
            insecure = _INSECURE_DEFAULT_SECRET
            if self.jwt_secret.get_secret_value() == insecure:
                raise ValueError("JWT_SECRET must be set in production")
            if self.signing_secret.get_secret_value() == insecure:
                raise ValueError("SIGNING_SECRET must be set in production")
            if self.auth_dev_autologin:
                raise ValueError("AUTH_DEV_AUTOLOGIN cannot be enabled in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def max_retries_for(self, quality_mode: str) -> int:
        return {
            "ECONOMY": self.generation_max_retries_economy,
            "BALANCED": self.generation_max_retries_balanced,
            "MAX": self.generation_max_retries_max,
        }.get(quality_mode.upper(), self.generation_max_retries_balanced)

    def fx_rates(self) -> dict[str, float]:
        rates: dict[str, float] = {self.cost_currency.upper(): 1.0}
        for chunk in self.fx_rates_to_base.split(","):
            if ":" not in chunk:
                continue
            code, rate = chunk.split(":", 1)
            rates[code.strip().upper()] = float(rate)
        return rates


@lru_cache
def get_settings() -> Settings:
    return Settings()
