from __future__ import annotations

from typing import Any, Dict

from app.config_loader import load_config


class TextNormalizer:
    """LLM-assisted text normalizer with config-driven schema.

    Falls back to identity when LLM is unavailable.
    """

    def __init__(self) -> None:
        self._prompt: str | None = None

    def _get_prompt(self) -> str:
        if self._prompt is None:
            cfg = load_config()
            self._prompt = (
                cfg.get("intent", {})
                .get("normalization", {})
                .get(
                    "prompt",
                    (
                        "You normalize user input for VR controls/QA. "
                        "Return compact JSON with fields: canonical_text (string). "
                        "Do not add commentary."
                    ),
                )
            )
        return self._prompt or ""

    def normalize(self, text: str) -> Dict[str, Any]:
        canonical = text.strip()
        try:
            # Best-effort call to Ollama if available
            from app.llm.ollama_client import OllamaClient

            prompt = self._get_prompt()
            messages = [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": f"Text: {text}\nReturn JSON with key canonical_text only.",
                },
            ]
            client = OllamaClient()
            out = client.chat(messages).strip()
            # Very lightweight parse: look for canonical_text
            import json as _json

            data = _json.loads(out) if out.startswith("{") else {}
            canonical = str(data.get("canonical_text") or canonical)
        except Exception:
            # Silent fallback to identity
            pass
        return {"canonical_text": canonical}


# Global instance
normalizer = TextNormalizer()



