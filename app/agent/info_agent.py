from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from app.agent.base_agent import BaseAgent
from app.rag.retriever import Retriever
from app.models import Chunk


class InfoAgent(BaseAgent):
    """LangChain-based Info Agent that provides dental information using LLM and context."""

    def __init__(self, retriever: Retriever | None = None) -> None:
        super().__init__("Info Agent", "info_agent.json")
        self.retriever = retriever

    def set_retriever(self, retriever: Retriever) -> None:
        self.retriever = retriever

    def _get_context_from_rag(self, query: str) -> str:
        """Get context from RAG system using the retriever."""
        if not self.retriever:
            return ""
        
        try:
            # Retrieve relevant chunks
            retrieved = self.retriever.retrieve(query, k=5)
            if not retrieved:
                return ""
            
            # Build chunk lookup
            chunk_ids = [item[0] for item in retrieved]
            chunks = Chunk.query.filter(Chunk.id.in_(chunk_ids)).all()
            chunk_lookup = {str(chunk.id): chunk.text for chunk in chunks}
            
            # Build context
            context = self.retriever.build_context(query, retrieved, chunk_lookup)
            return context
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return ""

    def _get_system_prompt(self) -> str:
        return """You are an Info Agent for a VR Dental Planning system.

Your role is to provide accurate, helpful information about dental anatomy, procedures, and VR environment components.

Key responsibilities:
- Answer questions about dental anatomy (sinuses, skull, teeth, implants, etc.)
- Explain VR environment components (handles, controls, tools)
- Provide definitions and explanations
- Help users understand dental procedures and planning
- Handle conversational responses like "thank you", "thanks", "ok", "okay"

Guidelines:
- Be concise but informative
- Use professional dental terminology when appropriate
- Reference the VR environment context when relevant
- If you don't know something, say so clearly
- Always ground your answers in the provided context when available
- For social responses like "thank you", respond naturally and briefly (e.g., "You're welcome!" or "Happy to help!")
- Don't repeat introductory information unless specifically asked

Respond with a JSON object matching the schema provided."""

    def _get_context_from_rag(self, query: str) -> str:
        """Get context from RAG system."""
        if self.retriever is None:
            return ""
        
        try:
            retrieved = self.retriever.retrieve(query, k=6)
            chunk_ids = [meta.get("chunk_id") for _, _, meta in retrieved]
            rows = Chunk.query.filter(Chunk.id.in_(chunk_ids)).all() if chunk_ids else []
            lookup = {c.id: c.text for c in rows}
            context = self.retriever.build_context(query, retrieved, lookup)
            return context or ""
        except Exception as e:
            print(f"Error retrieving RAG context: {e}")
            return ""

    def _validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the response."""
        validated = super()._validate_response(response)
        
        # Ensure required fields for Info Agent
        if 'message' not in validated:
            validated['message'] = validated.get('answer', 'No answer provided')
        
        if 'sources' not in validated:
            validated['sources'] = []
        
        return validated

    def get_agent_description(self) -> str:
        return "Info Agent - Provides dental information, anatomy explanations, and definitions"

    def process(self, query: str, conversation_history: List[Dict] = None, session_id: str = None) -> Dict[str, Any]:
        """Process a user query with special handling for conversational responses."""
        try:
            query_lower = query.lower().strip()
            
            # Handle conversational responses
            conversational_responses = {
                'thank you': "You're welcome! Happy to help with your dental planning.",
                'thanks': "You're welcome!",
                'ok': "Got it! Let me know if you need anything else.",
                'okay': "Got it! Let me know if you need anything else.",
                'got it': "Perfect! Feel free to ask if you have any questions.",
                'alright': "Great! I'm here if you need assistance.",
                'sure': "Excellent! What would you like to do next?",
                'yes': "Perfect! How can I help you further?",
                'no': "No problem! Let me know if you change your mind.",
                'good': "Great! Is there anything else you'd like to know?",
                'fine': "Wonderful! What would you like to explore next?"
            }
            
            # Check for exact matches or close matches
            for phrase, response in conversational_responses.items():
                if phrase in query_lower or query_lower == phrase:
                    return {
                        "type": "answer",
                        "agent": "Info Agent",
                        "intent": "conversational_response",
                        "message": response,
                        "confidence": 0.9,
                        "context_used": False,
                        "sources": []
                    }
            
            # For other queries, use the base class processing
            return super().process(query, conversation_history)
            
        except Exception as e:
            print(f"Error in Info Agent processing: {e}")
            return self._create_error_response(str(e))

    def answer_with_entity(
        self,
        intent_label: str,
        entity: Optional[Tuple[str, float, Dict[str, Any]]],
        text: str,
    ) -> Dict[str, Any]:
        """Legacy method for entity-based answers."""
        # Prefer deterministic entity metadata when available
        if entity:
            name, conf, data = entity
            canonical = data.get("name", name)
            if intent_label == "info_location":
                loc = data.get("location")
                if loc:
                    return {
                        "type": "answer",
                        "agent": "Info Agent",
                        "intent": intent_label,
                        "message": f"The {canonical} is located {loc}.",
                        "confidence": conf,
                        "context_used": False,
                        "sources": []
                    }
            if intent_label == "info_definition":
                definition = data.get("definition")
                if definition:
                    return {
                        "type": "answer",
                        "agent": "Info Agent",
                        "intent": intent_label,
                        "message": definition,
                        "confidence": conf,
                        "context_used": False,
                        "sources": []
                    }
        
        # Fall back to LLM-based answer
        return self.process(text)


# Global instance (retriever injected from routes)
info_agent = InfoAgent()


