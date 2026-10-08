"""Mock image generator.

* `generate_image` draws an illustrative SVG card for a suggestion (hair shape,
  garment silhouette, room palette, window view...). Free and instant, so the
  UI always has a visual card — real providers would render actual previews.
* `edit_image` produces a *frame preview*: the real keyframe with the edited
  region tinted and labelled (FFmpeg), which is the cheap "preview before you
  pay for video" step of spec §20.
"""

from __future__ import annotations

import colorsys
from xml.sax.saxutils import escape

from videodna.media.ffmpeg import escape_drawtext, escape_filter_path, find_font_file, run_ffmpeg
from videodna.media.transcode import probe_video_size
from videodna.orchestrator.adapters.mock.base import MockMixin
from videodna.orchestrator.adapters.mock.story import stable_noise
from videodna.orchestrator.interfaces import (
    ImageEditRequest,
    ImageGenerationRequest,
    ImageGeneratorProvider,
    ImageResult,
    ProviderUsageInfo,
)


def _shade(hex_color: str, factor: float) -> str:
    hex_color = (hex_color or "#888888").lstrip("#")
    if len(hex_color) != 6:
        hex_color = "888888"
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    h, lum, s = colorsys.rgb_to_hls(r, g, b)
    lum = max(0.0, min(1.0, lum * factor))
    r, g, b = colorsys.hls_to_rgb(h, lum, s)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def _hash_color(text: str) -> str:
    h = stable_noise(text)
    r, g, b = colorsys.hls_to_rgb(h, 0.55, 0.55)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


_HAIR_PATHS = {
    "short": "M70 92 Q70 50 128 46 Q186 50 186 92 Q160 70 128 72 Q96 70 70 92Z",
    "buzz": "M76 90 Q76 58 128 56 Q180 58 180 90 Q128 76 76 90Z",
    "medium": "M64 120 Q60 50 128 44 Q196 50 192 120 L176 120 Q172 78 128 74 Q84 78 80 120Z",
    "long": "M60 190 Q50 50 128 42 Q206 50 196 190 L172 190 Q176 84 128 76 Q80 84 84 190Z",
    "curly": "M62 100 a16 16 0 0 1 20-34 a18 18 0 0 1 30-18 a18 18 0 0 1 32 0 a18 18 0 0 1 30 18 a16 16 0 0 1 20 34 Q128 70 62 100Z",
    "wavy": "M62 150 Q52 60 128 44 Q204 60 194 150 Q184 130 178 150 Q170 90 128 76 Q86 90 78 150 Q72 130 62 150Z",
    "straight": "M64 170 L64 80 Q66 46 128 44 Q190 46 192 80 L192 170 L176 170 L176 86 Q128 70 80 86 L80 170Z",
    "side_part": "M70 94 Q66 48 120 44 Q190 44 188 94 Q170 64 112 68 Q90 72 70 94Z",
    "afro": "M128 20 a70 64 0 1 1 -0.1 0Z",
    "braids": "M70 96 Q70 46 128 44 Q186 46 186 96 L178 196 L166 196 L170 96 Q128 72 86 96 L90 196 L78 196Z",
    "bun": "M128 18 a20 20 0 1 1 -0.1 0Z M70 94 Q70 50 128 48 Q186 50 186 94 Q128 74 70 94Z",
    "mohawk": "M116 24 L140 24 L146 84 L110 84Z",
    "ponytail": "M70 94 Q70 48 128 46 Q186 48 186 94 Q128 74 70 94Z M180 70 Q214 110 196 170 L184 168 Q196 120 170 84Z",
    "bangs": "M66 110 Q62 46 128 44 Q194 46 190 110 L176 110 L174 88 L82 88 L80 110Z",
}


def _hair_svg(shape: str | None, color: str) -> str:
    path = _HAIR_PATHS.get(shape or "short", _HAIR_PATHS["short"])
    return (
        '<ellipse cx="128" cy="112" rx="50" ry="60" fill="#e9c4a6"/>'
        '<rect x="104" y="160" width="48" height="40" fill="#e9c4a6"/>'
        '<path d="M58 256 Q60 196 128 196 Q196 196 198 256Z" fill="#5d6d7e"/>'
        f'<path d="{path}" fill="{color}" stroke="{_shade(color, 0.7)}" stroke-width="2"/>'
    )


