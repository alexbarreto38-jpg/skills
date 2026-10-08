"""Uploads: multipart, signed part URLs, resumable (spec §49).

Flow (same for S3/MinIO and local storage):
  1. POST /projects/{id}/uploads            -> signed URL per part
  2. PUT <part url> (browser -> storage)     -> ETag per part
  3. GET /projects/{id}/uploads/{uploadId}   -> which parts already arrived (resume)
  4. POST .../complete {parts}               -> object assembled, ingest/analysis job

Cheap checks (declared type/size, rights confirmation) happen here; deep
checks (codec, duration, real container) happen in the worker with FFprobe,
because the API process never downloads the video.
"""

from __future__ import annotations

import math
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from videodna.api import schemas as s
from videodna.db import models as m
from videodna.domain.enums import JobKind, ProjectStatus, SourceVideoStatus
from videodna.errors import UPLOAD_GONE, AppError, ErrorCode
from videodna.jobs.service import create_job
from videodna.runtime import Runtime
from videodna.storage.base import source_key
from videodna.wording import file_size

RIGHTS_STATEMENT = (
    "Declaro que sou o autor deste vídeo, que possuo licença para utilizá-lo ou que tenho "
    "autorização expressa dos titulares para transformá-lo. Entendo que alterações feitas "
    "pela ferramenta não tornam o conteúdo automaticamente livre de direitos autorais."
)

_MAX_PARTS = 10_000


def _validate_declared(runtime: Runtime, content_type: str, size: int, rights: bool) -> None:
    settings = runtime.settings
    if not rights:
        raise AppError(ErrorCode.RIGHTS_NOT_CONFIRMED)
    if content_type.lower() not in {c.lower() for c in settings.upload_allowed_content_types}:
        raise AppError(
            ErrorCode.UNSUPPORTED_MEDIA,
            details={"contentType": content_type, "allowed": settings.upload_allowed_content_types},
        )
    if size > settings.upload_max_bytes:
        raise AppError(
            ErrorCode.FILE_TOO_LARGE,
            f"O arquivo tem {file_size(size)} e o limite é "
            f"{file_size(settings.upload_max_bytes)}. Corte ou comprima o vídeo e envie de novo.",
            details={"sizeBytes": size, "maxBytes": settings.upload_max_bytes},
        )


def _part_urls(runtime: Runtime, source: m.SourceVideo) -> list[s.UploadPartUrl]:
    ttl = runtime.settings.signed_url_ttl_sec
    return [
        s.UploadPartUrl(
            part_number=n,
            url=runtime.storage.signed_part_url(
                source.storage_key, source.upload_id, n, ttl_sec=ttl
            ),
        )
        for n in range(1, (source.upload_part_count or 0) + 1)
    ]


def init_upload(
    db: Session, runtime: Runtime, project: m.Project, req: s.UploadInitRequest
) -> s.UploadInitResponse:
    _validate_declared(runtime, req.content_type, req.size_bytes, req.rights_confirmed)
    part_size = runtime.settings.upload_part_size
    part_count = max(1, math.ceil(req.size_bytes / part_size))
    if part_count > _MAX_PARTS:
        part_size = math.ceil(req.size_bytes / _MAX_PARTS)
        part_count = math.ceil(req.size_bytes / part_size)

    source_id = uuid.uuid4()
    key = source_key(project.id, source_id, req.filename)
    upload_id = runtime.storage.create_multipart(key, req.content_type)
    source = m.SourceVideo(
        id=source_id,
        project_id=project.id,
        original_filename=Path(req.filename).name[:255],
        content_type=req.content_type,
        size_bytes=req.size_bytes,
        storage_key=key,
        status=SourceVideoStatus.PENDING_UPLOAD,
        upload_id=upload_id,
        upload_part_size=part_size,
        upload_part_count=part_count,
        rights_confirmed_at=datetime.now(UTC),
        rights_statement=req.rights_statement or RIGHTS_STATEMENT,
    )
    db.add(source)
    project.status = ProjectStatus.UPLOADING
    db.flush()
    return s.UploadInitResponse(
        upload_id=upload_id,
        source_video_id=source.id,
        part_size=part_size,
        part_count=part_count,
        parts=_part_urls(runtime, source),
        expires_in_sec=runtime.settings.signed_url_ttl_sec,
    )


def _source_for_upload(db: Session, project: m.Project, upload_id: str) -> m.SourceVideo:
    source = db.scalar(
        select(m.SourceVideo).where(
            m.SourceVideo.project_id == project.id, m.SourceVideo.upload_id == upload_id
        )
    )
    if source is None:
        raise AppError(ErrorCode.NOT_FOUND, UPLOAD_GONE)
    return source


def upload_status(
    db: Session, runtime: Runtime, project: m.Project, upload_id: str
) -> s.UploadStatusResponse:
    source = _source_for_upload(db, project, upload_id)
    parts = runtime.storage.list_parts(source.storage_key, upload_id)
    return s.UploadStatusResponse(
        upload_id=upload_id,
        source_video_id=source.id,
        part_count=source.upload_part_count or 0,
        part_size=source.upload_part_size or 0,
        uploaded_parts=[
            s.UploadedPart(part_number=p.part_number, etag=p.etag, size=p.size) for p in parts
        ],
        parts=_part_urls(runtime, source)
        if source.status == SourceVideoStatus.PENDING_UPLOAD
        else [],
    )


