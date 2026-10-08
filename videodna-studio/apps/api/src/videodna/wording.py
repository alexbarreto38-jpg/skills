"""pt-BR wording for the messages people read: plan warnings, job progress,
version names. The owner reads "Cena 2", "R$ 12,00" and "00:03,5", never
"SHOT_002", "12.00 BRL", "3.46s" or an enum value.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from videodna.domain.enums import QualityMode, RenderKind, Strategy

# Same names as QUALITY_MODE in apps/web/src/lib/labels.ts, so the server's
# sentences match the buttons the user clicked.
QUALITY_LABEL: dict[QualityMode, str] = {
    QualityMode.ECONOMY: "Econômico",
    QualityMode.BALANCED: "Equilibrado",
    QualityMode.MAX: "Qualidade máxima",
}

RENDER_LABEL: dict[RenderKind, str] = {
    RenderKind.PREVIEW: "Prévia",
    RenderKind.FINAL: "Versão final",
}

STRATEGY_LABEL: dict[Strategy, str] = {
    Strategy.PASSTHROUGH: "copiada do original",
    Strategy.ATTRIBUTE_EDIT: "ajuste de cor",
    Strategy.LOCALIZED_EDIT: "mudança só no elemento",
    Strategy.BACKGROUND_REPLACEMENT: "troca do cenário",
    Strategy.SHOT_RECONSTRUCTION: "cena refeita",
    Strategy.FULL_REGENERATION: "cena criada do zero",
}


def scene(shot_key: str | None, index: int | None = None) -> str:
    """'Cena 2' from a shot's 0-based index, or from its key ('SHOT_002')."""
    if index is not None:
        return f"Cena {index + 1}"
    digits = (shot_key or "").rsplit("_", 1)[-1]
    return f"Cena {int(digits)}" if digits.isdigit() else "Uma cena"


def money(amount: float | Decimal, currency: str) -> str:
    """12.5, 'BRL' -> 'R$ 12,50'."""
    text = f"{Decimal(str(amount)):,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    return f"R$ {text}" if currency.upper() == "BRL" else f"{text} {currency}"


def clock(seconds: float) -> str:
    """3.46 -> '00:03,5' (the player's mm:ss, with a decimal comma)."""
    minutes, secs = divmod(round(max(0.0, seconds), 1), 60)
    return f"{int(minutes):02d}:{secs:04.1f}".replace(".", ",")


def duration(seconds: float) -> str:
    """2.1 -> '2,1 s'."""
    return f"{seconds:.1f}".replace(".", ",") + " s"


def file_size(n_bytes: int) -> str:
    """2 * 1024**3 -> '2 GB'; 350 * 1024**2 -> '350 MB'."""
    for unit, factor in (("GB", 1024**3), ("MB", 1024**2), ("KB", 1024)):
        if n_bytes >= factor:
            value = n_bytes / factor
            text = f"{value:.0f}" if value >= 10 or value.is_integer() else f"{value:.1f}"
            return f"{text.replace('.', ',')} {unit}"
    return f"{n_bytes} bytes"


def minutes(seconds: float) -> str:
    """600 -> '10 minutos'; 90 -> '1 min 30 s'; 45 -> '45 segundos'."""
    total = round(seconds)
    mins, secs = divmod(total, 60)
    if mins and secs:
        return f"{mins} min {secs} s"
    if mins:
        return count(mins, "minuto", "minutos")
    return count(secs, "segundo", "segundos")


def count(n: int, singular: str, plural: str) -> str:
    """count(1, 'cena', 'cenas') -> '1 cena'; real plurals instead of 'cena(s)'."""
    return f"{n} {singular if n == 1 else plural}"


def join_or(items: Iterable[str]) -> str:
    """['a', 'b', 'c'] -> 'a, b ou c'."""
    parts = [p for p in items if p]
    if len(parts) <= 1:
        return "".join(parts)
    return f"{', '.join(parts[:-1])} ou {parts[-1]}"
