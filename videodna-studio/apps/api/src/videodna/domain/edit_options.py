"""What can be edited on each kind of element, and how (backend-driven UI).

The inspector renders these categories; the Suggestion Engine fills each one
with 6–12 contextual options. Character editing is deliberately coarse (hair,
garments, accessories, whole look/character) — the edits that change what a
viewer actually notices (spec §9).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from videodna.domain.enums import EditOpType, EntityType
from videodna.domain.video_dna import Entity


@dataclass(frozen=True)
class EditCategory:
    id: str
    label: str
    op: EditOpType
    property: str | None = None
    display: Literal["cards", "swatches"] = "cards"
    description: str = ""


CATEGORIES: dict[str, EditCategory] = {
    c.id: c
    for c in [
        EditCategory("hair_style", "Estilo do cabelo", EditOpType.SET_ATTRIBUTE, "style"),
        EditCategory(
            "hair_color", "Cor do cabelo", EditOpType.CHANGE_APPEARANCE, "color", "swatches"
        ),
        EditCategory("wardrobe_upper", "Roupa superior", EditOpType.REPLACE),
        EditCategory("wardrobe_lower", "Roupa inferior", EditOpType.REPLACE),
        EditCategory("footwear", "Calçado", EditOpType.REPLACE),
        EditCategory(
            "wardrobe_color", "Cor da peça", EditOpType.CHANGE_APPEARANCE, "color", "swatches"
        ),
        EditCategory("accessory", "Acessório", EditOpType.REPLACE),
        EditCategory("character_look", "Look completo", EditOpType.CHANGE_APPEARANCE),
        EditCategory("character_replace", "Trocar personagem", EditOpType.REPLACE),
        EditCategory("environment_preset", "Estilo do ambiente", EditOpType.APPLY_PRESET),
        EditCategory("window_view", "Vista da janela", EditOpType.REPLACE),
        EditCategory("wall", "Parede", EditOpType.CHANGE_APPEARANCE, display="swatches"),
        EditCategory("floor", "Piso", EditOpType.CHANGE_APPEARANCE, display="swatches"),
        EditCategory("lighting", "Iluminação", EditOpType.CHANGE_APPEARANCE),
        EditCategory("object_replace", "Substituir por", EditOpType.REPLACE),
        EditCategory(
            "object_appearance",
            "Alterar aparência",
            EditOpType.CHANGE_APPEARANCE,
            "color",
            "swatches",
        ),
        EditCategory("furniture_style", "Trocar móvel", EditOpType.REPLACE),
    ]
}

_WARDROBE_BY_SLOT = {
    "upper": "wardrobe_upper",
    "lower": "wardrobe_lower",
    "footwear": "footwear",
    "full": "character_look",
}

_PART_CATEGORIES = {
    "wall": ["wall"],
    "ceiling": ["wall"],
    "floor": ["floor"],
    "window_view": ["window_view"],
    "window": ["object_appearance"],
    "door": ["object_appearance"],
}


def categories_for(entity: Entity) -> list[EditCategory]:
    ids: list[str]
    match entity.type:
        case EntityType.CHARACTER:
            ids = ["character_look", "character_replace"]
        case EntityType.HAIR:
            ids = ["hair_style", "hair_color"]
        case EntityType.WARDROBE:
            ids = [
                _WARDROBE_BY_SLOT.get(entity.subtype or "upper", "wardrobe_upper"),
                "wardrobe_color",
            ]
        case EntityType.ACCESSORY:
            ids = ["accessory", "object_appearance"]
        case EntityType.OBJECT:
            ids = (
                ["object_replace", "object_appearance"]
                if entity.replaceable
                else ["object_appearance"]
            )
        case EntityType.FURNITURE:
            ids = ["furniture_style", "object_appearance"]
        case EntityType.ENVIRONMENT:
            ids = ["environment_preset"]
        case EntityType.ENVIRONMENT_PART:
            ids = _PART_CATEGORIES.get(entity.subtype or "", ["object_appearance"])
        case EntityType.LIGHTING:
            ids = ["lighting"]
        case _:
            ids = []
    return [CATEGORIES[i] for i in ids]


def quick_actions_for(entity: Entity) -> list[str]:
    """Object-style actions shown as buttons: Manter / Substituir / Remover / Alterar."""
    if entity.type in {EntityType.OBJECT, EntityType.FURNITURE, EntityType.ACCESSORY}:
        actions = ["KEEP", "CHANGE_APPEARANCE", "REMOVE"]
        if entity.replaceable:
            actions.insert(1, "REPLACE")
        return actions
    if entity.type == EntityType.CHARACTER:
        return ["KEEP", "REPLACE", "CHANGE_APPEARANCE"]
    if entity.type == EntityType.ENVIRONMENT:
        return ["KEEP", "APPLY_PRESET", "ADD_ENTITY"]
    return ["KEEP", "CHANGE_APPEARANCE"]
