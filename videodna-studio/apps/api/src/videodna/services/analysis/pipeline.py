"""Layered analysis pipeline (spec §4–§8).

    A  technical      ffprobe                                   (local, free)
       ingest         hash, 720p proxy, poster                  (local, free)
    B  shots          scene score + blackdetect                 (local, free)
    C  keyframes      start/mid/end + interval, colors          (local, free)
       narrative      VideoAnalyzerProvider (multimodal)        (AI)
       detection/OCR  ImageAnalyzerProvider on keyframes only   (AI)
       tracking       TrackingProvider per shot                 (AI)
       audio          SpeechProvider                            (AI)
       assembly       consensus, confidence, persistent ids     (local)

Everything local runs first and is reused by every AI stage, so providers
only ever see what they need (a proxy, a few keyframes) — never every frame.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select

from videodna.db import models as m
from videodna.domain.enums import (
    AnalysisStatus,
    JobStatus,
    ProjectStatus,
    SourceVideoStatus,
)
from videodna.domain.video_dna import (
    Keyframe,
    LightingInfo,
    ProviderRun,
    Shot,
    TechnicalMetadata,
    VideoDNA,
)
from videodna.errors import AppError, ErrorCode
from videodna.jobs.runner import JobContext
from videodna.logging_setup import get_logger
from videodna.media import colors, transcode
from videodna.media.hashing import sha256_file
from videodna.media.keyframes import extract_frame, select_keyframes
from videodna.media.probe import probe, validate_technical
from videodna.media.shots import detect_shots
from videodna.orchestrator.capabilities import Capability
from videodna.orchestrator.interfaces import (
    ImageAnalysisRequest,
    ImageAnalysisResult,
    KeyframeInput,
    SpeechRequest,
    SpeechResult,
    TrackingRequest,
    TrackResult,
    TrackSeed,
    VideoAnalysisRequest,
)
from videodna.orchestrator.router import RoutingTask
from videodna.services.analysis.assembler import AssemblyInput, assemble_dna
from videodna.services.analysis.persistence import dna_from_json, persist_dna
from videodna.storage.base import analysis_key, source_asset_key

log = get_logger(__name__)


# --- ingest --------------------------------------------------------------------


def _load_source(ctx: JobContext) -> m.SourceVideo:
    with ctx.session() as session:
        source_id = ctx.payload.get("sourceVideoId")
        query = select(m.SourceVideo).where(m.SourceVideo.project_id == ctx.project_id)
        if source_id:
            query = query.where(m.SourceVideo.id == uuid.UUID(source_id))
        source = session.scalars(query.order_by(m.SourceVideo.created_at.desc())).first()
        if source is None:
            raise AppError(ErrorCode.UPLOAD_INCOMPLETE, "Nenhum vídeo enviado para este projeto.")
        session.expunge(source)
        return source


def ensure_ingested(
    ctx: JobContext, *, progress_from: float, progress_to: float
) -> tuple[m.SourceVideo, Path, TechnicalMetadata]:
    """Download, validate, hash and proxy the source. Idempotent: a READY source
    only needs its proxy downloaded."""
    storage = ctx.runtime.storage
    settings = ctx.runtime.settings
    source = _load_source(ctx)
    if source.status not in {
        SourceVideoStatus.UPLOADED,
        SourceVideoStatus.INGESTING,
        SourceVideoStatus.READY,
    }:
        raise AppError(ErrorCode.UPLOAD_INCOMPLETE)
    span = progress_to - progress_from

    if source.status == SourceVideoStatus.READY and source.proxy_key and source.technical:
        ctx.reporter.progress("ingest", progress_to, "Vídeo já processado — reutilizando proxy")
        proxy = storage.download(source.proxy_key, ctx.workdir / "proxy.mp4")
        return source, proxy, TechnicalMetadata.model_validate(source.technical)

    ctx.reporter.progress(
        "ingest", progress_from, "Baixando vídeo para processamento", status=JobStatus.PREPARING
    )
    with ctx.session() as session:
        row = session.get(m.SourceVideo, source.id)
        row.status = SourceVideoStatus.INGESTING
        session.commit()

    local = storage.download(
        source.storage_key, ctx.workdir / f"original{Path(source.storage_key).suffix}"
    )
    try:
        ctx.reporter.progress(
            "probe", progress_from + span * 0.15, "Lendo metadados técnicos (FFprobe)"
        )
        technical = probe(local)
        validate_technical(technical, settings)
    except AppError as exc:
        with ctx.session() as session:
            row = session.get(m.SourceVideo, source.id)
            if exc.code == ErrorCode.MEDIA_PROCESSING_FAILED:
                # Our tooling failed (e.g. FFmpeg missing), not the file: keep it retryable.
                row.status = SourceVideoStatus.UPLOADED
            else:
                row.status = SourceVideoStatus.REJECTED
            row.error_code = exc.code.value
            session.commit()
        raise

    ctx.reporter.progress("hash", progress_from + span * 0.3, "Calculando hash do arquivo")
    content_hash = sha256_file(local)
    technical = technical.model_copy(update={"size_bytes": local.stat().st_size})

    ctx.reporter.progress(
        "proxy",
        progress_from + span * 0.45,
        f"Gerando proxy {settings.proxy_height}p para o editor",
    )
    proxy = transcode.make_proxy(local, ctx.workdir / "proxy.mp4", height=settings.proxy_height)
    poster = transcode.make_poster(
        local, ctx.workdir / "poster.jpg", time=min(technical.duration_sec * 0.1, 2.0)
    )
    proxy_key = source_asset_key(ctx.project_id, source.id, "proxy.mp4")
    poster_key = source_asset_key(ctx.project_id, source.id, "poster.jpg")
    storage.put_file(proxy_key, proxy, "video/mp4")
    storage.put_file(poster_key, poster, "image/jpeg")

    with ctx.session() as session:
        row = session.get(m.SourceVideo, source.id)
        row.status = SourceVideoStatus.READY
        row.technical = technical.model_dump(mode="json", by_alias=True)
        row.content_hash = content_hash
        row.proxy_key = proxy_key
        row.poster_key = poster_key
        row.duration_sec = technical.duration_sec
        row.width = technical.width
        row.height = technical.height
        row.fps = technical.fps
        if settings.media_retention_days:
            row.retention_until = datetime.now(UTC) + timedelta(days=settings.media_retention_days)
        project = session.get(m.Project, ctx.project_id)
        if project.status in {ProjectStatus.DRAFT, ProjectStatus.UPLOADING}:
            project.status = ProjectStatus.UPLOADED
        session.commit()
        session.refresh(row)
        session.expunge(row)
        source = row
    ctx.reporter.progress("ingest", progress_to, "Vídeo validado")
    # The proxy is what every later stage reads; the original is only needed for
    # the final render, so drop it from the workdir right away.
    local.unlink(missing_ok=True)
    return source, proxy, technical


def run_ingest_job(ctx: JobContext) -> dict[str, Any]:
    source, _, technical = ensure_ingested(ctx, progress_from=0, progress_to=100)
    return {
        "sourceVideoId": str(source.id),
        "durationSec": technical.duration_sec,
        "_message": "Vídeo validado e pronto para análise",
    }


# --- analysis --------------------------------------------------------------------


def _local_shots(
    ctx: JobContext, proxy: Path, technical: TechnicalMetadata, analysis_id: uuid.UUID
) -> list[Shot]:
    settings = ctx.runtime.settings
    storage = ctx.runtime.storage
    ctx.reporter.progress("shots", 18, "Detectando cortes e shots", status=JobStatus.ANALYZING)
    boundaries = detect_shots(
        proxy,
        technical.duration_sec,
        technical.fps,
        threshold=settings.shot_detection_threshold,
        min_duration=settings.shot_min_duration_sec,
    )
    picks = select_keyframes(
        boundaries,
        technical.fps,
        interval_sec=settings.analysis_keyframe_interval_sec,
        max_total=settings.analysis_max_keyframes,
    )
    ctx.reporter.progress(
        "keyframes", 24, f"{len(boundaries)} shots detectados — extraindo {len(picks)} keyframes"
    )
    keyframes_by_shot: dict[int, list[Keyframe]] = {}
    measurements: dict[int, list[tuple[list[str], float]]] = {}
    for i, pick in enumerate(picks, start=1):
        kf_id = f"KF_{i:04d}"
        local = extract_frame(proxy, pick.time, ctx.workdir / "keyframes" / f"{kf_id}.jpg")
        key = analysis_key(ctx.project_id, analysis_id, f"keyframes/{kf_id}.jpg")
        storage.put_file(key, local, "image/jpeg")
        keyframes_by_shot.setdefault(pick.shot_index, []).append(
            Keyframe(
                id=kf_id,
                time=pick.time,
                frame=pick.frame,
                reason=pick.reason,
                asset_key=key,
                width=640,
            )
        )
        measurements.setdefault(pick.shot_index, []).append(colors.measure(local))
        if i % 10 == 0:
            ctx.reporter.progress(
                "keyframes", 24 + 6 * i / len(picks), f"Keyframes {i}/{len(picks)}"
            )

    shots: list[Shot] = []
    for b in boundaries:
        kfs = keyframes_by_shot.get(b.index, [])
        meas = measurements.get(b.index, [])
        mid = next((k for k in kfs if k.reason == "shot_mid"), kfs[0] if kfs else None)
        brightness = round(sum(x[1] for x in meas) / len(meas), 3) if meas else None
        shots.append(
            Shot(
                id=f"SHOT_{b.index + 1:03d}",
                index=b.index,
                start_time=b.start_time,
                end_time=b.end_time,
                duration=b.duration,
                start_frame=b.start_frame,
                end_frame=b.end_frame,
                transition_in=b.transition_in,
                keyframes=kfs,
                thumbnail_key=mid.asset_key if mid else None,
                dominant_colors=colors.merge_palettes([x[0] for x in meas], top=4),
                lighting=LightingInfo(brightness=brightness),
                confidence=0.95,
            )
        )
    return shots


def _keyframe_inputs(ctx: JobContext, shots: list[Shot]) -> list[KeyframeInput]:
    return [
        KeyframeInput(
            id=k.id, shot_id=s.id, time=k.time, path=ctx.workdir / "keyframes" / f"{k.id}.jpg"
        )
        for s in shots
        for k in s.keyframes
    ]


def _try_reuse(ctx: JobContext, source: m.SourceVideo, shots: list[Shot]) -> m.VideoAnalysis | None:
    """Same content + same pipeline + same mode + same shot cut = the AI layers
    can be reused for free (spec §83/§84)."""
    if not source.content_hash:
        return None
    settings = ctx.runtime.settings
    with ctx.session() as session:
        owner_id = session.scalar(select(m.Project.owner_id).where(m.Project.id == ctx.project_id))
        rows = session.scalars(
            select(m.VideoAnalysis)
            .join(m.SourceVideo, m.SourceVideo.id == m.VideoAnalysis.source_video_id)
            .join(m.Project, m.Project.id == m.VideoAnalysis.project_id)
            .where(
                m.SourceVideo.content_hash == source.content_hash,
                m.Project.owner_id == owner_id,
                m.VideoAnalysis.status == AnalysisStatus.COMPLETED,
                m.VideoAnalysis.pipeline_version == settings.analysis_pipeline_version,
                m.VideoAnalysis.mock.is_(settings.ai_mock_mode),
            )
            .order_by(m.VideoAnalysis.completed_at.desc())
        ).all()
        for row in rows:
            if not row.dna:
                continue
            old = dna_from_json(row.dna)
            same_cut = len(old.shots) == len(shots) and all(
                abs(a.start_time - b.start_time) < 0.05 and abs(a.end_time - b.end_time) < 0.05
                for a, b in zip(old.shots, shots, strict=True)
            )
            if same_cut:
                session.expunge(row)
                return row
    return None


def _reuse_dna(
    old: VideoDNA, shots: list[Shot], source: m.SourceVideo, reused_from: uuid.UUID
) -> VideoDNA:
    new_shots = []
    for old_shot, shot in zip(old.shots, shots, strict=True):
        new_shots.append(
            shot.model_copy(
                update={
                    "scene_id": old_shot.scene_id,
                    "camera": old_shot.camera,
                    "lighting": old_shot.lighting.model_copy(
                        update={"brightness": shot.lighting.brightness}
                    ),
                }
            )
        )
    provenance = old.analysis.model_copy(
        update={
            "reused_from_analysis_id": str(reused_from),
            "created_at": datetime.now(UTC).isoformat(),
            "providers": [],
        }
    )
    return old.model_copy(
        update={
            "source_video_id": str(source.id),
            "shots": new_shots,
            "analysis": provenance,
        },
        deep=True,
    )


def run_analysis_job(ctx: JobContext) -> dict[str, Any]:
    settings = ctx.runtime.settings
    with ctx.session() as session:
        project = session.get(m.Project, ctx.project_id)
        project.status = ProjectStatus.ANALYZING
        session.commit()

    try:
        source, proxy, technical = ensure_ingested(ctx, progress_from=0, progress_to=15)
        with ctx.session() as session:
            analysis = m.VideoAnalysis(
                project_id=ctx.project_id,
                source_video_id=source.id,
                status=AnalysisStatus.RUNNING,
                pipeline_version=settings.analysis_pipeline_version,
                mock=settings.ai_mock_mode,
            )
            session.add(analysis)
            session.commit()
            analysis_id = analysis.id

        shots = _local_shots(ctx, proxy, technical, analysis_id)
        reusable = None if ctx.payload.get("force") else _try_reuse(ctx, source, shots)

        if reusable is not None:
            ctx.reporter.progress(
                "reuse", 80, "Conteúdo idêntico já analisado — reutilizando análise (custo zero)"
            )
            dna = _reuse_dna(dna_from_json(reusable.dna), shots, source, reusable.id)
        else:
            dna = _run_ai_stages(ctx, source, proxy, technical, shots)

        ctx.reporter.progress("persist", 96, "Salvando Video DNA")
        with ctx.session() as session:
            analysis = session.get(m.VideoAnalysis, analysis_id)
            if reusable is not None:
                analysis.reused_from_id = reusable.id
            persist_dna(session, analysis, dna)
            project = session.get(m.Project, ctx.project_id)
            project.current_analysis_id = analysis_id
            project.status = ProjectStatus.READY
            session.commit()
            summary = dict(analysis.summary)
    except Exception:
        with ctx.session() as session:
            project = session.get(m.Project, ctx.project_id)
            if project is not None:
                project.status = (
                    ProjectStatus.READY if project.current_analysis_id else ProjectStatus.FAILED
                )
            pending = session.scalars(
                select(m.VideoAnalysis).where(
                    m.VideoAnalysis.project_id == ctx.project_id,
                    m.VideoAnalysis.status == AnalysisStatus.RUNNING,
                )
            ).all()
            for row in pending:
                row.status = AnalysisStatus.FAILED
            session.commit()
        raise

    return {
        "analysisId": str(analysis_id),
        "reused": reusable is not None,
        "summary": summary,
        "_message": "Análise concluída",
    }


def _run_ai_stages(
    ctx: JobContext,
    source: m.SourceVideo,
    proxy: Path,
    technical: TechnicalMetadata,
    shots: list[Shot],
) -> VideoDNA:
    settings = ctx.runtime.settings
    orchestrator = ctx.runtime.orchestrator
    keyframes = _keyframe_inputs(ctx, shots)
    runs: list[ProviderRun] = []
    usage = ctx.usage()

    # Narrative / multimodal understanding
    ctx.reporter.progress("narrative", 32, "Entendendo a história, personagens e ações")
    task = RoutingTask(
        capability=Capability.VIDEO_UNDERSTANDING, duration_sec=technical.duration_sec
    )
    narrative = orchestrator.run(
        task,
        lambda adapter, decision: adapter.analyze_video(
            VideoAnalysisRequest(
                video_path=proxy, technical=technical, shots=shots, keyframes=keyframes
            )
        ),
        operation="analysis.narrative",
        context=usage,
    )
    runs.append(_run("narrative", narrative))

    # Detection + OCR on keyframes only
    ctx.reporter.progress(
        "detection", 50, f"Detectando objetos e textos em {len(keyframes)} keyframes"
    )
    detections: ImageAnalysisResult | None = None
    detector_name: str | None = None
    try:
        det = orchestrator.run(
            RoutingTask(capability=Capability.OBJECT_DETECTION, quantity=len(keyframes)),
            lambda adapter, decision: adapter.analyze_images(
                ImageAnalysisRequest(
                    keyframes=keyframes,
                    prompts=[e.label for e in narrative.result.entities],
                    duration_sec=technical.duration_sec,
                    shots=shots,
                )
            ),
            operation="analysis.detection",
            context=usage,
        )
        detections, detector_name = det.result, det.decision.provider
        runs.append(_run("detection", det))
    except AppError as exc:
        ctx.reporter.log(
            f"Detecção indisponível ({exc.code.value}); seguindo só com a análise multimodal",
            level="warning",
        )

    # Tracking per shot, seeded by detections (fallback: the analyzer's boxes)
    ctx.reporter.progress("tracking", 62, "Rastreando personagens e objetos entre frames")
    tracks: list[TrackResult] = []
    tracker_name: str | None = None
    for i, shot in enumerate(shots):
        seeds = _seeds_for_shot(shot, narrative.result, detections)
        if not seeds:
            continue
        try:
            tr = orchestrator.run(
                RoutingTask(
                    capability=Capability.TRACKING_MULTI_OBJECT, duration_sec=shot.duration
                ),
                lambda adapter, decision, shot=shot, seeds=seeds: adapter.track(
                    TrackingRequest(video_path=proxy, shot=shot, fps=technical.fps, seeds=seeds)
                ),
                operation="analysis.tracking",
                context=ctx.usage(shot.id),
            )
        except AppError as exc:
            ctx.reporter.log(f"Tracking falhou no {shot.id} ({exc.code.value})", level="warning")
            continue
        tracks.extend(tr.result.tracks)
        tracker_name = tr.decision.provider
        if i == 0:
            runs.append(_run("tracking", tr))
        ctx.reporter.progress(
            "tracking", 62 + 12 * (i + 1) / len(shots), f"Rastreando shot {i + 1}/{len(shots)}"
        )

    # Audio
    speech: SpeechResult | None = None
    if technical.has_audio:
        ctx.reporter.progress("audio", 76, "Analisando fala, música e efeitos sonoros")
        audio_path = transcode.extract_audio(proxy, ctx.workdir / "audio.wav")
        if audio_path is not None:
            try:
                sp = orchestrator.run(
                    RoutingTask(
                        capability=Capability.SPEECH_TRANSCRIPTION,
                        duration_sec=technical.duration_sec,
                    ),
                    lambda adapter, decision: adapter.transcribe(
                        SpeechRequest(media_path=audio_path, duration_sec=technical.duration_sec)
                    ),
                    operation="analysis.speech",
                    context=usage,
                )
                speech = sp.result
                runs.append(_run("speech", sp))
            except AppError as exc:
                ctx.reporter.log(
                    f"Análise de áudio indisponível ({exc.code.value})", level="warning"
                )

    ctx.reporter.progress(
        "assembly", 88, "Montando o Video DNA e verificando consenso entre modelos"
    )
    return assemble_dna(
        AssemblyInput(
            source_video_id=str(source.id),
            content_hash=source.content_hash,
            technical=technical,
            shots=shots,
            analysis=narrative.result,
            analyzer_provider=narrative.decision.provider,
            detections=detections,
            detector_provider=detector_name,
            tracks=tracks,
            tracker_provider=tracker_name,
            speech=speech,
            provider_runs=runs,
            pipeline_version=settings.analysis_pipeline_version,
            mock=settings.ai_mock_mode,
            low_confidence_threshold=settings.analysis_low_confidence_threshold,
        )
    )


def _run(stage: str, outcome) -> ProviderRun:
    return ProviderRun(
        stage=stage,
        provider=outcome.decision.provider,
        model=outcome.decision.model,
        cost=float(outcome.actual_cost),
        confidence=getattr(outcome.result, "confidence", None),
    )


def _seeds_for_shot(
    shot: Shot, analysis, detections: ImageAnalysisResult | None
) -> list[TrackSeed]:
    seeds: list[TrackSeed] = []
    seen: set[str] = set()
    if detections:
        for det in detections.detections:
            if det.shot_id == shot.id and det.entity_hint:
                seeds.append(
                    TrackSeed(
                        entity_key=det.entity_hint,
                        time=det.time,
                        bbox=det.bbox,
                        confidence=det.confidence,
                    )
                )
                seen.add(det.entity_hint)
    mid = (shot.start_time + shot.end_time) / 2
    for cand in analysis.entities:
        box = cand.bbox_by_shot.get(shot.id)
        if box is not None and cand.key not in seen and cand.bbox_by_shot:
            if box.w >= 0.99 and box.h >= 0.99:
                continue  # whole-frame boxes (environment) are not trackable objects
            seeds.append(
                TrackSeed(entity_key=cand.key, time=mid, bbox=box, confidence=cand.confidence)
            )
    return seeds
