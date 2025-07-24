#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Main analyzer for code structure analysis

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import json
import logging
import traceback
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import asdict

from .models import CodeElement
from .filters import FilterContext
from .parsers import PythonParser, JavaParser, JavaScriptParser

logger = logging.getLogger(__name__)


class StructureAnalyzer:
    """Main analyzer that coordinates parsing and output"""
    
    def __init__(self):
        self.parsers = {
            '.py': PythonParser(),
            '.java': JavaParser(),
            '.js': JavaScriptParser(),
            '.jsx': JavaScriptParser(),
            '.ts': JavaScriptParser(),
            '.tsx': JavaScriptParser(),
        }
    
    def analyze_file(self, filepath: Path, options) -> List[CodeElement]:
        """Analyze a file and return structured elements"""
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return []
        
        suffix = filepath.suffix.lower()
        if suffix not in self.parsers:
            logger.error(f"Unsupported file type: {suffix}")
            logger.info(f"Supported types: {', '.join(self.parsers.keys())}")
            return []
        
        try:
            content = filepath.read_text(encoding='utf-8')
            parser = self.parsers[suffix]
            filter_context = FilterContext(options)
            
            # Pass filter context for early filtering
            if hasattr(parser, 'parse'):
                if 'filter_context' in parser.parse.__code__.co_varnames:
                    # New parsers with filter context support
                    if 'skip_preprocessing' in parser.parse.__code__.co_varnames:
                        elements = parser.parse(content, str(filepath), filter_context,
                                              options.include_variables, 
                                              skip_preprocessing=options.no_preprocess)
                    else:
                        elements = parser.parse(content, str(filepath), filter_context,
                                              options.include_variables)
                    
                    # Apply smart filtering for decorator/annotation filters that need parent-child logic
                    if (options.filter_decorator or 
                        (hasattr(options, 'filter_annotation') and options.filter_annotation)):
                        elements = self._apply_filters_smart(elements, options)
                else:
                    # Legacy parser interface
                    elements = parser.parse(content, str(filepath), options.include_variables)
                    # Apply filters after parsing
                    elements = self._apply_filters_smart(elements, options)
            else:
                elements = []
            
            # Sort elements
            if options.sort_by == 'name':
                elements.sort(key=lambda e: e.name.lower())
            elif options.sort_by == 'size':
                elements.sort(key=lambda e: e.size, reverse=True)
            else:  # default: line
                elements.sort(key=lambda e: e.line_start)
            
            return elements
            
        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
            logger.debug(traceback.format_exc())
            return []
    
    def _element_matches_filters(self, elem: CodeElement, options) -> bool:
        """Check if an element matches the filters"""
        # Visibility filter
        if options.filter_visibility and elem.visibility not in options.filter_visibility:
            return False
        
        # Name filter (regex)
        if options.filter_name:
            try:
                pattern = re.compile(options.filter_name)
                if not pattern.search(elem.name):  # Use search instead of match
                    return False
            except re.error:
                logger.warning(f"Invalid regex pattern: {options.filter_name}")
        
        # Decorator filter (Python)
        if options.filter_decorator:
            if not elem.decorators or options.filter_decorator not in elem.decorators:
                return False
        
        # Annotation filter (Java)
        if hasattr(options, 'filter_annotation') and options.filter_annotation:
            if not elem.annotations or options.filter_annotation not in elem.annotations:
                return False
        
        return True
    
    def _has_matching_children(self, elem: CodeElement, options) -> bool:
        """Check if element or any of its descendants match filters"""
        # Check self
        if self._element_matches_filters(elem, options):
            return True
        
        # Check children recursively
        for child in elem.children:
            if self._has_matching_children(child, options):
                return True
        
        return False
    
    def _apply_filters_smart(self, elements: List[CodeElement], options) -> List[CodeElement]:
        """Apply filters but keep parents if children match (legacy support)"""
        filtered = []
        
        for elem in elements:
            # Type filters (these remove elements completely)
            if not options.include_imports and elem.type == 'import':
                continue
            if not options.include_fields and elem.type == 'field':
                continue
            if not options.include_variables and elem.type == 'variable':
                continue
            
            # For other filters, keep element if it or any children match
            if (options.filter_visibility or options.filter_name or options.filter_decorator or 
                (hasattr(options, 'filter_annotation') and options.filter_annotation)):
                if not self._has_matching_children(elem, options):
                    continue
            
            # Recursively filter children
            if elem.children:
                elem.children = self._apply_filters_smart(elem.children, options)
            
            filtered.append(elem)
        
        return filtered
    
    def format_output(self, elements: List[CodeElement], options) -> str:
        """Format elements for display"""
        if options.json:
            return self._format_json(elements)
        else:
            return self._format_text(elements, options.max_depth)
    
    def _format_json(self, elements: List[CodeElement]) -> str:
        """Format as JSON"""
        def element_to_dict(elem: CodeElement) -> Dict:
            d = asdict(elem)
            d['children'] = [element_to_dict(child) for child in elem.children]
            return d
        
        data = [element_to_dict(elem) for elem in elements if elem.parent is None]
        return json.dumps(data, indent=2)
    
    def _format_text(self, elements: List[CodeElement], max_depth: Optional[int]) -> str:
        """Format as hierarchical text"""
        output = []
        
        # Filter to get only root elements (those without parents)
        roots = [elem for elem in elements if elem.parent is None]
        
        # Build output
        def format_element(elem: CodeElement, depth: int = 0) -> None:
            if max_depth is not None and depth > max_depth:
                return
            
            indent = "  " * depth
            icon = self._get_icon(elem.type)
            
            # Format line info
            line_info = f"(lines {elem.line_start}-{elem.line_end})"
            
            # Add decorators if present (Python)
            decorator_str = ""
            if elem.decorators:
                decorator_str = f" [{', '.join(elem.decorators)}]"
            
            # Add annotations if present (Java)
            annotation_str = ""
            if elem.annotations:
                annotation_str = f" [{', '.join(elem.annotations)}]"
            
            # Add visibility for Java
            visibility_str = ""
            if elem.visibility and elem.visibility != 'public':
                visibility_str = f" [{elem.visibility}]"
            
            # Build the line
            line = f"{indent}{icon} {elem.name} {line_info}{visibility_str}{decorator_str}{annotation_str}"
            output.append(line)
            
            # Add children from the element's children list
            for child in elem.children:
                format_element(child, depth + 1)
        
        # Start with roots
        for root in roots:
            format_element(root)
        
        return '\n'.join(output)
    
    def _get_icon(self, elem_type: str) -> str:
        """Get icon for element type"""
        icons = {
            'package': '📦',
            'import': '📥',
            'class': '📋',
            'method': '🔧',
            'function': '🔧',
            'field': '📌',
            'variable': '📊',
        }
        return icons.get(elem_type, '•')