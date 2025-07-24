#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
show_structure_ast_v3.py - Fixed version with improved filtering and performance

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import ast
import json
import argparse
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Pattern
from dataclasses import dataclass, asdict, field
from pathlib import Path
import configparser

# Setup logging
logging.basicConfig(level=logging.WARNING, format='%(message)s')
logger = logging.getLogger(__name__)

# Optional imports for additional language support
try:
    import javalang
    JAVA_SUPPORT = True
except ImportError:
    JAVA_SUPPORT = False
    logger.debug("javalang not available - Java parsing will use enhanced regex fallback")

try:
    import esprima
    JS_SUPPORT = True
except ImportError:
    JS_SUPPORT = False
    logger.debug("esprima not available - JavaScript parsing will use enhanced regex fallback")


@dataclass
class CodeElement:
    """Represents a code element (class, method, function, etc.)"""
    type: str  # 'class', 'method', 'function', 'field', 'import', 'variable'
    name: str
    line_start: int
    line_end: int
    visibility: Optional[str] = None  # public, private, protected
    parent: Optional[str] = None
    children: List['CodeElement'] = field(default_factory=list)
    signature: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    raw_text: Optional[str] = None  # For debugging
    
    @property
    def size(self) -> int:
        """Number of lines in this element"""
        return self.line_end - self.line_start + 1


class ContentPreprocessor:
    """Pre-processes code content to handle string literals and comments"""
    
    @staticmethod
    def should_preprocess(content: str, language: str) -> bool:
        """Determine if preprocessing is needed based on content characteristics"""
        # For small files, preprocessing overhead isn't worth it
        if len(content) < 50000:  # ~1000 lines
            return False
        
        # Check for complex string patterns that might confuse regex
        complex_patterns = [
            r'"\s*{',  # String containing brace
            r'{\s*"',  # Brace followed by string
            r'/\*.*\*/',  # Multi-line comments
            r'"[^"]*\\[^"]*"',  # Escaped quotes in strings
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, content[:5000]):  # Check first part only
                return True
        
        return False
    
    @staticmethod
    def strip_strings_and_comments_simple(content: str, language: str) -> str:
        """Simplified preprocessing - just remove obvious comments"""
        if language == 'java':
            # Remove single-line comments
            content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
            # Remove multi-line comments (simple cases)
            content = re.sub(r'/\*[^*]*\*/', '', content, flags=re.DOTALL)
        return content


class PythonParser:
    """Parser for Python files using AST"""
    
    def parse(self, content: str, filename: str, include_variables: bool = False) -> List[CodeElement]:
        """Parse Python content and return code elements"""
        try:
            tree = ast.parse(content, filename=filename)
            elements = []
            self._process_node(tree, elements, parent=None, include_variables=include_variables)
            return elements
        except SyntaxError as e:
            logger.error(f"Python syntax error at line {e.lineno}: {e.msg}")
            return []
    
    def _process_node(self, node: ast.AST, elements: List[CodeElement], 
                      parent: Optional[str] = None, parent_element: Optional[CodeElement] = None,
                      include_variables: bool = False):
        """Recursively process AST nodes"""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                class_elem = CodeElement(
                    type='class',
                    name=child.name,
                    line_start=child.lineno,
                    line_end=self._get_end_line(child),
                    parent=parent,
                    decorators=[self._get_decorator_name(d) for d in child.decorator_list]
                )
                elements.append(class_elem)
                if parent_element:
                    parent_element.children.append(class_elem)
                
                # Process methods within class
                self._process_node(child, elements, parent=child.name, parent_element=class_elem, 
                                 include_variables=include_variables)
                
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visibility = self._get_python_visibility(child.name)
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
                elements.append(func_elem)
                if parent_element:
                    parent_element.children.append(func_elem)
                    
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
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
                        var_elem = CodeElement(
                            type='variable',
                            name=target.id,
                            line_start=child.lineno,
                            line_end=child.lineno
                        )
                        elements.append(var_elem)
                
            else:
                # Continue traversing
                self._process_node(child, elements, parent=parent, parent_element=parent_element,
                                 include_variables=include_variables)
    
    def _get_end_line(self, node: ast.AST) -> int:
        """Get the end line of a node"""
        if hasattr(node, 'end_lineno'):
            return node.end_lineno
        # Fallback: traverse to find last line
        max_line = node.lineno
        for child in ast.walk(node):
            if hasattr(child, 'lineno'):
                max_line = max(max_line, child.lineno)
        return max_line
    
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
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        return f"{node.name}({', '.join(args)})"
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return f"@{decorator.id}"
        elif isinstance(decorator, ast.Attribute):
            return f"@{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return f"@{decorator.func.id}"
            elif isinstance(decorator.func, ast.Attribute):
                return f"@{decorator.func.attr}"
        return "@decorator"
    
    def _get_import_name(self, node: ast.AST) -> str:
        """Get import statement as string"""
        if isinstance(node, ast.Import):
            return f"import {', '.join(alias.name for alias in node.names)}"
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            return f"from {module} import {', '.join(alias.name for alias in node.names)}"
        return "import"


