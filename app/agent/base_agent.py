from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.llm.ollama_client import OllamaClient
from app.scene.context_loader import scene_context_loader


class BaseAgent(ABC):
    """Base class for all LangChain-based agents in the VR dental system."""
    
    def __init__(self, agent_name: str, schema_file: str):
        self.agent_name = agent_name
        self.schema_file = schema_file
        self.llm_client = OllamaClient()
        self.schema = self._load_schema()
        self.system_prompt = self._get_system_prompt()
        self.json_parser = JsonOutputParser()
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema for this agent."""
        schema_path = Path("config/schemas") / self.schema_file
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Schema file not found at {schema_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing schema file {schema_path}: {e}")
            return {}
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    def _get_context_from_scene_reference(self, query: str) -> str:
        """Get relevant context from scene_reference.md."""
        return scene_context_loader.search_context(query)
    
    def _get_context_from_rag(self, query: str) -> str:
        """Get context from RAG system (placeholder for now)."""
        # TODO: Integrate with existing RAG system
        return ""
    
    def _build_context(self, query: str, conversation_history: List[Dict] = None) -> str:
        """Build comprehensive context for the agent."""
        context_parts = []
        
        # Add scene reference context
        scene_context = self._get_context_from_scene_reference(query)
        if scene_context:
            context_parts.append(f"VR Scene Context:\n{scene_context}")
        
        # Add RAG context
        rag_context = self._get_context_from_rag(query)
        if rag_context:
            context_parts.append(f"Knowledge Base Context:\n{rag_context}")
        
        # Add conversation history
        if conversation_history and len(conversation_history) > 0:
            recent_history = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
            history_text = "Recent Conversation:\n"
            for exchange in recent_history:
                history_text += f"User: {exchange.get('user', '')}\n"
                history_text += f"Agent: {exchange.get('response', '')}\n"
            context_parts.append(history_text)
        
        return "\n\n".join(context_parts)
    
    def _create_messages(self, query: str, context: str) -> List[Dict[str, str]]:
        """Create messages for the LLM."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nUser Query: {query}\n\nRespond with ONLY a valid JSON object matching this schema: {json.dumps(self.schema)}\n\nDo not include any explanation, markdown formatting, or text outside the JSON object."}
        ]
        return messages
    
    def _validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the response against the schema."""
        # Basic validation - ensure required fields are present
        required_fields = ['type', 'agent', 'intent', 'confidence', 'context_used']
        for field in required_fields:
            if field not in response:
                if field == 'agent':
                    response[field] = self.agent_name
                elif field == 'confidence':
                    response[field] = 0.8
                elif field == 'context_used':
                    response[field] = True
                elif field == 'intent':
                    response[field] = 'general'
        
        return response
    
    def process(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Process a user query and return structured response."""
        try:
            # Build context
            context = self._build_context(query, conversation_history)
            
            # Create messages
            messages = self._create_messages(query, context)
            
            # Get LLM response
            llm_response = self.llm_client.chat(messages)
            
            # Parse JSON response - handle cases where LLM returns JSON wrapped in markdown or with extra text
            try:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    response_data = json.loads(json_str)
                else:
                    response_data = json.loads(llm_response)
            except json.JSONDecodeError:
                # Fallback if LLM doesn't return valid JSON
                response_data = self._create_fallback_response(query, llm_response)
            
            # Validate and return
            validated_response = self._validate_response(response_data)
            return validated_response
            
        except Exception as e:
            print(f"Error in {self.agent_name}: {e}")
            return self._create_error_response(str(e))
    
    def _create_fallback_response(self, query: str, llm_response: str) -> Dict[str, Any]:
        """Create a fallback response when LLM doesn't return valid JSON."""
        return {
            "type": "answer",
            "agent": self.agent_name,
            "intent": "general",
            "message": llm_response,
            "confidence": 0.5,
            "context_used": True
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "type": "answer",
            "agent": self.agent_name,
            "intent": "error",
            "message": f"I encountered an error: {error_message}",
            "confidence": 0.0,
            "context_used": False
        }
    
    @abstractmethod
    def get_agent_description(self) -> str:
        """Get a description of what this agent does."""
        pass
