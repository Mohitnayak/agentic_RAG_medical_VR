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
        
        # 0. Deterministic fast-path for explicit numeric controls (e.g., "set brightness to 50%")
        # Try to detect numeric value and a value target lexically from config before ML routing
        fast_value = numeric_parser.parse_value(text)
        if fast_value:
            fast_value_num, fast_value_conf = fast_value
            target_name, matched_candidates = self._detect_value_target(text)
            if target_name:
                # Return direct control action with detected target and parsed value
                return {
                    "type": "tool_action",
                    "tool": "control",
                    "arguments": {
                        "hand": "right",
                        "target": target_name,
                        "operation": "set",
                        "value": fast_value_num,
                    },
                    "confidence": {
                        "intent": 0.85,
                        "entity": 0.75,
                        "value": fast_value_conf,
                    },
                }
            # If we detected a number but not a clear value target → targeted clarification
            # Suggest likely value controls from config with ranges
            cfg = load_config()
            ranges_cfg = cfg.get("ranges", {})
            likely = []
            for name in ("contrast", "brightness"):
                r = ranges_cfg.get(name, {})
                r_min = r.get("min")
                r_max = r.get("max")
                if r_min is not None and r_max is not None:
                    likely.append(f"{name} ({r_min}–{r_max})")
                else:
                    likely.append(name)
            return {
                "type": "clarification",
                "message": f"I detected value {fast_value_num}. Which control should I apply it to?",
                "clarifications": [
                    f"Choose one: {', '.join(likely)}",
                ],
                "confidence": {
                    "intent": 0.7,
                    "entity": 0.2,
                    "value": fast_value_conf,
                },
            }

        # 1. Intent classification (ML-only approach)
        intent_label, intent_confidence = classifier.classify(text)
        
        # Fuzzy matching fallback for typos when semantic classifier fails
        if intent_confidence < intent_threshold:
            fuzzy_label, fuzzy_confidence = self._fuzzy_intent_match(text)
            if fuzzy_confidence > intent_confidence:
                intent_label, intent_confidence = fuzzy_label, fuzzy_confidence
        
        # LLM tie-breaker for low confidence cases (only if Ollama is available)
        if intent_confidence < intent_threshold:
            try:
                llm_label, llm_confidence = self._llm_classify(text)
                if llm_confidence > intent_confidence:
                    intent_label, intent_confidence = llm_label, llm_confidence
            except Exception:
                # Ollama not available, skip LLM fallback
                pass
        
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
        # Additional disambiguation for "show me the implants" – offer definition vs overlay control
        if "show me" in text.lower() and "implant" in text.lower():
            # If confidence is low, ask targeted clarification instead of generic one
            if intent_confidence < 0.7:
                return {
                    "type": "clarification",
                    "message": "Do you want to show the implants overlay or hear a quick definition?",
                    "clarifications": [
                        "Turn on implants overlay",
                        "Tell me about implants",
                    ],
                    "confidence": {
                        "intent": intent_confidence,
                        "entity": 0.4,
                        "value": 0.0,
                    },
                }
        
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
        
        # Get best entity - prefer semantic over lexical, and longer/more specific matches
        best_entity = None
        entity_confidence = 0.0
        if entity_results:
            # Sort by confidence, but prefer semantic entities and longer entity names
            def entity_score(entity):
                name, conf, data = entity
                # Boost semantic entities (they come first in the list)
                semantic_boost = 0.1 if name in [e[0] for e in semantic_entities] else 0.0
                # Boost longer entity names (more specific)
                length_boost = len(name) * 0.01
                return conf + semantic_boost + length_boost
            
            best_entity = max(entity_results, key=entity_score)
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
            # Provide richer, context-aware clarifications using top entity candidates
            top_candidates = entity_results[:5] if entity_results else []
            clarification_response = self._generate_clarification(
                text,
                intent_label,
                intent_confidence,
                best_entity,
                entity_confidence,
                value_result,
                value_confidence,
                top_candidates,
            )
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

    def _detect_value_target(self, text: str) -> Tuple[Optional[str], List[str]]:
        """Lexically detect a value-control target (e.g., brightness/contrast) from config.

        Returns (best_target_name, matched_names)
        """
        cfg = load_config()
        entity_cfg = cfg.get("entities", {}).get("entities", [])
        text_lower = text.lower()
        matches: List[str] = []

        # Build candidate list: only entities with type==value
        candidates: List[Tuple[str, List[str]]] = []
        for e in entity_cfg:
            if e.get("type") == "value":
                name = e.get("name", "")
                syns = [s.lower() for s in e.get("synonyms", [])]
                candidates.append((name, syns))

        for name, syns in candidates:
            if name and name in text_lower:
                matches.append(name)
                continue
            for s in syns:
                if s and s in text_lower:
                    matches.append(name)
                    break

        # Deduplicate while preserving order
        seen = set()
        matches = [m for m in matches if not (m in seen or seen.add(m))]

        if len(matches) == 1:
            return matches[0], matches
        else:
            return None, matches
    
    def _fuzzy_intent_match(self, text: str) -> Tuple[str, float]:
        """Fuzzy matching fallback for typos and variations."""
        try:
            from rapidfuzz.fuzz import partial_ratio
            
            text_lower = text.lower()
            
            # Common patterns - prioritize info questions over control actions
            control_patterns = {
                "info_definition": [
                    "what is", "what are", "definition", "tell me about", "information",
                    "wat is", "wat are", "definiton", "infomation"
                ],
                "info_location": [
                    "where is", "where are", "which side", "what side",
                    "were is", "were are", "wich side", "wat side"
                ],
                "control_on": [
                    "turn on", "activate", "enable", "switch on", "start", "show", 
                    "give me", "provide me", "bring up", "turnn on", "tirn on",
                    "turnn", "tirn", "activat", "enabl", "swich on"
                ],
                "control_off": [
                    "turn off", "deactivate", "disable", "switch off", "stop", "hide",
                    "turnn off", "tirn off", "deactivat", "disabl", "swich off"
                ]
            }
            
            best_match = "none"
            best_score = 0.0
            
            for intent, patterns in control_patterns.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        # Calculate fuzzy score for the pattern
                        score = partial_ratio(pattern, text_lower) / 100.0
                        
                        # Boost info patterns to prioritize them over control patterns
                        if intent.startswith("info_"):
                            score = min(score + 0.3, 1.0)
                        
                        if score > best_score:
                            best_score = score
                            best_match = intent
            
            # Boost confidence for exact matches
            if best_score > 0.8:
                best_score = min(best_score + 0.2, 1.0)
            
            return best_match, best_score
            
        except ImportError:
            # Fallback to simple pattern matching
            text_lower = text.lower()
            
            if any(word in text_lower for word in ["turn on", "activate", "enable", "show", "start"]):
                return "control_on", 0.6
            elif any(word in text_lower for word in ["turn off", "deactivate", "disable", "hide", "stop"]):
                return "control_off", 0.6
            elif any(word in text_lower for word in ["what is", "what are", "definition"]):
                return "info_definition", 0.6
            elif any(word in text_lower for word in ["where is", "where are", "which side"]):
                return "info_location", 0.6
            
            return "none", 0.0
        except Exception as e:
            print(f"Warning: Fuzzy matching failed: {e}")
            return "none", 0.0

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
    
    def _generate_clarification(
        self,
        text: str,
        intent_label: str,
        intent_conf: float,
        entity: Optional[Tuple],
        entity_conf: float,
        value_result: Optional[Tuple],
        value_conf: float,
        entity_candidates: List[Tuple[str, float, Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Generate context-aware clarification suggestions based on input and candidates."""
        clarifications: List[str] = []
        text_lower = text.lower()
        detected_value = None
        if value_result:
            detected_value = value_result[0]

        # Load entities/ranges for targeted suggestions
        try:
            cfg = load_config()
            entity_cfg = cfg.get("entities", {}).get("entities", [])
            ranges_cfg = cfg.get("ranges", {})
        except Exception:
            entity_cfg, ranges_cfg = [], {}

        # Build helpful suggestion lists
        switch_targets = [e for e in entity_cfg if e.get("type") == "switch"]
        value_targets = [e for e in entity_cfg if e.get("type") == "value"]

        # 1) If a numeric value is present but entity is unclear → ask which control to apply it to
        if detected_value is not None and (entity is None or entity_conf < 0.5):
            options = []
            for e in value_targets:
                name = e.get("name", "")
                r = ranges_cfg.get(name, {})
                r_min = r.get("min")
                r_max = r.get("max")
                if r_min is not None and r_max is not None:
                    options.append(f"{name} ({r_min}–{r_max})")
                else:
                    options.append(name)
            if options:
                clarifications.append(
                    f"I detected value {detected_value}. Which control should I apply it to? (e.g., {', '.join(options[:4])})"
                )

        # 2) If control intent (on/off/toggle) and entity is unclear → suggest top candidates + common switches
        if intent_label in ("control_on", "control_off") and (entity is None or entity_conf < 0.5):
            candidate_names = []
            for n, c, d in entity_candidates[:5]:
                canonical = d.get("name", n)
                if canonical not in candidate_names:
                    candidate_names.append(canonical)
            # Add common switches if we have room
            for e in switch_targets:
                nm = e.get("name", "")
                if nm and nm not in candidate_names:
                    candidate_names.append(nm)
                if len(candidate_names) >= 5:
                    break
            if candidate_names:
                clarifications.append(
                    f"Which element should I {'turn on' if intent_label=='control_on' else 'turn off'}? (e.g., {', '.join(candidate_names[:5])})"
                )

        # 3) If info intent and entity unclear → suggest top entity candidates
        if intent_label in ("info_definition", "info_location") and (entity is None or entity_conf < 0.5):
            candidate_names = []
            for n, c, d in entity_candidates[:5]:
                canonical = d.get("name", n)
                if canonical not in candidate_names:
                    candidate_names.append(canonical)
            if candidate_names:
                what = "definition" if intent_label == "info_definition" else "location"
                clarifications.append(
                    f"Whose {what} do you want? (e.g., {', '.join(candidate_names[:5])})"
                )

        # 4) If intent confidence is low → ask a light, non-intrusive nudge rather than generic patterns
        if intent_conf < 0.6 and not clarifications:
            clarifications.append(
                "I can help with controls (turn on/off, set values) or info (what/where). What would you like to do?"
            )

        # 5) If nothing specific generated, provide a minimal fallback clarification
        if not clarifications:
            clarifications.append("Could you specify the element or value?")

        return {
            "type": "clarification",
            "message": "I need a bit more detail:",
            "clarifications": clarifications,
            "confidence": {
                "intent": intent_conf,
                "entity": entity_conf,
                "value": value_conf,
            },
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
        canonical_target = entity_data.get("name", entity_name)
        
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
        elif intent_label == "control_value" and not value_result:
            # Missing numeric value → ask a targeted value clarification using ranges for this control
            try:
                cfg = load_config()
                ranges_cfg = cfg.get("ranges", {})
                r = ranges_cfg.get(canonical_target, {})
                r_min = r.get("min")
                r_max = r.get("max")
                range_hint = f" ({r_min}–{r_max})" if r_min is not None and r_max is not None else ""
            except Exception:
                range_hint = ""
            return {
                "type": "clarification",
                "message": f"What value should I set for {canonical_target}{range_hint}?",
                "clarifications": [
                    f"Example: set {canonical_target} to 50",
                    f"Example: {canonical_target} 75%",
                ],
                "confidence": {
                    "intent": 0.8,
                    "entity": entity_conf,
                    "value": 0.0,
                }
            }
        
        # Determine hand based on entity type
        hand = "right"  # Default to right hand
        if entity_type == "skull_model":
            hand = "left"
        
        return {
            "type": "tool_action",
            "tool": "control",
            "arguments": {
                "hand": hand,
                "target": canonical_target,
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
        canonical_name = entity_data.get("name", entity_name)  # Use canonical name from entity data
        
        if intent_label == "info_definition":
            # Try to get definition from the definitions resolver first
            from app.scene.defs import resolve_definition
            definition = resolve_definition(text)
            
            if definition:
                return {
                    "type": "answer",
                    "answer": definition,
                    "context_used": False,
                    "confidence": entity_conf
                }
            else:
                # Fallback to entity data or generic message
                definition = entity_data.get("definition", f"{canonical_name} is a VR scene element.")
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