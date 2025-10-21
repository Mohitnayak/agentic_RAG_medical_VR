from __future__ import annotations

from typing import Any, Dict, List

from flask import current_app

from ..llm.ollama_client import OllamaClient
from ..agent.parser import try_parse_action
from ..tools.registry import ToolRegistry


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


