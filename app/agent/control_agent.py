from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from app.agent.base_agent import BaseAgent
from app.config_loader import load_config


class ControlAgent(BaseAgent):
    """LangChain-based Control Agent that manages VR tools, overlays, implants, and system actions."""

    def __init__(self) -> None:
        super().__init__("Control Agent", "control_agent.json")

    def _get_system_prompt(self) -> str:
        return """You are a Control Agent for a VR Dental Planning system.

Your role is to manage VR tools, overlays, implants, and system actions.

Key responsibilities:
- Toggle VR tools and overlays (handles, sinuses, xray flashlight, etc.)
- Select dental implants by size
- Execute undo/redo actions
- Control system functions

Available action types:
- control_on: Turn on/toggle on a feature
- control_off: Turn off/toggle off a feature  
- control_toggle: Toggle a feature on/off
- implant_select: Select an implant by size (e.g., "4x11.5")
- undo_action: Undo last action
- redo_action: Redo last action

Available targets:
- handles: On-screen manipulation controls
- show_sinus: Sinus overlay display
- show_nerve: Nerve overlay display
- xray_flashlight: X-ray flashlight tool
- align_implants: Implant alignment tool
- implant_[size]: Specific implant selection (e.g., "implant_4x11.5")
- implant_removed: When removing implants

State tracking:
- "present": Implant is active/visible in the scene
- "absent": Implant is removed/hidden from the scene
- "selected": Implant is selected but not yet placed (for future use)

Guidelines:
- Determine action type from user intent (on/off/toggle/select/undo/redo)
- Extract target from user input
- For implants, extract size and format as "implant_[height]x[length]"
- Include "state" field: "present" for adding implants, "absent" for removing implants
- Use flexible value field: single values for toggles, arrays for implant sizes
- Provide clear confirmation messages

Respond with a JSON object matching the schema provided."""

    def _parse_implant_size(self, query: str) -> Dict[str, Any]:
        """Parse implant size from user query."""
        import re
        query_lower = query.lower()
        
        # Look for size patterns like "10x3", "4 x 11.5", "size 3.5x8"
        size_patterns = [
            r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)',  # "10x3", "4 x 11.5"
            r'size\s+(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)',  # "size 10x3"
            r'(\d+(?:\.\d+)?)\s*by\s*(\d+(?:\.\d+)?)',  # "10 by 3"
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, query_lower)
            if match:
                height = float(match.group(1))
                length = float(match.group(2))
                return {
                    'height': height,
                    'length': length,
                    'target': f'implant_{height}x{length}',
                    'value': [height, length]
                }
        
        # Default fallback
        return {
            'height': 4.0,
            'length': 11.5,
            'target': 'implant_4x11.5',
            'value': [4.0, 11.5]
        }

    def _validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the response."""
        validated = super()._validate_response(response)
        
        # Ensure required fields for Control Agent
        if 'target' not in validated:
            validated['target'] = 'handles'  # Default
        
        if 'value' not in validated:
            validated['value'] = None  # Default
        
        # Add state field for implant-related responses
        if validated.get('type') == 'implant_select' and 'state' not in validated:
            validated['state'] = 'present'  # Default to present for implant selections
        
        return validated

    def process(self, query: str, conversation_history: List[Dict] = None, session_id: str = None) -> Dict[str, Any]:
        """Process a user query with special handling for implant selection."""
        try:
            query_lower = query.lower()
            
            # Check for implant removal requests
            if any(phrase in query_lower for phrase in ['remove implant', 'delete implant', 'take away implant', 'hide implant', 'no implant']):
                return {
                    "type": "implant_select",
                    "agent": "Control Agent",
                    "intent": "remove_implant",
                    "target": "implant_removed",
                    "value": None,
                    "message": "Removing current implant from the scene.",
                    "state": "absent",  # Implant is now absent/removed
                    "confidence": 0.9,
                    "context_used": False
                }
            
            # Check for size rejection or new size request
            if any(phrase in query_lower for phrase in ['i do not want', "don't want", 'not that size', 'different size', 'another size']):
                # Look for new dimensions in the query
                parsed = self._parse_implant_size(query)
                if parsed['height'] != 4.0 or parsed['length'] != 11.5:  # Different from default
                    return {
                        "type": "implant_select",
                        "agent": "Control Agent",
                        "intent": "select_new_implant_size",
                        "target": parsed['target'],
                        "value": parsed['value'],
                        "message": f"Selecting new implant size {parsed['height']}x{parsed['length']} instead.",
                        "state": "present",  # New implant is now present
                        "confidence": 0.9,
                        "context_used": True
                    }
                else:
                    return {
                        "type": "answer",
                        "agent": "Control Agent",
                        "intent": "clarify_implant_size",
                        "message": "I understand you don't want that implant size. Please specify the dimensions you prefer (height x length), for example: '4.5 x 12' or '3.5 x 10'.",
                        "confidence": 0.8,
                        "context_used": True
                    }
            
            # Check if this is an implant selection request
            if any(keyword in query_lower for keyword in ['implant', 'give me', 'pick up', 'select']):
                # Parse implant size
                parsed = self._parse_implant_size(query)
                
                return {
                    "type": "implant_select",
                    "agent": "Control Agent",
                    "intent": "select_implant",
                    "target": parsed['target'],
                    "value": parsed['value'],
                    "message": f"Selecting implant of size {parsed['height']}x{parsed['length']}.",
                    "state": "present",  # Implant is now present/active
                    "confidence": 0.9,
                    "context_used": False
                }
            
            # Check if user provided just numbers (likely implant dimensions)
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', query)
            if len(numbers) >= 2 and conversation_history:
                # Check if recent conversation was about implants
                recent_context = ' '.join([ex.get('user', '') + ' ' + ex.get('response', '') for ex in conversation_history[-2:]])
                if 'implant' in recent_context.lower():
                    height = float(numbers[0])
                    length = float(numbers[1])
                    return {
                        "type": "implant_select",
                        "agent": "Control Agent",
                        "intent": "select_implant_from_dimensions",
                        "target": f'implant_{height}x{length}',
                        "value": [height, length],
                        "message": f"Selecting implant of size {height}x{length}.",
                        "state": "present",  # Implant is now present/active
                        "confidence": 0.9,
                        "context_used": True
                    }
            
            # For other control commands, use the base class processing
            return super().process(query, conversation_history)
            
        except Exception as e:
            print(f"Error in Control Agent processing: {e}")
            return self._create_error_response(str(e))

    def get_agent_description(self) -> str:
        return "Control Agent - Manages VR tools, overlays, implants, and system actions"

    # Legacy method for backward compatibility
    def act(
        self,
        intent_label: str,
        entity: Optional[Tuple[str, float, Dict[str, Any]]],
        value_result: Optional[Tuple[float, float]],
        text: str,
    ) -> Dict[str, Any]:
        if not entity:
            return {
                "type": "control_on",
                "agent": "Control Agent",
                "intent": "clarification",
                "target": "handles",
                "value": None,
                "message": "Which element would you like to control?",
                "confidence": 0.0,
                "context_used": False,
            }

        entity_name, entity_conf, entity_data = entity
        canonical_target = entity_data.get("name", entity_name)

        operation = "toggle"
        value: Any = None
        action_type = "control_toggle"
        
        if intent_label == "control_on":
            operation = "set"
            value = "on"
            action_type = "control_on"
        elif intent_label == "control_off":
            operation = "set"
            value = "off"
            action_type = "control_off"
        elif intent_label == "control_value" and value_result:
            operation = "set"
            value = value_result[0]
            action_type = "control_value"
        elif intent_label == "control_value" and not value_result:
            # Ask for missing value using ranges
            try:
                cfg = load_config()
                ranges_cfg = cfg.get("ranges", {})
                r = ranges_cfg.get(canonical_target, {})
                r_min = r.get("min")
                r_max = r.get("max")
                range_hint = (
                    f" ({r_min}–{r_max})" if r_min is not None and r_max is not None else ""
                )
            except Exception:
                range_hint = ""
            return {
                "type": "control_value",
                "agent": "Control Agent",
                "intent": "clarification",
                "target": canonical_target,
                "value": None,
                "message": f"What value should I set for {canonical_target}{range_hint}?",
                "confidence": entity_conf,
                "context_used": False,
            }

        return {
            "type": action_type,
            "agent": "Control Agent",
            "intent": intent_label,
            "target": canonical_target,
            "value": value,
            "message": f"Executing {action_type} on {canonical_target}",
            "confidence": entity_conf,
            "context_used": False,
        }


# Global instance
control_agent = ControlAgent()


