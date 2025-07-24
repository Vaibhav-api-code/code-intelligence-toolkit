#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
find_text v2 - Unified text and file search tool with standardized interface.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import fnmatch
import re

# Import standard parser
try:
    from standard_arg_parser import create_standard_parser, parse_standard_args
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False

# Import configuration
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass


def search_in_files(pattern: str, args) -> List[Dict]:
    """Search for pattern in file contents using ripgrep."""
    cmd = ['rg', '--json']
    
    # Add pattern
    if args.type == 'regex':
        cmd.append(pattern)
    elif args.type == 'word':
        cmd.extend(['-w', pattern])
    else:
        cmd.extend(['-F', pattern])  # Fixed string
    
    # Add case sensitivity
    if args.ignore_case:
        cmd.append('-i')
    
    # Add context
    if args.context:
        cmd.extend(['-C', str(args.context)])
    elif args.before_context:
        cmd.extend(['-B', str(args.before_context)])
    elif args.after_context:
        cmd.extend(['-A', str(args.after_context)])
    
    # Add file type filter
    if args.glob:
        cmd.extend(['-g', args.glob])
    
    # Add exclude pattern
    if hasattr(args, 'exclude') and args.exclude:
        cmd.extend(['--glob', f'!{args.exclude}'])
    
    # Add scope
    if args.file:
        cmd.append(args.file)
    else:
        cmd.append(args.scope)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        matches = []
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data['type'] == 'match':
                    match_info = {
                        'file': data['data']['path']['text'],
                        'line': data['data']['line_number'],
                        'text': data['data']['lines']['text'].rstrip(),
                        'matches': []
                    }
                    # Extract match positions
                    for submatch in data['data']['submatches']:
                        match_info['matches'].append({
                            'start': submatch['start'],
                            'end': submatch['end'],
                            'text': submatch['match']['text']
                        })
                    matches.append(match_info)
            except:
                continue
        
        return matches
    except Exception as e:
        print(f"Error running ripgrep: {e}", file=sys.stderr)
        return []


