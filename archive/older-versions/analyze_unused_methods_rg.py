#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Find potentially unused methods in a Java file using ripgrep.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
from pathlib import Path
import argparse
import subprocess
import shutil
from preflight_checks import run_preflight_checks, PreflightChecker

# Import standard argument parser with fallback
try:
    from standard_arg_parser import create_standard_parser
except ImportError:
    import argparse
    def create_standard_parser(description, tool_type='analyze'):
        return argparse.ArgumentParser(description=description)

# Import configuration support with fallback
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass
shutil

try:
    import javalang
    HAS_JAVALANG = True
except ImportError:
    HAS_JAVALANG = False

# Import AST context finder
try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

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

def extract_methods(file_path):
    """Extract all method declarations from a Java file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    methods = []
    
    if HAS_JAVALANG:
        try:
            tree = javalang.parse.parse(content)
            for path, node in tree:
                if isinstance(node, javalang.tree.MethodDeclaration):
                    # Get line number
                    line_num = node.position.line if node.position else 0
                    
                    # Build parameter string
                    params = []
                    for param in node.parameters:
                        param_type = param.type.name if hasattr(param.type, 'name') else str(param.type)
                        params.append(f"{param_type} {param.name}")
                    param_str = ', '.join(params)
                    
                    methods.append({
                        'name': node.name,
                        'line': line_num,
                        'modifiers': node.modifiers,
                        'return_type': node.return_type.name if node.return_type and hasattr(node.return_type, 'name') else 'void',
                        'parameters': param_str,
                        'is_public': 'public' in node.modifiers,
                        'is_private': 'private' in node.modifiers,
                        'is_static': 'static' in node.modifiers,
                        'is_test': any(ann.name in ['Test', 'ParameterizedTest'] for ann in (node.annotations or []))
                    })
        except Exception as e:
            print(f"Warning: Failed to parse with javalang: {e}")
            # Fall back to regex
            return extract_methods_regex(content)
    else:
        return extract_methods_regex(content)
    
    return methods

def extract_methods_regex(content):
    """Fallback regex-based method extractor."""
    methods = []
    
    # Improved regex to capture method declarations
    method_pattern = re.compile(
        r'^[ \t]*(?P<modifiers>(?:public|private|protected|static|final|abstract|synchronized|native|\s)+)?'
        r'(?P<return_type>\w+(?:\s*<[^>]+>)?(?:\s*\[\s*\])?)\s+'
        r'(?P<name>\w+)\s*\('
        r'(?P<params>[^)]*)\)',
        re.MULTILINE
    )
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        match = method_pattern.search(line)
        if match and not line.strip().startswith('//'):
            modifiers = match.group('modifiers') or ''
            methods.append({
                'name': match.group('name'),
                'line': i + 1,
                'modifiers': modifiers.split(),
                'return_type': match.group('return_type'),
                'parameters': match.group('params').strip(),
                'is_public': 'public' in modifiers,
                'is_private': 'private' in modifiers,
                'is_static': 'static' in modifiers,
                'is_test': '@Test' in lines[max(0, i-5):i]  # Check previous 5 lines for @Test
            })
    
    return methods

def find_method_calls_rg(method_name, search_scope="src/", ignore_self=None):
    """Find all calls to a method using ripgrep."""
    check_ripgrep()
    
    # Build patterns for method calls
    escaped = re.escape(method_name)
    patterns = [
        fr'\.{escaped}\s*\(',      # Instance method: obj.method(
        fr'\b{escaped}\s*\(',      # Direct call: method(
        fr'::{escaped}\b',         # Method reference: ::method
        fr'"{escaped}"',           # String reference (reflection)
    ]
    
    # Combine patterns
    combined_pattern = '|'.join(f'({p})' for p in patterns)
    
    # Run ripgrep
    cmd = ['rg', '-c', '-t', 'java', combined_pattern, search_scope]
    
    total_calls = 0
    calling_files = []
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.rsplit(':', 1)
                    if len(parts) == 2:
                        file_path, count = parts
                        count = int(count)
                        if ignore_self and file_path == ignore_self:
                            # For self-references, we need to subtract 1 for the declaration
                            count = max(0, count - 1)
                        if count > 0:
                            total_calls += count
                            calling_files.append((file_path, count))
    except Exception as e:
        print(f"Error running ripgrep: {e}")
    
    return total_calls, calling_files

def analyze_unused_methods(file_path, search_scope="src/", include_private=False, show_ast_context=False):
    """Find potentially unused methods in a file."""
    print(f"Analyzing methods in: {file_path}")
    print("=" * 80)
    
    # Initialize AST context finder if needed
    context_finder = None
    if show_ast_context and HAS_AST_CONTEXT:
        context_finder = ASTContextFinder()
    
    # Extract all methods
    methods = extract_methods(file_path)
    if not methods:
        print("No methods found in file.")
        return
    
    print(f"Found {len(methods)} methods")
    print("-" * 80)
    
    # Analyze each method
    unused = []
    used = []
    
    for method in methods:
        # Skip methods we typically don't check
        if method['name'] in ['main', 'toString', 'equals', 'hashCode']:
            continue
        
        # Skip test methods
        if method['is_test']:
            continue
        
        # Skip private methods if not requested
        if method['is_private'] and not include_private:
            continue
        
        # Check for overrides (simple heuristic)
        if method['name'].startswith('on') or method['name'].startswith('handle'):
            # Likely an event handler or callback
            continue
        
        # Find calls to this method
        calls, calling_files = find_method_calls_rg(method['name'], search_scope, ignore_self=file_path)
        
        method_info = {
            'method': method,
            'calls': calls,
            'calling_files': calling_files
        }
        
        if calls == 0:
            unused.append(method_info)
        else:
            used.append(method_info)
    
    # Print results
    if unused:
        print(f"\nPotentially unused methods ({len(unused)}):")
        print("-" * 80)
        for info in sorted(unused, key=lambda x: x['method']['line']):
            method = info['method']
            modifiers = ' '.join(method['modifiers']) if method['modifiers'] else 'package-private'
            
            # Get AST context if available
            context_str = ""
            if context_finder:
                context = context_finder._format_context_parts(
                    context_finder.get_context_for_line(file_path, method['line'])
                )
                if context:
                    context_str = f" [{context}]"
            
            print(f"\nLine {method['line']}{context_str}: {method['name']}({method['parameters']})")
            print(f"  Modifiers: {modifiers}")
            print(f"  Return type: {method['return_type']}")
    else:
        print("\nNo unused methods found!")
    
    # Summary of used methods
    if used:
        print(f"\n\nUsed methods ({len(used)}):")
        print("-" * 80)
        for info in sorted(used, key=lambda x: -x['calls']):
            method = info['method']
            
            # Get AST context if available
            context_str = ""
            if context_finder:
                context = context_finder._format_context_parts(
                    context_finder.get_context_for_line(file_path, method['line'])
                )
                if context:
                    context_str = f" [{context}]"
            
            print(f"\n{method['name']}({method['parameters']}){context_str} - {info['calls']} calls")
            if info['calling_files'][:3]:  # Show top 3 callers
                print("  Called from:")
                for file, count in info['calling_files'][:3]:
                    print(f"    - {file} ({count} times)")
                if len(info['calling_files']) > 3:
                    print(f"    ... and {len(info['calling_files']) - 3} more files")

def main():
    # Create a basic parser without predefined tool type arguments
    import argparse
    parser = argparse.ArgumentParser(description='Find unused methods in Java files using ripgrep')
    
    # Add the required file argument
    parser.add_argument('file', help='Java file to analyze')
    parser.add_argument('--include-private', action='store_true',
                       help='Include private methods in analysis')
    parser.add_argument('--summary', action='store_true',
                       help='Show only summary without details')
    parser.add_argument('--ast-context', action='store_true',
                       help='Show AST context (class/method hierarchy)')
    parser.add_argument('--no-ast-context', action='store_true',
                       help='Disable AST context')
    
    args = parser.parse_args()
    
    # Run preflight checks
    run_preflight_checks([
        (PreflightChecker.check_file_readable, (args.file,)),
        (PreflightChecker.check_ripgrep_installed, ())
    ])
    
    # Load configuration and apply to args
    config = load_config()
    apply_config_to_args('analyze_unused_methods_rg', args, parser, config)
    
    if not Path(args.file).exists():
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    # Determine ast_context setting
    if args.no_ast_context:
        ast_context = False
    elif args.ast_context:
        ast_context = True
    else:
        # Use config or default to False
        ast_context = getattr(args, 'ast_context', False)
    
    # Use directory of the file as scope if not specified
    scope = getattr(args, 'scope', Path(args.file).parent)
    analyze_unused_methods(args.file, scope, args.include_private, ast_context)

if __name__ == "__main__":
    main()