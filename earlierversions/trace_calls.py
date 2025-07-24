#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Trace method call hierarchies in Java code.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-19
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re, sys, json, argparse, subprocess, logging, shutil, os
from collections import defaultdict, deque
from pathlib import Path

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    format="%(levelname)s: %(message)s")
LOG = logging.getLogger("trace_calls")

from java_parsing_utils import find_closing_brace

# Import configuration support with fallback
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass
find_closing_brace

# Import AST context finder
try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

# Import the superior CallerIdentifier from cross_file_analysis_ast
try:
    from cross_file_analysis_ast import CallerIdentifier
    HAS_CALLER_IDENTIFIER = True
except ImportError:
    HAS_CALLER_IDENTIFIER = False

# Import the superior AST-based analyzer for finding callees
try:
    from method_analyzer_ast import analyze_method_body_ast, find_method_definition
    HAS_METHOD_ANALYZER = True
except ImportError:
    HAS_METHOD_ANALYZER = False

# Note: extract_method_calls and find_method_in_file functions removed
# We now use AST-based analysis from method_analyzer_ast.py instead

def find_callers(method_name, search_scope="src/", max_depth=3):
    """Find all methods that call the specified method."""
    callers = defaultdict(list)
    visited = set()
    
    def search_level(target_method, current_depth):
        if current_depth > max_depth:
            return

        level_callers = set()

        # Use ripgrep to find all usages
        cmd = ['rg', '--json', '-w', target_method, search_scope, '-t', 'java']
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data['type'] == 'match':
                        match_data = data['data']
                        file_path = match_data['path']['text']
                        line_num = match_data['line_number']
                        line_content = match_data['lines']['text'].strip()

                        # Use the superior AST-based identifier
                        containing_method = None
                        if HAS_CALLER_IDENTIFIER:
                            containing_method = CallerIdentifier.find_enclosing_function(file_path, line_num)
                        else:
                            # Fallback to regex if module not found
                            with open(file_path, 'r') as f_read:
                                lines = f_read.readlines()
                            for i in range(line_num - 1, max(-1, line_num - 100), -1):
                                method_def = re.match(r'^\s*((?:public|private|protected)\s+)?((?:static|final|synchronized)\s+)*([\w<>\[\]]+\s+)?(\w+)\s*\([^)]*\)', lines[i])
                                if method_def:
                                    containing_method = method_def.group(4)
                                    break
                        
                        if containing_method and (file_path, containing_method) not in visited:
                            level_callers.add((file_path, containing_method, int(line_num)))
                            visited.add((file_path, containing_method))
                            callers[current_depth].append({
                                'file': file_path, 'method': containing_method,
                                'line': int(line_num), 'context': line_content,
                            })
                except (json.JSONDecodeError, KeyError):
                    continue
        except subprocess.CalledProcessError as e:
            LOG.error("ripgrep failed: %s", e)
            return

        # Recursively find callers of the callers
        if current_depth < max_depth:
            for file_path, method, _ in level_callers:
                search_level(method, current_depth + 1)
    
    search_level(method_name, 1)
    return dict(callers)

def find_callees(file_path, method_name, max_depth=3):
    """Find all methods called by the specified method."""
    callees = defaultdict(list)
    visited = set()
    
    def trace_calls(current_file, current_method, current_depth, parent_path):
        if current_depth > max_depth or (current_file, current_method) in visited:
            return
        
        if not HAS_METHOD_ANALYZER:
            print("Warning: method_analyzer_ast.py not found, cannot trace callees.", file=sys.stderr)
            return

        visited.add((current_file, current_method))
        
        # Use the AST-based analyzer to get accurate call information
        # Detect language based on file extension
        language = 'java' if str(current_file).endswith('.java') else 'python'
        analysis = analyze_method_body_ast(current_file, current_method, language)

        # Check for analysis errors
        if 'error' in analysis:
            print(f"Warning: Could not analyze {current_method} in {current_file}: {analysis['error']}", file=sys.stderr)
            return

        # Add unique calls to the callee list
        for call in analysis.get('calls_with_args', []):
            call_info = {
                'method': call['method'],
                'object': None,  # This info is less relevant in AST context
                'file': current_file,
                'caller_method': current_method,
                'path': parent_path + [current_method],
                'line': call.get('line', 0)
            }
            
            callees[current_depth].append(call_info)

        # Recurse on unique methods found
        unique_callees = sorted(list(analysis.get('unique_methods', set())))
        for called_method_name in unique_callees:
            if current_depth < max_depth:
                # Find definition of the callee to trace it
                # We search the whole scope, as it could be in another file
                definitions = find_method_definition(called_method_name, Path(current_file).parent, language)
                if definitions:
                    next_file = definitions[0]['file']
                    trace_calls(next_file, called_method_name, current_depth + 1, parent_path + [current_method])
    
    trace_calls(file_path, method_name, 1, [])
    return dict(callees)

