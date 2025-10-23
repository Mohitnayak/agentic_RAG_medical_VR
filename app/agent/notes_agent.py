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

    def process(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Process a user query with special handling for notes functionality."""
        try:
            query_lower = query.lower().strip()
            
            # Handle start notes requests
            start_phrases = ['start taking notes', 'start notes', 'begin notes', 'start recording', 'take notes']
            if any(phrase in query_lower for phrase in start_phrases):
                return {
                    "type": "note_action",
                    "agent": "Notes Agent",
                    "intent": "start_notes",
                    "function": "start_notes",
                    "message": "Notes are now active! You can type your notes below.",
                    "state": "on",
                    "note_text": None,
                    "confidence": 0.9,
                    "context_used": False
                }
            
            # Handle end notes requests
            end_phrases = ['stop taking notes', 'end notes', 'stop notes', 'done taking notes', 'finish notes', 'stop recording']
            if any(phrase in query_lower for phrase in end_phrases):
                return {
                    "type": "note_action",
                    "agent": "Notes Agent",
                    "intent": "end_notes",
                    "function": "end_notes",
                    "message": "Notes session ended. Your notes have been saved.",
                    "state": "off",
                    "note_text": None,
                    "confidence": 0.9,
                    "context_used": False
                }
            
            # Handle note retrieval requests
            retrieve_phrases = ['show me my notes', 'give me my notes', 'show notes', 'my notes', 'notes i took', 'last notes']
            if any(phrase in query_lower for phrase in retrieve_phrases):
                return {
                    "type": "note_action",
                    "agent": "Notes Agent",
                    "intent": "retrieve_notes",
                    "function": "retrieve_notes",
                    "message": "Here are your saved notes:",
                    "state": "off",
                    "note_text": None,
                    "confidence": 0.9,
                    "context_used": False
                }
            
            # Handle add note requests (when user provides content)
            add_phrases = ['note this:', 'add note:', 'record:', 'note:']
            for phrase in add_phrases:
                if phrase in query_lower:
                    # Extract content after the phrase
                    content_start = query_lower.find(phrase) + len(phrase)
                    content = query[content_start:].strip()
                    if content:
                        return {
                            "type": "note_action",
                            "agent": "Notes Agent",
                            "intent": "add_note",
                            "function": "add_note",
                            "message": f"Note added: {content}",
                            "state": "on",
                            "note_text": content,
                            "confidence": 0.9,
                            "context_used": False
                        }
            
            # For other queries, use the base class processing
            return super().process(query, conversation_history)
            
        except Exception as e:
            print(f"Error in Notes Agent processing: {e}")
            return self._create_error_response(str(e))

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


