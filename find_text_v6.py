#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
find_text v6 - Enhanced text search with structural code block extraction.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Union
import fnmatch
import re
import shutil
import ast

# Import AST context finder
try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

# Import Java parsing utilities
try:
    from java_parsing_utils import find_closing_brace, extract_method_body
    HAS_JAVA_UTILS = True
except ImportError:
    HAS_JAVA_UTILS = False

# Try to import javalang for better Java parsing
try:
    import javalang
    HAS_JAVALANG = True
except ImportError:
    HAS_JAVALANG = False

# Import standard argument parser
try:
    from enhanced_standard_arg_parser import create_search_parser
    from standard_arg_parser import create_standard_parser, parse_standard_args
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False
    
    def create_parser(tool_type, description):
        return argparse.ArgumentParser(description=description)
    
    def create_standard_parser(tool_type, description, epilog=None):
        parser = argparse.ArgumentParser(description=description, epilog=epilog, 
                                       formatter_class=argparse.RawDescriptionHelpFormatter)
        return parser
    
    def parse_standard_args(parser, tool_type):
        return parser.parse_args()

# Import AST configuration
try:
    from common_config import get_config, set_config
except ImportError:
    def get_config(key: str, default=None):
        """Simple config fallback that defaults to True for ast_context."""
        if key == 'ast_context':
            return True
        return default

# Import method extraction functionality
try:
    from extract_methods_v2 import extract_method
    HAS_EXTRACT_METHODS = True
except ImportError:
    HAS_EXTRACT_METHODS = False

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


