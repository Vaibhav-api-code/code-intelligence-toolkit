#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced cross-file dependency analysis with AST-based caller identification.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import subprocess
import json
import re
import sys
import argparse
from pathlib import Path
import shutil
import os
from collections import Counter, defaultdict
from typing import List, Dict, Optional, Tuple, Set
import ast

# Try to import javalang for Java AST support

# Import standard argument parser
try:
    from enhanced_standard_arg_parser import create_analyze_parser
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False
    create_analyze_parser = None

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
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False

# Import common utilities if available
try:
    from common_utils import check_ripgrep, detect_language, add_common_args
except ImportError:
    # Fallback if common_utils not available
    def check_ripgrep():
        if not shutil.which('rg'):
            print("Error: ripgrep (rg) is not installed or not in your PATH.", file=sys.stderr)
            print("Please install it from: https://github.com/BurntSushi/ripgrep#installation", file=sys.stderr)
            sys.exit(1)

# Import AST context finder
try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

class CallerIdentifier:
    """Identifies the enclosing function/method for a given line using AST."""
    
    @staticmethod
    def find_enclosing_function_python(filepath: str, line_number: int) -> Optional[str]:
        """
        Find the enclosing function for a line in Python code.
        
        Args:
            filepath: Path to the Python file
            line_number: Line number (1-indexed)
            
        Returns:
            Function name or None
        """
        try:
            # Check file size before reading (prevent memory issues)
            file_path_obj = Path(filepath)
            if file_path_obj.stat().st_size > 5 * 1024 * 1024:  # 5MB limit
                print(f"Warning: File '{filepath}' is very large ({file_path_obj.stat().st_size // (1024*1024)}MB), skipping AST parsing", file=sys.stderr)
                return CallerIdentifier.find_enclosing_function_regex(filepath, line_number)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Basic sanity check on file content
            if len(code.strip()) == 0:
                return None
                
            tree = ast.parse(code)
            
            class FunctionFinder(ast.NodeVisitor):
                def __init__(self, target_line):
                    self.target_line = target_line
                    self.best_match = None
                    self.best_span = float('inf')
                
                def visit_FunctionDef(self, node):
                    # Check if our target line is within this function
                    if hasattr(node, 'lineno'):
                        start_line = node.lineno
                        end_line = getattr(node, 'end_lineno', None)
                        
                        # If end_lineno not available, estimate from the AST
                        if end_line is None:
                            # Find the last line by looking at all child nodes
                            end_line = start_line
                            for child in ast.walk(node):
                                if hasattr(child, 'lineno') and child.lineno > end_line:
                                    end_line = child.lineno
                        
                        # Check if target line is within this function
                        if start_line <= self.target_line <= end_line:
                            span = end_line - start_line
                            # Prefer the innermost (smallest span) function
                            if span < self.best_span:
                                self.best_span = span
                                self.best_match = node.name
                    
                    # Continue visiting children for nested functions
                    self.generic_visit(node)
                
                def visit_AsyncFunctionDef(self, node):
                    self.visit_FunctionDef(node)
                
                def get_result(self):
                    return self.best_match
            
            finder = FunctionFinder(line_number)
            finder.visit(tree)
            return finder.get_result()
            
        except Exception as e:
            # Fall back to None if AST parsing fails
            return None
    
    @staticmethod
    def find_enclosing_function_java(filepath: str, line_number: int) -> Optional[str]:
        """
        Find the enclosing method for a line in Java code with nested class support.
        
        This enhanced version correctly handles:
        - Regular methods in classes
        - Methods in static nested classes  
        - Methods in inner classes
        - Methods in anonymous classes
        - Multiple levels of nesting
        
        Args:
            filepath: Path to the Java file
            line_number: Line number (1-indexed)
            
        Returns:
            Method name with context (e.g., "OuterClass.InnerClass.methodName") or None
        """
        if not JAVALANG_AVAILABLE:
            return None
            
        try:
            # Check file size before reading (prevent memory issues)
            file_path_obj = Path(filepath)
            if file_path_obj.stat().st_size > 5 * 1024 * 1024:  # 5MB limit
                print(f"Warning: File '{filepath}' is very large ({file_path_obj.stat().st_size // (1024*1024)}MB), skipping AST parsing", file=sys.stderr)
                return CallerIdentifier.find_enclosing_function_regex(filepath, line_number)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Basic sanity check on file content
            if len(code.strip()) == 0:
                return None
                
            tree = javalang.parse.parse(code)
            
            # Build a mapping of line numbers to AST nodes
            line_to_node = {}
            
            # Custom walker to build line mapping and track nesting
            class JavaASTWalker:
                def __init__(self):
                    self.class_stack = []  # Track nested classes
                    self.method_candidates = []  # (line, end_line, full_name, node)
                
                def walk(self, node, path=None):
                    if path is None:
                        path = []
                    
                    # Handle class declarations (including nested)
                    if isinstance(node, (javalang.tree.ClassDeclaration, 
                                       javalang.tree.InterfaceDeclaration,
                                       javalang.tree.EnumDeclaration,
                                       javalang.tree.AnnotationDeclaration)):
                        self.class_stack.append(node.name)
                        current_class_path = ".".join(self.class_stack)
                        
                        # Process children
                        for child_name, child in node:
                            if child:
                                if isinstance(child, list):
                                    for item in child:
                                        self.walk(item, path + [child_name])
                                else:
                                    self.walk(child, path + [child_name])
                        
                        self.class_stack.pop()
                    
                    # Handle anonymous classes and lambda expressions
                    elif isinstance(node, javalang.tree.ClassCreator):
                        # Anonymous class - use a generic name
                        anonymous_name = f"Anonymous${len(self.class_stack)}"
                        self.class_stack.append(anonymous_name)
                        
                        # Process the body of anonymous class
                        if hasattr(node, 'body') and node.body:
                            for item in node.body:
                                self.walk(item, path + ['body'])
                        
                        self.class_stack.pop()
                    
                    # Handle lambda expressions (Java 8+)
                    elif isinstance(node, javalang.tree.LambdaExpression):
                        # Lambda expressions can contain method calls
                        lambda_name = f"Lambda${len(self.class_stack)}"
                        self.class_stack.append(lambda_name)
                        
                        if hasattr(node, 'body') and node.body:
                            self.walk(node.body, path + ['lambda_body'])
                        
                        self.class_stack.pop()
                    
                    # Handle method declarations
                    elif isinstance(node, javalang.tree.MethodDeclaration):
                        if hasattr(node, 'position') and node.position:
                            start_line = node.position.line
                            
                            # Estimate method end line by looking at the method body
                            end_line = self._estimate_method_end_line(node, start_line, code)
                            
                            # Build full method name with class context
                            class_context = ".".join(self.class_stack) if self.class_stack else ""
                            full_method_name = f"{class_context}.{node.name}" if class_context else node.name
                            
                            self.method_candidates.append((start_line, end_line, full_method_name, node))
                        
                        # Still process method body for nested classes/lambdas
                        for child_name, child in node:
                            if child and child_name == 'body':
                                if isinstance(child, list):
                                    for item in child:
                                        self.walk(item, path + [child_name])
                                else:
                                    self.walk(child, path + [child_name])
                    
                    # Handle constructor declarations
                    elif isinstance(node, javalang.tree.ConstructorDeclaration):
                        if hasattr(node, 'position') and node.position:
                            start_line = node.position.line
                            end_line = self._estimate_method_end_line(node, start_line, code)
                            
                            class_context = ".".join(self.class_stack) if self.class_stack else ""
                            constructor_name = f"{class_context}.<init>" if class_context else "<init>"
                            
                            self.method_candidates.append((start_line, end_line, constructor_name, node))
                        
                        # Process constructor body for nested constructs
                        if hasattr(node, 'body') and node.body:
                            for stmt in node.body:
                                self.walk(stmt, path + ['constructor_body'])
                    
                    # Handle static/instance initializers
                    elif isinstance(node, javalang.tree.BlockStatement):
                        # Static blocks and instance initializers
                        parent_path = path[-1] if path else ""
                        if parent_path in ['static_initializers', 'instance_initializers']:
                            class_context = ".".join(self.class_stack) if self.class_stack else ""
                            initializer_name = f"{class_context}.<{parent_path}>" if class_context else f"<{parent_path}>"
                            
                            if hasattr(node, 'position') and node.position:
                                start_line = node.position.line
                                end_line = self._estimate_block_end_line(node, start_line, code)
                                self.method_candidates.append((start_line, end_line, initializer_name, node))
                        
                        # Continue processing block statements
                        for child_name, child in node:
                            if child:
                                if isinstance(child, list):
                                    for item in child:
                                        self.walk(item, path + [child_name])
                                else:
                                    self.walk(child, path + [child_name])
                    
                    # Continue walking for other node types
                    else:
                        for child_name, child in node:
                            if child:
                                if isinstance(child, list):
                                    for item in child:
                                        self.walk(item, path + [child_name])
                                else:
                                    self.walk(child, path + [child_name])
                
                def _estimate_method_end_line(self, method_node, start_line: int, source_code: str) -> int:
                    """
                    Estimate the end line of a method by counting braces.
                    Enhanced version that handles nested braces and complex syntax.
                    """
                    lines = source_code.split('\n')
                    if start_line > len(lines):
                        return start_line
                    
                    return self._estimate_block_end_line_enhanced(start_line, lines)
                
                def _estimate_block_end_line(self, block_node, start_line: int, source_code: str) -> int:
                    """
                    Estimate the end line of a block statement.
                    """
                    lines = source_code.split('\n')
                    if start_line > len(lines):
                        return start_line
                    
                    return self._estimate_block_end_line_enhanced(start_line, lines)
                
                def _estimate_block_end_line_enhanced(self, start_line: int, lines: List[str]) -> int:
                    """
                    Enhanced brace counting that handles complex Java syntax including:
                    - Nested braces in lambdas, anonymous classes, array initializers
                    - String literals with escape sequences
                    - Block comments spanning multiple lines
                    - Generic type parameters with angle brackets
                    """
                    brace_count = 0
                    found_opening_brace = False
                    in_block_comment = False
                    
                    for i in range(start_line - 1, len(lines)):
                        line = lines[i]
                        
                        # Handle multi-line block comments
                        if in_block_comment:
                            end_comment = line.find('*/')
                            if end_comment != -1:
                                in_block_comment = False
                                line = line[end_comment + 2:]  # Continue processing rest of line
                            else:
                                continue  # Skip entire line if still in comment
                        
                        # Process character by character
                        in_string = False
                        in_char = False
                        escape_next = False
                        j = 0
                        
                        while j < len(line):
                            char = line[j]
                            
                            if escape_next:
                                escape_next = False
                                j += 1
                                continue
                            
                            if char == '\\':
                                escape_next = True
                            elif char == '"' and not in_char:
                                in_string = not in_string
                            elif char == "'" and not in_string:
                                in_char = not in_char
                            elif not in_string and not in_char:
                                if char == '{':
                                    brace_count += 1
                                    found_opening_brace = True
                                elif char == '}':
                                    brace_count -= 1
                                    if found_opening_brace and brace_count == 0:
                                        return i + 1  # Found the end
                                elif line[j:j+2] == '//':
                                    break  # Rest of line is comment
                                elif line[j:j+2] == '/*':
                                    # Start of block comment
                                    end_comment = line.find('*/', j + 2)
                                    if end_comment != -1:
                                        j = end_comment + 1  # Skip past end of comment
                                    else:
                                        in_block_comment = True
                                        break  # Comment continues to next line
                            
                            j += 1
                    
                    # If we couldn't find the end, estimate based on typical method length
                    # but cap it to prevent runaway estimates
                    return min(start_line + 100, len(lines))
            
            # Walk the AST and build method candidates
            walker = JavaASTWalker()
            walker.walk(tree)
            
            # Find the innermost method containing our target line
            best_match = None
            best_span = float('inf')
            
            for start_line, end_line, method_name, node in walker.method_candidates:
                if start_line <= line_number <= end_line:
                    span = end_line - start_line
                    if span < best_span:
                        best_span = span
                        best_match = method_name
            
            return best_match
            
        except Exception as e:
            # If AST parsing fails, fall back to the regex method
            return CallerIdentifier.find_enclosing_function_regex(filepath, line_number)
    
    @staticmethod
    def find_enclosing_function(filepath: str, line_number: int) -> Optional[str]:
        """
        Find the enclosing function/method for a line.
        
        Args:
            filepath: Path to the file
            line_number: Line number (1-indexed)
            
        Returns:
            Function/method name or None
        """
        if filepath.endswith('.py'):
            return CallerIdentifier.find_enclosing_function_python(filepath, line_number)
        elif filepath.endswith('.java') and JAVALANG_AVAILABLE:
            return CallerIdentifier.find_enclosing_function_java(filepath, line_number)
        else:
            # Fallback to regex-based extraction
            return CallerIdentifier.find_enclosing_function_regex(filepath, line_number)
    
    @staticmethod
    def find_enclosing_function_regex(filepath: str, line_number: int) -> Optional[str]:
        """
        Fallback regex-based function finder.
        
        Args:
            filepath: Path to the file
            line_number: Line number (1-indexed)
            
        Returns:
            Function name or None
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Search backwards from the target line for a function definition
            for i in range(line_number - 1, -1, -1):
                line = lines[i]
                
                # Python function
                match = re.match(r'^\s*def\s+(\w+)\s*\(', line)
                if match:
                    return match.group(1)
                
                # Java/C++ method
                match = re.match(r'^\s*(?:public|private|protected|static|\s)+\w+\s+(\w+)\s*\(', line)
                if match:
                    return match.group(1)
                
                # JavaScript function
                match = re.match(r'^\s*(?:function\s+)?(\w+)\s*(?:=\s*function\s*)?\(', line)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception:
            return None

def find_all_callers(target: str, scope: str = ".", language: str = None, 
                    whole_word: bool = True, ignore_case: bool = False) -> str:
    """
    Finds all files and locations that reference the target using ripgrep's JSON output.

    Args:
        target: The method or class name to search for.
        scope: The directory to search within.
        language: The language to filter for (e.g., 'java', 'python').
        whole_word: Whether to match whole words only.
        ignore_case: Whether to ignore case in matching.

    Returns:
        The raw JSON string output from ripgrep.
    """
    check_ripgrep()
    
    # Input validation and sanitization
    if not target or not target.strip():
        print("Error: Target cannot be empty", file=sys.stderr)
        return ""
    
    # Sanitize target to prevent command injection
    if any(char in target for char in ['`', '$', ';', '|', '&', '>', '<', '(', ')', '\n', '\r']):
        print(f"Error: Invalid characters in target '{target}'", file=sys.stderr)
        return ""
    
    # Validate scope path
    scope_path = Path(scope)
    if not scope_path.exists():
        print(f"Error: Scope path '{scope}' does not exist", file=sys.stderr)
        return ""
    
    # Sanitize language parameter
    if language and not re.match(r'^[a-zA-Z0-9_-]+$', language):
        print(f"Error: Invalid language identifier '{language}'", file=sys.stderr)
        return ""

    # Use ripgrep with JSON output for robust parsing
    cmd = ['rg', '--json']
    
    if whole_word:
        cmd.append('-w')
    
    if ignore_case:
        cmd.append('-i')
    
    if language:
        cmd.extend(['-t', language])
    
    # Add the search pattern
    cmd.append(target)
    
    # Use absolute path for scope to prevent path traversal
    cmd.append(str(scope_path.resolve()))
    
    try:
        # Enhanced subprocess security
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120,
            cwd=scope_path.resolve(),  # Set working directory explicitly
            shell=False,  # Never use shell=True
            env={'PATH': os.environ.get('PATH', '')},  # Minimal environment
            check=False  # Don't raise on non-zero exit
        )
        
        if result.returncode != 0 and result.stderr:
            print(f"Warning: ripgrep returned error: {result.stderr.strip()}", file=sys.stderr)
        
        return result.stdout
        
    except subprocess.TimeoutExpired:
        print(f"Search timed out for target: {target}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"Search failed: {e}", file=sys.stderr)
        return ""

def is_likely_definition(content: str, filepath: str) -> bool:
    """
    Determines if a line is likely a definition rather than a usage.
    
    Args:
        content: The line content.
        filepath: The file path (to determine language).
        
    Returns:
        True if likely a definition, False otherwise.
    """
    content_lower = content.lower().strip()
    
    # Language-specific definition patterns
    if filepath.endswith(('.py', '.pyw')):
        # Python function/class definitions
        return bool(re.match(r'^\s*(def|class)\s+', content))
    
    elif filepath.endswith(('.java', '.scala', '.kt')):
        # Java/JVM language method/class definitions
        # Look for access modifiers, return types, etc.
        patterns = [
            r'^\s*(public|private|protected|static|final|abstract|synchronized|native|strictfp)*\s*class\s+',
            r'^\s*(public|private|protected|static|final|abstract|synchronized|native)*\s*\w+\s+\w+\s*\(',
            r'^\s*@\w+\s*$',  # Annotations often precede definitions
        ]
        return any(re.search(pattern, content) for pattern in patterns)
    
    elif filepath.endswith(('.js', '.jsx', '.ts', '.tsx')):
        # JavaScript/TypeScript definitions
        patterns = [
            r'^\s*function\s+\w+\s*\(',
            r'^\s*(?:export\s+)?(?:async\s+)?function\s+',
            r'^\s*class\s+\w+',
            r'^\s*(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>)',
        ]
        return any(re.search(pattern, content) for pattern in patterns)
    
    elif filepath.endswith(('.c', '.cpp', '.cc', '.cxx', '.h', '.hpp')):
        # C/C++ definitions
        # Look for function signatures (return type followed by name and parentheses)
        return bool(re.search(r'^\s*(?:\w+\s+)*\w+\s+\w+\s*\([^)]*\)\s*\{?', content))
    
    elif filepath.endswith('.go'):
        # Go definitions
        return bool(re.match(r'^\s*func\s+', content))
    
    elif filepath.endswith('.rs'):
        # Rust definitions
        return bool(re.match(r'^\s*(fn|struct|enum|trait|impl)\s+', content))
    
    elif filepath.endswith('.rb'):
        # Ruby definitions
        return bool(re.match(r'^\s*(def|class|module)\s+', content))
    
    elif filepath.endswith('.php'):
        # PHP definitions
        return bool(re.match(r'^\s*(function|class)\s+', content))
    
    # Generic heuristic for unknown languages
    # Look for common definition keywords
    generic_patterns = [
        r'^\s*(function|def|class|struct|interface|enum)\s+',
        r'^\s*(public|private|protected)\s+.*\(',
    ]
    return any(re.search(pattern, content_lower) for pattern in generic_patterns)

def parse_caller_results(output: str) -> List[Dict]:
    """
    Parses ripgrep's JSON output to extract structured caller information.
    Enhanced with memory safety and security checks.

    Args:
        output: The raw JSON string from ripgrep.

    Returns:
        A list of dictionaries, where each dictionary represents a caller.
    """
    callers = []
    line_count = 0
    max_lines = 10000  # Prevent memory issues with huge outputs
    
    for line in output.strip().split('\n'):
        line_count += 1
        if line_count > max_lines:
            print(f"Warning: Output truncated after {max_lines} lines", file=sys.stderr)
            break
            
        if not line:
            continue
            
        try:
            data = json.loads(line)
            # We only care about the 'match' events
            if data['type'] == 'match':
                match_data = data['data']
                
                # Security: Validate file path
                file_path = match_data['path']['text']
                if not file_path or '..' in file_path:
                    continue  # Skip suspicious paths
                
                # Extract context lines if available
                context_before = []
                context_after = []
                
                # ripgrep JSON format includes submatches for exact positions
                submatches = match_data.get('submatches', [])
                match_positions = [(sm['start'], sm['end']) for sm in submatches] if submatches else []
                
                # Determine if this is a definition or usage
                content = match_data['lines']['text'].strip()
                
                # Limit content length to prevent memory issues
                if len(content) > 1000:
                    content = content[:1000] + "..."
                
                is_definition = is_likely_definition(content, file_path)
                
                callers.append({
                    'file': file_path,
                    'line_number': match_data['line_number'],
                    'content': content,
                    'match_positions': match_positions,
                    'context_before': context_before,
                    'context_after': context_after,
                    'is_definition': is_definition
                })
                
                # Limit total results to prevent memory issues
                if len(callers) > 5000:
                    print(f"Warning: Results truncated after {len(callers)} matches", file=sys.stderr)
                    break
                    
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Log parsing errors but continue
            if line_count <= 10:  # Only log first few errors
                print(f"Warning: Failed to parse line {line_count}: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Unexpected error parsing line {line_count}: {e}", file=sys.stderr)
            continue
            
    return callers

def highlight_match_enhanced(content: str, match_positions: List[Tuple[int, int]]) -> str:
    """
    Enhanced highlighting that colors only the exact match positions.
    
    Args:
        content: The line content.
        match_positions: List of (start, end) positions for matches.
        
    Returns:
        Content with highlighted matches.
    """
    if not match_positions:
        return content
    
    # Sort positions by start index
    positions = sorted(match_positions, key=lambda x: x[0])
    
    # Build highlighted string
    result = []
    last_end = 0
    
    for start, end in positions:
        # Adjust positions - ripgrep uses byte offsets, we need character offsets
        # For simplicity, we'll use the positions as-is
        start = max(0, start)
        end = min(len(content), end)
        
        # Add text before match
        if start > last_end:
            result.append(content[last_end:start])
        
        # Add highlighted match
        if start < len(content) and end <= len(content):
            result.append(f"\033[93m{content[start:end]}\033[0m")  # Yellow highlight
        
        last_end = end
    
    # Add remaining text
    if last_end < len(content):
        result.append(content[last_end:])
    
    return ''.join(result)

def analyze_method_usage(calls: List[Dict], target: str) -> Dict:
    """
    Analyzes a list of method calls to calculate frequency and usage patterns.

    Args:
        calls: A list of call-site dictionaries from parse_caller_results.
        target: The target method/class name for context.

    Returns:
        A dictionary containing the analysis.
    """
    # Separate definitions from usages
    definitions = [c for c in calls if c.get('is_definition', False)]
    usages = [c for c in calls if not c.get('is_definition', False)]
    
    analysis = {
        'target': target,
        'total_references': len(calls),
        'total_definitions': len(definitions),
        'total_usages': len(usages),
        'unique_files': len(set(c['file'] for c in calls)),
        'by_file': Counter(c['file'] for c in usages),  # Count only usages per file
        'definitions': definitions,
        'calling_contexts': Counter(),
        'usage_patterns': defaultdict(list),
        'enclosing_functions': Counter()  # NEW: Track which functions call our target
    }
    
    # Analyze calling contexts and identify enclosing functions
    for call in usages:
        content = call['content']
        content_lower = content.lower()
        
        # Identify the enclosing function using AST
        enclosing_func = CallerIdentifier.find_enclosing_function(
            call['file'], 
            call['line_number']
        )
        if enclosing_func:
            analysis['enclosing_functions'][enclosing_func] += 1
        
        # Detect calling context
        if re.search(r'\bif\s*\(|else\s+if\s*\(|\belse\b', content):
            analysis['calling_contexts']['conditional'] += 1
            analysis['usage_patterns']['conditional'].append(call)
        elif re.search(r'\bfor\s*\(|\bwhile\s*\(|\bdo\s*{', content):
            analysis['calling_contexts']['loop'] += 1
            analysis['usage_patterns']['loop'].append(call)
        elif re.search(r'\breturn\s+', content):
            analysis['calling_contexts']['return_statement'] += 1
            analysis['usage_patterns']['return'].append(call)
        elif re.search(r'\bcatch\s*\(|\btry\s*{|\bthrow\s+', content):
            analysis['calling_contexts']['exception_handling'] += 1
            analysis['usage_patterns']['exception'].append(call)
        elif re.search(r'=\s*' + re.escape(target), content):
            analysis['calling_contexts']['assignment'] += 1
            analysis['usage_patterns']['assignment'].append(call)
        elif re.search(r'\bnew\s+' + re.escape(target), content):
            analysis['calling_contexts']['instantiation'] += 1
            analysis['usage_patterns']['instantiation'].append(call)
        else:
            analysis['calling_contexts']['other'] += 1
            analysis['usage_patterns']['other'].append(call)
    
    # Detect if this is likely a utility method (used across many files)
    if analysis['unique_files'] > 5 and analysis['total_usages'] > 10:
        analysis['likely_utility'] = True
    else:
        analysis['likely_utility'] = False
    
    return analysis

def build_recursive_call_tree_enhanced(target: str, scope: str, language: str, 
                                      whole_word: bool, ignore_case: bool,
                                      max_depth: int, current_depth: int = 0,
                                      seen_targets: Optional[Set[str]] = None) -> Dict:
    """
    Enhanced recursive call tree building using AST-based caller identification.
    
    Args:
        target: The method/class to analyze.
        scope: Directory to search.
        language: Programming language filter.
        whole_word: Whether to match whole words only.
        ignore_case: Whether to ignore case.
        max_depth: Maximum recursion depth.
        current_depth: Current recursion depth.
        seen_targets: Set of already analyzed targets to prevent cycles.
        
    Returns:
        Dictionary representing the call tree.
    """
    if seen_targets is None:
        seen_targets = set()
    
    # Prevent infinite recursion
    if current_depth >= max_depth or target in seen_targets:
        return {'target': target, 'depth': current_depth, 'truncated': True}
    
    seen_targets.add(target)
    
    # Find all callers of this target
    search_results = find_all_callers(target, scope, language, whole_word, ignore_case)
    callers = parse_caller_results(search_results)
    
    # Separate definitions from usages
    definitions = [c for c in callers if c.get('is_definition', False)]
    usages = [c for c in callers if not c.get('is_definition', False)]
    
    # Build node
    node = {
        'target': target,
        'depth': current_depth,
        'total_references': len(callers),
        'definitions': len(definitions),
        'usages': len(usages),
        'callers': []
    }
    
    # Extract unique caller functions using AST
    caller_functions = Counter()
    for usage in usages:
        enclosing_func = CallerIdentifier.find_enclosing_function(
            usage['file'], 
            usage['line_number']
        )
        if enclosing_func and enclosing_func != target:
            caller_functions[enclosing_func] += 1
    
    # Recursively analyze top caller functions
    for caller_func, count in caller_functions.most_common(5):  # Top 5 callers
        if caller_func not in seen_targets:
            child_node = build_recursive_call_tree_enhanced(
                caller_func, scope, language, whole_word, ignore_case,
                max_depth, current_depth + 1, seen_targets
            )
            child_node['call_count'] = count  # Add how many times it calls the target
            node['callers'].append(child_node)
    
    return node

def format_call_tree_enhanced(tree: Dict, indent: str = "") -> str:
    """
    Enhanced call tree formatting with call counts.
    
    Args:
        tree: The call tree dictionary.
        indent: Current indentation level.
        
    Returns:
        Formatted string representation.
    """
    output = []
    
    # Format current node
    truncated = " [TRUNCATED]" if tree.get('truncated', False) else ""
    refs = f"({tree.get('usages', 0)} usages, {tree.get('definitions', 0)} defs)"
    call_count = f" ×{tree.get('call_count', '')}" if tree.get('call_count') else ""
    output.append(f"{indent}└─ {tree['target']}{call_count} {refs}{truncated}")
    
    # Format children
    for i, child in enumerate(tree.get('callers', [])):
        is_last = i == len(tree['callers']) - 1
        child_indent = indent + ("   " if is_last else "│  ")
        output.extend(format_call_tree_enhanced(child, child_indent).split('\n'))
    
    return '\n'.join(output).rstrip()

def format_analysis_report(analysis: Dict, show_samples: bool = True, 
                         max_samples: int = 3, show_ast_context: bool = False) -> str:
    """
    Formats the usage analysis into a readable report with enhanced function tracking.
    """
    # Initialize AST context finder if needed
    context_finder = None
    if show_ast_context and HAS_AST_CONTEXT:
        context_finder = ASTContextFinder()
    output = []
    
    # Header
    output.append("=" * 80)
    output.append(f"CROSS-FILE USAGE ANALYSIS: '{analysis['target']}'")
    output.append("=" * 80)
    
    # Summary statistics
    output.append(f"\n📊 SUMMARY STATISTICS")
    output.append("-" * 40)
    output.append(f"Total References: {analysis['total_references']}")
    output.append(f"  Definitions: {analysis['total_definitions']}")
    output.append(f"  Usages: {analysis['total_usages']}")
    output.append(f"Unique Files: {analysis['unique_files']}")
    output.append(f"Average Usages per File: {analysis['total_usages'] / max(1, analysis['unique_files']):.1f}")
    
    if analysis['likely_utility']:
        output.append("\n⚡ This appears to be a utility method (used across many files)")
    
    # Show definitions if any
    if analysis['definitions']:
        output.append(f"\n📌 DEFINITIONS FOUND")
        output.append("-" * 40)
        for defn in analysis['definitions'][:3]:  # Show up to 3 definitions
            # Get AST context if available
            context_str = ""
            if context_finder:
                context = context_finder._format_context_parts(
                    context_finder.get_context_for_line(defn['file'], defn['line_number'])
                )
                if context:
                    context_str = f" [{context}]"
            
            output.append(f"  {Path(defn['file']).name}:{defn['line_number']}{context_str}")
            highlighted = highlight_match_enhanced(defn['content'], defn.get('match_positions', []))
            output.append(f"    {highlighted}")
        if len(analysis['definitions']) > 3:
            output.append(f"  ... and {len(analysis['definitions']) - 3} more")
    
    # NEW: Show enclosing functions
    if analysis.get('enclosing_functions'):
        output.append(f"\n🔗 CALLING FUNCTIONS")
        output.append("-" * 40)
        for func_name, count in analysis['enclosing_functions'].most_common(10):
            output.append(f"  {func_name}() - {count} call{'s' if count > 1 else ''}")
        if len(analysis['enclosing_functions']) > 10:
            output.append(f"  ... and {len(analysis['enclosing_functions']) - 10} more")
    
    # Top files by usage
    output.append(f"\n📁 TOP FILES BY USAGE (excluding definitions)")
    output.append("-" * 40)
    for file_path, count in analysis['by_file'].most_common(10):
        file_name = Path(file_path).name
        output.append(f"  {count:3d}x {file_name:30} ({file_path})")
    
    if len(analysis['by_file']) > 10:
        output.append(f"  ... and {len(analysis['by_file']) - 10} more files")
    
    # Calling contexts
    output.append(f"\n🔍 CALLING CONTEXTS")
    output.append("-" * 40)
    total_contexts = sum(analysis['calling_contexts'].values())
    for context, count in analysis['calling_contexts'].most_common():
        percentage = (count / total_contexts * 100) if total_contexts > 0 else 0
        context_name = context.replace('_', ' ').title()
        output.append(f"  {context_name:20} {count:4d} ({percentage:5.1f}%)")
    
    # Sample usage patterns
    if show_samples and analysis['usage_patterns']:
        output.append(f"\n💡 SAMPLE USAGE PATTERNS")
        output.append("-" * 40)
        
        for pattern, calls in analysis['usage_patterns'].items():
            if calls and pattern != 'other':
                output.append(f"\n{pattern.upper().replace('_', ' ')}:")
                for call in calls[:max_samples]:
                    # Get AST context if available
                    context_str = ""
                    if context_finder:
                        context = context_finder._format_context_parts(
                            context_finder.get_context_for_line(call['file'], call['line_number'])
                        )
                        if context:
                            context_str = f" [{context}]"
                    
                    output.append(f"  {Path(call['file']).name}:{call['line_number']}{context_str}")
                    highlighted = highlight_match_enhanced(call['content'], call.get('match_positions', []))
                    output.append(f"    {highlighted}")
                if len(calls) > max_samples:
                    output.append(f"  ... and {len(calls) - max_samples} more")
    
    return '\n'.join(output)

def main():
    if HAS_STANDARD_PARSER:
        parser = create_analyze_parser('Enhanced cross-file dependency analysis with AST support')
    else:
        parser = argparse.ArgumentParser(
            description='''Enhanced cross-file dependency analysis with AST support
            
Examples:
  # Find class instantiations  
  # Case-insensitive search  
  # With usage analysis (includes enclosing functions)  
  # Output as JSON  
  # Recursive call tree analysis (AST-enhanced)  
  # Find definitions vs usages  

AST SUPPORT:
  - Python: Built-in ast module (always available)
  - Java: javalang library (install with: pip install javalang)
  - Others: Regex-based fallback
            ''',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
    
    # Only add target argument if standard parser hasn't already added it
    if not HAS_STANDARD_PARSER:
        parser.add_argument('target', help='Method or class name to find references for')
    
    # Add common arguments if standard parser not available
    if not HAS_STANDARD_PARSER:
        parser.add_argument('--scope', default='.', help='Directory to search in (default: current directory)')
        parser.add_argument('--quiet', '-q', action='store_true', help='Suppress verbose output')
        parser.add_argument('--ignore-case', '-i', action='store_true', help='Ignore case when searching')
        parser.add_argument('--json', action='store_true', help='Output results as JSON')
        parser.add_argument('--recursive', action='store_true', help='Build recursive call tree')
        parser.add_argument('--max-depth', type=int, default=3, help='Maximum recursion depth (default: 3)')
    
    # Search options - only add if not provided by standard parser
    if not HAS_STANDARD_PARSER:
        parser.add_argument('--language', '--lang', choices=['python', 'java', 'javascript', 'cpp', 'go', 'rust'],
                           help='Filter by programming language')
    
    parser.add_argument('--no-whole-word', action='store_true', 
                       help='Don\'t require whole word matching')
    
    # Add recursive analysis options (needed regardless of standard parser)
    # Only add if not already present
    try:
        parser.add_argument('--recursive', action='store_true', help='Build recursive call tree')
    except argparse.ArgumentError:
        pass  # Already exists
    
    try:
        parser.add_argument('--max-depth', type=int, default=3, help='Maximum recursion depth (default: 3)')
    except argparse.ArgumentError:
        pass  # Already exists
    
    # Analysis options
    parser.add_argument('--analyze', action='store_true',
                       help='Perform usage frequency and pattern analysis')
    parser.add_argument('--show-samples', action='store_true', default=True,
                       help='Show sample usage patterns (default: true)')
    parser.add_argument('--max-samples', type=int, default=3,
                       help='Maximum samples per pattern (default: 3)')
    
    # Output options - only add if not provided by standard parser
    if not HAS_STANDARD_PARSER:
        parser.add_argument('--ast-context', action='store_true',
                           help='Show AST context (class/method) for each result')
    
    args = parser.parse_args()
    
    try:
        # Find all callers
        if not args.quiet:
            print(f"Searching for references to '{args.target}'...", file=sys.stderr)
            if JAVALANG_AVAILABLE:
                print("✨ Using AST-enhanced caller identification", file=sys.stderr)
            else:
                print("⚠️  javalang not installed - using regex fallback for Java", file=sys.stderr)
        
        search_results = find_all_callers(
            args.target, 
            args.scope, 
            args.language,
            whole_word=not args.no_whole_word,
            ignore_case=args.ignore_case
        )
        
        # Parse results
        callers = parse_caller_results(search_results)
        
        if not callers:
            print(f"No references found for '{args.target}'")
            sys.exit(0)
        
        # Handle recursive analysis
        if args.recursive:
            if not args.quiet:
                print(f"Building recursive call tree (max depth: {args.max_depth})...", file=sys.stderr)
            
            call_tree = build_recursive_call_tree_enhanced(
                args.target, args.scope, args.language,
                whole_word=not args.no_whole_word,
                ignore_case=args.ignore_case,
                max_depth=args.max_depth
            )
            
            if args.json:
                print(json.dumps(call_tree, indent=2))
            else:
                print(f"\n🌳 RECURSIVE CALL TREE for '{args.target}'")
                print("=" * 60)
                print(format_call_tree_enhanced(call_tree))
                print("\nNote: Shows up to 5 callers per function, max depth: " + str(args.max_depth))
            sys.exit(0)
        
        # Output based on mode
        if args.json:
            if args.analyze:
                analysis = analyze_method_usage(callers, args.target)
                # Convert Counter objects to dicts for JSON serialization
                analysis['by_file'] = dict(analysis['by_file'])
                analysis['calling_contexts'] = dict(analysis['calling_contexts'])
                analysis['enclosing_functions'] = dict(analysis['enclosing_functions'])
                # Don't include full usage_patterns in JSON (too verbose)
                analysis.pop('usage_patterns', None)
                output = {
                    'analysis': analysis,
                    'callers': callers
                }
            else:
                output = {'callers': callers}
            
            print(json.dumps(output, indent=2))
        
        elif args.analyze:
            # Perform analysis and show report
            analysis = analyze_method_usage(callers, args.target)
            report = format_analysis_report(analysis, args.show_samples, args.max_samples, args.ast_context)
            print(report)
        
        else:
            # Simple list of callers
            definitions = [c for c in callers if c.get('is_definition', False)]
            usages = [c for c in callers if not c.get('is_definition', False)]
            
            # Initialize AST context finder if needed
            context_finder = None
            if args.ast_context and HAS_AST_CONTEXT:
                context_finder = ASTContextFinder()
            
            print(f"Found {len(callers)} reference(s) to '{args.target}':")
            if definitions:
                print(f"  {len(definitions)} definition(s)")
            if usages:
                print(f"  {len(usages)} usage(s)\n")
            
            # Show definitions first
            if definitions:
                print("DEFINITIONS:")
                for defn in definitions:
                    # Get AST context if available
                    context_str = ""
                    if context_finder:
                        context = context_finder._format_context_parts(
                            context_finder.get_context_for_line(defn['file'], defn['line_number'])
                        )
                        if context:
                            context_str = f" [{context}]"
                    
                    print(f"{defn['file']}:{defn['line_number']}{context_str}")
                    if not args.quiet:
                        highlighted = highlight_match_enhanced(defn['content'], defn.get('match_positions', []))
                        print(f"  {highlighted}")
                print()
            
            # Show usages
            if usages:
                print("USAGES:")
                for caller in usages:
                    # Get AST context if available
                    context_str = ""
                    if context_finder:
                        context = context_finder._format_context_parts(
                            context_finder.get_context_for_line(caller['file'], caller['line_number'])
                        )
                        if context:
                            context_str = f" [{context}]"
                    
                    print(f"{caller['file']}:{caller['line_number']}{context_str}")
                    if not args.quiet:
                        highlighted = highlight_match_enhanced(caller['content'], caller.get('match_positions', []))
                        print(f"  {highlighted}\n")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()