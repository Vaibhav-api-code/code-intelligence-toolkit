#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
find_text v4 - Enhanced text search with AST context and method extraction support.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
import fnmatch
import re

# Import AST context finder

# Import standard argument parser
try:
    from enhanced_standard_arg_parser import create_search_parser as create_parser
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

try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

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

# Import method extraction functionality
try:
    from extract_methods_v2 import extract_method
    HAS_EXTRACT_METHODS = True
except ImportError:
    HAS_EXTRACT_METHODS = False

def search_in_files(pattern: str, args) -> List[Dict]:
    """Search for pattern in file contents using ripgrep."""
    cmd = ['rg', '--json']    # Add pattern
    if args.type == 'regex':
        cmd.append(pattern)
    elif args.type == 'word':
        cmd.extend(['-w', pattern])
    else:
        cmd.extend(['-F', pattern])  # Fixed string
    
    # Add case sensitivity
    if args.ignore_case:
        cmd.append('-i')    # Add context
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
            except json.JSONDecodeError:
                # Ignore lines that are not valid JSON (e.g., from rg summary)
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
            except (OSError, PermissionError):
                # Ignore files we can't access
                continue
    
    return results

def extract_method_from_context(file_path: str, ast_context: str, max_lines: Optional[int] = None) -> Optional[Dict]:
    """Extract method from file based on AST context."""
    if not HAS_EXTRACT_METHODS:
        return None
    
    # Parse the AST context to get method name
    # Context format: "ClassName(start-end) → methodName(start-end)"
    method_match = re.search(r'→\s*(\w+)\s*\(', ast_context)
    if not method_match:
        # Try simpler format
        method_match = re.search(r'(\w+)\s*\(', ast_context)
    
    if not method_match:
        return None
    
    method_name = method_match.group(1)
    
    try:
        # Extract the method
        results = extract_method(file_path, method_name, include_javadoc=True)
        
        if isinstance(results, dict) and 'error' in results:
            return None
        
        if not results:
            return None
        
        # Get the first matching method
        method_info = results[0]
        
        # Check line count if max_lines specified
        if max_lines and method_info['line_count'] > max_lines:
            return {
                'skipped': True,
                'reason': f"Method '{method_name}' has {method_info['line_count']} lines (exceeds {max_lines} line limit)",
                'line_count': method_info['line_count']
            }
        
        return method_info
        
    except Exception as e:
        print(f"Error extracting method: {e}", file=sys.stderr)
        return None

