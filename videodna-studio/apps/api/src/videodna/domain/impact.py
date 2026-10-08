"""Impact analysis: what else changes when one element changes.

For each edit operation this computes an impact level, the shots and entities
it touches, the temporal/physical dependencies the generator has to honour,
and warnings (including blocking conflicts with the project locks).

Example (spec §17): replacing the glass with a plate in a "breaks" action yields
HAND_INTERACTION (the hand must hold the plate), PHYSICS_MOTION (the plate must
fall), DESTRUCTION_FX (shards must look like a plate), DERIVED_ENTITY (the shard
entity itself), GAZE_TARGET (the mother looks at it) and a future-feature
AUDIO_SFX note — and the level is HIGH.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from videodna.domain.enums import (
    DependencyType,
    EditOpType,
    EntityType,
    ImpactLevel,
    Importance,
)
from videodna.domain.operations import OperationSpec, apply_operations
from videodna.domain.settings import ProjectLocks
from videodna.domain.video_dna import Entity, VideoDNA
from videodna.domain.vocabulary import (
    CONTACT_PREDICATES,
    GAZE_PREDICATES,
    OBJECT_CLASSES,
    OCCLUSION_PREDICATES,
    VERBS,
    property_phrases,
)
from videodna.wording import count, join_and, join_or

# The switch that unblocks a story conflict, named as the editor shows it.
_STORY_SWITCH = "desligue “Manter a história” em Opções avançadas"

CHANGE_KIND_LABEL: dict[str, str] = {
    "METADATA": "correção da análise",
    "ATTRIBUTE_COLOR": "troca de cor",
    "LOCAL_APPEARANCE": "aparência",
    "OBJECT_REPLACE": "substituição de objeto",
    "OBJECT_REMOVE": "remoção de objeto",
    "OBJECT_ADD": "novo objeto",
    "ENVIRONMENT_PART": "parte do cenário",
    "ENVIRONMENT_FULL": "troca de ambiente",
    "CHARACTER_APPEARANCE": "visual do personagem",
    "CHARACTER_REPLACE": "troca de personagem",
    "CHARACTER_REMOVE": "remoção de personagem",
    "INSTRUCTION": "instrução personalizada",
}


class ChangeKind(StrEnum):
    METADATA = "METADATA"
    ATTRIBUTE_COLOR = "ATTRIBUTE_COLOR"
    LOCAL_APPEARANCE = "LOCAL_APPEARANCE"
    OBJECT_REPLACE = "OBJECT_REPLACE"
    OBJECT_REMOVE = "OBJECT_REMOVE"
    OBJECT_ADD = "OBJECT_ADD"
    ENVIRONMENT_PART = "ENVIRONMENT_PART"
    ENVIRONMENT_FULL = "ENVIRONMENT_FULL"
    CHARACTER_APPEARANCE = "CHARACTER_APPEARANCE"
    CHARACTER_REPLACE = "CHARACTER_REPLACE"
    CHARACTER_REMOVE = "CHARACTER_REMOVE"
    INSTRUCTION = "INSTRUCTION"


_BASE_LEVEL: dict[ChangeKind, ImpactLevel] = {
    ChangeKind.METADATA: ImpactLevel.NONE,
    ChangeKind.ATTRIBUTE_COLOR: ImpactLevel.LOW,
    ChangeKind.LOCAL_APPEARANCE: ImpactLevel.LOW,
    ChangeKind.OBJECT_REPLACE: ImpactLevel.MEDIUM,
    ChangeKind.OBJECT_REMOVE: ImpactLevel.MEDIUM,
    ChangeKind.OBJECT_ADD: ImpactLevel.MEDIUM,
    ChangeKind.ENVIRONMENT_PART: ImpactLevel.MEDIUM,
    ChangeKind.ENVIRONMENT_FULL: ImpactLevel.HIGH,
    ChangeKind.CHARACTER_APPEARANCE: ImpactLevel.MEDIUM,
    ChangeKind.CHARACTER_REPLACE: ImpactLevel.HIGH,
    ChangeKind.CHARACTER_REMOVE: ImpactLevel.HIGH,
    ChangeKind.INSTRUCTION: ImpactLevel.MEDIUM,
}

_LEVEL_SCORE = {
    ImpactLevel.NONE: 0.0,
    ImpactLevel.LOW: 0.25,
    ImpactLevel.MEDIUM: 0.5,
    ImpactLevel.HIGH: 0.8,
}
_LEVEL_ORDER = [ImpactLevel.NONE, ImpactLevel.LOW, ImpactLevel.MEDIUM, ImpactLevel.HIGH]

# Dependencies that escalate an edit to HIGH: they need physics-aware generation.
_ESCALATING = {
    DependencyType.PHYSICS_MOTION,
    DependencyType.DESTRUCTION_FX,
    DependencyType.HAND_INTERACTION,
}

_COLOR_PROPS = {"color", "colorHex", "colorLabel"}
_LOCAL_TYPES = {EntityType.HAIR, EntityType.WARDROBE, EntityType.ACCESSORY}
_OBJECT_TYPES = {EntityType.OBJECT, EntityType.FURNITURE}
_ENV_PART_TYPES = {EntityType.ENVIRONMENT_PART, EntityType.LIGHTING}


class _Model(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_serialization_defaults_required=True,
    )


class Dependency(_Model):
    type: DependencyType
    description: str
    entity_id: str | None = None
    action_id: str | None = None
    shot_ids: list[str] = Field(default_factory=list)
    future_feature: bool = False


class ImpactWarning(_Model):
    code: str
    message: str
    blocking: bool = False
    entity_id: str | None = None


class ImpactReport(_Model):
    operation_id: str
    entity_id: str | None
    change_kind: ChangeKind
    level: ImpactLevel
    score: float
    reasons: list[str] = Field(default_factory=list)
    affected_shot_ids: list[str] = Field(default_factory=list)
    affected_entity_ids: list[str] = Field(default_factory=list)
    dependencies: list[Dependency] = Field(default_factory=list)
    warnings: list[ImpactWarning] = Field(default_factory=list)

    @property
    def blocking(self) -> bool:
        return any(w.blocking for w in self.warnings)


def classify(op: OperationSpec, entity: Entity | None) -> ChangeKind:
    if op.op in {EditOpType.CORRECT, EditOpType.KEEP}:
        return ChangeKind.METADATA
    if entity is None:
        return ChangeKind.INSTRUCTION
    color_only = (op.op == EditOpType.SET_ATTRIBUTE and (op.property or "") in _COLOR_PROPS) or (
        op.op == EditOpType.CHANGE_APPEARANCE
        and isinstance(op.new_value, dict)
        and set(op.new_value.get("attributes", op.new_value)) <= _COLOR_PROPS | {"label"}
        and not op.instruction
    )
    if entity.type == EntityType.CHARACTER:
        if op.op == EditOpType.REPLACE:
            return ChangeKind.CHARACTER_REPLACE
        if op.op == EditOpType.REMOVE:
            return ChangeKind.CHARACTER_REMOVE
        if op.op == EditOpType.INSTRUCTION:
            return ChangeKind.INSTRUCTION
        return ChangeKind.CHARACTER_APPEARANCE
    if entity.type in _LOCAL_TYPES:
        if color_only:
            return ChangeKind.ATTRIBUTE_COLOR
        if op.op == EditOpType.REMOVE and entity.type == EntityType.ACCESSORY:
            return ChangeKind.OBJECT_REMOVE
        return ChangeKind.LOCAL_APPEARANCE
    if entity.type in _OBJECT_TYPES:
        if op.op == EditOpType.REMOVE:
            return ChangeKind.OBJECT_REMOVE
        if op.op == EditOpType.ADD_ENTITY:
            return ChangeKind.OBJECT_ADD
        if color_only:
            return ChangeKind.ATTRIBUTE_COLOR
        return ChangeKind.OBJECT_REPLACE
    if entity.type == EntityType.ENVIRONMENT:
        if op.op == EditOpType.ADD_ENTITY:
            return ChangeKind.OBJECT_ADD
        if op.op == EditOpType.INSTRUCTION:
            return ChangeKind.INSTRUCTION
        return ChangeKind.ENVIRONMENT_FULL
    if entity.type in _ENV_PART_TYPES:
        if op.op == EditOpType.ADD_ENTITY:
            return ChangeKind.OBJECT_ADD
        return ChangeKind.ENVIRONMENT_PART
    return ChangeKind.INSTRUCTION


def _raise(level: ImpactLevel, to: ImpactLevel) -> ImpactLevel:
    return to if _LEVEL_ORDER.index(to) > _LEVEL_ORDER.index(level) else level


def analyze_operation(
    original: VideoDNA,
    current: VideoDNA,
    op: OperationSpec,
    locks: ProjectLocks,
) -> ImpactReport:
    entity = original.entity(op.entity_id) if op.entity_id else None
    current_entity = current.entity(op.entity_id) if op.entity_id else None
    if entity is None and op.op == EditOpType.ADD_ENTITY:
        entity = current_entity
    kind = classify(op, entity)
    level = _BASE_LEVEL[kind]
    reasons: list[str] = []
    deps: list[Dependency] = []
    warnings: list[ImpactWarning] = []
    affected_entities: set[str] = set()

    if kind == ChangeKind.METADATA:
        return ImpactReport(
            operation_id=op.id,
            entity_id=op.entity_id,
            change_kind=kind,
            level=level,
            score=0.0,
            reasons=[
                "Este elemento continua igual ao original; nada precisa ser gerado."
                if op.op == EditOpType.KEEP
                else "Só corrige o que a análise entendeu: o vídeo não muda e nada é gerado."
            ],
        )

    if entity is None:
        shots = [s.id for s in original.shots]
        return ImpactReport(
            operation_id=op.id,
            entity_id=None,
            change_kind=kind,
            level=ImpactLevel.MEDIUM,
            score=_LEVEL_SCORE[ImpactLevel.MEDIUM],
            reasons=["Pedido geral: vale para o vídeo todo."],
            affected_shot_ids=shots,
        )

    affected_entities.add(entity.id)
    new_label = current_entity.label if current_entity else entity.label
    shots = original.shots_for_entity(entity.id) or (
        current.shots_for_entity(entity.id) if current_entity else []
    )
    if kind == ChangeKind.ENVIRONMENT_FULL:
        shots = original.shots_for_entity(entity.id) or [s.id for s in original.shots]
    affected_shots: set[str] = set(shots)
    # "Copo de vidro → Prato" says more than "Substituição de objeto em Copo de vidro".
    if kind in {ChangeKind.OBJECT_REMOVE, ChangeKind.CHARACTER_REMOVE}:
        reasons.append(f"Remover {entity.label}")
    elif new_label != entity.label:
        reasons.append(f"{entity.label} → {new_label}")
    else:
        reasons.append(f"{CHANGE_KIND_LABEL[kind.value].capitalize()}: {entity.label}")

    # --- actions: physical / temporal dependencies -------------------------
    if kind in {
        ChangeKind.OBJECT_REPLACE,
        ChangeKind.OBJECT_REMOVE,
        ChangeKind.CHARACTER_REPLACE,
        ChangeKind.CHARACTER_REMOVE,
        ChangeKind.CHARACTER_APPEARANCE,
    }:
        new_class = OBJECT_CLASSES.get(
            str(current_entity.attributes.get("class", "")) if current_entity else ""
        )
        unknown_props: list[str] = []
        missing_props: list[str] = []
        incompatible_blocks = False
        lost_actions: list[str] = []
        for action in original.actions_involving(entity.id):
            spec = VERBS.get(action.verb)
            if spec is None:
                continue
            affected_shots.update(action.shot_ids)
            dep_types: list[DependencyType] = []
            if entity.id in action.target_ids:
                dep_types += list(spec.target_dependencies)
            if action.actor_id == entity.id:
                dep_types += list(spec.actor_dependencies)
            actor = original.entity(action.actor_id) if action.actor_id else None
            for dep_type in dep_types:
                deps.append(
                    _describe_dependency(
                        dep_type,
                        entity,
                        new_label,
                        actor,
                        action.id,
                        action.shot_ids,
                        locks,
                        original,
                    )
                )
            if action.actor_id and action.actor_id != entity.id:
                affected_entities.add(action.actor_id)
            if kind == ChangeKind.OBJECT_REPLACE and spec.requires_properties:
                if new_class is None and current_entity and current_entity.attributes.get("class"):
                    unknown_props += spec.requires_properties
                elif new_class is not None:
                    missing = [p for p in spec.requires_properties if p not in new_class.properties]
                    missing_props += missing
                    incompatible_blocks |= bool(missing) and locks.story and action.essential
            if kind in {ChangeKind.OBJECT_REMOVE, ChangeKind.CHARACTER_REMOVE} and action.essential:
                lost_actions.append(f"“{action.label}”")

        # One sentence per element, not one per action: removing the glass loses
        # three actions, and three near-identical warnings read as three problems.
        if unknown_props:
            warnings.append(
                ImpactWarning(
                    code="PHYSICS_UNKNOWN",
                    message=(
                        f"Não conhecemos bem “{new_label}”: talvez não "
                        f"{property_phrases(unknown_props)} como no vídeo original. "
                        "Confira o resultado com atenção."
                    ),
                    entity_id=entity.id,
                )
            )
        if missing_props:
            warnings.append(
                ImpactWarning(
                    code="INCOMPATIBLE_ACTION",
                    message=(
                        f"{new_label} talvez não {property_phrases(missing_props)} como no vídeo "
                        "original. "
                        + (
                            f"Escolha outro objeto ou {_STORY_SWITCH}."
                            if incompatible_blocks
                            else "Confira o resultado com atenção."
                        )
                    ),
                    blocking=incompatible_blocks,
                    entity_id=entity.id,
                )
            )
        if lost_actions:
            warnings.append(
                ImpactWarning(
                    code="STORY_LOCK" if locks.story else "STORY_CHANGE",
                    message=(
                        f"Remover {entity.label} apaga "
                        + (
                            "uma parte importante da história"
                            if len(lost_actions) == 1
                            else "partes importantes da história"
                        )
                        + f" ({join_and(lost_actions)}). "
                        + (
                            f"Para remover mesmo assim, {_STORY_SWITCH}."
                            if locks.story
                            else "A história do vídeo vai mudar."
                        )
                    ),
                    blocking=locks.story,
                    entity_id=entity.id,
                )
            )

    # --- derived entities (shards, spilled liquid...) -----------------------
    for derived in (e for e in original.entities if e.derived_from == entity.id):
        affected_entities.add(derived.id)
        derived_shots = original.shots_for_entity(derived.id)
        affected_shots.update(derived_shots)
        cur = current.entity(derived.id)
        deps.append(
            Dependency(
                type=DependencyType.DERIVED_ENTITY,
                description=(
                    f"{derived.label} → {cur.label}"
                    if cur and cur.label != derived.label
                    else f"Também muda: {derived.label}"
                ),
                entity_id=derived.id,
                shot_ids=derived_shots,
            )
        )

    # --- relationships: contact, gaze, occlusion ----------------------------
    if kind not in {ChangeKind.ATTRIBUTE_COLOR, ChangeKind.LOCAL_APPEARANCE}:
        for rel in original.relationships_involving(entity.id):
            other_id = rel.object_id if rel.subject_id == entity.id else rel.subject_id
            other = original.entity(other_id)
            other_label = other.label if other else other_id
            if rel.predicate in CONTACT_PREDICATES and rel.predicate != "holds":
                dep_type = DependencyType.CONTACT_SURFACE
                text = f"O contato entre {new_label} e {other_label} precisa continuar certo"
            elif rel.predicate in GAZE_PREDICATES and rel.object_id == entity.id:
                dep_type = DependencyType.GAZE_TARGET
                text = (
                    f"{other_label} olha para {new_label}: o olhar precisa continuar "
                    "na direção certa"
                )
            elif rel.predicate in OCCLUSION_PREDICATES:
                dep_type = DependencyType.OCCLUSION
                text = (
                    f"{new_label} e {other_label} se sobrepõem na imagem: "
                    "a sobreposição precisa continuar certa"
                )
            else:
                continue
            deps.append(
                Dependency(
                    type=dep_type, description=text, entity_id=other_id, shot_ids=rel.shot_ids
                )
            )

    # --- environment-wide changes ----------------------------------------------
    if kind == ChangeKind.ENVIRONMENT_FULL:
        children = [
            c
            for c in current.descendants_of(entity.id)
            if not (c.edit and c.edit.locked) and c.type != EntityType.CHARACTER
        ]
        affected_entities.update(c.id for c in children)
        deps.append(
            Dependency(
                type=DependencyType.CHILD_ELEMENTS,
                description=count(
                    len(children),
                    "elemento do cenário será adaptado ao novo estilo",
                    "elementos do cenário serão adaptados ao novo estilo",
                ),
                entity_id=entity.id,
                shot_ids=sorted(affected_shots),
            )
        )
        deps.append(
            Dependency(
                type=DependencyType.LIGHTING,
                description="A iluminação dos personagens deve acompanhar o novo ambiente",
                entity_id=entity.id,
                shot_ids=sorted(affected_shots),
            )
        )
        if locks.camera:
            reasons.append("A câmera continua igual: mesmo ângulo, movimento e cortes")

    if kind == ChangeKind.ENVIRONMENT_PART and entity.subtype == "window_view":
        deps.append(
            Dependency(
                type=DependencyType.LIGHTING,
                description="A luz que entra pela janela deve combinar com a nova vista",
                entity_id=entity.id,
                shot_ids=sorted(affected_shots),
            )
        )

    # --- characters: continuity & motion ---------------------------------------
    character_id = _owning_character(original, entity)
    if character_id and kind != ChangeKind.CHARACTER_REMOVE:
        affected_entities.add(character_id)
        if len(affected_shots) > 1:
            deps.append(
                Dependency(
                    type=DependencyType.CONTINUITY,
                    description=(
                        f"A aparência de {_label(original, character_id)} precisa ficar igual "
                        f"nas {len(affected_shots)} cenas"
                    ),
                    entity_id=character_id,
                    shot_ids=sorted(affected_shots),
                )
            )
        if kind == ChangeKind.CHARACTER_REPLACE and locks.motion:
            reasons.append("Poses, gestos e movimentos continuam iguais ao original")
    elif entity.type in _OBJECT_TYPES and len(affected_shots) > 1:
        deps.append(
            Dependency(
                type=DependencyType.CONTINUITY,
                description=f"{new_label} precisa ficar igual nas {len(affected_shots)} cenas",
                entity_id=entity.id,
                shot_ids=sorted(affected_shots),
            )
        )

    # --- narrative role ------------------------------------------------------
    if entity.importance == Importance.ESSENTIAL and kind not in {
        ChangeKind.ATTRIBUTE_COLOR,
        ChangeKind.LOCAL_APPEARANCE,
    }:
        deps.append(
            Dependency(
                type=DependencyType.STORY_ROLE,
                description=(
                    "Parte importante da história"
                    + (": a história continua a mesma" if locks.story else "")
                ),
                entity_id=entity.id,
                shot_ids=sorted(affected_shots),
            )
        )
        level = _raise(level, ImpactLevel.MEDIUM)

    # --- uncertainty ---------------------------------------------------------
    # Judged on the edited DNA: replacing a doubtful element resolves the doubt.
    if current_entity is not None and current_entity.needs_review:
        alternatives = join_or(
            [current_entity.label, *(a.label for a in current_entity.alternatives)]
        )
        warnings.append(
            ImpactWarning(
                code="LOW_CONFIDENCE",
                message=(
                    f"A análise não tem certeza do que é este elemento ({alternatives}). "
                    "Confirme o que é antes de gerar."
                ),
                entity_id=entity.id,
            )
        )

    if any(d.type in _ESCALATING for d in deps):
        level = ImpactLevel.HIGH
        reasons.append("Envolve mãos, quedas ou objetos quebrando ao longo do vídeo")

    score = _LEVEL_SCORE[level] + min(0.19, 0.02 * len(deps) + 0.01 * len(affected_shots))
    order = {s.id: s.index for s in original.shots}
    return ImpactReport(
        operation_id=op.id,
        entity_id=entity.id,
        change_kind=kind,
        level=level,
        score=round(score, 3),
        reasons=reasons,
        affected_shot_ids=sorted(affected_shots, key=lambda s: order.get(s, 0)),
        affected_entity_ids=sorted(affected_entities),
        dependencies=_dedupe(deps),
        warnings=warnings,
    )


def _label(dna: VideoDNA, entity_id: str) -> str:
    entity = dna.entity(entity_id)
    return entity.label if entity else "o personagem"


def _owning_character(dna: VideoDNA, entity: Entity) -> str | None:
    current: Entity | None = entity
    while current is not None:
        if current.type == EntityType.CHARACTER:
            return current.id
        current = dna.entity(current.parent_id) if current.parent_id else None
    return None


def _describe_dependency(
    dep_type: DependencyType,
    entity: Entity,
    new_label: str,
    actor: Entity | None,
    action_id: str,
    shot_ids: list[str],
    locks: ProjectLocks,
    dna: VideoDNA,
) -> Dependency:
    actor_label = actor.label if actor else "o personagem"
    text = {
        DependencyType.HAND_INTERACTION: f"A mão de {actor_label} precisa segurar {new_label}",
        DependencyType.PHYSICS_MOTION: (
            f"{new_label} precisa cair acompanhando o movimento original"
        ),
        DependencyType.DESTRUCTION_FX: (
            f"{new_label} deve quebrar e os fragmentos devem parecer de {new_label.lower()}"
        ),
        # Sound is not regenerated yet: with "Manter o som" off the result is silent.
        DependencyType.AUDIO_SFX: (
            "Os sons continuam os do vídeo original (“Manter o som” está ligado)"
            if locks.audio
            else "Mudar os sons junto com a imagem ainda não é possível nesta versão"
        ),
        DependencyType.CONTINUITY: f"{entity.label} precisa ficar igual de uma cena para a outra",
        DependencyType.CONTACT_SURFACE: (
            f"O contato de {new_label} com a superfície precisa continuar certo"
        ),
        DependencyType.GAZE_TARGET: f"O olhar na direção de {new_label} precisa continuar certo",
    }.get(dep_type, "Precisa continuar coerente com o resto do vídeo")
    return Dependency(
        type=dep_type,
        description=text,
        entity_id=entity.id,
        action_id=action_id,
        shot_ids=shot_ids,
        future_feature=dep_type == DependencyType.AUDIO_SFX,
    )


def _dedupe(deps: list[Dependency]) -> list[Dependency]:
    seen: set[tuple[str, str | None, str | None, str]] = set()
    out: list[Dependency] = []
    for d in deps:
        key = (d.type.value, d.entity_id, d.action_id, d.description)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def analyze_operations(
    original: VideoDNA, operations: list[OperationSpec], locks: ProjectLocks
) -> list[ImpactReport]:
    current = apply_operations(original, operations)
    return [analyze_operation(original, current, op, locks) for op in operations]
