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
    JOB_INTERRUPTED = "JOB_INTERRUPTED"
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
    ErrorCode.JOB_INTERRUPTED: 409,
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

# Every message says what happened and what to do now, in the words the screens
# use ("Analisar de novo", "Revisar e gerar", "Direitos de uso"). The person
# reading them is not technical: no "upload", "codec", "requisição" or "recurso".
USER_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.VALIDATION_ERROR: (
        "Alguma informação veio incompleta ou num formato inesperado. "
        "Confira o que preencheu e tente de novo."
    ),
    ErrorCode.NOT_FOUND: (
        "Não encontramos o que você abriu; talvez tenha sido excluído. "
        "Volte para a lista de projetos e abra de novo."
    ),
    ErrorCode.CONFLICT: (
        "Isso não pode ser feito agora porque o projeto mudou. "
        "Atualize a página (F5) e tente de novo."
    ),
    ErrorCode.UNAUTHORIZED: "Sua sessão terminou. Entre de novo para continuar.",
    ErrorCode.FORBIDDEN: ("Sua conta não tem acesso a esta parte. Volte para a lista de projetos."),
    ErrorCode.RATE_LIMITED: (
        "Foram muitos pedidos em pouco tempo. Espere cerca de 1 minuto e tente de novo."
    ),
    ErrorCode.RIGHTS_NOT_CONFIRMED: (
        "Falta confirmar que você pode usar este vídeo. "
        "Marque a caixa “Direitos de uso” e envie de novo."
    ),
    ErrorCode.INVALID_VIDEO: (
        "Não conseguimos abrir este arquivo como vídeo; ele pode estar corrompido. "
        "Salve o vídeo de novo em MP4 e envie outra vez."
    ),
    ErrorCode.UNSUPPORTED_MEDIA: (
        "Este tipo de arquivo não é aceito. "
        "Envie um vídeo MP4 (o formato mais comum), MOV, WebM, MKV ou AVI."
    ),
    ErrorCode.FILE_TOO_LARGE: (
        "O arquivo passa do tamanho máximo. Corte ou comprima o vídeo e envie de novo."
    ),
    ErrorCode.VIDEO_TOO_LONG: (
        "O vídeo passa da duração máxima. Corte um trecho menor e envie de novo."
    ),
    ErrorCode.UPLOAD_INCOMPLETE: ("O vídeo não chegou inteiro. Escolha o arquivo e envie de novo."),
    ErrorCode.MEDIA_PROCESSING_FAILED: (
        "Não conseguimos preparar este vídeo. "
        "Tente de novo; se repetir, salve o vídeo em MP4 e envie outra vez."
    ),
    ErrorCode.ANALYSIS_REQUIRED: (
        "Este vídeo ainda não foi analisado. "
        "Espere a análise terminar ou clique em “Analisar de novo”."
    ),
    ErrorCode.ANALYSIS_FAILED: (
        "A análise do vídeo não terminou. Clique em “Analisar de novo”; "
        "se falhar outra vez, use “Enviar outro vídeo”."
    ),
    ErrorCode.PLAN_STALE: (
        "Você mudou algo depois de abrir a revisão, então o plano e o custo mudaram. "
        "Abra “Revisar e gerar” de novo para ver o plano atualizado."
    ),
    ErrorCode.PLAN_BLOCKED: (
        "Algumas mudanças não podem ser geradas como estão (veja os avisos em vermelho). "
        "Volte ao editor e ajuste ou desfaça essas mudanças."
    ),
    ErrorCode.NOTHING_TO_GENERATE: (
        "Suas mudanças não alteram a imagem (por exemplo, só “Manter” ou correções de nome). "
        "Volte ao editor e escolha algo para trocar."
    ),
    ErrorCode.INSUFFICIENT_CREDITS: (
        "Esta geração passa do seu limite de gastos. "
        "Escolha a qualidade “Econômico”, gere uma prévia ou faça menos mudanças."
    ),
    ErrorCode.JOB_CANCELLED: (
        "Você cancelou este processamento. Quando quiser, é só começar de novo."
    ),
    ErrorCode.JOB_INTERRUPTED: (
        "O processamento foi interrompido (o VideoDNA foi fechado ou o computador reiniciou). "
        "Clique em tentar de novo."
    ),
    ErrorCode.PROVIDER_TIMEOUT: (
        "O serviço de IA demorou demais para responder. Espere um pouco e tente de novo."
    ),
    ErrorCode.PROVIDER_QUOTA: (
        "O serviço de IA atingiu o limite de uso por agora. "
        "Tente mais tarde ou escolha outra qualidade."
    ),
    ErrorCode.PROVIDER_UNAVAILABLE: (
        "O serviço de IA está fora do ar no momento. Tente de novo em alguns minutos."
    ),
    ErrorCode.PROVIDER_INVALID_REQUEST: (
        "O serviço de IA não aceitou este pedido. Tente outra opção ou simplifique a mudança."
    ),
    ErrorCode.PROVIDER_CONTENT_REJECTED: (
        "O serviço de IA recusou este conteúdo pelas regras dele. "
        "Tente outra mudança ou outro vídeo."
    ),
    ErrorCode.PROVIDER_ERROR: (
        "O serviço de IA teve um problema. Tente de novo; se repetir, escolha outra qualidade."
    ),
    ErrorCode.NO_PROVIDER_AVAILABLE: (
        "Nenhum serviço de IA consegue fazer isso agora. Tente mais tarde ou desfaça esta mudança."
    ),
    ErrorCode.GENERATION_FAILED: (
        "Não conseguimos gerar o vídeo. Suas mudanças continuam salvas: "
        "abra “Revisar e gerar” e tente de novo."
    ),
    ErrorCode.QA_FAILED: (
        "Não conseguimos conferir a qualidade do vídeo gerado. "
        "Assista ao resultado com atenção antes de usar."
    ),
    ErrorCode.INTERNAL_ERROR: (
        "Algo deu errado do nosso lado. Tente de novo em instantes; "
        "se continuar, rode o iniciar.ps1 de novo para reiniciar o VideoDNA Studio."
    ),
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
    """404 with a whole sentence written at the raise site.

    It used to take a noun ("Versão") and append "não encontrado", which read
    "Versão não encontrado" and never said what to do next.
    """

    def __init__(self, message: str | None = None) -> None:
        super().__init__(ErrorCode.NOT_FOUND, message)


# Things that go missing from more than one endpoint read the same everywhere.
PROJECT_GONE = (
    "Não encontramos este projeto; talvez tenha sido excluído. Volte para a lista de projetos."
)
ELEMENT_GONE = (
    "Este elemento não existe mais (talvez uma mudança o tenha removido). Atualize a página (F5)."
)
SUGGESTION_GONE = "Esta opção não está mais disponível. Escolha outra na lista."
PLAN_GONE = (
    "Este plano de geração não existe mais. Volte ao editor e clique em “Revisar e gerar” de novo."
)
JOB_GONE = "Não encontramos este processamento. Volte ao projeto para ver como ele está."
UPLOAD_GONE = "Este envio expirou ou foi cancelado. Escolha o arquivo e envie de novo."
FILE_GONE = "Este arquivo não existe mais. Atualize a página (F5)."
