from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from videodna.api import schemas as s
from videodna.api.deps import AdminDep, DbDep, RuntimeDep
from videodna.services.metrics import metrics

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics", response_model=s.MetricsOut, summary="Métricas internas (admin)")
def admin_metrics(
    db: DbDep,
    runtime: RuntimeDep,
    _admin: AdminDep,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> s.MetricsOut:
    return metrics(db, runtime, days)
