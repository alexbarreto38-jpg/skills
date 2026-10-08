"""Curated suggestion catalog used by the mock suggestion provider.

Each item: label, structured value, tags (for context filtering) and a preview
hint (for the SVG card generator). A real LLM-backed provider would produce
the same shape; the context rules below are what it is expected to honour.
"""

from __future__ import annotations

from typing import Any

Item = dict[str, Any]


def _color(label: str, hex_value: str, *tags: str) -> Item:
    return {
        "label": label,
        "value": {"color": label.lower(), "colorHex": hex_value},
        "hex": hex_value,
        "tags": list(tags),
    }


COLORS: list[Item] = [
    _color("Azul", "#2f6fdb", "casual", "cool"),
    _color("Amarela", "#f2c230", "casual", "warm", "beach"),
    _color("Verde", "#2e9e5b", "casual"),
    _color("Branca", "#f5f5f2", "casual", "beach", "formal"),
    _color("Preta", "#1f1f22", "formal", "urban"),
    _color("Rosa", "#e86fa5", "casual", "warm"),
    _color("Laranja", "#ef7d32", "casual", "warm", "beach"),
    _color("Cinza mescla", "#9aa0a6", "casual", "urban"),
    _color("Vinho", "#7b2236", "formal", "cold"),
    _color("Azul-marinho", "#1f2f56", "formal", "urban"),
    _color("Lilás", "#a98bd6", "casual"),
    _color("Verde-oliva", "#6b7340", "casual", "outdoor"),
]

HAIR_STYLES: list[Item] = [
    {"label": "Curto", "value": "curto", "shape": "short", "tags": ["neutral"]},
    {"label": "Médio", "value": "médio", "shape": "medium", "tags": ["neutral"]},
    {"label": "Comprido", "value": "comprido", "shape": "long", "tags": ["neutral"]},
    {"label": "Cacheado", "value": "cacheado", "shape": "curly", "tags": ["neutral"]},
    {"label": "Ondulado", "value": "ondulado", "shape": "wavy", "tags": ["neutral"]},
    {"label": "Liso", "value": "liso", "shape": "straight", "tags": ["neutral"]},
    {"label": "Buzz cut", "value": "buzz cut", "shape": "buzz", "tags": ["neutral"]},
    {"label": "Social", "value": "social", "shape": "side_part", "tags": ["formal", "adult"]},
    {"label": "Afro", "value": "afro", "shape": "afro", "tags": ["neutral"]},
    {"label": "Trançado", "value": "trançado", "shape": "braids", "tags": ["neutral"]},
    {"label": "Coque", "value": "coque", "shape": "bun", "tags": ["neutral"]},
    {"label": "Moicano", "value": "moicano", "shape": "mohawk", "tags": ["urban"]},
    {
        "label": "Rabo de cavalo",
        "value": "rabo de cavalo",
        "shape": "ponytail",
        "tags": ["neutral"],
    },
    {"label": "Franja", "value": "com franja", "shape": "bangs", "tags": ["neutral"]},
]

HAIR_COLORS: list[Item] = [
    {
        "label": "Castanho",
        "value": {"color": "castanho", "colorHex": "#5b3a22"},
        "hex": "#5b3a22",
        "tags": [],
    },
    {
        "label": "Preto",
        "value": {"color": "preto", "colorHex": "#1c1c1c"},
        "hex": "#1c1c1c",
        "tags": [],
    },
    {
        "label": "Loiro",
        "value": {"color": "loiro", "colorHex": "#d9b36c"},
        "hex": "#d9b36c",
        "tags": [],
    },
    {
        "label": "Ruivo",
        "value": {"color": "ruivo", "colorHex": "#a5452a"},
        "hex": "#a5452a",
        "tags": [],
    },
    {
        "label": "Castanho claro",
        "value": {"color": "castanho claro", "colorHex": "#8a6142"},
        "hex": "#8a6142",
        "tags": [],
    },
    {
        "label": "Grisalho",
        "value": {"color": "grisalho", "colorHex": "#b8b8b8"},
        "hex": "#b8b8b8",
        "tags": ["adult"],
    },
    {
        "label": "Azul fantasia",
        "value": {"color": "azul fantasia", "colorHex": "#3b6fe0"},
        "hex": "#3b6fe0",
        "tags": ["urban"],
    },
    {
        "label": "Rosa pastel",
        "value": {"color": "rosa pastel", "colorHex": "#f0a6c8"},
        "hex": "#f0a6c8",
        "tags": ["urban"],
    },
]


