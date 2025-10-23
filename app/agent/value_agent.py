from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from app.agent.base_agent import BaseAgent
from app.config_loader import load_config


class ValueAgent(BaseAgent):
    """LangChain-based Value Agent that controls image properties like brightness, contrast, and opacity."""

    def __init__(self) -> None:
        super().__init__("Value Agent", "value_agent.json")

    def _get_system_prompt(self) -> str:
        return """You are a Value Agent for a VR Dental Planning system.

Your role is to control image properties and visual settings in the VR environment.

Key responsibilities:
- Adjust brightness (0-100)
- Adjust contrast (0-100) 
- Adjust opacity/transparency (0-100)
- Handle increase/decrease commands
- Validate value ranges
- Provide clear feedback on changes

Available targets:
- brightness: Controls overall image brightness
- contrast: Controls image contrast
- opacity: Controls transparency/opacity

Command types:
1. Set specific value: "set brightness to 50", "contrast 75"
2. Increase/decrease: "increase contrast", "decrease brightness", "lower opacity"
3. Increase/decrease by amount: "increase brightness by 10", "decrease contrast by 5"

Guidelines:
- Extract target (brightness/contrast/opacity) from user input
- For specific values: extract numeric value (0-100)
- For increase/decrease: use current value +10/-10 (default step)
- For increase/decrease by amount: extract the amount and apply it
- Validate that final values are within range (0-100)
- Provide clear confirmation messages
- Default to brightness if target is unclear

Respond with a JSON object matching the schema provided."""

    def _parse_value_command(self, query: str) -> Dict[str, Any]:
        """Parse value commands including increase/decrease logic."""
        import re
        query_lower = query.lower()
        
        # Determine target
        target = 'brightness'  # Default
        if 'contrast' in query_lower:
            target = 'contrast'
        elif 'opacity' in query_lower or 'transparency' in query_lower:
            target = 'opacity'
        
        # Check for increase/decrease commands
        if 'increase' in query_lower or 'raise' in query_lower or 'higher' in query_lower:
            # Look for "by X" pattern
            by_match = re.search(r'by\s+(\d+(?:\.\d+)?)', query_lower)
            if by_match:
                step = int(float(by_match.group(1)))
                return {
                    'target': target,
                    'value': f"+{step}",
                    'operation': 'increase_by',
                    'step': step
                }
            else:
                return {
                    'target': target,
                    'value': "+10",  # Default increase step
                    'operation': 'increase',
                    'step': 10
                }
        
        elif 'decrease' in query_lower or 'lower' in query_lower or 'reduce' in query_lower:
            # Look for "by X" pattern
            by_match = re.search(r'by\s+(\d+(?:\.\d+)?)', query_lower)
            if by_match:
                step = int(float(by_match.group(1)))
                return {
                    'target': target,
                    'value': f"-{step}",
                    'operation': 'decrease_by',
                    'step': step
                }
            else:
                return {
                    'target': target,
                    'value': "-10",  # Default decrease step
                    'operation': 'decrease',
                    'step': 10
                }
        
        # Look for specific numeric values
        value_match = re.search(r'(\d+(?:\.\d+)?)', query)
        if value_match:
            value = int(float(value_match.group(1)))
            return {
                'target': target,
                'value': value,
                'operation': 'set'
            }
        
        # Default fallback
        return {
            'target': target,
            'value': 50,
            'operation': 'set'
        }

    def _validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the response."""
        validated = super()._validate_response(response)
        
        # Ensure required fields for Value Agent
        if 'target' not in validated:
            validated['target'] = 'brightness'  # Default
        
        if 'value' not in validated:
            validated['value'] = 50  # Default
        
        # Handle string values like "+10", "-5" for increase/decrease
        if isinstance(validated['value'], str):
            if validated['value'].startswith('+'):
                validated['value'] = validated['value'][1:]  # Remove + sign
            elif validated['value'].startswith('-'):
                validated['value'] = validated['value'][1:]  # Remove - sign
        
        # Validate value range
        if isinstance(validated['value'], (int, float)):
            validated['value'] = max(0, min(100, int(validated['value'])))
        
        return validated

    def process(self, query: str, conversation_history: List[Dict] = None, session_id: str = None) -> Dict[str, Any]:
        """Process a user query with special handling for increase/decrease commands."""
        try:
            # Parse the command to detect increase/decrease operations
            parsed = self._parse_value_command(query)
            
            # If it's an increase/decrease command, create response directly
            if parsed['operation'] in ['increase', 'decrease', 'increase_by', 'decrease_by']:
                operation = parsed['operation']
                target = parsed['target']
                step = parsed['step']
                
                if operation in ['increase', 'increase_by']:
                    message = f"Increasing {target} by {step}"
                    value = f"+{step}"
                else:  # decrease or decrease_by
                    message = f"Decreasing {target} by {step}"
                    value = f"-{step}"
                
                return {
                    "type": "control_value",
                    "agent": "Value Agent",
                    "intent": f"{operation}_{target}",
                    "target": target,
                    "value": value,
                    "message": message,
                    "confidence": 0.9,
                    "context_used": False
                }
            
            # For regular set commands, use the base class processing
            return super().process(query, conversation_history)
            
        except Exception as e:
            print(f"Error in Value Agent processing: {e}")
            return self._create_error_response(str(e))

    def get_agent_description(self) -> str:
        return "Value Agent - Controls image properties like brightness, contrast, and opacity"

    # Legacy method for backward compatibility
    def act(
        self,
        entity: Optional[Tuple[str, float, Dict[str, Any]]],
        value_result: Optional[Tuple[float, float]],
        text: str,
    ) -> Dict[str, Any]:
        if not entity:
            return {
                "type": "control_value",
                "agent": "Value Agent",
                "intent": "clarification",
                "target": "brightness",
                "value": 50,
                "message": "Which control should I set?",
                "confidence": 0.0,
                "context_used": False,
            }

        entity_name, entity_conf, entity_data = entity
        canonical_target = entity_data.get("name", entity_name)
        entity_type = entity_data.get("type", "")

        # Ensure this is a value-type target
        if entity_type != "value":
            return {
                "type": "control_value",
                "agent": "Value Agent",
                "intent": "clarification",
                "target": canonical_target,
                "value": 50,
                "message": f"{canonical_target} is not a numeric control. Which numeric control should I set?",
                "confidence": entity_conf,
                "context_used": False,
            }

        # Require numeric value
        if not value_result:
            # Ask for value with range hint
            try:
                cfg = load_config()
                r = cfg.get("ranges", {}).get(canonical_target, {})
                r_min = r.get("min")
                r_max = r.get("max")
                hint = f" ({r_min}–{r_max})" if r_min is not None and r_max is not None else ""
            except Exception:
                hint = ""
            return {
                "type": "control_value",
                "agent": "Value Agent",
                "intent": "clarification",
                "target": canonical_target,
                "value": 50,
                "message": f"What value should I set for {canonical_target}{hint}?",
                "confidence": entity_conf,
                "context_used": False,
            }

        value, value_conf = value_result
        return {
            "type": "control_value",
            "agent": "Value Agent",
            "intent": "set_value",
            "target": canonical_target,
            "value": int(value),
            "message": f"Setting {canonical_target} to {value}.",
            "confidence": (entity_conf + value_conf) / 2,
            "context_used": False,
        }


# Global instance
value_agent = ValueAgent()


