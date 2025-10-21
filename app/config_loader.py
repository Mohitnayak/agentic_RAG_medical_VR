from __future__ import annotations

import json
import os
from typing import Any, Dict


def load_json(relative_path: str) -> Dict[str, Any]:
    try:
        path = os.path.join(os.getcwd(), relative_path)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_config() -> Dict[str, Any]:
    """Load all configuration files."""
    return {
        "intent": load_json("config/intent.json"),
        "entities": load_json("config/entities.json"),
        "ranges": load_json("config/ranges.json"),
        "retrieval": load_json("config/retrieval.json")
    }
