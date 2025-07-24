#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
navigate_ast v2 - Navigate to code locations with standardized interface.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import ast
import re
import argparse
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Import standard parser

# Import standard argument parser
try:
    from standard_arg_parser import create_standard_parser as create_parser
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False
    
    def create_parser(tool_type, description):
        return argparse.ArgumentParser(description=description)

# Import preflight checks
try:
    from preflight_checks import run_preflight_checks, PreflightChecker
except ImportError:
    def run_preflight_checks(checks, exit_on_fail=True):
        pass
    class PreflightChecker:
        @staticmethod
        def check_file_readable(path):
            return True, ""
        @staticmethod
        def check_directory_accessible(path):
            return True, ""
        @staticmethod
        def check_ripgrep_installed():
            return True, ""
        @staticmethod
        def check_regex_pattern(pattern):
            return True, ""

try:
    from standard_arg_parser import create_standard_parser, parse_standard_args
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False

# Try to import javalang for Java support
try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False

def find_python_symbol(file_path: str, symbol_name: str, symbol_type: str = 'auto') -> List[Dict]:
    """Find symbol in Python file using AST."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        results = []
        
        class SymbolFinder(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                if symbol_type in ['auto', 'function', 'method'] and node.name == symbol_name:
                    results.append({
                        'type': 'function',
                        'name': node.name,
                        'line': node.lineno,
                        'col_offset': node.col_offset,
                        'signature': self._get_function_signature(node)
                    })
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)
            
            def visit_ClassDef(self, node):
                if symbol_type in ['auto', 'class'] and node.name == symbol_name:
                    results.append({
                        'type': 'class',
                        'name': node.name,
                        'line': node.lineno,
                        'col_offset': node.col_offset,
                        'bases': [ast.unparse(base) if hasattr(ast, 'unparse') else str(base) for base in node.bases]
                    })
                self.generic_visit(node)
            
            def visit_Assign(self, node):
                # Look for variable assignments
                if symbol_type in ['auto', 'variable']:
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == symbol_name:
                            results.append({
                                'type': 'variable',
                                'name': symbol_name,
                                'line': node.lineno,
                                'col_offset': node.col_offset
                            })
                self.generic_visit(node)
            
            def _get_function_signature(self, node):
                """Extract function signature."""
                args = []
                for arg in node.args.args:
                    args.append(arg.arg)
                return f"{node.name}({', '.join(args)})"
        
        finder = SymbolFinder()
        finder.visit(tree)
        
        return results
        
    except Exception as e:
        print(f"Error parsing Python file: {e}", file=sys.stderr)
        return []

def find_java_symbol(file_path: str, symbol_name: str, symbol_type: str = 'auto') -> List[Dict]:
    """Find symbol in Java file using javalang AST."""
    if not JAVALANG_AVAILABLE:
        return find_symbol_regex(file_path, symbol_name, symbol_type, 'java')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = javalang.parse.parse(content)
        results = []
        
        for path, node in tree:
            if isinstance(node, javalang.tree.MethodDeclaration):
                if symbol_type in ['auto', 'method'] and node.name == symbol_name:
                    params = ', '.join(f"{p.type.name} {p.name}" for p in node.parameters)
                    results.append({
                        'type': 'method',
                        'name': node.name,
                        'line': node.position.line if node.position else 0,
                        'signature': f"{node.name}({params})"
                    })
            
            elif isinstance(node, javalang.tree.ClassDeclaration):
                if symbol_type in ['auto', 'class'] and node.name == symbol_name:
                    results.append({
                        'type': 'class',
                        'name': node.name,
                        'line': node.position.line if node.position else 0
                    })
            
            elif isinstance(node, javalang.tree.FieldDeclaration):
                if symbol_type in ['auto', 'variable', 'field']:
                    for declarator in node.declarators:
                        if declarator.name == symbol_name:
                            results.append({
                                'type': 'field',
                                'name': declarator.name,
                                'line': node.position.line if node.position else 0,
                                'field_type': node.type.name if hasattr(node.type, 'name') else str(node.type)
                            })
        
        return results
        
    except Exception as e:
        print(f"Error parsing Java file: {e}", file=sys.stderr)
        return find_symbol_regex(file_path, symbol_name, symbol_type, 'java')

def find_symbol_regex(file_path: str, symbol_name: str, symbol_type: str, language: str) -> List[Dict]:
    """Fallback regex-based symbol finding."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        results = []
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Python patterns
            if language == 'python':
                # Function definition
                if re.match(rf'^\\s*def\\s+{re.escape(symbol_name)}\\s*\\(', line):
                    results.append({
                        'type': 'function',
                        'name': symbol_name,
                        'line': i,
                        'content': line_stripped
                    })
                # Class definition
                elif re.match(rf'^\\s*class\\s+{re.escape(symbol_name)}\\s*[\\(:]', line):
                    results.append({
                        'type': 'class',
                        'name': symbol_name,
                        'line': i,
                        'content': line_stripped
                    })
            
            # Java patterns
            elif language == 'java':
                # Method definition
                if re.search(rf'\\b{re.escape(symbol_name)}\\s*\\(.*\\)\\s*\\{{?', line):
                    results.append({
                        'type': 'method',
                        'name': symbol_name,
                        'line': i,
                        'content': line_stripped
                    })
                # Class definition
                elif re.search(rf'\\bclass\\s+{re.escape(symbol_name)}\\b', line):
                    results.append({
                        'type': 'class',
                        'name': symbol_name,
                        'line': i,
                        'content': line_stripped
                    })
        
        return results
        
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return []