def _garment_svg(shape: str | None, color: str) -> str:
    dark = _shade(color, 0.75)
    shape = (shape or "").lower()
    if any(k in shape for k in ("calça", "bermuda", "short", "saia", "legging")):
        short = any(k in shape for k in ("bermuda", "short", "saia"))
        h = 120 if short else 180
        return (
            f'<path d="M78 40 L178 40 L184 {40 + h} L136 {40 + h} L128 90 L120 {40 + h} '
            f'L72 {40 + h}Z" fill="{color}" stroke="{dark}" stroke-width="3"/>'
        )
    if any(
        k in shape
        for k in ("tênis", "sapato", "bota", "chinelo", "sandália", "pantufa", "descalço")
    ):
        return (
            f'<path d="M48 170 Q60 120 104 128 L150 150 Q206 156 210 186 L48 190Z" fill="{color}" '
            f'stroke="{dark}" stroke-width="3"/><rect x="48" y="186" width="162" height="12" rx="6" fill="{dark}"/>'
        )
    long_sleeve = any(
        k in shape for k in ("moletom", "jaqueta", "suéter", "terno", "cardigã", "camisa social")
    )
    sleeve = (
        "M78 52 L28 110 L52 132 L84 100" if not long_sleeve else "M78 52 L22 178 L50 186 L86 100"
    )
    sleeve_r = (
        "M178 52 L228 110 L204 132 L172 100"
        if not long_sleeve
        else "M178 52 L234 178 L206 186 L170 100"
    )
    return (
        f'<path d="{sleeve}" fill="{color}" stroke="{dark}" stroke-width="3"/>'
        f'<path d="{sleeve_r}" fill="{color}" stroke="{dark}" stroke-width="3"/>'
        f'<path d="M78 52 Q104 40 110 38 Q128 58 146 38 Q152 40 178 52 L172 210 L84 210Z" '
        f'fill="{color}" stroke="{dark}" stroke-width="3"/>'
    )


def _room_svg(colors: list[str]) -> str:
    wall, floor, accent = (colors + ["#e9e7e2", "#c9b79c", "#2f3a45"])[:3]
    return (
        f'<rect x="0" y="0" width="256" height="170" fill="{wall}"/>'
        f'<rect x="0" y="170" width="256" height="86" fill="{floor}"/>'
        f'<rect x="150" y="34" width="70" height="80" fill="#bfe3f5" stroke="{_shade(wall, 0.7)}" stroke-width="5"/>'
        f'<rect x="26" y="120" width="104" height="54" rx="10" fill="{accent}"/>'
        f'<rect x="20" y="104" width="24" height="70" rx="8" fill="{_shade(accent, 0.8)}"/>'
        f'<rect x="112" y="104" width="24" height="70" rx="8" fill="{_shade(accent, 0.8)}"/>'
        f'<rect x="150" y="186" width="80" height="12" rx="3" fill="{_shade(floor, 0.6)}"/>'
    )


def _view_svg(shape: str | None, colors: list[str]) -> str:
    sky, ground = (colors + ["#a7c7e7", "#5f7d6a"])[:2]
    scene = f'<rect x="40" y="30" width="176" height="196" fill="{sky}"/>'
    if shape == "beach":
        scene += '<rect x="40" y="128" width="176" height="40" fill="#2a8fc4"/>'
        scene += f'<rect x="40" y="168" width="176" height="58" fill="{ground}"/>'
        scene += '<circle cx="176" cy="70" r="18" fill="#ffd166"/>'
    elif shape == "city_night":
        for i, h in enumerate([90, 130, 70, 150, 110, 80]):
            x = 44 + i * 29
            scene += f'<rect x="{x}" y="{226 - h}" width="25" height="{h}" fill="{ground}"/>'
            scene += f'<rect x="{x + 6}" y="{236 - h}" width="5" height="6" fill="#ffd166"/>'
    elif shape in {"mountains", "snow", "forest"}:
        fill = "#f8fbff" if shape == "snow" else ground
        scene += f'<path d="M40 226 L100 110 L140 170 L176 96 L216 226Z" fill="{fill}"/>'
    elif shape == "sunset":
        scene += '<circle cx="128" cy="150" r="34" fill="#ff7b54"/>'
        scene += f'<rect x="40" y="160" width="176" height="66" fill="{ground}"/>'
    else:
        scene += f'<rect x="40" y="160" width="176" height="66" fill="{ground}"/>'
    return (
        scene
        + '<rect x="40" y="30" width="176" height="196" fill="none" stroke="#f4f4f2" stroke-width="12"/>'
        + '<line x1="128" y1="30" x2="128" y2="226" stroke="#f4f4f2" stroke-width="8"/>'
    )