def _garment(label: str, item: str, color: str, hex_value: str, *tags: str) -> Item:
    return {
        "label": label,
        "value": {
            "label": label,
            "attributes": {"item": item, "color": color, "colorHex": hex_value},
        },
        "hex": hex_value,
        "shape": item,
        "tags": list(tags),
    }


WARDROBE_UPPER: list[Item] = [
    _garment("Camiseta azul", "camiseta", "azul", "#2f6fdb", "casual", "warm", "beach", "home"),
    _garment(
        "Camiseta listrada",
        "camiseta",
        "listrada azul e branca",
        "#4b79c9",
        "casual",
        "beach",
        "home",
    ),
    _garment(
        "Camiseta amarela", "camiseta", "amarela", "#f2c230", "casual", "warm", "beach", "home"
    ),
    _garment("Moletom cinza", "moletom", "cinza", "#8f949b", "casual", "cold", "home"),
    _garment("Camisa polo verde", "camisa polo", "verde", "#2e9e5b", "casual", "home"),
    _garment("Regata branca", "regata", "branca", "#f5f5f2", "casual", "warm", "beach"),
    _garment("Camisa xadrez", "camisa", "xadrez vermelha", "#b03a2e", "casual", "cold", "outdoor"),
    _garment("Jaqueta jeans", "jaqueta", "jeans", "#4a6fa5", "casual", "cold", "urban"),
    _garment("Suéter bege", "suéter", "bege", "#d9c3a5", "casual", "cold", "home"),
    _garment("Camisa social branca", "camisa social", "branca", "#f4f4f4", "formal", "adult"),
    _garment("Terno azul-marinho", "terno", "azul-marinho", "#1f2f56", "formal", "cold", "adult"),
    _garment(
        "Camiseta de time",
        "camiseta esportiva",
        "vermelha e preta",
        "#c0392b",
        "casual",
        "sport",
        "home",
    ),
    _garment("Blusa floral", "blusa", "floral", "#e58fb1", "casual", "warm", "beach"),
    _garment("Cardigã verde", "cardigã", "verde", "#5f7d6a", "casual", "cold", "home"),
]

WARDROBE_LOWER: list[Item] = [
    _garment("Bermuda jeans", "bermuda", "azul jeans", "#4a6fa5", "casual", "warm", "home"),
    _garment("Bermuda cáqui", "bermuda", "cáqui", "#b7a57a", "casual", "warm", "beach"),
    _garment("Calça jeans", "calça", "azul", "#2f4a6d", "casual", "home", "urban"),
    _garment("Calça de moletom", "calça de moletom", "cinza", "#8f949b", "casual", "cold", "home"),
    _garment("Short de praia", "short", "estampado", "#2bb3c0", "casual", "warm", "beach"),
    _garment("Calça social", "calça social", "preta", "#1f1f22", "formal", "adult"),
    _garment("Saia jeans", "saia", "jeans", "#4a6fa5", "casual", "warm"),
    _garment("Legging preta", "legging", "preta", "#202020", "casual", "sport"),
]

FOOTWEAR: list[Item] = [
    _garment("Tênis branco", "tênis", "branco", "#f4f4f4", "casual", "home", "urban"),
    _garment("Chinelo", "chinelo", "azul", "#2f6fdb", "casual", "warm", "beach", "home"),
    _garment("Sandália", "sandália", "marrom", "#8a5a3b", "casual", "warm", "beach"),
    _garment("Tênis colorido", "tênis", "colorido", "#ef7d32", "casual", "sport"),
    _garment("Bota", "bota", "marrom", "#6b4226", "casual", "cold", "outdoor"),
    _garment("Sapato social", "sapato social", "preto", "#1f1f22", "formal", "adult"),
    _garment("Pantufa", "pantufa", "cinza", "#9aa0a6", "casual", "cold", "home"),
    _garment("Descalço", "descalço", "pele", "#d1a684", "casual", "beach", "home"),
]

