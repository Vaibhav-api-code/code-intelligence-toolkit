#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Find all references to a method, field, or class in the codebase using ripgrep.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
import subprocess
from pathlib import Path
from preflight_checks import run_preflight_checks
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

# Import configuration support with fallback
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass
shutil

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

def find_references(target_name, scope="src/", ref_type="auto", context_lines=3,
                    ignore_case=False):
    """Find all references to a method, field, or class using ripgrep.

    Parameters
    ----------
    target_name : str
        Name of the method, field, or class to search for.
    scope : str
        Root directory to search. Defaults to ``src/``.
    ref_type : str
        One of ``method``, ``field``, ``class``, or ``auto`` to infer type.
    context_lines : int
        Number of context lines to include around each reference.
    ignore_case : bool
        Perform a case-insensitive search when True.
    """
    
    check_ripgrep()
    references = []
    
    # Build search patterns based on type
    if ref_type == "auto":
        # Try to detect type based on name
        if target_name[0].isupper():
            ref_type = "class"
        elif target_name.endswith("()"):
            ref_type = "method"
            target_name = target_name[:-2]  # Remove ()
        else:
            ref_type = "method"  # Default to method
    
    patterns = []
    escaped = re.escape(target_name)
    
    if ref_type == "method":
        patterns = [
            fr'\.{escaped}\s*\(',      # Instance method: obj.method(
            fr'\b{escaped}\s*\(',      # Direct call: method(
            fr'::{escaped}\b',         # Method reference: ::method
            fr'"{escaped}"',           # String reference (reflection)
        ]
    elif ref_type == "field":
        patterns = [
            fr'\.{escaped}\b',         # Instance field: obj.field
            fr'\b{escaped}\s*=',       # Assignment: field =
            fr'\b{escaped}\s*\.',      # Field access: field.
            fr'\b{escaped}\s*\[',      # Array access: field[
            fr'"{escaped}"',           # String reference
        ]
    elif ref_type == "class":
        patterns = [
            fr'\bnew\s+{escaped}\s*\(',     # Instantiation: new Class(
            fr'\bnew\s+{escaped}\s*\[',     # Array creation: new Class[
            fr'\b{escaped}\.class\b',       # Class literal: Class.class
            fr'\b{escaped}\s+\w+\s*[=;]',   # Variable declaration: Class var
            fr'\bextends\s+{escaped}\b',    # Inheritance: extends Class
            fr'\bimplements\s+{escaped}\b', # Implementation: implements Class
            fr'\b{escaped}<',               # Generic usage: Class<
            fr'\({escaped}\)',              # Cast: (Class)
            fr'@{escaped}\b',               # Annotation: @Class
        ]
    
    # Combine all patterns into a single regex for ripgrep
    combined_pattern = '|'.join(f'({p})' for p in patterns)
    
    # Build ripgrep command
    rg_cmd = ['rg', '--json', '-U']  # -U for multiline
    if ignore_case:
        rg_cmd.append('-i')
    rg_cmd.extend([
        '-t', 'java',  # Only Java files
        '--context', str(context_lines),
        combined_pattern,
        scope
    ])
    
    try:
        result = subprocess.run(rg_cmd, capture_output=True, text=True)
        
        # Process ripgrep JSON output
        import json
        current_file = None
        current_file_refs = []
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            try:
                data = json.loads(line)
                msg_type = data.get('type')
                
                if msg_type == 'begin':
                    # New file
                    if current_file and current_file_refs:
                        references.append({
                            'file': current_file,
                            'refs': current_file_refs
                        })
                    current_file = data['data']['path']['text']
                    current_file_refs = []
                    
                elif msg_type == 'match':
                    # Found a match
                    match_data = data['data']
                    line_num = match_data['line_number']
                    line_text = match_data['lines']['text'].rstrip()
                    
                    # Get the actual matched substring
                    submatches = match_data.get('submatches', [])
                    match_info = None
                    if submatches:
                        submatch = submatches[0]
                        match_info = {
                            'start': submatch['start'],
                            'end': submatch['end'],
                            'text': submatch['match']['text']
                        }
                    
                    current_file_refs.append({
                        'line_num': line_num,
                        'line': line_text,
                        'context': [],  # We'll handle context differently with ripgrep
                        'match_info': match_info
                    })
                    
                elif msg_type == 'context':
                    # Context line
                    if current_file_refs:
                        context_data = data['data']
                        current_file_refs[-1]['context'].append({
                            'line_num': context_data['line_number'],
                            'text': context_data['lines']['text'].rstrip(),
                            'is_match': False
                        })
                        
            except json.JSONDecodeError:
                # Skip invalid JSON lines
                continue
        
        # Don't forget the last file
        if current_file and current_file_refs:
            references.append({
                'file': current_file,
                'refs': current_file_refs
            })
            
    except Exception as e:
        print(f"Error running ripgrep: {e}")
        return []
    
    return references