def build_call_tree(method_name, callers, callees, show_ast_context=False, file_path=None):
    """Build a visual representation of the call tree."""
    tree_lines = []
    
    # Initialize AST context finder if needed
    context_finder = None
    if show_ast_context and HAS_AST_CONTEXT:
        context_finder = ASTContextFinder()
    
    # Add callers (who calls this method)
    if callers:
        tree_lines.append("CALLERS (who calls this method):")
        tree_lines.append("=" * 60)
        
        for depth in sorted(callers.keys()):
            indent = "  " * (depth - 1)
            tree_lines.append(f"\n{indent}Level {depth}:")
            
            for caller in callers[depth]:
                # Get AST context if available
                context_str = ""
                if context_finder:
                    context = context_finder._format_context_parts(
                        context_finder.get_context_for_line(caller['file'], caller['line'])
                    )
                    if context:
                        context_str = f" [{context}]"
                
                tree_lines.append(f"{indent}├── {caller['method']}{context_str} in {Path(caller['file']).name}:{caller['line']}")
                tree_lines.append(f"{indent}│   {caller['context'][:60]}...")
    
    # Add the target method
    tree_lines.append("\n" + "=" * 60)
    target_context_str = ""
    if context_finder and file_path and HAS_METHOD_ANALYZER:
        # Find definition to get line number for context
        language = 'java' if str(file_path).endswith('.java') else 'python'
        definitions = find_method_definition(method_name, str(Path(file_path).parent), language)
        if definitions:
            context = context_finder._format_context_parts(
                context_finder.get_context_for_line(definitions[0]['file'], definitions[0]['line'])
            )
            if context:
                target_context_str = f" [{context}]"
    
    tree_lines.append(f"TARGET METHOD: {method_name}{target_context_str}")
    tree_lines.append("=" * 60)
    
    # Add callees (what this method calls)
    if callees:
        tree_lines.append("\nCALLEES (what this method calls):")
        tree_lines.append("=" * 60)
        
        for depth in sorted(callees.keys()):
            indent = "  " * (depth - 1)
            tree_lines.append(f"\n{indent}Level {depth}:")
            
            # Group by method name to avoid duplicates
            seen_methods = set()
            for callee in callees[depth]:
                method_id = f"{callee['method']}"
                if method_id not in seen_methods:
                    seen_methods.add(method_id)
                    obj_prefix = f"{callee['object']}." if callee['object'] else ""
                    tree_lines.append(f"{indent}├── {obj_prefix}{callee['method']}()")
    
    return "\n".join(tree_lines)

def analyze_call_patterns(callers, callees):
    """Analyze and summarize call patterns."""
    analysis = {
        'total_callers': sum(len(calls) for calls in callers.values()),
        'total_callees': sum(len(calls) for calls in callees.values()),
        'max_caller_depth': max(callers.keys()) if callers else 0,
        'max_callee_depth': max(callees.keys()) if callees else 0,
        'unique_caller_files': set(),
        'unique_callee_methods': set()
    }
    
    # Count unique files and methods
    for calls in callers.values():
        for caller in calls:
            analysis['unique_caller_files'].add(caller['file'])
    
    for calls in callees.values():
        for callee in calls:
            analysis['unique_callee_methods'].add(callee['method'])
    
    return analysis

def print_analysis(analysis):
    """Print call pattern analysis."""
    print("\n" + "=" * 60)
    print("CALL PATTERN ANALYSIS")
    print("=" * 60)
    
    print(f"\nIncoming calls (callers):")
    print(f"  Total callers: {analysis['total_callers']}")
    print(f"  Unique files: {len(analysis['unique_caller_files'])}")
    print(f"  Max depth traced: {analysis['max_caller_depth']}")
    
    print(f"\nOutgoing calls (callees):")
    print(f"  Total calls: {analysis['total_callees']}")
    print(f"  Unique methods called: {len(analysis['unique_callee_methods'])}")
    print(f"  Max depth traced: {analysis['max_callee_depth']}")

def main():
    parser = argparse.ArgumentParser(description='Trace method call hierarchies')
    parser.add_argument('method_name', help='Method name to trace')
    parser.add_argument('--file', help='File containing the method (for callee tracing)')
    parser.add_argument('--max-depth', type=int, default=3,
                       help='Maximum depth to trace (default: 3)')
    parser.add_argument('--direction', choices=['up', 'down', 'both'],
                       default='both', help='Trace direction: up (callers), down (callees), or both')
    parser.add_argument('--scope', default='.',
                       help='Directory scope for searching (default: current directory)')
    parser.add_argument('--ast-context', action='store_true', default=True,
                       help='Show AST context (class/method) for each result (default: enabled)')
    parser.add_argument('--no-ast-context', action='store_true',
                       help='Disable AST context display')
    
    args = parser.parse_args()
    
    # Handle AST context flag logic
    if args.no_ast_context:
        args.ast_context = False
    
    if not shutil.which("rg"):
        LOG.error("ripgrep (rg) is required but not found in PATH")
        sys.exit(2)
    
    callers = {}
    callees = {}
    
    # Find callers (up direction)
    if args.direction in ['up', 'both']:
        print(f"Tracing callers of '{args.method_name}'...")
        callers = find_callers(args.method_name, args.scope, args.max_depth)
    
    # Find callees (down direction)
    if args.direction in ['down', 'both']:
        if not args.file:
            print("Warning: --file not specified, cannot trace callees")
            print("To trace what a method calls, specify the file containing it")
        else:
            if not Path(args.file).exists():
                print(f"Error: File '{args.file}' not found")
                sys.exit(1)
            
            print(f"Tracing callees of '{args.method_name}'...")
            callees = find_callees(args.file, args.method_name, args.max_depth)
    
    # Build and print call tree
    tree = build_call_tree(args.method_name, callers, callees, args.ast_context, args.file)
    print("\n" + tree)
    
    # Analyze patterns
    analysis = analyze_call_patterns(callers, callees)
    print_analysis(analysis)

if __name__ == "__main__":
    main()