"""Controlled vocabulary for actions, relationships and object physics.

Providers return free text; the DNA assembler normalizes verbs and predicates to
these canonical forms so the impact analyzer can reason about dependencies
("if the glass becomes a plate, the hand must still hold it, it must still fall
and it must still break").
"""

from __future__ import annotations

from dataclasses import dataclass, field

from videodna.domain.enums import DependencyType


@dataclass(frozen=True)
class VerbSpec:
    verb: str
    label_pt: str
    # Dependencies a *target/actor substitution* inherits from this action.
    target_dependencies: tuple[DependencyType, ...] = ()
    actor_dependencies: tuple[DependencyType, ...] = ()
    # Physical properties an object must have to keep performing the action.
    requires_properties: tuple[str, ...] = ()
    physics: tuple[str, ...] = ()
    synonyms: tuple[str, ...] = field(default_factory=tuple)


VERBS: dict[str, VerbSpec] = {
    spec.verb: spec
    for spec in [
        VerbSpec(
            "hold",
            "segura",
            target_dependencies=(DependencyType.HAND_INTERACTION,),
            requires_properties=("holdable",),
            physics=("contact",),
            synonyms=("segurar", "segura", "pega", "pegar", "grab", "holds"),
        ),
        VerbSpec(
            "fall",
            "cai",
            actor_dependencies=(DependencyType.PHYSICS_MOTION,),
            physics=("gravity", "motion"),
            synonyms=("cair", "cai", "drop", "drops", "falls"),
        ),
        VerbSpec(
            "break",
            "quebra",
            actor_dependencies=(DependencyType.DESTRUCTION_FX, DependencyType.AUDIO_SFX),
            requires_properties=("breakable",),
            physics=("destruction", "fragments"),
            synonyms=("quebrar", "quebra", "shatter", "breaks", "estilhaça"),
        ),
        VerbSpec(
            "throw",
            "arremessa",
            target_dependencies=(DependencyType.HAND_INTERACTION, DependencyType.PHYSICS_MOTION),
            requires_properties=("holdable",),
            physics=("motion", "gravity"),
            synonyms=("jogar", "joga", "arremessar", "throws"),
        ),
        VerbSpec(
            "enter",
            "entra",
            actor_dependencies=(DependencyType.CONTINUITY,),
            physics=("locomotion",),
            synonyms=("entrar", "entra", "enters", "chega", "chegar"),
        ),
        VerbSpec(
            "walk",
            "caminha",
            physics=("locomotion",),
            synonyms=("andar", "anda", "caminhar", "walks"),
        ),
        VerbSpec(
            "sit",
            "senta",
            target_dependencies=(DependencyType.CONTACT_SURFACE,),
            requires_properties=("sittable",),
            physics=("contact",),
            synonyms=("sentar", "senta", "sits"),
        ),
        VerbSpec(
            "look_at",
            "olha para",
            target_dependencies=(DependencyType.GAZE_TARGET,),
            synonyms=("olhar", "olha", "looks at", "percebe", "notices"),
        ),
        VerbSpec(
            "react",
            "reage",
            target_dependencies=(DependencyType.GAZE_TARGET,),
            synonyms=("reagir", "reage", "briga", "reacts", "scolds"),
        ),
        VerbSpec(
            "speak",
            "fala",
            actor_dependencies=(DependencyType.AUDIO_SFX,),
            synonyms=("falar", "fala", "speaks", "diz"),
        ),
        VerbSpec(
            "place",
            "coloca",
            target_dependencies=(DependencyType.HAND_INTERACTION, DependencyType.CONTACT_SURFACE),
            requires_properties=("holdable",),
            physics=("contact",),
            synonyms=("colocar", "coloca", "places", "puts"),
        ),
    ]
}


def normalize_verb(raw: str) -> str:
    value = raw.strip().lower()
    if value in VERBS:
        return value
    for spec in VERBS.values():
        if value in spec.synonyms:
            return spec.verb
    return value


PREDICATES: dict[str, str] = {
    "holds": "segura",
    "in_front_of": "está_em_frente_de",
    "behind": "atrás_de",
    "on_top_of": "em_cima_de",
    "looks_at": "olha_para",
    "falls_onto": "cai_em",
    "enters": "entra_em",
    "next_to": "ao_lado_de",
    "inside": "dentro_de",
    "wears": "veste",
}

# Predicates that imply a physical contact the generator must preserve.
CONTACT_PREDICATES = {"holds", "on_top_of", "falls_onto", "wears", "inside"}
OCCLUSION_PREDICATES = {"behind", "in_front_of"}
GAZE_PREDICATES = {"looks_at"}


@dataclass(frozen=True)
class ObjectClass:
    key: str
    label_pt: str
    properties: frozenset[str]
    family: str


def _oc(key: str, label: str, family: str, *props: str) -> ObjectClass:
    return ObjectClass(key, label, frozenset(props), family)


# Object classes known to the mock catalog and to the impact analyzer. Real
# providers return open-vocabulary labels; unknown classes simply have no
# property guarantees, which the analyzer reports as "compatibility unknown".
OBJECT_CLASSES: dict[str, ObjectClass] = {
    oc.key: oc
    for oc in [
        _oc("glass", "copo", "tableware", "holdable", "breakable", "container"),
        _oc("wine_glass", "taça", "tableware", "holdable", "breakable", "container"),
        _oc("plate", "prato", "tableware", "holdable", "breakable"),
        _oc("mug", "caneca", "tableware", "holdable", "breakable", "container"),
        _oc("bowl", "tigela", "tableware", "holdable", "breakable", "container"),
        _oc("bottle", "garrafa", "tableware", "holdable", "breakable", "container"),
        _oc("plastic_cup", "copo de plástico", "tableware", "holdable", "container"),
        _oc("vase", "vaso", "decoration", "holdable", "breakable"),
        _oc("phone", "telefone celular", "electronics", "holdable"),
        _oc("tablet", "tablet", "electronics", "holdable"),
        _oc("remote", "controle remoto", "electronics", "holdable"),
        _oc("book", "livro", "stationery", "holdable"),
        _oc("pillow", "almofada", "textile", "holdable"),
        _oc("plant", "planta", "decoration"),
        _oc("box", "caixa", "storage", "holdable"),
        _oc("pouf", "pufe", "furniture", "sittable"),
        _oc("sofa", "sofá", "furniture", "sittable"),
        _oc("armchair", "poltrona", "furniture", "sittable"),
        _oc("table", "mesa", "furniture", "surface"),
        _oc("chair", "cadeira", "furniture", "sittable"),
        _oc("cap", "boné", "wearable", "holdable"),
        _oc("watch", "relógio", "wearable"),
        _oc("fragments", "fragmentos", "debris"),
    ]
}


def object_class(key: str | None) -> ObjectClass | None:
    if not key:
        return None
    return OBJECT_CLASSES.get(key)
