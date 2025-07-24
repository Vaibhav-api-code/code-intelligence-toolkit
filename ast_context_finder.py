#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
AST Context Finder - Provides hierarchical context (class → method) for any line in a file.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import ast
import sys
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import argparse

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

# Try to import javalang for Java support
try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False

class ASTContextFinder:
    """Find hierarchical context for any line in a file using AST."""
    
    def __init__(self):
        self._cache = {}  # Cache parsed ASTs
    
    def get_context_for_line(self, filepath: str, line_number: int) -> Optional[List[Tuple[str, int, int, str]]]:
        """
        Get a list of hierarchical context parts for a specific line.
        
        Returns: List of (name, start, end, type) tuples or None
        """
        filepath = str(Path(filepath).resolve())
        
        # Determine language
        if filepath.endswith('.py'):
            return self._get_python_context(filepath, line_number)
        elif filepath.endswith('.java') and JAVALANG_AVAILABLE:
            return self._get_java_context(filepath, line_number)
        
        return None
    
    def _format_context_parts(self, context_parts: Optional[List[Tuple]]) -> Optional[str]:
        """Format a list of context parts into a string."""
        if not context_parts:
            return None
        return " → ".join([
            f"{name}({start}-{end})" 
            for name, start, end, _ in context_parts
        ])

    def _get_python_context(self, filepath: str, line_number: int) -> Optional[List[Tuple]]:
        """Get context for Python files using ast module."""
        try:
            # Use cache if available
            if filepath not in self._cache:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self._cache[filepath] = ast.parse(content)
            
            tree = self._cache[filepath]
            
            # Find all containing scopes
            context_parts = []
            
            for node in ast.walk(tree):
                if not (hasattr(node, 'lineno') and hasattr(node, 'end_lineno')):
                    continue
                
                # end_lineno can be None, default to lineno
                end_lineno = node.end_lineno or node.lineno
                if node.lineno <= line_number <= end_lineno:
                    if isinstance(node, ast.ClassDef):
                        context_parts.append((node.name, node.lineno, end_lineno, 'class'))
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        context_parts.append((node.name, node.lineno, end_lineno, 'function'))
            
            # Sort by line number to get proper nesting
            context_parts.sort(key=lambda x: x[1])
            return context_parts if context_parts else None
            
        except (SyntaxError, IOError) as e:
            print(f"Error parsing Python file '{filepath}': {e}", file=sys.stderr)
            return None
    
    def _get_java_context(self, filepath: str, line_number: int) -> Optional[List[Tuple]]:
        """Get context for Java files using javalang with regex fallback."""
        try:
            if filepath not in self._cache:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self._cache[filepath] = (content, javalang.parse.parse(content))
            
            source_text, tree = self._cache[filepath]
            
            context_parts = []
            
            for path, node in tree:
                if not hasattr(node, 'position') or not node.position:
                    continue
                
                node_start_line = node.position.line
                
                # Determine node type and name
                node_type, node_name = None, None
                if isinstance(node, javalang.tree.ClassDeclaration):
                    node_type, node_name = 'class', node.name
                elif isinstance(node, javalang.tree.MethodDeclaration):
                    node_type, node_name = 'method', node.name
                
                if not node_type:
                    continue

                # Find end line and check if it contains the target line
                node_end_line = self._find_java_node_end(source_text, node_start_line)
                if node_start_line <= line_number <= node_end_line:
                    context_parts.append((node_name, node_start_line, node_end_line, node_type))

            # Sort by start line to establish correct nesting
            context_parts.sort(key=lambda x: x[1])
            return context_parts if context_parts else None

        except Exception as e:
            # Catching javalang parsing errors - fall back to regex-based parsing
            print(f"javalang parsing failed for '{filepath}': {e}, falling back to regex parsing", file=sys.stderr)
            return self._get_java_context_regex_fallback(filepath, line_number)
    
    def _find_java_node_end(self, source_text: str, start_line: int) -> int:
        """
        Find the end line of a Java node by counting braces, ignoring those in
        comments and string literals.
        """
        try:
            lines = source_text.splitlines()
            
            brace_count = 0
            found_first_brace = False
            in_single_line_comment = False
            in_multiline_comment = False
            
            for i in range(start_line - 1, len(lines)):
                line = lines[i]
                in_string = False
                
                # Simple state machine for parsing
                j = 0
                while j < len(line):
                    if in_multiline_comment:
                        if line[j:j+2] == '*/':
                            in_multiline_comment = False
                            j += 1
                    elif in_string:
                        if line[j] == '\\': j += 1 # Skip escaped chars
                        elif line[j] == '"': in_string = False
                    elif line[j:j+2] == '//': break # Rest of line is a comment
                    elif line[j:j+2] == '/*': in_multiline_comment = True; j+= 1
                    elif line[j] == '"': in_string = True
                    elif line[j] == '{':
                        brace_count += 1
                        found_first_brace = True
                    elif line[j] == '}':
                        brace_count -= 1
                    j += 1
                
                if found_first_brace and brace_count == 0:
                    return i + 1
            
            return len(lines)  # Default to end of file
        except IndexError:
            return len(source_text.splitlines())
    
    def _get_java_context_regex_fallback(self, filepath: str, line_number: int) -> Optional[List[Tuple]]:
        """Regex-based fallback for Java context when javalang parsing fails."""
        import re
        
        try:
            if filepath not in self._cache:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Cache content without parsed tree for fallback
                self._cache[filepath] = (content, None)
            
            source_text, _ = self._cache[filepath]
            lines = source_text.splitlines()
            
            context_parts = []
            
            # Find class declarations using regex
            class_pattern = r'^\s*(?:public|private|protected)?\s*(?:static)?\s*class\s+(\w+)'
            method_pattern = r'^\s*(?:public|private|protected)?\s*(?:static)?\s*(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\s*\{'
            
            for i, line in enumerate(lines, 1):
                # Check for class declaration
                class_match = re.search(class_pattern, line)
                if class_match:
                    class_name = class_match.group(1)
                    end_line = self._find_java_node_end(source_text, i)
                    if i <= line_number <= end_line:
                        context_parts.append((class_name, i, end_line, 'class'))
                
                # Check for method declaration  
                method_match = re.search(method_pattern, line)
                if method_match:
                    method_name = method_match.group(1)
                    # Skip constructors that match class name
                    end_line = self._find_java_node_end(source_text, i)
                    if i <= line_number <= end_line:
                        context_parts.append((method_name, i, end_line, 'method'))
            
            # Sort by start line to establish correct nesting
            context_parts.sort(key=lambda x: x[1])
            return context_parts if context_parts else None
            
        except Exception as e:
            print(f"Regex fallback also failed for '{filepath}': {e}", file=sys.stderr)
            return None
    
    def get_detailed_context(self, filepath: str, line_number: int) -> Dict[str, any]:
        """
        Get detailed context information including type and nesting level.
        
        Returns dict with:
        - 'formatted': Formatted string like "Class → method"
        - 'parts': List of context parts with details
        - 'language': Detected language
        """
        filepath = str(Path(filepath).resolve())
        
        # Basic response structure
        result = {
            'formatted': None,
            'parts': [],
            'language': None
        }
        
        context_parts = self.get_context_for_line(filepath, line_number)
        
        if filepath.endswith('.py'): result['language'] = 'python'
        elif filepath.endswith('.java'): result['language'] = 'java'
        
        if context_parts:
            result['formatted'] = self._format_context_parts(context_parts)
            for i, (name, start, end, type) in enumerate(context_parts):
                result['parts'].append({
                    'name': name,
                    'type': type,
                    'start_line': start,
                    'end_line': end,
                    'level': i,
                })
        
        return result

