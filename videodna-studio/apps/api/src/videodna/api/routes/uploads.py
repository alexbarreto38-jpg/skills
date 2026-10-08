from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile

from videodna.api import schemas as s
from videodna.api.deps import (
    DbDep,
    RuntimeDep,
    UserDep,
    expensive_rate_limit,
    get_owned_project,
    rate_limit,
)
from videodna.errors import AppError, ErrorCode
from videodna.jobs.queue import get_queue
from videodna.services import uploads as svc
from videodna.services.projects import source_out
from videodna.storage.signing import InvalidToken, verify

router = APIRouter(tags=["uploads"])


@router.post(
    "/projects/{project_id}/uploads",
    response_model=s.UploadInitResponse,
    status_code=201,
    dependencies=[Depends(rate_limit)],
    summary="Iniciar upload multipart (URLs assinadas por parte)",
)
def init_upload(
    project_id: uuid.UUID, req: s.UploadInitRequest, db: DbDep, runtime: RuntimeDep, user: UserDep
) -> s.UploadInitResponse:
    project = get_owned_project(db, user, project_id)
    out = svc.init_upload(db, runtime, project, req)
    db.commit()
    return out


@router.get(
    "/projects/{project_id}/uploads/{upload_id}",
    response_model=s.UploadStatusResponse,
    summary="Status do upload (partes recebidas, para retomar)",
)
def upload_status(
    project_id: uuid.UUID, upload_id: str, db: DbDep, runtime: RuntimeDep, user: UserDep
) -> s.UploadStatusResponse:
    project = get_owned_project(db, user, project_id)
    return svc.upload_status(db, runtime, project, upload_id)


@router.post(
    "/projects/{project_id}/uploads/{upload_id}/complete",
    response_model=s.UploadCompleteResponse,
    dependencies=[Depends(expensive_rate_limit)],
    summary="Concluir upload e iniciar a análise",
)
def complete_upload(
    project_id: uuid.UUID,
    upload_id: str,
    req: s.UploadCompleteRequest,
    db: DbDep,
    runtime: RuntimeDep,
    user: UserDep,
) -> s.UploadCompleteResponse:
    project = get_owned_project(db, user, project_id)
    source, job, created = svc.complete_upload(db, runtime, user, project, upload_id, req)
    db.commit()
    if job is not None and created:
        get_queue().enqueue(job.id)
        db.refresh(job)
    return s.UploadCompleteResponse(
        source_video=source_out(runtime, source),
        job=s.JobOut.model_validate(job) if job else None,
    )


@router.delete(
    "/projects/{project_id}/uploads/{upload_id}", status_code=204, summary="Abortar upload"
)
def abort_upload(
    project_id: uuid.UUID, upload_id: str, db: DbDep, runtime: RuntimeDep, user: UserDep
) -> Response:
    project = get_owned_project(db, user, project_id)
    svc.abort_upload(db, runtime, project, upload_id)
    db.commit()
    return Response(status_code=204)


@router.post(
    "/projects/{project_id}/upload",
    response_model=s.UploadCompleteResponse,
    status_code=201,
    dependencies=[Depends(expensive_rate_limit)],
    summary="Upload simples (multipart/form-data, uma requisição)",
)
def simple_upload(
    project_id: uuid.UUID,
    db: DbDep,
    runtime: RuntimeDep,
    user: UserDep,
    file: Annotated[UploadFile, File(description="Arquivo de vídeo")],
    rights_confirmed: Annotated[bool, Form(alias="rightsConfirmed")] = False,
    analyze: Annotated[bool, Form()] = True,
) -> s.UploadCompleteResponse:
    project = get_owned_project(db, user, project_id)
    source, job, created = svc.simple_upload(
        db,
        runtime,
        user,
        project,
        filename=file.filename or "video.mp4",
        content_type=file.content_type or "application/octet-stream",
        stream=file.file,
        rights_confirmed=rights_confirmed,
        analyze=analyze,
    )
    db.commit()
    if job is not None and created:
        get_queue().enqueue(job.id)
        db.refresh(job)
    return s.UploadCompleteResponse(
        source_video=source_out(runtime, source),
        job=s.JobOut.model_validate(job) if job else None,
    )


@router.put(
    "/storage/uploads/{upload_id}/parts/{part_number}",
    include_in_schema=False,
    summary="Receptor de partes (apenas storage local; S3 recebe direto)",
)
async def put_local_part(
    upload_id: str,
    part_number: int,
    request: Request,
    runtime: RuntimeDep,
    token: Annotated[str, Query()],
) -> Response:
    try:
        payload = verify(token, runtime.settings.signing_secret.get_secret_value())
    except InvalidToken as exc:
        raise AppError(ErrorCode.FORBIDDEN, "URL de upload inválida ou expirada.") from exc
    if payload.get("u") != upload_id or payload.get("n") != part_number:
        raise AppError(ErrorCode.FORBIDDEN, "URL de upload inválida.")
    body = await request.body()
    if len(body) > max(runtime.settings.upload_part_size * 2, 32 * 1024 * 1024):
        raise AppError(ErrorCode.FILE_TOO_LARGE)
    from videodna.storage.local import LocalStorage

    if not isinstance(runtime.storage, LocalStorage):
        raise AppError(ErrorCode.NOT_FOUND)
    try:
        etag = runtime.storage.write_part(upload_id, part_number, body)
    except FileNotFoundError as exc:
        raise AppError(ErrorCode.NOT_FOUND, "Upload não encontrado.") from exc
    return Response(status_code=200, headers={"ETag": f'"{etag}"'})
