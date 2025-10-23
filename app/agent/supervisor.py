from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from app.scene.normalizer import normalizer
from app.scene.classifier import classifier
from app.config_loader import load_config


class SupervisorAgent:
    """Decides which specialized agent should handle the turn.

    For now, prefer explicit notes intents via lightweight heuristics, then
    fall back to semantic classifier labels (control_*, info_*, notes_*).
    Returns a structured response when it can decide immediately; otherwise
    returns None to let the router continue its pipeline.
    """

    def __init__(self) -> None:
        pass

    def _notes_match(self, text: str) -> Optional[Dict[str, Any]]:
        t = text.lower().strip()
        # Simple phrase detection for notes
        starts = [
            "start recording",
            "start taking notes",
            "begin notes",
            "start notes",
        ]
        ends = [
            "stop recording",
            "end notes",
            "finalize notes",
            "stop notes",
        ]
        add_markers = ["note this:", "take notes of", "note:", "record:"]

        if any(p in t for p in starts):
            return {"type": "note_action", "function": "start_notes"}
        if any(p in t for p in ends):
            return {"type": "note_action", "function": "end_notes"}
        for m in add_markers:
            if m in t:
                idx = t.find(m)
                content = t[idx + len(m):].strip()
                return {"type": "note_action", "function": "add_note", "text": content}
        return None

    def decide(self, session_id: str, text: str) -> Optional[Dict[str, Any]]:
        # Normalize text (best-effort)
        norm = normalizer.normalize(text)
        ctext = norm.get("canonical_text") or text

        # Prefer explicit notes phrases
        notes = self._notes_match(ctext)
        if notes:
            return notes

        # Use semantic classifier if enabled to detect notes_* labels when configured
        label, conf = classifier.classify(ctext)
        if label.startswith("notes_"):
            if label == "notes_start":
                return {"type": "note_action", "function": "start_notes"}
            if label == "notes_end":
                return {"type": "note_action", "function": "end_notes"}
            if label == "notes_add":
                return {"type": "note_action", "function": "add_note"}

        # No immediate decision; let router proceed
        return None


# Global instance
supervisor = SupervisorAgent()



