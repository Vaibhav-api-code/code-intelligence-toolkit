#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
JavaScript/TypeScript code parser

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import logging
import traceback
from typing import List, Optional, Any

from ..models import CodeElement
from ..filters import FilterContext

logger = logging.getLogger(__name__)

# Optional import for esprima
try:
    import esprima
    JS_SUPPORT = True
except ImportError:
    JS_SUPPORT = False
    logger.debug("esprima not available - JavaScript parsing will use enhanced regex fallback")


class JavaScriptParser:
    """Parser for JavaScript/TypeScript files"""
    
    def parse(self, content: str, filename: str, filter_context: FilterContext,
              include_variables: bool = False) -> List[CodeElement]:
        """Parse JavaScript content and return code elements"""
        if JS_SUPPORT:
            try:
                return self._parse_with_esprima(content, filename, filter_context, include_variables)
            except Exception as e:
                logger.warning(f"JavaScript AST parsing failed: {e}")
                logger.info("Falling back to regex parsing")
        
        return self._parse_with_regex(content, filename, filter_context, include_variables)
    
    def _parse_with_esprima(self, content: str, filename: str, filter_context: FilterContext,
                           include_variables: bool) -> List[CodeElement]:
        """Parse using esprima library with defensive error handling"""
        try:
            tree = esprima.parseScript(content, loc=True, range=True)
            elements = []
            self._process_js_node(tree, elements, filter_context, include_variables=include_variables, depth=0)
            return elements
        except esprima.Error as e:
            logger.error(f"JavaScript syntax error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in JavaScript parsing: {e}")
            logger.debug(traceback.format_exc())
            raise  # Re-raise to trigger fallback
    
    def _process_js_node(self, node: Any, elements: List[CodeElement],
                        filter_context: FilterContext,
                        parent: Optional[str] = None, 
                        include_variables: bool = False,
                        depth: int = 0):
        """Process JavaScript AST nodes with early filtering"""
        # Check if we should continue traversing based on depth
        if not filter_context.should_traverse_children(depth):
            return
        
        if isinstance(node, dict):
            node_type = node.get('type')
            
            if node_type == 'FunctionDeclaration':
                func_name = node['id']['name'] if node.get('id') else 'anonymous'
                
                # Early filter check
                if not filter_context.should_process_element('function', func_name, depth=depth):
                    return
                
                func_elem = CodeElement(
                    type='function',
                    name=func_name,
                    line_start=node['loc']['start']['line'],
                    line_end=node['loc']['end']['line'],
                    parent=parent
                )
                elements.append(func_elem)
                
            elif node_type == 'ClassDeclaration':
                class_name = node['id']['name']
                
                # Early filter check
                if not filter_context.should_process_element('class', class_name, depth=depth):
                    return
                
                class_elem = CodeElement(
                    type='class',
                    name=class_name,
                    line_start=node['loc']['start']['line'],
                    line_end=node['loc']['end']['line']
                )
                elements.append(class_elem)
                
                # Process class body
                if 'body' in node and 'body' in node['body']:
                    for item in node['body']['body']:
                        self._process_js_node(item, elements, filter_context, 
                                            parent=class_name, 
                                            include_variables=include_variables,
                                            depth=depth + 1)
            
            elif include_variables and node_type == 'VariableDeclaration' and not parent:
                # Top-level variables
                for decl in node.get('declarations', []):
                    if decl.get('id', {}).get('type') == 'Identifier':
                        var_name = decl['id']['name']
                        
                        # Early filter check
                        if not filter_context.should_process_element('variable', var_name, depth=depth):
                            continue
                        
                        var_elem = CodeElement(
                            type='variable',
                            name=var_name,
                            line_start=node['loc']['start']['line'],
                            line_end=node['loc']['end']['line']
                        )
                        elements.append(var_elem)
            
            # Recursively process children
            for key, value in node.items():
                if isinstance(value, dict):
                    self._process_js_node(value, elements, filter_context, parent, 
                                        include_variables, depth)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self._process_js_node(item, elements, filter_context, parent, 
                                                include_variables, depth)
    
    def _parse_with_regex(self, content: str, filename: str, filter_context: FilterContext,
                         include_variables: bool) -> List[CodeElement]:
        """Simplified regex-based parser for JavaScript with defensive error handling"""
        try:
            lines = content.split('\n')
            elements = []
            
            # Simple patterns
            function_pattern = re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)')
            class_pattern = re.compile(r'^\s*(?:export\s+)?class\s+(\w+)')
            method_pattern = re.compile(r'^\s*(?:static\s+)?(?:async\s+)?(\w+)\s*\(')
            arrow_pattern = re.compile(r'^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*[^=]*=>')
            
            current_class = None
            brace_count = 0
            
            for i, line in enumerate(lines, 1):
                try:
                    # Track braces
                    brace_count += line.count('{') - line.count('}')
                    
                    # Check for class
                    class_match = class_pattern.match(line)
                    if class_match:
                        class_name = class_match.group(1)
                        
                        # Early filter check
                        if not filter_context.should_process_element('class', class_name):
                            continue
                        
                        class_elem = CodeElement(
                            type='class',
                            name=class_name,
                            line_start=i,
                            line_end=i  # Will update
                        )
                        elements.append(class_elem)
                        current_class = class_elem
                        continue
                    
                    # Check for function
                    func_match = function_pattern.match(line)
                    if func_match:
                        func_name = func_match.group(1)
                        
                        # Early filter check
                        if not filter_context.should_process_element('function', func_name, 
                                                                   depth=1 if current_class else 0):
                            continue
                        
                        func_elem = CodeElement(
                            type='function',
                            name=func_name,
                            line_start=i,
                            line_end=i,
                            parent=current_class.name if current_class else None
                        )
                        elements.append(func_elem)
                        if current_class:
                            current_class.children.append(func_elem)
                        continue
                    
                    # Check for arrow function
                    arrow_match = arrow_pattern.match(line)
                    if arrow_match:
                        func_name = arrow_match.group(1)
                        
                        # Early filter check
                        if not filter_context.should_process_element('function', func_name,
                                                                   depth=1 if current_class else 0):
                            continue
                        
                        func_elem = CodeElement(
                            type='function',
                            name=func_name,
                            line_start=i,
                            line_end=i,
                            parent=current_class.name if current_class else None
                        )
                        elements.append(func_elem)
                        if current_class:
                            current_class.children.append(func_elem)
                        continue
                    
                    # Reset current class when leaving its scope
                    if current_class and brace_count <= 0:
                        current_class.line_end = i
                        current_class = None
                        
                except Exception as e:
                    logger.debug(f"Error processing line {i}: {e}")
                    continue
            
            return elements
            
        except Exception as e:
            logger.error(f"Regex parsing failed for JavaScript file: {e}")
            logger.debug(traceback.format_exc())
            return []