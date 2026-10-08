"""Normalized error codes.

Raw provider/library errors never reach the client. Everything is mapped to an
`ErrorCode`, a user-facing message (pt-BR) and an HTTP status. The original
exception is logged server-side with the request/job id for debugging.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    # client / validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    RIGHTS_NOT_CONFIRMED = "RIGHTS_NOT_CONFIRMED"
    # media
    INVALID_VIDEO = "INVALID_VIDEO"
    UNSUPPORTED_MEDIA = "UNSUPPORTED_MEDIA"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    VIDEO_TOO_LONG = "VIDEO_TOO_LONG"
    UPLOAD_INCOMPLETE = "UPLOAD_INCOMPLETE"
    MEDIA_PROCESSING_FAILED = "MEDIA_PROCESSING_FAILED"
    # workflow
    ANALYSIS_REQUIRED = "ANALYSIS_REQUIRED"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    PLAN_STALE = "PLAN_STALE"
    PLAN_BLOCKED = "PLAN_BLOCKED"
    NOTHING_TO_GENERATE = "NOTHING_TO_GENERATE"
    INSUFFICIENT_CREDITS = "INSUFFICIENT_CREDITS"
    JOB_CANCELLED = "JOB_CANCELLED"
    # providers
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_QUOTA = "PROVIDER_QUOTA"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_INVALID_REQUEST = "PROVIDER_INVALID_REQUEST"
    PROVIDER_CONTENT_REJECTED = "PROVIDER_CONTENT_REJECTED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    NO_PROVIDER_AVAILABLE = "NO_PROVIDER_AVAILABLE"
    GENERATION_FAILED = "GENERATION_FAILED"
    QA_FAILED = "QA_FAILED"
    # fallback
    INTERNAL_ERROR = "INTERNAL_ERROR"


_HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.RIGHTS_NOT_CONFIRMED: 422,
    ErrorCode.INVALID_VIDEO: 422,
    ErrorCode.UNSUPPORTED_MEDIA: 415,
    ErrorCode.FILE_TOO_LARGE: 413,
    ErrorCode.VIDEO_TOO_LONG: 422,
    ErrorCode.UPLOAD_INCOMPLETE: 409,
    ErrorCode.MEDIA_PROCESSING_FAILED: 500,
    ErrorCode.ANALYSIS_REQUIRED: 409,
    ErrorCode.ANALYSIS_FAILED: 500,
    ErrorCode.PLAN_STALE: 409,
    ErrorCode.PLAN_BLOCKED: 409,
    ErrorCode.NOTHING_TO_GENERATE: 409,
    ErrorCode.INSUFFICIENT_CREDITS: 402,
    ErrorCode.JOB_CANCELLED: 409,
    ErrorCode.PROVIDER_TIMEOUT: 504,
    ErrorCode.PROVIDER_QUOTA: 503,
    ErrorCode.PROVIDER_UNAVAILABLE: 503,
    ErrorCode.PROVIDER_INVALID_REQUEST: 502,
    ErrorCode.PROVIDER_CONTENT_REJECTED: 422,
    ErrorCode.PROVIDER_ERROR: 502,
    ErrorCode.NO_PROVIDER_AVAILABLE: 503,
    ErrorCode.GENERATION_FAILED: 500,
    ErrorCode.QA_FAILED: 500,
    ErrorCode.INTERNAL_ERROR: 500,
}

USER_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.VALIDATION_ERROR: "Os dados enviados são inválidos.",
    ErrorCode.NOT_FOUND: "Recurso não encontrado.",
    ErrorCode.CONFLICT: "A operação conflita com o estado atual.",
    ErrorCode.UNAUTHORIZED: "Faça login para continuar.",
    ErrorCode.FORBIDDEN: "Você não tem permissão para esta ação.",
    ErrorCode.RATE_LIMITED: "Muitas requisições. Aguarde alguns instantes.",
    ErrorCode.RIGHTS_NOT_CONFIRMED: (
        "Confirme que você possui os direitos ou autorização para transformar este vídeo."
    ),
    ErrorCode.INVALID_VIDEO: "O arquivo não parece ser um vídeo válido.",
    ErrorCode.UNSUPPORTED_MEDIA: "Formato ou codec de vídeo não suportado.",
    ErrorCode.FILE_TOO_LARGE: "O arquivo excede o tamanho máximo permitido.",
    ErrorCode.VIDEO_TOO_LONG: "O vídeo excede a duração máxima permitida.",
    ErrorCode.UPLOAD_INCOMPLETE: "O upload ainda não foi concluído.",
    ErrorCode.MEDIA_PROCESSING_FAILED: "Falha ao processar o vídeo.",
    ErrorCode.ANALYSIS_REQUIRED: "Analise o vídeo antes de continuar.",
    ErrorCode.ANALYSIS_FAILED: "A análise do vídeo falhou.",
    ErrorCode.PLAN_STALE: (
        "As alterações mudaram desde que o plano foi criado. Gere um novo plano."
    ),
    ErrorCode.PLAN_BLOCKED: "O plano possui conflitos que precisam ser resolvidos.",
    ErrorCode.NOTHING_TO_GENERATE: "Nenhuma alteração para gerar.",
    ErrorCode.INSUFFICIENT_CREDITS: "Créditos insuficientes para esta geração.",
    ErrorCode.JOB_CANCELLED: "A tarefa foi cancelada.",
    ErrorCode.PROVIDER_TIMEOUT: "O serviço de IA demorou demais para responder.",
    ErrorCode.PROVIDER_QUOTA: "O serviço de IA atingiu o limite de uso.",
    ErrorCode.PROVIDER_UNAVAILABLE: "O serviço de IA está indisponível no momento.",
    ErrorCode.PROVIDER_INVALID_REQUEST: "O serviço de IA recusou a requisição.",
    ErrorCode.PROVIDER_CONTENT_REJECTED: "O serviço de IA recusou o conteúdo.",
    ErrorCode.PROVIDER_ERROR: "O serviço de IA retornou um erro.",
    ErrorCode.NO_PROVIDER_AVAILABLE: "Nenhum serviço de IA disponível para esta operação.",
    ErrorCode.GENERATION_FAILED: "A geração falhou.",
    ErrorCode.QA_FAILED: "A verificação de qualidade falhou.",
    ErrorCode.INTERNAL_ERROR: "Erro interno. Tente novamente.",
}


def http_status_for(code: ErrorCode) -> int:
    return _HTTP_STATUS.get(code, 500)


class AppError(Exception):
    """A normalized, user-presentable error."""

    def __init__(
        self,
        code: ErrorCode,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        self.code = code
        self.message = message or USER_MESSAGES.get(code, USER_MESSAGES[ErrorCode.INTERNAL_ERROR])
        self.details = details or {}
        self.status_code = status_code or http_status_for(code)
        super().__init__(f"{code}: {self.message}")


class NotFound(AppError):
    def __init__(self, what: str = "Recurso") -> None:
        super().__init__(ErrorCode.NOT_FOUND, f"{what} não encontrado.")
