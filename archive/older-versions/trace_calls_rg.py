#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Trace method call hierarchies in Java code using ripgrep.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
from pathlib import Path
import subprocess
from collections import defaultdict, deque
from preflight_checks import run_preflight_checks
from java_parsing_utils import find_closing_brace
# Import standard argument parser
try:
    from standard_arg_parser import create_standard_parser as create_parser
    HAS_STANDARD_PARSER = True
except ImportError:
    import argparse
    HAS_STANDARD_PARSER = False
    
    def create_parser(tool_type, description):
        return argparse.ArgumentParser(description=description)
import shutil
import json

# Import configuration support with fallback
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass
json

def check_ripgrep():
    """Check if ripgrep is installed."""
    try:
        from dependency_checker import check_ripgrep as check_rg
        check_rg()
    except ImportError:
        # Fallback if dependency_checker not available
        if not shutil.which('rg'):
            print("Error: ripgrep (rg) is not installed.", file=sys.stderr)
            print("Install it from: https://github.com/BurntSushi/ripgrep#installation", file=sys.stderr)
            sys.exit(1)

def extract_method_calls(method_content):
    """Extract all method calls from a method body."""
    calls = []
    
    # Pattern for method calls: object.method(), method(), ClassName.method()
    call_pattern = r'(?:(\w+)\.)?(\w+)\s*\('
    
    for match in re.finditer(call_pattern, method_content):
        object_ref = match.group(1)
        method_name = match.group(2)
        
        # Skip common keywords that look like method calls
        if method_name in ['if', 'while', 'for', 'switch', 'catch', 'synchronized', 'new']:
            continue
        
        calls.append({
            'object': object_ref,
            'method': method_name,
            'full_call': match.group(0)
        })
    
    return calls