class JavaParser:
    """Enhanced parser for Java files with better regex fallback"""
    
    def __init__(self):
        self.preprocessor = ContentPreprocessor()
    
    def parse(self, content: str, filename: str, include_variables: bool = False, 
              skip_preprocessing: bool = False) -> List[CodeElement]:
        """Parse Java content and return code elements"""
        if JAVA_SUPPORT:
            try:
                return self._parse_with_javalang(content, filename, include_variables)
            except Exception as e:
                logger.warning(f"Java AST parsing failed: {e}")
                logger.info("Falling back to enhanced regex parsing")
        
        return self._parse_with_regex(content, filename, include_variables, skip_preprocessing)
    
    def _parse_with_javalang(self, content: str, filename: str, include_variables: bool) -> List[CodeElement]:
        """Parse using javalang library"""
        try:
            tree = javalang.parse.parse(content)
            elements = []
            lines = content.split('\n')
            
            # Process package
            if tree.package:
                elements.append(CodeElement(
                    type='package',
                    name=f"package {tree.package.name}",
                    line_start=1,
                    line_end=1
                ))
            
            # Process imports
            for imp in tree.imports:
                elements.append(CodeElement(
                    type='import',
                    name=f"import {imp.path}",
                    line_start=1,  # javalang doesn't provide line numbers
                    line_end=1
                ))
            
            # Process types (classes, interfaces, enums)
            for path, node in tree.filter(javalang.tree.TypeDeclaration):
                if isinstance(node, javalang.tree.ClassDeclaration):
                    class_line = self._find_line_number(lines, f"class {node.name}")
                    class_elem = CodeElement(
                        type='class',
                        name=node.name,
                        line_start=class_line,
                        line_end=self._find_closing_brace(lines, class_line),
                        visibility=self._get_java_visibility(node.modifiers)
                    )
                    elements.append(class_elem)
                    
                    # Process methods
                    for method in node.methods:
                        method_line = self._find_method_line(lines, method, class_line)
                        method_elem = CodeElement(
                            type='method',
                            name=method.name,
                            line_start=method_line,
                            line_end=self._find_closing_brace(lines, method_line),
                            visibility=self._get_java_visibility(method.modifiers),
                            parent=node.name,
                            signature=self._get_method_signature(method)
                        )
                        elements.append(method_elem)
                        class_elem.children.append(method_elem)
                    
                    # Process fields
                    for field in node.fields:
                        for declarator in field.declarators:
                            field_line = self._find_line_number(lines, declarator.name, class_line)
                            field_elem = CodeElement(
                                type='field',
                                name=declarator.name,
                                line_start=field_line,
                                line_end=field_line,
                                visibility=self._get_java_visibility(field.modifiers),
                                parent=node.name
                            )
                            elements.append(field_elem)
                            class_elem.children.append(field_elem)
            
            return elements
            
        except Exception as e:
            logger.error(f"Java parsing error: {e}")
            raise
    
    def _parse_with_regex(self, content: str, filename: str, include_variables: bool,
                         skip_preprocessing: bool = False) -> List[CodeElement]:
        """Simplified regex-based parser for Java"""
        import re
        
        lines = content.split('\n')
        elements = []
        
        # Optionally preprocess for very large or complex files
        if not skip_preprocessing and self.preprocessor.should_preprocess(content, 'java'):
            content = self.preprocessor.strip_strings_and_comments_simple(content, 'java')
            lines = content.split('\n')
        
        # Simplified patterns
        package_pattern = re.compile(r'^\s*package\s+([\w.]+)\s*;')
        import_pattern = re.compile(r'^\s*import\s+(?:static\s+)?([\w.*]+)\s*;')
        class_pattern = re.compile(r'^\s*(public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:abstract\s+)?class\s+(\w+)')
        method_pattern = re.compile(r'^\s*(public|private|protected)?\s*(?:static\s+)?(?:final\s+)?[\w<>\[\]]+\s+(\w+)\s*\(')
        field_pattern = re.compile(r'^\s*(public|private|protected)?\s*(?:static\s+)?(?:final\s+)?[\w<>\[\]]+\s+(\w+)\s*[=;]')
        
        current_class = None
        brace_count = 0
        class_stack = []
        
        for i, line in enumerate(lines, 1):
            # Skip empty lines and obvious comments
            if not line.strip() or line.strip().startswith('//'):
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
                    elements.append(CodeElement(
                        type='package',
                        name=f"package {package_match.group(1)}",
                        line_start=i,
                        line_end=i
                    ))
                    continue
                
                # Check for import
                import_match = import_pattern.match(line)
                if import_match:
                    elements.append(CodeElement(
                        type='import',
                        name=f"import {import_match.group(1)}",
                        line_start=i,
                        line_end=i
                    ))
                    continue
            
            # Check for class
            class_match = class_pattern.match(line)
            if class_match:
                visibility = class_match.group(1) or 'package-private'
                class_name = class_match.group(2)
                class_elem = CodeElement(
                    type='class',
                    name=class_name,
                    line_start=i,
                    line_end=i,  # Will be updated
                    visibility=visibility
                )
                elements.append(class_elem)
                if current_class:
                    current_class.children.append(class_elem)
                current_class = class_elem
                class_stack.append((class_elem, brace_count))
                continue
            
            # Inside a class, look for methods and fields
            if current_class:
                # Check for method
                method_match = method_pattern.match(line)
                if method_match and '=' not in line:  # Avoid matching field assignments
                    visibility = method_match.group(1) or 'package-private'
                    method_name = method_match.group(2)
                    # Skip constructors that look like method calls
                    if method_name not in ['new', 'if', 'while', 'for', 'switch']:
                        method_elem = CodeElement(
                            type='method',
                            name=method_name,
                            line_start=i,
                            line_end=i,  # Simple assumption
                            visibility=visibility,
                            parent=current_class.name
                        )
                        elements.append(method_elem)
                        current_class.children.append(method_elem)
                        continue
                
                # Check for field
                if include_variables or True:  # Always include fields for now
                    field_match = field_pattern.match(line)
                    if field_match and '(' not in line:  # Avoid matching method declarations
                        visibility = field_match.group(1) or 'package-private'
                        field_name = field_match.group(2)
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
        
        # Close any remaining open elements
        while class_stack:
            elem = class_stack.pop()[0]
            elem.line_end = len(lines)
        
        return elements
    
    def _get_java_visibility(self, modifiers: List[str]) -> str:
        """Get Java visibility from modifiers"""
        if not modifiers:
            return 'package-private'
        for mod in modifiers:
            if mod in ['public', 'private', 'protected']:
                return mod
        return 'package-private'
    
    def _get_method_signature(self, method) -> str:
        """Get method signature"""
        params = []
        if hasattr(method, 'parameters'):
            for param in method.parameters:
                params.append(f"{param.type.name} {param.name}")
        return f"{method.name}({', '.join(params)})"
    
    def _find_line_number(self, lines: List[str], text: str, start_from: int = 0) -> int:
        """Find line number containing text"""
        for i in range(start_from, len(lines)):
            if text in lines[i]:
                return i + 1
        return 1
    
    def _find_method_line(self, lines: List[str], method, start_from: int) -> int:
        """Find method definition line"""
        # Look for method name with parenthesis
        for i in range(start_from - 1, len(lines)):
            if method.name in lines[i] and '(' in lines[i]:
                return i + 1
        return start_from
    
    def _find_closing_brace(self, lines: List[str], start_line: int) -> int:
        """Find the closing brace for a block starting at start_line"""
        brace_count = 0
        for i in range(start_line - 1, len(lines)):
            line = lines[i]
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and '}' in line:
                return i + 1
        return len(lines)


