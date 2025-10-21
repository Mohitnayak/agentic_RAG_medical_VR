from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple, Optional
from app.config_loader import load_config


class SemanticEntityResolver:
    """Resolve entities using embedding similarity against catalog."""
    
    def __init__(self):
        self.embeddings = None
        self.entity_names = []
        self.entity_data = {}
        self._config = None
        
    def _get_config(self) -> Dict[str, Any]:
        """Load entities config."""
        if self._config is None:
            config = load_config()
            self._config = config.get("entities", {})
        return self._config
    
    def _load_embeddings(self):
        """Lazy load entity embeddings."""
        if self.embeddings is not None:
            return
            
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            config = self._get_config()
            entities = config.get("entities", [])
            
            # Build entity names and data
            entity_names = []
            entity_data = {}
            
            for entity in entities:
                name = entity.get("name", "")
                synonyms = entity.get("synonyms", [])
                entity_names.append(name)
                entity_data[name] = entity
                
                # Add synonyms as separate entries
                for synonym in synonyms:
                    entity_names.append(synonym)
                    entity_data[synonym] = entity
            
            # Generate embeddings for all names and synonyms
            if entity_names:
                self.embeddings = model.encode(entity_names)
                self.entity_names = entity_names
                self.entity_data = entity_data
                
        except ImportError:
            print("Warning: sentence-transformers not installed. Semantic entity resolution disabled.")
        except Exception as e:
            print(f"Warning: Failed to load entity embeddings: {e}")
    
    def resolve(self, text: str, k: int = 3) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Resolve text to entities using embedding similarity.
        Returns list of (entity_name, confidence, entity_data) tuples.
        """
        self._load_embeddings()
        
        if self.embeddings is None:
            return []
            
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Encode input text
            query_embedding = model.encode([text])
            
            # Compute similarities
            import numpy as np
            similarities = np.dot(query_embedding, self.embeddings.T)[0]
            
            # Get top-k results
            top_indices = np.argsort(similarities)[::-1][:k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.3:  # Minimum similarity threshold
                    entity_name = self.entity_names[idx]
                    entity_data = self.entity_data[entity_name]
                    results.append((entity_name, float(similarities[idx]), entity_data))
                    
            return results
            
        except Exception as e:
            print(f"Warning: Entity resolution failed: {e}")
            return []
    
    def lexical_overlap(self, text: str) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Fallback lexical entity resolution using fuzzy matching.
        """
        try:
            from rapidfuzz.fuzz import partial_ratio
        except ImportError:
            # Fallback to simple string matching if rapidfuzz not available
            return self._simple_lexical_overlap(text)
            
        config = self._get_config()
        entities = config.get("entities", [])
        
        text_lower = text.lower()
        results = []
        
        for entity in entities:
            name = entity.get("name", "").lower()
            synonyms = [s.lower() for s in entity.get("synonyms", [])]
            
            # Check name and synonyms with fuzzy matching
            candidates = [name] + synonyms
            best_score = 0
            
            for candidate in candidates:
                if candidate:
                    score = partial_ratio(text_lower, candidate)
                    best_score = max(best_score, score)
            
            # Use threshold of 70 for fuzzy matching
            if best_score >= 70:
                results.append((entity["name"], best_score / 100.0, entity))
        
        return results
    
    def _simple_lexical_overlap(self, text: str) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Simple lexical matching fallback."""
        config = self._get_config()
        entities = config.get("entities", [])
        
        text_lower = text.lower()
        results = []
        
        for entity in entities:
            name = entity.get("name", "").lower()
            synonyms = [s.lower() for s in entity.get("synonyms", [])]
            
            # Check for exact matches
            if name in text_lower:
                results.append((entity["name"], 1.0, entity))
            else:
                # Check synonyms
                for synonym in synonyms:
                    if synonym in text_lower:
                        results.append((entity["name"], 0.8, entity))
                        break
        
        return results


# Global instance
entity_resolver = SemanticEntityResolver()