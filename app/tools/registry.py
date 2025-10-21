from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class ToolError(Exception):
    pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, schema: Dict[str, Any], handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        self._tools[name] = {
            "name": name,
            "description": description,
            "schema": schema,
            "handler": handler,
        }

    def spec_for_prompt(self) -> str:
        # Minimal schema rendering for prompt context
        specs = []
        for tool in self._tools.values():
            specs.append({"name": tool["name"], "description": tool["description"], "schema": tool["schema"]})
        return str(specs)

    def execute(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        tool = self._tools.get(name)
        if not tool:
            raise ToolError(f"Unknown tool: {name}")
        handler = tool["handler"]
        return handler(arguments)


