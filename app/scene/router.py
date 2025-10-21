from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional, Union
from app.config_loader import load_config
from app.scene.classifier import classifier
from app.scene.entity_resolver import entity_resolver
from app.scene.values import numeric_parser
from app.scene.intent import parse_intent
from app.logging import confidence_logger


class DecisionRouter:
    """Combines intent, entity, and value parsing with confidence-based routing."""
    
    def __init__(self):
        self._config = None
        
    def _get_config(self) -> Dict[str, Any]:
        """Load intent config."""
        if self._config is None:
            config = load_config()
            self._config = config.get("intent", {})
        return self._config
    
    def route(self, text: str) -> Dict[str, Any]:
        """
        Route user input to appropriate action.
        Returns structured response with tool action or clarification request.
        """
        config = self._get_config()
        thresholds = config.get("thresholds", {})
        
        intent_threshold = thresholds.get("intent_confidence", 0.6)
        entity_threshold = thresholds.get("entity_confidence", 0.5)
        value_threshold = thresholds.get("value_confidence", 0.4)
        router_cutoff = thresholds.get("router_cutoff", 0.3)
        
        # 1. Intent classification (ML-only approach)
        intent_label, intent_confidence = classifier.classify(text)
        
        # LLM tie-breaker for low confidence cases
        if intent_confidence < intent_threshold:
            llm_label, llm_confidence = self._llm_classify(text)
            if llm_confidence > intent_confidence:
                intent_label, intent_confidence = llm_label, llm_confidence
        
        # Special handling for implant requests
        if "implant" in text.lower() and ("give me" in text.lower() or "provide me" in text.lower()):
            if any(char.isdigit() for char in text):
                # Has specific size - treat as control action
                intent_label = "control_value"
                intent_confidence = 0.9
            else:
                # No specific size - ask for size
                intent_label = "size_request"
                intent_confidence = 0.8
        
        # 2. Entity resolution
        semantic_entities = entity_resolver.resolve(text, k=3)
        lexical_entities = entity_resolver.lexical_overlap(text)
        
        # Combine entity results
        entity_results = []
        seen_entities = set()
        
        for name, conf, data in semantic_entities:
            if name not in seen_entities:
                entity_results.append((name, conf, data))
                seen_entities.add(name)
        
        for name, conf, data in lexical_entities:
            if name not in seen_entities:
                entity_results.append((name, conf, data))
                seen_entities.add(name)
        
        # Get best entity
        best_entity = None
        entity_confidence = 0.0
        if entity_results:
            best_entity = max(entity_results, key=lambda x: x[1])
            entity_confidence = best_entity[1]
        
        # 3. Value parsing
        value_result = None
        value_confidence = 0.0
        
        if intent_label in ["control_value", "size_request"]:
            value_result = numeric_parser.parse_value(text)
            if value_result:
                _, value_confidence = value_result
        
        # 4. Decision logic
        overall_confidence = min(intent_confidence, entity_confidence) if entity_confidence > 0 else intent_confidence
        
        # Check if we need clarification
        if overall_confidence < router_cutoff:
            clarification_response = self._generate_clarification(text, intent_label, intent_confidence, best_entity, entity_confidence, value_result, value_confidence)
            confidence_logger.log_clarification(text, clarification_response["clarifications"], clarification_response["confidence"])
            return clarification_response
        
        # Route to appropriate action
        if intent_label.startswith("control_"):
            control_response = self._generate_control_action(intent_label, best_entity, value_result, text)
            if control_response.get("type") == "tool_action":
                confidence_logger.log_tool_action(text, control_response["tool"], control_response["arguments"], control_response["confidence"])
            return control_response
        elif intent_label.startswith("info_"):
            info_response = self._generate_info_response(intent_label, best_entity, text)
            confidence_logger.log_answer(text, info_response["answer"], info_response["context_used"], info_response["confidence"])
            return info_response
        elif intent_label == "size_request":
            size_response = self._generate_size_request_response(text)
            confidence_logger.log_clarification(text, size_response["clarifications"], size_response["confidence"])
            return size_response
        else:
            fallback_response = self._generate_fallback_response(text)
            confidence_logger.log_clarification(text, fallback_response["clarifications"], {})
            return fallback_response
    
    def _llm_classify(self, text: str) -> Tuple[str, float]:
        """LLM-based intent classification as tie-breaker."""
        try:
            from app.llm.ollama_client import OllamaClient
            client = OllamaClient()
            
            # Get allowed labels from config
            config = self._get_config()
            labels = config.get("classifier", {}).get("labels", [])
            label_prompts = config.get("classifier", {}).get("label_prompts", {})
            
            # Create constrained prompt
            prompt = f"""Classify this user input into one of these exact labels: {', '.join(labels)}

User input: "{text}"

Respond with only the label name (e.g., "control_on", "info_definition", etc.). No explanation."""

            response = client.chat(prompt)
            response = response.strip().lower()
            
            # Check if response is a valid label
            if response in labels:
                return response, 0.7  # Medium confidence for LLM
            else:
                return "none", 0.0
                
        except Exception as e:
            print(f"Warning: LLM classification failed: {e}")
            return "none", 0.0
    
    def _generate_clarification(self, text: str, intent_label: str, intent_conf: float, 
                               entity: Optional[Tuple], entity_conf: float,
                               value_result: Optional[Tuple], value_conf: float) -> Dict[str, Any]:
        """Generate clarification request."""
        clarifications = []
        
        if intent_conf < 0.6:
            clarifications.append("Could you clarify what you'd like to do? (e.g., 'turn on', 'show me', 'what is')")
        
        if entity_conf < 0.5:
            clarifications.append("Which element are you referring to? (e.g., 'handles', 'implants', 'x-ray')")
        
        if value_result and value_conf < 0.4:
            clarifications.append("What value would you like to set? (e.g., '50%', '4 x 11.5')")
        
        return {
            "type": "clarification",
            "message": "I need more information:",
            "clarifications": clarifications,
            "confidence": {
                "intent": intent_conf,
                "entity": entity_conf,
                "value": value_conf
            }
        }
    
    def _generate_control_action(self, intent_label: str, entity: Optional[Tuple], 
                                value_result: Optional[Tuple], text: str) -> Dict[str, Any]:
        """Generate control tool action."""
        if not entity:
            return {
                "type": "clarification",
                "message": "Which element would you like to control?",
                "clarifications": ["Please specify the target (e.g., 'handles', 'implants', 'x-ray')"]
            }
        
        entity_name, entity_conf, entity_data = entity
        entity_type = entity_data.get("type", "unknown")
        
        # Determine operation and value
        operation = "toggle"
        value = None
        
        if intent_label == "control_on":
            operation = "set"
            value = "on"
        elif intent_label == "control_off":
            operation = "set"
            value = "off"
        elif intent_label == "control_value" and value_result:
            operation = "set"
            value, _ = value_result
        
        # Determine hand based on entity type
        hand = "right"  # Default to right hand
        if entity_type == "skull_model":
            hand = "left"
        
        return {
            "type": "tool_action",
            "tool": "control",
            "arguments": {
                "hand": hand,
                "target": entity_name,
                "operation": operation,
                "value": value
            },
            "confidence": {
                "intent": 0.8,
                "entity": entity_conf,
                "value": value_result[1] if value_result else 0.0
            }
        }
    
    def _generate_info_response(self, intent_label: str, entity: Optional[Tuple], text: str) -> Dict[str, Any]:
        """Generate information response."""
        if not entity:
            return {
                "type": "clarification",
                "message": "What would you like to know about?",
                "clarifications": ["Please specify the element (e.g., 'handles', 'implants', 'x-ray')"]
            }
        
        entity_name, entity_conf, entity_data = entity
        
        if intent_label == "info_definition":
            definition = entity_data.get("definition", f"{entity_name} is a VR scene element.")
            return {
                "type": "answer",
                "answer": definition,
                "context_used": False,
                "confidence": entity_conf
            }
        elif intent_label == "info_location":
            location = entity_data.get("location", f"{entity_name} location is not specified.")
            return {
                "type": "answer", 
                "answer": location,
                "context_used": False,
                "confidence": entity_conf
            }
        else:
            return {
                "type": "answer",
                "answer": f"{entity_name} information: {entity_data.get('definition', 'No description available.')}",
                "context_used": False,
                "confidence": entity_conf
            }
    
    def _generate_fallback_response(self, text: str) -> Dict[str, Any]:
        """Generate fallback response for unclear input."""
        return {
            "type": "clarification",
            "message": "I'm not sure what you're asking for.",
            "clarifications": [
                "Try asking about scene elements (e.g., 'what are handles?')",
                "Try control commands (e.g., 'turn on x-ray')",
                "Try location questions (e.g., 'where is the skull?')"
            ]
        }
    
    def _generate_size_request_response(self, text: str) -> Dict[str, Any]:
        """Generate size request clarification."""
        return {
            "type": "clarification",
            "message": "Which size for implants?",
            "clarifications": [
                "Provide height_y_mm (3.0–4.8) and length_z_mm (6–17)",
                "Example: 'give me implant size 4 x 11.5'"
            ],
            "confidence": {
                "intent": 0.8,
                "entity": 0.0,
                "value": 0.0
            }
        }


# Global instance
decision_router = DecisionRouter()