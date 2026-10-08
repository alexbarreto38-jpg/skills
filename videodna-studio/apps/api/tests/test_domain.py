"""Video DNA schema, edit operations and impact analysis (pure domain, no I/O)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from videodna.domain.enums import EditOpType, EntityType, ImpactLevel, Importance
from videodna.domain.impact import ChangeKind, analyze_operation, analyze_operations, classify
from videodna.domain.operations import (
    OperationError,
    OperationSpec,
    apply_operations,
    pin_added_entity_key,
    validate_operation,
)
from videodna.domain.settings import ProjectLocks
from videodna.domain.video_dna import (
    Action,
    AnalysisProvenance,
    Appearance,
    BBox,
    Entity,
    EntityAlternative,
    Narrative,
    Scene,
    Shot,
    TechnicalMetadata,
    VideoDNA,
)


def _shot(i: int, start: float, end: float) -> Shot:
    return Shot(
        id=f"SHOT_{i:03d}",
        index=i - 1,
        scene_id="SCENE_001",
        start_time=start,
        end_time=end,
        duration=end - start,
        start_frame=int(start * 25),
        end_frame=int(end * 25) - 1,
    )


def _entity(key: str, etype: EntityType, label: str, shots: list[Shot], **kw) -> Entity:
    return Entity(
        id=key,
        type=etype,
        label=label,
        confidence=kw.pop("confidence", 0.95),
        appearances=[
            Appearance(shot_id=s.id, start_time=s.start_time, end_time=s.end_time) for s in shots
        ],
        **kw,
    )


@pytest.fixture
def dna() -> VideoDNA:
    s1, s2, s3 = _shot(1, 0, 3), _shot(2, 3, 5), _shot(3, 5, 8)
    entities = [
        _entity(
            "ENVIRONMENT_001", EntityType.ENVIRONMENT, "Sala", [], importance=Importance.IMPORTANT
        ),
        _entity(
            "CHARACTER_001",
            EntityType.CHARACTER,
            "Menino",
            [s1, s2, s3],
            importance=Importance.ESSENTIAL,
        ),
        _entity(
            "HAIR_001",
            EntityType.HAIR,
            "Cabelo curto castanho",
            [],
            parent_id="CHARACTER_001",
            attributes={"style": "curto", "color": "castanho"},
        ),
        _entity(
            "OBJECT_001",
            EntityType.OBJECT,
            "Copo",
            [s1, s2],
            importance=Importance.ESSENTIAL,
            attributes={"class": "glass"},
        ),
        _entity(
            "OBJECT_005",
            EntityType.OBJECT,
            "Fragmentos de vidro",
            [s2, s3],
            derived_from="OBJECT_001",
            attributes={"class": "fragments"},
            replaceable=False,
        ),
        _entity(
            "FLOOR_001",
            EntityType.ENVIRONMENT_PART,
            "Piso",
            [],
            parent_id="ENVIRONMENT_001",
            subtype="floor",
        ),
    ]
    return VideoDNA(
        source_video_id="src",
        technical=TechnicalMetadata(
            duration_sec=8,
            width=1280,
            height=720,
            aspect_ratio="16:9",
            display_aspect_ratio=1.78,
            fps=25,
            frame_count=200,
        ),
        scenes=[
            Scene(
                id="SCENE_001",
                index=0,
                label="Sala",
                start_time=0,
                end_time=8,
                shot_ids=["SHOT_001", "SHOT_002", "SHOT_003"],
                environment_id="ENVIRONMENT_001",
            )
        ],
        shots=[s1, s2, s3],
        entities=entities,
        actions=[
            Action(
                id="ACTION_001",
                verb="hold",
                label="segura",
                actor_id="CHARACTER_001",
                target_ids=["OBJECT_001"],
                start_time=0,
                end_time=3,
                shot_ids=["SHOT_001"],
                essential=True,
                confidence=0.9,
            ),
            Action(
                id="ACTION_002",
                verb="fall",
                label="cai",
                actor_id="OBJECT_001",
                target_ids=["FLOOR_001"],
                start_time=3,
                end_time=4,
                shot_ids=["SHOT_002"],
                essential=True,
                confidence=0.9,
            ),
            Action(
                id="ACTION_003",
                verb="break",
                label="quebra",
                actor_id="OBJECT_001",
                result_entity_ids=["OBJECT_005"],
                start_time=4,
                end_time=5,
                shot_ids=["SHOT_002"],
                essential=True,
                confidence=0.9,
            ),
        ],
        narrative=Narrative(summary="x", roles={"OBJETO_A": "OBJECT_001"}, confidence=0.9),
        analysis=AnalysisProvenance(
            pipeline_version="t", mock=True, created_at="now", low_confidence_threshold=0.6
        ),
    )


def op(n: int, **kw) -> OperationSpec:
    return OperationSpec(id=f"op{n}", sequence=n, **kw)


def test_dna_rejects_dangling_references(dna):
    data = dna.model_dump(mode="json", by_alias=True)
    data["actions"][0]["targetIds"] = ["OBJECT_999"]
    with pytest.raises(ValidationError, match="unknown entity OBJECT_999"):
        VideoDNA.model_validate(data)


def test_dna_round_trips_as_camel_case_json(dna):
    data = dna.model_dump(mode="json", by_alias=True)
    assert "sourceVideoId" in data and "durationSec" in data["technical"]
    assert VideoDNA.model_validate(data) == dna


def test_bbox_must_stay_inside_frame():
    with pytest.raises(ValidationError):
        BBox(x=0.9, y=0.1, w=0.3, h=0.1)


def test_shot_end_after_start():
    with pytest.raises(ValidationError):
        _shot(1, 3, 3)


def test_original_is_never_mutated(dna):
    before = dna.model_dump()
    current = apply_operations(
        dna,
        [
            op(
                1,
                entity_id="HAIR_001",
                op=EditOpType.SET_ATTRIBUTE,
                property="style",
                new_value="cacheado",
            )
        ],
    )
    assert dna.model_dump() == before
    hair = current.entity("HAIR_001")
    assert hair.attributes["style"] == "cacheado"
    assert hair.label == "Cabelo cacheado castanho"
    assert hair.edit.original_label == "Cabelo curto castanho"


def test_replace_propagates_to_derived_entities(dna):
    current = apply_operations(
        dna,
        [
            op(
                1,
                entity_id="OBJECT_001",
                op=EditOpType.REPLACE,
                new_value={"label": "Prato", "class": "plate"},
            )
        ],
    )
    assert current.entity("OBJECT_001").label == "Prato"
    shards = current.entity("OBJECT_005")
    assert shards.label == "Fragmentos de prato"
    assert shards.edit.modified is True


def test_last_operation_wins_and_order_is_by_sequence(dna):
    ops = [
        op(
            2, entity_id="HAIR_001", op=EditOpType.SET_ATTRIBUTE, property="style", new_value="afro"
        ),
        op(
            1, entity_id="HAIR_001", op=EditOpType.SET_ATTRIBUTE, property="style", new_value="liso"
        ),
    ]
    assert apply_operations(dna, ops).entity("HAIR_001").attributes["style"] == "afro"


def test_add_entity_creates_new_element_with_placement(dna):
    current = apply_operations(
        dna,
        [
            op(
                1,
                entity_id="ENVIRONMENT_001",
                op=EditOpType.ADD_ENTITY,
                new_value={
                    "label": "Garrafa de água",
                    "placement": {"relativeTo": "OBJECT_001", "predicate": "next_to"},
                },
            )
        ],
    )
    added = current.entity("OBJECT_101")
    assert added is not None and added.edit.added is True
    assert {a.shot_id for a in added.appearances} == {"SHOT_001", "SHOT_002"}


def test_added_entity_keys_survive_removing_an_earlier_addition(dna):
    def add(n: int, label: str, current: VideoDNA) -> OperationSpec:
        spec = op(
            n, entity_id="ENVIRONMENT_001", op=EditOpType.ADD_ENTITY, new_value={"label": label}
        )
        return pin_added_entity_key(current, spec)

    bottle = add(1, "Garrafa", dna)
    vase = add(2, "Vaso", apply_operations(dna, [bottle]))
    paint_vase = op(
        3, entity_id="OBJECT_102", op=EditOpType.SET_ATTRIBUTE, property="color", new_value="azul"
    )
    assert vase.new_value["entityKey"] == "OBJECT_102"

    # Dropping the bottle must not renumber the vase onto OBJECT_101.
    current = apply_operations(dna, [vase, paint_vase])
    assert current.entity("OBJECT_101") is None
    assert current.entity("OBJECT_102").label == "Vaso"
    assert current.entity("OBJECT_102").attributes["color"] == "azul"


def test_correction_clears_uncertainty(dna):
    dna.entities[3].needs_review = True
    current = apply_operations(
        dna,
        [op(1, entity_id="OBJECT_001", op=EditOpType.CORRECT, property="label", new_value="Taça")],
    )
    glass = current.entity("OBJECT_001")
    assert glass.label == "Taça" and glass.needs_review is False and glass.confidence == 1.0
    assert glass.edit.modified is False  # metadata only: nothing to regenerate


@pytest.mark.parametrize(
    "spec,error",
    [
        (
            dict(entity_id="HAIR_001", op=EditOpType.APPLY_PRESET, new_value={"presetId": "x"}),
            "not allowed",
        ),
        (dict(entity_id="NOPE", op=EditOpType.REMOVE), "unknown entity"),
        (dict(entity_id="OBJECT_001", op=EditOpType.REPLACE, new_value={}), "label"),
        (
            dict(entity_id="OBJECT_001", op=EditOpType.CORRECT, property="attributes", new_value=1),
            "cannot correct",
        ),
        (dict(entity_id=None, op=EditOpType.INSTRUCTION, instruction="  "), "instruction"),
    ],
)
def test_invalid_operations_are_rejected(dna, spec, error):
    with pytest.raises(OperationError, match=error):
        validate_operation(dna, op(1, **spec))


def test_impact_hair_change_is_low(dna):
    spec = op(
        1, entity_id="HAIR_001", op=EditOpType.SET_ATTRIBUTE, property="style", new_value="afro"
    )
    report = analyze_operations(dna, [spec], ProjectLocks())[0]
    assert report.change_kind == ChangeKind.LOCAL_APPEARANCE
    assert report.level == ImpactLevel.LOW
    assert report.affected_shot_ids == [
        "SHOT_001",
        "SHOT_002",
        "SHOT_003",
    ]  # inherited from the boy


def test_impact_glass_to_plate_is_high_with_physical_dependencies(dna):
    spec = op(
        1,
        entity_id="OBJECT_001",
        op=EditOpType.REPLACE,
        new_value={"label": "Prato", "class": "plate"},
    )
    report = analyze_operations(dna, [spec], ProjectLocks())[0]
    assert report.level == ImpactLevel.HIGH
    types = {d.type.value for d in report.dependencies}
    assert {
        "HAND_INTERACTION",
        "PHYSICS_MOTION",
        "DESTRUCTION_FX",
        "DERIVED_ENTITY",
        "STORY_ROLE",
    } <= types
    assert "OBJECT_005" in report.affected_entity_ids and "SHOT_003" in report.affected_shot_ids
    assert not report.blocking


def test_story_lock_blocks_removing_an_essential_object(dna):
    spec = op(1, entity_id="OBJECT_001", op=EditOpType.REMOVE)
    locked = analyze_operations(dna, [spec], ProjectLocks(story=True))[0]
    assert locked.blocking
    unlocked = analyze_operations(dna, [spec], ProjectLocks(story=False))[0]
    assert not unlocked.blocking and any(w.code == "STORY_CHANGE" for w in unlocked.warnings)


def test_environment_change_is_high_and_lists_children(dna):
    spec = op(
        1, entity_id="ENVIRONMENT_001", op=EditOpType.APPLY_PRESET, new_value={"presetId": "loft"}
    )
    report = analyze_operations(dna, [spec], ProjectLocks())[0]
    assert report.change_kind == ChangeKind.ENVIRONMENT_FULL and report.level == ImpactLevel.HIGH
    assert "FLOOR_001" in report.affected_entity_ids


def test_classification_of_metadata_ops(dna):
    assert (
        classify(op(1, entity_id="OBJECT_001", op=EditOpType.KEEP), dna.entity("OBJECT_001"))
        == ChangeKind.METADATA
    )
    current = apply_operations(dna, [])
    report = analyze_operation(
        dna, current, op(1, entity_id="OBJECT_001", op=EditOpType.KEEP), ProjectLocks()
    )
    assert report.level == ImpactLevel.NONE


def test_replacing_an_uncertain_element_resolves_the_doubt(dna):
    glass = dna.entity("OBJECT_001")
    glass.needs_review = True
    glass.alternatives = [EntityAlternative(label="Taça", confidence=0.7, source="detector")]
    replace = op(1, entity_id="OBJECT_001", op=EditOpType.REPLACE, new_value={"label": "Prato"})
    current = apply_operations(dna, [replace])
    assert current.entity("OBJECT_001").needs_review is False
    assert current.entity("OBJECT_001").alternatives == []
    (report,) = analyze_operations(dna, [replace], ProjectLocks())
    assert not [w for w in report.warnings if w.code == "LOW_CONFIDENCE"]

    recolor = op(
        1, entity_id="OBJECT_001", op=EditOpType.SET_ATTRIBUTE, property="color", new_value="azul"
    )
    (report,) = analyze_operations(dna, [recolor], ProjectLocks())
    assert [w.code for w in report.warnings] == ["LOW_CONFIDENCE"]