ACCESSORIES: list[Item] = [
    {
        "label": "Boné",
        "value": {"label": "Boné", "class": "cap", "attributes": {"color": "azul"}},
        "hex": "#2f6fdb",
        "tags": ["casual", "urban"],
    },
    {
        "label": "Óculos de sol",
        "value": {"label": "Óculos de sol", "class": "sunglasses"},
        "hex": "#222222",
        "tags": ["beach", "warm"],
    },
    {
        "label": "Relógio esportivo",
        "value": {"label": "Relógio esportivo", "class": "watch"},
        "hex": "#444444",
        "tags": ["sport"],
    },
    {
        "label": "Pulseira colorida",
        "value": {"label": "Pulseira colorida", "class": "bracelet"},
        "hex": "#e86fa5",
        "tags": ["casual"],
    },
    {
        "label": "Chapéu de palha",
        "value": {"label": "Chapéu de palha", "class": "hat"},
        "hex": "#d9b36c",
        "tags": ["beach", "warm"],
    },
    {
        "label": "Cachecol",
        "value": {"label": "Cachecol", "class": "scarf"},
        "hex": "#7b2236",
        "tags": ["cold"],
    },
    {
        "label": "Mochila",
        "value": {"label": "Mochila", "class": "backpack"},
        "hex": "#2e9e5b",
        "tags": ["casual", "child"],
    },
    {
        "label": "Fones de ouvido",
        "value": {"label": "Fones de ouvido", "class": "headphones"},
        "hex": "#1f1f22",
        "tags": ["urban"],
    },
]

CHARACTER_LOOKS: list[Item] = [
    {
        "label": "Look casual de verão",
        "value": {"attributes": {"look": "casual de verão"}},
        "palette": ["#f2c230", "#2bb3c0", "#f5f5f2"],
        "tags": ["warm", "beach", "casual"],
    },
    {
        "label": "Look esportivo",
        "value": {"attributes": {"look": "esportivo"}},
        "palette": ["#c0392b", "#202020", "#f4f4f4"],
        "tags": ["sport", "casual"],
    },
    {
        "label": "Look de inverno",
        "value": {"attributes": {"look": "inverno aconchegante"}},
        "palette": ["#7b2236", "#8f949b", "#6b4226"],
        "tags": ["cold", "home"],
    },
    {
        "label": "Look social",
        "value": {"attributes": {"look": "social"}},
        "palette": ["#1f2f56", "#f4f4f4", "#1f1f22"],
        "tags": ["formal", "adult"],
    },
    {
        "label": "Pijama",
        "value": {"attributes": {"look": "pijama"}},
        "palette": ["#a98bd6", "#f0a6c8", "#f5f5f2"],
        "tags": ["home", "casual"],
    },
    {
        "label": "Uniforme escolar",
        "value": {"attributes": {"look": "uniforme escolar"}},
        "palette": ["#f5f5f2", "#1f2f56", "#2f6fdb"],
        "tags": ["child"],
    },
]

CHARACTER_REPLACEMENTS: list[Item] = [
    {
        "label": "Menina de 9 anos",
        "value": {
            "label": "Menina",
            "attributes": {"ageGroup": "child", "apparentAge": "8-10 anos"},
        },
        "tags": ["child"],
    },
    {
        "label": "Menino de 12 anos",
        "value": {
            "label": "Menino mais velho",
            "attributes": {"ageGroup": "child", "apparentAge": "11-13 anos"},
        },
        "tags": ["child"],
    },
    {
        "label": "Menino de 6 anos",
        "value": {
            "label": "Menino pequeno",
            "attributes": {"ageGroup": "child", "apparentAge": "5-7 anos"},
        },
        "tags": ["child"],
    },
    {
        "label": "Mulher de 40 anos",
        "value": {
            "label": "Mulher",
            "attributes": {"ageGroup": "adult", "apparentAge": "35-45 anos"},
        },
        "tags": ["adult"],
    },
    {
        "label": "Homem de 40 anos",
        "value": {
            "label": "Homem",
            "attributes": {"ageGroup": "adult", "apparentAge": "35-45 anos"},
        },
        "tags": ["adult"],
    },
    {
        "label": "Avó",
        "value": {
            "label": "Avó",
            "attributes": {"ageGroup": "senior", "apparentAge": "65-75 anos"},
        },
        "tags": ["adult", "senior"],
    },
    {
        "label": "Avô",
        "value": {
            "label": "Avô",
            "attributes": {"ageGroup": "senior", "apparentAge": "65-75 anos"},
        },
        "tags": ["adult", "senior"],
    },
]


