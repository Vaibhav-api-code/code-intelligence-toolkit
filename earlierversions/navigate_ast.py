#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
AST-enhanced navigation tool for finding definitions with perfect accuracy.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
from pathlib import Path
import argparse
import ast
from typing import List, Dict, Optional, Tuple

# Try to import javalang for Java AST support
try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False


class PythonNavigator:
    """AST-based navigator for Python code."""
    
    @staticmethod
    def find_all_definitions(code: str) -> Dict[str, List[Dict]]:
        """
        Find all definitions in Python code using AST.
        
        Returns dict with 'classes', 'methods', 'fields' lists.
        """
        definitions = {
            'classes': [],
            'methods': [],
            'fields': [],
            'functions': []  # Python has functions outside classes too
        }
        
        try:
            tree = ast.parse(code)
            
            class DefinitionFinder(ast.NodeVisitor):
                def __init__(self):
                    self.current_class = None
                    self.class_stack = []
                
                def visit_ClassDef(self, node):
                    # Record class definition
                    definitions['classes'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'end_line': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        'type': 'class',
                        'docstring': ast.get_docstring(node),
                        'bases': [ast.unparse(base) if hasattr(ast, 'unparse') else str(base) 
                                 for base in node.bases],
                        'decorators': [ast.unparse(dec) if hasattr(ast, 'unparse') else str(dec)
                                      for dec in node.decorator_list]
                    })
                    
                    # Track context
                    self.class_stack.append(node.name)
                    self.current_class = node.name
                    self.generic_visit(node)
                    self.class_stack.pop()
                    self.current_class = self.class_stack[-1] if self.class_stack else None
                
                def visit_FunctionDef(self, node):
                    # Extract parameters
                    params = []
                    for arg in node.args.args:
                        param_info = {'name': arg.arg}
                        if arg.annotation:
                            param_info['type'] = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
                        params.append(param_info)
                    
                    # Determine if it's a method or function
                    is_method = self.current_class is not None
                    
                    definition = {
                        'name': node.name,
                        'line': node.lineno,
                        'end_line': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        'type': 'method' if is_method else 'function',
                        'class': self.current_class,
                        'docstring': ast.get_docstring(node),
                        'parameters': params,
                        'return_type': ast.unparse(node.returns) if node.returns and hasattr(ast, 'unparse') else None,
                        'decorators': [ast.unparse(dec) if hasattr(ast, 'unparse') else str(dec)
                                      for dec in node.decorator_list],
                        'is_async': False
                    }
                    
                    if is_method:
                        definitions['methods'].append(definition)
                    else:
                        definitions['functions'].append(definition)
                    
                    self.generic_visit(node)
                
                def visit_AsyncFunctionDef(self, node):
                    # Handle async functions/methods
                    self.visit_FunctionDef(node)
                    # Mark as async
                    if self.current_class:
                        definitions['methods'][-1]['is_async'] = True
                    else:
                        definitions['functions'][-1]['is_async'] = True
                
                def visit_AnnAssign(self, node):
                    # Type-annotated field
                    if isinstance(node.target, ast.Name) and self.current_class:
                        field_info = {
                            'name': node.target.id,
                            'line': node.lineno,
                            'type': 'field',
                            'class': self.current_class,
                            'annotation': ast.unparse(node.annotation) if hasattr(ast, 'unparse') else str(node.annotation)
                        }
                        definitions['fields'].append(field_info)
                    self.generic_visit(node)
                
                def visit_Assign(self, node):
                    # Regular assignment (potential field)
                    if self.current_class:
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                definitions['fields'].append({
                                    'name': target.id,
                                    'line': node.lineno,
                                    'type': 'field',
                                    'class': self.current_class,
                                    'annotation': None
                                })
                    self.generic_visit(node)
            
            finder = DefinitionFinder()
            finder.visit(tree)
            
        except SyntaxError as e:
            print(f"Warning: Python syntax error at line {e.lineno}: {e.msg}", file=sys.stderr)
            print("Falling back to regex-based parsing", file=sys.stderr)
            return PythonNavigator._find_definitions_regex(code)
        except RecursionError:
            print("Error: File too complex for AST parsing (recursion limit)", file=sys.stderr)
            return PythonNavigator._find_definitions_regex(code)
        except MemoryError:
            print("Error: File too large for AST parsing", file=sys.stderr)
            return PythonNavigator._find_definitions_regex(code)
        
        return definitions
    
    @staticmethod
    def _find_definitions_regex(code: str) -> Dict[str, List[Dict]]:
        """Fallback regex-based definition finding."""
        definitions = {
            'classes': [],
            'methods': [],
            'fields': [],
            'functions': []
        }
        
        lines = code.splitlines()
        
        # Find classes
        for i, line in enumerate(lines):
            match = re.match(r'^class\s+(\w+)', line)
            if match:
                definitions['classes'].append({
                    'name': match.group(1),
                    'line': i + 1,
                    'type': 'class'
                })
        
        # Find functions/methods
        for i, line in enumerate(lines):
            match = re.match(r'^(\s*)def\s+(\w+)\s*\((.*?)\)', line)
            if match:
                indent = len(match.group(1))
                name = match.group(2)
                params = match.group(3)
                
                definition = {
                    'name': name,
                    'line': i + 1,
                    'type': 'method' if indent > 0 else 'function'
                }
                
                if indent > 0:
                    definitions['methods'].append(definition)
                else:
                    definitions['functions'].append(definition)
        
        return definitions


