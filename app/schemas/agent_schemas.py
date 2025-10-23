from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class NoteFunction(str, Enum):
    START_NOTES = "start_notes"
    ADD_NOTE = "add_note"
    END_NOTES = "end_notes"

class NotesAgentResponse(BaseModel):
    """Schema for Notes Agent responses"""
    type: str = Field(default="note_action", description="Response type")
    agent: str = Field(default="Notes Agent", description="Agent name")
    intent: str = Field(description="Detected intent")
    function: NoteFunction = Field(description="Note function to execute")
    message: str = Field(description="Human-readable message")
    note_text: Optional[str] = Field(default=None, description="Note content if adding")
    confidence: float = Field(description="Confidence score")
    context_used: bool = Field(default=False, description="Whether context was used")

class ValueControl(BaseModel):
    """Schema for Value Agent responses"""
    type: str = Field(default="control_value", description="Response type")
    agent: str = Field(default="Value Agent", description="Agent name")
    intent: str = Field(description="Detected intent")
    target: str = Field(description="Control target (brightness, contrast, opacity)")
    value: int = Field(ge=0, le=100, description="Value to set (0-100)")
    message: str = Field(description="Human-readable message")
    confidence: float = Field(description="Confidence score")
    context_used: bool = Field(default=False, description="Whether context was used")

class ControlAction(str, Enum):
    CONTROL_ON = "control_on"
    CONTROL_OFF = "control_off"
    CONTROL_TOGGLE = "control_toggle"
    IMPLANT_SELECT = "implant_select"
    UNDO_ACTION = "undo_action"
    REDO_ACTION = "redo_action"

class ControlAgentResponse(BaseModel):
    """Schema for Control Agent responses"""
    type: ControlAction = Field(description="Control action type")
    agent: str = Field(default="Control Agent", description="Agent name")
    intent: str = Field(description="Detected intent")
    target: str = Field(description="Control target")
    message: str = Field(description="Human-readable message")
    implant_size: Optional[str] = Field(default=None, description="Implant size if applicable")
    confidence: float = Field(description="Confidence score")
    context_used: bool = Field(default=False, description="Whether context was used")

class InfoAgentResponse(BaseModel):
    """Schema for Info Agent responses"""
    type: str = Field(default="answer", description="Response type")
    agent: str = Field(default="Info Agent", description="Agent name")
    intent: str = Field(description="Detected intent")
    answer: str = Field(description="Information answer")
    confidence: float = Field(description="Confidence score")
    context_used: bool = Field(description="Whether context was used")
    sources: Optional[List[str]] = Field(default=None, description="Information sources")

