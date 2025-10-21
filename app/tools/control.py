from __future__ import annotations

from typing import Any, Dict
from app.config_loader import load_config


ALLOWED_HANDS = {"left", "right", "none"}


def _get_ranges() -> Dict[str, Any]:
    """Load ranges from config."""
    config = load_config()
    return config.get("ranges", {})


def _get_entities() -> Dict[str, Any]:
    """Load entities from config."""
    config = load_config()
    entities = config.get("entities", {}).get("entities", [])
    
    switch_targets = set()
    value_targets = set()
    
    for entity in entities:
        entity_type = entity.get("type", "")
        name = entity.get("name", "")
        
        if entity_type == "switch":
            switch_targets.add(name)
        elif entity_type == "control":
            value_targets.add(name)
    
    return {
        "switch_targets": switch_targets,
        "value_targets": value_targets
    }


def _validate(args: Dict[str, Any]) -> tuple[bool, str | None, Dict[str, Any] | None]:
    hand = args.get("hand", "none")
    target = args.get("target")
    operation = args.get("operation")
    value = args.get("value")
    ranges = _get_ranges()
    entities = _get_entities()
    
    switch_targets = entities["switch_targets"]
    value_targets = entities["value_targets"]

    if hand not in ALLOWED_HANDS:
        return False, "invalid hand", None
    if not isinstance(target, str):
        return False, "target required", None
    if operation not in {"set", "toggle"}:
        return False, "operation must be 'set' or 'toggle'", None

    # Enforce controller constraint: left hand cannot control implants/menu
    if hand == "left" and target in (switch_targets | value_targets):
        if target != "skull_model":
            return False, "left hand cannot control this target", None

    normalized: Dict[str, Any] = {"hand": hand, "target": target, "operation": operation}

    if target in switch_targets:
        if operation == "set":
            if value not in {"on", "off"}:
                return False, "value must be 'on' or 'off'", None
            normalized["value"] = value
        else:  # toggle
            normalized["value"] = "toggle"
        return True, None, normalized

    if target in value_targets:
        if not isinstance(value, (int, float)):
            return False, "value must be a number", None
        
        # Use ranges from config
        target_range = ranges.get(target, {"min": 0, "max": 100})
        min_val = target_range.get("min", 0)
        max_val = target_range.get("max", 100)
        
        if not (min_val <= float(value) <= max_val):
            return False, f"value out of range ({min_val}-{max_val})", None
        normalized["value"] = float(value)
        return True, None, normalized

    if target == "implants":
        # Allow either on/off or sizing object
        if isinstance(value, str):
            if value not in {"on", "off"}:
                return False, "implants value must be 'on' or 'off' or size object", None
            normalized["value"] = value
            return True, None, normalized
        if isinstance(value, dict):
            implant_ranges = ranges.get("implants", {})
            height_range = implant_ranges.get("height_y_mm", {"min": 3.0, "max": 4.8})
            length_range = implant_ranges.get("length_z_mm", {"min": 6.0, "max": 17.0})
            
            h = value.get("height_y_mm")
            l = value.get("length_z_mm")
            if h is not None and not (height_range["min"] <= float(h) <= height_range["max"]):
                return False, f"height_y_mm out of range ({height_range['min']}-{height_range['max']})", None
            if l is not None and not (length_range["min"] <= float(l) <= length_range["max"]):
                return False, f"length_z_mm out of range ({length_range['min']}-{length_range['max']})", None
            normalized["value"] = {k: float(v) for k, v in value.items() if k in {"height_y_mm", "length_z_mm"}}
            return True, None, normalized
        return False, "invalid implants value", None

    return False, "unknown target", None


def control_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    ok, err, norm = _validate(args)
    if not ok or norm is None:
        return {"ok": False, "error": err}
    return {"ok": True, "applied": norm}


def tool_spec() -> Dict[str, Any]:
    return {
        "name": "control",
        "description": "Control VR scene tools and implants with validated arguments.",
        "schema": {
            "type": "object",
            "properties": {
                "hand": {"type": "string", "enum": ["left", "right", "none"]},
                "target": {"type": "string"},
                "operation": {"type": "string", "enum": ["set", "toggle"]},
                "value": {}
            },
            "required": ["target", "operation"],
        },
        "handler": control_handler,
    }


