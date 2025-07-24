#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Extract code blocks between patterns from Java files.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
from pathlib import Path
import argparse
from java_parsing_utils import find_closing_brace

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
        @staticmethod
        def check_ripgrep_installed():
            return True, ""
        @staticmethod
        def check_regex_pattern(pattern):
            return True, ""

def find_block_with_braces(content, start_pattern, start_pos=0):
    """Find a code block starting with a pattern and track braces."""
    # Find the start pattern
    try:
        match = re.search(start_pattern, content[start_pos:], re.MULTILINE)
    except re.error as e:
        print(f"Invalid start pattern '{start_pattern}': {e}")
        return None
    if not match:
        return None
    
    pattern_start = start_pos + match.start()
    pattern_end = start_pos + match.end()
    
    # Find the opening brace
    brace_pos = content.find('{', pattern_end)
    if brace_pos == -1:
        return None
    
    # Use the proper brace counting utility
    end_pos = find_closing_brace(content, brace_pos)
    
    if end_pos != -1:
        return {
            'start': pattern_start,
            'end': end_pos,
            'content': content[pattern_start:end_pos],
            'pattern_match': match.group(0)
        }
    
    return None

def find_block_between_patterns(content, start_pattern, end_pattern, start_pos=0):
    """Find a code block between two patterns."""
    # Find the start pattern
    try:
        start_match = re.search(start_pattern, content[start_pos:], re.MULTILINE)
    except re.error as e:
        print(f"Invalid start pattern '{start_pattern}': {e}")
        return None

    if not start_match:
        return None
    
    pattern_start = start_pos + start_match.start()
    
    # Find the end pattern after the start
    try:
        end_match = re.search(end_pattern, content[pattern_start:], re.MULTILINE)
    except re.error as e:
        print(f"Invalid end pattern '{end_pattern}': {e}")
        return None

    if not end_match:
        return None
    
    pattern_end = pattern_start + end_match.end()
    
    return {
        'start': pattern_start,
        'end': pattern_end,
        'content': content[pattern_start:pattern_end],
        'start_match': start_match.group(0),
        'end_match': end_match.group(0)
    }

def extract_blocks(file_path, start_pattern, end_pattern=None, include_context=0, block_type="auto"):
    """Extract code blocks from a Java file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = []
    pos = 0
    
    while pos < len(content):
        if block_type == "auto":
            # Try to detect block type
            if any(keyword in start_pattern for keyword in ['if', 'try', 'while', 'for', 'switch', 'synchronized']):
                block_type = "braces"
            elif end_pattern:
                block_type = "patterns"
            else:
                block_type = "braces"
        
        if block_type == "braces" or end_pattern is None:
            block = find_block_with_braces(content, start_pattern, pos)
        else:
            block = find_block_between_patterns(content, start_pattern, end_pattern, pos)
        
        if not block:
            break
        
        # Get line numbers
        lines_before_start = content[:block['start']].count('\n')
        lines_before_end = content[:block['end']].count('\n')
        
        block_info = {
            'start_line': lines_before_start + 1,
            'end_line': lines_before_end + 1,
            'content': block['content'],
            'lines': block['content'].count('\n') + 1
        }
        
        # Add context if requested
        if include_context > 0:
            lines = content.splitlines()
            context_start = max(0, lines_before_start - include_context)
            context_end = min(len(lines), lines_before_end + include_context + 1)
            
            context_lines = []
            for i in range(context_start, context_end):
                is_block_line = lines_before_start <= i <= lines_before_end
                context_lines.append({
                    'line_num': i + 1,
                    'text': lines[i],
                    'is_block': is_block_line
                })
            
            block_info['context'] = context_lines
        
        blocks.append(block_info)
        pos = block['end']
    
    return blocks

def extract_specific_blocks(file_path):
    """Extract common block types from a Java file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    block_types = {
        'try_catch': [],
        'if_blocks': [],
        'for_loops': [],
        'while_loops': [],
        'switch_blocks': [],
        'synchronized_blocks': [],
        'method_blocks': []
    }
    
    # Extract try-catch blocks
    for match in re.finditer(r'try\s*\{', content):
        block = find_block_with_braces(content, r'try\s*\{', match.start())
        if block:
            # Also find associated catch/finally blocks
            pos = block['end']
            full_block = block['content']
            
            while True:
                catch_match = re.match(r'\s*(catch|finally)\s*(?:\([^)]*\))?\s*\{', content[pos:])
                if catch_match:
                    catch_block = find_block_with_braces(content, catch_match.group(0), pos)
                    if catch_block:
                        full_block += content[pos:catch_block['end']]
                        pos = catch_block['end']
                    else:
                        break
                else:
                    break
            
            lines_before = content[:match.start()].count('\n')
            block_types['try_catch'].append({
                'start_line': lines_before + 1,
                'content': full_block,
                'lines': full_block.count('\n') + 1
            })
    
    # Extract if blocks
    for match in re.finditer(r'if\s*\([^)]+\)\s*\{', content):
        block = find_block_with_braces(content, r'if\s*\([^)]+\)\s*\{', match.start())
        if block:
            lines_before = content[:block['start']].count('\n')
            block_types['if_blocks'].append({
                'start_line': lines_before + 1,
                'content': block['content'],
                'lines': block['content'].count('\n') + 1,
                'condition': re.search(r'if\s*\(([^)]+)\)', block['content']).group(1)
            })
    
    # Extract for loops
    for match in re.finditer(r'for\s*\([^)]+\)\s*\{', content):
        block = find_block_with_braces(content, r'for\s*\([^)]+\)\s*\{', match.start())
        if block:
            lines_before = content[:block['start']].count('\n')
            block_types['for_loops'].append({
                'start_line': lines_before + 1,
                'content': block['content'],
                'lines': block['content'].count('\n') + 1
            })
    
    return block_types

