"""FastAPI application factory."""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from videodna import __version__
from videodna.api.routes import (
    admin,
    analysis,
    auth,
    config_routes,
    edits,
    generation,
    health,
    jobs,
    media,
    projects,
    suggestions,
    uploads,
    versions,
)
from videodna.config import get_settings
from videodna.errors import USER_MESSAGES, AppError, ErrorCode
from videodna.logging_setup import bind_context, configure_logging, get_logger, reset_context
from videodna.observability import init_observability

log = get_logger("videodna.api")

TAGS = [
    {"name": "auth", "description": "Autenticação (JWT)."},
    {"name": "projects", "description": "Projetos, versões e duplicação."},
    {"name": "uploads", "description": "Upload multipart com URLs assinadas e retomada."},
    {"name": "analysis", "description": "Análise, Video DNA e elementos."},
    {"name": "edits", "description": "Operações de edição, undo/redo e impacto."},
    {"name": "suggestions", "description": "Suggestion Engine e previews."},
    {"name": "generation", "description": "Generation Plan, custo, geração, QA e resultados."},
    {"name": "jobs", "description": "Jobs e progresso em tempo real (SSE)."},
    {"name": "media", "description": "Entrega de mídia via URLs assinadas."},
    {"name": "admin", "description": "Métricas internas."},
    {"name": "system", "description": "Saúde e configuração."},
]


def _error(
    code: ErrorCode, message: str, status: int, request: Request, details=None
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code.value,
                "message": message,
                "details": details or {},
                "requestId": getattr(request.state, "request_id", None),
            }
        },
    )


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    init_observability(settings)

    app = FastAPI(
        title="VideoDNA Studio API",
        version=__version__,
        description=(
            "API do VideoDNA Studio — análise, desmontagem semântica, edição estrutural e "
            "reconstrução de vídeos com múltiplos modelos de IA. Erros seguem o formato "
            "`{error: {code, message, details, requestId}}` com códigos normalizados."
        ),
        openapi_tags=TAGS,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["ETag", "X-Request-Id"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        token = bind_context(request_id=request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            reset_context(token)
        response.headers["X-Request-Id"] = request_id
        if not request.url.path.startswith(("/media/", "/healthz")):
            log.info(
                "request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return _error(exc.code, exc.message, exc.status_code, request, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        details = {
            "fields": [
                {"loc": [str(p) for p in e.get("loc", [])], "msg": e.get("msg")}
                for e in exc.errors()
            ]
        }
        return _error(
            ErrorCode.VALIDATION_ERROR,
            USER_MESSAGES[ErrorCode.VALIDATION_ERROR],
            422,
            request,
            details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException):
        code = {
            404: ErrorCode.NOT_FOUND,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
        }.get(
            exc.status_code,
            ErrorCode.INTERNAL_ERROR if exc.status_code >= 500 else ErrorCode.CONFLICT,
        )
        return _error(code, USER_MESSAGES[code], exc.status_code, request)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        log.exception("unhandled error", extra={"path": request.url.path})
        return _error(
            ErrorCode.INTERNAL_ERROR, USER_MESSAGES[ErrorCode.INTERNAL_ERROR], 500, request
        )

    for module in (
        health,
        config_routes,
        auth,
        projects,
        uploads,
        media,
        analysis,
        edits,
        suggestions,
        generation,
        jobs,
        versions,
        admin,
    ):
        app.include_router(module.router)
    return app
