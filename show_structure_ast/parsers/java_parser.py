#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Java code parser with AST and regex fallback

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import logging
import traceback
from typing import List, Optional

from ..models import CodeElement
from ..filters import FilterContext
from ..preprocessor import ContentPreprocessor

logger = logging.getLogger(__name__)

# Optional import for javalang
try:
    import javalang
    JAVA_SUPPORT = True
except ImportError:
    JAVA_SUPPORT = False
    logger.debug("javalang not available - Java parsing will use enhanced regex fallback")


class JavaParser:
    """Enhanced parser for Java files with better regex fallback"""
    
    def __init__(self):
        self.preprocessor = ContentPreprocessor()
    
    def parse(self, content: str, filename: str, filter_context: FilterContext,
              include_variables: bool = False, skip_preprocessing: bool = False) -> List[CodeElement]:
        """Parse Java content and return code elements"""
        if JAVA_SUPPORT:
            try:
                return self._parse_with_javalang(content, filename, filter_context, include_variables)
            except Exception as e:
                logger.warning(f"Java AST parsing failed: {e}")
                logger.info("Falling back to enhanced regex parsing")
        
        return self._parse_with_regex(content, filename, filter_context, include_variables, skip_preprocessing)
    
    def _parse_with_javalang(self, content: str, filename: str, filter_context: FilterContext,
                           include_variables: bool) -> List[CodeElement]:
        """Parse using javalang library with defensive error handling"""
        try:
            tree = javalang.parse.parse(content)
            elements = []
            lines = content.split('\n')
            
            # Process package
            if tree.package:
                package_name = f"package {tree.package.name}"
                if filter_context.should_process_element('package', package_name):
                    elements.append(CodeElement(
                        type='package',
                        name=package_name,
                        line_start=1,
                        line_end=1
                    ))
            
            # Process imports
            for imp in tree.imports:
                import_name = f"import {imp.path}"
                if filter_context.should_process_element('import', import_name):
                    elements.append(CodeElement(
                        type='import',
                        name=import_name,
                        line_start=1,  # javalang doesn't provide line numbers
                        line_end=1
                    ))
            
            # Process types (classes, interfaces, enums)
            for path, node in tree.filter(javalang.tree.TypeDeclaration):
                if isinstance(node, javalang.tree.ClassDeclaration):
                    visibility = self._get_java_visibility(node.modifiers)
                    annotations = self._get_java_annotations(node)
                    
                    # Early filter check
                    if not filter_context.should_process_element('class', node.name, visibility=visibility,
                                                                annotations=annotations):
                        continue
                    
                    class_line = self._find_line_number(lines, f"class {node.name}")
                    class_elem = CodeElement(
                        type='class',
                        name=node.name,
                        line_start=class_line,
                        line_end=self._find_closing_brace(lines, class_line),
                        visibility=visibility,
                        annotations=annotations
                    )
                    elements.append(class_elem)
                    
                    # Process methods
                    for method in node.methods:
                        method_visibility = self._get_java_visibility(method.modifiers)
                        method_annotations = self._get_java_annotations(method)
                        
                        # Early filter check
                        if not filter_context.should_process_element('method', method.name, 
                                                                    visibility=method_visibility, depth=1,
                                                                    annotations=method_annotations):
                            continue
                        
                        method_line = self._find_method_line(lines, method, class_line)
                        method_elem = CodeElement(
                            type='method',
                            name=method.name,
                            line_start=method_line,
                            line_end=self._find_closing_brace(lines, method_line),
                            visibility=method_visibility,
                            parent=node.name,
                            signature=self._get_method_signature(method),
                            annotations=method_annotations
                        )
                        elements.append(method_elem)
                        class_elem.children.append(method_elem)
                    
                    # Process fields
                    if include_variables or filter_context.include_fields:
                        for field in node.fields:
                            field_visibility = self._get_java_visibility(field.modifiers)
                            for declarator in field.declarators:
                                # Early filter check
                                if not filter_context.should_process_element('field', declarator.name,
                                                                            visibility=field_visibility, depth=1):
                                    continue
                                
                                field_line = self._find_line_number(lines, declarator.name, class_line)
                                field_elem = CodeElement(
                                    type='field',
                                    name=declarator.name,
                                    line_start=field_line,
                                    line_end=field_line,
                                    visibility=field_visibility,
                                    parent=node.name
                                )
                                elements.append(field_elem)
                                class_elem.children.append(field_elem)
            
            return elements
            
        except javalang.parser.JavaSyntaxError as e:
            logger.error(f"Java syntax error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Java parsing: {e}")
            logger.debug(traceback.format_exc())
            raise  # Re-raise to trigger fallback
    
    def _parse_with_regex(self, content: str, filename: str, filter_context: FilterContext,
                         include_variables: bool, skip_preprocessing: bool = False) -> List[CodeElement]:
        """Simplified regex-based parser for Java with defensive error handling"""
        try:
            lines = content.split('\n')
            elements = []
            
            # Optionally preprocess for very large or complex files
            if not skip_preprocessing and self.preprocessor.should_preprocess(content, 'java'):
                try:
                    content = self.preprocessor.strip_strings_and_comments_simple(content, 'java')
                    lines = content.split('\n')
                except Exception as e:
                    logger.debug(f"Preprocessing failed, using original content: {e}")
            
            # Simplified patterns
            package_pattern = re.compile(r'^\s*package\s+([\w.]+)\s*;')
            import_pattern = re.compile(r'^\s*import\s+(?:static\s+)?([\w.*]+)\s*;')
            class_pattern = re.compile(r'^\s*(public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:abstract\s+)?class\s+(\w+)')
            method_pattern = re.compile(r'^\s*(public|private|protected)?\s*(?:static\s+)?(?:final\s+)?[\w<>\[\]]+\s+(\w+)\s*\(')
            field_pattern = re.compile(r'^\s*(public|private|protected)?\s*(?:static\s+)?(?:final\s+)?[\w<>\[\]]+\s+(\w+)\s*[=;]')
            annotation_pattern = re.compile(r'^\s*@(\w+)(?:\([^)]*\))?')
            
            current_class = None
            brace_count = 0
            class_stack = []
            pending_annotations = []  # Collect annotations for next element
            
            for i, line in enumerate(lines, 1):
                try:
                    # Skip empty lines and obvious comments
                    if not line.strip() or line.strip().startswith('//'):
                        continue
                    
                    # Check for annotations
                    annotation_match = annotation_pattern.match(line)
                    if annotation_match:
                        annotation_name = f"@{annotation_match.group(1)}"
                        pending_annotations.append(annotation_name)
                        continue
                    
                    # Track braces
                    open_braces = line.count('{')
                    close_braces = line.count('}')
                    brace_count += open_braces - close_braces
                    
                    # Handle closing braces
                    if close_braces > 0 and class_stack:
                        while close_braces > 0 and class_stack:
                            if brace_count <= class_stack[-1][1]:
                                elem = class_stack.pop()[0]
                                elem.line_end = i
                                if elem == current_class:
                                    current_class = class_stack[-1][0] if class_stack else None
                            close_braces -= 1
                    
                    # Check for package
                    if not current_class:
                        package_match = package_pattern.match(line)
                        if package_match:
                            package_name = f"package {package_match.group(1)}"
                            if filter_context.should_process_element('package', package_name):
                                elements.append(CodeElement(
                                    type='package',
                                    name=package_name,
                                    line_start=i,
                                    line_end=i
                                ))
                            continue
                        
                        # Check for import
                        import_match = import_pattern.match(line)
                        if import_match:
                            import_name = f"import {import_match.group(1)}"
                            if filter_context.should_process_element('import', import_name):
                                elements.append(CodeElement(
                                    type='import',
                                    name=import_name,
                                    line_start=i,
                                    line_end=i
                                ))
                            continue
                    
                    # Check for class
                    class_match = class_pattern.match(line)
                    if class_match:
                        visibility = class_match.group(1) or 'package-private'
                        class_name = class_match.group(2)
                        
                        # Early filter check
                        if not filter_context.should_process_element('class', class_name, visibility=visibility,
                                                                    annotations=pending_annotations):
                            pending_annotations = []  # Clear annotations even if filtered
                            continue
                        
                        class_elem = CodeElement(
                            type='class',
                            name=class_name,
                            line_start=i,
                            line_end=i,  # Will be updated
                            visibility=visibility,
                            annotations=pending_annotations.copy()
                        )
                        pending_annotations = []  # Clear after use
                        elements.append(class_elem)
                        if current_class:
                            current_class.children.append(class_elem)
                        current_class = class_elem
                        class_stack.append((class_elem, brace_count))
                        continue
                    
                    # Inside a class, look for methods and fields
                    if current_class and filter_context.should_traverse_children(len(class_stack)):
                        # Check for method
                        method_match = method_pattern.match(line)
                        if method_match and '=' not in line:  # Avoid matching field assignments
                            visibility = method_match.group(1) or 'package-private'
                            method_name = method_match.group(2)
                            # Skip constructors that look like method calls
                            if method_name not in ['new', 'if', 'while', 'for', 'switch']:
                                # Early filter check
                                if filter_context.should_process_element('method', method_name, 
                                                                       visibility=visibility, depth=len(class_stack),
                                                                       annotations=pending_annotations):
                                    method_elem = CodeElement(
                                        type='method',
                                        name=method_name,
                                        line_start=i,
                                        line_end=i,  # Simple assumption
                                        visibility=visibility,
                                        parent=current_class.name,
                                        annotations=pending_annotations.copy()
                                    )
                                    elements.append(method_elem)
                                    current_class.children.append(method_elem)
                                pending_annotations = []  # Clear after use
                                continue
                        
                        # Check for field
                        if include_variables or filter_context.include_fields:
                            field_match = field_pattern.match(line)
                            if field_match and '(' not in line:  # Avoid matching method declarations
                                visibility = field_match.group(1) or 'package-private'
                                field_name = field_match.group(2)
                                # Early filter check
                                if filter_context.should_process_element('field', field_name,
                                                                       visibility=visibility, depth=len(class_stack)):
                                    field_elem = CodeElement(
                                        type='field',
                                        name=field_name,
                                        line_start=i,
                                        line_end=i,
                                        visibility=visibility,
                                        parent=current_class.name
                                    )
                                    elements.append(field_elem)
                                    current_class.children.append(field_elem)
                    
                    # Clear pending annotations if line contains code but no match
                    if line.strip() and not line.strip().startswith('@'):
                        pending_annotations = []
                        
                except Exception as e:
                    logger.debug(f"Error processing line {i}: {e}")
                    continue
            
            # Close any remaining open elements
            while class_stack:
                elem = class_stack.pop()[0]
                elem.line_end = len(lines)
            
            return elements
            
        except Exception as e:
            logger.error(f"Regex parsing failed for Java file: {e}")
            logger.debug(traceback.format_exc())
            return []
    
    def _get_java_visibility(self, modifiers: List[str]) -> str:
        """Get Java visibility from modifiers"""
        if not modifiers:
            return 'package-private'
        for mod in modifiers:
            if mod in ['public', 'private', 'protected']:
                return mod
        return 'package-private'
    
    def _get_java_annotations(self, node) -> List[str]:
        """Extract Java annotations from a node"""
        annotations = []
        try:
            if hasattr(node, 'annotations') and node.annotations:
                for annotation in node.annotations:
                    if hasattr(annotation, 'name'):
                        # Handle simple annotations like @Override
                        annotations.append(f"@{annotation.name}")
                    elif hasattr(annotation, 'element') and hasattr(annotation.element, 'name'):
                        # Handle annotations with values like @Test(timeout=5000)
                        annotations.append(f"@{annotation.element.name}")
        except Exception as e:
            logger.debug(f"Error extracting annotations: {e}")
        return annotations
    
    def _get_method_signature(self, method) -> str:
        """Get method signature with defensive error handling"""
        try:
            params = []
            if hasattr(method, 'parameters'):
                for param in method.parameters:
                    params.append(f"{param.type.name} {param.name}")
            return f"{method.name}({', '.join(params)})"
        except Exception:
            return f"{method.name}(...)"
    
    def _find_line_number(self, lines: List[str], text: str, start_from: int = 0) -> int:
        """Find line number containing text"""
        try:
            for i in range(start_from, len(lines)):
                if text in lines[i]:
                    return i + 1
        except Exception:
            pass
        return 1
    
    def _find_method_line(self, lines: List[str], method, start_from: int) -> int:
        """Find method definition line"""
        try:
            # Look for method name with parenthesis
            for i in range(start_from - 1, len(lines)):
                if method.name in lines[i] and '(' in lines[i]:
                    return i + 1
        except Exception:
            pass
        return start_from
    
    def _find_closing_brace(self, lines: List[str], start_line: int) -> int:
        """Find the closing brace for a block starting at start_line"""
        try:
            brace_count = 0
            for i in range(start_line - 1, len(lines)):
                line = lines[i]
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0 and '}' in line:
                    return i + 1
        except Exception:
            pass
        return len(lines)