class CodeBlockExtractor:
    """Extract complete code blocks containing search matches."""
    
    def __init__(self):
        self.ast_finder = ASTContextFinder() if HAS_AST_CONTEXT else None
    
    def extract_block(self, filepath: str, line_number: int) -> Optional[Dict]:
        """
        Extract the complete code block containing the given line.
        
        Returns dict with:
        - 'start_line': First line of the block
        - 'end_line': Last line of the block
        - 'content': The complete block content
        - 'block_type': Type of block (if/for/while/try/method/etc)
        """
        filepath = str(Path(filepath).resolve())
        
        if filepath.endswith('.py'):
            return self._extract_python_block(filepath, line_number)
        elif filepath.endswith('.java'):
            return self._extract_java_block(filepath, line_number)
        else:
            # For other languages, try generic brace matching
            return self._extract_generic_block(filepath, line_number)
    
    def _extract_python_block(self, filepath: str, line_number: int) -> Optional[Dict]:
        """Extract Python block using AST."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.splitlines()
            
            # Find the smallest node containing the line
            best_node = None
            best_size = float('inf')
            
            for node in ast.walk(tree):
                if not (hasattr(node, 'lineno') and hasattr(node, 'end_lineno')):
                    continue
                
                end_lineno = node.end_lineno or node.lineno
                
                # Check if this node contains our line
                if node.lineno <= line_number <= end_lineno:
                    # Prefer structural nodes over generic ones
                    if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With,
                                       ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        size = end_lineno - node.lineno
                        if size < best_size:
                            best_node = node
                            best_size = size
            
            if best_node:
                # Get the source segment for this node
                block_type = type(best_node).__name__.lower()
                start_line = best_node.lineno
                end_line = best_node.end_lineno or best_node.lineno
                
                # Extract the content
                content_lines = lines[start_line-1:end_line]
                content = '\n'.join(content_lines)
                
                return {
                    'start_line': start_line,
                    'end_line': end_line,
                    'content': content,
                    'block_type': block_type
                }
            
            # If no structural block found, try to find multi-line statement
            return self._find_multiline_statement(lines, line_number)
            
        except Exception as e:
            print(f"Error extracting Python block: {e}", file=sys.stderr)
            return None
    
    def _extract_java_block(self, filepath: str, line_number: int) -> Optional[Dict]:
        """Extract Java block using brace matching or javalang."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.splitlines()
            
            # First try javalang if available
            if HAS_JAVALANG:
                result = self._extract_java_block_with_javalang(content, lines, line_number)
                if result:
                    return result
            
            # Fallback to pattern matching
            return self._extract_java_block_with_patterns(content, lines, line_number)
            
        except Exception as e:
            print(f"Error extracting Java block: {e}", file=sys.stderr)
            return None
    
    def _extract_java_block_with_javalang(self, content: str, lines: List[str], 
                                         line_number: int) -> Optional[Dict]:
        """Use javalang to find containing block."""
        if not HAS_JAVALANG:
            return None
        
        try:
            tree = javalang.parse.parse(content)
            
            # Find nodes that might contain blocks
            candidates = []
            
            for path, node in tree:
                if not hasattr(node, 'position') or not node.position:
                    continue
                
                start_line = node.position.line
                
                # Check various block types
                if isinstance(node, (javalang.tree.IfStatement, javalang.tree.ForStatement,
                                   javalang.tree.WhileStatement, javalang.tree.TryStatement,
                                   javalang.tree.MethodDeclaration, javalang.tree.ClassDeclaration)):
                    # Try to find the end of this block
                    end_line = self._find_java_block_end(content, start_line)
                    
                    if start_line <= line_number <= end_line:
                        candidates.append({
                            'node': node,
                            'start_line': start_line,
                            'end_line': end_line,
                            'size': end_line - start_line
                        })
            
            # Choose the smallest containing block
            if candidates:
                best = min(candidates, key=lambda x: x['size'])
                
                block_type = type(best['node']).__name__.replace('Statement', '').lower()
                content_lines = lines[best['start_line']-1:best['end_line']]
                
                return {
                    'start_line': best['start_line'],
                    'end_line': best['end_line'],
                    'content': '\n'.join(content_lines),
                    'block_type': block_type
                }
            
        except Exception:
            pass
        
        return None
    
    def _extract_java_block_with_patterns(self, content: str, lines: List[str], 
                                         line_number: int) -> Optional[Dict]:
        """Use pattern matching to find Java blocks."""
        if not HAS_JAVA_UTILS:
            return None
        
        # Patterns for different block types
        block_patterns = [
            (r'\b(if|else\s+if)\s*\(', 'if'),
            (r'\b(for|while)\s*\(', 'loop'),
            (r'\btry\s*\{', 'try'),
            (r'\bcatch\s*\(', 'catch'),
            (r'\bswitch\s*\(', 'switch'),
            (r'(public|private|protected|static|final)*\s*\w+\s+\w+\s*\([^)]*\)\s*\{', 'method'),
        ]
        
        # Search backwards from the target line to find block start
        for i in range(line_number - 1, -1, -1):
            line_content = lines[i]
            
            for pattern, block_type in block_patterns:
                match = re.search(pattern, line_content)
                if match:
                    # Find the opening brace
                    full_content = '\n'.join(lines)
                    line_start_pos = sum(len(lines[j]) + 1 for j in range(i))
                    brace_pos = full_content.find('{', line_start_pos)
                    
                    if brace_pos != -1:
                        # Find closing brace
                        close_pos = find_closing_brace(full_content, brace_pos)
                        if close_pos != -1:
                            # Convert positions back to line numbers
                            end_line = full_content[:close_pos].count('\n') + 1
                            
                            if i + 1 <= line_number <= end_line:
                                content_lines = lines[i:end_line]
                                return {
                                    'start_line': i + 1,
                                    'end_line': end_line,
                                    'content': '\n'.join(content_lines),
                                    'block_type': block_type
                                }
        
        # Try to find multi-line method calls
        return self._find_multiline_statement(lines, line_number)
    
    def _find_java_block_end(self, content: str, start_line: int) -> int:
        """Find the end line of a Java block."""
        lines = content.splitlines()
        
        # Find the first opening brace after start_line
        brace_count = 0
        found_first_brace = False
        
        for i in range(start_line - 1, len(lines)):
            line = lines[i]
            
            for char in line:
                if char == '{':
                    brace_count += 1
                    found_first_brace = True
                elif char == '}':
                    brace_count -= 1
                
                if found_first_brace and brace_count == 0:
                    return i + 1
        
        return len(lines)
    
    def _extract_generic_block(self, filepath: str, line_number: int) -> Optional[Dict]:
        """Extract block for languages without specific support."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Look for common block patterns
            block_patterns = [
                (r'\b(if|else\s+if)\s*\(', 'if'),
                (r'\b(for|while)\s*\(', 'loop'),
                (r'\bfunction\s+\w+\s*\(', 'function'),
                (r'\bdef\s+\w+\s*\(', 'function'),
            ]
            
            # Search backwards for block start
            for i in range(line_number - 1, -1, -1):
                line = lines[i].rstrip()
                
                for pattern, block_type in block_patterns:
                    if re.search(pattern, line):
                        # Try to find block end using indentation or braces
                        end_line = self._find_block_end_generic(lines, i)
                        
                        if i < line_number <= end_line:
                            content = ''.join(lines[i:end_line])
                            return {
                                'start_line': i + 1,
                                'end_line': end_line,
                                'content': content.rstrip(),
                                'block_type': block_type
                            }
            
        except Exception as e:
            print(f"Error extracting generic block: {e}", file=sys.stderr)
        
        return None
    
    def _find_block_end_generic(self, lines: List[str], start_idx: int) -> int:
        """Find block end using indentation or braces."""
        if '{' in lines[start_idx]:
            # Use brace matching
            brace_count = 0
            for i in range(start_idx, len(lines)):
                brace_count += lines[i].count('{') - lines[i].count('}')
                if brace_count == 0 and i > start_idx:
                    return i + 1
        else:
            # Use indentation
            start_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
            for i in range(start_idx + 1, len(lines)):
                line = lines[i]
                if line.strip():  # Non-empty line
                    indent = len(line) - len(line.lstrip())
                    if indent <= start_indent:
                        return i
        
        return len(lines)
    
    def _find_multiline_statement(self, lines: List[str], line_number: int) -> Optional[Dict]:
        """Find multi-line statements (method calls, conditions, etc.)."""
        # Common patterns for statement continuation
        continuation_chars = ['(', '[', '{', ',', '\\', '&&', '||', '+', '-', '*', '/', '=']
        
        # Find the start of the statement
        start_line = line_number
        for i in range(line_number - 1, max(0, line_number - 20), -1):
            line = lines[i-1].rstrip() if i > 0 else ""
            
            # Check if previous line continues into this one
            continues = any(line.endswith(char) for char in continuation_chars)
            if not continues and i < line_number - 1:
                # Also check for unclosed parentheses
                open_count = lines[i-1].count('(') - lines[i-1].count(')')
                if open_count <= 0:
                    break
            
            start_line = i
        
        # Find the end of the statement
        end_line = line_number
        paren_count = 0
        bracket_count = 0
        brace_count = 0
        
        for i in range(start_line - 1, min(len(lines), start_line + 50)):
            line = lines[i]
            paren_count += line.count('(') - line.count(')')
            bracket_count += line.count('[') - line.count(']')
            brace_count += line.count('{') - line.count('}')
            
            # Check if statement is complete
            if (paren_count <= 0 and bracket_count <= 0 and brace_count <= 0 and 
                not any(line.rstrip().endswith(char) for char in continuation_chars)):
                end_line = i + 1
                if i >= line_number - 1:
                    break
        
        if end_line > start_line:
            content = '\n'.join(lines[start_line-1:end_line])
            return {
                'start_line': start_line,
                'end_line': end_line,
                'content': content,
                'block_type': 'statement'
            }
        
        return None


class LineRange:
    """Helper class to manage line ranges with merging."""
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end
    
    def overlaps_or_adjacent(self, other: 'LineRange') -> bool:
        """Check if this range overlaps or is adjacent to another."""
        return not (self.end < other.start - 1 or other.end < self.start - 1)
    
    def merge(self, other: 'LineRange') -> 'LineRange':
        """Merge this range with another, returning a new range."""
        return LineRange(min(self.start, other.start), max(self.end, other.end))
    
    def __repr__(self):
        return f"LineRange({self.start}, {self.end})"


def parse_pattern_with_context(pattern: str) -> Tuple[str, int]:
    """Parse pattern with optional ± context syntax."""
    # Check for ± syntax at the end
    match = re.match(r'^(.+?)\s*±\s*(\d+)$', pattern)
    if match:
        return match.group(1), int(match.group(2))
    
    # Check for +/- syntax
    match = re.match(r'^(.+?)\s*\+/-\s*(\d+)$', pattern)
    if match:
        return match.group(1), int(match.group(2))
    
    return pattern, 0


def get_ripgrep_path():
    """Get the path to ripgrep executable."""
    rg_path = shutil.which('rg')
    if not rg_path:
        print("Error: ripgrep (rg) is not installed. Please install it first.")
        print("  macOS: brew install ripgrep")
        print("  Ubuntu/Debian: apt-get install ripgrep")
        print("  Other: https://github.com/BurntSushi/ripgrep#installation")
        sys.exit(1)
    return rg_path


def search_with_context(pattern: str, args, context_lines: int = 0, extract_block: bool = False) -> List[Dict]:
    """Search for pattern and get full context using non-JSON mode."""
    rg_path = get_ripgrep_path()
    
    # Build ripgrep command – deterministic & parser-friendly
    cmd = [
        rg_path,
        "--line-number",
        "--with-filename", 
        "--color=never",
    ]
    
    # Add pattern type flags
    if args.type in ['fixed', 'text']:
        cmd.append('-F')
    elif args.type == 'word':
        cmd.append('-w')
    # regex is default, no flag needed
    
    # Case sensitivity
    if args.ignore_case:
        cmd.append('-i')
    else:
        cmd.append('-s')
    
    # Context lines
    if context_lines > 0:
        cmd.extend(['-C', str(context_lines)])
    
    # File filtering
    if hasattr(args, 'glob') and args.glob:
        # Handle both single string and list of strings
        if isinstance(args.glob, str):
            cmd.extend(['-g', args.glob])
        elif isinstance(args.glob, list):
            for g in args.glob:
                cmd.extend(['-g', g])
        else:
            # If it's something else, try to iterate (handles the case where it might be iterable)
            try:
                for g in args.glob:
                    cmd.extend(['-g', g])
            except TypeError:
                # If not iterable, convert to string
                cmd.extend(['-g', str(args.glob)])
    
    # Pattern and paths
    cmd.extend(["-e", pattern])
    cmd.append("--")            # end of options – next are files/paths
    
    # Add file or scope
    if hasattr(args, 'file') and args.file:
        if isinstance(args.file, list):
            cmd.extend(args.file)
        else:
            cmd.append(args.file)
    elif hasattr(args, 'scope') and args.scope:
        cmd.append(args.scope)
    else:
        cmd.append('.')
    
    try:
        if args.verbose:
            print(f"DEBUG: Running ripgrep command: {' '.join(cmd)}", file=sys.stderr)
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        
        if result.returncode not in [0, 1]:  # 0 = found matches, 1 = no matches
            print(f"Error running ripgrep: {result.stderr}", file=sys.stderr)
            return []
        
        if not result.stdout:
            return []
        
        # Parse the output
        matches = []
        current_file = None
        current_match = None
        context_before = []
        context_after_remaining = 0
        
        # If searching a specific file, set it as current
        if hasattr(args, 'file') and args.file and isinstance(args.file, str):
            current_file = args.file
        
        lines = result.stdout.splitlines()
        
        for line in lines:
            # Try single file format first: line:content or line-content
            single_file_match = re.match(r'^(\d+)([:|-])(.*)$', line)
            if single_file_match:
                line_num = int(single_file_match.group(1))
                separator = single_file_match.group(2)
                content = single_file_match.group(3)
                file_path = current_file or "unknown"
            else:
                # Try multi-file format: path:line:content or path:line-content
                # Accept drive letters or other colons in the path
                multi_file_match = re.match(r'^(.*):(\d+)([:|-])(.*)$', line)
                if multi_file_match:
                    file_path = multi_file_match.group(1)
                    line_num = int(multi_file_match.group(2))
                    separator = multi_file_match.group(3)
                    content = multi_file_match.group(4)
                    current_file = file_path  # Update current file
                else:
                    # Line doesn't match expected format - skip it
                    continue
            
            if separator == ':':
                # This is an actual match
                # Save any pending match with its context
                if current_match and context_after_remaining == 0:
                    matches.append(current_match)
                    context_before = []
                
                # Create new match
                current_match = {
                    'file': file_path,
                    'line': line_num,
                    'content': content,
                    'match': pattern,
                    'context_before': list(context_before),  # Copy the before context
                    'context_after': []
                }
                
                # If extract_block is requested, get the complete block
                if extract_block:
                    extractor = CodeBlockExtractor()
                    block_info = extractor.extract_block(file_path, line_num)
                    if block_info:
                        current_match['block'] = block_info
                
                # Reset context tracking
                context_after_remaining = context_lines
                
            elif separator == '-':
                # This is a context line
                if current_match and context_after_remaining > 0:
                    # This is after context for current match
                    current_match['context_after'].append({
                        'line': line_num,
                        'content': content
                    })
                    context_after_remaining -= 1
                    
                    # If we've collected all after context, save the match
                    if context_after_remaining == 0:
                        matches.append(current_match)
                        current_match = None
                        context_before = []
                else:
                    # This is before context for next match
                    context_before.append({
                        'line': line_num,
                        'content': content
                    })
                    # Keep only the last N context lines
                    if len(context_before) > context_lines:
                        context_before.pop(0)
        
        # Don't forget the last match
        if current_match:
            matches.append(current_match)
        
        
        return matches
        
    except Exception as e:
        print(f"Error during search: {e}", file=sys.stderr)
        return []


def format_line_content(content: str, line_num: int, pattern: str = None, 
                       highlight: bool = True) -> str:
    """Format a line with line number and optional highlighting."""
    # Format line number
    formatted = f"{line_num:6d}: {content}"
    
    # Highlight pattern if requested
    if highlight and pattern:
        # Simple highlighting with terminal colors
        formatted = formatted.replace(pattern, f"\033[91m{pattern}\033[0m")
    
    return formatted


def extract_method_from_context(file_path: str, ast_context: str, max_lines: Optional[int] = None) -> Optional[Dict]:
    """Extract method from file based on AST context."""
    if not HAS_EXTRACT_METHODS:
        return None
    
    # Parse the AST context to get method name
    # Context format: "ClassName(start-end) → methodName(start-end)"
    method_match = re.search(r'→\s*(\w+)\s*\(', ast_context)
    if not method_match:
        # Try simpler format
        method_match = re.search(r'(\w+)\s*\(', ast_context)
    
    if not method_match:
        return None
    
    method_name = method_match.group(1)
    
    try:
        # Extract the method
        results = extract_method(file_path, method_name, include_javadoc=True)
        
        if isinstance(results, dict) and 'error' in results:
            return None
        
        if not results:
            return None
        
        # Get the first matching method
        method_info = results[0]
        
        # Check line count if max_lines specified
        if max_lines and method_info['line_count'] > max_lines:
            return {
                'skipped': True,
                'reason': f"Method '{method_name}' has {method_info['line_count']} lines (exceeds {max_lines} line limit)",
                'line_count': method_info['line_count']
            }
        
        return method_info
        
    except Exception as e:
        print(f"Error extracting method: {e}", file=sys.stderr)
        return None


def extract_method_from_match_fallback(file_path: str, match_line: str, line_number: int, max_lines: Optional[int] = None) -> Optional[Dict]:
    """Fallback method extraction when AST context is not available."""
    if not HAS_EXTRACT_METHODS:
        return None
    
    # Try to extract method name from the matched line using regex
    # Match patterns like: "public void methodName(" or "private String methodName("
    method_patterns = [
        r'(?:public|private|protected)\s+(?:static\s+)?(?:\w+\s+)*(\w+)\s*\(',  # Standard method
        r'(\w+)\s*\([^)]*\)\s*\{',  # Simple method with opening brace
        r'(?:public|private|protected).*?(\w+)\s*\(',  # Flexible method pattern
    ]
    
    method_name = None
    for pattern in method_patterns:
        match = re.search(pattern, match_line)
        if match:
            potential_name = match.group(1)
            # Skip common keywords and types
            if potential_name not in ['void', 'String', 'int', 'double', 'boolean', 'if', 'for', 'while', 'return']:
                method_name = potential_name
                break
    
    if not method_name:
        return None
    
    try:
        # Extract the method using the detected method name
        results = extract_method(file_path, method_name, include_javadoc=True)
        
        if isinstance(results, dict) and 'error' in results:
            return None
        
        if not results:
            return None
        
        # Find the method that contains our line number
        for method_info in results:
            if method_info['start_line'] <= line_number <= method_info['end_line']:
                # Check line count if max_lines specified
                if max_lines and method_info['line_count'] > max_lines:
                    return {
                        'skipped': True,
                        'reason': f"Method '{method_name}' has {method_info['line_count']} lines (exceeds {max_lines} line limit)",
                        'line_count': method_info['line_count']
                    }
                
                return method_info
        
        # If no method contains the line, return the first one
        method_info = results[0]
        if max_lines and method_info['line_count'] > max_lines:
            return {
                'skipped': True,
                'reason': f"Method '{method_name}' has {method_info['line_count']} lines (exceeds {max_lines} line limit)",
                'line_count': method_info['line_count']
            }
        
        return method_info
        
    except Exception as e:
        print(f"Error in fallback method extraction: {e}", file=sys.stderr)
        return None


def display_matches(matches: List[Dict], args):
    """Display search matches with proper formatting."""
    if not matches:
        print("No matches found.")
        return
    
    # Determine if colors should be used
    use_colors = (sys.stdout.isatty() and not (hasattr(args, 'no_color') and args.no_color))
    
    # If wholefile mode, show entire files containing matches
    if hasattr(args, 'wholefile') and args.wholefile:
        displayed_files = set()
        for match in matches:
            if match['file'] not in displayed_files:
                displayed_files.add(match['file'])
                try:
                    with open(match['file'], 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"=== {match['file']} (entire file) ===")
                    print(content)
                    if not content.endswith('\n'):
                        print()  # Add newline if file doesn't end with one
                    print("=" * 80)
                except Exception as e:
                    print(f"Error reading file {match['file']}: {e}", file=sys.stderr)
        return
    
    # If extract_block mode, show blocks instead of individual lines
    if args.extract_block:
        current_file = None
        for match in matches:
            if match['file'] != current_file:
                if current_file:
                    print()  # Blank line between files
                print(f"=== {match['file']} ===")
                current_file = match['file']
            
            if 'block' in match:
                block = match['block']
                print(f"\n[Match at line {match['line']} in {block['block_type']} block]")
                print(f"Lines {block['start_line']}-{block['end_line']}:")
                print("-" * 80)
                
                # Show the block with line numbers
                lines = block['content'].splitlines()
                for i, line in enumerate(lines, block['start_line']):
                    # Highlight the matching line
                    if i == match['line']:
                        if use_colors:
                            print(f"\033[92m{i:6d}: {line}\033[0m")  # Green for match line
                        else:
                            print(f"{i:6d}: {line}")
                    else:
                        print(f"{i:6d}: {line}")
                
                print("-" * 80)
            else:
                # Fallback to regular display
                print(f"\n{match['line']:6d}: {match['content']}")
    else:
        # Regular display mode with optional AST context
        current_file = None
        ast_finder = ASTContextFinder() if HAS_AST_CONTEXT and args.ast_context else None
        
        for match in matches:
            if match['file'] != current_file:
                if current_file:
                    print()  # Blank line between files
                print(f"=== {match['file']} ===")
                current_file = match['file']
            
            # Show before context
            if 'context_before' in match:
                for ctx in match['context_before']:
                    print(f"{ctx['line']:6d}- {ctx['content']}")
            
            # Show the match line (highlighted)
            print(f"{match['line']:6d}: {match['content']}")
            
            # Add AST context if enabled
            ast_context = None
            if ast_finder and not args.extract_block:
                context = ast_finder.get_context_for_line(match['file'], match['line'])
                if context:
                    formatted = ast_finder._format_context_parts(context)
                    ast_context = formatted
                    print(f"         AST context: [{formatted}]")
            
            # Extract method if requested
            should_extract = ((hasattr(args, 'extract_method') and args.extract_method) or 
                            (hasattr(args, 'extract_method_alllines') and args.extract_method_alllines))
            if should_extract and HAS_EXTRACT_METHODS:
                # Determine max lines
                max_lines = None if (hasattr(args, 'extract_method_alllines') and args.extract_method_alllines) else 1000
                
                method_info = None
                
                # First try: Extract using AST context (preferred method)
                if ast_context:
                    method_info = extract_method_from_context(match['file'], ast_context, max_lines)
                
                # Second try: Fallback method if AST context failed or unavailable
                if not method_info:
                    method_info = extract_method_from_match_fallback(match['file'], match['content'], match['line'], max_lines)
                
                if method_info:
                    if method_info.get('skipped'):
                        print(f"\n    [Method extraction skipped: {method_info['reason']}]")
                        if hasattr(args, 'verbose') and args.verbose:
                            print(f"    [Use --extract-method-alllines to extract methods over 1000 lines]")
                    else:
                        extraction_method = "AST context" if ast_context else "regex fallback"
                        print(f"\n    ╔══ Extracted Method: {method_info['signature']} ══╗")
                        print(f"    ║ Lines {method_info['start_line']}-{method_info['end_line']} ({method_info['line_count']} lines) [{extraction_method}]")
                        print("    ╚" + "═" * (len(method_info['signature']) + 35) + "╝")
                        print()
                        
                        # Print method content with indentation
                        for line in method_info['content'].split('\n'):
                            print(f"    {line}")
                        print()
            
            # Show after context
            if 'context_after' in match:
                for ctx in match['context_after']:
                    print(f"{ctx['line']:6d}- {ctx['content']}")


def merge_ranges(ranges: List[LineRange]) -> List[LineRange]:
    """Merge overlapping or adjacent line ranges."""
    if not ranges:
        return []
    
    # Sort by start line
    sorted_ranges = sorted(ranges, key=lambda r: r.start)
    
    merged = [sorted_ranges[0]]
    for current in sorted_ranges[1:]:
        last = merged[-1]
        if last.overlaps_or_adjacent(current):
            merged[-1] = last.merge(current)
        else:
            merged.append(current)
    
    return merged


def extract_line_ranges(matches: List[Dict], context: int = 0) -> Dict[str, List[LineRange]]:
    """Extract line ranges from matches, grouped by file."""
    file_ranges = {}
    
    for match in matches:
        file_path = match['file']
        line_num = match['line']
        
        if file_path not in file_ranges:
            file_ranges[file_path] = []
        
        # Create range with context
        start = max(1, line_num - context)
        end = line_num + context  # Will be clamped when reading file
        
        file_ranges[file_path].append(LineRange(start, end))
    
    # Merge overlapping ranges for each file
    for file_path in file_ranges:
        file_ranges[file_path] = merge_ranges(file_ranges[file_path])
    
    return file_ranges


def read_line_ranges(file_path: str, ranges: List[LineRange]) -> List[str]:
    """Read specific line ranges from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        output_lines = []
        for range_obj in ranges:
            # Clamp to file bounds
            start = max(0, range_obj.start - 1)  # Convert to 0-based
            end = min(len(lines), range_obj.end)  # end is exclusive in slicing
            
            # Add the lines with line numbers
            for i in range(start, end):
                output_lines.append(f"{i+1:6d}: {lines[i].rstrip()}")
            
            # Add separator between ranges if needed
            if range_obj != ranges[-1]:
                output_lines.append("  ...")
        
        return output_lines
        
    except Exception as e:
        return [f"Error reading file: {e}"]


