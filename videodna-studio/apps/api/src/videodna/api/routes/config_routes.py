from __future__ import annotations

from fastapi import APIRouter

from videodna.api import schemas as s
from videodna.api.deps import RuntimeDep, UserDep
from videodna.domain.enums import QualityMode
from videodna.services.uploads import RIGHTS_STATEMENT

router = APIRouter(tags=["system"])


@router.get("/config", response_model=s.AppConfigOut, summary="Configuração pública do app")
def app_config(runtime: RuntimeDep) -> s.AppConfigOut:
    settings = runtime.settings
    return s.AppConfigOut(
        app_name=settings.app_name,
        mock_mode=settings.ai_mock_mode,
        environment=settings.app_env,
        currency=settings.cost_currency,
        low_confidence_threshold=settings.analysis_low_confidence_threshold,
        quality_modes=list(QualityMode),
        default_quality_mode=QualityMode.BALANCED,
        features=runtime.flags.as_dict(),
        upload_max_bytes=settings.upload_max_bytes,
        upload_allowed_content_types=settings.upload_allowed_content_types,
        video_max_duration_sec=settings.video_max_duration_sec,
        rights_statement=RIGHTS_STATEMENT,
    )


@router.get("/providers", response_model=list[s.ProviderOut], summary="Provider Registry")
def providers(runtime: RuntimeDep, _user: UserDep) -> list[s.ProviderOut]:
    return [s.ProviderOut.model_validate(p) for p in runtime.registry.describe()]