def complete_upload(
    db: Session,
    runtime: Runtime,
    user: m.User,
    project: m.Project,
    upload_id: str,
    req: s.UploadCompleteRequest,
) -> tuple[m.SourceVideo, m.Job | None, bool]:
    source = _source_for_upload(db, project, upload_id)
    if source.status != SourceVideoStatus.PENDING_UPLOAD:
        # Idempotent: completing twice returns the existing state/job.
        job = _job_for_source(
            db, project, source, JobKind.ANALYSIS if req.analyze else JobKind.INGEST
        )
        return source, job, False
    expected = source.upload_part_count or 0
    numbers = sorted({p.part_number for p in req.parts})
    if numbers != list(range(1, expected + 1)):
        raise AppError(
            ErrorCode.UPLOAD_INCOMPLETE,
            details={"expectedParts": expected, "receivedParts": numbers},
        )
    try:
        runtime.storage.complete_multipart(
            source.storage_key, upload_id, [(p.part_number, p.etag) for p in req.parts]
        )
    except ValueError as exc:
        raise AppError(ErrorCode.UPLOAD_INCOMPLETE, details={"reason": str(exc)}) from exc
    actual = runtime.storage.size(source.storage_key)
    if actual != source.size_bytes:
        runtime.storage.delete(source.storage_key)
        source.status = SourceVideoStatus.REJECTED
        source.error_code = ErrorCode.UPLOAD_INCOMPLETE.value
        db.flush()
        raise AppError(
            ErrorCode.UPLOAD_INCOMPLETE,
            details={"declared": source.size_bytes, "received": actual},
        )
    source.status = SourceVideoStatus.UPLOADED
    project.status = ProjectStatus.UPLOADED
    db.flush()
    job, created = _start_processing(db, user, project, source, analyze=req.analyze)
    return source, job, created


def simple_upload(
    db: Session,
    runtime: Runtime,
    user: m.User,
    project: m.Project,
    *,
    filename: str,
    content_type: str,
    stream: BinaryIO,
    rights_confirmed: bool,
    analyze: bool,
) -> tuple[m.SourceVideo, m.Job | None, bool]:
    """Single-request multipart/form-data upload, streamed to a temp file and
    then to storage (handy for curl, tests and small files)."""
    max_bytes = runtime.settings.upload_max_bytes
    with tempfile.NamedTemporaryFile(
        prefix="upload-", suffix=Path(filename).suffix, delete=False
    ) as tmp:
        size = 0
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                tmp.close()
                Path(tmp.name).unlink(missing_ok=True)
                raise AppError(
                    ErrorCode.FILE_TOO_LARGE,
                    f"O arquivo passa do limite de {file_size(max_bytes)}. "
                    "Corte ou comprima o vídeo e envie de novo.",
                    details={"maxBytes": max_bytes},
                )
            tmp.write(chunk)
        tmp_path = Path(tmp.name)
    try:
        _validate_declared(runtime, content_type, size, rights_confirmed)
        return register_file(
            db,
            runtime,
            user,
            project,
            path=tmp_path,
            filename=filename,
            content_type=content_type,
            rights_statement=RIGHTS_STATEMENT,
            analyze=analyze,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


def register_file(
    db: Session,
    runtime: Runtime,
    user: m.User,
    project: m.Project,
    *,
    path: Path,
    filename: str,
    content_type: str,
    rights_statement: str,
    analyze: bool,
) -> tuple[m.SourceVideo, m.Job, bool]:
    """Store a local file as the project's source video and queue its processing."""
    source_id = uuid.uuid4()
    key = source_key(project.id, source_id, filename)
    runtime.storage.put_file(key, path, content_type)
    source = m.SourceVideo(
        id=source_id,
        project_id=project.id,
        original_filename=Path(filename).name[:255],
        content_type=content_type,
        size_bytes=path.stat().st_size,
        storage_key=key,
        status=SourceVideoStatus.UPLOADED,
        rights_confirmed_at=datetime.now(UTC),
        rights_statement=rights_statement,
    )
    db.add(source)
    project.status = ProjectStatus.UPLOADED
    db.flush()
    job, created = _start_processing(db, user, project, source, analyze=analyze)
    return source, job, created


def abort_upload(db: Session, runtime: Runtime, project: m.Project, upload_id: str) -> None:
    source = _source_for_upload(db, project, upload_id)
    if source.status != SourceVideoStatus.PENDING_UPLOAD:
        raise AppError(
            ErrorCode.CONFLICT,
            "Este vídeo já terminou de ser enviado, então não dá mais para cancelar o envio.",
        )
    runtime.storage.abort_multipart(source.storage_key, upload_id)
    db.delete(source)
    db.flush()


def _start_processing(
    db: Session, user: m.User, project: m.Project, source: m.SourceVideo, *, analyze: bool
) -> tuple[m.Job, bool]:
    kind = JobKind.ANALYSIS if analyze else JobKind.INGEST
    return create_job(
        db,
        project_id=project.id,
        kind=kind,
        idempotency_key=f"{kind.value.lower()}:{source.id}",
        payload={"sourceVideoId": str(source.id)},
        user_id=user.id,
        message="Na fila para análise" if analyze else "Na fila para conferir o vídeo",
    )


def _job_for_source(
    db: Session, project: m.Project, source: m.SourceVideo, kind: JobKind
) -> m.Job | None:
    return db.scalar(
        select(m.Job).where(
            m.Job.project_id == project.id,
            m.Job.kind == kind,
            m.Job.idempotency_key == f"{kind.value.lower()}:{source.id}",
        )
    )