def format_output(results: List[Dict], args, search_type: str) -> None:
    """Format and print results with optional AST context and method extraction."""
    if args.json:
        print(json.dumps(results, indent=2))
        return
    
    # Initialize AST context finder if requested
    context_finder = None
    if hasattr(args, 'ast_context') and args.ast_context and HAS_AST_CONTEXT:
        context_finder = ASTContextFinder()
    
    # Track extracted methods to avoid duplicates
    extracted_methods: Set[Tuple[str, str]] = set()
    
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
            
            # Get AST context if available
            ast_context = None
            if context_finder:
                ast_context = context_finder._format_context_parts(
                    context_finder.get_context_for_line(match['file'], match['line'])
                )
                if ast_context:
                    print(f"       AST context of line {match['line']} - [{ast_context}]")
            
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
            
            # Extract method if requested
            should_extract = args.extract_method or args.extract_method_alllines
            if should_extract and ast_context and HAS_EXTRACT_METHODS:
                # Determine if we've already extracted this method
                method_key = (match['file'], ast_context)
                if method_key not in extracted_methods:
                    extracted_methods.add(method_key)
                    
                    # Determine max lines
                    max_lines = None if args.extract_method_alllines else 500
                    
                    # Extract the method
                    method_info = extract_method_from_context(match['file'], ast_context, max_lines)
                    
                    if method_info:
                        if method_info.get('skipped'):
                            print(f"\n    [Method extraction skipped: {method_info['reason']}]")
                            if args.verbose:
                                print(f"    [Use --extract-method-alllines to extract methods over 500 lines]")
                        else:
                            print(f"\n    ╔══ Extracted Method: {method_info['signature']} ══╗")
                            print(f"    ║ Lines {method_info['start_line']}-{method_info['end_line']} ({method_info['line_count']} lines)")
                            print("    ╚" + "═" * (len(method_info['signature']) + 25) + "╝")
                            print()
                            
                            # Print method content with indentation
                            for line in method_info['content'].split('\n'):
                                print(f"    {line}")
                            print()
    
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
            'find_text v4 - Search with AST context and method extraction',
            epilog='''
EXAMPLES:
  # Search with method extraction  
  # Search with AST context  
  # Search in files (default when pattern contains text)  
  # Find files by name (detected by pattern)  
  # Advanced usage
METHOD EXTRACTION:
  --extract-method extracts methods containing matches (up to 500 lines)
  --extract-method-alllines extracts methods regardless of size
  
  Extraction requires AST context to identify the containing method.
  Works best with Java and Python files.

AST CONTEXT:
  When --ast-context is enabled, shows hierarchical location:
  Line 42: [ClassName(10-100) → methodName(40-50)]: code here
'''
        )
    else:
        # Fallback parser
        parser = argparse.ArgumentParser(description='find_text v4 - Search with AST context and method extraction')
        parser.add_argument('pattern', help='Search pattern')
    
    # Add AST context options
    parser.add_argument('--ast-context', action='store_true',
                      help='Show AST context (class/method) for matches')
    parser.add_argument('--no-ast-context', action='store_true',
                      help='Disable AST context even if enabled in config')
    
    # Add method extraction options
    parser.add_argument('--extract-method', action='store_true',
                      help='Extract containing methods (up to 500 lines)')
    parser.add_argument('--extract-method-alllines', action='store_true',
                      help='Extract containing methods regardless of size')
    
    # Parse arguments
    if HAS_STANDARD_PARSER:
        args = parse_standard_args(parser, 'search')
    else:
        args = parser.parse_args()
    
    # Apply configuration
    apply_config_to_args('find_text', args, parser)
    
    # Handle --no-ast-context flag (overrides config)
    if args.no_ast_context:
        args.ast_context = False
    
    # Method extraction requires AST context
    if (args.extract_method or args.extract_method_alllines):
        if not HAS_AST_CONTEXT:
            print("Error: Method extraction requires ast_context_finder module", file=sys.stderr)
            sys.exit(1)
        if not HAS_EXTRACT_METHODS:
            print("Error: Method extraction requires extract_methods_v2 module", file=sys.stderr)
            sys.exit(1)
        # Enable AST context for method extraction
        args.ast_context = True
    
    # Check if AST context is available
    if args.ast_context and not HAS_AST_CONTEXT:
        print("Warning: AST context requested but ast_context_finder module not found", 
              file=sys.stderr)
        print("Continuing without AST context...", file=sys.stderr)
        args.ast_context = False
    
    # Determine search type based on pattern
    pattern = args.pattern
    search_type = 'content'  # Default
    
    # Simple heuristic: if pattern looks like a file pattern, search files
    # But not if we're explicitly in regex mode
    if args.type != 'regex' and ('*' in pattern or '?' in pattern or 
        pattern.startswith('.') or 
        ('/' not in pattern and '.' in pattern and 
         pattern.split('.')[-1] in ['py', 'java', 'js', 'cpp', 'c', 'h', 'txt', 'log', 'json', 'xml'])):
        search_type = 'files'
    
    # Override if user explicitly wants file search
    if hasattr(args, 'files_only') and args.files_only:
        search_type = 'files'
    
    if args.verbose:
        print(f"Search type: {search_type}", file=sys.stderr)
        print(f"Pattern: {pattern}", file=sys.stderr)
        print(f"Scope: {args.file or args.scope}", file=sys.stderr)
        if args.no_ast_context:
            print(f"AST context: explicitly disabled", file=sys.stderr)
        elif args.ast_context:
            print(f"AST context: enabled", file=sys.stderr)
        if args.extract_method:
            print(f"Method extraction: enabled (max 500 lines)", file=sys.stderr)
        elif args.extract_method_alllines:
            print(f"Method extraction: enabled (all lines)", file=sys.stderr)
    
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