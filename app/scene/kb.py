from __future__ import annotations

from typing import Dict, Optional


# Canonical entities and their locations in the scene
ENTITY_TO_LOCATION: Dict[str, str] = {
    "skull_model": "left",
    "implants": "right",
    "menu_bar": "center",
    "xray_display": "above the skull",
    "control_panel": "far-left",
    "dental_tray": "right",
}


# Synonyms mapped to canonical entity names
SYNONYM_TO_ENTITY: Dict[str, str] = {
    # skull
    "skull": "skull_model",
    "skull model": "skull_model",
    "dental model": "skull_model",
    # implants and tray
    "implant": "implants",
    "implants": "implants",
    "implant tray": "implants",
    "dental implants": "implants",
    # menu
    "menu": "menu_bar",
    "menu bar": "menu_bar",
    # xray
    "x-ray": "xray_display",
    "x ray": "xray_display",
    "xray": "xray_display",
    "xray display": "xray_display",
    # controls
    "control panel": "control_panel",
    "contrast panel": "control_panel",
    "brightness panel": "control_panel",
    # tray
    "dental tray": "dental_tray",
}


def resolve_location(question: str) -> Optional[str]:
    """Return a deterministic location answer if the question mentions a known entity.

    Example: "Where is the skull?" -> "The skull model is on the left."
    """
    q = question.strip().lower()
    # Try longest synonym first to avoid partial matches
    for synonym in sorted(SYNONYM_TO_ENTITY.keys(), key=len, reverse=True):
        if synonym in q:
            entity = SYNONYM_TO_ENTITY[synonym]
            loc = ENTITY_TO_LOCATION.get(entity)
            if not loc:
                return None
            friendly = {
                "skull_model": "skull model",
                "implants": "implants",
                "menu_bar": "menu bar",
                "xray_display": "X-ray display",
                "control_panel": "control panel",
                "dental_tray": "dental tray",
            }.get(entity, entity)
            # Phrase consistently
            if loc.startswith("above") or loc.startswith("far-"):
                return f"The {friendly} is {loc}."
            return f"The {friendly} is on the {loc}."
    return None


