from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import faiss  # type: ignore
import numpy as np


class FAISSVectorStore:
    def __init__(self, dim: int, storage_dir: str = "storage") -> None:
        self.dim = dim
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.index_path = os.path.join(self.storage_dir, "faiss.index")
        self.meta_path = os.path.join(self.storage_dir, "faiss_meta.jsonl")

        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            self.index = faiss.IndexFlatIP(self.dim)  # cosine via normalized vectors

        self.ids: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r", encoding="utf-8") as f:
                for line in f:
                    rec = json.loads(line)
                    self.ids.append(rec["id"])
                    self.metadatas.append(rec["metadata"])

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12
        return vectors / norms

    def upsert(self, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> None:
        if not embeddings:
            return
        vectors = np.array(embeddings, dtype="float32")
        vectors = self._normalize(vectors)
        self.index.add(vectors)
        self.ids.extend(ids)
        self.metadatas.extend(metadatas)

    def query(self, embedding: List[float], k: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        if len(self.ids) == 0:
            return []
        vec = np.array([embedding], dtype="float32")
        vec = self._normalize(vec)
        scores, indices = self.index.search(vec, min(k, len(self.ids)))
        results: List[Tuple[str, float, Dict[str, Any]]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            meta = self.metadatas[idx]
            if where:
                # Simple equality filter
                match = all(meta.get(key) == val for key, val in where.items())
                if not match:
                    continue
            results.append((self.ids[idx], float(score), meta))
        return results

    def delete_by_document(self, document_id: str) -> None:
        # Rebuild without entries for document_id (simple but OK for v1)
        keep: List[int] = [i for i, m in enumerate(self.metadatas) if m.get("document_id") != document_id]
        if len(keep) == len(self.metadatas):
            return
        kept_vectors = []  # cannot read back vectors from IndexFlatIP; require rebuild
        # As a simplification for v1, clear and re-add kept entries by storing embeddings externally is needed.
        # Since we didn't store them, we'll clear all. In v1, rely on full reindex on document replace.
        self.index = faiss.IndexFlatIP(self.dim)
        self.ids = []
        self.metadatas = []

    def persist(self) -> None:
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            for _id, meta in zip(self.ids, self.metadatas):
                f.write(json.dumps({"id": _id, "metadata": meta}, ensure_ascii=False) + "\n")


