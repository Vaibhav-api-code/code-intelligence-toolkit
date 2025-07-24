#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced multiline reader tool for flexible line range extraction.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Union, Optional
import re

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

class LineRange:
    """Represents a line range with start and end positions."""
    
    def __init__(self, start: int, end: int):
        self.start = max(1, start)  # Ensure positive line numbers
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

def parse_line_spec(spec: str) -> List[LineRange]:
    """
    Parse line specifications into LineRange objects.
    
    Supported formats:
    - "100" -> line 100
    - "100-120" -> lines 100 to 120
    - "100,200,300" -> lines 100, 200, and 300
    - "100-120,200-210" -> lines 100-120 and 200-210
    - "100:10" -> 10 lines starting from line 100
    - "100±5" -> 5 lines before and after line 100
    """
    ranges = []
    
    # Split by comma first
    parts = [part.strip() for part in spec.split(',')]
    
    for part in parts:
        if '±' in part:
            # Context around a line: "100±5"
            center, context = part.split('±', 1)
            center = int(center)
            context = int(context)
            ranges.append(LineRange(center - context, center + context))
        elif ':' in part:
            # Range with length: "100:10"
            start, length = part.split(':', 1)
            start = int(start)
            length = int(length)
            ranges.append(LineRange(start, start + length - 1))
        elif '-' in part:
            # Range: "100-120"
            start, end = part.split('-', 1)
            ranges.append(LineRange(int(start), int(end)))
        else:
            # Single line: "100"
            line_num = int(part)
            ranges.append(LineRange(line_num, line_num))
    
    return ranges

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

def read_file_lines(file_path: str) -> List[str]:
    """Read file lines with error handling. Supports reading from stdin."""
    try:
        if file_path == '-':
            # Read from stdin
            return sys.stdin.readlines()
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.readlines()
    except Exception as e:
        raise Exception(f"Error reading file: {e}")

def extract_line_ranges(lines: List[str], ranges: List[LineRange]) -> List[Tuple[LineRange, List[str]]]:
    """Extract specified line ranges from file lines."""
    results = []
    
    for line_range in ranges:
        # Adjust for 0-based indexing and handle bounds
        start_idx = max(0, line_range.start - 1)
        end_idx = min(len(lines), line_range.end)
        
        if start_idx < len(lines):
            extracted_lines = lines[start_idx:end_idx]
            # Adjust the actual range based on what was extracted
            actual_range = LineRange(start_idx + 1, start_idx + len(extracted_lines))
            results.append((actual_range, extracted_lines))
    
    return results

def format_output(results: List[Tuple[LineRange, List[str]]], file_path: str, 
                 show_line_numbers: bool = True, show_separators: bool = True,
                 highlight_lines: Optional[List[int]] = None,
                 pattern_matches: Optional[dict] = None) -> str:
    """Format the extracted lines for output with optional pattern highlighting."""
    if not results:
        return f"No lines found in {file_path}"
    
    output = []
    
    # ANSI color codes for highlighting
    HIGHLIGHT_START = '\033[93m'  # Yellow
    HIGHLIGHT_END = '\033[0m'     # Reset
    LINE_HIGHLIGHT = '\033[92m'   # Green for line markers
    
    if show_separators:
        output.append(f"=== File: {file_path} ===")
    
    for i, (line_range, lines) in enumerate(results):
        if show_separators and i > 0:
            output.append("")  # Add blank line between ranges
        
        if show_separators:
            output.append(f"--- Lines {line_range} ---")
        
        for j, line in enumerate(lines):
            line_num = line_range.start + j
            line_content = line.rstrip('\n')
            
            # Apply pattern highlighting if we have match info
            if pattern_matches and line_num in pattern_matches:
                match_info = pattern_matches[line_num]
                if hasattr(match_info, 'start') and hasattr(match_info, 'end'):
                    start = match_info.start()
                    end = match_info.end()
                    # Highlight the matched portion
                    line_content = (
                        line_content[:start] + 
                        HIGHLIGHT_START + line_content[start:end] + HIGHLIGHT_END +
                        line_content[end:]
                    )
            
            if show_line_numbers:
                if highlight_lines and line_num in highlight_lines:
                    prefix = f"{LINE_HIGHLIGHT}>>>{line_num:4d}: {HIGHLIGHT_END}"
                else:
                    prefix = f"{line_num:4d}: "
                
                output.append(f"{prefix}{line_content}")
            else:
                output.append(line_content)
    
    return '\n'.join(output)

def find_lines_containing_pattern(lines: List[str], pattern: str, 
                                regex: bool = False, ignore_case: bool = False) -> List[Tuple[int, Optional[re.Match]]]:
    """Find line numbers containing a pattern, returning line numbers and match objects."""
    results = []
    
    if regex:
        flags = re.IGNORECASE if ignore_case else 0
        compiled_pattern = re.compile(pattern, flags)
        for i, line in enumerate(lines):
            match = compiled_pattern.search(line)
            if match:
                results.append((i + 1, match))
    else:
        if ignore_case:
            pattern_lower = pattern.lower()
            for i, line in enumerate(lines):
                lower_line = line.lower()
                if pattern_lower in lower_line:
                    # Create a pseudo-match object with start/end positions
                    start = lower_line.find(pattern_lower)
                    results.append((i + 1, type('Match', (), {'start': lambda: start, 'end': lambda: start + len(pattern)})))
        else:
            for i, line in enumerate(lines):
                if pattern in line:
                    # Create a pseudo-match object with start/end positions
                    start = line.find(pattern)
                    results.append((i + 1, type('Match', (), {'start': lambda: start, 'end': lambda: start + len(pattern)})))
    
    return results

