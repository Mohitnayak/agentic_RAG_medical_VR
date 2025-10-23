from __future__ import annotations

import uuid
from typing import Any, Dict

from flask import Blueprint, request, Response
from time import sleep

from .schemas import ChatRequest, IngestRequest, NotesAddRequest, NotesEndRequest, NotesStartRequest, validate_response, validate_control_arguments
from .scene.router import decision_router
from .models import db, Chunk, Document
from .rag.chunker import split_text
from .llm.ollama_client import OllamaClient
from .rag.faiss_store import FAISSVectorStore
from .rag.retriever import Retriever
from .tools.registry import ToolRegistry
from .tools.activate import tool_spec as activate_tool_spec
from .tools.control import tool_spec as control_tool_spec
from .agent.planner import Agent
from .agent.info_agent import info_agent


api_bp = Blueprint("api", __name__)


@api_bp.get("/v1/ping")
def api_ping():
    return {"status": "ok", "service": "agentic-rag", "version": 1}, 200


# Simple in-memory log buffer for demo SSE streaming
_log_messages: list[str] = []


def _sse_format(data: str) -> str:
    return f"data: {data}\n\n"


@api_bp.post("/v1/scene/log")
def scene_log_add():
    payload = request.get_json(force=True) or {}
    msg = str(payload.get("message") or "")
    if not msg:
        return {"ok": False, "error": "empty message"}, 400
    _log_messages.append(msg)
    # Truncate to last 200
    if len(_log_messages) > 200:
        del _log_messages[:-200]
    return {"ok": True}, 200


@api_bp.get("/v1/scene/logs")
def scene_logs_stream():
    def event_stream():
        idx = 0
        while True:
            while idx < len(_log_messages):
                yield _sse_format(_log_messages[idx])
                idx += 1
            sleep(0.5)
    return Response(event_stream(), mimetype="text/event-stream")


# Initialize singletons lazily
_vector_store: FAISSVectorStore | None = None
_retriever: Retriever | None = None
_agent: Agent | None = None
_tools: ToolRegistry | None = None


def _ensure_services() -> None:
    global _vector_store, _retriever, _agent, _tools
    if _tools is None:
        _tools = ToolRegistry()
        spec = activate_tool_spec()
        _tools.register(spec["name"], spec["description"], spec["schema"], spec["handler"])
        spec2 = control_tool_spec()
        _tools.register(spec2["name"], spec2["description"], spec2["schema"], spec2["handler"])
    if _vector_store is None:
        # embedding dim for nomic-embed-text is typically 768
        _vector_store = FAISSVectorStore(dim=768)
    if _retriever is None:
        _retriever = Retriever(_vector_store, embedding_dim=768)
        # Inject retriever into InfoAgent for domain-gated answers
        info_agent.set_retriever(_retriever)
    if _agent is None:
        _agent = Agent(_tools)


@api_bp.post("/v1/ingest")
def ingest():
    _ensure_services()
    data = IngestRequest(**request.get_json(force=True))
    doc_id = str(uuid.uuid4())
    doc = Document(id=doc_id, source_type=data.sourceType, title=data.metadata.get("title") if data.metadata else None, domain=data.metadata.get("domain") if data.metadata else None)
    db.session.add(doc)
    chunks = split_text(data.payload)

    # Persist chunk texts in DB; embeddings go to vector store
    client = OllamaClient()
    embeddings = client.embed(chunks)
    ids = []
    metadatas = []
    for idx, text in enumerate(chunks):
        chunk_id = str(uuid.uuid4())
        ids.append(chunk_id)
        db.session.add(Chunk(id=chunk_id, document_id=doc_id, text=text, meta={"document_id": doc_id, "idx": idx}))
        metadatas.append({"document_id": doc_id, "chunk_id": chunk_id, "idx": idx})
    db.session.commit()

    assert _vector_store is not None
    _vector_store.upsert(ids, embeddings, metadatas)
    _vector_store.persist()
    return {"ok": True, "documentId": doc_id, "chunks": len(chunks)}, 200