def show_location(file_path: str, line_number: int, context: int = 10, highlight: bool = True) -> None:
    """Show specific location in file with context."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start_line = max(1, line_number - context)
        end_line = min(len(lines), line_number + context)
        
        print(f"\\n📁 {file_path}")
        print("─" * min(80, len(file_path) + 4))
        
        for i in range(start_line - 1, end_line):
            current_line = i + 1
            line_content = lines[i].rstrip()
            
            # Highlight target line
            if current_line == line_number and highlight and sys.stdout.isatty():
                print(f"\\033[1;32m{current_line:6d}→ {line_content}\\033[0m")
            else:
                print(f"{current_line:6d}  {line_content}")
        
        print()
        
    except Exception as e:
        print(f"Error displaying location: {e}", file=sys.stderr)

def main():
    # Create parser - use basic ArgumentParser to avoid conflicts with standard parser expectations
    parser = argparse.ArgumentParser(description='navigate_ast v2 - Navigate to code locations')
    
    # File argument
    parser.add_argument('file', help='File to navigate in')
    
    # Target specification (one required)
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument('--to', help='Navigate to symbol (auto-detect type)')
    target_group.add_argument('--line', '-l', type=int, help='Go to line number')
    target_group.add_argument('--method', '-m', help='Go to method/function')
    target_group.add_argument('--class', '-c', dest='class_name', help='Go to class')
    target_group.add_argument('--variable', dest='var_name', help='Go to variable')
    
    # Options (only add if not already provided by standard parser)
    parser.add_argument('--context', '-C', type=int, default=10,
                       help='Lines of context to show around target (default: 10)')
    parser.add_argument('--highlight', action='store_true', default=True,
                       help='Highlight target line (default: true)')
    parser.add_argument('--no-highlight', dest='highlight', action='store_false',
                       help='Disable highlighting')
    
    # Add remaining options
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimize output, show only results')
    
    args = parser.parse_args()
    
    # Validate file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{args.file}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not file_path.is_file():
        print(f"Error: '{args.file}' is not a file", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Handle line number navigation
        if args.line:
            show_location(str(file_path), args.line, args.context, args.highlight)
            return
        
        # Determine target and type
        target = None
        symbol_type = 'auto'
        
        if args.to:
            target = args.to
            symbol_type = 'auto'
        elif args.method:
            target = args.method
            symbol_type = 'method'
        elif args.class_name:
            target = args.class_name
            symbol_type = 'class'
        elif hasattr(args, 'var_name') and args.var_name:
            target = args.var_name
            symbol_type = 'variable'
        
        if not target:
            print("Error: No target specified", file=sys.stderr)
            sys.exit(1)
        
        # Detect language
        language = 'auto'
        if str(file_path).endswith('.py'):
            language = 'python'
        elif str(file_path).endswith('.java'):
            language = 'java'
        
        # Find symbol
        if language == 'python':
            results = find_python_symbol(str(file_path), target, symbol_type)
        elif language == 'java':
            results = find_java_symbol(str(file_path), target, symbol_type)
        else:
            results = find_symbol_regex(str(file_path), target, symbol_type, 'generic')
        
        if not results:
            print(f"Symbol '{target}' not found in {file_path}")
            sys.exit(0)
        
        # Output results
        if args.json:
            import json
            print(json.dumps(results, indent=2))
        else:
            if len(results) > 1:
                print(f"{len(results)} definitions of '{target}':")
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result['type']} at line {result['line']}")
                    if 'signature' in result:
                        print(f"   {result['signature']}")
                print()
            
            # Show first result location
            first_result = results[0]
            if not args.quiet:
                if len(results) > 1:
                    print(f"First result: {first_result['type']} at line {first_result['line']}")
                else:
                    print(f"{first_result['type']} '{target}' at line {first_result['line']}:")
            
            show_location(str(file_path), first_result['line'], args.context, args.highlight)
    
    except KeyboardInterrupt:
        print("\\nNavigation interrupted", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()