def find_file(filename: str) -> Optional[str]:
    """Try to find a file by name using find_files tool."""
    # Try to use find_files.py tool
    find_files_path = Path(__file__).parent / 'find_files.py'
    if find_files_path.exists():
        try:
            result = subprocess.run(
                ['python3', str(find_files_path), '--name', filename, '--type', 'f', '--limit', '10'],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                if lines:
                    # Filter to exact matches
                    exact_matches = [l for l in lines if Path(l).name == filename]
                    if len(exact_matches) == 1:
                        return exact_matches[0]
                    elif len(exact_matches) > 1:
                        print(f"Multiple files found for '{filename}':")
                        for match in exact_matches[:5]:
                            print(f"  {match}")
                        print("Please specify the full path.")
                        return None
        except Exception:
            pass
    
    # Fallback to simple search
    try:
        result = subprocess.run(
            ['find', '.', '-name', filename, '-type', 'f'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            if lines and lines[0]:
                if len(lines) == 1:
                    return lines[0]
                else:
                    print(f"Multiple files found for '{filename}':")
                    for line in lines[:5]:
                        print(f"  {line}")
                    print("Please specify the full path.")
                    return None
    except Exception:
        pass
    
    return None


def create_parser():
    """Create the argument parser."""
    if HAS_STANDARD_PARSER:
        # Use create_search_parser which has all the standard search options
        parser = create_search_parser(
            'Enhanced text search with multiline capabilities, auto file finding, and code block extraction',
            epilog="""Examples:
  # Basic search
  %(prog)s "TODO"
  
  # Search with context lines using ± syntax
  %(prog)s "processData" ±10
  
  # Search specific file (auto-finds if not full path)
  %(prog)s "calculateTotal" --file DataManager.java
  
  # Extract complete code blocks
  %(prog)s "error handling" --extract-block
  
  # Search and extract line ranges
  %(prog)s "TODO" --scope src/ -g "*.py" | %(prog)s --ranges -
  
  # Extract specific line ranges  
  %(prog)s --file config.py --lines 100-150
  
  # Multiple ranges
  %(prog)s --file utils.py --lines 50-60,100-120,200-210
"""
        )
    else:
        parser = argparse.ArgumentParser(
            description='Enhanced text search with multiline capabilities and auto file finding',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Add all the search options manually if standard parser not available
        parser.add_argument('pattern', nargs='?', help='Search pattern (supports ± context syntax)')
        
        # Search options
        parser.add_argument('-i', '--ignore-case', action='store_true',
                          help='Case insensitive search')
        parser.add_argument('-w', '--word', action='store_true',
                          help='Match whole words only')
        parser.add_argument('-F', '--fixed-strings', action='store_true',
                          help='Treat pattern as literal string')
        parser.add_argument('--type', choices=['fixed', 'regex', 'word'], default='regex',
                          help='Pattern type (default: regex)')
        
        # Context options
        parser.add_argument('-C', '--context', type=int, default=0,
                          help='Number of context lines (overrides ± in pattern)')
        parser.add_argument('-A', '--after-context', type=int,
                          help='Lines of context after match')
        parser.add_argument('-B', '--before-context', type=int,
                          help='Lines of context before match')
        
        # File/scope options
        parser.add_argument('--file', nargs='+',
                          help='File(s) to search (auto-finds if name only)')
        parser.add_argument('--scope', help='Directory scope for search')
        parser.add_argument('-g', '--glob', action='append',
                          help='Include files matching glob (can be repeated)')
        
        # Output options
        parser.add_argument('--json', action='store_true',
                          help='Output in JSON format')
        parser.add_argument('-q', '--quiet', action='store_true',
                          help='Suppress non-essential output')
        parser.add_argument('-v', '--verbose', action='store_true',
                          help='Verbose output')
    
    # Add new options that aren't in the standard parser
    
    # Override --file to accept multiple files if using enhanced parser
    if HAS_STANDARD_PARSER and '--file' in parser._option_string_actions:
        # Remove the existing --file argument
        file_action = parser._option_string_actions['--file']
        parser._remove_action(file_action)
        for option_string in file_action.option_strings:
            parser._option_string_actions.pop(option_string, None)
        
        # Re-add with nargs='+'
        parser.add_argument('--file', nargs='+',
                          help='File(s) to search (auto-finds if name only)')
    
    # Block extraction
    parser.add_argument('--extract-block', action='store_true',
                      help='Extract complete code blocks containing matches')
    
    # Method extraction (from v4)
    parser.add_argument('--extract-method', action='store_true',
                      help='Extract containing methods (up to 1000 lines)')
    parser.add_argument('--extract-method-alllines', action='store_true',
                      help='Extract containing methods regardless of size')
    
    # Range features (from v5)
    parser.add_argument('--extract-ranges', action='store_true',
                      help='Output line ranges suitable for multiline_reader')
    parser.add_argument('--merge-ranges', action='store_true',
                      help='Merge overlapping context ranges')
    
    # Output control (from v5)
    parser.add_argument('--no-color', action='store_true',
                      help='Disable color output')
    parser.add_argument('--auto-find', action='store_true',
                      help='Automatically find file if not found at given path (default behavior)')
    
    # Context arguments (from v5) - only add if not already present
    if not hasattr(parser, '_option_string_actions') or '-A' not in parser._option_string_actions:
        parser.add_argument('-A', '--after-context', type=int, metavar='N', 
                          help='Show N lines after match')
    if not hasattr(parser, '_option_string_actions') or '-B' not in parser._option_string_actions:
        parser.add_argument('-B', '--before-context', type=int, metavar='N', 
                          help='Show N lines before match')
    if not hasattr(parser, '_option_string_actions') or '-C' not in parser._option_string_actions:
        parser.add_argument('-C', '--context', type=int, metavar='N', 
                          help='Show N lines around match')
    if not hasattr(parser, '_option_string_actions') or '-i' not in parser._option_string_actions:
        parser.add_argument('-i', '--ignore-case', action='store_true', 
                          help='Case-insensitive search')
    if not hasattr(parser, '_option_string_actions') or '-v' not in parser._option_string_actions:
        parser.add_argument('-v', '--verbose', action='store_true', 
                          help='Verbose output')
    if not hasattr(parser, '_option_string_actions') or '-q' not in parser._option_string_actions:
        parser.add_argument('-q', '--quiet', action='store_true', 
                          help='Quiet mode')
    
    # Line extraction options
    parser.add_argument('--lines', help='Extract specific line ranges (e.g., 10-20,30-40)')
    parser.add_argument('--ranges', help='Read line ranges from file or stdin (-)')
    
    # Whole file extraction
    parser.add_argument('--wholefile', action='store_true',
                      help='Return entire file content when a match is found (NEW IN V6)')
    
    # AST context control (may already be in enhanced parser)
    if not hasattr(parser, '_option_string_actions') or '--ast-context' not in parser._option_string_actions:
        parser.add_argument('--ast-context', action='store_true', 
                          default=None,
                          help='Show AST context (class → method hierarchy) - enabled by default via config')
        parser.add_argument('--no-ast-context', action='store_true',
                          help='Disable AST context display')
    
    return parser


def resolve_file_paths(file_arg):
    """Resolve file paths with auto-finding capability."""
    if not file_arg:
        return None
    
    # Handle both single file (string) and multiple files (list)
    files_to_check = [file_arg] if isinstance(file_arg, str) else file_arg
    resolved_files = []
    
    for f in files_to_check:
        if Path(f).exists():
            resolved_files.append(str(Path(f).resolve()))  # Convert to absolute path
        else:
            # Try to find the file
            found = find_file(f)
            if found:
                resolved_files.append(str(Path(found).resolve()))  # Convert to absolute path
            else:
                print(f"Error: File not found: {f}", file=sys.stderr)
                sys.exit(1)
    
    return resolved_files[0] if len(resolved_files) == 1 else resolved_files


def run_preflight_checks(args):
    """Run preflight checks on parsed arguments."""
    # Check file existence
    if hasattr(args, 'file') and args.file:
        files_to_check = [args.file] if isinstance(args.file, str) else args.file
        for f in files_to_check:
            if not Path(f).exists():
                print(f"Error: File not found: {f}", file=sys.stderr)
                sys.exit(1)
    
    # Check directory existence
    if hasattr(args, 'scope') and args.scope:
        if not Path(args.scope).is_dir():
            print(f"Error: Directory not found: {args.scope}", file=sys.stderr)
            sys.exit(1)


def main():
    parser = create_parser()
    
    # Parse arguments normally (pattern is now optional with nargs='?')
    # Skip preflight checks from standard parser - we handle file resolution ourselves
    args = parser.parse_args()
    
    # Validate arguments after parsing
    if not args.pattern and not (hasattr(args, 'lines') and args.lines) and not (hasattr(args, 'ranges') and args.ranges) and not (hasattr(args, 'wholefile') and args.wholefile):
        parser.error("Pattern required unless using --lines, --ranges, or --wholefile")
    
    # Resolve file paths after parsing (handle both attribute names)
    file_arg = getattr(args, 'file', None) or getattr(args, 'file_input', None)
    if file_arg:
        resolved_files = resolve_file_paths(file_arg)
        # Set both attributes for compatibility
        args.file = resolved_files
        if hasattr(args, 'file_input'):
            args.file_input = resolved_files
    
    # Run preflight checks on resolved paths
    run_preflight_checks(args)
    
    
    # Handle AST context configuration
    if args.no_ast_context:
        args.ast_context = False
    elif args.ast_context is None:
        # Not explicitly set, use config default
        args.ast_context = get_config('ast_context', True)
    # else args.ast_context is True (explicitly enabled)
    
    # Handle --lines option for direct line extraction
    if hasattr(args, 'lines') and args.lines and not args.pattern:
        if not args.file:
            print("Error: --lines requires --file", file=sys.stderr)
            sys.exit(1)
        
        # Parse line ranges
        ranges = []
        for range_str in args.lines.split(','):
            if '-' in range_str:
                start, end = range_str.split('-', 1)
                ranges.append(LineRange(int(start), int(end)))
            else:
                line_num = int(range_str)
                ranges.append(LineRange(line_num, line_num))
        
        # Get the resolved file path (already validated and found)
        file_path = args.file[0] if isinstance(args.file, list) else args.file
        
        lines = read_line_ranges(file_path, ranges)
        print(f"=== {file_path} ===")
        for line in lines:
            print(line)
        return
    
    # Handle --ranges option for reading ranges from file
    if args.ranges:
        # Implementation for reading ranges from file
        print("--ranges option not yet implemented", file=sys.stderr)
        sys.exit(1)
    
    # Handle --wholefile without pattern
    if hasattr(args, 'wholefile') and args.wholefile and not args.pattern:
        if not args.file:
            print("Error: --wholefile requires --file when used without a search pattern", file=sys.stderr)
            sys.exit(1)
        
        # Display whole files without searching
        files = args.file if isinstance(args.file, list) else [args.file]
        
        if args.json:
            # JSON output for wholefile without pattern
            file_data = []
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    file_entry = {
                        'file': os.path.abspath(file_path),
                        'wholefile_content': content,
                        'wholefile_lines': content.splitlines(),
                        'total_lines': len(content.splitlines())
                    }
                    file_data.append(file_entry)
                except Exception as e:
                    file_entry = {
                        'file': os.path.abspath(file_path),
                        'wholefile_error': str(e)
                    }
                    file_data.append(file_entry)
            print(json.dumps(file_data, indent=2))
        else:
            # Regular output for wholefile without pattern
            for i, file_path in enumerate(files):
                if i > 0:
                    print()  # Blank line between files
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"=== {file_path} (entire file) ===")
                    print(content)
                    if not content.endswith('\n'):
                        print()  # Add newline if file doesn't end with one
                    print("=" * 80)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        sys.exit(0)
    
    # Regular search mode - require pattern unless using special modes
    if not args.pattern and not (hasattr(args, 'lines') and args.lines) and not (hasattr(args, 'ranges') and args.ranges):
        parser.print_help()
        sys.exit(1)
    
    # Parse pattern for ± context
    if args.pattern:
        pattern, pattern_context = parse_pattern_with_context(args.pattern)
    else:
        pattern, pattern_context = None, 0
    
    # Determine final context lines
    if hasattr(args, 'context') and args.context and args.context > 0:
        context_lines = args.context
    elif hasattr(args, 'after_context') and hasattr(args, 'before_context') and (args.after_context or args.before_context):
        # Use max of before/after
        context_lines = max(args.after_context or 0, args.before_context or 0)
    elif pattern_context > 0:
        context_lines = pattern_context
    else:
        context_lines = 0
    
    
    # Additional validation (regex pattern check)
    if hasattr(args, 'type') and args.type == 'regex' and pattern:
        try:
            re.compile(pattern)
        except re.error as e:
            print(f"Error: Invalid regex pattern: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Perform search
    matches = search_with_context(pattern, args, context_lines, args.extract_block)
    
    # Handle extract-ranges option
    if hasattr(args, 'extract_ranges') and args.extract_ranges:
        # Group by file and extract line ranges
        file_ranges = {}
        for match in matches:
            if match.get('is_match', True):  # Only process actual matches, not context
                file = match['file']
                if file not in file_ranges:
                    file_ranges[file] = []
                file_ranges[file].append(match['line'])
        
        # Output in multiline_reader format
        for file, lines in file_ranges.items():
            if hasattr(args, 'merge_ranges') and args.merge_ranges:
                # Create ranges with context and merge overlapping ones
                ranges = []
                for line in lines:
                    start = max(1, line - context_lines)
                    end = line + context_lines
                    ranges.append((start, end))
                
                # Sort and merge overlapping ranges
                if ranges:
                    sorted_ranges = sorted(ranges, key=lambda r: r[0])
                    merged = [sorted_ranges[0]]
                    
                    for current in sorted_ranges[1:]:
                        last = merged[-1]
                        # Check if ranges overlap or are adjacent
                        if current[0] <= last[1] + 1:
                            # Merge ranges
                            merged[-1] = (last[0], max(last[1], current[1]))
                        else:
                            # Add new range
                            merged.append(current)
                    
                    for start, end in merged:
                        if start == end:
                            print(f"{file}:{start}")
                        else:
                            print(f"{file}:{start}-{end}")
            else:
                # Output individual lines with context notation
                for line in lines:
                    if context_lines > 0:
                        print(f"{file}:{line}±{context_lines}")
                    else:
                        print(f"{file}:{line}")
        return
    
    # Output results
    if args.json:
        if hasattr(args, 'wholefile') and args.wholefile:
            # For wholefile mode, enhance matches with full file content
            enhanced_matches = []
            processed_files = set()
            
            for match in matches:
                if match['file'] not in processed_files:
                    processed_files.add(match['file'])
                    try:
                        with open(match['file'], 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        
                        # Create an enhanced match entry with full file content
                        enhanced_match = match.copy()
                        enhanced_match['wholefile_content'] = file_content
                        enhanced_match['wholefile_lines'] = file_content.splitlines()
                        enhanced_match['total_lines'] = len(enhanced_match['wholefile_lines'])
                        enhanced_matches.append(enhanced_match)
                    except Exception as e:
                        # If file can't be read, just include the regular match
                        match['wholefile_error'] = str(e)
                        enhanced_matches.append(match)
                else:
                    # For subsequent matches in the same file, just add regular match info
                    enhanced_matches.append(match)
            
            print(json.dumps(enhanced_matches, indent=2))
        else:
            print(json.dumps(matches, indent=2))
    else:
        display_matches(matches, args)
    
    # Exit with appropriate code and helpful hints for no matches
    if not matches:
        # Check if pattern contains regex special characters and suggest --type regex
        if pattern and args.type != 'regex':
            regex_chars = ['|', '*', '+', '?', '^', '$', '[', ']', '(', ')', '{', '}', '\\']
            if any(char in pattern for char in regex_chars):
                print(f"\nHint: Pattern '{pattern}' contains special characters ({', '.join(char for char in regex_chars if char in pattern)}).", file=sys.stderr)
                print("      Try adding --type regex to interpret it as a regular expression.", file=sys.stderr)
                print(f"      Example: {sys.argv[0]} '{pattern}' --type regex", file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()