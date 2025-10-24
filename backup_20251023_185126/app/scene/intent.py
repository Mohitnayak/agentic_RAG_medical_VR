from __future__ import annotations

import re
from typing import Any, Dict, Optional
import json
import os

from .values import numeric_parser

SWITCH_TARGETS = {
    "handles": "handles",
    "xray flashlight": "xray_flashlight",
    "x-ray flashlight": "xray_flashlight",
    "x ray flashlight": "xray_flashlight",
    "nerve": "show_nerve",
    "sinus": "show_sinus",
    "sinuses": "show_sinus",
    "show nerve": "show_nerve",
    "show sinus": "show_sinus",
    "show sinuses": "show_sinus",
    "align implants": "align_implants",
    "undo": "undo",
    "redo": "redo",
}

VALUE_TARGETS = {
    "contrast": "contrast",
    "brightness": "brightness",
}


def _find_phrase(text: str, phrases: list[str]) -> Optional[str]:
    for p in phrases:
        if p in text:
            return p
    return None


def parse_intent(message: str) -> Optional[Dict[str, Any]]:
    """Return a control action if the message implies a tool/scene control.

    Heuristics:
    - Verbs for switches: turn on/off, enable/disable, toggle, show/hide (handles, nerve, sinus, xray flashlight, align implants)
    - Numeric set: set/increase/decrease <brightness|contrast> to <num>
    - Implants: "give me the dental implants" -> if sizes present (a x b) apply; else ask size (return ask_size)
    - "show me <scene object>" is treated as Q&A, NOT a control, unless target is an overlay/switch (handles/nerve/sinus/xray)
    """
    text = message.strip().lower()

    # Handle definition and location questions FIRST
    # Definition questions
    if text.startswith("what are") or text.startswith("what is") or text.startswith("definition of"):
        return {"type": "ask_definition", "text": text}
    
    # Location questions  
    if text.startswith("where is") or text.startswith("where are"):
        return {"type": "ask_location", "text": text}

    # If user asks for information/definitions, do not treat as control intent
    info_markers = [
        "information on",
        "info on",
        "information about",
        "tell me about",
        "explain",
        "provide me information on",
        "provide me information about",
    ]
    if any(m in text for m in info_markers):
        return None

    # Brightness/contrast numeric control using robust parser
    if any(k in text for k in VALUE_TARGETS):
        for key, target in VALUE_TARGETS.items():
            if key in text:
                val = numeric_parser.parse_value(text, "brightness")
                if val is not None:
                    value, confidence = val
                    return {"tool": "control", "arguments": {"hand": "right", "target": target, "operation": "set", "value": float(value)}}

    # Switch verbs
    # Load verbs from config
    verbs = {
        "on": ["turn on", "enable", "switch on", "start", "show", "give me", "provide me with"],
        "off": ["turn off", "disable", "switch off", "stop", "hide"],
        "toggle": ["toggle"],
    }
    try:
        with open(os.path.join("config", "intent.json"), "r", encoding="utf-8") as f:
            cfg = json.load(f)
            if isinstance(cfg.get("verbs"), dict):
                for k in ("on", "off", "toggle"):
                    if isinstance(cfg["verbs"].get(k), list):
                        verbs[k] = [v.lower() for v in cfg["verbs"][k]]
    except Exception:
        pass

    on_verbs = [v + (" " if not v.endswith(" ") else "") for v in verbs["on"]]
    off_verbs = [v + (" " if not v.endswith(" ") else "") for v in verbs["off"]]
    toggle_verbs = [v + (" " if not v.endswith(" ") else "") for v in verbs["toggle"]]

    # Map switches; prefer explicit targets
    for phrase, target in SWITCH_TARGETS.items():
        if phrase in text:
            if _find_phrase(text, on_verbs):
                return {"tool": "control", "arguments": {"hand": "right", "target": target, "operation": "set", "value": "on"}}
            if _find_phrase(text, off_verbs):
                return {"tool": "control", "arguments": {"hand": "right", "target": target, "operation": "set", "value": "off"}}
            if _find_phrase(text, toggle_verbs):
                return {"tool": "control", "arguments": {"hand": "right", "target": target, "operation": "toggle"}}
            # "show me the handles" or "give me sinuses" -> ON for overlays/switches
            if target in {"handles", "xray_flashlight", "show_nerve", "show_sinus"} and (text.startswith("show") or text.startswith("give me") or text.startswith("provide me with")):
                return {"tool": "control", "arguments": {"hand": "right", "target": target, "operation": "set", "value": "on"}}

    # "give me the <switch>" / "provide me with <switch>" → ON for overlays/switch targets
    if text.startswith("give me") or text.startswith("give me the") or text.startswith("provide me with"):
        for phrase, target in SWITCH_TARGETS.items():
            if phrase in text and target in {"handles", "xray_flashlight", "show_nerve", "show_sinus", "align_implants"}:
                return {
                    "tool": "control",
                    "arguments": {"hand": "right", "target": target, "operation": "set", "value": "on"},
                }

    # Implants: give me or set implants (optionally with sizes)
    if "give me the dental implants" in text or "give me implants" in text or "set implants" in text:
        sizes = numeric_parser.parse_implant_size(text)
        if sizes is not None:
            size_dict, confidence = sizes
            return {"tool": "control", "arguments": {"hand": "right", "target": "implants", "operation": "set", "value": size_dict}}
        # no size provided
        return {"type": "ask_size", "text": "Which size for implants? Provide height_y_mm (3.0–4.8) and length_z_mm (6–17)."}

    # Default: no control intent
    return None
