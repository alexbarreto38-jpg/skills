"""Generation Planner (spec §24/§27/§46/§63).

Nothing expensive is called without a plan. For every shot the planner picks
the *lightest* strategy that can deliver the requested edits:

    PASSTHROUGH < ATTRIBUTE_EDIT < LOCALIZED_EDIT < BACKGROUND_REPLACEMENT
                < SHOT_RECONSTRUCTION < FULL_REGENERATION

…escalating only when the combination of edits makes chained light passes
riskier (artifacts compound) than one heavier pass. The quality mode moves
those thresholds. Shots without edits are copied untouched (zero cost).
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from videodna.db import models as m
from videodna.domain.enums import (
    CostKind,
    DependencyType,
    EntityType,
    QualityMode,
    RenderKind,
    Strategy,
)
from videodna.domain.impact import ChangeKind, Dependency, ImpactReport, analyze_operation
from videodna.domain.operations import OperationSpec, apply_operations, is_generative
from videodna.domain.video_dna import VideoDNA
from videodna.errors import AppError
from videodna.media.hashing import sha256_text
from videodna.media.transcode import target_height
from videodna.orchestrator.capabilities import (
    FEATURE_CAMERA_PRESERVATION,
    FEATURE_MASK_INPUT,
    FEATURE_MOTION_PRESERVATION,
    FEATURE_REFERENCE_IMAGES,
    Capability,
)
from videodna.orchestrator.router import RoutingDecision, RoutingTask
from videodna.runtime import Runtime
from videodna.services.editing import active_ops, current_state, require_analysis, to_spec
from videodna.services.generation.plan_models import (
    CostLine,
    GenerationPlanSpec,
    GenerationStep,
    PlannedEdit,
    PlanSummary,
    PlanWarning,
    PreStep,
    ReferencePackPlan,
    ShotPlan,
)
from videodna.services.projects import settings_of

STRATEGY_CAPABILITY: dict[Strategy, Capability] = {
    Strategy.ATTRIBUTE_EDIT: Capability.VIDEO_ATTRIBUTE_EDIT,
    Strategy.LOCALIZED_EDIT: Capability.VIDEO_LOCALIZED_EDIT,
    Strategy.BACKGROUND_REPLACEMENT: Capability.VIDEO_BACKGROUND_REPLACE,
    Strategy.SHOT_RECONSTRUCTION: Capability.VIDEO_SHOT_RECONSTRUCTION,
    Strategy.FULL_REGENERATION: Capability.VIDEO_FULL_GENERATION,
}

_WEIGHT: dict[ChangeKind, int] = {
    ChangeKind.ATTRIBUTE_COLOR: 1,
    ChangeKind.LOCAL_APPEARANCE: 2,
    ChangeKind.OBJECT_REPLACE: 2,
    ChangeKind.OBJECT_REMOVE: 2,
    ChangeKind.OBJECT_ADD: 2,
    ChangeKind.ENVIRONMENT_PART: 2,
    ChangeKind.ENVIRONMENT_FULL: 4,
    ChangeKind.CHARACTER_APPEARANCE: 3,
    ChangeKind.CHARACTER_REPLACE: 5,
    ChangeKind.CHARACTER_REMOVE: 5,
    ChangeKind.INSTRUCTION: 2,
}
# Complexity at which one heavy pass beats several light ones.
_RECONSTRUCT_AT: dict[QualityMode, int] = {
    QualityMode.ECONOMY: 10,
    QualityMode.BALANCED: 8,
    QualityMode.MAX: 6,
}
_PHYSICS = {
    DependencyType.PHYSICS_MOTION,
    DependencyType.DESTRUCTION_FX,
    DependencyType.HAND_INTERACTION,
}
_ENV_KINDS = {ChangeKind.ENVIRONMENT_FULL, ChangeKind.ENVIRONMENT_PART}
_REPAIR_FRACTION = Decimal("0.5")  # a localized repair regenerates ~half a shot


def ops_fingerprint(
    analysis_id: str,
    ops: list[OperationSpec],
    quality_mode: QualityMode,
    render_kind: RenderKind,
    locks_json: str,
) -> str:
    return sha256_text(
        analysis_id,
        quality_mode.value,
        render_kind.value,
        locks_json,
        *sorted(f"{o.id}:{o.sequence}" for o in ops),
    )


def _complexity(impacts: list[ImpactReport]) -> int:
    total = 0
    for imp in impacts:
        total += _WEIGHT.get(imp.change_kind, 1)
        if any(d.type in _PHYSICS for d in imp.dependencies):
            total += 1
    return total


def choose_strategy(
    impacts: list[ImpactReport], mode: QualityMode
) -> list[tuple[Strategy, list[ImpactReport]]]:
    """Return the ordered generation steps for one shot."""
    if not impacts:
        return []
    kinds = {i.change_kind for i in impacts}
    complexity = _complexity(impacts)
    threshold = _RECONSTRUCT_AT[mode]
    if kinds <= {ChangeKind.ATTRIBUTE_COLOR}:
        return [(Strategy.ATTRIBUTE_EDIT, impacts)]
    if kinds & {ChangeKind.CHARACTER_REPLACE, ChangeKind.CHARACTER_REMOVE}:
        return [(Strategy.SHOT_RECONSTRUCTION, impacts)]
    if ChangeKind.ENVIRONMENT_FULL in kinds:
        env = [i for i in impacts if i.change_kind in _ENV_KINDS]
        local = [i for i in impacts if i.change_kind not in _ENV_KINDS]
        if not local:
            return [(Strategy.BACKGROUND_REPLACEMENT, impacts)]
        if mode == QualityMode.ECONOMY and complexity < threshold:
            # Cheapest acceptable: swap the background, then edit locally.
            return [(Strategy.BACKGROUND_REPLACEMENT, env), (Strategy.LOCALIZED_EDIT, local)]
        return [(Strategy.SHOT_RECONSTRUCTION, impacts)]
    if complexity >= threshold:
        return [(Strategy.SHOT_RECONSTRUCTION, impacts)]
    return [(Strategy.LOCALIZED_EDIT, impacts)]


def _required_features(strategy: Strategy, locks, needs_references: bool) -> frozenset[str]:
    features: set[str] = set()
    if strategy in {Strategy.ATTRIBUTE_EDIT, Strategy.LOCALIZED_EDIT}:
        features.add(FEATURE_MASK_INPUT)
    if strategy in {Strategy.BACKGROUND_REPLACEMENT, Strategy.SHOT_RECONSTRUCTION} and locks.camera:
        features.add(FEATURE_CAMERA_PRESERVATION)
    if strategy == Strategy.SHOT_RECONSTRUCTION and locks.motion:
        features.add(FEATURE_MOTION_PRESERVATION)
    if needs_references and strategy in {Strategy.SHOT_RECONSTRUCTION, Strategy.FULL_REGENERATION}:
        features.add(FEATURE_REFERENCE_IMAGES)
    return frozenset(features)


def _edit_description(
    original: VideoDNA, current: VideoDNA, op: OperationSpec, kind: ChangeKind
) -> PlannedEdit:
    before = original.entity(op.entity_id) if op.entity_id else None
    after = current.entity(op.entity_id) if op.entity_id else None
    if op.op.value == "REMOVE":
        text = f"Remover {before.label if before else op.entity_id}"
    elif op.op.value == "ADD_ENTITY":
        label = op.new_value.get("label") if isinstance(op.new_value, dict) else "elemento"
        text = f"Adicionar {label}" + (f" em {before.label}" if before else "")
    elif op.op.value == "INSTRUCTION":
        text = f"Instrução: {op.instruction}"
    elif before and after:
        text = (
            f"{before.label} → {after.label}"
            if before.label != after.label
            else f"{after.label}: alterar aparência"
        )
        if op.instruction:
            text += f" ({op.instruction})"
    else:
        text = op.instruction or op.op.value
    return PlannedEdit(
        operation_id=op.id,
        entity_key=op.entity_id,
        entity_label=(after or before).label if (after or before) else (op.entity_id or "projeto"),
        change_kind=kind.value,
        description=text,
    )


def _owning_character(dna: VideoDNA, entity_key: str | None) -> str | None:
    current = dna.entity(entity_key) if entity_key else None
    while current is not None:
        if current.type == EntityType.CHARACTER:
            return current.id
        current = dna.entity(current.parent_id) if current.parent_id else None
    return None


def build_plan(
    db: Session,
    runtime: Runtime,
    user: m.User,
    project: m.Project,
    *,
    quality_mode: QualityMode,
    render_kind: RenderKind,
) -> GenerationPlanSpec:
    settings = runtime.settings
    router = runtime.orchestrator
    analysis, original, current, op_rows = current_state(db, project)
    locks = settings_of(project).locks
    specs = [to_spec(o) for o in op_rows]
    fingerprint = ops_fingerprint(
        str(analysis.id), specs, quality_mode, render_kind, locks.model_dump_json()
    )
    impacts = [analyze_operation(original, current, spec, locks) for spec in specs]
    by_op = {imp.operation_id: imp for imp in impacts}
    generative = [spec for spec in specs if is_generative(spec)]

    source_height = original.technical.height
    wanted = settings.proxy_height if render_kind == RenderKind.PREVIEW else settings.final_height
    out_height = target_height(source_height, wanted)
    warnings: list[PlanWarning] = []
    cost_lines: list[CostLine] = []
    providers: set[str] = set()

    # --- per-shot impacts ---------------------------------------------------------
    impacts_by_shot: dict[str, list[ImpactReport]] = defaultdict(list)
    for spec in generative:
        imp = by_op[spec.id]
        if imp.change_kind == ChangeKind.METADATA:
            continue
        for shot_id in imp.affected_shot_ids:
            impacts_by_shot[shot_id].append(imp)

    # --- reference packs (continuity, spec §28/§29) -----------------------------------
    modified_characters: dict[str, set[str]] = defaultdict(set)
    scene_modified = False
    for spec in generative:
        imp = by_op[spec.id]
        char = _owning_character(original, spec.entity_id)
        if char:
            modified_characters[char].update(imp.affected_shot_ids)
        if imp.change_kind in _ENV_KINDS:
            scene_modified = True
    packs: list[ReferencePackPlan] = []
    pack_task = RoutingTask(capability=Capability.IMAGE_GENERATE, quantity=2)
    try:
        pack_decision: RoutingDecision | None = router.route(pack_task)
    except AppError:
        pack_decision = None
    for char_key, shots in sorted(modified_characters.items()):
        entity = current.entity(char_key)
        if entity is None:
            continue
        children = ", ".join(
            c.label for c in current.descendants_of(char_key) if c.type != EntityType.CHARACTER
        )
        packs.append(
            ReferencePackPlan(
                id=f"REFPACK_{char_key}",
                kind="character",
                entity_key=char_key,
                label=f"Character Reference Pack — {entity.label}",
                description=f"{entity.label}: {children}",
                shot_keys=sorted(shots),
                images=2,
                provider=pack_decision.provider if pack_decision else None,
                estimated_cost=float(pack_decision.estimated_cost) if pack_decision else 0.0,
            )
        )
    environment = next((e for e in current.entities if e.type == EntityType.ENVIRONMENT), None)
    if scene_modified and environment is not None:
        parts = ", ".join(c.label for c in current.descendants_of(environment.id)[:8])
        packs.append(
            ReferencePackPlan(
                id=f"REFPACK_{environment.id}",
                kind="scene",
                entity_key=environment.id,
                label=f"Scene Reference Pack — {environment.label}",
                description=f"{environment.label}: {parts}",
                shot_keys=sorted(
                    {
                        sid
                        for sc in current.scenes
                        if sc.environment_id == environment.id
                        for sid in sc.shot_ids
                    }
                ),
                images=2,
                provider=pack_decision.provider if pack_decision else None,
                estimated_cost=float(pack_decision.estimated_cost) if pack_decision else 0.0,
            )
        )
    for pack in packs:
        if pack.estimated_cost:
            cost_lines.append(
                CostLine(label=pack.label, provider=pack.provider, amount=pack.estimated_cost)
            )

    # --- shots ------------------------------------------------------------------------
    shot_plans: list[ShotPlan] = []
    qa_task_cap = Capability.QA_VIDEO_INSPECTION
    for shot in original.shots:
        shot_impacts = impacts_by_shot.get(shot.id, [])
        plan = ShotPlan(
            shot_key=shot.id,
            index=shot.index,
            start_time=shot.start_time,
            end_time=shot.end_time,
            duration=shot.duration,
            strategy=Strategy.PASSTHROUGH,
        )
        steps = choose_strategy(shot_impacts, quality_mode)
        if not steps:
            shot_plans.append(plan)
            continue
        plan.complexity = _complexity(shot_impacts)
        plan.edits = [
            _edit_description(
                original,
                current,
                next(s for s in specs if s.id == imp.operation_id),
                imp.change_kind,
            )
            for imp in shot_impacts
        ]
        deps: list[Dependency] = []
        for imp in shot_impacts:
            deps.extend(d for d in imp.dependencies if not d.shot_ids or shot.id in d.shot_ids)
        plan.dependencies = deps
        plan.reference_packs = [p.id for p in packs if shot.id in p.shot_keys]
        needs_refs = bool(plan.reference_packs)

        for strategy, step_impacts in steps:
            decision, strategy = _route_step(
                router,
                strategy,
                quality_mode,
                shot.duration,
                out_height,
                locks,
                needs_refs,
                len(step_impacts),
                warnings,
                shot.id,
            )
            if decision is None:
                continue
            providers.add(decision.provider)
            plan.steps.append(
                GenerationStep(
                    strategy=strategy,
                    capability=decision.capability.value,
                    provider=decision.provider,
                    model=decision.model,
                    chunks=decision.chunks,
                    edit_operation_ids=[i.operation_id for i in step_impacts],
                    required_features=sorted(_required_features(strategy, locks, needs_refs)),
                    estimated_cost=float(decision.estimated_cost),
                    estimated_latency_sec=decision.estimated_latency_sec,
                    routing=decision.to_dict(),
                )
            )
            cost_lines.append(
                CostLine(
                    label=f"{shot.id} · {strategy.value}",
                    provider=decision.provider,
                    amount=float(decision.estimated_cost),
                )
            )
        plan.strategy = max(
            (s.strategy for s in plan.steps), key=list(Strategy).index, default=Strategy.PASSTHROUGH
        )

        # Segmentation masks are computed only for what is edited (on demand).
        if any(
            s.strategy in {Strategy.ATTRIBUTE_EDIT, Strategy.LOCALIZED_EDIT} for s in plan.steps
        ):
            keys = sorted(
                {
                    i.entity_id
                    for i in shot_impacts
                    if i.entity_id and i.change_kind not in _ENV_KINDS
                }
            )
            if keys:
                try:
                    seg = router.route(
                        RoutingTask(capability=Capability.SEGMENTATION_IMAGE, quantity=len(keys))
                    )
                    plan.pre_steps.append(
                        PreStep(
                            kind="SEGMENTATION",
                            entity_keys=keys,
                            provider=seg.provider,
                            model=seg.model,
                            estimated_cost=float(seg.estimated_cost),
                        )
                    )
                    providers.add(seg.provider)
                    if seg.estimated_cost:
                        cost_lines.append(
                            CostLine(
                                label=f"{shot.id} · máscaras",
                                provider=seg.provider,
                                amount=float(seg.estimated_cost),
                            )
                        )
                except AppError:
                    warnings.append(
                        PlanWarning(
                            code="NO_SEGMENTATION",
                            message=(
                                f"Sem provider de segmentação para {shot.id}; "
                                "a edição usará apenas o tracking."
                            ),
                        )
                    )

        try:
            qa = router.route(RoutingTask(capability=qa_task_cap, duration_sec=shot.duration))
            plan.qa_provider = qa.provider
            plan.qa_estimated_cost = float(qa.estimated_cost)
            providers.add(qa.provider)
            if qa.estimated_cost:
                cost_lines.append(
                    CostLine(
                        label=f"{shot.id} · QA",
                        provider=qa.provider,
                        amount=float(qa.estimated_cost),
                    )
                )
        except AppError:
            warnings.append(
                PlanWarning(
                    code="NO_AI_QA",
                    message="Sem inspetor de IA disponível; apenas QA técnico será executado.",
                )
            )

        plan.estimated_cost = round(
            sum(s.estimated_cost for s in plan.steps)
            + sum(p.estimated_cost for p in plan.pre_steps)
            + plan.qa_estimated_cost,
            4,
        )
        plan.expected_duration_sec = round(
            sum(s.estimated_latency_sec for s in plan.steps) + 2.0, 1
        )
        shot_plans.append(plan)

    # --- warnings from impacts / analysis confidence ------------------------------------
    for imp in impacts:
        for w in imp.warnings:
            warnings.append(
                PlanWarning(
                    code=w.code, message=w.message, blocking=w.blocking, entity_key=w.entity_id
                )
            )
    generated = [p for p in shot_plans if p.steps]
    if not generative:
        warnings.append(
            PlanWarning(
                code="NOTHING_TO_GENERATE",
                message="Nenhuma alteração visual para gerar.",
                blocking=True,
            )
        )
    elif not generated:
        warnings.append(
            PlanWarning(
                code="NO_SHOTS_AFFECTED",
                message="As alterações não afetam nenhum shot visível.",
                blocking=True,
            )
        )
    if locks.audio and any(
        d.type == DependencyType.AUDIO_SFX for p in generated for d in p.dependencies
    ):
        warnings.append(
            PlanWarning(
                code="AUDIO_LOCKED",
                message=(
                    "LOCK AUDIO ativo: o áudio original será mantido, inclusive efeitos sonoros."
                ),
            )
        )
    if locks.timing:
        warnings.append(
            PlanWarning(
                code="TIMING_LOCKED",
                message="LOCK TIMING ativo: duração e ritmo de cada shot serão preservados.",
            )
        )

    base = Decimal(str(sum(p.estimated_cost for p in shot_plans))) + Decimal(
        str(sum(p.estimated_cost for p in packs))
    )
    max_retries = settings.max_retries_for(quality_mode.value)

    # Repair budget: shots whose edits involve physics are the ones video models
    # get wrong most often, so each is budgeted one partial repair; the worst
    # shot is budgeted the remaining retries on top.
    def step_cost(p: ShotPlan) -> Decimal:
        return Decimal(str(sum(s.estimated_cost for s in p.steps)))

    risky = [p for p in generated if any(d.type in _PHYSICS for d in p.dependencies)]
    worst_shot = max((step_cost(p) for p in generated), default=Decimal(0))
    repairs = (
        sum((step_cost(p) * _REPAIR_FRACTION for p in risky), Decimal(0))
        if max_retries
        else Decimal(0)
    )
    repairs += worst_shot * _REPAIR_FRACTION * max(0, max_retries - 1)
    with_repairs = base + repairs

    budget_warning = _budget_warning(db, runtime, user, base)
    if budget_warning:
        warnings.append(budget_warning)

    strategies: dict[str, int] = defaultdict(int)
    for p in shot_plans:
        strategies[p.strategy.value] += 1
    expected = sum(p.expected_duration_sec for p in generated) / 2 + 3 * len(generated)

    return GenerationPlanSpec(
        project_id=str(project.id),
        analysis_id=str(analysis.id),
        quality_mode=quality_mode,
        render_kind=render_kind,
        output_height=out_height,
        resolution_label=f"{out_height}p",
        locks=locks,
        operations=specs,
        summary=PlanSummary(
            total_shots=len(shot_plans),
            affected_shots=len(generated),
            passthrough_shots=len(shot_plans) - len(generated),
            generations=sum(len(p.steps) for p in generated),
            edit_count=len(generative),
            strategies=dict(strategies),
        ),
        shots=shot_plans,
        reference_packs=packs,
        impacts=impacts,
        warnings=warnings,
        blocking=any(w.blocking for w in warnings),
        max_retries=max_retries,
        estimated_cost=float(base.quantize(Decimal("0.01"))),
        estimated_cost_with_repairs=float(with_repairs.quantize(Decimal("0.01"))),
        currency=settings.cost_currency,
        expected_duration_sec=round(expected, 1),
        cost_breakdown=cost_lines,
        providers=sorted(providers),
        ops_fingerprint=fingerprint,
    )


def _route_step(
    router,
    strategy: Strategy,
    mode: QualityMode,
    duration: float,
    height: int,
    locks,
    needs_refs: bool,
    edit_count: int,
    warnings: list[PlanWarning],
    shot_key: str,
) -> tuple[RoutingDecision | None, Strategy]:
    """Route a step; escalate one level when no provider supports the lighter
    strategy (e.g. too many edits for the economic editor)."""
    ladder = [strategy]
    if strategy in {Strategy.ATTRIBUTE_EDIT, Strategy.LOCALIZED_EDIT}:
        ladder.append(Strategy.SHOT_RECONSTRUCTION)
    if strategy == Strategy.SHOT_RECONSTRUCTION and not (locks.motion or locks.camera):
        ladder.append(Strategy.FULL_REGENERATION)
    for candidate in ladder:
        task = RoutingTask(
            capability=STRATEGY_CAPABILITY[candidate],
            quality_mode=mode,
            duration_sec=duration,
            output_height=height,
            required_features=_required_features(candidate, locks, needs_refs),
            edit_count=edit_count,
        )
        try:
            decision = router.route(task)
        except AppError:
            continue
        if candidate != strategy:
            warnings.append(
                PlanWarning(
                    code="STRATEGY_ESCALATED",
                    message=(
                        f"{shot_key}: nenhum provider para {strategy.value}; "
                        f"usando {candidate.value}."
                    ),
                )
            )
        return decision, candidate
    warnings.append(
        PlanWarning(
            code="NO_PROVIDER",
            message=f"{shot_key}: nenhum provider disponível para {strategy.value}.",
            blocking=True,
        )
    )
    return None, strategy


def _budget_warning(
    db: Session, runtime: Runtime, user: m.User, estimate: Decimal
) -> PlanWarning | None:
    if user.budget_limit is None:
        return None
    spent = db.scalar(
        select(func.coalesce(func.sum(m.CostEntry.amount), 0)).where(
            m.CostEntry.user_id == user.id, m.CostEntry.kind == CostKind.ACTUAL
        )
    ) or Decimal(0)
    if Decimal(spent) + estimate > user.budget_limit:
        return PlanWarning(
            code="INSUFFICIENT_CREDITS",
            message=(
                f"Orçamento insuficiente: gasto {float(spent):.2f} + "
                f"estimativa {float(estimate):.2f} "
                f"> limite {float(user.budget_limit):.2f} {runtime.settings.cost_currency}."
            ),
            blocking=True,
        )
    return None


def current_fingerprint(
    db: Session, project: m.Project, quality_mode: QualityMode, render_kind: RenderKind
) -> str:
    analysis = require_analysis(db, project)
    specs = [to_spec(o) for o in active_ops(db, project, analysis.id)]
    return ops_fingerprint(
        str(analysis.id),
        specs,
        quality_mode,
        render_kind,
        settings_of(project).locks.model_dump_json(),
    )


def planned_dna(original: VideoDNA, plan: GenerationPlanSpec) -> VideoDNA:
    """The exact DNA the plan was computed for (edits made later don't leak in)."""
    return apply_operations(original, plan.operations)


def nothing_to_generate(plan: GenerationPlanSpec) -> bool:
    return any(w.code in {"NOTHING_TO_GENERATE", "NO_SHOTS_AFFECTED"} for w in plan.warnings)
