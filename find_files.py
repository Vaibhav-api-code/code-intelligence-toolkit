#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Fast file finding tool with comprehensive filters.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
import fnmatch
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Iterator
import stat

# Import standard argument parser
try:
    from enhanced_standard_arg_parser import create_directory_parser as create_parser
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
        def check_directory_accessible(path):
            return True, ""

# Load common configuration system
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    # Graceful fallback if common_config is not available
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass

def parse_size(size_str: str) -> int:
    """Parse size string like '10MB' to bytes."""
    size_str = size_str.upper().strip()
    
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3,
        'TB': 1024**4
    }
    
    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            try:
                number = float(size_str[:-len(suffix)])
                return int(number * multiplier)
            except ValueError:
                pass
    
    try:
        return int(size_str)
    except ValueError:
        print(f"Warning: Could not parse size '{size_str}', ignoring", file=sys.stderr)
        return 0

def parse_time_delta(time_str: str) -> timedelta:
    """Parse time string like '2d', '3h', '30m' to timedelta."""
    time_str = time_str.lower().strip()
    
    multipliers = {
        's': 1,          # seconds
        'm': 60,         # minutes
        'h': 3600,       # hours
        'd': 86400,      # days
        'w': 604800,     # weeks
    }
    
    for suffix, seconds in multipliers.items():
        if time_str.endswith(suffix):
            try:
                number = float(time_str[:-1])
                return timedelta(seconds=number * seconds)
            except ValueError:
                pass
    
    # Try parsing as plain number (assume days)
    try:
        return timedelta(days=float(time_str))
    except ValueError:
        print(f"Warning: Could not parse time '{time_str}', ignoring", file=sys.stderr)
        return timedelta(0)

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"

def should_skip_directory(dir_path: Path, args) -> bool:
    """Check if directory should be skipped."""
    dir_name = dir_path.name
    
    # Skip hidden directories unless --all is specified
    if not args.all and dir_name.startswith('.'):
        return True
    
    # Skip common build/cache directories unless explicitly included
    if not args.include_build:
        skip_dirs = {
            '__pycache__', '.git', '.svn', '.hg', '.bzr',
            'node_modules', 'target', 'build', 'dist', '.gradle',
            '.idea', '.vscode', '.settings', 'bin', 'obj',
            '.tox', '.coverage', '.pytest_cache', '.mypy_cache'
        }
        if dir_name in skip_dirs:
            return True
    
    return False

def matches_filters(file_path: Path, args) -> bool:
    """Check if file matches all specified filters."""
    try:
        stat_info = file_path.stat()
        file_name = file_path.name
        
        # Hidden files filter
        if not args.all and file_name.startswith('.'):
            return False
        
        # Type filters
        if args.dirs_only and not file_path.is_dir():
            return False
        if args.files_only and not file_path.is_file():
            return False
        
        # Name pattern filter
        if args.name:
            if not fnmatch.fnmatch(file_name, args.name):
                return False
        
        # Name regex filter
        if args.regex:
            if not re.search(args.regex, file_name, re.IGNORECASE if args.ignore_case else 0):
                return False
        
        # Extension filter
        if args.ext:
            extensions = [ext.strip() for ext in args.ext.split(',')]
            file_ext = file_path.suffix.lower().lstrip('.')
            if not any(file_ext == ext.lower().lstrip('.') for ext in extensions):
                return False
        
        # Size filters
        if args.min_size:
            min_bytes = parse_size(args.min_size)
            if stat_info.st_size < min_bytes:
                return False
        
        if args.max_size:
            max_bytes = parse_size(args.max_size)
            if stat_info.st_size > max_bytes:
                return False
        
        # Time filters
        file_mtime = datetime.fromtimestamp(stat_info.st_mtime)
        now = datetime.now()
        
        if args.newer_than:
            delta = parse_time_delta(args.newer_than)
            if now - file_mtime > delta:
                return False
        
        if args.older_than:
            delta = parse_time_delta(args.older_than)
            if now - file_mtime < delta:
                return False
        
        # Permission filters
        if args.executable and not os.access(file_path, os.X_OK):
            return False
        
        if args.readable and not os.access(file_path, os.R_OK):
            return False
        
        if args.writable and not os.access(file_path, os.W_OK):
            return False
        
        return True
        
    except (OSError, PermissionError):
        return False

