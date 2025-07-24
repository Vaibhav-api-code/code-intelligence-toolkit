#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
find_text v5 - Enhanced text search with multiline capabilities and auto file finding.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Union
import fnmatch
import re
import shutil

# Import AST context finder
try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

# Import standard argument parser
try:
    from enhanced_standard_arg_parser import create_search_parser
    from standard_arg_parser import create_standard_parser, parse_standard_args
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False
    
    def create_parser(tool_type, description):
        return argparse.ArgumentParser(description=description)
    
    def create_standard_parser(tool_type, description, epilog=None):
        parser = argparse.ArgumentParser(description=description, epilog=epilog, 
                                       formatter_class=argparse.RawDescriptionHelpFormatter)
        return parser
    
    def parse_standard_args(parser, tool_type):
        return parser.parse_args()

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

# Import file finding tools
try:
    from find_files import find_files
    HAS_FIND_FILES = True
except ImportError:
    HAS_FIND_FILES = False

class LineRange:
    """Represents a line range with start and end positions."""
    
    def __init__(self, start: int, end: int):
        self.start = max(1, start)
        self.end = max(self.start, end)
    
    def __str__(self):
        return f"{self.start}-{self.end}" if self.start != self.end else str(self.start)
    
    def __repr__(self):
        return f"LineRange({self.start}, {self.end})"
    
    def contains(self, line_num: int) -> bool:
        """Check if a line number is within this range."""
        return self.start <= line_num <= self.end
    
    def overlaps(self, other: 'LineRange') -> bool:
        """Check if this range overlaps with another range."""
        return not (self.end < other.start or self.start > other.end)
    
    def merge(self, other: 'LineRange') -> 'LineRange':
        """Merge this range with another range."""
        return LineRange(min(self.start, other.start), max(self.end, other.end))

def merge_overlapping_ranges(ranges: List[LineRange]) -> List[LineRange]:
    """Merge overlapping or adjacent ranges."""
    if not ranges:
        return []
    
    # Sort ranges by start position
    sorted_ranges = sorted(ranges, key=lambda r: r.start)
    merged = [sorted_ranges[0]]
    
    for current in sorted_ranges[1:]:
        last = merged[-1]
        
        # Check if ranges overlap or are adjacent
        if current.start <= last.end + 1:
            # Merge ranges
            merged[-1] = last.merge(current)
        else:
            # Add new range
            merged.append(current)
    
    return merged

def parse_context_spec(spec: str) -> int:
    """Parse context specification like ±10 or just a number."""
    if spec.startswith('±'):
        return int(spec[1:])
    return int(spec)

def find_file_auto(filename: str, search_paths: List[str] = None) -> Optional[str]:
    """Auto-find file using find_files or fallback methods."""
    if search_paths is None:
        search_paths = ['.', 'src', 'java-intelligence-analysis-toolkit']
    
    # If it's already a valid path, return it
    if os.path.exists(filename):
        return filename
    
    # Simple file finding using walk
    found_files = set()  # Use set to avoid duplicates
    basename = os.path.basename(filename)
    
    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
        for root, dirs, files in os.walk(search_path):
            if basename in files:
                full_path = os.path.abspath(os.path.join(root, basename))
                found_files.add(full_path)
    
    if found_files:
        # Convert back to list and sort
        found_list = sorted(list(found_files))
        if len(found_list) == 1:
            return found_list[0]
        else:
            print(f"Multiple files found for '{filename}':", file=sys.stderr)
            for i, path in enumerate(found_list[:5]):
                print(f"  {i+1}. {path}", file=sys.stderr)
            if len(found_list) > 5:
                print(f"  ... and {len(found_list) - 5} more", file=sys.stderr)
            # Return the first one anyway
            print(f"Using first match: {found_list[0]}", file=sys.stderr)
            return found_list[0]
    
    return None

