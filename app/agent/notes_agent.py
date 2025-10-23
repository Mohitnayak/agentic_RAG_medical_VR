from __future__ import annotations

from typing import Any, Dict, List
from app.agent.base_agent import BaseAgent


class NotesAgent(BaseAgent):
    """LangChain-based Notes Agent that manages note-taking and documentation."""

    def __init__(self) -> None:
        super().__init__("Notes Agent", "notes_agent.json")

    def _get_system_prompt(self) -> str:
        return """You are a Notes Agent for a VR Dental Planning system.

Your role is to manage note-taking, recording, and documentation functions.

Key responsibilities:
- Start note-taking sessions
- Add notes with user-provided content
- End note-taking sessions
- Manage note organization and storage

Available functions:
- start_notes: Begin a new note-taking session
- add_note: Add a note with specific content
- end_notes: End the current note-taking session

Guidelines:
- Determine the appropriate function based on user intent
- Extract note content when provided
- Provide clear confirmation messages
- Be helpful in guiding users through note-taking

Respond with a JSON object matching the schema provided."""

    def _validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the response."""
        validated = super()._validate_response(response)
        
        # Ensure required fields for Notes Agent
        if 'function' not in validated:
            validated['function'] = 'start_notes'  # Default
        
        if 'note_text' not in validated:
            validated['note_text'] = None
        
        return validated

    def get_agent_description(self) -> str:
        return "Notes Agent - Manages note-taking, recording, and documentation"

    # Legacy methods for backward compatibility
    def start(self) -> Dict[str, Any]:
        return {
            "type": "note_action",
            "agent": "Notes Agent",
            "intent": "start_notes",
            "function": "start_notes",
            "message": "Starting a new note-taking session.",
            "note_text": None,
            "confidence": 0.8,
            "context_used": False,
        }

    def end(self) -> Dict[str, Any]:
        return {
            "type": "note_action",
            "agent": "Notes Agent",
            "intent": "end_notes",
            "function": "end_notes",
            "message": "Note-taking session ended.",
            "note_text": None,
            "confidence": 0.8,
            "context_used": False,
        }

    def add(self, text: str | None) -> Dict[str, Any]:
        return {
            "type": "note_action",
            "agent": "Notes Agent",
            "intent": "add_note",
            "function": "add_note",
            "message": "Note added.",
            "note_text": text or "",
            "confidence": 0.8,
            "context_used": False,
        }


# Global instance
notes_agent = NotesAgent()


