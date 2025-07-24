#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
General-purpose text and file finder with multiple search strategies.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import os
import re
import subprocess
import argparse
from pathlib import Path
import shutil
from datetime import datetime, timedelta
import fnmatch

def check_ripgrep():
    """Check if ripgrep is installed."""
    if not shutil.which('rg'):
        print("Error: ripgrep (rg) is not installed.")
        print("Install it with: brew install ripgrep")
        sys.exit(1)

def format_size(size):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"

def find_in_content(pattern, path=".", file_pattern="*", regex=False, ignore_case=False, 
                   whole_word=False, invert=False, count_only=False, files_only=False,
                   max_depth=None, before_context=0, after_context=0, context=0,
                   language=None, multiline_ranges=None):
    """Find pattern in file contents using ripgrep."""
    check_ripgrep()
    
    cmd = ["rg"]
    
    # Always include line numbers for enhanced context to work
    if multiline_ranges:
        cmd.append("-n")
    
    # Language-specific file type filtering
    if language:
        lang_map = {
            'python': 'py',
            'java': 'java',
            'javascript': 'js',
            'typescript': 'ts',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rust': 'rust',
            'ruby': 'rb',
            'php': 'php'
        }
        if language.lower() in lang_map:
            cmd.extend(['-t', lang_map[language.lower()]])
    
    # Add flags
    if regex:
        cmd.append("-e")
    else:
        cmd.append("-F")  # Fixed string
    
    if ignore_case:
        cmd.append("-i")
    
    if whole_word:
        cmd.append("-w")
    
    if invert:
        cmd.append("-v")
    
    if count_only:
        cmd.append("-c")
    
    if files_only:
        cmd.append("-l")
    
    if max_depth:
        cmd.extend(["--max-depth", str(max_depth)])
    
    # Context options
    if context > 0:
        cmd.extend(["-C", str(context)])
    else:
        if before_context > 0:
            cmd.extend(["-B", str(before_context)])
        if after_context > 0:
            cmd.extend(["-A", str(after_context)])
    
    # Add file pattern
    if file_pattern != "*":
        cmd.extend(["-g", file_pattern])
    
    # Add pattern and path
    cmd.append(pattern)
    cmd.append(path)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            # If multiline ranges are specified, enhance the output
            if multiline_ranges:
                output = enhance_with_multiline_ranges(output, multiline_ranges)
            return output
        elif result.returncode == 1:
            # No matches found
            return ""
        else:
            print(f"Error: {result.stderr}", file=sys.stderr)
            return ""
    except Exception as e:
        print(f"Error running ripgrep: {e}", file=sys.stderr)
        return ""


def enhance_with_multiline_ranges(ripgrep_output, multiline_ranges):
    """
    Enhance ripgrep output with additional multiline context.
    
    Args:
        ripgrep_output: The output from ripgrep
        multiline_ranges: Dictionary with additional context specifications
                         e.g., {"extend_context": 10, "show_method_boundaries": True}
    
    Returns:
        Enhanced output with additional context
    """
    lines = ripgrep_output.strip().split('\n')
    enhanced_lines = []
    
    for line in lines:
        enhanced_lines.append(line)
        
        # Parse ripgrep output to extract filename and line number
        # Handle both formats: "filename:line_num:content" and "filename:content"
        match = re.match(r'^([^:]+):(?:(\d+):)?(.*)$', line)
        if match:
            filename = match.group(1)
            line_num_str = match.group(2)
            content = match.group(3)
            
            # If no line number in output, skip extended context
            if not line_num_str:
                continue
                
            line_num = int(line_num_str)
            
            # Add extended context if requested
            if multiline_ranges.get('extend_context', 0) > 0:
                extend_context = multiline_ranges['extend_context']
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        file_lines = f.readlines()
                    
                    # Add context lines before and after
                    start_line = max(0, line_num - extend_context - 1)
                    end_line = min(len(file_lines), line_num + extend_context)
                    
                    enhanced_lines.append(f"  >>> Extended context for {filename}:{line_num} <<<")
                    for i in range(start_line, end_line):
                        if i + 1 != line_num:  # Don't duplicate the original match
                            enhanced_lines.append(f"  {i+1:4d}: {file_lines[i].rstrip()}")
                    enhanced_lines.append("  >>> End extended context <<<")
                    
                except Exception as e:
                    enhanced_lines.append(f"  Error reading context: {e}")
    
    return '\n'.join(enhanced_lines)


