from __future__ import annotations

from typing import Dict, List, Any, Optional
from app.llm.ollama_client import OllamaClient


class LangChainSupervisor:
    """LLM-based supervisor agent that automatically selects the best agent for user queries."""
    
    def __init__(self):
        self.llm_client = OllamaClient()
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for agent selection."""
        return """You are a Supervisor Agent for a VR Dental Planning system.

Your job is to analyze user questions and determine which specialized agent should handle them.

IMPORTANT: Consider conversation context carefully. If the user is continuing a previous topic, route to the same agent type.

Available agents:
1. Info Agent: Questions about dental anatomy, definitions, locations, explanations
   - Examples: "What are sinuses?", "Where is the skull?", "Explain implants", "Tell me about dental procedures"
   
2. Notes Agent: Recording, documenting, note-taking, memory functions
   - Examples: "Take notes", "Record this", "Start recording", "Note this: patient prefers 4x11.5", "Stop recording"
   
3. Value Agent: Adjusting image properties like brightness, contrast, opacity
   - Examples: "Set brightness to 50", "Adjust contrast to 75%", "Change opacity to 80"
   
4. Control Agent: Toggling VR tools, overlays, selecting implants, undo/redo actions
   - Examples: "Show sinuses", "Turn on handles", "Pick up implant size 4x11.5", "Undo", "Toggle xray flashlight"
   - CRITICAL: If user mentions implant sizes, dimensions, or "give me implant", route to Control Agent
   - CRITICAL: If user says "I don't want that size" after implant selection, route to Control Agent

Context Rules:
- If previous message was about implants and user provides numbers, route to Control Agent
- If user says "I don't want that size" after implant selection, route to Control Agent  
- If user provides dimensions like "20, 30" after implant discussion, route to Control Agent
- Only route to Value Agent for explicit brightness/contrast/opacity requests
- For social responses like "thank you", "thanks", "ok", "okay", "got it", route to Info Agent for conversational response

Analyze the user's question and respond with ONLY the agent name: "info", "notes", "value", or "control"

Be precise and consider the primary intent of the user's request."""
    
    def select_agent(self, query: str, conversation_history: List[Dict] = None) -> str:
        """Select the best agent for handling the user query."""
        try:
            # Build context from conversation history
            context = ""
            if conversation_history and len(conversation_history) > 0:
                recent_history = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
                context = "Recent conversation:\n"
                for exchange in recent_history:
                    context += f"User: {exchange.get('user', '')}\n"
                    context += f"Agent: {exchange.get('response', '')}\n"
                context += "\n"
            
            # Create messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"{context}Current user query: {query}\n\nWhich agent should handle this?"}
            ]
            
            # Get LLM response
            response = self.llm_client.chat(messages).strip().lower()
            
            # Validate and return agent name
            valid_agents = ["info", "notes", "value", "control"]
            
            # Extract agent name from response
            for agent in valid_agents:
                if agent in response:
                    return agent
            
            # Fallback to info agent if no clear match
            return "info"
            
        except Exception as e:
            print(f"Error in supervisor agent selection: {e}")
            return "info"  # Safe fallback
    
    def get_agent_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all available agents."""
        return {
            "info": "Info Agent - Provides dental information, anatomy explanations, and definitions",
            "notes": "Notes Agent - Manages note-taking, recording, and documentation",
            "value": "Value Agent - Controls image properties like brightness, contrast, and opacity",
            "control": "Control Agent - Manages VR tools, overlays, implants, and system actions"
        }
    
    def explain_selection(self, query: str, selected_agent: str) -> str:
        """Explain why a particular agent was selected."""
        descriptions = self.get_agent_descriptions()
        agent_desc = descriptions.get(selected_agent, "Unknown agent")
        
        return f"Selected {selected_agent} agent because: {agent_desc}"


# Global instance
langchain_supervisor = LangChainSupervisor()

