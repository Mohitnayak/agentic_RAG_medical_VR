from __future__ import annotations

from typing import Any, List, Tuple


class Guardrails:
    """Content filtering and safety checks for responses."""
    
    def __init__(self):
        pass
    
    def allow_answer(self, context: str | None, retrieved: List[Tuple[float, str, dict[str, Any]]]) -> bool:
        """Check if we have sufficient context to provide an answer."""
        if not context or len(context.strip()) < 10:
            return False
        
        # Require at least some retrieved chunks
        if not retrieved or len(retrieved) == 0:
            return False
            
        # Check if any retrieved chunks have reasonable similarity scores
        if retrieved and all(score < 0.3 for score, _, _ in retrieved):
            return False
            
        return True
    
    def filter_content(self, text: str) -> str:
        """Basic content filtering - placeholder for future enhancements."""
        return text.strip()


# Global instance
guardrails = Guardrails()

