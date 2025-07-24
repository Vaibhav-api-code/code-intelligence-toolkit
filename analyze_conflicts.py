#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Analyze argument conflicts between standard_arg_parser and individual tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict

def analyze_tool_arguments(file_path):
    """Extract argument definitions from a Python tool."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find add_argument calls
        arguments = []
        for match in re.finditer(r'parser\.add_argument\((.*?)\)', content, re.DOTALL):
            arg_def = match.group(1)
            
            # Extract flag names
            flags = []
            for flag_match in re.finditer(r'[\'"](-{1,2}[^\'",\s]+)[\'"]', arg_def):
                flags.append(flag_match.group(1))
            
            if flags:
                arguments.append({
                    'flags': flags,
                    'definition': arg_def.strip()[:100] + ('...' if len(arg_def) > 100 else '')
                })
        
        return arguments
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return []

def get_standard_parser_arguments():
    """Get all arguments defined in standard_arg_parser."""
    standard_args = {
        'search': [
            'pattern', '--file', '--path', '--scope', '--type', '-i', '--ignore-case',
            '-w', '--whole-word', '--include', '--glob', '-g', '--exclude',
            '-A', '--after-context', '-B', '--before-context', '-C', '--context',
            '-v', '--verbose', '-q', '--quiet', '--json', '-r', '--recursive'
        ],
        'analyze': [
            'target', '--file', '--scope', '--type', '--max-depth', '--show-callers',
            '--show-callees', '-v', '--verbose', '-q', '--quiet', '--json'
        ],
        'refactor': [
            'operation', 'old_name', 'new_name', 'old_text', 'new_text',
            '--file', '--scope', '--type', '--dry-run', '--regex',
            '-v', '--verbose', '-q', '--quiet'
        ],
        'navigate': [
            'file', '--to', '--line', '-l', '--method', '-m', '--class', '-c',
            '--context', '-C', '--highlight', '-v', '--verbose', '-q', '--quiet'
        ],
        'directory': [
            'path', '-l', '--long', '-a', '--all', '--sort', '--include',
            '--glob', '-g', '--exclude', '--type', '-v', '--verbose',
            '-q', '--quiet', '--json', '-r', '--recursive', '--max-depth'
        ]
    }
    return standard_args

def main():
    """Analyze all conflicts."""
    print("🔍 Analyzing argument conflicts between standard_arg_parser and tools")
    print("=" * 80)
    
    # Get standard arguments
    standard_args = get_standard_parser_arguments()
    all_standard_flags = set()
    for tool_type, flags in standard_args.items():
        all_standard_flags.update(flags)
    
    print(f"Standard parser defines {len(all_standard_flags)} unique flags")
    
    # Analyze individual tools
    conflicts = defaultdict(list)
    tool_args = {}
    
    python_files = list(Path('.').glob('*.py'))
    for file_path in python_files:
        if file_path.name in ['standard_arg_parser.py', 'analyze_conflicts.py']:
            continue
            
        arguments = analyze_tool_arguments(file_path)
        if arguments:
            tool_args[file_path.name] = arguments
            
            # Check for conflicts
            for arg in arguments:
                for flag in arg['flags']:
                    if flag in all_standard_flags:
                        conflicts[flag].append({
                            'file': file_path.name,
                            'definition': arg['definition']
                        })
    
    # Report conflicts
    print(f"\n🚨 Found conflicts in {len(conflicts)} argument flags:")
    print("-" * 80)
    
    conflict_summary = {}
    for flag, tools in conflicts.items():
        print(f"\n{flag}:")
        conflict_summary[flag] = []
        for tool in tools:
            print(f"  📄 {tool['file']}: {tool['definition']}")
            conflict_summary[flag].append(tool['file'])
    
    # Most problematic flags
    print(f"\n📊 Most problematic flags:")
    print("-" * 40)
    for flag, tools in sorted(conflicts.items(), key=lambda x: len(x[1]), reverse=True):
        if len(tools) > 1:
            print(f"  {flag}: {len(tools)} tools ({', '.join([t['file'] for t in tools[:3]])})")
    
    # Tool-specific unique arguments
    print(f"\n🔧 Tool-specific arguments (not in standard parser):")
    print("-" * 60)
    
    unique_args = defaultdict(list)
    for tool_name, arguments in tool_args.items():
        for arg in arguments:
            for flag in arg['flags']:
                if flag not in all_standard_flags:
                    unique_args[flag].append(tool_name)
    
    # Show unique args that appear in multiple tools (potential new standard args)
    potential_standard = {}
    for flag, tools in unique_args.items():
        if len(tools) > 2:  # Used by 3+ tools
            potential_standard[flag] = tools
            print(f"  {flag}: {len(tools)} tools ({', '.join(tools[:3])})")
    
    # Save detailed report
    with open('ARGUMENT_CONFLICT_REPORT.md', 'w') as f:
        f.write("# Argument Conflict Analysis Report\n\n")
        f.write(f"**Date**: {os.popen('date').read().strip()}\n\n")
        
        f.write("## Summary\n")
        f.write(f"- Total conflicts: {len(conflicts)} flags\n")
        f.write(f"- Total tools analyzed: {len(tool_args)}\n")
        f.write(f"- Standard flags: {len(all_standard_flags)}\n\n")
        
        f.write("## Conflicts by Flag\n")
        for flag, tools in sorted(conflicts.items()):
            f.write(f"\n### `{flag}`\n")
            f.write(f"**Conflicts in {len(tools)} tools:**\n")
            for tool in tools:
                f.write(f"- `{tool['file']}`\n")
        
        f.write("\n## Potential New Standard Arguments\n")
        f.write("Arguments used by multiple tools that could be standardized:\n\n")
        for flag, tools in sorted(potential_standard.items(), key=lambda x: len(x[1]), reverse=True):
            f.write(f"- `{flag}`: {len(tools)} tools\n")
    
    print(f"\n📝 Detailed report saved to: ARGUMENT_CONFLICT_REPORT.md")
    
    return len(conflicts)

if __name__ == '__main__':
    conflicts = main()
    sys.exit(0 if conflicts == 0 else 1)