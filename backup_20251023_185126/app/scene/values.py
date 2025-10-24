from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple, Optional, Union
from app.config_loader import load_config


class NumericParser:
    """Parse numeric values and sizes from text."""
    
    def __init__(self):
        self._config = None
        
    def _get_config(self) -> Dict[str, Any]:
        """Load ranges config."""
        if self._config is None:
            config = load_config()
            self._config = config.get("ranges", {})
        return self._config
    
    def parse_brightness_contrast(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Parse brightness or contrast values from text.
        Returns (value, confidence) or None if not found.
        """
        # Look for percentage patterns
        percentage_pattern = r'(\d+(?:\.\d+)?)\s*%'
        matches = re.findall(percentage_pattern, text)
        
        if matches:
            try:
                value = float(matches[0])
                ranges = self._get_config()
                
                # Check if it's brightness or contrast
                if 'brightness' in text.lower():
                    target_range = ranges.get('brightness', {'min': 0, 'max': 100})
                elif 'contrast' in text.lower():
                    target_range = ranges.get('contrast', {'min': 0, 'max': 100})
                else:
                    target_range = {'min': 0, 'max': 100}
                
                min_val = target_range.get('min', 0)
                max_val = target_range.get('max', 100)
                
                if min_val <= value <= max_val:
                    return value, 0.9
                else:
                    return value, 0.5  # Lower confidence for out-of-range
                    
            except ValueError:
                pass
        
        # Look for simple numbers
        number_pattern = r'\b(\d+(?:\.\d+)?)\b'
        matches = re.findall(number_pattern, text)
        
        if matches:
            try:
                value = float(matches[0])
                ranges = self._get_config()
                
                if 'brightness' in text.lower():
                    target_range = ranges.get('brightness', {'min': 0, 'max': 100})
                elif 'contrast' in text.lower():
                    target_range = ranges.get('contrast', {'min': 0, 'max': 100})
                else:
                    target_range = {'min': 0, 'max': 100}
                
                min_val = target_range.get('min', 0)
                max_val = target_range.get('max', 100)
                
                if min_val <= value <= max_val:
                    return value, 0.7
                    
            except ValueError:
                pass
        
        return None
    
    def parse_implant_size(self, text: str) -> Optional[Tuple[Dict[str, float], float]]:
        """
        Parse implant size from text like "4 x 11.5" or "height 4.2 length 12".
        Returns ({height_y_mm: float, length_z_mm: float}, confidence) or None.
        """
        ranges = self._get_config()
        implant_ranges = ranges.get('implants', {})
        height_range = implant_ranges.get('height_y_mm', {'min': 3.0, 'max': 4.8})
        length_range = implant_ranges.get('length_z_mm', {'min': 6.0, 'max': 17.0})
        
        # Pattern for "4 x 11.5" format
        dimension_pattern = r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)'
        match = re.search(dimension_pattern, text)
        
        if match:
            try:
                val1, val2 = float(match.group(1)), float(match.group(2))
                
                # Determine which is height and which is length based on ranges
                if height_range['min'] <= val1 <= height_range['max'] and length_range['min'] <= val2 <= length_range['max']:
                    return {'height_y_mm': val1, 'length_z_mm': val2}, 0.9
                elif height_range['min'] <= val2 <= height_range['max'] and length_range['min'] <= val1 <= length_range['max']:
                    return {'height_y_mm': val2, 'length_z_mm': val1}, 0.9
                else:
                    return {'height_y_mm': val1, 'length_z_mm': val2}, 0.6
                    
            except ValueError:
                pass
        
        # Pattern for "height 4.2 length 12" format
        height_pattern = r'height[:\s]*(\d+(?:\.\d+)?)'
        length_pattern = r'length[:\s]*(\d+(?:\.\d+)?)'
        
        height_match = re.search(height_pattern, text, re.IGNORECASE)
        length_match = re.search(length_pattern, text, re.IGNORECASE)
        
        if height_match and length_match:
            try:
                height = float(height_match.group(1))
                length = float(length_match.group(1))
                
                if height_range['min'] <= height <= height_range['max'] and length_range['min'] <= length <= length_range['max']:
                    return {'height_y_mm': height, 'length_z_mm': length}, 0.9
                else:
                    return {'height_y_mm': height, 'length_z_mm': length}, 0.6
                    
            except ValueError:
                pass
        
        # Pattern for single values with context
        single_pattern = r'(\d+(?:\.\d+)?)'
        matches = re.findall(single_pattern, text)
        
        if matches:
            try:
                value = float(matches[0])
                
                # If it's in height range, assume it's height
                if height_range['min'] <= value <= height_range['max']:
                    return {'height_y_mm': value}, 0.5
                # If it's in length range, assume it's length
                elif length_range['min'] <= value <= length_range['max']:
                    return {'length_z_mm': value}, 0.5
                    
            except ValueError:
                pass
        
        return None
    
    def parse_value(self, text: str, target_type: str = "auto") -> Optional[Tuple[Union[float, Dict[str, float]], float]]:
        """
        Parse any numeric value from text.
        Returns (value, confidence) or None if not found.
        """
        if target_type == "brightness" or target_type == "contrast":
            result = self.parse_brightness_contrast(text)
            if result:
                return result
        
        elif target_type == "implant_size":
            result = self.parse_implant_size(text)
            if result:
                return result
        
        else:  # auto-detect
            # Try implant size first
            implant_result = self.parse_implant_size(text)
            if implant_result:
                return implant_result
            
            # Then try brightness/contrast
            brightness_result = self.parse_brightness_contrast(text)
            if brightness_result:
                return brightness_result
        
        return None


# Global instance
numeric_parser = NumericParser()