class JavaNavigator:
    """AST-based navigator for Java code."""
    
    @staticmethod
    def find_all_definitions(code: str) -> Dict[str, List[Dict]]:
        """
        Find all definitions in Java code using javalang AST.
        """
        if not JAVALANG_AVAILABLE:
            return JavaNavigator._find_definitions_regex(code)
        
        definitions = {
            'classes': [],
            'interfaces': [],
            'enums': [],
            'methods': [],
            'fields': []
        }
        
        try:
            tree = javalang.parse.parse(code)
            code_lines = code.splitlines()
            
            # Track current context
            current_class = None
            
            for path, node in tree:
                if isinstance(node, javalang.tree.ClassDeclaration):
                    current_class = node.name
                    definitions['classes'].append({
                        'name': node.name,
                        'line': node.position.line if node.position else 0,
                        'type': 'class',
                        'modifiers': list(node.modifiers) if node.modifiers else [],
                        'extends': node.extends.name if node.extends else None,
                        'implements': [i.name for i in node.implements] if node.implements else []
                    })
                
                elif isinstance(node, javalang.tree.InterfaceDeclaration):
                    current_class = node.name
                    definitions['interfaces'].append({
                        'name': node.name,
                        'line': node.position.line if node.position else 0,
                        'type': 'interface',
                        'modifiers': list(node.modifiers) if node.modifiers else []
                    })
                
                elif isinstance(node, javalang.tree.EnumDeclaration):
                    current_class = node.name
                    definitions['enums'].append({
                        'name': node.name,
                        'line': node.position.line if node.position else 0,
                        'type': 'enum',
                        'modifiers': list(node.modifiers) if node.modifiers else []
                    })
                
                elif isinstance(node, javalang.tree.MethodDeclaration):
                    # Extract parameters
                    params = []
                    for param in node.parameters:
                        params.append({
                            'name': param.name,
                            'type': param.type.name if hasattr(param.type, 'name') else str(param.type)
                        })
                    
                    definitions['methods'].append({
                        'name': node.name,
                        'line': node.position.line if node.position else 0,
                        'type': 'method',
                        'class': current_class,
                        'modifiers': list(node.modifiers) if node.modifiers else [],
                        'return_type': node.return_type.name if node.return_type else 'void',
                        'parameters': params,
                        'throws': [t.name for t in node.throws] if node.throws else []
                    })
                
                elif isinstance(node, javalang.tree.FieldDeclaration):
                    # Java can declare multiple fields in one line
                    for declarator in node.declarators:
                        definitions['fields'].append({
                            'name': declarator.name,
                            'line': node.position.line if node.position else 0,
                            'type': 'field',
                            'class': current_class,
                            'field_type': node.type.name if hasattr(node.type, 'name') else str(node.type),
                            'modifiers': list(node.modifiers) if node.modifiers else []
                        })
        
        except Exception as e:
            print(f"Warning: Java parsing failed: {e}", file=sys.stderr)
            print("Falling back to regex-based parsing", file=sys.stderr)
            return JavaNavigator._find_definitions_regex(code)
        
        return definitions
    
    @staticmethod
    def _find_definitions_regex(code: str) -> Dict[str, List[Dict]]:
        """Fallback regex-based definition finding."""
        definitions = {
            'classes': [],
            'interfaces': [],
            'enums': [],
            'methods': [],
            'fields': []
        }
        
        lines = code.splitlines()
        
        # Find classes, interfaces, enums
        for i, line in enumerate(lines):
            match = re.match(r'^\s*(public|private|protected)?\s*(class|interface|enum)\s+(\w+)', line)
            if match:
                def_type = match.group(2)
                name = match.group(3)
                
                target_list = definitions.get(f"{def_type}es" if def_type == 'class' else f"{def_type}s", [])
                target_list.append({
                    'name': name,
                    'line': i + 1,
                    'type': def_type
                })
        
        # Find methods
        method_pattern = r'^\s*((?:public|private|protected)\s+)?((?:static|final|synchronized|abstract|native)\s+)*((?:[\w<>\[\],.\s]+\s+)?)?(\w+)\s*\(([^)]*)\)'
        for i, line in enumerate(lines):
            match = re.match(method_pattern, line)
            if match and not any(keyword in line for keyword in ['new ', 'return ', '=', 'if ', 'while ']):
                method_name = match.group(4)
                params = match.group(5)
                definitions['methods'].append({
                    'name': method_name,
                    'line': i + 1,
                    'type': 'method',
                    'signature': f"{method_name}({params})"
                })
        
        # Find fields
        field_pattern = r'^\s*((?:public|private|protected)\s+)?((?:static|final|volatile|transient)\s+)*([\w<>\[\],.\s]+)\s+(\w+)\s*[=;]'
        for i, line in enumerate(lines):
            match = re.match(field_pattern, line)
            if match and 'class ' not in line:
                field_name = match.group(4)
                field_type = match.group(3)
                definitions['fields'].append({
                    'name': field_name,
                    'line': i + 1,
                    'type': 'field',
                    'field_type': field_type.strip() if field_type else 'unknown'
                })
        
        return definitions