def create_context_ranges(line_numbers: List[int], context: int) -> List[LineRange]:
    """Create context ranges around specific line numbers."""
    return [LineRange(line_num - context, line_num + context) for line_num in line_numbers]

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Extract multiple line ranges from files with flexible specifications')
    else:
        parser = argparse.ArgumentParser(description='Extract multiple line ranges from files with flexible specifications')
    
    # Use a custom action to handle the positional arguments more flexibly
    parser.add_argument('files_and_lines', nargs='*', 
                       help='Files to read from, optionally followed by line specification')
    
    # Pattern-based selection
    parser.add_argument('--pattern', help='Extract lines around pattern matches')
    parser.add_argument('--regex', action='store_true', help='Use regex pattern matching')
    # Context around specific lines
    parser.add_argument('--around-lines', help='Comma-separated list of line numbers to show context around')
    
    # Output formatting
    parser.add_argument('--no-line-numbers', action='store_true', help='Hide line numbers')
    parser.add_argument('--no-separators', action='store_true', help='Hide section separators')
    parser.add_argument('--highlight', help='Comma-separated list of line numbers to highlight')
    
    # Output options
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--merge-ranges', action='store_true', 
                       help='Merge overlapping or adjacent ranges')
    
    args = parser.parse_args()
    
    # Parse files and line specification from positional arguments
    files = []
    line_spec = None
    
    if args.files_and_lines:
        # Check if the last argument looks like a line specification
        last_arg = args.files_and_lines[-1]
        # Line specs contain numbers and specific characters
        if (any(char in last_arg for char in ['-', '±', ':', ',']) and 
            any(char.isdigit() for char in last_arg)):
            # Last argument is probably a line specification
            files = args.files_and_lines[:-1]
            line_spec = last_arg
        else:
            # All arguments are files
            files = args.files_and_lines
    
    # Handle case where no files are specified (use stdin)
    if not files:
        files = ['-']
    
    # Validate arguments
    if not line_spec and not args.pattern and not args.around_lines:
        parser.error("Must specify either line ranges, --pattern, or --around-lines")
    
    args.files = files
    args.lines = line_spec
    
    # Parse highlight lines
    highlight_lines = None
    if args.highlight:
        try:
            highlight_lines = [int(x.strip()) for x in args.highlight.split(',')]
        except ValueError:
            parser.error("Invalid highlight line numbers")
    
    # Process files
    all_output = []
    
    # Files to process are already in args.files
    files_to_process = args.files
    
    for file_path in files_to_process:
        try:
            # Check if file exists (skip for stdin)
            if file_path != '-' and not Path(file_path).exists():
                print(f"Warning: File '{file_path}' not found", file=sys.stderr)
                continue
            
            # Read file lines
            lines = read_file_lines(file_path)
            
            # Determine line ranges
            pattern_matches = None
            if args.pattern:
                # Pattern-based extraction
                matches = find_lines_containing_pattern(
                    lines, args.pattern, args.regex, args.ignore_case
                )
                
                if not matches:
                    if not args.no_separators:
                        all_output.append(f"No matches found for pattern '{args.pattern}' in {file_path}")
                    continue
                
                # Extract line numbers and match objects
                matching_lines = [line_num for line_num, _ in matches]
                pattern_matches = {line_num: match_obj for line_num, match_obj in matches}
                
                ranges = create_context_ranges(matching_lines, args.context)
                
                # Highlight the matching lines
                if highlight_lines is None:
                    highlight_lines = matching_lines
                else:
                    highlight_lines.extend(matching_lines)
            elif args.around_lines:
                # Context around specific lines
                try:
                    specific_lines = [int(x.strip()) for x in args.around_lines.split(',')]
                    ranges = create_context_ranges(specific_lines, args.context)
                    # Also highlight these lines
                    if highlight_lines is None:
                        highlight_lines = specific_lines
                    else:
                        highlight_lines.extend(specific_lines)
                except ValueError:
                    print(f"Invalid line numbers in --around-lines: {args.around_lines}", file=sys.stderr)
                    continue
            else:
                # Direct line specification
                ranges = parse_line_spec(args.lines)
            
            # Merge ranges if requested
            if args.merge_ranges:
                ranges = merge_overlapping_ranges(ranges)
            
            # Extract lines
            results = extract_line_ranges(lines, ranges)
            
            # Format output
            output = format_output(
                results, file_path,
                show_line_numbers=not args.no_line_numbers,
                show_separators=not args.no_separators,
                highlight_lines=highlight_lines,
                pattern_matches=pattern_matches
            )
            
            all_output.append(output)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            continue
    
    # Output results
    final_output = '\n\n'.join(all_output)
    
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(final_output)
            print(f"Output written to {args.output}")
        except Exception as e:
            print(f"Error writing to output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(final_output)

if __name__ == '__main__':
    main()