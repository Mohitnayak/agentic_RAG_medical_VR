from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict
from app.config_loader import load_config


class ConfidenceLogger:
    """Log low-confidence cases and clarifications for evaluation."""
    
    def __init__(self):
        self.logger = logging.getLogger("confidence")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler if not exists
        if not self.logger.handlers:
            handler = logging.FileHandler("logs/confidence.log")
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_low_confidence(self, text: str, intent_conf: float, entity_conf: float, 
                          value_conf: float, response_type: str):
        """Log low-confidence cases."""
        self.logger.info(json.dumps({
            "type": "low_confidence",
            "timestamp": datetime.now().isoformat(),
            "text": text[:100],  # Truncate for privacy
            "intent_confidence": intent_conf,
            "entity_confidence": entity_conf,
            "value_confidence": value_conf,
            "response_type": response_type
        }))
    
    def log_clarification(self, text: str, clarifications: list, confidences: Dict[str, float]):
        """Log clarification requests."""
        self.logger.info(json.dumps({
            "type": "clarification",
            "timestamp": datetime.now().isoformat(),
            "text": text[:100],  # Truncate for privacy
            "clarifications": clarifications,
            "confidences": confidences
        }))
    
    def log_tool_action(self, text: str, tool: str, arguments: Dict[str, Any], 
                       confidences: Dict[str, float]):
        """Log tool actions."""
        self.logger.info(json.dumps({
            "type": "tool_action",
            "timestamp": datetime.now().isoformat(),
            "text": text[:100],  # Truncate for privacy
            "tool": tool,
            "arguments": arguments,
            "confidences": confidences
        }))
    
    def log_answer(self, text: str, answer: str, context_used: bool, confidence: float):
        """Log answer responses."""
        self.logger.info(json.dumps({
            "type": "answer",
            "timestamp": datetime.now().isoformat(),
            "text": text[:100],  # Truncate for privacy
            "answer": answer[:200],  # Truncate for privacy
            "context_used": context_used,
            "confidence": confidence
        }))


# Global instance
confidence_logger = ConfidenceLogger()