@api_bp.post("/v1/chat")
def chat():
    _ensure_services()
    req = ChatRequest(**request.get_json(force=True))
    
    # Extract conversation history from request (agent selection is now automatic)
    conversation_history = request.get_json(force=True).get('conversation_history', [])

    # Use new decision router for intelligent routing with conversation context
    router_response = decision_router.route(
        req.message, 
        session_id=req.sessionId,
        conversation_history=conversation_history,
        selected_agent='all'  # Always use automatic agent selection
    )
    
    # Validate response using Pydantic schemas
    validated_response = validate_response(router_response)
    
    if "error" in validated_response:
        # Fallback to RAG if validation fails
        assert _retriever is not None and _vector_store is not None and _agent is not None
        retrieved = _retriever.retrieve(req.message, k=6)
        chunk_ids = [meta.get("chunk_id") for _, _, meta in retrieved]
        rows = Chunk.query.filter(Chunk.id.in_(chunk_ids)).all() if chunk_ids else []
        lookup = {c.id: c.text for c in rows}
        context = _retriever.build_context(req.message, retrieved, lookup)
        has_context = len(context.strip()) > 0
        
        from .models import Note
        notes_active = db.session.query(Note.id).filter_by(session_id=req.sessionId, finalized=False).first() is not None
        out = _agent.respond(req.message, context, notes_active, has_context)
        # Normalize tool_result into user-friendly reply
        if isinstance(out, dict) and out.get("type") == "tool_result":
            result = out.get("result", {}) or {}
            ok = bool(result.get("ok"))
            if ok:
                applied = result.get("applied", {}) or {}
                target = str(applied.get("target") or "target").replace("_", " ")
                operation = applied.get("operation")
                value = applied.get("value")
                narration = None
                try:
                    client = OllamaClient()
                    action_desc = f"operation='{operation}', target='{target}', value='{value}'"
                    prompt = (
                        "You are a concise assistant in a VR dental planning app.\n"
                        "Given the action that was performed, produce ONE short confirmation line to the user.\n"
                        "Be clear and natural; do not add extra explanations.\n\n"
                        f"User message: {req.message}\n"
                        f"Action: {action_desc}\n\n"
                        "Reply with one sentence only."
                    )
                    narration = client.chat(prompt).strip()
                except Exception:
                    narration = None

                if not narration:
                    if operation == "set" and isinstance(value, str) and value in {"on", "off"}:
                        narration = f"The {target} is now {value}."
                    elif operation == "set" and isinstance(value, (int, float)):
                        narration = f"Setting {target} to {value}."
                    elif operation == "toggle":
                        narration = f"Toggling {target}."
                    else:
                        if isinstance(value, str) and value in {"on", "off"}:
                            narration = f"Turned {value} {target}."
                        elif isinstance(value, (int, float)):
                            narration = f"Setting {target} to {value}."
                        else:
                            narration = f"Applied {operation or 'action'} to {target}."

                return {"type": "answer", "answer": narration, "context_used": False}, 200
            else:
                err = str(result.get("error") or "I couldn't apply that request.")
                clarifications = []
                if "value must be a number" in err:
                    clarifications = ["Provide a number, e.g., 'set brightness to 50'"]
                elif "unknown target" in err:
                    clarifications = ["Specify a control like brightness or contrast"]
                elif "left hand cannot control" in err:
                    clarifications = ["Use right hand controls for this element"]
                return {
                    "type": "clarification",
                    "message": err,
                    "clarifications": clarifications or ["Could you clarify the exact element and value?"],
                }, 200
        return out, 200
    
    # If router asks for clarification, try answering via RAG automatically using available context
    if validated_response.get("type") == "clarification":
        assert _retriever is not None and _vector_store is not None and _agent is not None
        retrieved = _retriever.retrieve(req.message, k=6)
        chunk_ids = [meta.get("chunk_id") for _, _, meta in retrieved]
        rows = Chunk.query.filter(Chunk.id.in_(chunk_ids)).all() if chunk_ids else []
        lookup = {c.id: c.text for c in rows}
        context = _retriever.build_context(req.message, retrieved, lookup)
        has_context = len(context.strip()) > 0
        
        from .models import Note
        notes_active = db.session.query(Note.id).filter_by(session_id=req.sessionId, finalized=False).first() is not None
        out = _agent.respond(req.message, context, notes_active, has_context)
        # If no useful context, return a clear LLM-style apology/intent and include original clarifications
        if not has_context:
            return {
                "type": "clarification",
                "message": "I couldn't find enough context to answer directly. Could you specify a bit more?",
                "clarifications": validated_response.get("clarifications", []),
                "confidence": validated_response.get("confidence", {})
            }, 200
        # Normalize tool_result into user-friendly reply
        if isinstance(out, dict) and out.get("type") == "tool_result":
            result = out.get("result", {}) or {}
            ok = bool(result.get("ok"))
            if ok:
                applied = result.get("applied", {}) or {}
                target = str(applied.get("target") or "target").replace("_", " ")
                operation = applied.get("operation")
                value = applied.get("value")
                narration = None
                try:
                    client = OllamaClient()
                    action_desc = f"operation='{operation}', target='{target}', value='{value}'"
                    prompt = (
                        "You are a concise assistant in a VR dental planning app.\n"
                        "Given the action that was performed, produce ONE short confirmation line to the user.\n"
                        "Be clear and natural; do not add extra explanations.\n\n"
                        f"User message: {req.message}\n"
                        f"Action: {action_desc}\n\n"
                        "Reply with one sentence only."
                    )
                    narration = client.chat(prompt).strip()
                except Exception:
                    narration = None

                if not narration:
                    if operation == "set" and isinstance(value, str) and value in {"on", "off"}:
                        narration = f"The {target} is now {value}."
                    elif operation == "set" and isinstance(value, (int, float)):
                        narration = f"Setting {target} to {value}."
                    elif operation == "toggle":
                        narration = f"Toggling {target}."
                    else:
                        if isinstance(value, str) and value in {"on", "off"}:
                            narration = f"Turned {value} {target}."
                        elif isinstance(value, (int, float)):
                            narration = f"Setting {target} to {value}."
                        else:
                            narration = f"Applied {operation or 'action'} to {target}."

                return {"type": "answer", "answer": narration, "context_used": False}, 200
            else:
                err = str(result.get("error") or "I couldn't apply that request.")
                clarifications = []
                if "value must be a number" in err:
                    clarifications = ["Provide a number, e.g., 'set brightness to 50'"]
                elif "unknown target" in err:
                    clarifications = ["Specify a control like brightness or contrast"]
                elif "left hand cannot control" in err:
                    clarifications = ["Use right hand controls for this element"]
                return {
                    "type": "clarification",
                    "message": err,
                    "clarifications": clarifications or ["Could you clarify the exact element and value?"],
                }, 200
        return out, 200

    # For tool actions, perform a dry validation of arguments; on failure, use RAG + LLM to reply naturally
    if validated_response.get("type") == "tool_action":
        args = validated_response.get("arguments") or {}
        arg_check = validate_control_arguments(args)
        if "error" in arg_check:
            assert _retriever is not None and _vector_store is not None and _agent is not None
            # Friendly preamble then try to answer via RAG
            retrieved = _retriever.retrieve(req.message, k=6)
            chunk_ids = [meta.get("chunk_id") for _, _, meta in retrieved]
            rows = Chunk.query.filter(Chunk.id.in_(chunk_ids)).all() if chunk_ids else []
            lookup = {c.id: c.text for c in rows}
            context = _retriever.build_context(req.message, retrieved, lookup)
            has_context = len(context.strip()) > 0
            from .models import Note
            notes_active = db.session.query(Note.id).filter_by(session_id=req.sessionId, finalized=False).first() is not None
            out = _agent.respond(req.message, context, notes_active, has_context)
            if not has_context:
                # Polite, natural reply with guidance
                target = args.get("target") or "this"
                return {
                    "type": "clarification",
                    "message": f"I couldn't validate the request for {target}. Let me check my knowledge base... I couldn't find enough context. What exact value/element should I use?",
                    "clarifications": [
                        "For values: try a number, e.g., 'set brightness to 50'",
                        "For overlays: e.g., 'turn on sinus overlay'",
                    ],
                    "confidence": {"intent": 0.7, "entity": 0.3, "value": 0.2}
                }, 200
            return out, 200
    
    # Add natural-language narration and function/state for successful tool actions
    if validated_response.get("type") == "tool_action":
        args = (validated_response.get("arguments") or {}).copy()
        target = str(args.get("target") or "target").replace("_", " ")
        operation = args.get("operation")
        value = args.get("value")
        # Try LLM-based acknowledgement first; fall back to template
        narration = None
        try:
            client = OllamaClient()
            action_desc = (
                f"operation='{operation}', target='{target}', value='{value}'"
            )
            prompt = (
                "You are a concise assistant in a VR dental planning app.\n"
                "Given the action that will be performed, produce ONE short confirmation line to the user.\n"
                "Be clear and natural; do not add extra explanations.\n\n"
                f"User message: {req.message}\n"
                f"Action: {action_desc}\n\n"
                "Reply with one sentence only."
            )
            narration = client.chat(prompt).strip()
        except Exception:
            narration = None

        if not narration:
            # Template fallback
            if operation == "set" and isinstance(value, str) and value in {"on", "off"}:
                narration = f"Turned {value} {target}."
            elif operation == "set" and isinstance(value, (int, float)):
                narration = f"Setting {target} to {value}."
            elif operation == "toggle":
                narration = f"Toggling {target}."

        if narration:
            enriched = dict(validated_response)
            # Add function/state fields per action UX contract
            if operation == "set" and isinstance(value, str) and value in {"on", "off"}:
                enriched["function"] = f"switch {target}"
                enriched["state"] = value
            elif operation == "set" and isinstance(value, (int, float)):
                enriched["function"] = f"set {target}"
                enriched["state"] = value
            elif operation == "toggle":
                enriched["function"] = f"toggle {target}"
                enriched["state"] = "toggle"
            enriched["answer"] = narration
            return enriched, 200

    # Standardize the response format for the chatbot
    # Always use "message" field for consistency
    response_text = (
        validated_response.get("answer")
        or validated_response.get("message")
        or validated_response.get("response")
    )
    if not response_text:
        if validated_response.get('type') in ['control_on', 'control_off', 'control_toggle', 'control_value', 'implant_select', 'undo_action', 'redo_action']:
            response_text = f"Executed {validated_response.get('type', 'action')}"
        else:
            response_text = "No response generated"
    
    standardized_response = {
        "agent": validated_response.get("agent", "Dental AI"),
        "intent": validated_response.get("intent", "General Response"),
        "message": response_text,  # Always use "message" field
        "confidence": validated_response.get("confidence", {}),
        "json_output": validated_response,
        "session_id": req.sessionId,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }
    
    return standardized_response, 200