def find_files(pattern, path=".", name_only=False, type_filter=None, size_filter=None,
               time_filter=None, max_depth=None, follow_links=False, hidden=False):
    """Find files by name pattern and various filters."""
    
    path = Path(path)
    matches = []
    
    # Determine iterator based on max_depth
    if max_depth is None:
        iterator = path.rglob(pattern) if not name_only else path.rglob("*")
    else:
        # Manual depth control - calculate relative depth from start path
        start_depth = len(path.parts)
        
        def limited_walk(p):
            try:
                for item in p.iterdir():
                    if not hidden and item.name.startswith('.'):
                        continue
                    
                    # Calculate relative depth
                    relative_depth = len(item.parts) - start_depth
                    if relative_depth <= max_depth:
                        yield item
                        if item.is_dir() and (follow_links or not item.is_symlink()):
                            # Only recurse if we haven't exceeded max depth
                            if relative_depth < max_depth:
                                yield from limited_walk(item)
            except (PermissionError, OSError):
                pass
        
        iterator = limited_walk(path)
    
    for file_path in iterator:
        try:
            # Skip hidden files unless requested
            if not hidden and any(part.startswith('.') for part in file_path.parts):
                continue
            
            # Name pattern matching
            if name_only and not fnmatch.fnmatch(file_path.name, pattern):
                continue
            
            # Type filter
            if type_filter:
                if type_filter == 'f' and not file_path.is_file():
                    continue
                elif type_filter == 'd' and not file_path.is_dir():
                    continue
                elif type_filter == 'l' and not file_path.is_symlink():
                    continue
            
            # Size filter
            if size_filter and file_path.is_file():
                size = file_path.stat().st_size
                op, size_bytes = size_filter
                
                if op == '+' and size <= size_bytes:
                    continue
                elif op == '-' and size >= size_bytes:
                    continue
            
            # Time filter
            if time_filter and file_path.exists():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                now = datetime.now()
                op, delta = time_filter
                
                if op == '+' and (now - mtime) <= delta:
                    continue
                elif op == '-' and (now - mtime) >= delta:
                    continue
            
            matches.append(file_path)
            
        except (PermissionError, OSError):
            continue
    
    return sorted(matches)

def find_duplicates(path=".", file_pattern="*", by_name=False, by_size=False, by_content=False):
    """Find duplicate files by name, size, or content."""
    from collections import defaultdict
    import hashlib
    
    files = find_files(file_pattern, path, type_filter='f')
    
    if by_name:
        duplicates = defaultdict(list)
        for f in files:
            duplicates[f.name].append(f)
        return {k: v for k, v in duplicates.items() if len(v) > 1}
    
    elif by_size:
        duplicates = defaultdict(list)
        for f in files:
            try:
                size = f.stat().st_size
                duplicates[size].append(f)
            except (OSError, PermissionError):
                pass
        return {k: v for k, v in duplicates.items() if len(v) > 1}
    
    elif by_content:
        # First group by size (files with different sizes can't be duplicates)
        size_groups = defaultdict(list)
        for f in files:
            try:
                size = f.stat().st_size
                if size > 0:  # Only hash non-empty files
                    size_groups[size].append(f)
            except (OSError, PermissionError):
                pass
        
        # Then check content hash for files with same size
        duplicates = defaultdict(list)
        for size, file_list in size_groups.items():
            if len(file_list) > 1:
                for f in file_list:
                    try:
                        hasher = hashlib.md5()
                        with open(f, 'rb') as fh:
                            # Read in chunks to handle large files
                            while chunk := fh.read(8192):
                                hasher.update(chunk)
                        file_hash = hasher.hexdigest()
                        duplicates[file_hash].append(f)
                    except (OSError, PermissionError):
                        pass
        
        return {k: v for k, v in duplicates.items() if len(v) > 1}
    
    return {}