class JavaScriptParser:
    """Parser for JavaScript/TypeScript files"""
    
    def parse(self, content: str, filename: str, include_variables: bool = False) -> List[CodeElement]:
        """Parse JavaScript content and return code elements"""
        if JS_SUPPORT:
            try:
                return self._parse_with_esprima(content, filename, include_variables)
            except Exception as e:
                logger.warning(f"JavaScript AST parsing failed: {e}")
                logger.info("Falling back to regex parsing")
        
        return self._parse_with_regex(content, filename, include_variables)
    
    def _parse_with_esprima(self, content: str, filename: str, include_variables: bool) -> List[CodeElement]:
        """Parse using esprima library"""
        try:
            tree = esprima.parseScript(content, loc=True, range=True)
            elements = []
            self._process_js_node(tree, elements, include_variables=include_variables)
            return elements
        except Exception as e:
            logger.error(f"JavaScript parsing error: {e}")
            raise
    
    def _process_js_node(self, node: Any, elements: List[CodeElement], 
                         parent: Optional[str] = None, include_variables: bool = False):
        """Process JavaScript AST nodes"""
        if isinstance(node, dict):
            node_type = node.get('type')
            
            if node_type == 'FunctionDeclaration':
                func_elem = CodeElement(
                    type='function',
                    name=node['id']['name'] if node.get('id') else 'anonymous',
                    line_start=node['loc']['start']['line'],
                    line_end=node['loc']['end']['line'],
                    parent=parent
                )
                elements.append(func_elem)
                
            elif node_type == 'ClassDeclaration':
                class_elem = CodeElement(
                    type='class',
                    name=node['id']['name'],
                    line_start=node['loc']['start']['line'],
                    line_end=node['loc']['end']['line']
                )
                elements.append(class_elem)
                
                # Process class body
                if 'body' in node and 'body' in node['body']:
                    for item in node['body']['body']:
                        self._process_js_node(item, elements, parent=node['id']['name'], 
                                            include_variables=include_variables)
            
            elif include_variables and node_type == 'VariableDeclaration' and not parent:
                # Top-level variables
                for decl in node.get('declarations', []):
                    if decl.get('id', {}).get('type') == 'Identifier':
                        var_elem = CodeElement(
                            type='variable',
                            name=decl['id']['name'],
                            line_start=node['loc']['start']['line'],
                            line_end=node['loc']['end']['line']
                        )
                        elements.append(var_elem)
            
            # Recursively process children
            for key, value in node.items():
                if isinstance(value, dict):
                    self._process_js_node(value, elements, parent, include_variables)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self._process_js_node(item, elements, parent, include_variables)
    
    def _parse_with_regex(self, content: str, filename: str, include_variables: bool) -> List[CodeElement]:
        """Simplified regex-based parser for JavaScript"""
        import re
        
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
            # Track braces
            brace_count += line.count('{') - line.count('}')
            
            # Check for class
            class_match = class_pattern.match(line)
            if class_match:
                class_name = class_match.group(1)
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
        
        return elements


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
    
    def analyze_file(self, filepath: Path, options: argparse.Namespace) -> List[CodeElement]:
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
            
            # Pass skip_preprocessing flag if available
            if hasattr(parser, 'parse') and 'skip_preprocessing' in parser.parse.__code__.co_varnames:
                elements = parser.parse(content, str(filepath), options.include_variables, 
                                      skip_preprocessing=options.no_preprocess)
            else:
                elements = parser.parse(content, str(filepath), options.include_variables)
            
            # Apply filters with improved logic
            elements = self._apply_filters_smart(elements, options)
            
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
            return []
    
    def _element_matches_filters(self, elem: CodeElement, options: argparse.Namespace) -> bool:
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
        
        # Decorator filter
        if options.filter_decorator:
            if not elem.decorators or options.filter_decorator not in elem.decorators:
                return False
        
        return True
    
    def _has_matching_children(self, elem: CodeElement, options: argparse.Namespace) -> bool:
        """Check if element or any of its descendants match filters"""
        # Check self
        if self._element_matches_filters(elem, options):
            return True
        
        # Check children recursively
        for child in elem.children:
            if self._has_matching_children(child, options):
                return True
        
        return False
    
    def _apply_filters_smart(self, elements: List[CodeElement], options: argparse.Namespace) -> List[CodeElement]:
        """Apply filters but keep parents if children match"""
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
            if options.filter_visibility or options.filter_name or options.filter_decorator:
                if not self._has_matching_children(elem, options):
                    continue
            
            # Recursively filter children
            if elem.children:
                elem.children = self._apply_filters_smart(elem.children, options)
            
            filtered.append(elem)
        
        return filtered
    
    def format_output(self, elements: List[CodeElement], options: argparse.Namespace) -> str:
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
            
            # Add decorators if present
            decorator_str = ""
            if elem.decorators:
                decorator_str = f" [{', '.join(elem.decorators)}]"
            
            # Add visibility for Java
            visibility_str = ""
            if elem.visibility and elem.visibility != 'public':
                visibility_str = f" [{elem.visibility}]"
            
            # Build the line
            line = f"{indent}{icon} {elem.name} {line_info}{visibility_str}{decorator_str}"
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


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced hierarchical code structure viewer (v3)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('file', help='File to analyze')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--include-fields', action='store_true', help='Include field/attribute definitions')
    parser.add_argument('--include-imports', action='store_true', help='Include import statements')
    parser.add_argument('--include-variables', action='store_true', help='Include variable declarations')
    parser.add_argument('--max-depth', type=int, help='Maximum nesting depth to display')
    parser.add_argument('--filter-visibility', nargs='+', 
                        choices=['public', 'private', 'protected', 'package-private'],
                        help='Filter by visibility')
    parser.add_argument('--filter-name', help='Filter elements by name using regex')
    parser.add_argument('--filter-decorator', help='Filter Python elements by decorator')
    parser.add_argument('--sort-by', choices=['line', 'name', 'size'], default='line',
                        help='Sort elements by criteria')
    parser.add_argument('--no-preprocess', action='store_true', 
                        help='Skip preprocessing (faster but less accurate)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    
    # Analyze file
    filepath = Path(args.file)
    analyzer = StructureAnalyzer()
    elements = analyzer.analyze_file(filepath, args)
    
    if not elements:
        if not args.json:
            print("No code elements found or unable to parse file", file=sys.stderr)
        else:
            print("[]")
        sys.exit(1)
    
    # Format and display
    output = analyzer.format_output(elements, args)
    print(output)


if __name__ == '__main__':
    main()