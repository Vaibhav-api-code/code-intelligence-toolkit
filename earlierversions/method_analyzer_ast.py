#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
AST-enhanced method analyzer for accurate call flow analysis and parameter tracking.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict, Counter
import json
import ast
import shutil
from typing import List, Dict, Set, Tuple, Optional

# Try to import javalang for Java AST support
try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False

# Import AST context finder
try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

# Import common utilities
try:
    from common_utils import check_ripgrep, detect_language, add_common_args
except ImportError:
    def check_ripgrep():
        if not shutil.which('rg'):
            print("Error: ripgrep (rg) is not installed.", file=sys.stderr)
            sys.exit(1)

# Import pre-flight checks
try:
    from preflight_checks import PreflightChecker, check_method_name, check_ripgrep as check_rg
except ImportError:
    PreflightChecker = None
    check_method_name = None
    check_rg = None


class PythonCallAnalyzer:
    """AST-based call analyzer for Python code."""
    
    @staticmethod
    def extract_method_calls(code: str, method_name: str) -> List[Dict]:
        """
        Extract all method calls from Python code using AST.
        
        Returns list of dicts with:
        - method: The method being called
        - args: List of argument strings
        - line: Line number
        - context: The containing function/method
        """
        calls = []
        
        try:
            tree = ast.parse(code)
            
            class CallVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.current_context = None
                    self.context_stack = []
                
                def visit_FunctionDef(self, node):
                    # Track context
                    self.context_stack.append(node.name)
                    self.current_context = node.name
                    self.generic_visit(node)
                    self.context_stack.pop()
                    self.current_context = self.context_stack[-1] if self.context_stack else None
                
                def visit_AsyncFunctionDef(self, node):
                    self.visit_FunctionDef(node)
                
                def visit_ClassDef(self, node):
                    self.context_stack.append(f"class {node.name}")
                    self.generic_visit(node)
                    self.context_stack.pop()
                
                def visit_Call(self, node):
                    # Extract the method name being called
                    method = None
                    if isinstance(node.func, ast.Name):
                        method = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        method = node.func.attr
                    
                    if method:
                        # Extract arguments
                        args = []
                        
                        # Positional arguments
                        for arg in node.args:
                            try:
                                args.append(ast.unparse(arg) if hasattr(ast, 'unparse') else repr(arg))
                            except:
                                args.append("...")
                        
                        # Keyword arguments
                        for kw in node.keywords:
                            try:
                                if kw.arg:
                                    value = ast.unparse(kw.value) if hasattr(ast, 'unparse') else repr(kw.value)
                                    args.append(f"{kw.arg}={value}")
                            except:
                                args.append("...")
                        
                        calls.append({
                            'method': method,
                            'args': args,
                            'line': node.lineno if hasattr(node, 'lineno') else 0,
                            'context': self.current_context or 'module_level'
                        })
                    
                    self.generic_visit(node)
            
            visitor = CallVisitor()
            visitor.visit(tree)
            
        except SyntaxError as e:
            print(f"Warning: Python syntax error: {e}", file=sys.stderr)
            return PythonCallAnalyzer._extract_calls_regex(code, method_name)
        except (RecursionError, MemoryError) as e:
            print(f"Warning: Python AST processing failed: {e}", file=sys.stderr)
            return PythonCallAnalyzer._extract_calls_regex(code, method_name)
        
        return calls
    
    @staticmethod
    def _extract_calls_regex(code: str, method_name: str) -> List[Dict]:
        """Fallback regex-based extraction."""
        calls = []
        lines = code.splitlines()
        
        for i, line in enumerate(lines):
            # Find method calls
            matches = re.finditer(r'(\w+)\s*\((.*?)\)', line)
            for match in matches:
                method = match.group(1)
                args_str = match.group(2)
                
                # Skip language keywords
                if method in {'if', 'while', 'for', 'with', 'except', 'def', 'class'}:
                    continue
                
                args = [arg.strip() for arg in args_str.split(',') if arg.strip()]
                calls.append({
                    'method': method,
                    'args': args,
                    'line': i + 1,
                    'context': 'unknown'
                })
        
        return calls


