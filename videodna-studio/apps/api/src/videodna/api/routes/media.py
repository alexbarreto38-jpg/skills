"""Serves local-storage media behind HMAC-signed URLs (supports Range, so the
player can seek). With S3 storage, clients receive presigned S3 URLs instead
and never hit this route."""

from __future__ import annotations

import mimetypes

from fastapi import APIRouter
from fastapi.responses import FileResponse

from videodna.api.deps import RuntimeDep
from videodna.errors import FILE_GONE, AppError, ErrorCode
from videodna.storage.local import LocalStorage
from videodna.storage.signing import InvalidToken, verify

router = APIRouter(tags=["media"])


@router.get("/media/{token}", include_in_schema=False)
def get_media(token: str, runtime: RuntimeDep) -> FileResponse:
    storage = runtime.storage
    if not isinstance(storage, LocalStorage):
        raise AppError(ErrorCode.NOT_FOUND, FILE_GONE)
    try:
        payload = verify(token, runtime.settings.signing_secret.get_secret_value())
    except InvalidToken as exc:
        raise AppError(
            ErrorCode.FORBIDDEN,
            "O link deste vídeo expirou. Atualize a página (F5) para criar um novo.",
        ) from exc
    key = payload["k"]
    if not storage.exists(key):
        raise AppError(ErrorCode.NOT_FOUND, FILE_GONE)
    path = storage.path_for(key)
    content_type = (
        payload.get("ct") or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    )
    headers = {"Cache-Control": "private, max-age=3600"}
    return FileResponse(
        path,
        media_type=content_type,
        filename=payload.get("dn"),
        content_disposition_type="attachment" if payload.get("dn") else "inline",
        headers=headers,
    )
