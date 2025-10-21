from __future__ import annotations

from typing import Any, Dict, List, Tuple

from flask import current_app

from ..llm.ollama_client import OllamaClient
from ..models import Chunk, db
from ..config_loader import load_config
from .vector_store import VectorStore


class Retriever:
    def __init__(self, vector_store: VectorStore, embedding_dim: int = 768) -> None:
        self.vector_store = vector_store
        self.embedding_dim = embedding_dim
        self.client = OllamaClient()
        self._config = None

    def _get_config(self) -> Dict[str, Any]:
        """Load retrieval config."""
        if self._config is None:
            config = load_config()
            self._config = config.get("retrieval", {})
        return self._config

    def embed_query(self, query: str) -> List[float]:
        vecs = self.client.embed([query])
        return vecs[0]

    def retrieve(self, query: str, k: int = 6, where: Dict[str, Any] | None = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        config = self._get_config()
        hybrid_weights = config.get("hybrid_weights", {"semantic": 0.7, "lexical": 0.3})
        top_k_config = config.get("top_k", {"semantic": 10, "lexical": 5, "final": 8})
        
        semantic_weight = hybrid_weights.get("semantic", 0.7)
        lexical_weight = hybrid_weights.get("lexical", 0.3)
        semantic_k = top_k_config.get("semantic", 10)
        lexical_k = top_k_config.get("lexical", 5)
        final_k = top_k_config.get("final", 8)

        # Semantic candidates
        q = self.embed_query(query)
        sem = self.vector_store.query(q, k=max(k, semantic_k), where=where)

        # Lexical candidates (simple BM25-ish proxy via term overlap)
        lex_scores: Dict[str, float] = self._lexical_scores(query, limit=lexical_k)

        # Combine by normalized score
        combined: List[Tuple[str, float, Dict[str, Any]]] = []
        if not sem:
            # Fall back to lexical-only by fetching metas
            for cid, ls in sorted(lex_scores.items(), key=lambda x: x[1], reverse=True)[:k]:
                combined.append((cid, ls, {"chunk_id": cid}))
            return combined

        max_sem = max((s for _, s, _ in sem), default=1.0) or 1.0
        for cid, s, meta in sem:
            ns = float(s) / max_sem
            ls = lex_scores.get(meta.get("chunk_id") or meta.get("id") or cid, 0.0)
            score = semantic_weight * ns + lexical_weight * ls
            combined.append((cid, score, meta))

        combined.sort(key=lambda x: x[1], reverse=True)
        return combined[:final_k]

    def _lexical_scores(self, query: str, limit: int = 24) -> Dict[str, float]:
        # tokenize simple words, filter short/common
        import re

        tokens = [t for t in re.findall(r"[a-zA-Z]+", query.lower()) if len(t) >= 3]
        if not tokens:
            return {}
        # Query chunks with LIKE on any token
        # Note: simplistic and SQLite-friendly; adequate for MVP
        q = db.session.query(Chunk.id, Chunk.text)
        # Limit scan size by sampling most recent chunks
        q = q.order_by(Chunk.id.desc()).limit(500)
        scores: Dict[str, float] = {}
        for cid, text in q:
            t_low = (text or "").lower()
            hits = sum(1 for tok in tokens if tok in t_low)
            if hits > 0:
                # normalize by token count
                scores[cid] = min(1.0, hits / max(1, len(tokens)))
        # keep top N
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit])

    def build_context(self, query: str, retrieved: List[Tuple[str, float, Dict[str, Any]]], chunk_lookup: Dict[str, str], max_chars: int = 3500) -> str:
        parts: List[str] = []
        seen: set[str] = set()
        for chunk_id, score, meta in retrieved:
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            text = chunk_lookup.get(chunk_id)
            if not text:
                continue
            parts.append(text)
            joined = "\n\n".join(parts)
            if len(joined) >= max_chars:
                break
        return "\n\n".join(parts)


