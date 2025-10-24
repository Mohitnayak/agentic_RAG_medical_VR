from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from flask import current_app

from ..llm.ollama_client import OllamaClient
from ..tools.registry import ToolRegistry


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


SYSTEM_PROMPT = (
    "You are an agent for dental surgical planning."
    " Answer ONLY using the provided context."
    " If the user's question is outside context or domain, say you cannot answer and ask to provide relevant dental planning material."
    " If a tool needs to be used, respond ONLY with a JSON object of the form:"
    " {\"tool\": \"<tool_name>\", \"arguments\": { ... }}"
    " If notes are active, ask the user to provide note entries until they say 'end'."
    " Do not speculate or provide general world knowledge (e.g., geography)."
    " Avoid clinical diagnosis; educational guidance only."
)


class Agent:
    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.client = OllamaClient()
        self.tools = tool_registry

    def build_messages(self, user: str, context: str, notes_active: bool, tool_specs: str) -> List[Dict[str, str]]:
        sys = SYSTEM_PROMPT + f"\n\nAvailable tools: {tool_specs}"
        if notes_active:
            sys += "\nNotes are active. To add a note, ask the user to provide the note text."
        messages = [
            {"role": "system", "content": sys},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{user}"},
        ]
        return messages

    def respond(self, user: str, context: str, notes_active: bool, has_context: bool) -> Dict[str, Any]:
        tool_specs = self.tools.spec_for_prompt()
        messages = self.build_messages(user, context, notes_active, tool_specs)
        if not has_context:
            # Force refusal path with guidance if no supporting context
            messages.append({"role": "system", "content": "No supporting context available for this query. Refuse with guidance to ingest relevant dental planning documents."})
        output = self.client.chat(messages)
        action = try_parse_action(output)
        if action:
            try:
                result = self.tools.execute(action.tool, action.arguments)
                return {"type": "tool_result", "tool": action.tool, "result": result}
            except Exception as e:
                return {"type": "error", "error": str(e)}
        return {"type": "answer", "text": output}


