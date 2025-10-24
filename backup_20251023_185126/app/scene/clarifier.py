from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.config_loader import load_config


class Clarifier:
    """Generates targeted clarifications using config entities and ranges."""

    def __init__(self) -> None:
        pass

    def ask_for_entity(self, intent_label: str, candidates: List[Tuple[str, float, Dict[str, Any]]]) -> Dict[str, Any]:
        names: List[str] = []
        for n, c, d in candidates[:5]:
            nm = d.get("name", n)
            if nm not in names:
                names.append(nm)
        verb = "turn on" if intent_label == "control_on" else ("turn off" if intent_label == "control_off" else "set")
        return {
            "type": "clarification",
            "message": f"Which element should I {verb}?",
            "clarifications": [f"e.g., {', '.join(names)}"] if names else ["Please specify the element"],
        }

    def ask_for_value(self, target: str) -> Dict[str, Any]:
        try:
            cfg = load_config()
            ranges_cfg = cfg.get("ranges", {})
            r = ranges_cfg.get(target, {})
            r_min = r.get("min")
            r_max = r.get("max")
            hint = f" ({r_min}–{r_max})" if r_min is not None and r_max is not None else ""
        except Exception:
            hint = ""
        return {
            "type": "clarification",
            "message": f"What value should I set for {target}{hint}?",
            "clarifications": [f"Example: set {target} to 50"],
        }


# Global instance
clarifier = Clarifier()




