#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Analyze internal method usage within a single Java file.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
import os
from pathlib import Path
from collections import defaultdict
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
        @staticmethod
        def check_directory_accessible(path):
            return True, ""

# Import AST context finder
try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

def analyze_internal_usage(file_path, show_ast_context=False):
    """Analyze which methods are used internally within the file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Initialize AST context finder if needed
    context_finder = None
    if show_ast_context and HAS_AST_CONTEXT:
        context_finder = ASTContextFinder()
    
    # Extract all method declarations
    method_pattern = r'^\s*(public|private|protected)(?:\s+(?:static|final|synchronized|abstract))*\s+(?:(?:<[^>]+>\s+)?([^(\s]+)\s+)?([a-zA-Z0-9_]+)\s*\([^)]*\)'
    
    methods = {}
    for match in re.finditer(method_pattern, content, re.MULTILINE):
        method_name = match.group(3)
        visibility = match.group(1)
        lines_before = content[:match.start()].count('\n')
        line_number = lines_before + 1
        
        methods[method_name] = {
            'visibility': visibility,
            'line': line_number,
            'internal_calls': 0,
            'call_locations': []
        }
    
    # Find method calls within the file
    for method_name in methods:
        # Skip constructor
        if method_name == Path(file_path).stem.split('.')[-1]:
            continue
            
        # Look for method calls: this.method(), method(), or just method(
        call_patterns = [
            rf'this\.{method_name}\s*\(',
            rf'(?<!\.){method_name}\s*\(',  # Not preceded by a dot
        ]
        
        for pattern in call_patterns:
            for match in re.finditer(pattern, content):
                # Skip the method declaration itself
                lines_before = content[:match.start()].count('\n') + 1
                if lines_before != methods[method_name]['line']:
                    methods[method_name]['internal_calls'] += 1
                    methods[method_name]['call_locations'].append(lines_before)
    
    # Categorize methods
    never_called_internally = []
    called_once = []
    called_multiple = []
    
    for name, info in methods.items():
        if info['internal_calls'] == 0:
            never_called_internally.append((name, info))
        elif info['internal_calls'] == 1:
            called_once.append((name, info))
        else:
            called_multiple.append((name, info))
    
    # Display results
    print(f"Internal Method Usage Analysis for {file_path}")
    print("=" * 80)
    print(f"Total methods: {len(methods)}\n")
    
    if never_called_internally:
        print(f"METHODS NEVER CALLED INTERNALLY ({len(never_called_internally)}):")
        print("-" * 60)
        if show_ast_context:
            print(f"{'Method Name':<40} {'Visibility':<10} {'Line':<6} {'Context'}")
        else:
            print(f"{'Method Name':<40} {'Visibility':<10} {'Line':<6}")
        print("-" * 60)
        for name, info in sorted(never_called_internally, key=lambda x: x[1]['line']):
            # Get AST context if available
            context_str = ""
            if context_finder:
                context = context_finder._format_context_parts(
                    context_finder.get_context_for_line(file_path, info['line'])
                )
                if context:
                    context_str = f"[{context}]"
            
            if show_ast_context:
                print(f"{name:<40} {info['visibility']:<10} {info['line']:<6} {context_str}")
            else:
                print(f"{name:<40} {info['visibility']:<10} {info['line']:<6}")
        print()
    
    if called_once:
        print(f"METHODS CALLED ONCE INTERNALLY ({len(called_once)}):")
        print("-" * 60)
        for name, info in sorted(called_once, key=lambda x: x[1]['line']):
            # Get AST context if available
            context_str = ""
            if context_finder:
                context = context_finder._format_context_parts(
                    context_finder.get_context_for_line(file_path, info['line'])
                )
                if context:
                    context_str = f" [{context}]"
            
            print(f"{name} (line {info['line']}{context_str}) - called at line {info['call_locations'][0]}")
        print()
    
    if called_multiple:
        print(f"METHODS CALLED MULTIPLE TIMES ({len(called_multiple)}):")
        print("-" * 60)
        for name, info in sorted(called_multiple, key=lambda x: -x[1]['internal_calls']):
            print(f"{name} - {info['internal_calls']} calls")
    
    # Special analysis for private methods
    print(f"\nPRIVATE METHOD ANALYSIS:")
    print("-" * 60)
    private_unused = [(n, i) for n, i in never_called_internally if i['visibility'] == 'private']
    
    if private_unused:
        print(f"Found {len(private_unused)} private methods that are never called internally.")
        print("These are potential candidates for removal unless they are:")
        print("  - Called via reflection")
        print("  - Used as method references/lambdas")
        print("  - Part of a framework requirement")
        print("\nPrivate methods never called internally:")
        for name, info in sorted(private_unused, key=lambda x: x[1]['line']):
            # Get AST context if available
            context_str = ""
            if context_finder:
                context = context_finder._format_context_parts(
                    context_finder.get_context_for_line(file_path, info['line'])
                )
                if context:
                    context_str = f" [{context}]"
            
            print(f"  Line {info['line']:4d}: {name}(){context_str}")
    else:
        print("All private methods are called at least once internally.")

def analyze_directory(directory_path, ast_context=False):
    """Analyze all Java files in a directory."""
    java_files = []
    
    # Find all Java files
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))
    
    if not java_files:
        print(f"No Java files found in '{directory_path}'")
        return
    
    print(f"Found {len(java_files)} Java files to analyze\n")
    
    # Analyze each file
    for file_path in sorted(java_files):
        relative_path = os.path.relpath(file_path, directory_path)
        print(f"\nAnalyzing: {relative_path}")
        print("=" * 80)
        analyze_internal_usage(file_path, ast_context)

def main():
    # Don't use standard parser for this tool - it needs custom arguments
    parser = argparse.ArgumentParser(
        description='Analyze internal method usage within Java classes',
        epilog='This helps identify methods that are defined but never called within the same class.'
    )
    
    # Add tool-specific arguments - support both positional and --file for compatibility
    parser.add_argument('path', nargs='?', help='Java file or directory to analyze')
    parser.add_argument('--file', dest='file_path', help='Java file to analyze (alternative to positional path)')
    parser.add_argument('--ast-context', action='store_true',
                       help='Show AST context (class/method) for each result')
    
    args = parser.parse_args()
    
    # Handle file path from either positional or --file argument
    file_path = args.path or args.file_path
    if not file_path:
        print('Error: File or directory path required', file=sys.stderr)
        sys.exit(1)
    
    # Run preflight checks
    path = Path(file_path)
    checks = []
    if path.is_file():
        checks.append((PreflightChecker.check_file_readable, (str(path),)))
    elif path.is_dir():
        checks.append((PreflightChecker.check_directory_accessible, (str(path),)))
    
    if checks:
        run_preflight_checks(checks)
    
    if not path.exists():
        print(f"Error: Path '{file_path}' not found")
        sys.exit(1)
    
    if path.is_file():
        if not file_path.endswith('.java'):
            print(f"Error: File '{file_path}' is not a Java file")
            sys.exit(1)
        analyze_internal_usage(file_path, args.ast_context)
    elif path.is_dir():
        analyze_directory(file_path, args.ast_context)
    else:
        print(f"Error: '{file_path}' is neither a file nor a directory")
        sys.exit(1)

if __name__ == "__main__":
    main()