def _preset(pid: str, label: str, wall: str, floor: str, accent: str, *tags: str) -> Item:
    return {
        "label": label,
        "value": {
            "presetId": pid,
            "label": label,
            "attributes": {
                "style": label.lower(),
                "palette": [wall, floor, accent],
                "tags": list(tags),
            },
        },
        "palette": [wall, floor, accent],
        "tags": list(tags),
    }


ENVIRONMENT_PRESETS: dict[str, list[Item]] = {
    "living_room": [
        _preset(
            "modern_apartment",
            "Apartamento moderno",
            "#e9e7e2",
            "#c9b79c",
            "#2f3a45",
            "indoor",
            "home",
            "urban",
            "modern",
        ),
        _preset(
            "simple_house",
            "Casa simples",
            "#efe4cf",
            "#b88a5a",
            "#6b8f71",
            "indoor",
            "home",
            "casual",
        ),
        _preset(
            "small_apartment",
            "Apartamento pequeno",
            "#f1efe9",
            "#a98a6a",
            "#d1495b",
            "indoor",
            "home",
            "urban",
        ),
        _preset(
            "beach_house",
            "Casa de praia",
            "#f6f1e3",
            "#d8c29d",
            "#2bb3c0",
            "indoor",
            "home",
            "beach",
            "warm",
        ),
        _preset(
            "sophisticated_room",
            "Sala sofisticada",
            "#d8d2c8",
            "#6e4b35",
            "#b08d57",
            "indoor",
            "home",
            "formal",
        ),
        _preset(
            "loft",
            "Loft industrial",
            "#8d8d8a",
            "#5a5a58",
            "#c86b3c",
            "indoor",
            "home",
            "urban",
            "modern",
        ),
        _preset(
            "contemporary_house",
            "Casa contemporânea",
            "#f3f3f1",
            "#d6cfc4",
            "#3d6b5b",
            "indoor",
            "home",
            "modern",
        ),
        _preset(
            "country_house",
            "Casa de campo",
            "#efe2c8",
            "#8a5a3b",
            "#7a8f4f",
            "indoor",
            "home",
            "outdoor",
            "cold",
        ),
        _preset(
            "mountain_cabin",
            "Cabana na montanha",
            "#a0784f",
            "#6b4226",
            "#c94c3c",
            "indoor",
            "home",
            "cold",
        ),
    ],
    "default": [
        _preset(
            "modern_interior",
            "Interior moderno",
            "#e9e7e2",
            "#c9b79c",
            "#2f3a45",
            "indoor",
            "modern",
        ),
        _preset(
            "rustic_interior", "Interior rústico", "#d9c3a5", "#7a4e2d", "#6b8f71", "indoor", "cold"
        ),
        _preset(
            "minimal_studio",
            "Estúdio minimalista",
            "#f5f5f2",
            "#e1ddd6",
            "#1f1f22",
            "indoor",
            "modern",
        ),
        _preset("tropical", "Ambiente tropical", "#f6f1e3", "#d8c29d", "#2e9e5b", "beach", "warm"),
    ],
}


def _view(label: str, kind: str, sky: str, ground: str, *tags: str) -> Item:
    return {
        "label": label,
        "value": {
            "label": f"Vista da janela: {label.lower()}",
            "attributes": {"view": label.lower(), "tags": list(tags)},
        },
        "view": kind,
        "palette": [sky, ground],
        "tags": list(tags),
    }