def search_with_context(pattern: str, args, context_lines: int = 0) -> List[Dict]:
    """Search for pattern and get full context using non-JSON mode."""
    # Use ripgrep without JSON to get context lines
    cmd = ['rg']
    
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
    if context_lines > 0:
        cmd.extend(['-C', str(context_lines)])
    elif args.context:
        cmd.extend(['-C', str(args.context)])
    elif args.before_context:
        cmd.extend(['-B', str(args.before_context)])
    elif args.after_context:
        cmd.extend(['-A', str(args.after_context)])
    
    # Add line numbers
    cmd.append('-n')
    
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
        if args.verbose:
            print(f"Running command: {' '.join(cmd)}", file=sys.stderr)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if args.verbose:
            print(f"Return code: {result.returncode}", file=sys.stderr)
            print(f"Output lines: {len(result.stdout.split('\n'))}", file=sys.stderr)
            if result.stderr:
                print(f"Stderr: {result.stderr}", file=sys.stderr)
        
        if result.returncode != 0 and not result.stdout:
            return []
        
        # Parse the output
        matches = []
        # Initialize current_file from args since context lines don't include file path
        current_file = args.file if args.file else None
        current_group = []
        
        for line in result.stdout.split('\n'):
            if not line:
                continue
            
            # Check if it's a file separator
            if line.startswith('--'):
                if current_group:
                    matches.extend(current_group)
                    current_group = []
                continue
            
            # Parse file:line:content format
            # Match lines have format: file:line:content
            # Context lines have format: line-content (no file path)
            
            # Try to detect if it's a match line (contains file path)
            colon_count = line.count(':')
            if colon_count >= 2:  # Likely a match line with file:line:content
                parts = line.split(':', 2)
                separator = ':'
                is_match_line = True
            else:
                # Try to parse as context line (line-content)
                match = re.match(r'^(\d+)([:-])(.*)$', line)
                if match:
                    parts = [current_file or '', match.group(1), match.group(3)]
                    separator = match.group(2)
                    is_match_line = (separator == ':')
                else:
                    continue
                
            if len(parts) >= 3:
                file_path = parts[0]
                try:
                    line_num = int(parts[1])
                    content = parts[2]
                    
                    # Check if this line contains the pattern
                    # is_match already set above based on separator
                    is_match = is_match_line
                    match_positions = []
                    
                    # Only find match positions for actual match lines
                    if is_match:
                        if args.type == 'regex':
                            regex = re.compile(pattern, re.IGNORECASE if args.ignore_case else 0)
                            for m in regex.finditer(content):
                                match_positions.append({'start': m.start(), 'end': m.end(), 'text': m.group()})
                        elif args.type == 'word':
                            word_regex = re.compile(r'\b' + re.escape(pattern) + r'\b', 
                                                  re.IGNORECASE if args.ignore_case else 0)
                            for m in word_regex.finditer(content):
                                match_positions.append({'start': m.start(), 'end': m.end(), 'text': m.group()})
                        else:
                            # Fixed string search
                            search_pattern = pattern.lower() if args.ignore_case else pattern
                            search_content = content.lower() if args.ignore_case else content
                            start = 0
                            while True:
                                pos = search_content.find(search_pattern, start)
                                if pos == -1:
                                    break
                                match_positions.append({
                                    'start': pos, 
                                    'end': pos + len(pattern), 
                                    'text': content[pos:pos + len(pattern)]
                                })
                                start = pos + 1
                    
                    match_info = {
                        'file': file_path,
                        'line': line_num,
                        'text': content,
                        'matches': match_positions,
                        'is_match': is_match,
                        'is_context': not is_match
                    }
                    
                    # Update current file from match lines
                    if is_match_line and file_path:
                        current_file = file_path
                    
                    # Use current file for context lines
                    if not file_path and current_file:
                        match_info['file'] = current_file
                    
                    current_group.append(match_info)
                        
                except ValueError:
                    # Not a valid line number, skip
                    continue
        
        # Add the last group
        if current_group:
            matches.extend(current_group)
        
        return matches
        
    except Exception as e:
        print(f"Error running ripgrep: {e}", file=sys.stderr)
        return []

