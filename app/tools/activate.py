from __future__ import annotations

from typing import Any, Dict


def activate_tool_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("name")
    properties = args.get("properties", {})
    if not isinstance(name, str) or not name:
        return {"ok": False, "error": "name is required"}
    if not isinstance(properties, dict):
        return {"ok": False, "error": "properties must be an object"}
    # For v1, we simulate activation by returning a confirmation payload
    return {"ok": True, "activated": {"name": name, "properties": properties}}


def tool_spec() -> Dict[str, Any]:
    return {
        "name": "activate_tool",
        "description": "Activate a tool with specific properties (e.g., colors, intensity).",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "properties": {"type": "object"},
            },
            "required": ["name"],
        },
        "handler": activate_tool_handler,
    }