WINDOW_VIEWS: list[Item] = [
    _view("Praia", "beach", "#8fd3f4", "#e8d3a2", "beach", "warm", "day"),
    _view("Cidade à noite", "city_night", "#1b2340", "#3a3f58", "urban", "night"),
    _view("Montanhas", "mountains", "#a7c7e7", "#5f7d6a", "outdoor", "cold", "day"),
    _view("Jardim florido", "garden", "#b7e1f3", "#5e9e4b", "outdoor", "day"),
    _view("Neve", "snow", "#dfe9f2", "#f8fbff", "cold", "day"),
    _view("Campo ao pôr do sol", "sunset", "#f4a259", "#7a8f4f", "outdoor", "warm"),
    _view("Rua residencial", "street", "#b7d3e9", "#8f949b", "urban", "day"),
    _view("Floresta", "forest", "#9ccbe0", "#2e5d3a", "outdoor", "day"),
]

WALLS: list[Item] = [
    {
        "label": "Branco neve",
        "value": {
            "label": "Parede branco neve",
            "attributes": {"color": "branco neve", "colorHex": "#fbfaf7"},
        },
        "hex": "#fbfaf7",
        "tags": ["modern"],
    },
    {
        "label": "Verde sálvia",
        "value": {
            "label": "Parede verde sálvia",
            "attributes": {"color": "verde sálvia", "colorHex": "#a7b8a0"},
        },
        "hex": "#a7b8a0",
        "tags": ["home"],
    },
    {
        "label": "Azul petróleo",
        "value": {
            "label": "Parede azul petróleo",
            "attributes": {"color": "azul petróleo", "colorHex": "#24535f"},
        },
        "hex": "#24535f",
        "tags": ["formal"],
    },
    {
        "label": "Terracota",
        "value": {
            "label": "Parede terracota",
            "attributes": {"color": "terracota", "colorHex": "#c7704f"},
        },
        "hex": "#c7704f",
        "tags": ["warm"],
    },
    {
        "label": "Tijolo aparente",
        "value": {
            "label": "Parede de tijolo aparente",
            "attributes": {"material": "tijolo aparente", "colorHex": "#9c4f3a"},
        },
        "hex": "#9c4f3a",
        "tags": ["urban"],
    },
    {
        "label": "Papel de parede floral",
        "value": {
            "label": "Papel de parede floral",
            "attributes": {"material": "papel de parede floral", "colorHex": "#e8c9c1"},
        },
        "hex": "#e8c9c1",
        "tags": ["home"],
    },
    {
        "label": "Madeira ripada",
        "value": {
            "label": "Parede de madeira ripada",
            "attributes": {"material": "madeira ripada", "colorHex": "#a0784f"},
        },
        "hex": "#a0784f",
        "tags": ["modern", "cold"],
    },
]

FLOORS: list[Item] = [
    {
        "label": "Madeira clara",
        "value": {
            "label": "Piso de madeira clara",
            "attributes": {"material": "madeira clara", "colorHex": "#d6b48a"},
        },
        "hex": "#d6b48a",
        "tags": ["home"],
    },
    {
        "label": "Porcelanato",
        "value": {
            "label": "Piso de porcelanato",
            "attributes": {"material": "porcelanato", "colorHex": "#e3e1dc"},
        },
        "hex": "#e3e1dc",
        "tags": ["modern"],
    },
    {
        "label": "Cimento queimado",
        "value": {
            "label": "Piso de cimento queimado",
            "attributes": {"material": "cimento queimado", "colorHex": "#8d8d8a"},
        },
        "hex": "#8d8d8a",
        "tags": ["urban"],
    },
    {
        "label": "Tapete persa",
        "value": {
            "label": "Tapete persa",
            "attributes": {"material": "tapete persa", "colorHex": "#8a2f3a"},
        },
        "hex": "#8a2f3a",
        "tags": ["formal"],
    },
    {
        "label": "Ladrilho hidráulico",
        "value": {
            "label": "Ladrilho hidráulico",
            "attributes": {"material": "ladrilho hidráulico", "colorHex": "#4f7c8a"},
        },
        "hex": "#4f7c8a",
        "tags": ["home"],
    },
    {
        "label": "Carpete cinza",
        "value": {
            "label": "Carpete cinza",
            "attributes": {"material": "carpete", "colorHex": "#9aa0a6"},
        },
        "hex": "#9aa0a6",
        "tags": ["cold"],
    },
]

