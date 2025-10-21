from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional

import requests
from requests.adapters import HTTPAdapter, Retry
from flask import current_app
import os


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, timeout_seconds: int = 60) -> None:
        # Resolve base URL without requiring Flask app context
        resolved = base_url
        if not resolved:
            try:
                resolved = current_app.config.get("OLLAMA_HOST")  # type: ignore[attr-defined]
            except Exception:
                resolved = None
        if not resolved:
            resolved = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.base_url = resolved
        self.timeout_seconds = timeout_seconds

        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
        )
        self.session = requests.Session()
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        if not texts:
            return []
        # Resolve embedding model without requiring Flask app context
        model_name = model
        if not model_name:
            try:
                model_name = current_app.config.get("EMBEDDING_MODEL")  # type: ignore[attr-defined]
            except Exception:
                model_name = None
        if not model_name:
            model_name = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        url = f"{self.base_url}/api/embeddings"

        results: List[List[float]] = []
        for t in texts:
            # Ollama expects a single string in "prompt"; batch client-side
            payload = {"model": model_name, "prompt": t}
            resp = self.session.post(url, json=payload, timeout=self.timeout_seconds)
            resp.raise_for_status()
            data = resp.json()
            vec = data.get("embedding") or (data.get("embeddings") and data.get("embeddings")[0])
            if not isinstance(vec, list):
                raise ValueError("Unexpected embeddings response from Ollama")
            results.append(vec)
        return results

    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        model_name = model
        if not model_name:
            try:
                model_name = current_app.config.get("CHAT_MODEL")  # type: ignore[attr-defined]
            except Exception:
                model_name = None
        if not model_name:
            model_name = os.getenv("CHAT_MODEL", "llama3.1")
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
        }
        resp = self.session.post(url, json=payload, timeout=self.timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        # { message: { role: "assistant", content: "..." } }
        message = data.get("message", {})
        return message.get("content", "")


