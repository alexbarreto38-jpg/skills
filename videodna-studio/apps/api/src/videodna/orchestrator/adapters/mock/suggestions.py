"""Mock Suggestion provider: curated catalog + context rules.

Context rules (what a real LLM provider must also respect):
* scene temperature/setting — no heavy coats at the beach, no swimwear in snow;
* the character — no adult formalwear suggestions for a child by default;
* physics — a replacement for an object that *breaks* in the story should be
  breakable, one that is *held* should be holdable (incompatible items are
  ranked last and tagged, not hidden);
* never suggest the current value again.
"""

from __future__ import annotations

from typing import Any

from videodna.domain.edit_options import CATEGORIES
from videodna.domain.vocabulary import OBJECT_CLASSES, VERBS
from videodna.orchestrator.adapters.mock import catalog
from videodna.orchestrator.adapters.mock.base import MockMixin
from videodna.orchestrator.interfaces import (
    ProviderUsageInfo,
    SuggestionCandidate,
    SuggestionContext,
    SuggestionProvider,
    SuggestionRequest,
    SuggestionResult,
)

_CONFLICTS = {
    "beach": {"cold", "formal"},
    "warm": {"cold"},
    "cold": {"beach"},
    "child": {"adult", "senior"},
}


def context_tags(ctx: SuggestionContext) -> set[str]:
    tags: set[str] = set(ctx.tags)
    for source in (ctx.environment, ctx.parent, ctx.entity):
        if source is not None:
            tags.update(str(t) for t in source.attributes.get("tags", []) or [])
    if ctx.character is not None:
        group = ctx.character.attributes.get("ageGroup")
        if group:
            tags.add(str(group))
    if {"beach", "tropical"} & tags:
        tags.add("warm")
    return tags


def _score(item: dict[str, Any], tags: set[str]) -> float | None:
    item_tags = set(item.get("tags", []))
    for ctx_tag, banned in _CONFLICTS.items():
        if ctx_tag in tags and item_tags & banned:
            return None
    score = 0.5 + 0.12 * len(item_tags & tags)
    if "formal" in item_tags and ({"home", "casual"} & tags):
        score -= 0.15
    return round(min(score, 0.99), 3)


