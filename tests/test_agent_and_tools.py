from app.agent.parser import try_parse_action
from app.agent.planner import Agent
from app.tools.registry import ToolRegistry


def test_try_parse_action_valid():
    txt = "Use tool {\"tool\": \"activate_tool\", \"arguments\": {\"name\": \"X\", \"properties\": {\"color\": [\"blue\", \"red\"]}}} thanks"
    act = try_parse_action(txt)
    assert act is not None
    assert act.tool == "activate_tool"
    assert act.arguments["name"] == "X"


class DummyClient:
    def chat(self, messages):
        # Emit a tool action in JSON
        return '{"tool":"activate_tool","arguments":{"name":"Drill","properties":{"color":["blue","red"]}}}'


def test_agent_executes_tool(monkeypatch):
    from app.llm import ollama_client as oc
    monkeypatch.setattr(oc, 'OllamaClient', lambda *a, **k: DummyClient())

    from app.tools.activate import tool_spec
    reg = ToolRegistry()
    spec = tool_spec()
    reg.register(spec["name"], spec["description"], spec["schema"], spec["handler"])

    agent = Agent(reg)
    out = agent.respond("activate drill", "", False)
    assert out["type"] == "tool_result"
    assert out["tool"] == "activate_tool"

