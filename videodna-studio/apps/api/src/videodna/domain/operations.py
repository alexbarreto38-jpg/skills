"""Edit operations: OriginalVideoDNA + EditOperations = CurrentVideoDNA.

Pure functions only — no database, no providers. The original DNA is never
mutated; `apply_operations` returns a new document with an `edit` overlay on
every touched entity, which is what makes undo/redo and versioning trivial.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from videodna.domain.enums import (
    ENTITY_KEY_PREFIX,
    EditOpType,
    EditSource,
    EntityType,
    Importance,
)
from videodna.domain.video_dna import (
    Appearance,
    Entity,
    EntityEditState,
    Relationship,
    VideoDNA,
)
from videodna.domain.vocabulary import OBJECT_CLASSES

# Operations that change pixels and therefore require generation.
GENERATIVE_OPS = frozenset(
    {
        EditOpType.SET_ATTRIBUTE,
        EditOpType.CHANGE_APPEARANCE,
        EditOpType.REPLACE,
        EditOpType.REMOVE,
        EditOpType.APPLY_PRESET,
        EditOpType.ADD_ENTITY,
        EditOpType.INSTRUCTION,
    }
)

CORRECTABLE_FIELDS = frozenset({"label", "type", "subtype", "importance", "description"})

ALLOWED_OPS: dict[EntityType, frozenset[EditOpType]] = {
    EntityType.CHARACTER: frozenset(
        {
            EditOpType.REPLACE,
            EditOpType.CHANGE_APPEARANCE,
            EditOpType.SET_ATTRIBUTE,
            EditOpType.KEEP,
            EditOpType.CORRECT,
            EditOpType.INSTRUCTION,
            EditOpType.REMOVE,
        }
    ),
    EntityType.ENVIRONMENT: frozenset(
        {
            EditOpType.APPLY_PRESET,
            EditOpType.CHANGE_APPEARANCE,
            EditOpType.SET_ATTRIBUTE,
            EditOpType.KEEP,
            EditOpType.CORRECT,
            EditOpType.INSTRUCTION,
            EditOpType.ADD_ENTITY,
        }
    ),
}
_DEFAULT_ALLOWED = frozenset(set(EditOpType) - {EditOpType.APPLY_PRESET})


class OperationSpec(BaseModel):
    """Domain view of an edit operation (the DB row maps 1:1 onto this)."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_serialization_defaults_required=True,
    )

    id: str
    sequence: int
    entity_id: str | None = None
    op: EditOpType
    property: str | None = None
    new_value: Any = None
    previous_value: Any = None
    instruction: str | None = None
    source: EditSource = EditSource.MANUAL


class OperationError(ValueError):
    pass


def _entity_or_raise(dna: VideoDNA, entity_id: str | None) -> Entity:
    if not entity_id:
        raise OperationError("operation requires an entity")
    entity = dna.entity(entity_id)
    if entity is None:
        raise OperationError(f"unknown entity {entity_id}")
    return entity


def validate_operation(dna: VideoDNA, op: OperationSpec) -> None:
    """Reject operations that make no sense for the target element."""
    if op.op == EditOpType.INSTRUCTION and op.entity_id is None:
        if not (op.instruction or "").strip():
            raise OperationError("instruction text is required")
        return
    entity = _entity_or_raise(dna, op.entity_id)
    allowed = ALLOWED_OPS.get(entity.type, _DEFAULT_ALLOWED)
    if op.op not in allowed:
        raise OperationError(f"{op.op} is not allowed on a {entity.type}")
    if not entity.editable and op.op not in {EditOpType.CORRECT, EditOpType.KEEP}:
        raise OperationError(f"{entity.id} is not editable")
    if op.op == EditOpType.SET_ATTRIBUTE and not op.property:
        raise OperationError("SET_ATTRIBUTE requires a property")
    if op.op == EditOpType.CORRECT:
        if not op.property or (
            op.property not in CORRECTABLE_FIELDS and not op.property.startswith("attributes.")
        ):
            raise OperationError(f"cannot correct field {op.property!r}")
        if op.property == "importance" and op.new_value not in {i.value for i in Importance}:
            raise OperationError("invalid importance")
        if op.property == "type" and op.new_value not in {t.value for t in EntityType}:
            raise OperationError("invalid entity type")
    has_dict = isinstance(op.new_value, dict)
    if op.op == EditOpType.REPLACE and not (has_dict and op.new_value.get("label")):
        raise OperationError("REPLACE requires newValue.label")
    if op.op == EditOpType.APPLY_PRESET and not (has_dict and op.new_value.get("presetId")):
        raise OperationError("APPLY_PRESET requires newValue.presetId")
    if op.op == EditOpType.CHANGE_APPEARANCE and not (
        isinstance(op.new_value, dict) or (op.instruction or "").strip()
    ):
        raise OperationError("CHANGE_APPEARANCE requires attributes or an instruction")
    if op.op == EditOpType.ADD_ENTITY and not (has_dict and op.new_value.get("label")):
        raise OperationError("ADD_ENTITY requires newValue.label")
    if op.op == EditOpType.INSTRUCTION and not (op.instruction or "").strip():
        raise OperationError("instruction text is required")


