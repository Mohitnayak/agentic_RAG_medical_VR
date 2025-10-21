from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ParsedAction:
    tool: str
    arguments: Dict[str, Any]


def try_parse_action(text: str) -> Optional[ParsedAction]:
    """Attempt to parse a JSON action from the assistant text.

    Expected format:
    {
      "tool": "activate_tool",
      "arguments": {"name": "X", "properties": {"color": ["blue", "red"]}}
    }
    """
    text = text.strip()
    # best-effort JSON extraction
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = text[start : end + 1]
    try:
        data = json.loads(candidate)
        tool = data.get("tool")
        arguments = data.get("arguments", {})
        if isinstance(tool, str) and isinstance(arguments, dict):
            return ParsedAction(tool=tool, arguments=arguments)
    except Exception:
        return None
    return None