from .notes.service import notes_service


@api_bp.post("/v1/notes/start")
def notes_start():
    body = NotesStartRequest(**request.get_json(force=True))
    notes_service.start(body.sessionId)
    return {"ok": True}, 200


@api_bp.post("/v1/notes/add")
def notes_add():
    body = NotesAddRequest(**request.get_json(force=True))
    note = notes_service.add(body.sessionId, body.text)
    return {"ok": True, "noteId": note.id}, 200


@api_bp.post("/v1/notes/end")
def notes_end():
    body = NotesEndRequest(**request.get_json(force=True))
    notes = notes_service.end(body.sessionId)
    return {"ok": True, "finalized": [n.id for n in notes]}, 200


@api_bp.get("/v1/notes/<session_id>")
def notes_list(session_id: str):
    items = notes_service.list(session_id)
    return {"ok": True, "notes": [{"id": n.id, "text": n.text, "finalized": n.finalized, "createdAt": n.created_at.isoformat()} for n in items]}, 200


@api_bp.get("/v1/docs")
def list_docs():
    docs = Document.query.order_by(Document.created_at.desc()).all()
    results = []
    for d in docs:
        count = Chunk.query.filter_by(document_id=d.id).count()
        results.append({
            "id": d.id,
            "title": d.title,
            "domain": d.domain,
            "sourceType": d.source_type,
            "createdAt": d.created_at.isoformat(),
            "numChunks": count,
        })
    return {"ok": True, "documents": results}, 200


@api_bp.get("/v1/docs/<doc_id>/chunks")
def list_doc_chunks(doc_id: str):
    chunks = Chunk.query.filter_by(document_id=doc_id).order_by(Chunk.id.asc()).all()
    return {
        "ok": True,
        "chunks": [{"id": c.id, "preview": c.text[:400]} for c in chunks],
    }, 200