def _generic_svg(colors: list[str], label: str) -> str:
    color = colors[0] if colors and colors[0] else _hash_color(label)
    initials = escape("".join(w[0] for w in label.split()[:2]).upper() or "?")
    return (
        f'<rect x="58" y="44" width="140" height="140" rx="32" fill="{color}" stroke="{_shade(color, 0.7)}" stroke-width="4"/>'
        f'<text x="128" y="134" text-anchor="middle" font-family="Inter,Arial,sans-serif" '
        f'font-size="56" font-weight="700" fill="#ffffff">{initials}</text>'
    )


def render_card_svg(hint: dict, prompt: str, width: int = 512, height: int = 512) -> str:
    kind = hint.get("kind", "generic")
    label = str(hint.get("label") or prompt)[:40]
    colors = [c for c in hint.get("colors", []) if c]
    shape = hint.get("shape")
    if kind == "hair":
        art = _hair_svg(shape, colors[0] if colors else "#5b3a22")
    elif kind == "garment":
        art = _garment_svg(shape or label, colors[0] if colors else _hash_color(label))
    elif kind == "swatch":
        color = colors[0] if colors else "#888888"
        art = (
            _garment_svg(shape, color)
            if shape
            else (
                f'<circle cx="128" cy="116" r="78" fill="{color}" stroke="{_shade(color, 0.7)}" stroke-width="6"/>'
            )
        )
    elif kind in {"room", "room_part"}:
        if kind == "room_part" and colors:
            base = ["#e9e7e2", "#c9b79c", "#2f3a45"]
            base[0 if shape == "wall" else 1] = colors[0]
            colors = base
        art = _room_svg(colors)
    elif kind == "window_view":
        art = _view_svg(shape, colors)
    elif kind in {"look", "lighting"}:
        stops = colors or ["#888888", "#444444"]
        art = "".join(
            f'<rect x="{24 + i * (208 // len(stops))}" y="40" width="{208 // len(stops) - 6}" height="168" rx="18" fill="{c}"/>'
            for i, c in enumerate(stops)
        )
    elif kind == "character":
        art = _hair_svg(
            "short" if shape != "senior" else "side_part",
            "#b8b8b8" if shape == "senior" else "#3b2a1e",
        )
    else:
        art = _generic_svg(colors, label)
    bg_a, bg_b = "#1c1f2b", "#2a2f45"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 256 300">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{bg_a}"/><stop offset="1" stop-color="{bg_b}"/></linearGradient></defs>'
        f'<rect width="256" height="300" rx="20" fill="url(#g)"/>'
        f'<g transform="translate(0,6)">{art}</g>'
        f'<rect x="0" y="252" width="256" height="48" fill="#000000" opacity="0.35"/>'
        f'<text x="128" y="283" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="17" '
        f'font-weight="600" fill="#f5f5f7">{escape(label)}</text>'
        "</svg>"
    )


class MockImageGenerator(MockMixin, ImageGeneratorProvider):
    def generate_image(self, request: ImageGenerationRequest) -> ImageResult:
        self.failures.check()
        svg = render_card_svg(request.hint, request.prompt, request.width, request.height)
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        dest = request.output_path.with_suffix(".svg")
        dest.write_text(svg, encoding="utf-8")
        return ImageResult(
            path=dest,
            content_type="image/svg+xml",
            width=request.width,
            height=request.height,
            usage=ProviderUsageInfo(model=self.descriptor.default_model(), images=1),
        )

    def edit_image(self, request: ImageEditRequest) -> ImageResult:
        self.failures.check()
        width, height = probe_video_size(request.image_path)
        color = (request.color_hex or _hash_color(request.label)).lstrip("#")
        filters = []
        if request.bbox is not None:
            b = request.bbox
            x, y = int(b.x * width), int(b.y * height)
            w, h = max(4, int(b.w * width)), max(4, int(b.h * height))
            filters.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color=0x{color}@0.45:t=fill")
            filters.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color=0x{color}@0.95:t=3")
        else:
            filters.append("hue=h=25:s=1.15")
        font = find_font_file()
        if font:
            filters.append(
                f"drawtext=fontfile={escape_filter_path(font)}:text='{escape_drawtext('PREVIEW · ' + request.label)}':"
                "fontsize=h/22:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=8:x=12:y=12"
            )
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        dest = request.output_path.with_suffix(".jpg")
        run_ffmpeg(
            ["-i", str(request.image_path), "-vf", ",".join(filters), "-q:v", "3", str(dest)]
        )
        return ImageResult(
            path=dest,
            content_type="image/jpeg",
            width=width,
            height=height,
            usage=ProviderUsageInfo(model=self.descriptor.default_model(), images=1),
        )