def describe_entity(entity: Entity) -> str:
    """Human label derived from attributes, so 'Cabelo curto castanho' becomes
    'Cabelo cacheado castanho' after a style change."""
    attrs = entity.attributes
    if entity.type == EntityType.HAIR:
        parts = [
            "Cabelo",
            attrs.get("styleLabel") or attrs.get("style"),
            attrs.get("colorLabel") or attrs.get("color"),
        ]
        return " ".join(str(p) for p in parts if p)
    if entity.type == EntityType.WARDROBE and attrs.get("item"):
        item = str(attrs.get("itemLabel") or attrs["item"])
        color = attrs.get("colorLabel") or attrs.get("color")
        label = item[:1].upper() + item[1:]
        return f"{label} {color}" if color else label
    return entity.label


def _ensure_edit(entity: Entity) -> EntityEditState:
    if entity.edit is None:
        entity.edit = EntityEditState(
            original_label=entity.label,
            original_attributes=dict(entity.attributes),
        )
    return entity.edit


def _next_key(dna: VideoDNA, entity_type: EntityType) -> str:
    prefix = ENTITY_KEY_PREFIX[entity_type]
    pattern = re.compile(rf"^{prefix}_(\d+)$")
    numbers = [int(m.group(1)) for e in dna.entities if (m := pattern.match(e.id))]
    # Added elements start at 101 so they never collide with analysis ids that a
    # later re-analysis might produce.
    return f"{prefix}_{max([100, *numbers]) + 1:03d}"


def _apply_one(dna: VideoDNA, op: OperationSpec) -> None:
    if op.op == EditOpType.INSTRUCTION and op.entity_id is None:
        return  # project-level instruction: consumed by the planner, not the DNA
    entity = _entity_or_raise(dna, op.entity_id)
    edit = _ensure_edit(entity)
    edit.operation_ids.append(op.id)

    if op.op == EditOpType.CORRECT:
        _apply_correction(entity, op)
        return
    if op.op == EditOpType.KEEP:
        edit.locked = True
        return

    edit.modified = True
    if op.instruction:
        edit.instructions.append(op.instruction)

    match op.op:
        case EditOpType.SET_ATTRIBUTE:
            entity.attributes[op.property or "value"] = op.new_value
            if isinstance(op.new_value, str) and op.property in {"style", "color", "item"}:
                entity.attributes.pop(f"{op.property}Label", None)
            entity.label = describe_entity(entity)
        case EditOpType.CHANGE_APPEARANCE:
            if isinstance(op.new_value, dict):
                entity.attributes.update(op.new_value.get("attributes", op.new_value))
                if op.new_value.get("label"):
                    entity.label = str(op.new_value["label"])
                else:
                    entity.label = describe_entity(entity)
        case EditOpType.REPLACE:
            _apply_replace(dna, entity, op)
        case EditOpType.REMOVE:
            edit.removed = True
        case EditOpType.APPLY_PRESET:
            value = op.new_value
            entity.attributes.update(value.get("attributes", {}))
            entity.attributes["preset"] = value["presetId"]
            entity.label = str(value.get("label") or entity.label)
        case EditOpType.ADD_ENTITY:
            _apply_add(dna, entity, op)
        case EditOpType.INSTRUCTION:
            pass


def _apply_correction(entity: Entity, op: OperationSpec) -> None:
    prop = op.property or ""
    if prop.startswith("attributes."):
        entity.attributes[prop.removeprefix("attributes.")] = op.new_value
    elif prop == "label":
        entity.label = str(op.new_value)
    elif prop == "description":
        entity.description = str(op.new_value)
    elif prop == "subtype":
        entity.subtype = str(op.new_value)
    elif prop == "importance":
        entity.importance = Importance(op.new_value)
    elif prop == "type":
        entity.type = EntityType(op.new_value)
    # A human confirmed it: the uncertainty flag no longer applies.
    entity.needs_review = False
    entity.confidence = 1.0
    entity.sources = [*entity.sources, "user"]


