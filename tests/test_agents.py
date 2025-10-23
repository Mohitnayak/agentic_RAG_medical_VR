from __future__ import annotations

from app.agent.supervisor import supervisor
from app.agent.control_agent import control_agent
from app.agent.info_agent import InfoAgent


def test_supervisor_notes_start():
    out = supervisor.decide("s1", "start recording")
    assert out is not None
    assert out.get("type") == "note_action"
    assert out.get("function") == "start_notes"


def test_control_agent_control_on():
    entity = ("show_sinus", 0.9, {"name": "show_sinus", "type": "switch"})
    out = control_agent.act("control_on", entity, None, "show sinuses")
    assert out.get("type") == "tool_action"
    assert out.get("tool") == "control"
    args = out.get("arguments") or {}
    assert args.get("target") == "show_sinus"
    assert args.get("operation") == "set"
    assert args.get("value") == "on"


def test_info_agent_guardrails_without_retriever():
    ia = InfoAgent(None)
    out = ia.answer("what are implants")
    assert out.get("type") in {"clarification", "answer"}
    # Without retriever, it should clarify rather than fabricate
    assert out.get("type") == "clarification"