def print_blocks(blocks, show_content=True):
    """Print extracted blocks."""
    if not blocks:
        print("No blocks found matching the pattern")
        return
    
    print(f"Found {len(blocks)} block(s)")
    print("=" * 80)
    
    for i, block in enumerate(blocks, 1):
        print(f"\nBlock {i}:")
        print(f"Lines: {block['start_line']}-{block['end_line']} ({block['lines']} lines)")
        
        if 'context' in block:
            print("\nWith context:")
            print("-" * 60)
            for ctx_line in block['context']:
                if ctx_line['is_block']:
                    print(f">>> {ctx_line['line_num']:4d}: {ctx_line['text']}")
                else:
                    print(f"    {ctx_line['line_num']:4d}: {ctx_line['text']}")
        elif show_content:
            print("\nContent:")
            print("-" * 60)
            # Show first and last few lines if block is large
            lines = block['content'].splitlines()
            if len(lines) > 20:
                for line in lines[:8]:
                    print(line)
                print(f"\n... ({len(lines) - 16} lines omitted) ...\n")
                for line in lines[-8:]:
                    print(line)
            else:
                print(block['content'])

def print_block_summary(block_types):
    """Print summary of different block types."""
    print("Code Block Summary")
    print("=" * 80)
    
    total_blocks = sum(len(blocks) for blocks in block_types.values())
    print(f"Total blocks found: {total_blocks}\n")
    
    for block_type, blocks in block_types.items():
        if blocks:
            print(f"{block_type.replace('_', ' ').title()}: {len(blocks)}")
            
            # Show largest blocks
            sorted_blocks = sorted(blocks, key=lambda x: x['lines'], reverse=True)
            print(f"  Largest: {sorted_blocks[0]['lines']} lines at line {sorted_blocks[0]['start_line']}")
            
            if len(blocks) > 1:
                print(f"  Average size: {sum(b['lines'] for b in blocks) / len(blocks):.1f} lines")
            
            # Special info for certain types
            if block_type == 'if_blocks' and 'condition' in blocks[0]:
                # Show most common conditions
                conditions = {}
                for block in blocks:
                    cond = block.get('condition', '').strip()
                    # Normalize common patterns
                    if 'null' in cond:
                        cond = 'null check'
                    elif '>' in cond or '<' in cond:
                        cond = 'comparison'
                    elif '&&' in cond or '||' in cond:
                        cond = 'compound condition'
                    
                    conditions[cond] = conditions.get(cond, 0) + 1
                
                if conditions:
                    most_common = sorted(conditions.items(), key=lambda x: x[1], reverse=True)[0]
                    print(f"  Most common type: {most_common[0]} ({most_common[1]} times)")
            
            print()

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Extract code blocks from Java files')
    else:
        parser = argparse.ArgumentParser(description='Extract code blocks from Java files')
    parser.add_argument('file', help='Java file to analyze')
    parser.add_argument('--start-pattern', help='Pattern to start block extraction')
    parser.add_argument('--end-pattern', help='Pattern to end block extraction')
    parser.add_argument('--include-context', type=int, default=0,
                       help='Number of context lines to include')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze all common block types')
    parser.add_argument('--no-content', action='store_true',
                       help='Show only block locations, not content')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    if args.analyze:
        # Analyze all block types
        block_types = extract_specific_blocks(args.file)
        print_block_summary(block_types)
    elif args.start_pattern:
        # Extract specific blocks
        blocks = extract_blocks(args.file, args.start_pattern, args.end_pattern,
                              args.include_context, args.type)
        print_blocks(blocks, show_content=not args.no_content)
    else:
        print("Error: Either --start-pattern or --analyze must be specified")
        sys.exit(1)

if __name__ == "__main__":
    main()