def find_files(search_paths: List[Path], args) -> Iterator[Dict]:
    """Find files matching the criteria."""
    found_count = 0
    
    for search_path in search_paths:
        if not search_path.exists():
            print(f"Warning: Path '{search_path}' does not exist", file=sys.stderr)
            continue
        
        if search_path.is_file():
            # Single file
            if matches_filters(search_path, args):
                yield get_file_info(search_path)
                found_count += 1
                if args.limit and found_count >= args.limit:
                    return
        else:
            # Directory traversal
            try:
                for root, dirs, files in os.walk(search_path):
                    root_path = Path(root)
                    
                    # Skip directories if needed
                    dirs[:] = [d for d in dirs if not should_skip_directory(root_path / d, args)]
                    
                    # Respect max depth
                    if args.max_depth is not None:
                        current_depth = len(root_path.relative_to(search_path).parts)
                        if current_depth >= args.max_depth:
                            dirs.clear()  # Don't go deeper
                    
                    # Check directories
                    if not args.files_only:
                        for dir_name in dirs:
                            dir_path = root_path / dir_name
                            if matches_filters(dir_path, args):
                                yield get_file_info(dir_path)
                                found_count += 1
                                if args.limit and found_count >= args.limit:
                                    return
                    
                    # Check files
                    if not args.dirs_only:
                        for file_name in files:
                            file_path = root_path / file_name
                            if matches_filters(file_path, args):
                                yield get_file_info(file_path)
                                found_count += 1
                                if args.limit and found_count >= args.limit:
                                    return
                                    
            except PermissionError:
                print(f"Warning: Permission denied accessing '{search_path}'", file=sys.stderr)
                continue

def get_file_info(file_path: Path) -> Dict:
    """Get file information dictionary."""
    try:
        stat_info = file_path.stat()
        mtime = datetime.fromtimestamp(stat_info.st_mtime)
        
        return {
            'path': str(file_path),
            'name': file_path.name,
            'size': stat_info.st_size,
            'size_formatted': format_size(stat_info.st_size),
            'mtime': mtime,
            'mtime_formatted': mtime.strftime('%Y-%m-%d %H:%M:%S'),
            'is_dir': file_path.is_dir(),
            'is_file': file_path.is_file(),
            'is_symlink': file_path.is_symlink(),
            'extension': file_path.suffix.lower(),
            'permissions': stat.filemode(stat_info.st_mode)
        }
    except (OSError, PermissionError) as e:
        return {
            'path': str(file_path),
            'name': file_path.name,
            'error': str(e)
        }