def format_line_with_context(filepath: str, line_number: int, line_content: str, 
                           context_finder: Optional[ASTContextFinder] = None) -> str:
    """
    Format a line with its AST context.
    
    Example output:
    "    42: [ClassName(10-50) → methodName(30-45)]: line content here"
    """
    if context_finder is None:
        context_finder = ASTContextFinder()
    
    context_parts = context_finder.get_context_for_line(filepath, line_number)
    context = context_finder._format_context_parts(context_parts)

    if context:
        return f"{line_number:6d}: [{context}]: {line_content}"
    else:
        return f"{line_number:6d}: {line_content}"

def main():
    """Test the context finder with command line arguments."""
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Find AST context for a line in a file')
    else:
        parser = argparse.ArgumentParser(description='Find AST context for a line in a file')
    
    # Add tool-specific arguments
    # Note: --file is already added by the analyze parser when HAS_STANDARD_PARSER is True
    if not HAS_STANDARD_PARSER:
        parser.add_argument('--file', help='File to analyze')
    parser.add_argument('line_number', type=int, help='Line number to find context for')
    
    args = parser.parse_args()
    
    # Handle file path mapping for standard parser compatibility
    filepath = args.file
    if not filepath:
        print('Error: File path required (use --file)', file=sys.stderr)
        sys.exit(1)
    
    # Run preflight checks
    checks = [(PreflightChecker.check_file_readable, (filepath,))]
    run_preflight_checks(checks)
    
    line_number = args.line_number
    
    finder = ASTContextFinder()
    
    # Get simple context
    context_parts = finder.get_context_for_line(filepath, line_number)
    context = finder._format_context_parts(context_parts)
    if context_parts:
        print(f"Context at line {line_number}: {context}")
    else:
        print(f"No context found for line {line_number}")
    
    # Get detailed context
    detailed = finder.get_detailed_context(filepath, line_number)
    if detailed['parts']:
        print("\nDetailed context:")
        for part in detailed['parts']:
            indent = "  " * part['level']
            print(f"{indent}└─ {part['name']} (lines {part['start_line']}-{part['end_line']})")

if __name__ == "__main__":
    main()