def main():
    parser = argparse.ArgumentParser(
        description='General-purpose file and text finder',
        epilog='''
EXAMPLES:
  # Find text in files
  %(prog)s "TODO" --in-files                    # Find TODO in all files
  %(prog)s "pattern" --in-files -g "*.java"     # Find in Java files only
  %(prog)s "regex.*pattern" --in-files --regex  # Use regex pattern
  %(prog)s "text" --in-files -w                 # Whole word matching
  %(prog)s "text" --in-files -l                 # List files only
  %(prog)s "error" --in-files -C 3              # Show 3 lines of context
  %(prog)s "TODO" --in-files -B 2 -A 5          # Show 2 before, 5 after
  
  # Find files by name
  %(prog)s "*.java"                             # Find all Java files
  %(prog)s "Test*.java" --type f                # Find test files
  %(prog)s "*" --type d                         # Find all directories
  %(prog)s "*.log" --size +10M                  # Find large log files
  %(prog)s "*.tmp" --time +7d                   # Find old temp files
  
  # Find duplicates
  %(prog)s --duplicates-by-name                 # Find files with same name
  %(prog)s --duplicates-by-size "*.jar"         # Find JARs with same size
  %(prog)s --duplicates-by-content "*.java"     # Find identical Java files
  
  # Complex searches
  %(prog)s "FIXME" --in-files -g "*.java" --max-depth 3
  %(prog)s "*.class" --type f --size +1M --time -1d
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Main argument - pattern to search for
    parser.add_argument('pattern', nargs='?', help='Pattern to search for (text or filename)')
    
    # Search mode
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--in-files', action='store_true', 
                           help='Search for text within files (default: search filenames)')
    mode_group.add_argument('--duplicates-by-name', action='store_true',
                           help='Find files with duplicate names')
    mode_group.add_argument('--duplicates-by-size', action='store_true',
                           help='Find files with duplicate sizes')
    mode_group.add_argument('--duplicates-by-content', action='store_true',
                           help='Find files with identical content')
    
    # Common options
    parser.add_argument('--path', '-p', default='.', help='Path to search in (default: current dir)')
    parser.add_argument('--max-depth', type=int, help='Maximum directory depth to search')
    parser.add_argument('--hidden', '-H', action='store_true', help='Include hidden files')
    parser.add_argument('--follow-links', '-L', action='store_true', help='Follow symbolic links')
    
    # File search options
    parser.add_argument('--type', choices=['f', 'd', 'l'], 
                       help='File type: f=file, d=directory, l=symlink')
    parser.add_argument('--size', help='File size filter (e.g., +10M, -1G)')
    parser.add_argument('--time', help='Modified time filter (e.g., +7d, -1h)')
    
    # Text search options
    parser.add_argument('--glob', '-g', dest='file_pattern', default='*',
                       help='File pattern for text search (e.g., *.java)')
    parser.add_argument('--regex', '-E', action='store_true', 
                       help='Use regex pattern matching')
    parser.add_argument('--ignore-case', '-i', action='store_true',
                       help='Case-insensitive search')
    parser.add_argument('--whole-word', '-w', action='store_true',
                       help='Match whole words only')
    parser.add_argument('--invert', '-v', action='store_true',
                       help='Invert match (show non-matching lines)')
    parser.add_argument('--lang', '--language', dest='language',
                       choices=['python', 'java', 'javascript', 'typescript', 'cpp', 'c', 'go', 'rust', 'ruby', 'php'],
                       help='Search only in files of specified language')
    parser.add_argument('--count', '-c', action='store_true',
                       help='Show match count per file')
    parser.add_argument('--files-only', '-l', action='store_true',
                       help='List matching files only')
    
    # Context options
    parser.add_argument('--before-context', '-B', type=int, default=0, metavar='N',
                       help='Show N lines before each match')
    parser.add_argument('--after-context', '-A', type=int, default=0, metavar='N',
                       help='Show N lines after each match')
    parser.add_argument('--context', '-C', type=int, default=0, metavar='N',
                       help='Show N lines before and after each match')
    
    # Enhanced multiline context options
    parser.add_argument('--extend-context', type=int, metavar='N',
                       help='Show N additional lines of context around each match (beyond ripgrep context)')
    parser.add_argument('--multiline-ranges', help='Specify custom multiline ranges (e.g., "extend_context:10")')
    
    # Output options
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress headers and formatting')
    parser.add_argument('--stats', action='store_true',
                       help='Show statistics summary')
    
    args = parser.parse_args()
    
    # Handle duplicate finding modes
    if args.duplicates_by_name or args.duplicates_by_size or args.duplicates_by_content:
        pattern = args.pattern or '*'
        
        if args.duplicates_by_name:
            duplicates = find_duplicates(args.path, pattern, by_name=True)
            dup_type = "name"
        elif args.duplicates_by_size:
            duplicates = find_duplicates(args.path, pattern, by_size=True)
            dup_type = "size"
        else:
            duplicates = find_duplicates(args.path, pattern, by_content=True)
            dup_type = "content"
        
        if not duplicates:
            if not args.quiet:
                print(f"No duplicate files found by {dup_type}")
            sys.exit(0)
        
        # Display duplicates
        total_files = 0
        for key, files in duplicates.items():
            if not args.quiet:
                if dup_type == "size":
                    print(f"\n=== Files with size {format_size(key)} ===")
                else:
                    print(f"\n=== Duplicate group: {key} ===")
            
            for f in sorted(files):
                print(f)
                total_files += 1
        
        if args.stats and not args.quiet:
            print(f"\nFound {len(duplicates)} groups with {total_files} total files")
        
        sys.exit(0)
    
    # Require pattern for other modes
    if not args.pattern:
        parser.error("Pattern required (use --help for examples)")
    
    # Parse size filter
    size_filter = None
    if args.size:
        if args.size[0] not in '+-':
            parser.error("Size filter must start with + or - (e.g., +10M, -1G)")
        op, value_str = args.size[0], args.size[1:]
        
        multiplier = 1
        unit = value_str[-1].upper()
        if unit in 'KMGT':
            units = {'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
            multiplier = units[unit]
            value_str = value_str[:-1]
        
        try:
            size_bytes = float(value_str) * multiplier
            size_filter = (op, size_bytes)
        except ValueError:
            parser.error(f"Invalid size value: '{args.size[1:]}'")
    
    # Parse time filter
    time_filter = None
    if args.time:
        if args.time[0] not in '+-':
            parser.error("Time filter must start with + or - (e.g., +7d, -1h)")
        op, value_str = args.time[0], args.time[1:]
        
        try:
            unit = value_str[-1].lower()
            if unit == 'd':
                delta = timedelta(days=int(value_str[:-1]))
            elif unit == 'h':
                delta = timedelta(hours=int(value_str[:-1]))
            elif unit == 'm':
                delta = timedelta(minutes=int(value_str[:-1]))
            else:
                delta = timedelta(days=int(value_str))
            time_filter = (op, delta)
        except ValueError:
            parser.error(f"Invalid time value: '{args.time[1:]}'")
    
    # Execute search
    if args.in_files:
        # Prepare multiline ranges if specified
        multiline_ranges = None
        if args.extend_context:
            multiline_ranges = {'extend_context': args.extend_context}
        elif args.multiline_ranges:
            # Parse custom multiline ranges specification
            multiline_ranges = {}
            for spec in args.multiline_ranges.split(','):
                if ':' in spec:
                    key, value = spec.split(':', 1)
                    try:
                        multiline_ranges[key] = int(value)
                    except ValueError:
                        multiline_ranges[key] = value
        
        # Search text in files
        result = find_in_content(
            args.pattern, args.path, args.file_pattern,
            regex=args.regex, ignore_case=args.ignore_case,
            whole_word=args.whole_word, invert=args.invert,
            count_only=args.count, files_only=args.files_only,
            max_depth=args.max_depth, before_context=args.before_context,
            after_context=args.after_context, context=args.context,
            language=args.language, multiline_ranges=multiline_ranges
        )
        
        if result:
            print(result, end='')
        elif not args.quiet:
            print("No matches found")
    else:
        # Search for files
        files = find_files(
            args.pattern, args.path, name_only=True,
            type_filter=args.type, size_filter=size_filter,
            time_filter=time_filter, max_depth=args.max_depth,
            follow_links=args.follow_links, hidden=args.hidden
        )
        
        if not files:
            if not args.quiet:
                print("No files found")
            sys.exit(1)
        
        # Display results
        for f in files:
            if args.stats:
                try:
                    stat = f.stat()
                    size = format_size(stat.st_size) if f.is_file() else "DIR"
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    print(f"{str(f):<50} {size:>10} {mtime}")
                except (OSError, PermissionError):
                    print(f"{str(f):<50} {'<NO STATS>':>10} {'<NO STATS>'}")
            else:
                print(f)
        
        if args.stats and not args.quiet:
            total_size = 0
            for f in files:
                try:
                    if f.is_file():
                        total_size += f.stat().st_size
                except (OSError, PermissionError):
                    pass
            print(f"\nTotal: {len(files)} files, {format_size(total_size)}")

if __name__ == '__main__':
    main()