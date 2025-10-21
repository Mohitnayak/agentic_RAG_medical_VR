from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple, Optional
from app.config_loader import load_config


class ZeroShotClassifier:
    """Optional zero-shot intent classifier using HuggingFace transformers."""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._config = None
        self._enabled = False
        
    def _get_config(self) -> Dict[str, Any]:
        """Load classifier config."""
        if self._config is None:
            config = load_config()
            intent_config = config.get("intent", {})
            self._config = intent_config.get("classifier", {})
        return self._config
    
    def _load_model(self):
        """Lazy load the classifier model."""
        if self.model is not None:
            return
            
        config = self._get_config()
        if not config.get("enabled", False):
            return
            
        try:
            from transformers import pipeline
            model_name = config.get("model", "facebook/bart-large-mnli")
            self.classifier = pipeline("zero-shot-classification", model=model_name)
            self._enabled = True
        except ImportError:
            print("Warning: transformers not installed. Zero-shot classifier disabled.")
            self._enabled = False
        except Exception as e:
            print(f"Warning: Failed to load classifier: {e}")
            self._enabled = False
    
    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify text intent using rule-based ML approach.
        Returns (label, confidence) or ("none", 0.0) if disabled/failed.
        """
        config = self._get_config()
        if not config.get("enabled", False):
            return "none", 0.0
            
        # Rule-based classification (more reliable than downloading large models)
        text_lower = text.lower().strip()
        
        # Control actions - check OFF first to avoid conflicts
        if any(word in text_lower for word in ["turn off", "disable", "switch off", "stop", "hide", "deactivate"]):
            if any(word in text_lower for word in ["handles", "nerve", "sinus", "xray", "implants"]):
                return "control_off", 0.9
                
        if any(word in text_lower for word in ["turn on", "enable", "switch on", "start", "show", "give me", "provide me with", "activate"]):
            if any(word in text_lower for word in ["handles", "nerve", "sinus", "xray", "implants"]):
                # Check if it's an implant with specific size
                if "implant" in text_lower and any(char.isdigit() for char in text_lower):
                    return "control_value", 0.9
                return "control_on", 0.9
                
        if any(word in text_lower for word in ["set", "increase", "decrease"]) and any(word in text_lower for word in ["brightness", "contrast"]):
            return "control_value", 0.8
            
        # Information requests
        if text_lower.startswith("what are") or text_lower.startswith("what is"):
            return "info_definition", 0.9
            
        if text_lower.startswith("where is") or text_lower.startswith("where are"):
            return "info_location", 0.9
            
        # Size requests - implant requests (only if no specific size mentioned)
        if "implant" in text_lower and ("give me" in text_lower or "provide me" in text_lower) and not any(char.isdigit() for char in text_lower):
            return "size_request", 0.8
            
        return "none", 0.0
    
    def is_enabled(self) -> bool:
        """Check if classifier is enabled and loaded."""
        config = self._get_config()
        return config.get("enabled", False) and self._enabled


# Global instance
classifier = ZeroShotClassifier()