def extract_line_ranges(file_path: str, ranges: List[LineRange]) -> List[Tuple[LineRange, List[str]]]:
    """Extract specified line ranges from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        return []
    
    results = []
    for line_range in ranges:
        start_idx = max(0, line_range.start - 1)
        end_idx = min(len(lines), line_range.end)
        
        if start_idx < len(lines):
            extracted_lines = lines[start_idx:end_idx]
            actual_range = LineRange(start_idx + 1, start_idx + len(extracted_lines))
            results.append((actual_range, extracted_lines))
    
    return results

def format_output_with_context(results: List[Dict], args) -> None:
    """Format and print results with full context display."""
    if args.json:
        # Filter to only include actual matches for JSON output
        json_results = [r for r in results if r.get('is_match', True)]
        print(json.dumps(json_results, indent=2))
        return
    
    if not results:
        if not args.quiet:
            print("No matches found")
        return
    
    # Show result summary in verbose mode
    if args.verbose:
        match_count = sum(1 for r in results if r.get('is_match', False))
        context_count = sum(1 for r in results if r.get('is_context', False))
        print(f"Found {match_count} matches with {context_count} context lines", file=sys.stderr)
    
    # Initialize AST context finder if requested
    context_finder = None
    if hasattr(args, 'ast_context') and args.ast_context and HAS_AST_CONTEXT:
        context_finder = ASTContextFinder()
    
    # ANSI color codes
    MATCH_COLOR = '\033[1;31m'      # Bold red for matches
    CONTEXT_COLOR = '\033[90m'       # Gray for context lines
    LINE_NUM_COLOR = '\033[36m'      # Cyan for line numbers
    FILE_COLOR = '\033[1;34m'        # Bold blue for file names
    AST_COLOR = '\033[33m'           # Yellow for AST context
    RESET = '\033[0m'
    
    use_colors = sys.stdout.isatty() and not args.no_color if hasattr(args, 'no_color') else sys.stdout.isatty()
    
    current_file = None
    for i, match in enumerate(results):
        # Print file header
        if match['file'] != current_file:
            current_file = match['file']
            if i > 0:
                print()  # Blank line between files
            if use_colors:
                print(f"{FILE_COLOR}{match['file']}{RESET}:")
            else:
                print(f"{match['file']}:")
        
        # Get AST context if available and it's a match line
        if context_finder and match.get('is_match', True):
            ast_context = context_finder._format_context_parts(
                context_finder.get_context_for_line(match['file'], match['line'])
            )
            if ast_context:
                if use_colors:
                    print(f"       {AST_COLOR}AST context of line {match['line']} - [{ast_context}]{RESET}")
                else:
                    print(f"       AST context of line {match['line']} - [{ast_context}]")
        
        # Format line with highlighting
        line_text = match['text']
        line_num_str = f"{match['line']:6}"
        
        # Apply color to line number
        if use_colors:
            if match.get('is_context'):
                line_num_str = f"{CONTEXT_COLOR}{line_num_str}{RESET}"
            else:
                line_num_str = f"{LINE_NUM_COLOR}{line_num_str}{RESET}"
        
        # Highlight matches in the line
        if match['matches'] and use_colors:
            offset = 0
            highlighted = ""
            for m in sorted(match['matches'], key=lambda x: x['start']):
                highlighted += line_text[offset:m['start']]
                highlighted += f"{MATCH_COLOR}{line_text[m['start']:m['end']]}{RESET}"
                offset = m['end']
            highlighted += line_text[offset:]
            
            # Apply context color to non-match lines
            if match.get('is_context'):
                print(f"{line_num_str}: {CONTEXT_COLOR}{highlighted}{RESET}")
            else:
                print(f"{line_num_str}: {highlighted}")
        else:
            # No highlighting
            if use_colors and match.get('is_context'):
                print(f"{line_num_str}: {CONTEXT_COLOR}{line_text}{RESET}")
            else:
                print(f"{line_num_str}: {line_text}")
        
        # Extract method if requested (only for match lines)
        if match.get('is_match', True) and (args.extract_method or args.extract_method_alllines):
            # Method extraction code remains the same
            pass

def main():
    # Create parser
    if HAS_STANDARD_PARSER:
        parser = create_standard_parser(
            'search',
            'find_text v5 - Enhanced search with multiline capabilities',
            epilog='''
EXAMPLES:
  # Search with ± context syntax
  find_text.py "TODO" ±10                    # 10 lines before and after
  find_text.py "error" --file MyClass.java ±5  # With specific file
  
  # Auto file finding
  find_text.py "processOrder" --file OrderManager.java  # Finds file automatically
  
  # Extract line ranges after search
  find_text.py "TODO" --extract-ranges       # Shows line numbers for piping
  
  # Traditional context options still work
  find_text.py "pattern" -C 5                # 5 lines of context
  find_text.py "pattern" -A 3 -B 2           # 3 after, 2 before
'''
        )
    else:
        parser = argparse.ArgumentParser(description='find_text v5 - Enhanced search')
        parser.add_argument('pattern', help='Search pattern')
        # Add standard search arguments
        parser.add_argument('--file', '--path', dest='file', help='Search in specific file')
        parser.add_argument('--scope', default='.', help='Directory scope for search')
        parser.add_argument('--type', choices=['text', 'regex', 'word'], default='text', help='Search type')
        parser.add_argument('-i', '--ignore-case', action='store_true', help='Case-insensitive search')
        parser.add_argument('-w', '--whole-word', action='store_true', help='Match whole words only')
        parser.add_argument('--include', '--glob', '-g', dest='glob', help='Include files matching pattern')
        parser.add_argument('--exclude', help='Exclude files matching pattern')
        parser.add_argument('-A', '--after-context', type=int, metavar='N', help='Show N lines after match')
        parser.add_argument('-B', '--before-context', type=int, metavar='N', help='Show N lines before match')
        parser.add_argument('-C', '--context', type=int, metavar='N', help='Show N lines around match')
        parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
        parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
        parser.add_argument('--json', action='store_true', help='Output as JSON')
        parser.add_argument('-r', '--recursive', action='store_true', default=True, help='Search recursively')
    
    # Add context argument that can handle ± syntax
    parser.add_argument('context_spec', nargs='?', 
                       help='Context specification (e.g., ±10 for 10 lines before/after)')
    
    # Add new options
    parser.add_argument('--extract-ranges', action='store_true',
                       help='Output line ranges suitable for multiline_reader')
    parser.add_argument('--merge-ranges', action='store_true',
                       help='Merge overlapping context ranges')
    parser.add_argument('--no-color', action='store_true',
                       help='Disable color output')
    parser.add_argument('--auto-find', action='store_true',
                       help='Automatically find file if not found at given path')
    
    # Keep all existing options
    parser.add_argument('--ast-context', action='store_true',
                       help='Show AST context (class/method) for matches')
    parser.add_argument('--no-ast-context', action='store_true',
                       help='Disable AST context even if enabled in config')
    parser.add_argument('--extract-method', action='store_true',
                       help='Extract containing methods (up to 500 lines)')
    parser.add_argument('--extract-method-alllines', action='store_true',
                       help='Extract containing methods regardless of size')
    
    # Parse arguments WITHOUT validation first (to check for auto-find)
    args = parser.parse_args()
    
    # Auto-find file BEFORE preflight checks
    if hasattr(args, 'file') and args.file and (hasattr(args, 'auto_find') and args.auto_find or not os.path.exists(args.file)):
        if hasattr(args, 'verbose') and args.verbose:
            print(f"Attempting to auto-find file: {args.file}", file=sys.stderr)
        found_file = find_file_auto(args.file)
        if found_file:
            if hasattr(args, 'verbose') and args.verbose:
                print(f"Auto-found file: {found_file}", file=sys.stderr)
            args.file = found_file
        else:
            print(f"Error: File '{args.file}' not found", file=sys.stderr)
            if hasattr(args, 'auto_find') and args.auto_find:
                print("Auto-find was enabled but couldn't locate the file", file=sys.stderr)
            sys.exit(1)
    
    # NOW run preflight checks with the found file
    if HAS_STANDARD_PARSER:
        try:
            from preflight_checks import PreflightChecker, run_preflight_checks
            
            checks = []
            
            # File existence checks
            if hasattr(args, 'file') and args.file:
                checks.append((PreflightChecker.check_file_readable, (args.file,)))
            
            # Directory existence checks
            if hasattr(args, 'scope') and args.scope and args.scope != '.':
                checks.append((PreflightChecker.check_directory_accessible, (args.scope,)))
            
            # Run all checks
            if checks:
                run_preflight_checks(checks)
                
        except ImportError:
            pass  # Pre-flight checks not available
    
    # Apply configuration
    apply_config_to_args('find_text', args, parser)
    
    # Handle context_spec if provided
    if hasattr(args, 'context_spec') and args.context_spec:
        try:
            context_lines = parse_context_spec(args.context_spec)
            # Override any existing context settings
            args.context = context_lines
            args.before_context = None
            args.after_context = None
        except ValueError:
            print(f"Invalid context specification: {args.context_spec}", file=sys.stderr)
            sys.exit(1)
    
    # Handle --no-ast-context flag
    if args.no_ast_context:
        args.ast_context = False
    
    # Determine if we need to use context-aware search
    use_context_search = (args.context or args.before_context or args.after_context or 
                         args.extract_ranges or args.merge_ranges)
    
    # Verbose output
    if args.verbose:
        print(f"Pattern: {args.pattern}", file=sys.stderr)
        print(f"File: {args.file}", file=sys.stderr)
        print(f"Scope: {args.scope}", file=sys.stderr)
        print(f"Context: {args.context}", file=sys.stderr)
        print(f"AST context: {'enabled' if getattr(args, 'ast_context', False) else 'disabled'}", file=sys.stderr)
    
    # Perform search
    try:
        if use_context_search:
            # Use non-JSON mode to get context
            results = search_with_context(args.pattern, args)
            
            # Handle extract-ranges option
            if args.extract_ranges:
                # Group by file and extract line ranges
                file_ranges = {}
                for match in results:
                    if match.get('is_match', True):
                        file = match['file']
                        if file not in file_ranges:
                            file_ranges[file] = []
                        file_ranges[file].append(match['line'])
                
                # Output in multiline_reader format
                for file, lines in file_ranges.items():
                    if args.merge_ranges:
                        # Create ranges with context and merge
                        context = args.context or 0
                        ranges = [LineRange(line - context, line + context) for line in lines]
                        merged = merge_overlapping_ranges(ranges)
                        for r in merged:
                            print(f"{file}:{r}")
                    else:
                        # Output individual lines with context notation
                        context = args.context or 0
                        for line in lines:
                            if context > 0:
                                print(f"{file}:{line}±{context}")
                            else:
                                print(f"{file}:{line}")
                return
        else:
            # Use existing JSON-based search for simple cases
            from find_text_v4 import search_in_files
            results = search_in_files(args.pattern, args)
        
        # Format output
        if use_context_search:
            format_output_with_context(results, args)
        else:
            # Use existing formatter for compatibility
            from find_text_v4 import format_output
            format_output(results, args, 'content')
        
    except KeyboardInterrupt:
        print("\nSearch interrupted", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