def format_output(files: List[Dict], args) -> str:
    """Format the output based on requested style."""
    if not files:
        return "🔍 No files found matching the criteria"
    
    output = []
    
    if args.long:
        # Detailed format
        output.append(f"🔍 FOUND {len(files)} FILES")
        output.append("=" * 80)
        
        for file_info in files:
            if 'error' in file_info:
                output.append(f"❌ {file_info['path']} - Error: {file_info['error']}")
                continue
            
            path = file_info['path']
            size = file_info['size_formatted']
            mtime = file_info['mtime_formatted']
            perms = file_info['permissions']
            
            type_icon = "📁" if file_info['is_dir'] else "📄"
            
            output.append(f"{type_icon} {perms} {size:>8} {mtime} {path}")
    
    elif args.size_info:
        # Size-focused format
        output.append(f"🔍 FOUND {len(files)} FILES (with sizes)")
        output.append("=" * 60)
        
        for file_info in files:
            if 'error' in file_info:
                continue
            
            path = file_info['path']
            size = file_info['size_formatted']
            type_icon = "📁" if file_info['is_dir'] else "📄"
            
            output.append(f"{type_icon} {size:>8} {path}")
    
    else:
        # Simple path list (default)
        output.append(f"🔍 FOUND {len(files)} FILES")
        output.append("-" * 40)
        
        for file_info in files:
            if 'error' in file_info:
                output.append(f"❌ {file_info['path']} - Error: {file_info['error']}")
            else:
                output.append(file_info['path'])
    
    # Summary statistics
    if args.summary:
        total_files = sum(1 for f in files if f.get('is_file', False))
        total_dirs = sum(1 for f in files if f.get('is_dir', False))
        total_size = sum(f.get('size', 0) for f in files)
        
        output.append("")
        output.append("📊 SUMMARY")
        output.append(f"   Files: {total_files}")
        output.append(f"   Directories: {total_dirs}")
        output.append(f"   Total size: {format_size(total_size)}")
    
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(
        description='Fast file finding with comprehensive filters',
        epilog='''
EXAMPLES:
  # Find all Python files
  find_files.py --ext py
  
  # Find large files (>10MB)
  find_files.py --min-size 10MB
  
  # Find recently modified files (last 2 days)
  find_files.py --newer-than 2d
  
  # Find by name pattern
  find_files.py --name "*.java" --size-info
  
  # Find executable files
  find_files.py --executable --files-only
  
  # Find in specific directories with depth limit
  find_files.py src/ tests/ --max-depth 3
  
  # Complex search: Java files >1KB, modified in last week
  find_files.py --ext java --min-size 1KB --newer-than 1w --long
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('paths', nargs='*', default=['.'],
                       help='Paths to search (default: current directory)')
    
    # Name/pattern filters
    parser.add_argument('--name', '-n', help='Filename pattern (supports wildcards)')
    parser.add_argument('--regex', '-r', help='Filename regex pattern')
    parser.add_argument('--ext', help='File extension(s) - comma separated')
    # Type filters
    parser.add_argument('--files-only', '-f', action='store_true',
                       help='Find only files')
    parser.add_argument('--dirs-only', '-d', action='store_true',
                       help='Find only directories')
    
    # Size filters
    parser.add_argument('--min-size', help='Minimum file size (e.g., "1MB")')
    parser.add_argument('--max-size', help='Maximum file size (e.g., "100KB")')
    
    # Time filters
    parser.add_argument('--newer-than', help='Modified within timeframe (e.g., "2d", "3h")')
    parser.add_argument('--older-than', help='Modified before timeframe (e.g., "1w")')
    
    # Permission filters
    parser.add_argument('--executable', '-x', action='store_true',
                       help='Find executable files')
    parser.add_argument('--readable', action='store_true',
                       help='Find readable files')
    parser.add_argument('--writable', action='store_true',
                       help='Find writable files')
    
    # Traversal options
    parser.add_argument('--all', '-a', action='store_true',
                       help='Include hidden files and directories')
    parser.add_argument('--include-build', action='store_true',
                       help='Include build/cache directories')
    
    parser.add_argument('--max-depth', type=int, help='Maximum directory depth to search')
    parser.add_argument('--long', '-l', action='store_true', help='Long format with details')
    parser.add_argument('--ignore-case', action='store_true', help='Case-insensitive search')

    # Output options
    parser.add_argument('--size-info', '-s', action='store_true',
                       help='Show file sizes')
    parser.add_argument('--summary', action='store_true',
                       help='Show summary statistics')
    parser.add_argument('--limit', '--max', type=int, dest='limit',
                       help='Limit number of results (--max is an alias)')
    
    args = parser.parse_args()
    
    # Apply configuration defaults
    apply_config_to_args('find_files', args, parser)
    
    try:
        # Convert paths to Path objects
        search_paths = [Path(p).resolve() for p in args.paths]
        
        # Find files
        files = list(find_files(search_paths, args))
        
        # Sort files by path for consistent output
        files.sort(key=lambda f: f['path'])
        
        # Format and output
        output = format_output(files, args)
        print(output)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()