def _apply_replace(dna: VideoDNA, entity: Entity, op: OperationSpec) -> None:
    value: dict[str, Any] = op.new_value
    entity.label = str(value["label"])
    # Doubts about what the *old* element was ("Copo / Taça?") no longer apply.
    entity.needs_review = False
    entity.alternatives = []
    if value.get("description"):
        entity.description = str(value["description"])
    if value.get("class"):
        entity.attributes["class"] = value["class"]
    entity.attributes.update(value.get("attributes", {}))
    entity.attributes["replacedFrom"] = entity.edit.original_label if entity.edit else None

    # Derived elements follow their source: shards of a glass become shards of a plate.
    new_class = OBJECT_CLASSES.get(str(value.get("class", "")))
    for derived in (e for e in dna.entities if e.derived_from == entity.id):
        d_edit = _ensure_edit(derived)
        d_edit.modified = True
        d_edit.operation_ids.append(op.id)
        noun = new_class.label_pt if new_class else entity.label.lower()
        if derived.attributes.get("class") == "fragments":
            derived.label = f"Fragmentos de {noun}"
        derived.attributes["derivedFromLabel"] = entity.label


def pin_added_entity_key(dna: VideoDNA, op: OperationSpec) -> OperationSpec:
    """Fix the id an ADD_ENTITY will create, at the moment it is created.

    Ids of added elements are sequential (OBJECT_101, OBJECT_102...). Recomputing
    them on every replay would renumber later additions when an earlier one is
    deleted, silently retargeting every edit made to them.
    """
    if op.op != EditOpType.ADD_ENTITY or not isinstance(op.new_value, dict):
        return op
    if op.new_value.get("entityKey"):
        return op
    entity_type = EntityType(op.new_value.get("type", EntityType.OBJECT.value))
    pinned = {**op.new_value, "entityKey": _next_key(dna, entity_type)}
    return op.model_copy(update={"new_value": pinned})


def added_entity_key(op: OperationSpec) -> str | None:
    if op.op != EditOpType.ADD_ENTITY or not isinstance(op.new_value, dict):
        return None
    return op.new_value.get("entityKey")


def _apply_add(dna: VideoDNA, parent: Entity, op: OperationSpec) -> None:
    value: dict[str, Any] = op.new_value
    entity_type = EntityType(value.get("type", EntityType.OBJECT.value))
    pinned = value.get("entityKey")
    new_id = pinned if pinned and dna.entity(pinned) is None else _next_key(dna, entity_type)
    placement = value.get("placement") or {}
    anchor_id = placement.get("relativeTo")
    anchor = dna.entity(anchor_id) if anchor_id else None
    shot_ids = dna.shots_for_entity(anchor.id if anchor else parent.id)
    appearances = []
    for sid in shot_ids:
        shot = dna.shot(sid)
        if shot:
            appearances.append(
                Appearance(shot_id=sid, start_time=shot.start_time, end_time=shot.end_time)
            )
    new_entity = Entity(
        id=new_id,
        type=entity_type,
        subtype=value.get("subtype"),
        label=str(value["label"]),
        description=value.get("description"),
        parent_id=parent.id,
        attributes=dict(value.get("attributes", {})),
        importance=Importance.DECORATIVE,
        confidence=1.0,
        appearances=appearances,
        sources=["user"],
        edit=EntityEditState(modified=True, added=True, operation_ids=[op.id]),
    )
    dna.entities.append(new_entity)
    if anchor:
        dna.relationships.append(
            Relationship(
                id=f"REL_ADD_{new_id}",
                subject_id=new_id,
                predicate=str(placement.get("predicate", "on_top_of")),
                object_id=anchor.id,
                shot_ids=shot_ids,
                confidence=1.0,
            )
        )


def apply_operations(original: VideoDNA, operations: list[OperationSpec]) -> VideoDNA:
    """Return the current DNA. `operations` must be the *active* operations."""
    current = original.model_copy(deep=True)
    for op in sorted(operations, key=lambda o: o.sequence):
        _apply_one(current, op)
    return current


def modified_entities(dna: VideoDNA) -> list[Entity]:
    return [e for e in dna.entities if e.edit and (e.edit.modified or e.edit.removed)]


def is_generative(op: OperationSpec) -> bool:
    return op.op in GENERATIVE_OPS


class EditHistory(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_serialization_defaults_required=True,
    )

    can_undo: bool
    can_redo: bool
    active_count: int
    undone_ids: list[str] = Field(default_factory=list)
