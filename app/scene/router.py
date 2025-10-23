from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.agent.langchain_supervisor import langchain_supervisor
from app.agent.info_agent import info_agent
from app.agent.notes_agent import notes_agent
from app.agent.value_agent import value_agent
from app.agent.control_agent import control_agent
from app.logging import confidence_logger


class DecisionRouter:
    """LangChain-based decision router that uses LLM supervisor for automatic agent selection."""
    
    def __init__(self):
        self.agents = {
            'info': info_agent,
            'notes': notes_agent,
            'value': value_agent,
            'control': control_agent
        }
    
    def route(self, text: str, session_id: str | None = None, conversation_history: List[Dict] = None, selected_agent: str = 'all') -> Dict[str, Any]:
        """
        Route user input using LangChain supervisor for automatic agent selection.
        Returns structured response from the selected agent.
        """
        try:
            print(f"Router processing: '{text}'")  # Debug log
            
            # 1. Use LangChain supervisor to select the best agent
            agent_name = langchain_supervisor.select_agent(text, conversation_history)
            print(f"Router selected agent: {agent_name}")  # Debug log
            
            # 2. Get the selected agent
            agent = self.agents.get(agent_name, info_agent)  # Default to info agent
            print(f"Router got agent: {agent.__class__.__name__}")  # Debug log
            
            # 3. Process the query with the selected agent
            response = agent.process(text, conversation_history, session_id)
            print(f"Router got response: {response}")  # Debug log
            
            # 4. Add session_id to response for agents that need it
            if session_id:
                response['session_id'] = session_id
            
            # 5. Log the response for confidence tracking
            self._log_response(text, response, agent_name)
            
            return response
            
        except Exception as e:
            print(f"Error in LangChain router: {e}")
            # Fallback to info agent
            return self._create_error_response(str(e))
    
    def _log_response(self, text: str, response: Dict[str, Any], agent_name: str) -> None:
        """Log the response for confidence tracking."""
        try:
            response_type = response.get('type', 'unknown')
            confidence = response.get('confidence', 0.0)
            
            if response_type == 'answer':
                confidence_logger.log_answer(
                    text,
                    response.get('answer', ''),
                    response.get('context_used', False),
                    confidence
                )
            elif response_type in ['control_on', 'control_off', 'control_toggle', 'control_value', 'implant_select', 'undo_action', 'redo_action']:
                confidence_logger.log_tool_action(
                    text,
                    'control',
                    {
                        'agent': agent_name,
                        'target': response.get('target', ''),
                        'value': response.get('value'),
                        'type': response_type
                    },
                    {'confidence': confidence}
                )
            elif response_type == 'note_action':
                confidence_logger.log_clarification(
                    text,
                    [response.get('message', '')],
                    {'confidence': confidence}
                )
        except Exception as e:
            print(f"Error logging response: {e}")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "type": "answer",
            "agent": "System",
            "intent": "error",
            "answer": f"I encountered an error processing your request: {error_message}. Please try again.",
            "confidence": 0.0,
            "context_used": False,
            "sources": []
        }
    
    def get_agent_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all available agents."""
        return langchain_supervisor.get_agent_descriptions()
    
    def explain_selection(self, query: str, selected_agent: str) -> str:
        """Explain why a particular agent was selected."""
        return langchain_supervisor.explain_selection(query, selected_agent)


# Global instance
decision_router = DecisionRouter()