def find_method_in_file(file_path, method_name):
    """Find a method definition in a file and extract its content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find method definition
    escaped = re.escape(method_name)
    method_pattern = rf'((?:public|private|protected)\s+)?((?:static|final|synchronized|abstract|native)\s+)*((?:[\w<>\[\],.\s]+\s+)?)?{escaped}\s*\([^)]*\)(?:\s+throws\s+[^{{]+)?\s*\{{'
    
    match = re.search(method_pattern, content, re.MULTILINE)
    if not match:
        return None
    
    # Extract the complete method body
    start_pos = match.start()
    brace_pos = content.find('{', match.end() - 10)  # Find opening brace near match end
    
    if brace_pos == -1:
        return None
        
    end_pos = find_closing_brace(content, brace_pos)
    
    if end_pos != -1:
        method_content = content[start_pos:end_pos]
        lines_before = content[:start_pos].count('\n')
        
        return {
            'content': method_content,
            'start_line': lines_before + 1,
            'file': file_path,
            'signature': match.group(0).split('{')[0].strip()
        }
    
    return None

def find_callers(method_name, search_scope="src/", max_depth=3):
    """Find all methods that call the specified method using ripgrep."""
    check_ripgrep()
    callers = defaultdict(list)
    visited = set()
    
    def search_level(target_method, current_depth):
        if current_depth > max_depth:
            return
        
        # Search for calls to this method
        escaped = re.escape(target_method)
        patterns = [
            fr'\.{escaped}\s*\(',      # Instance method: obj.method(
            fr'\b{escaped}\s*\(',      # Direct call: method(
            fr'::{escaped}\b',         # Method reference: ::method
        ]
        
        level_callers = set()
        
        # Combine patterns for ripgrep
        combined_pattern = '|'.join(f'({p})' for p in patterns)
        
        # Use ripgrep with JSON output for structured parsing
        cmd = ['rg', '--json', '-t', 'java', combined_pattern, search_scope]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    if data.get('type') != 'match':
                        continue
                    
                    match_data = data['data']
                    file_path = match_data['path']['text']
                    line_num = match_data['line_number']
                    line_content = match_data['lines']['text'].rstrip()
                    
                    # Try to extract the containing method
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                    
                    # Search backwards for method definition
                    method_line = int(line_num) - 1
                    containing_method = None
                    
                    for i in range(method_line, max(-1, method_line - 100), -1):
                        method_def = re.match(r'^\s*((?:public|private|protected)\s+)?((?:static|final|synchronized)\s+)*([\w<>\[\]]+\s+)?(\w+)\s*\([^)]*\)', lines[i])
                        if method_def:
                            containing_method = method_def.group(4)
                            break
                    
                    if containing_method and (file_path, containing_method) not in visited:
                        level_callers.add((file_path, containing_method, int(line_num)))
                        visited.add((file_path, containing_method))
                        
                        callers[current_depth].append({
                            'file': file_path,
                            'method': containing_method,
                            'line': int(line_num),
                            'context': line_content.strip()
                        })
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"Error searching with ripgrep: {e}", file=sys.stderr)
        
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
        
        visited.add((current_file, current_method))
        
        # Find the method in the file
        method_info = find_method_in_file(current_file, current_method)
        if not method_info:
            return
        
        # Extract method calls
        calls = extract_method_calls(method_info['content'])
        
        for call in calls:
            call_info = {
                'method': call['method'],
                'object': call['object'],
                'file': current_file,
                'caller_method': current_method,
                'path': parent_path + [current_method]
            }
            
            callees[current_depth].append(call_info)
            
            # Try to find the called method in the same file (simplified)
            if current_depth < max_depth:
                next_method_info = find_method_in_file(current_file, call['method'])
                if next_method_info:
                    trace_calls(current_file, call['method'], current_depth + 1, 
                              parent_path + [current_method])
    
    trace_calls(file_path, method_name, 1, [])
    return dict(callees)

def build_call_tree(method_name, callers, callees):
    """Build a visual representation of the call tree."""
    tree_lines = []
    
    # Add callers (who calls this method)
    if callers:
        tree_lines.append("CALLERS (who calls this method):")
        tree_lines.append("=" * 60)
        
        for depth in sorted(callers.keys()):
            indent = "  " * (depth - 1)
            tree_lines.append(f"\n{indent}Level {depth}:")
            
            for caller in callers[depth]:
                tree_lines.append(f"{indent}├── {caller['method']} in {Path(caller['file']).name}:{caller['line']}")
                tree_lines.append(f"{indent}│   {caller['context'][:60]}...")
    
    # Add the target method
    tree_lines.append("\n" + "=" * 60)
    tree_lines.append(f"TARGET METHOD: {method_name}")
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
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Trace method call hierarchies using ripgrep')
    else:
        parser = argparse.ArgumentParser(description='Trace method call hierarchies using ripgrep')
    
    # Add additional arguments not provided by standard parser
    if not HAS_STANDARD_PARSER:
        parser.add_argument('target', help='Method name to trace')
    
    # For standard parser, --file is already provided, so use --source-file for callee tracing
    if HAS_STANDARD_PARSER:
        parser.add_argument('--source-file', help='File containing the method (for callee tracing)')
    
    parser.add_argument('--direction', choices=['up', 'down', 'both'],
                       default='both', help='Trace direction: up (callers), down (callees), or both')
    
    args = parser.parse_args()
    
    # Run preflight checks
    from preflight_checks import PreflightChecker
    checks = [(PreflightChecker.check_ripgrep_installed, ())]
    if hasattr(args, 'scope') and args.scope:
        checks.append((PreflightChecker.check_directory_accessible, (args.scope,)))
    run_preflight_checks(checks)
    
    # Handle target name mapping for standard parser compatibility
    method_name = getattr(args, 'target', getattr(args, 'method_name', None))
    if not method_name:
        print('Error: Method name required', file=sys.stderr)
        sys.exit(1)
    
    callers = {}
    callees = {}
    
    # Find callers (up direction)
    if args.direction in ['up', 'both']:
        print(f"Tracing callers of '{method_name}'...")
        callers = find_callers(method_name, args.scope, args.max_depth)
    
    # Find callees (down direction)
    if args.direction in ['down', 'both']:
        # Get the file path for callee tracing
        file_path = getattr(args, 'source_file', None) or getattr(args, 'file', None)
        
        if not file_path:
            file_arg = '--source-file' if HAS_STANDARD_PARSER else            print(f"Warning: {file_arg} not specified, cannot trace callees")
            print("To trace what a method calls, specify the file containing it")
        else:
            if not Path(file_path).exists():
                print(f"Error: File '{file_path}' not found")
                sys.exit(1)
            
            print(f"Tracing callees of '{method_name}'...")
            callees = find_callees(file_path, method_name, args.max_depth)
    
    # Build and print call tree
    tree = build_call_tree(method_name, callers, callees)
    print("\n" + tree)
    
    # Analyze patterns
    analysis = analyze_call_patterns(callers, callees)
    print_analysis(analysis)

if __name__ == "__main__":
    main()