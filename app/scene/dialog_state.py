from __future__ import annotations

import time
from typing import Any, Dict, Optional


class DialogueMemory:
    """In-memory dialog frames for slot filling keyed by session ID.

    Designed to be easily swappable to a DB-backed store later.
    """

    def __init__(self) -> None:
        self._frames: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds: int = 300

    def set_pending(self, session_id: str, frame: Dict[str, Any]) -> None:
        self._frames[session_id] = {"frame": frame, "ts": time.time()}

    def get_pending(self, session_id: str) -> Optional[Dict[str, Any]]:
        item = self._frames.get(session_id)
        if not item:
            return None
        if time.time() - item.get("ts", 0) > self._ttl_seconds:
            self._frames.pop(session_id, None)
            return None
        return item.get("frame")

    def clear(self, session_id: str) -> None:
        self._frames.pop(session_id, None)


# Global instance
dialog_memory = DialogueMemory()