class JavaCallAnalyzer:
    """AST-based call analyzer for Java code."""
    
    @staticmethod
    def extract_method_calls(code: str, method_name: str) -> List[Dict]:
        """
        Extract all method calls from Java code using javalang AST.
        """
        if not JAVALANG_AVAILABLE:
            return JavaCallAnalyzer._extract_calls_regex(code, method_name)
        
        calls = []
        
        try:
            tree = javalang.parse.parse(code)
            
            # Track current context
            context_stack = []
            
            for path, node in tree:
                # Update context
                if isinstance(node, javalang.tree.ClassDeclaration):
                    context_stack = [f"class {node.name}"]
                elif isinstance(node, javalang.tree.MethodDeclaration):
                    if context_stack:
                        context = f"{context_stack[0]}.{node.name}"
                    else:
                        context = node.name
                
                # Find method invocations
                if isinstance(node, javalang.tree.MethodInvocation):
                    # Extract arguments
                    args = []
                    if node.arguments:
                        for arg in node.arguments:
                            # Try to get a string representation
                            if isinstance(arg, javalang.tree.Literal):
                                args.append(arg.value)
                            elif isinstance(arg, javalang.tree.MemberReference):
                                args.append(arg.member)
                            else:
                                args.append(str(type(arg).__name__))
                    
                    calls.append({
                        'method': node.member,
                        'args': args,
                        'line': node.position.line if node.position else 0,
                        'context': context if 'context' in locals() else 'unknown'
                    })
        
        except Exception as e:
            print(f"Warning: Java AST processing failed: {e}", file=sys.stderr)
            return JavaCallAnalyzer._extract_calls_regex(code, method_name)
        
        return calls
    
    @staticmethod
    def _extract_calls_regex(code: str, method_name: str) -> List[Dict]:
        """Fallback regex-based extraction."""
        calls = []
        lines = code.splitlines()
        
        for i, line in enumerate(lines):
            # Find method calls
            matches = re.finditer(r'(\w+)\s*\((.*?)\)', line)
            for match in matches:
                method = match.group(1)
                args_str = match.group(2)
                
                # Skip language keywords and common class names
                if method in {'if', 'while', 'for', 'switch', 'catch', 'new', 'return', 
                             'System', 'String', 'Integer', 'Boolean'}:
                    continue
                
                args = [arg.strip() for arg in args_str.split(',') if arg.strip()]
                calls.append({
                    'method': method,
                    'args': args,
                    'line': i + 1,
                    'context': 'unknown'
                })
        
        return calls