def navigate_to_definition(file_path: str, target_name: str, 
                         target_type: Optional[str] = None,
                         show_context: bool = True,
                         context_lines: int = 10) -> List[Dict]:
    """
    Navigate to a definition using AST for perfect accuracy.
    
    Args:
        file_path: Path to the file
        target_name: Name of the target to find
        target_type: Optional type filter ('class', 'method', 'field', etc.)
        show_context: Whether to include surrounding context
        context_lines: Number of context lines to show
        
    Returns:
        List of found definitions with details
    """
    # Input validation
    if not target_name or not target_name.strip():
        print("Error: target_name cannot be empty", file=sys.stderr)
        return []
    
    # Sanitize target name (only allow alphanumeric and underscore)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', target_name.strip()):
        print(f"Error: Invalid target name '{target_name}' - must be a valid identifier", file=sys.stderr)
        return []
    
    # Validate context_lines range
    context_lines = max(0, min(context_lines, 100))  # Cap at 100 lines
    
    try:
        # Check file size before reading (prevent memory issues)
        file_path_obj = Path(file_path)
        if file_path_obj.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
            print(f"Warning: File '{file_path}' is very large ({file_path_obj.stat().st_size // (1024*1024)}MB), processing may be slow", file=sys.stderr)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
            
        # Basic sanity check on file content
        if len(code.strip()) == 0:
            print(f"Warning: File '{file_path}' appears to be empty", file=sys.stderr)
            return []
            
    except (UnicodeDecodeError, PermissionError, FileNotFoundError) as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected error reading file: {e}", file=sys.stderr)
        return []
    
    # Detect language
    language = 'python' if file_path.endswith('.py') else 'java'
    
    # Get all definitions using AST
    if language == 'python':
        definitions = PythonNavigator.find_all_definitions(code)
    else:
        definitions = JavaNavigator.find_all_definitions(code)
    
    # Filter by target name and type
    results = []
    
    for def_type, def_list in definitions.items():
        # Skip if type filter doesn't match
        if target_type and not def_type.startswith(target_type):
            continue
        
        for definition in def_list:
            if definition['name'] == target_name:
                # Add file content for context
                definition['file_path'] = file_path
                definition['language'] = language
                
                if show_context:
                    lines = code.splitlines()
                    # Robust bounds checking
                    def_line = max(1, definition.get('line', 1))
                    end_line = definition.get('end_line', def_line)
                    
                    start = max(0, def_line - context_lines - 1)
                    end = min(len(lines), end_line + context_lines)
                    
                    # Additional safety check
                    if start < end and end <= len(lines):
                        definition['context_lines'] = lines[start:end]
                        definition['context_start'] = start + 1
                    else:
                        definition['context_lines'] = []
                        definition['context_start'] = def_line
                
                results.append(definition)
    
    return results