def print_references(references, target_name, ref_type, show_ast_context=False):
    """Print found references in a readable format."""
    if not references:
        print(f"No references found for {ref_type} '{target_name}'")
        return
    
    # Initialize AST context finder if needed
    context_finder = None
    if show_ast_context and HAS_AST_CONTEXT:
        context_finder = ASTContextFinder()
    
    total_refs = sum(len(file_info['refs']) for file_info in references)
    print(f"Found {total_refs} reference(s) to {ref_type} '{target_name}' in {len(references)} file(s)")
    print("=" * 80)
    
    for file_info in references:
        print(f"\nFile: {file_info['file']}")
        print(f"References: {len(file_info['refs'])}")
        print("-" * 80)
        
        for ref in file_info['refs']:
            # Get AST context if available
            context_str = ""
            if context_finder:
                context = context_finder._format_context_parts(
                    context_finder.get_context_for_line(file_info['file'], ref['line_num'])
                )
                if context:
                    context_str = f" [{context}]"
            
            print(f"\nLine {ref['line_num']}{context_str}:")
            
            # Print the match line
            print(f">>> {ref['line_num']:4d}: {ref['line']}")
            
            # Print context if available
            for ctx_line in ref.get('context', []):
                print(f"    {ctx_line['line_num']:4d}: {ctx_line['text']}")

def analyze_usage_patterns(references, target_name, ignore_case=False):
    """Analyze and summarize how the target is used."""
    if not references:
        return
    
    print("\n" + "=" * 80)
    print("Usage Pattern Analysis:")
    print("-" * 80)
    
    # Count different usage patterns
    patterns = {
        'method_calls': 0,
        'field_access': 0,
        'instantiations': 0,
        'inheritance': 0,
        'type_usage': 0,
        'string_refs': 0,
        'other': 0
    }
    
    escaped_target = re.escape(target_name)

    for file_info in references:
        for ref in file_info['refs']:
            line = ref['line']
            cmp_line = line.lower() if ignore_case else line
            cmp_target = target_name.lower() if ignore_case else target_name

            if f'.{cmp_target}(' in cmp_line:
                patterns['method_calls'] += 1
            elif f'new {cmp_target}' in cmp_line:
                patterns['instantiations'] += 1
            elif f'extends {cmp_target}' in cmp_line or f'implements {cmp_target}' in cmp_line:
                patterns['inheritance'] += 1
            elif f'.{cmp_target}' in cmp_line and '(' not in cmp_line:
                patterns['field_access'] += 1
            elif f'"{cmp_target}"' in cmp_line:
                patterns['string_refs'] += 1
            elif re.search(fr'{escaped_target}\s+\w+', cmp_line,
                           flags=re.IGNORECASE if ignore_case else 0):
                patterns['type_usage'] += 1
            else:
                patterns['other'] += 1
    
    # Print summary
    for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
        if count > 0:
            pattern_name = pattern.replace('_', ' ').title()
            print(f"  {pattern_name}: {count}")

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Find references to methods, fields, or classes using ripgrep')
    else:
        parser = argparse.ArgumentParser(description='Find references to methods, fields, or classes using ripgrep')
    # Add additional arguments not provided by standard parser
    if not HAS_STANDARD_PARSER:
        parser.add_argument('target', help='Name of method, field, or class to find')
    parser.add_argument('--summary-only', action='store_true',
                       help='Show only summary without detailed references')
    parser.add_argument('-C', '--context', type=int, default=3, metavar='N',
                       help='Show N lines of context around matches (default: 3)')
    parser.add_argument('--ast-context', action='store_true', default=True,
                        help='Show AST context (class/method) for each reference (default: enabled)')
    parser.add_argument('--no-ast-context', action='store_true',
                        help='Disable AST context display')
    
    # Add ignore-case argument (not provided by standard analyze parser)
    parser.add_argument('-i', '--ignore-case', action='store_true',
                       help='Case-insensitive search')
    
    args = parser.parse_args()
    
    # Load configuration and apply to args
    config = load_config()
    apply_config_to_args('find_references_rg', args, parser, config)
    
    # Run preflight checks - basic ripgrep availability check
    from preflight_checks import PreflightChecker
    ripgrep_check = PreflightChecker.check_ripgrep_installed()
    if not ripgrep_check[0]:
        print(f"Error: {ripgrep_check[1]}", file=sys.stderr)
        sys.exit(1)
    
    # Handle AST context flag logic
    if args.no_ast_context:
        args.ast_context = False
    
    # Ensure required attributes exist with defaults
    if not hasattr(args, 'type'):
        args.type = 'auto'
    if not hasattr(args, 'scope'):
        args.scope = '.'
    if not hasattr(args, 'ignore_case'):
        args.ignore_case = False
    
    # Map standard parser types to our internal types
    type_mapping = {
        'function': 'method',  # Map function to method
        'variable': 'field'    # Map variable to field
    }
    ref_type = type_mapping.get(args.type, args.type)
    
    references = find_references(args.target, args.scope, ref_type,
                                 args.context, args.ignore_case)
    
    if not args.summary_only:
        print_references(references, args.target, ref_type, args.ast_context)
    
    analyze_usage_patterns(references, args.target, args.ignore_case)

if __name__ == "__main__":
    main()