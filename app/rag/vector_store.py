from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Tuple


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def query(self, embedding: List[float], k: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Return list of (id, score, metadata) with higher score = closer."""
        raise NotImplementedError

    @abstractmethod
    def delete_by_document(self, document_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def persist(self) -> None:
        raise NotImplementedError


