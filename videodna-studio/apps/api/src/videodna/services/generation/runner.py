"""Generation job: plan -> per-shot generation -> QA -> localized repair -> assembly.

* Shot by shot (spec §27): failures, retries, QA and cost stay local to a shot.
* PASSTHROUGH shots are cut from the source untouched — no provider call.
* QA runs twice per attempt: deterministic technical checks + AI inspector.
* Localized repair (spec §33): only the problematic time window is
  regenerated (when the provider supports partial ranges) and spliced back.
* Retries are capped per quality mode (spec §34); a budget guard stops paid
  repairs once actual spend exceeds the approved estimate + tolerance.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from videodna.db import models as m
from videodna.domain.enums import (
    SEVERITY_RANK,
    CostKind,
    JobStatus,
    OutputKind,
    PlanStatus,
    ProjectStatus,
    QAIssueStatus,
    QASeverity,
    RenderKind,
)
from videodna.domain.video_dna import Shot, TrackSample, VideoDNA
from videodna.errors import AppError, ErrorCode
from videodna.jobs.runner import JobContext
from videodna.logging_setup import get_logger
from videodna.media import transcode
from videodna.orchestrator.capabilities import FEATURE_PARTIAL_RANGE, Capability, ProviderKind
from videodna.orchestrator.interfaces import (
    EditSpec,
    ImageGenerationRequest,
    QAIssueCandidate,
    QARequest,
    QAResult,
    ReferencePack,
    SegmentationRequest,
    SegmentationTarget,
    VideoEditRequest,
    VideoGenerationRequest,
)
from videodna.orchestrator.router import RoutingDecision, RoutingTask
from videodna.services.analysis.persistence import dna_from_json
from videodna.services.generation.plan_models import GenerationPlanSpec, GenerationStep, ShotPlan
from videodna.services.generation.planner import current_fingerprint, planned_dna
from videodna.storage.base import job_key

log = get_logger(__name__)

_MIN_WINDOW = 0.6  # seconds — shorter repairs are not worth a provider call
_WHOLE_SHOT_RATIO = 0.7


@dataclass
class ShotState:
    plan: ShotPlan
    shot: Shot
    segment: Path | None = None
    attempts: int = 0
    providers: list[str] = field(default_factory=list)
    open_issues: list[QAIssueCandidate] = field(default_factory=list)
    unresolved: bool = False


@dataclass
class Run:
    """State of one generation job, passed to every step."""

    ctx: JobContext
    plan: GenerationPlanSpec
    dna: VideoDNA
    fps: float
    budget: Decimal
    spent: Decimal = Decimal(0)


def _load(ctx: JobContext) -> tuple[m.GenerationPlan, GenerationPlanSpec, VideoDNA, m.SourceVideo]:
    with ctx.session() as session:
        plan_row = session.get(m.GenerationPlan, ctx.plan_id)
        if plan_row is None:
            raise AppError(ErrorCode.NOT_FOUND, "Plano não encontrado.")
        analysis = session.get(m.VideoAnalysis, plan_row.analysis_id)
        source = session.get(m.SourceVideo, analysis.source_video_id)
        plan = GenerationPlanSpec.model_validate(plan_row.plan)
        original = dna_from_json(analysis.dna)
        session.expunge_all()
    return plan_row, plan, planned_dna(original, plan), source


def _edit_specs(
    dna: VideoDNA, plan: GenerationPlanSpec, shot: Shot, op_ids: list[str]
) -> list[EditSpec]:
    ops = {o.id: o for o in plan.operations}
    specs: list[EditSpec] = []
    for op_id in op_ids:
        op = ops.get(op_id)
        if op is None:
            continue
        keys = [op.entity_id] if op.entity_id else []
        if op.entity_id:
            keys += [e.id for e in dna.entities if e.derived_from == op.entity_id]
            keys += [
                e.id
                for e in dna.entities
                if e.edit and e.edit.added and op.id in e.edit.operation_ids
            ]
        if not keys:
            specs.append(
                EditSpec(
                    entity_key=None,
                    op=op.op,
                    label=op.instruction or "instrução",
                    instruction=op.instruction,
                )
            )
            continue
        for key in dict.fromkeys(keys):
            entity = dna.entity(key)
            if entity is None:
                continue
            track: list[TrackSample] = [s for t in dna.tracks_for(key, shot.id) for s in t.samples]
            if not track and entity.edit and entity.edit.added and entity.parent_id:
                track = [s for t in dna.tracks_for(entity.parent_id, shot.id) for s in t.samples]
            palette = entity.attributes.get("palette")
            specs.append(
                EditSpec(
                    entity_key=key,
                    entity_type=entity.type,
                    op=op.op,
                    property=op.property,
                    label=entity.label,
                    new_value=op.new_value,
                    color_hex=entity.attributes.get("colorHex")
                    or (palette[-1] if palette else None),
                    instruction=op.instruction,
                    track=track,
                )
            )
    return specs


def _build_reference_packs(
    ctx: JobContext, plan: GenerationPlanSpec, dna: VideoDNA
) -> dict[str, ReferencePack]:
    packs: dict[str, ReferencePack] = {}
    for pack in plan.reference_packs:
        entity = dna.entity(pack.entity_key)
        if entity is None:
            continue
        paths: list[Path] = []
        for i in range(pack.images):
            try:
                out = ctx.runtime.orchestrator.run(
                    RoutingTask(capability=Capability.IMAGE_GENERATE, quantity=1),
                    lambda adapter, d, i=i, pack=pack, entity=entity: adapter.generate_image(
                        ImageGenerationRequest(
                            prompt=pack.description,
                            purpose="reference",
                            hint={
                                "kind": "character" if pack.kind == "character" else "room",
                                "label": f"{entity.label} · ref {i + 1}",
                                "colors": entity.attributes.get("palette", []),
                            },
                            output_path=ctx.workdir / "refs" / f"{pack.id}_{i}",
                        )
                    ),
                    operation="generation.reference_pack",
                    context=ctx.usage(),
                )
            except AppError as exc:
                ctx.reporter.log(
                    f"Reference pack {pack.label}: imagem {i + 1} falhou ({exc.code.value})",
                    level="warning",
                )
                continue
            result = out.result
            key = job_key(ctx.project_id, ctx.job_id, f"refs/{pack.id}_{i}{result.path.suffix}")
            ctx.runtime.storage.put_file(key, result.path, result.content_type)
            _save_output(
                ctx,
                OutputKind.REFERENCE_IMAGE,
                key,
                result.content_type,
                result.path,
                provider=out.decision.provider,
                model=out.decision.model,
                provenance={"pack": pack.id, "entity": pack.entity_key},
            )
            paths.append(result.path)
        packs[pack.id] = ReferencePack(
            kind=pack.kind,
            entity_key=pack.entity_key,
            description=pack.description,
            attributes=entity.attributes,
            image_paths=paths,
        )
    return packs


def _segment(run: Run, shot_plan: ShotPlan, specs: list[EditSpec]) -> None:
    ctx, dna = run.ctx, run.dna
    pre = next((p for p in shot_plan.pre_steps if p.kind == "SEGMENTATION"), None)
    shot = dna.shot(shot_plan.shot_key)
    if pre is None or shot is None or not shot.keyframes:
        return
    keyframe = next((k for k in shot.keyframes if k.reason == "shot_mid"), shot.keyframes[0])
    local = ctx.runtime.storage.download(
        keyframe.asset_key, ctx.workdir / "kf" / f"{keyframe.id}.jpg"
    )
    targets = []
    for spec in specs:
        if spec.entity_key in pre.entity_keys and spec.track:
            sample = min(spec.track, key=lambda s: abs(s.time - keyframe.time))
            targets.append(SegmentationTarget(entity_key=spec.entity_key, bbox=sample.bbox))
    if not targets:
        return
    try:
        out = ctx.runtime.orchestrator.run(
            RoutingTask(capability=Capability.SEGMENTATION_IMAGE, quantity=len(targets)),
            lambda adapter, d: adapter.segment(
                SegmentationRequest(
                    image_path=local,
                    keyframe_id=keyframe.id,
                    targets=targets,
                    output_dir=ctx.workdir / "masks" / shot.id,
                )
            ),
            operation="generation.segmentation",
            context=ctx.usage(shot.id),
        )
    except AppError as exc:
        ctx.reporter.log(
            f"Máscaras indisponíveis no {shot.id} ({exc.code.value}); usando só tracking",
            level="warning",
        )
        return
    run.spent += out.actual_cost
    masks = {mk.entity_key: mk.mask_path for mk in out.result.masks}
    for spec in specs:
        if spec.entity_key in masks:
            spec.mask_paths.append(masks[spec.entity_key])


def _decision_for(
    ctx: JobContext, plan: GenerationPlanSpec, step: GenerationStep, duration: float
) -> tuple[RoutingTask, RoutingDecision]:
    task = RoutingTask(
        capability=Capability(step.capability),
        quality_mode=plan.quality_mode,
        duration_sec=duration,
        output_height=plan.output_height,
        required_features=frozenset(step.required_features),
        edit_count=len(step.edit_operation_ids),
    )
    decision = ctx.runtime.orchestrator.route(task)
    if decision.provider != step.provider:
        ceiling = Decimal(str(step.estimated_cost)) * Decimal(
            str(1 + ctx.runtime.settings.fallback_max_cost_increase)
        )
        if step.estimated_cost and decision.estimated_cost > ceiling:
            raise AppError(
                ErrorCode.NO_PROVIDER_AVAILABLE,
                "O provider planejado não está disponível e a alternativa custaria bem mais.",
                details={"planned": step.provider, "alternative": decision.provider},
            )
        ctx.reporter.log(
            f"Provider {step.provider} indisponível; usando {decision.provider}", level="warning"
        )
    return task, decision


def _generate_step(
    run: Run,
    step: GenerationStep,
    shot: Shot,
    *,
    input_path: Path,
    timeline_offset: float,
    start: float,
    end: float,
    specs: list[EditSpec],
    references: list[ReferencePack],
    attempt: int,
    repair_hint: str | None,
    out: Path,
) -> tuple[Path, str, Decimal]:
    ctx, plan = run.ctx, run.plan
    task, decision = _decision_for(ctx, plan, step, end - start)
    capability = Capability(step.capability)
    kind = ctx.runtime.registry.descriptor(decision.provider).kind
    request_args = dict(
        capability=capability,
        input_path=input_path,
        timeline_offset=timeline_offset,
        start_time=start,
        end_time=end,
        edits=specs,
        references=references,
        constraints=plan.locks,
        quality_mode=plan.quality_mode,
        model=decision.model,
        output_path=out,
        output_height=plan.output_height,
        fps=run.fps,
        attempt=attempt,
        repair_hint=repair_hint,
    )

    def call(adapter, d):
        if kind == ProviderKind.VIDEO_GENERATOR:
            return adapter.generate_video(
                VideoGenerationRequest(**request_args, prompt=step.strategy.value)
            )
        return adapter.edit_video(VideoEditRequest(**request_args))

    outcome = ctx.runtime.orchestrator.run(
        task,
        call,
        operation="generation.repair" if repair_hint else "generation.shot",
        context=ctx.usage(shot.id),
        decision=decision,
    )
    return outcome.result.path, outcome.decision.provider, outcome.actual_cost


def _run_qa(run: Run, state: ShotState, original_path: Path) -> list[QAIssueCandidate]:
    ctx, plan, dna = run.ctx, run.plan, run.dna
    shot = state.shot
    specs = [
        s
        for step in state.plan.steps
        for s in _edit_specs(dna, plan, shot, step.edit_operation_ids)
    ]
    expected = [e for e in dna.entities if shot.id in {a.shot_id for a in e.appearances}]
    request = QARequest(
        output_path=state.segment,
        original_path=original_path,
        shot=shot,
        timeline_offset=0.0,
        expected_entities=expected,
        edits=specs,
        dependencies=sorted({d.type.value for d in state.plan.dependencies}),
        constraints=plan.locks,
        expected_height=plan.output_height,
        attempt=state.attempts,
    )
    issues: list[QAIssueCandidate] = []
    capabilities = [Capability.QA_TECHNICAL]
    if state.plan.qa_provider:
        capabilities.append(Capability.QA_VIDEO_INSPECTION)
    for capability in capabilities:
        try:
            outcome = ctx.runtime.orchestrator.run(
                RoutingTask(capability=capability, duration_sec=shot.duration),
                lambda adapter, d: adapter.inspect(request),
                operation="generation.qa",
                context=ctx.usage(shot.id),
            )
        except AppError as exc:
            ctx.reporter.log(
                f"QA {capability.value} indisponível no {shot.id} ({exc.code.value})",
                level="warning",
            )
            continue
        run.spent += outcome.actual_cost
        _save_qa(ctx, shot.id, state.attempts, outcome.decision.provider, outcome.result)
        issues.extend(outcome.result.issues)
    return issues


def _save_qa(ctx: JobContext, shot_key: str, attempt: int, provider: str, result: QAResult) -> None:
    with ctx.session() as session:
        report = m.QAReport(
            project_id=ctx.project_id,
            job_id=ctx.job_id,
            shot_key=shot_key,
            attempt=attempt,
            provider=provider,
            passed=result.passed,
            score=result.score,
            summary=result.summary,
            checks=[c.model_dump(mode="json") for c in result.checks],
        )
        session.add(report)
        session.flush()
        for issue in result.issues:
            session.add(
                m.QAIssue(
                    report_id=report.id,
                    project_id=ctx.project_id,
                    job_id=ctx.job_id,
                    shot_key=shot_key,
                    issue_type=issue.issue_type,
                    severity=issue.severity,
                    start_time=issue.start_time,
                    end_time=issue.end_time,
                    description=issue.description,
                    affected_entity_key=issue.affected_entity_key,
                    status=QAIssueStatus.OPEN,
                    repair_attempts=attempt,
                )
            )
        session.commit()


def _close_issues(ctx: JobContext, shot_key: str, status: QAIssueStatus) -> None:
    with ctx.session() as session:
        for issue in session.scalars(
            select(m.QAIssue).where(
                m.QAIssue.job_id == ctx.job_id,
                m.QAIssue.shot_key == shot_key,
                m.QAIssue.status == QAIssueStatus.OPEN,
            )
        ):
            issue.status = status
        session.commit()


def _save_output(
    ctx: JobContext,
    kind: OutputKind,
    key: str,
    content_type: str,
    path: Path,
    *,
    shot_key: str | None = None,
    attempt: int = 0,
    provider: str | None = None,
    model: str | None = None,
    provenance: dict[str, Any] | None = None,
    duration: float | None = None,
    size: tuple[int, int] | None = None,
) -> uuid.UUID:
    with ctx.session() as session:
        row = m.GenerationOutput(
            project_id=ctx.project_id,
            job_id=ctx.job_id,
            kind=kind,
            shot_key=shot_key,
            storage_key=key,
            content_type=content_type,
            duration_sec=duration,
            width=size[0] if size else None,
            height=size[1] if size else None,
            size_bytes=path.stat().st_size if path.exists() else None,
            attempt=attempt,
            provider=provider,
            model=model,
            provenance=provenance or {},
        )
        session.add(row)
        session.commit()
        return row.id


def _severe(issues: list[QAIssueCandidate], minimum: QASeverity) -> list[QAIssueCandidate]:
    floor = SEVERITY_RANK[minimum]
    return [i for i in issues if SEVERITY_RANK[QASeverity(i.severity)] >= floor]


def run_generation_job(ctx: JobContext) -> dict[str, Any]:
    settings = ctx.runtime.settings
    plan_row, plan, dna, source = _load(ctx)

    with ctx.session() as session:
        project = session.get(m.Project, ctx.project_id)
        if (
            current_fingerprint(session, project, plan.quality_mode, plan.render_kind)
            != plan.ops_fingerprint
        ):
            # The DNA we generate is frozen in the plan, but a stale plan means the user
            # changed something after approving the estimate: never spend on it silently.
            raise AppError(ErrorCode.PLAN_STALE)
        project.status = ProjectStatus.GENERATING
        row = session.get(m.GenerationPlan, plan_row.id)
        row.status = PlanStatus.EXECUTING
        session.add(
            m.CostEntry(
                project_id=ctx.project_id,
                user_id=ctx.user_id,
                job_id=ctx.job_id,
                plan_id=plan_row.id,
                kind=CostKind.ESTIMATE,
                provider="plan",
                operation="generation.plan",
                amount=Decimal(str(plan.estimated_cost)),
                currency=plan.currency,
                quantity=plan.summary.affected_shots,
                unit="shot",
                description=(
                    f"Estimativa do plano ({plan.quality_mode.value}, {plan.resolution_label})"
                ),
            )
        )
        session.commit()

    budget = Decimal(str(plan.estimated_cost_with_repairs)) * Decimal(
        str(1 + settings.cost_overrun_tolerance)
    )
    run = Run(ctx=ctx, plan=plan, dna=dna, fps=dna.technical.fps, budget=budget)
    try:
        result = _execute(run, plan_row, source)
    except Exception:
        with ctx.session() as session:
            row = session.get(m.GenerationPlan, plan_row.id)
            row.status = PlanStatus.FAILED
            project = session.get(m.Project, ctx.project_id)
            project.status = ProjectStatus.READY
            session.commit()
        raise
    return result


def _execute(run: Run, plan_row: m.GenerationPlan, source: m.SourceVideo) -> dict[str, Any]:
    ctx, plan, dna = run.ctx, run.plan, run.dna
    settings = ctx.runtime.settings
    storage = ctx.runtime.storage
    reporter = ctx.reporter

    # --- PREPARING: source media, reference packs ------------------------------------
    reporter.progress("prepare", 2, "Preparando mídia de origem", status=JobStatus.PREPARING)
    if plan.render_kind == RenderKind.PREVIEW and source.proxy_key:
        input_path = storage.download(source.proxy_key, ctx.workdir / "input.mp4")
    else:
        input_path = storage.download(
            source.storage_key, ctx.workdir / f"input{Path(source.storage_key).suffix}"
        )

    references: dict[str, ReferencePack] = {}
    if plan.reference_packs:
        reporter.progress(
            "references",
            6,
            f"Criando {len(plan.reference_packs)} reference pack(s) de continuidade",
        )
        references = _build_reference_packs(ctx, plan, dna)

    shots = [ShotState(plan=sp, shot=dna.shot(sp.shot_key)) for sp in plan.shots]
    to_generate = [s for s in shots if s.plan.steps]
    segments_dir = ctx.workdir / "segments"

    # --- GENERATING ------------------------------------------------------------------
    done = 0
    for state in shots:
        shot = state.shot
        if not state.plan.steps:
            state.segment = transcode.cut_segment(
                input_path,
                segments_dir / f"{shot.id}.mp4",
                start=shot.start_time,
                end=shot.end_time,
                height=plan.output_height,
                fps=run.fps,
            )
            continue
        done += 1
        reporter.progress(
            "generate",
            10 + 55 * (done - 1) / max(1, len(to_generate)),
            f"Gerando cena {done}/{len(to_generate)} ({shot.id} · {state.plan.strategy.value})",
            status=JobStatus.GENERATING,
            data={"shotKey": shot.id, "strategy": state.plan.strategy.value},
        )
        current_input, offset = input_path, 0.0
        for n, step in enumerate(state.plan.steps):
            specs = _edit_specs(dna, plan, shot, step.edit_operation_ids)
            _segment(run, state.plan, specs)
            refs = [references[r] for r in state.plan.reference_packs if r in references]
            out_path, provider, cost = _generate_step(
                run,
                step,
                shot,
                input_path=current_input,
                timeline_offset=offset,
                start=shot.start_time,
                end=shot.end_time,
                specs=specs,
                references=refs,
                attempt=0,
                repair_hint=None,
                out=segments_dir / f"{shot.id}_s{n}_a0.mp4",
            )
            run.spent += cost
            state.providers.append(provider)
            current_input, offset = out_path, shot.start_time
        state.segment = current_input

    # --- QA + REPAIRING --------------------------------------------------------------
    unresolved: list[dict[str, Any]] = []
    min_severity = QASeverity(settings.qa_repair_min_severity)
    for i, state in enumerate(to_generate, start=1):
        shot = state.shot
        reporter.progress(
            "qa",
            66 + 20 * (i - 1) / max(1, len(to_generate)),
            f"Verificando qualidade {i}/{len(to_generate)} ({shot.id})",
            status=JobStatus.QA,
        )
        issues = _severe(_run_qa(run, state, input_path), min_severity)
        while issues and state.attempts < plan.max_retries:
            if run.spent >= run.budget:
                reporter.log(
                    "Orçamento de reparo atingido; parando novas tentativas", level="warning"
                )
                break
            state.attempts += 1
            issue = max(issues, key=lambda x: SEVERITY_RANK[QASeverity(x.severity)])
            reporter.progress(
                "repair",
                66 + 20 * (i - 1) / max(1, len(to_generate)),
                f"Corrigindo {shot.id}: {issue.description} "
                f"(tentativa {state.attempts}/{plan.max_retries})",
                status=JobStatus.REPAIRING,
                data={
                    "shotKey": shot.id,
                    "issueType": issue.issue_type,
                    "start": issue.start_time,
                    "end": issue.end_time,
                },
            )
            _repair(run, state, input_path, issue, references, segments_dir)
            issues = _severe(_run_qa(run, state, input_path), min_severity)
            if not issues:
                _close_issues(ctx, shot.id, QAIssueStatus.REPAIRED)
        if issues:
            _close_issues(ctx, shot.id, QAIssueStatus.UNRESOLVED)
            state.unresolved = True
            for issue in issues:
                unresolved.append(
                    {
                        "shotKey": shot.id,
                        "issueType": issue.issue_type,
                        "start": issue.start_time,
                        "end": issue.end_time,
                        "description": issue.description,
                        "message": "Esta parte ainda apresenta inconsistência.",
                    }
                )
        elif state.attempts == 0:
            _close_issues(ctx, shot.id, QAIssueStatus.REPAIRED)

    # --- ASSEMBLING --------------------------------------------------------------------
    reporter.progress("assemble", 88, "Montando a timeline final", status=JobStatus.ASSEMBLING)
    ordered = [s.segment for s in sorted(shots, key=lambda s: s.shot.index)]
    video_only = transcode.concat_segments(ordered, ctx.workdir / "assembled.mp4", fps=run.fps)
    audio_source = input_path if dna.technical.has_audio and plan.locks.audio else None
    final_path = transcode.mux_final(
        video_only, audio_source, ctx.workdir / "final.mp4", duration=dna.technical.duration_sec
    )
    final_duration = transcode.probe_duration(final_path)
    final_size = transcode.probe_video_size(final_path)
    if plan.locks.timing and abs(final_duration - dna.technical.duration_sec) > max(
        0.1, 3 / run.fps
    ):
        reporter.log(
            f"Duração final {final_duration:.2f}s difere da original "
            f"{dna.technical.duration_sec:.2f}s",
            level="warning",
        )

    kind = OutputKind.FINAL if plan.render_kind == RenderKind.FINAL else OutputKind.PREVIEW
    final_key = job_key(ctx.project_id, ctx.job_id, f"{kind.value.lower()}.mp4")
    storage.put_file(final_key, final_path, "video/mp4")
    for state in to_generate:
        seg_key = job_key(ctx.project_id, ctx.job_id, f"shots/{state.shot.id}.mp4")
        storage.put_file(seg_key, state.segment, "video/mp4")
        _save_output(
            ctx,
            OutputKind.SHOT_SEGMENT,
            seg_key,
            "video/mp4",
            state.segment,
            shot_key=state.shot.id,
            attempt=state.attempts,
            provider=",".join(dict.fromkeys(state.providers)) or None,
            duration=state.shot.duration,
        )

    provenance = {
        "sourceVideoId": str(source.id),
        "sourceContentHash": source.content_hash,
        "analysisId": plan.analysis_id,
        "generationJobId": str(ctx.job_id),
        "planId": str(plan_row.id),
        "generatedAt": datetime.now(UTC).isoformat(),
        "renderKind": plan.render_kind.value,
        "qualityMode": plan.quality_mode.value,
        "mock": settings.ai_mock_mode,
        "locks": plan.locks.model_dump(mode="json", by_alias=True),
        "transformations": [
            {
                "operationId": op.id,
                "op": op.op.value,
                "entity": op.entity_id,
                "property": op.property,
            }
            for op in plan.operations
        ],
        "shots": [
            {
                "shotKey": s.shot.id,
                "strategy": s.plan.strategy.value,
                "providers": list(dict.fromkeys(s.providers)),
                "repairAttempts": s.attempts,
                "unresolved": s.unresolved,
            }
            for s in shots
        ],
    }
    output_id = _save_output(
        ctx,
        kind,
        final_key,
        "video/mp4",
        final_path,
        provider=",".join(sorted({p for s in shots for p in s.providers})) or None,
        provenance=provenance,
        duration=final_duration,
        size=final_size,
    )
    prov_path = ctx.workdir / "provenance.json"
    prov_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    prov_key = job_key(ctx.project_id, ctx.job_id, "provenance.json")
    storage.put_file(prov_key, prov_path, "application/json")
    _save_output(
        ctx,
        OutputKind.PROVENANCE,
        prov_key,
        "application/json",
        prov_path,
        provenance={"outputId": str(output_id)},
    )

    with ctx.session() as session:
        number = (
            session.scalar(
                select(func.max(m.ProjectVersion.number)).where(
                    m.ProjectVersion.project_id == ctx.project_id
                )
            )
            or 0
        ) + 1
        version = m.ProjectVersion(
            project_id=ctx.project_id,
            number=number,
            name=f"Versão {number} — {plan.resolution_label} {plan.quality_mode.value.lower()}",
            analysis_id=uuid.UUID(plan.analysis_id),
            operations=[o.model_dump(mode="json", by_alias=True) for o in plan.operations],
            settings={
                "locks": plan.locks.model_dump(mode="json", by_alias=True),
                "qualityMode": plan.quality_mode.value,
            },
            job_id=ctx.job_id,
            output_id=output_id,
        )
        session.add(version)
        output = session.get(m.GenerationOutput, output_id)
        output.version_id = version.id
        row = session.get(m.GenerationPlan, plan_row.id)
        row.status = PlanStatus.EXECUTED
        project = session.get(m.Project, ctx.project_id)
        project.status = ProjectStatus.COMPLETED
        actual = session.scalar(
            select(func.coalesce(func.sum(m.CostEntry.amount), 0)).where(
                m.CostEntry.job_id == ctx.job_id, m.CostEntry.kind == CostKind.ACTUAL
            )
        )
        session.commit()
        version_id = version.id

    needs_attention = bool(unresolved)
    return {
        "outputId": str(output_id),
        "versionId": str(version_id),
        "durationSec": final_duration,
        "estimatedCost": plan.estimated_cost,
        "actualCost": round(float(actual or 0), 4),
        "currency": plan.currency,
        "needsAttention": needs_attention,
        "unresolvedIssues": unresolved,
        "repairs": sum(s.attempts for s in shots),
        "_message": (
            "Concluído — algumas partes ainda apresentam inconsistência"
            if needs_attention
            else "Concluído"
        ),
    }


def _repair(
    run: Run,
    state: ShotState,
    input_path: Path,
    issue: QAIssueCandidate,
    references: dict[str, ReferencePack],
    segments_dir: Path,
) -> None:
    """Regenerate only the faulty window when possible, then splice it in."""
    ctx, plan, dna = run.ctx, run.plan, run.dna
    shot = state.shot
    step = state.plan.steps[-1]
    window_start = max(shot.start_time, issue.start_time - 0.3)
    window_end = min(shot.end_time, issue.end_time + 0.3)
    if window_end - window_start < _MIN_WINDOW:
        window_end = min(shot.end_time, window_start + _MIN_WINDOW)
    descriptor = ctx.runtime.registry.descriptor(step.provider)
    partial_ok = FEATURE_PARTIAL_RANGE in descriptor.features and len(state.plan.steps) == 1
    whole = (window_end - window_start) >= _WHOLE_SHOT_RATIO * shot.duration or not partial_ok
    start, end = (shot.start_time, shot.end_time) if whole else (window_start, window_end)

    # Chained shots are repaired on the last step only, starting from the
    # previous step's output (never from scratch).
    base_input, offset = input_path, 0.0
    if len(state.plan.steps) > 1:
        base_input, offset = (
            segments_dir / f"{shot.id}_s{len(state.plan.steps) - 2}_a0.mp4",
            shot.start_time,
        )
    specs = _edit_specs(dna, plan, shot, step.edit_operation_ids)
    refs = [references[r] for r in state.plan.reference_packs if r in references]
    hint = f"{issue.issue_type}: {issue.description}"
    out_path, provider, cost = _generate_step(
        run,
        step,
        shot,
        input_path=base_input,
        timeline_offset=offset,
        start=start,
        end=end,
        specs=specs,
        references=refs,
        attempt=state.attempts,
        repair_hint=hint,
        out=segments_dir / f"{shot.id}_repair{state.attempts}.mp4",
    )
    run.spent += cost
    state.providers.append(provider)
    if whole:
        state.segment = out_path
    else:
        state.segment = transcode.splice(
            state.segment,
            shot.start_time,
            out_path,
            start,
            end,
            segments_dir / f"{shot.id}_spliced{state.attempts}.mp4",
            height=plan.output_height,
            fps=run.fps,
        )
    ctx.reporter.log(
        f"{shot.id}: "
        + (
            "shot inteiro regenerado"
            if whole
            else f"trecho {start:.2f}s–{end:.2f}s regenerado e substituído"
        ),
        data={"shotKey": shot.id, "whole": whole, "start": start, "end": end},
    )
