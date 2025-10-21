from __future__ import annotations

import uuid
from typing import Any, Dict

from flask import Blueprint, request

from .schemas import ChatRequest, IngestRequest, NotesAddRequest, NotesEndRequest, NotesStartRequest, validate_response
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


api_bp = Blueprint("api", __name__)


@api_bp.get("/v1/ping")
def api_ping():
    return {"status": "ok", "service": "agentic-rag", "version": 1}, 200


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

    # Use new decision router for intelligent routing
    router_response = decision_router.route(req.message)
    
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
        return out, 200
    
    return validated_response, 200


from .notes.manager import NotesManager

_notes = NotesManager()


@api_bp.post("/v1/notes/start")
def notes_start():
    body = NotesStartRequest(**request.get_json(force=True))
    _notes.start(body.sessionId)
    return {"ok": True}, 200


@api_bp.post("/v1/notes/add")
def notes_add():
    body = NotesAddRequest(**request.get_json(force=True))
    note = _notes.add(body.sessionId, body.text)
    return {"ok": True, "noteId": note.id}, 200


@api_bp.post("/v1/notes/end")
def notes_end():
    body = NotesEndRequest(**request.get_json(force=True))
    notes = _notes.end(body.sessionId)
    return {"ok": True, "finalized": [n.id for n in notes]}, 200


@api_bp.get("/v1/notes/<session_id>")
def notes_list(session_id: str):
    items = _notes.list(session_id)
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