class MockSuggestionProvider(MockMixin, SuggestionProvider):
    def suggest(self, request: SuggestionRequest) -> SuggestionResult:
        self.failures.check()
        category = CATEGORIES[request.category]
        ctx = request.context
        tags = context_tags(ctx)
        items = self._items(request.category, ctx)
        current = self._current_value(request.category, ctx)
        excluded = {label.lower() for label in request.exclude_labels}

        scored: list[tuple[float, dict[str, Any]]] = []
        for item in items:
            if self._same(item, current):
                continue
            score = _score(item, tags)
            if score is None:
                continue
            item = dict(item)
            if request.category in {"object_replace", "furniture_style"}:
                score, note = self._physics(item, ctx, score)
                if note:
                    item["tags"] = [*item.get("tags", []), note]
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        ranked = [pair for pair in scored if pair[1]["label"].lower() not in excluded]

        # Earlier pages arrive as `exclude_labels`, so each page is simply the best
        # remaining items; beyond the catalog, variants keep "Gerar mais opções" useful.
        page = ranked[: request.count]
        if len(page) < request.count:
            page += self._variants(
                request, scored, request.count - len(page), request.page * request.count, excluded
            )

        suggestions = [
            self._candidate(request.category, category.op, item, score, ctx) for score, item in page
        ]
        return SuggestionResult(
            suggestions=suggestions,
            usage=ProviderUsageInfo(
                model=self.descriptor.default_model(), tokens=420 + 60 * len(suggestions)
            ),
        )

    # --- catalog selection -------------------------------------------------------

    def _items(self, category: str, ctx: SuggestionContext) -> list[dict[str, Any]]:
        entity = ctx.entity
        match category:
            case "hair_style":
                return catalog.HAIR_STYLES
            case "hair_color":
                return catalog.HAIR_COLORS
            case "wardrobe_upper":
                return catalog.WARDROBE_UPPER
            case "wardrobe_lower":
                return catalog.WARDROBE_LOWER
            case "footwear":
                return catalog.FOOTWEAR
            case "wardrobe_color" | "object_appearance":
                return catalog.COLORS
            case "accessory":
                return catalog.ACCESSORIES
            case "character_look":
                return catalog.CHARACTER_LOOKS
            case "character_replace":
                return catalog.CHARACTER_REPLACEMENTS
            case "environment_preset":
                key = str(entity.attributes.get("category", "default"))
                return catalog.ENVIRONMENT_PRESETS.get(key, catalog.ENVIRONMENT_PRESETS["default"])
            case "window_view":
                return catalog.WINDOW_VIEWS
            case "wall":
                return catalog.WALLS
            case "floor":
                return catalog.FLOORS
            case "lighting":
                return catalog.LIGHTING
            case "object_replace" | "furniture_style":
                cls = OBJECT_CLASSES.get(str(entity.attributes.get("class", "")))
                family = cls.family if cls else "default"
                primary = catalog.OBJECT_REPLACEMENTS.get(family, [])
                fallback = catalog.OBJECT_REPLACEMENTS["default"]
                current_class = cls.key if cls else None
                seen: set[str] = set()
                out = []
                for item in [*primary, *fallback]:
                    if item["class"] == current_class or item["label"] in seen:
                        continue
                    seen.add(item["label"])
                    out.append(item)
                return out
        return []

    @staticmethod
    def _current_value(category: str, ctx: SuggestionContext) -> Any:
        attrs = ctx.entity.attributes
        if category == "hair_style":
            return attrs.get("style")
        if category in {"hair_color", "wardrobe_color", "object_appearance"}:
            return attrs.get("color")
        if category.startswith("wardrobe") or category == "footwear":
            return ctx.entity.label
        if category == "environment_preset":
            return attrs.get("preset")
        if category == "window_view":
            return attrs.get("view")
        return ctx.entity.label

    @staticmethod
    def _same(item: dict[str, Any], current: Any) -> bool:
        if current is None:
            return False
        current_text = str(current).lower()
        value = item.get("value")
        candidates = {item["label"].lower()}
        if isinstance(value, str):
            candidates.add(value.lower())
        elif isinstance(value, dict):
            candidates.update(
                str(v).lower()
                for v in (
                    value.get("presetId"),
                    value.get("color"),
                    value.get("label"),
                    (value.get("attributes") or {}).get("view"),
                    (value.get("attributes") or {}).get("color"),
                )
                if v
            )
        return current_text in candidates

    @staticmethod
    def _physics(
        item: dict[str, Any], ctx: SuggestionContext, score: float
    ) -> tuple[float, str | None]:
        cls = OBJECT_CLASSES.get(item.get("class", ""))
        for verb in ctx.actions:
            spec = VERBS.get(verb)
            if spec is None or not spec.requires_properties:
                continue
            if cls is None:
                return score - 0.1, f"física desconhecida para '{spec.label_pt}'"
            missing = [p for p in spec.requires_properties if p not in cls.properties]
            if missing:
                return score - 0.35, f"incompatível com '{spec.label_pt}'"
        if cls is not None:
            score += 0.1  # known physics → safer generation
        return round(min(score, 0.99), 3), None

    def _variants(
        self,
        request: SuggestionRequest,
        ranked: list[tuple[float, dict[str, Any]]],
        needed: int,
        offset: int,
        excluded: set[str],
    ) -> list[tuple[float, dict[str, Any]]]:
        """'Gerar mais opções' beyond the catalog: color variants of the best items."""
        if not ranked:
            return []
        out: list[tuple[float, dict[str, Any]]] = []
        colorable = request.category in {
            "wardrobe_upper",
            "wardrobe_lower",
            "footwear",
            "accessory",
            "object_replace",
            "furniture_style",
        }
        i = offset
        while len(out) < needed and i < offset + needed * 6:
            score, base = ranked[i % len(ranked)]
            color = catalog.COLORS[(i // len(ranked)) % len(catalog.COLORS)]
            i += 1
            if not colorable:
                continue
            item = dict(base)
            noun = base["label"].split(" ")[0]
            item["label"] = f"{noun} {color['label'].lower()}"
            value = dict(base["value"]) if isinstance(base.get("value"), dict) else {}
            attributes = dict(value.get("attributes", {}))
            attributes.update(color["value"])
            value["attributes"] = attributes
            value["label"] = item["label"]
            item["value"] = value
            item["hex"] = color["hex"]
            if item["label"].lower() in excluded or any(
                existing[1]["label"] == item["label"] for existing in [*ranked, *out]
            ):
                continue
            out.append((round(score * 0.9, 3), item))
        return out

    # --- output -------------------------------------------------------------------

    @staticmethod
    def _candidate(
        category: str, op, item: dict[str, Any], score: float, ctx: SuggestionContext
    ) -> SuggestionCandidate:
        cat = CATEGORIES[category]
        value = item.get("value")
        prop = cat.property
        hint: dict[str, Any] = {"label": item["label"]}
        current_hex = ctx.entity.attributes.get("colorHex")
        match category:
            case "hair_style":
                hint.update(kind="hair", shape=item.get("shape"), colors=[current_hex or "#5b3a22"])
            case "hair_color" | "wardrobe_color" | "object_appearance":
                value = {"attributes": dict(item["value"])}
                hint.update(
                    kind="swatch", colors=[item["hex"]], shape=ctx.entity.attributes.get("item")
                )
            case "wardrobe_upper" | "wardrobe_lower" | "footwear":
                hint.update(kind="garment", shape=item.get("shape"), colors=[item.get("hex")])
            case "accessory" | "object_replace" | "furniture_style":
                hint.update(
                    kind="object", shape=item.get("class"), colors=[item.get("hex") or "#8a8f98"]
                )
            case "character_look" | "environment_preset" | "lighting":
                hint.update(
                    kind={
                        "character_look": "look",
                        "environment_preset": "room",
                        "lighting": "lighting",
                    }[category],
                    colors=item.get("palette", []),
                )
            case "character_replace":
                hint.update(
                    kind="character", shape=(item["value"]["attributes"] or {}).get("ageGroup")
                )
            case "window_view":
                hint.update(
                    kind="window_view", shape=item.get("view"), colors=item.get("palette", [])
                )
            case "wall" | "floor":
                hint.update(kind="room_part", shape=category, colors=[item.get("hex")])
        return SuggestionCandidate(
            label=item["label"],
            description=item.get("description"),
            op=op,
            property=prop if category == "hair_style" else None,
            value=value,
            tags=[t for t in item.get("tags", []) if t],
            score=score,
            preview_hint=hint,
        )