def find_files_by_pattern(pattern: str, args) -> List[Dict]:
    """Find files by name pattern."""
    results = []
    base_path = Path(args.scope)
    
    # Determine if pattern is regex
    is_regex = args.type == 'regex'
    regex_pattern = re.compile(pattern) if is_regex else None
    
    # Walk directory
    for root, dirs, files in os.walk(base_path):
        # Check depth limit
        if hasattr(args, 'max_depth') and args.max_depth:
            depth = len(Path(root).relative_to(base_path).parts)
            if depth > args.max_depth:
                dirs.clear()  # Don't recurse deeper
                continue
        
        # Filter directories if not recursive
        if not args.recursive:
            dirs.clear()
        
        for filename in files:
            # Match pattern
            if is_regex:
                if not regex_pattern.search(filename):
                    continue
            else:
                if not fnmatch.fnmatch(filename, pattern):
                    continue
            
            # Apply glob filter if specified
            if args.glob and not fnmatch.fnmatch(filename, args.glob):
                continue
            
            file_path = Path(root) / filename
            try:
                stat = file_path.stat()
                results.append({
                    'path': str(file_path),
                    'name': filename,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
            except:
                continue
    
    return results


def format_output(results: List[Dict], args, search_type: str) -> None:
    """Format and print results."""
    if args.json:
        print(json.dumps(results, indent=2))
        return
    
    if search_type == 'content':
        # Format content search results
        if not results:
            if not args.quiet:
                print("No matches found")
            return
        
        current_file = None
        for match in results:
            # Print file header
            if match['file'] != current_file:
                current_file = match['file']
                print(f"\n{match['file']}:")
            
            # Print line with highlighting
            line_text = match['text']
            if match['matches'] and sys.stdout.isatty():
                # Highlight matches
                offset = 0
                highlighted = ""
                for m in sorted(match['matches'], key=lambda x: x['start']):
                    highlighted += line_text[offset:m['start']]
                    highlighted += f"\033[1;31m{line_text[m['start']:m['end']]}\033[0m"
                    offset = m['end']
                highlighted += line_text[offset:]
                print(f"{match['line']:6}: {highlighted}")
            else:
                print(f"{match['line']:6}: {line_text}")
    
    else:
        # Format file search results
        if not results:
            if not args.quiet:
                print("No files found")
            return
        
        for file_info in sorted(results, key=lambda x: x['path']):
            print(file_info['path'])


def main():
    # Create parser based on availability of standard parser
    if HAS_STANDARD_PARSER:
        parser = create_standard_parser(
            'search',
            'find_text v2 - Search for text in files or find files by name',
            epilog='''
EXAMPLES:
  # Search in files (default when pattern contains text)
  %(prog)s "TODO"                    # Search in all files
  %(prog)s "TODO" --file main.py     # Search in specific file
  %(prog)s "TODO" --scope src/       # Search in directory
  %(prog)s "TODO" -g "*.java" -C 3   # Java files with context
  
  # Find files by name (detected by pattern)
  %(prog)s "*.test.js"               # Find test files
  %(prog)s "^test_.*\\.py$" --type regex  # Regex pattern
  
  # Advanced usage
  %(prog)s "error|warning" --type regex -i  # Case-insensitive regex
  %(prog)s "TODO" --exclude "*.min.js"      # Exclude minified files
'''
        )
    else:
        # Fallback parser
        parser = argparse.ArgumentParser(
            description='find_text v2 - Search for text in files or find files by name'
        )
        parser.add_argument('pattern', help='Search pattern')
        parser.add_argument('--file', help='Search in specific file')
        parser.add_argument('--scope', default='.', help='Directory scope')
        parser.add_argument('--type', choices=['text', 'regex', 'word'], default='text')
        parser.add_argument('-i', '--ignore-case', action='store_true')
        parser.add_argument('-g', '--glob', help='File pattern')
        parser.add_argument('-C', '--context', type=int)
        parser.add_argument('-r', '--recursive', action='store_true', default=True)
        parser.add_argument('--json', action='store_true')
        parser.add_argument('-q', '--quiet', action='store_true')
        parser.add_argument('-v', '--verbose', action='store_true')
    
    # Additional arguments not in standard parser
    if not HAS_STANDARD_PARSER:
        parser.add_argument('-B', '--before-context', type=int)
        parser.add_argument('-A', '--after-context', type=int)
        parser.add_argument('--exclude', help='Exclude pattern')
    
    # Parse arguments
    if HAS_STANDARD_PARSER:
        args = parse_standard_args(parser, 'search')
    else:
        args = parser.parse_args()
    
    # Apply configuration
    apply_config_to_args('find_text', args, parser)
    
    # Determine search type based on pattern
    pattern = args.pattern
    search_type = 'content'  # Default
    
    # Simple heuristic: if pattern looks like a file pattern, search files
    if ('*' in pattern or '?' in pattern or 
        pattern.startswith('.') or 
        (args.type != 'regex' and '/' not in pattern and '.' in pattern and 
         pattern.split('.')[-1] in ['py', 'java', 'js', 'cpp', 'c', 'h', 'txt', 'log', 'json', 'xml'])):
        search_type = 'files'
    
    # Override if user explicitly wants file search
    if hasattr(args, 'files_only') and args.files_only:
        search_type = 'files'
    
    if args.verbose:
        print(f"Search type: {search_type}", file=sys.stderr)
        print(f"Pattern: {pattern}", file=sys.stderr)
        print(f"Scope: {args.file or args.scope}", file=sys.stderr)
    
    # Perform search
    try:
        if search_type == 'content':
            results = search_in_files(pattern, args)
        else:
            results = find_files_by_pattern(pattern, args)
        
        # Format output
        format_output(results, args, search_type)
        
    except KeyboardInterrupt:
        print("\nSearch interrupted", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()