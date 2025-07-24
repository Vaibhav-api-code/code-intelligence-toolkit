#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Find all references to a method, field, or class in the codebase.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-19
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
import subprocess
from pathlib import Path
import argparse

# Import configuration support with fallback
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass
argparse

def find_references(target_name, scope="src/", ref_type="auto", context_lines=3,
                    ignore_case=False):
    """Find all references to a method, field, or class.

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
            fr'\\.{escaped}\\s*\\(',      # Instance method: obj.method(
            fr'\\b{escaped}\\s*\\(',      # Direct call: method(
            fr'::{escaped}\\b',           # Method reference: ::method
            fr'"{escaped}"',              # String reference (reflection)
        ]
    elif ref_type == "field":
        patterns = [
            fr'\\.{escaped}\\b',          # Instance field: obj.field
            fr'\\b{escaped}\\s*=',        # Assignment: field =
            fr'\\b{escaped}\\s*\\.',      # Field access: field.
            fr'\\b{escaped}\\s*\\[',      # Array access: field[
            fr'"{escaped}"',              # String reference
        ]
    elif ref_type == "class":
        patterns = [
            fr'\\bnew\\s+{escaped}\\s*\\(',     # Instantiation: new Class(
            fr'\\bnew\\s+{escaped}\\s*\\[',     # Array creation: new Class[
            fr'\\b{escaped}\\.class\\b',        # Class literal: Class.class
            fr'\\b{escaped}\\s+\\w+\\s*[=;]',   # Variable declaration: Class var
            fr'\\bextends\\s+{escaped}\\b',     # Inheritance: extends Class
            fr'\\bimplements\\s+{escaped}\\b',  # Implementation: implements Class
            fr'\\b{escaped}<',                  # Generic usage: Class<
            fr'\\({escaped}\\)',                # Cast: (Class)
            fr'@{escaped}\\b',                  # Annotation: @Class
        ]
    
    # Find files containing references
    all_files = set()
    grep_flags = ['-r', '-l', '-P']
    if ignore_case:
        grep_flags.append('-i')

    for pattern in patterns:
        cmd = ['grep', *grep_flags, pattern, scope, '--include=*.java']
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                all_files.update(f for f in files if f)
        except Exception as e:
            print(f"Error searching with pattern {pattern}: {e}")
    
    # For each file, find exact locations with context
    for file_path in sorted(all_files):
        if not Path(file_path).exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        file_refs = []
        
        for i, line in enumerate(lines):
            line_matches = False
            match_info = None

            # Check each pattern
            for pattern in patterns:
                flags = re.IGNORECASE if ignore_case else 0
                if re.search(pattern, line, flags=flags):
                    line_matches = True
                    # Find the exact match position
                    match = re.search(pattern, line, flags=flags)
                    if match:
                        match_info = {
                            'start': match.start(),
                            'end': match.end(),
                            'text': match.group(0)
                        }
                    break
            
            if line_matches:
                # Get context
                start_line = max(0, i - context_lines)
                end_line = min(len(lines), i + context_lines + 1)
                
                context = []
                for j in range(start_line, end_line):
                    is_match_line = (j == i)
                    context.append({
                        'line_num': j + 1,
                        'text': lines[j].rstrip(),
                        'is_match': is_match_line
                    })
                
                file_refs.append({
                    'line_num': i + 1,
                    'line': line.rstrip(),
                    'context': context,
                    'match_info': match_info
                })
        
        if file_refs:
            references.append({
                'file': file_path,
                'refs': file_refs
            })
    
    return references

def print_references(references, target_name, ref_type):
    """Print found references in a readable format."""
    if not references:
        print(f"No references found for {ref_type} '{target_name}'")
        return
    
    total_refs = sum(len(file_info['refs']) for file_info in references)
    print(f"Found {total_refs} reference(s) to {ref_type} '{target_name}' in {len(references)} file(s)")
    print("=" * 80)
    
    for file_info in references:
        print(f"\nFile: {file_info['file']}")
        print(f"References: {len(file_info['refs'])}")
        print("-" * 80)
        
        for ref in file_info['refs']:
            print(f"\nLine {ref['line_num']}:")
            
            # Print context with highlighting
            for ctx_line in ref['context']:
                if ctx_line['is_match']:
                    print(f">>> {ctx_line['line_num']:4d}: {ctx_line['text']}")
                else:
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
    parser = argparse.ArgumentParser(description='Find references to methods, fields, or classes')
    parser.add_argument('target', help='Name of method, field, or class to find')
    parser.add_argument('--scope', default='.', help='Directory to search in (default: current directory)')
    parser.add_argument('--type', choices=['method', 'field', 'class', 'auto'], 
                       default='auto', help='Type of reference to find')
    parser.add_argument('--context', type=int, default=3,
                       help='Number of context lines to show (default: 3)')
    parser.add_argument('--summary-only', action='store_true',
                       help='Show only summary without detailed references')
    parser.add_argument('-i', '--ignore-case', action='store_true',
                        help='Case-insensitive search')
    
    args = parser.parse_args()
    
    references = find_references(args.target, args.scope, args.type,
                                 args.context, args.ignore_case)
    
    if not args.summary_only:
        print_references(references, args.target, args.type)
    
    analyze_usage_patterns(references, args.target, args.ignore_case)

if __name__ == "__main__":
    main()