LIGHTING: list[Item] = [
    {
        "label": "Luz do entardecer",
        "value": {
            "label": "Luz quente do entardecer",
            "attributes": {"timeOfDay": "entardecer", "colorTemperature": "warm"},
        },
        "palette": ["#f4a259", "#7a4e2d"],
        "tags": ["warm"],
    },
    {
        "label": "Luz fria de manhã",
        "value": {
            "label": "Luz fria da manhã",
            "attributes": {"timeOfDay": "manhã", "colorTemperature": "cool"},
        },
        "palette": ["#cfe3f4", "#7d9cb8"],
        "tags": ["cold"],
    },
    {
        "label": "Noite com abajur",
        "value": {
            "label": "Noite iluminada por abajur",
            "attributes": {
                "timeOfDay": "noite",
                "source": "artificial",
                "colorTemperature": "warm",
            },
        },
        "palette": ["#2a2238", "#f2c230"],
        "tags": ["night"],
    },
    {
        "label": "Dia nublado",
        "value": {
            "label": "Luz difusa de dia nublado",
            "attributes": {"timeOfDay": "dia", "colorTemperature": "neutral"},
        },
        "palette": ["#c9ced4", "#8f949b"],
        "tags": ["cold"],
    },
    {
        "label": "Sol forte",
        "value": {
            "label": "Sol forte do meio-dia",
            "attributes": {"timeOfDay": "meio-dia", "colorTemperature": "neutral"},
        },
        "palette": ["#fff3c4", "#f2c230"],
        "tags": ["warm", "beach"],
    },
]


def _obj(label: str, cls: str, material: str | None = None, *tags: str) -> Item:
    attributes = {"material": material} if material else {}
    return {
        "label": label,
        "value": {"label": label, "class": cls, "attributes": attributes},
        "class": cls,
        "tags": list(tags),
    }


OBJECT_REPLACEMENTS: dict[str, list[Item]] = {
    "tableware": [
        _obj("Prato", "plate", "porcelana", "home"),
        _obj("Caneca", "mug", "cerâmica", "home"),
        _obj("Garrafa", "bottle", "vidro", "home"),
        _obj("Tigela", "bowl", "cerâmica", "home"),
        _obj("Taça", "wine_glass", "cristal", "formal"),
        _obj("Copo de plástico", "plastic_cup", "plástico", "child"),
        _obj("Vaso pequeno", "vase", "porcelana", "home"),
    ],
    "electronics": [
        _obj("Tablet", "tablet", None, "urban"),
        _obj("Controle de videogame", "remote", None, "child"),
        _obj("Livro", "book", None, "home"),
        _obj("Telefone antigo", "phone", None, "home"),
    ],
    "decoration": [
        _obj("Vaso com flores", "vase", "cerâmica", "home"),
        _obj("Escultura moderna", "vase", "resina", "modern"),
        _obj("Luminária de mesa", "lamp", None, "home"),
        _obj("Pilha de livros", "book", None, "home"),
        _obj("Cacto", "plant", None, "warm"),
    ],
    "furniture": [
        _obj("Sofá de couro caramelo", "sofa", "couro", "formal"),
        _obj("Sofá de linho branco", "sofa", "linho", "beach", "modern"),
        _obj("Poltrona", "armchair", "veludo", "home"),
        _obj("Mesa de vidro", "table", "vidro", "modern"),
        _obj("Mesa rústica", "table", "madeira de demolição", "cold"),
        _obj("Pufe", "pouf", "tecido", "home"),
    ],
    "storage": [
        _obj("Caixa de brinquedos", "box", "plástico", "child"),
        _obj("Cesto de vime", "box", "vime", "beach"),
        _obj("Pufe", "pouf", "tecido", "home"),
    ],
    "default": [
        _obj("Livro", "book", None, "home"),
        _obj("Vaso com flores", "vase", "cerâmica", "home"),
        _obj("Caixa", "box", "papelão", "home"),
        _obj("Almofada", "pillow", "tecido", "home"),
    ],
}
