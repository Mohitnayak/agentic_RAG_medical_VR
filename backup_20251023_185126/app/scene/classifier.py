from __future__ import annotations

import os
import numpy as np
from typing import Any, Dict, List, Tuple, Optional
from app.config_loader import load_config


class ZeroShotClassifier:
    """Semantic zero-shot intent classifier using sentence transformers."""
    
    def __init__(self):
        self._config = None
        self._enabled = False
        self._model = None
        self._label_names = None
        self._label_texts = None
        self._label_embeddings = None
        
    def _get_config(self) -> Dict[str, Any]:
        """Load classifier config."""
        if self._config is None:
            config = load_config()
            intent_config = config.get("intent", {})
            self._config = intent_config.get("classifier", {})
        return self._config
    
    def _ensure_model(self):
        """Lazy load the semantic classifier model."""
        if self._model is not None:
            return
            
        config = self._get_config()
        if not config.get("enabled", False):
            return
            
        try:
            from sentence_transformers import SentenceTransformer
            model_name = config.get("model", "all-MiniLM-L6-v2")
            self._model = SentenceTransformer(model_name)
            
            # Load label prompts and create embeddings
            label_prompts = config.get("label_prompts", {})
            self._label_names = list(label_prompts.keys())
            self._label_texts = [label_prompts[k] for k in self._label_names]
            
            # Create normalized embeddings for cosine similarity
            self._label_embeddings = self._model.encode(
                self._label_texts, 
                normalize_embeddings=True
            )
            
            self._enabled = True
            print(f"Loaded semantic classifier with {len(self._label_names)} labels")
            
        except ImportError:
            print("Warning: sentence-transformers not installed. Semantic classifier disabled.")
            self._enabled = False
        except Exception as e:
            print(f"Warning: Failed to load semantic classifier: {e}")
            self._enabled = False
    
    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify text intent using semantic similarity.
        Returns (label, confidence) or ("none", 0.0) if disabled/failed.
        """
        config = self._get_config()
        if not config.get("enabled", False):
            return "none", 0.0
            
        self._ensure_model()
        
        if not self._enabled or self._model is None:
            return "none", 0.0
            
        try:
            # Encode input text with normalization
            query_embedding = self._model.encode([text], normalize_embeddings=True)[0]
            
            # Compute cosine similarities (since embeddings are normalized)
            similarities = np.dot(self._label_embeddings, query_embedding)
            
            # Get best match
            best_idx = int(np.argmax(similarities))
            best_label = self._label_names[best_idx]
            best_confidence = float(similarities[best_idx])
            
            # Apply minimum confidence threshold
            min_confidence = 0.3
            if best_confidence < min_confidence:
                return "none", best_confidence
                
            return best_label, best_confidence
            
        except Exception as e:
            print(f"Warning: Classification failed: {e}")
            return "none", 0.0
    
    def is_enabled(self) -> bool:
        """Check if classifier is enabled and loaded."""
        config = self._get_config()
        return config.get("enabled", False) and self._enabled


# Global instance
classifier = ZeroShotClassifier()