def find_method_definition(method_name: str, scope: str = ".", language: str = "java") -> List[Dict]:
    """Find where a method is defined using ripgrep."""
    check_ripgrep()
    
    # Input validation
    if not method_name or not method_name.strip():
        return []
    
    # Sanitize method name (only allow valid identifiers)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', method_name.strip()):
        print(f"Warning: Invalid method name '{method_name}' - must be a valid identifier", file=sys.stderr)
        return []
    
    # Validate scope path
    scope_path = Path(scope)
    if not scope_path.exists():
        print(f"Warning: Scope path '{scope}' does not exist", file=sys.stderr)
        return []
    
    # Pattern to find method definitions
    if language == 'python':
        pattern = rf'^\s*def\s+{re.escape(method_name)}\s*\('
    elif language == 'java':
        pattern = rf'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+{re.escape(method_name)}\s*\('
    else:
        pattern = rf'\b{re.escape(method_name)}\s*\('
    
    cmd = ['rg', '--json', '-t', language, pattern, str(scope)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        definitions = []
        
        for line in result.stdout.split('\n'):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data['type'] == 'match':
                    match_data = data['data']
                    file_path = match_data['path']['text']
                    
                    # Security: Ensure file path is within scope
                    if Path(file_path).resolve().is_relative_to(scope_path.resolve()):
                        definitions.append({
                            'file': file_path,
                            'line': match_data['line_number'],
                            'content': match_data['lines']['text'].strip()
                        })
            except (json.JSONDecodeError, KeyError):
                continue
        
        return definitions[:100]  # Limit results to prevent memory issues
    except subprocess.TimeoutExpired:
        print("Warning: Search timed out after 30 seconds", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Warning: Search failed: {e}", file=sys.stderr)
        return []


def analyze_method_body_ast(file_path: str, method_name: str, language: str) -> Dict:
    """
    Analyze a method's body using AST to extract accurate call flow.
    """
    try:
        # Security: Check file size before reading
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return {'error': f"File '{file_path}' does not exist"}
        
        file_size = file_path_obj.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            print(f"Warning: File '{file_path}' is very large ({file_size // (1024*1024)}MB), analysis may be slow", file=sys.stderr)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Basic content validation
        if len(code.strip()) == 0:
            return {'error': f"File '{file_path}' appears to be empty"}
        
        # Use appropriate analyzer
        if language == 'python':
            all_calls = PythonCallAnalyzer.extract_method_calls(code, method_name)
        elif language == 'java':
            all_calls = JavaCallAnalyzer.extract_method_calls(code, method_name)
        else:
            # Fallback to simple extraction
            all_calls = extract_calls_simple(code)
        
        # Filter to calls within the target method
        method_calls = [
            call for call in all_calls 
            if call['context'] and method_name in call['context']
        ]
        
        # Also get all calls if we couldn't determine context
        if not method_calls:
            method_calls = all_calls[:1000]  # Limit to prevent memory issues
        
        # Analyze the calls
        call_analysis = {
            'total_calls': len(method_calls),
            'unique_methods': set(call['method'] for call in method_calls),
            'call_frequency': Counter(call['method'] for call in method_calls),
            'calls_with_args': method_calls[:100],  # Limit for output size
            'ast_used': language in ['python', 'java']
        }
        
        return call_analysis
        
    except (UnicodeDecodeError, PermissionError, FileNotFoundError) as e:
        return {
            'total_calls': 0,
            'unique_methods': set(),
            'call_frequency': Counter(),
            'calls_with_args': [],
            'ast_used': False,
            'error': f"File access error: {e}"
        }
    except (RecursionError, MemoryError) as e:
        return {
            'total_calls': 0,
            'unique_methods': set(),
            'call_frequency': Counter(),
            'calls_with_args': [],
            'ast_used': False,
            'error': f"Processing error: {e}"
        }
    except Exception as e:
        return {
            'total_calls': 0,
            'unique_methods': set(),
            'call_frequency': Counter(),
            'calls_with_args': [],
            'ast_used': False,
            'error': str(e)
        }


def extract_calls_simple(code: str) -> List[Dict]:
    """Simple regex-based call extraction as ultimate fallback."""
    calls = []
    matches = re.finditer(r'(\w+)\s*\((.*?)\)', code, re.MULTILINE)
    
    for i, match in enumerate(matches):
        method = match.group(1)
        if method not in {'if', 'while', 'for', 'switch', 'catch', 'new', 'return'}:
            calls.append({
                'method': method,
                'args': [match.group(2)] if match.group(2) else [],
                'line': 0,  # Can't determine line number easily
                'context': 'unknown'
            })
    
    return calls


def trace_method_flow_ast(method_name: str, scope: str = ".", language: str = "java", 
                         max_depth: int = 3) -> Dict:
    """
    Trace method call flow using AST for accurate analysis.
    """
    traced = set()
    
    def trace_recursive(target_method: str, depth: int) -> List[Dict]:
        if depth > max_depth or target_method in traced:
            return []
        
        # Prevent stack overflow from too many recursive calls
        if len(traced) > 100:  # Reasonable limit
            return []
        
        traced.add(target_method)
        
        # Find method definition
        definitions = find_method_definition(target_method, scope, language)
        if not definitions:
            return []
        
        # Analyze the first definition
        def_info = definitions[0]
        analysis = analyze_method_body_ast(def_info['file'], target_method, language)
        
        # Check for analysis errors
        if 'error' in analysis:
            print(f"Warning: Analysis failed for {target_method}: {analysis['error']}", file=sys.stderr)
            return []
        
        # Build call tree
        children = []
        for called_method in sorted(analysis['unique_methods'])[:10]:  # Limit to 10
            if called_method != target_method:  # Avoid self-recursion
                children.append({
                    'method': called_method,
                    'frequency': analysis['call_frequency'].get(called_method, 0),
                    'ast_used': analysis['ast_used'],
                    'children': trace_recursive(called_method, depth + 1)
                })
        
        return children
    
    return {
        'root': method_name,
        'ast_analysis': True,
        'children': trace_recursive(method_name, 1)
    }


def format_ast_analysis_report(method_name: str, definitions: List[Dict], 
                             flow_analysis: Dict, show_args: bool = True,
                             show_ast_context: bool = False) -> str:
    """Format the AST-enhanced analysis report."""
    output = []
    
    # Initialize AST context finder if needed
    context_finder = None
    if show_ast_context and HAS_AST_CONTEXT:
        context_finder = ASTContextFinder()
    
    # Header
    output.append("=" * 80)
    output.append(f"AST-ENHANCED METHOD ANALYSIS: '{method_name}'")
    output.append("=" * 80)
    
    # Definitions found
    if definitions:
        output.append(f"\n📍 METHOD DEFINITIONS FOUND: {len(definitions)}")
        output.append("-" * 40)
        for defn in definitions[:3]:
            # Get AST context if available
            context_str = ""
            if context_finder:
                context = context_finder._format_context_parts(
                    context_finder.get_context_for_line(defn['file'], defn['line'])
                )
                if context:
                    context_str = f" [{context}]"
            
            output.append(f"{defn['file']}:{defn['line']}{context_str}")
            output.append(f"  {defn['content']}")
    else:
        output.append("\n⚠️  No method definitions found")
        return '\n'.join(output)
    
    # Analyze first definition in detail
    first_def = definitions[0]
    body_analysis = analyze_method_body_ast(first_def['file'], method_name, 
                                          detect_language(first_def['file']))
    
    if body_analysis['ast_used']:
        output.append("\n✨ Using AST analysis for accurate call extraction")
    else:
        output.append("\n⚠️  AST not available - using regex fallback")
    
    # Method calls analysis
    output.append(f"\n📊 METHOD CALLS ANALYSIS")
    output.append("-" * 40)
    output.append(f"Total method calls: {body_analysis['total_calls']}")
    output.append(f"Unique methods called: {len(body_analysis['unique_methods'])}")
    
    if body_analysis['call_frequency']:
        output.append("\nMost frequently called methods:")
        for method, count in body_analysis['call_frequency'].most_common(10):
            output.append(f"  {method:30} {count:3d}x")
    
    # Show calls with arguments if requested
    if show_args and body_analysis['calls_with_args']:
        output.append(f"\n📋 CALLS WITH ARGUMENTS")
        output.append("-" * 40)
        
        for i, call in enumerate(body_analysis['calls_with_args'][:10]):
            output.append(f"\n{i+1}. {call['method']}({', '.join(call['args'])})")
            if call.get('line'):
                output.append(f"   Line: {call['line']}")
            if call.get('context') and call['context'] != 'unknown':
                output.append(f"   Context: {call['context']}")
    
    # Flow analysis
    if flow_analysis and flow_analysis.get('children'):
        output.append(f"\n🔄 CALL FLOW TREE (AST-based)")
        output.append("-" * 40)
        
        def format_tree(node: Dict, indent: int = 0) -> List[str]:
            lines = []
            prefix = "  " * indent + ("└─ " if indent > 0 else "")
            
            if isinstance(node, dict) and 'method' in node:
                freq = f" ({node.get('frequency', 1)}x)" if node.get('frequency') else ""
                ast_marker = " [AST]" if node.get('ast_used') else " [Regex]"
                lines.append(f"{prefix}{node['method']}{freq}{ast_marker}")
                
                for child in node.get('children', []):
                    lines.extend(format_tree(child, indent + 1))
            
            return lines
        
        output.append(f"Root: {flow_analysis['root']}")
        for child in flow_analysis.get('children', []):
            output.extend(format_tree(child))
    
    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(
        description='AST-enhanced method analyzer for accurate call flow analysis',
        epilog='''
EXAMPLES:
  # Analyze method with AST-based call extraction
  %(prog)s processOrder --trace-flow
  
  # Show detailed argument analysis
  %(prog)s calculatePrice --show-args --language python
  
  # Deep call tree analysis
  %(prog)s initialize --max-depth 4 --scope src/
  
  # Export analysis as JSON
  %(prog)s sendNotification --json

AST SUPPORT:
  - Python: Built-in ast module (always available)
  - Java: javalang library (install with: pip install javalang)
  - Others: Regex-based fallback
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("method_name", help="Method name to analyze")
    parser.add_argument("--file", dest="file_path", type=Path, required=True,
                        help="Path to the source file containing the method to analyze")

    # Analysis options
    parser.add_argument('--scope', default='.',
                        help='Directory to search for call definitions during flow tracing (default: current)')
    parser.add_argument('--language', '--lang',
                       choices=['python', 'java', 'auto'], default='auto',
                       help='Programming language (default: auto-detect)')
    parser.add_argument('--trace-flow', action='store_true',
                       help='Trace method call flow using AST')
    parser.add_argument('--show-args', action='store_true', default=True,
                       help='Show method arguments (default: true)')
    parser.add_argument('--max-depth', type=int, default=3,
                       help='Maximum depth for flow tracing (default: 3)')

    # Output options
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output')
    parser.add_argument('--ast-context', action='store_true', default=True,
                       help='Show AST context (class/method) for each result (default: enabled)')
    parser.add_argument('--no-ast-context', action='store_true',
                       help='Disable AST context display')
    
    args = parser.parse_args()
    
    # Handle AST context flag logic
    if args.no_ast_context:
        args.ast_context = False
    
    # Pre-flight checks
    if PreflightChecker:
        # Use new pre-flight system
        success, error_msg = PreflightChecker.validate_method_name(args.method_name)
        if not success:
            print(error_msg, file=sys.stderr)
            print(f"Usage: {parser.prog} <method_name> [options]", file=sys.stderr)
            print(f"Example: {parser.prog} calculatePrice --scope src/", file=sys.stderr)
            sys.exit(2)
        
        # Check ripgrep
        if check_rg:
            check_rg()
        else:
            check_ripgrep()
    else:
        # Fallback to original checks
        if '/' in args.method_name or '\\' in args.method_name:
            print(f"Error: It looks like you provided a file path instead of a method name.", file=sys.stderr)
            print(f"Usage: {parser.prog} <method_name> [options]", file=sys.stderr)
            print(f"Example: {parser.prog} calculatePrice --scope src/", file=sys.stderr)
            sys.exit(2)
        
        if args.method_name.endswith('.java') or args.method_name.endswith('.py'):
            print(f"Error: Please provide just the method name, not a file name.", file=sys.stderr)
            print(f"Usage: {parser.prog} <method_name> [options]", file=sys.stderr)
            print(f"Example: {parser.prog} processOrder --trace-flow", file=sys.stderr)
            sys.exit(2)
        
        check_ripgrep()
    
    try:
        # Find method definitions
        if not args.quiet:
            print(f"Searching for method '{args.method_name}'...", file=sys.stderr)
        
        definitions = find_method_definition(args.method_name, args.scope, args.language)
        
        if not definitions:
            print(f"No definitions found for method '{args.method_name}'")
            sys.exit(0)
        
        # Auto-detect language if needed
        if args.language == 'auto' and definitions:
            first_file = definitions[0]['file']
            if first_file.endswith('.py'):
                args.language = 'python'
            elif first_file.endswith('.java'):
                args.language = 'java'
        
        # Trace flow if requested
        flow_analysis = None
        if args.trace_flow:
            if not args.quiet:
                ast_status = "✨ AST available" if (args.language == 'python' or JAVALANG_AVAILABLE) else "⚠️ Using regex"
                print(f"Tracing call flow... {ast_status}", file=sys.stderr)
            
            flow_analysis = trace_method_flow_ast(args.method_name, args.scope, 
                                                args.language, args.max_depth)
        
        # Output results
        if args.json:
            # Analyze first definition for JSON output
            first_def = definitions[0]
            body_analysis = analyze_method_body_ast(first_def['file'], args.method_name, args.language)
            
            output = {
                'method': args.method_name,
                'definitions': definitions,
                'analysis': {
                    'total_calls': body_analysis['total_calls'],
                    'unique_methods': list(body_analysis['unique_methods']),
                    'call_frequency': dict(body_analysis['call_frequency']),
                    'ast_used': body_analysis['ast_used']
                },
                'flow': flow_analysis
            }
            
            if args.show_args:
                output['calls_with_args'] = body_analysis['calls_with_args']
            
            print(json.dumps(output, indent=2))
        else:
            # Format report
            report = format_ast_analysis_report(
                args.method_name, definitions, flow_analysis, args.show_args,
                args.ast_context
            )
            print(report)
    
    except KeyboardInterrupt:
        print("\nAnalysis interrupted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()