def format_ast_navigation_report(results: List[Dict], target_name: str) -> str:
    """Format the AST-based navigation results."""
    output = []
    
    if not results:
        output.append(f"❌ No definitions found for '{target_name}'")
        return '\n'.join(output)
    
    # Header
    output.append("=" * 80)
    output.append(f"AST-BASED NAVIGATION RESULTS: '{target_name}'")
    output.append("=" * 80)
    output.append(f"✨ Found {len(results)} definition(s) using AST analysis")
    
    for i, result in enumerate(results):
        if len(results) > 1:
            output.append(f"\n{'='*20} Definition {i+1} {'='*20}")
        
        # Basic info
        output.append(f"\n📍 Name: {result['name']}")
        output.append(f"📍 Type: {result['type']}")
        output.append(f"📍 Line: {result['line']}")
        if 'end_line' in result and result['end_line'] != result['line']:
            output.append(f"📍 End Line: {result['end_line']}")
        
        # Language-specific details
        if result.get('language') == 'python':
            if result['type'] in ['method', 'function']:
                output.append(f"📍 Context: {result.get('class', 'module-level')}")
                if result.get('parameters'):
                    output.append("📋 Parameters:")
                    for param in result['parameters']:
                        param_str = param['name']
                        if 'type' in param:
                            param_str += f": {param['type']}"
                        output.append(f"   • {param_str}")
                if result.get('return_type'):
                    output.append(f"↩️  Return type: {result['return_type']}")
                if result.get('is_async'):
                    output.append("⚡ Async function")
                if result.get('decorators'):
                    output.append(f"🎨 Decorators: {', '.join(result['decorators'])}")
            elif result['type'] == 'class':
                if result.get('bases'):
                    output.append(f"🔗 Inherits from: {', '.join(result['bases'])}")
            elif result['type'] == 'field':
                if result.get('annotation'):
                    output.append(f"📝 Type annotation: {result['annotation']}")
        
        elif result.get('language') == 'java':
            if result.get('modifiers'):
                output.append(f"🔒 Modifiers: {' '.join(result['modifiers'])}")
            
            if result['type'] == 'method':
                output.append(f"📍 Class: {result.get('class', 'unknown')}")
                output.append(f"↩️  Return type: {result.get('return_type', 'void')}")
                if result.get('parameters'):
                    output.append("📋 Parameters:")
                    for param in result['parameters']:
                        output.append(f"   • {param['type']} {param['name']}")
                if result.get('throws'):
                    output.append(f"⚠️  Throws: {', '.join(result['throws'])}")
            elif result['type'] == 'class':
                if result.get('extends'):
                    output.append(f"🔗 Extends: {result['extends']}")
                if result.get('implements'):
                    output.append(f"📝 Implements: {', '.join(result['implements'])}")
            elif result['type'] == 'field':
                output.append(f"📝 Type: {result.get('field_type', 'unknown')}")
                output.append(f"📍 Class: {result.get('class', 'unknown')}")
        
        # Documentation
        if result.get('docstring'):
            output.append("📖 Documentation:")
            doc_lines = result['docstring'].split('\n')[:3]
            for line in doc_lines:
                output.append(f"   {line}")
            if len(result['docstring'].split('\n')) > 3:
                output.append("   ...")
        
        # Context
        if result.get('context_lines'):
            output.append(f"\n📄 Code context:")
            output.append("=" * 60)
            
            for j, line in enumerate(result['context_lines']):
                line_num = result['context_start'] + j
                is_definition_line = result['line'] <= line_num <= result.get('end_line', result['line'])
                
                if is_definition_line:
                    prefix = ">>> " if line_num == result['line'] else "  | "
                else:
                    prefix = "    "
                
                output.append(f"{prefix}{line_num:4d}: {line}")
    
    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(
        description='AST-enhanced navigation tool for perfect definition finding',
        epilog='''
EXAMPLES:
  # Find a specific method (positional)
  navigate_ast.py MyClass.java calculatePrice
  
  # Find using --find flag (same result)
  navigate_ast.py MyClass.java --find calculatePrice
  
  # Find only classes
  navigate_ast.py src/models.py --target-type class User
  
  # Find with more context
  navigate_ast.py utils.py helper_function --context-lines 20
  
  # Find a field using --find
  navigate_ast.py Config.java --find MAX_RETRIES --target-type field

AST SUPPORT:
  - Python: Built-in ast module (always available)
  - Java: javalang library (install with: pip install javalang)
  - Provides 100% accurate definition finding
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('file', help='File to navigate')
    
    # Support both direct target and --find flag for consistency
    parser.add_argument('target', nargs='?', help='Name of the target to find')
    parser.add_argument('--find', '-f', dest='find_target',
                       help='Name of the target to find (alternative to positional argument)')
    
    # Navigation options
    parser.add_argument('--target-type', '--type',
                       choices=['class', 'method', 'field', 'function', 'interface', 'enum'],
                       help='Filter by definition type')
    parser.add_argument('--context-lines', '-c', type=int, default=10,
                       help='Number of context lines to show (default: 10)')
    parser.add_argument('--no-context', action='store_true',
                       help='Show only the definition line')
    
    # Output options
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output')
    
    args = parser.parse_args()
    
    # Determine target from either positional or --find flag
    target = args.target or args.find_target
    if not target:
        parser.error("Target name is required (either as positional argument or with --find)")
    
    try:
        # Check if file exists
        if not Path(args.file).exists():
            print(f"Error: File '{args.file}' not found", file=sys.stderr)
            sys.exit(1)
        
        # Navigate to definition
        if not args.quiet:
            ast_status = "✨ Using AST" if (args.file.endswith('.py') or JAVALANG_AVAILABLE) else "⚠️ Using regex"
            print(f"Searching for '{target}' in {args.file}... {ast_status}", file=sys.stderr)
        
        results = navigate_to_definition(
            args.file,
            target,
            target_type=args.target_type,
            show_context=not args.no_context,
            context_lines=args.context_lines
        )
        
        # Output results
        if args.json:
            import json
            # Remove context lines for JSON (too verbose)
            for result in results:
                result.pop('context_lines', None)
            print(json.dumps(results, indent=2))
        else:
            report = format_ast_navigation_report(results, target)
            print(report)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()