from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from videodna.api.deps import RuntimeDep

router = APIRouter(tags=["system"])


@router.get("/healthz", summary="Liveness")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", summary="Readiness (database, storage, queue)")
def readyz(runtime: RuntimeDep) -> dict[str, object]:
    checks: dict[str, bool] = {}
    try:
        with runtime.session_factory() as session:
            session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
    checks["storage"] = runtime.storage.healthy()
    if runtime.settings.queue_backend == "dramatiq" and runtime.settings.redis_url:
        try:
            import redis

            redis.Redis.from_url(runtime.settings.redis_url, socket_timeout=1).ping()
            checks["queue"] = True
        except Exception:
            checks["queue"] = False
    return {"status": "ok" if all(checks.values()) else "degraded", "checks": checks}
