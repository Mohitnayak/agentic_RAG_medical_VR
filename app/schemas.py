from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


# Request schemas for API endpoints
class ChatRequest(BaseModel):
    """Schema for chat API requests."""
    message: str = Field(description="User message")
    sessionId: str = Field(description="Session ID")


class IngestRequest(BaseModel):
    """Schema for ingest API requests."""
    payload: str = Field(description="Text content to ingest")
    sourceType: str = Field(description="Source type (e.g., 'text', 'file')")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Document metadata")


class NotesStartRequest(BaseModel):
    """Schema for starting notes."""
    sessionId: str = Field(description="Session ID")


class NotesAddRequest(BaseModel):
    """Schema for adding notes."""
    sessionId: str = Field(description="Session ID")
    text: str = Field(description="Note text")


class NotesEndRequest(BaseModel):
    """Schema for ending notes."""
    sessionId: str = Field(description="Session ID")


# Response schemas for validation
class ToolAction(BaseModel):
    """Schema for tool action responses."""
    type: str = Field(default="tool_action", description="Response type")
    tool: str = Field(description="Tool name")
    arguments: Dict[str, Any] = Field(description="Tool arguments")
    confidence: Optional[Dict[str, float]] = Field(default=None, description="Confidence scores")


class AnswerResponse(BaseModel):
    """Schema for answer responses."""
    type: str = Field(default="answer", description="Response type")
    message: str = Field(description="Answer text")
    context_used: bool = Field(description="Whether RAG context was used")
    confidence: Optional[float] = Field(default=None, description="Confidence score")


class ClarificationResponse(BaseModel):
    """Schema for clarification requests."""
    type: str = Field(default="clarification", description="Response type")
    message: str = Field(description="Clarification message")
    clarifications: List[str] = Field(description="Specific clarification questions")
    confidence: Optional[Dict[str, float]] = Field(default=None, description="Confidence scores")


class NoteAction(BaseModel):
    """Schema for note action responses."""
    type: str = Field(default="note_action", description="Response type")
    function: str = Field(description="Note function: start_notes, add_note, end_notes")
    text: Optional[str] = Field(default=None, description="Note text for add_note")


class ChatResponse(BaseModel):
    """Schema for chat API responses."""
    type: str = Field(description="Response type: tool_action, answer, or clarification")
    agent: Optional[str] = Field(default=None, description="Agent name")
    intent: Optional[str] = Field(default=None, description="Intent label")
    tool: Optional[str] = Field(default=None, description="Tool name (for tool_action)")
    arguments: Optional[Dict[str, Any]] = Field(default=None, description="Tool arguments (for tool_action)")
    answer: Optional[str] = Field(default=None, description="Answer text (for answer)")
    message: Optional[str] = Field(default=None, description="Response message")
    target: Optional[str] = Field(default=None, description="Target element (for control actions)")
    value: Optional[Union[str, int, float, List]] = Field(default=None, description="Value (for control actions)")
    function: Optional[str] = Field(default=None, description="Function name (for note actions)")
    note_text: Optional[str] = Field(default=None, description="Note text (for note actions)")
    context_used: Optional[bool] = Field(default=None, description="Whether RAG context was used (for answer)")
    clarifications: Optional[List[str]] = Field(default=None, description="Clarification questions (for clarification)")
    confidence: Optional[Union[float, Dict[str, float]]] = Field(default=None, description="Confidence scores")
    
    @validator('type')
    def validate_type(cls, v):
        valid_types = [
            'tool_action', 'answer', 'clarification', 'note_action',
            'control_on', 'control_off', 'control_toggle', 'control_value',
            'implant_select', 'undo_action', 'redo_action'
        ]
        if v not in valid_types:
            raise ValueError(f'type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('tool')
    def validate_tool(cls, v, values):
        if values.get('type') == 'tool_action' and not v:
            raise ValueError('tool is required for tool_action type')
        return v
    
    @validator('message')
    def validate_message(cls, v, values):
        if values.get('type') in ['answer', 'clarification'] and not v:
            raise ValueError('message is required for answer and clarification types')
        return v


class ControlArguments(BaseModel):
    """Schema for control tool arguments."""
    hand: str = Field(description="Hand: left, right, or none")
    target: str = Field(description="Target element")
    operation: str = Field(description="Operation: set or toggle")
    value: Optional[Union[str, float, Dict[str, float]]] = Field(default=None, description="Value to set")
    
    @validator('hand')
    def validate_hand(cls, v):
        if v not in ['left', 'right', 'none']:
            raise ValueError('hand must be left, right, or none')
        return v
    
    @validator('operation')
    def validate_operation(cls, v):
        if v not in ['set', 'toggle']:
            raise ValueError('operation must be set or toggle')
        return v


def validate_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize response using Pydantic schemas.
    Returns validated response or error details.
    """
    try:
        response_type = response.get('type')
        
        if response_type == 'tool_action':
            validated = ToolAction(**response)
        elif response_type == 'answer':
            validated = AnswerResponse(**response)
        elif response_type == 'clarification':
            validated = ClarificationResponse(**response)
        elif response_type == 'note_action':
            validated = NoteAction(**response)
        elif response_type in ['control_on', 'control_off', 'control_toggle', 'control_value', 'implant_select', 'undo_action', 'redo_action']:
            # For LangChain agent responses, use ChatResponse schema
            validated = ChatResponse(**response)
        else:
            return {"error": "Invalid response type", "original": response}
        
        return validated.dict()
    except Exception as e:
        return {"error": f"Validation failed: {str(e)}", "original": response}


def validate_control_arguments(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate control tool arguments.
    Returns validated arguments or error details.
    """
    try:
        validated = ControlArguments(**args)
        return validated.dict()
    except Exception as e:
        return {"error": f"Control validation failed: {str(e)}", "original": args}