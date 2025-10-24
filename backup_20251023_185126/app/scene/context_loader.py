from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Any
from pathlib import Path


class SceneContextLoader:
    """Loads and parses scene_reference.md for VR dental environment context."""
    
    def __init__(self, scene_reference_path: str = "docs/scene_reference.md"):
        self.scene_reference_path = scene_reference_path
        self._content = None
        self._parsed_sections = {}
        self._load_content()
    
    def _load_content(self) -> None:
        """Load and cache the scene reference content."""
        try:
            with open(self.scene_reference_path, 'r', encoding='utf-8') as f:
                self._content = f.read()
            self._parse_sections()
        except FileNotFoundError:
            print(f"Warning: Scene reference file not found at {self.scene_reference_path}")
            self._content = ""
        except Exception as e:
            print(f"Error loading scene reference: {e}")
            self._content = ""
    
    def _parse_sections(self) -> None:
        """Parse the markdown content into structured sections."""
        if not self._content:
            return
        
        # Parse scene elements table
        elements_match = re.search(r'### Scene elements overview\s*\n(.*?)(?=\n###|\n##|\Z)', self._content, re.DOTALL)
        if elements_match:
            self._parsed_sections['scene_elements'] = self._parse_elements_table(elements_match.group(1))
        
        # Parse switch controls table
        switches_match = re.search(r'### Switch controls\s*\n(.*?)(?=\n###|\n##|\Z)', self._content, re.DOTALL)
        if switches_match:
            self._parsed_sections['switch_controls'] = self._parse_controls_table(switches_match.group(1))
        
        # Parse value controls table
        values_match = re.search(r'### Value controls\s*\n(.*?)(?=\n###|\n##|\Z)', self._content, re.DOTALL)
        if values_match:
            self._parsed_sections['value_controls'] = self._parse_controls_table(values_match.group(1))
        
        # Parse information queries
        info_match = re.search(r'### Information queries.*?\n(.*?)(?=\n###|\n##|\Z)', self._content, re.DOTALL)
        if info_match:
            self._parsed_sections['information_queries'] = self._parse_info_table(info_match.group(1))
        
        # Parse implant sizing
        implant_match = re.search(r'### Implant sizing requests\s*\n(.*?)(?=\n###|\n##|\Z)', self._content, re.DOTALL)
        if implant_match:
            self._parsed_sections['implant_sizing'] = self._parse_implant_table(implant_match.group(1))
        
        # Parse notes functions
        notes_match = re.search(r'### Notes functions\s*\n(.*?)(?=\n###|\n##|\Z)', self._content, re.DOTALL)
        if notes_match:
            self._parsed_sections['notes_functions'] = self._parse_notes_table(notes_match.group(1))
    
    def _parse_elements_table(self, table_content: str) -> List[Dict[str, str]]:
        """Parse the scene elements table."""
        elements = []
        lines = table_content.strip().split('\n')
        
        for line in lines:
            if '|' in line and not line.startswith('|---'):
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 5:
                    elements.append({
                        'element': parts[1],
                        'type': parts[2],
                        'location': parts[3],
                        'purpose': parts[4],
                        'synonyms': parts[5] if len(parts) > 5 else ''
                    })
        
        return elements
    
    def _parse_controls_table(self, table_content: str) -> List[Dict[str, str]]:
        """Parse control tables (switches and values)."""
        controls = []
        lines = table_content.strip().split('\n')
        
        for line in lines:
            if '|' in line and not line.startswith('|---'):
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:
                    controls.append({
                        'control': parts[1],
                        'description': parts[2],
                        'utterances': parts[3] if len(parts) > 3 else '',
                        'notes': parts[4] if len(parts) > 4 else ''
                    })
        
        return controls
    
    def _parse_info_table(self, table_content: str) -> List[Dict[str, str]]:
        """Parse information queries table."""
        queries = []
        lines = table_content.strip().split('\n')
        
        for line in lines:
            if '|' in line and not line.startswith('|---'):
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:
                    queries.append({
                        'topic': parts[1],
                        'examples': parts[2],
                        'expected_answer': parts[3] if len(parts) > 3 else ''
                    })
        
        return queries
    
    def _parse_implant_table(self, table_content: str) -> List[Dict[str, str]]:
        """Parse implant sizing table."""
        implants = []
        lines = table_content.strip().split('\n')
        
        for line in lines:
            if '|' in line and not line.startswith('|---'):
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:
                    implants.append({
                        'intent': parts[1],
                        'examples': parts[2],
                        'behavior': parts[3] if len(parts) > 3 else ''
                    })
        
        return implants
    
    def _parse_notes_table(self, table_content: str) -> List[Dict[str, str]]:
        """Parse notes functions table."""
        notes = []
        lines = table_content.strip().split('\n')
        
        for line in lines:
            if '|' in line and not line.startswith('|---'):
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:
                    notes.append({
                        'action': parts[1],
                        'examples': parts[2],
                        'system_behavior': parts[3] if len(parts) > 3 else ''
                    })
        
        return notes
    
    def get_scene_description(self) -> str:
        """Get the main scene description."""
        if not self._content:
            return ""
        
        # Extract the scene description section
        desc_match = re.search(r'### Scene description\s*\n(.*?)(?=\n###|\n##|\Z)', self._content, re.DOTALL)
        return desc_match.group(1).strip() if desc_match else ""
    
    def get_element_info(self, element_name: str) -> Optional[Dict[str, str]]:
        """Get information about a specific scene element."""
        elements = self._parsed_sections.get('scene_elements', [])
        for element in elements:
            if element['element'].lower() == element_name.lower():
                return element
        return None
    
    def get_control_info(self, control_name: str) -> Optional[Dict[str, str]]:
        """Get information about a specific control (switch or value)."""
        # Check switch controls
        switches = self._parsed_sections.get('switch_controls', [])
        for switch in switches:
            if switch['control'].lower() == control_name.lower():
                return switch
        
        # Check value controls
        values = self._parsed_sections.get('value_controls', [])
        for value in values:
            if value['control'].lower() == control_name.lower():
                return value
        
        return None
    
    def get_implant_sizing_info(self) -> List[Dict[str, str]]:
        """Get implant sizing information."""
        return self._parsed_sections.get('implant_sizing', [])
    
    def get_notes_functions(self) -> List[Dict[str, str]]:
        """Get notes function information."""
        return self._parsed_sections.get('notes_functions', [])
    
    def search_context(self, query: str) -> str:
        """Search for relevant context based on query."""
        query_lower = query.lower()
        context_parts = []
        
        # Add scene description
        scene_desc = self.get_scene_description()
        if scene_desc:
            context_parts.append(f"Scene Description:\n{scene_desc}")
        
        # Search for relevant elements
        elements = self._parsed_sections.get('scene_elements', [])
        for element in elements:
            if any(keyword in query_lower for keyword in element['element'].lower().split()):
                context_parts.append(f"Element: {element['element']} - {element['purpose']}")
        
        # Search for relevant controls
        switches = self._parsed_sections.get('switch_controls', [])
        values = self._parsed_sections.get('value_controls', [])
        
        for control in switches + values:
            if any(keyword in query_lower for keyword in control['control'].lower().split()):
                context_parts.append(f"Control: {control['control']} - {control['description']}")
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def get_full_context(self) -> str:
        """Get the complete scene reference content."""
        return self._content or ""


# Global instance
scene_context_loader = SceneContextLoader()

