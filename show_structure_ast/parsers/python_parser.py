#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Python code parser using AST

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import ast
import logging
import traceback
from typing import List, Optional

from ..models import CodeElement
from ..filters import FilterContext

logger = logging.getLogger(__name__)


class PythonParser:
    """Parser for Python files using AST"""
    
    def parse(self, content: str, filename: str, filter_context: FilterContext,
              include_variables: bool = False) -> List[CodeElement]:
        """Parse Python content and return code elements"""
        try:
            tree = ast.parse(content, filename=filename)
            elements = []
            self._process_node(tree, elements, filter_context, parent=None, 
                             include_variables=include_variables, depth=0)
            return elements
        except SyntaxError as e:
            logger.error(f"Python syntax error at line {e.lineno}: {e.msg}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing Python file: {e}")
            logger.debug(traceback.format_exc())
            return []
    
    def _process_node(self, node: ast.AST, elements: List[CodeElement],
                      filter_context: FilterContext,
                      parent: Optional[str] = None, 
                      parent_element: Optional[CodeElement] = None,
                      include_variables: bool = False,
                      depth: int = 0):
        """Recursively process AST nodes with early filtering"""
        # Check if we should continue traversing based on depth
        if not filter_context.should_traverse_children(depth):
            return
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                # Early filter check
                if not filter_context.should_process_element('class', child.name, depth=depth):
                    continue
                
                class_elem = CodeElement(
                    type='class',
                    name=child.name,
                    line_start=child.lineno,
                    line_end=self._get_end_line(child),
                    parent=parent,
                    decorators=[self._get_decorator_name(d) for d in child.decorator_list]
                )
                
                # Apply decorator filter
                if filter_context.filter_decorator and filter_context.filter_decorator not in class_elem.decorators:
                    continue
                
                elements.append(class_elem)
                if parent_element:
                    parent_element.children.append(class_elem)
                
                # Process methods within class
                self._process_node(child, elements, filter_context, parent=child.name, 
                                 parent_element=class_elem, include_variables=include_variables,
                                 depth=depth + 1)
                
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visibility = self._get_python_visibility(child.name)
                
                # Early filter check
                if not filter_context.should_process_element(
                    'method' if parent else 'function', child.name, 
                    visibility=visibility, depth=depth):
                    continue
                
                func_elem = CodeElement(
                    type='method' if parent else 'function',
                    name=child.name,
                    line_start=child.lineno,
                    line_end=self._get_end_line(child),
                    visibility=visibility,
                    parent=parent,
                    signature=self._get_function_signature(child),
                    decorators=[self._get_decorator_name(d) for d in child.decorator_list]
                )
                
                # Apply decorator filter
                if filter_context.filter_decorator and filter_context.filter_decorator not in func_elem.decorators:
                    continue
                
                elements.append(func_elem)
                if parent_element:
                    parent_element.children.append(func_elem)
                    
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                # Early filter check
                if not filter_context.should_process_element('import', self._get_import_name(child), depth=depth):
                    continue
                
                import_elem = CodeElement(
                    type='import',
                    name=self._get_import_name(child),
                    line_start=child.lineno,
                    line_end=child.lineno
                )
                elements.append(import_elem)
                
            elif include_variables and isinstance(child, ast.Assign) and not parent:
                # Top-level variable assignments
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        # Early filter check
                        if not filter_context.should_process_element('variable', target.id, depth=depth):
                            continue
                        
                        var_elem = CodeElement(
                            type='variable',
                            name=target.id,
                            line_start=child.lineno,
                            line_end=child.lineno
                        )
                        elements.append(var_elem)
                
            else:
                # Continue traversing
                self._process_node(child, elements, filter_context, parent=parent, 
                                 parent_element=parent_element, include_variables=include_variables,
                                 depth=depth)
    
    def _get_end_line(self, node: ast.AST) -> int:
        """Get the end line of a node"""
        try:
            if hasattr(node, 'end_lineno'):
                return node.end_lineno
            # Fallback: traverse to find last line
            max_line = node.lineno
            for child in ast.walk(node):
                if hasattr(child, 'lineno'):
                    max_line = max(max_line, child.lineno)
            return max_line
        except Exception:
            return node.lineno if hasattr(node, 'lineno') else 1
    
    def _get_python_visibility(self, name: str) -> str:
        """Determine Python visibility based on naming convention"""
        if name.startswith('__') and not name.endswith('__'):
            return 'private'
        elif name.startswith('_'):
            return 'protected'
        else:
            return 'public'
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature"""
        try:
            args = []
            for arg in node.args.args:
                args.append(arg.arg)
            return f"{node.name}({', '.join(args)})"
        except Exception:
            return f"{node.name}(...)"
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name from AST node"""
        try:
            if isinstance(decorator, ast.Name):
                return f"@{decorator.id}"
            elif isinstance(decorator, ast.Attribute):
                return f"@{decorator.attr}"
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    return f"@{decorator.func.id}"
                elif isinstance(decorator.func, ast.Attribute):
                    return f"@{decorator.func.attr}"
        except Exception:
            pass
        return "@decorator"
    
    def _get_import_name(self, node: ast.AST) -> str:
        """Get import statement as string"""
        try:
            if isinstance(node, ast.Import):
                return f"import {', '.join(alias.name for alias in node.names)}"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                return f"from {module} import {', '.join(alias.name for alias in node.names)}"
        except Exception:
            pass
        return "import"