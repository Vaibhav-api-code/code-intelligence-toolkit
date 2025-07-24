#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
recent_files v2 - Find recently modified files with standardized interface.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import fnmatch

# Import standard parser

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

def parse_time_spec(time_spec: str) -> datetime:
    """Parse time specification like '2h', '3d', '1w' into datetime."""
    if not time_spec:
        return datetime.now() - timedelta(hours=24)  # Default: 24h
    
    time_spec = time_spec.lower().strip()
    
    # Extract number and unit
    import re
    match = re.match(r'^(\d+)([hdwmy]?)$', time_spec)
    if not match:
        raise ValueError(f"Invalid time format: {time_spec}. Use format like '2h', '3d', '1w'")
    
    amount = int(match.group(1))
    unit = match.group(2) or 'h'  # Default to hours
    
    # Convert to timedelta
    if unit == 'h':
        delta = timedelta(hours=amount)
    elif unit == 'd':
        delta = timedelta(days=amount)
    elif unit == 'w':
        delta = timedelta(weeks=amount)
    elif unit == 'm':
        delta = timedelta(days=amount * 30)  # Approximate
    elif unit == 'y':
        delta = timedelta(days=amount * 365)  # Approximate
    else:
        raise ValueError(f"Unknown time unit: {unit}")
    
    return datetime.now() - delta

def find_recent_files(args) -> List[Dict]:
    """Find files modified after the specified time."""
    # Parse time specification
    since_time = parse_time_spec(args.since)
    
    # Determine search path
    search_path = Path(args.path) if hasattr(args, 'path') and args.path else Path('.')
    
    if not search_path.exists():
        raise ValueError(f"Path does not exist: {search_path}")
    
    recent_files = []
    
    # Walk directory
    for root, dirs, files in os.walk(search_path):
        # Limit depth if specified
        if args.max_depth:
            current_depth = len(Path(root).relative_to(search_path).parts)
            if current_depth >= args.max_depth:
                dirs.clear()
                continue
        
        # Skip hidden directories unless explicitly requested
        if not getattr(args, 'all', False):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in files:
            # Skip hidden files unless requested
            if not getattr(args, 'all', False) and filename.startswith('.'):
                continue
            
            file_path = Path(root) / filename
            
            try:
                # Get file stats
                stat = file_path.stat()
                
                # Check modification time
                mod_time = datetime.fromtimestamp(stat.st_mtime)
                if mod_time < since_time:
                    continue
                
                # Apply glob filter if specified
                if args.glob:
                    if not fnmatch.fnmatch(filename, args.glob):
                        continue
                
                # Apply exclude filter
                if hasattr(args, 'exclude') and args.exclude:
                    if fnmatch.fnmatch(filename, args.exclude):
                        continue
                
                recent_files.append({
                    'path': str(file_path),
                    'name': filename,
                    'size': stat.st_size,
                    'modified': mod_time,
                    'modified_timestamp': stat.st_mtime,
                    'directory': str(Path(root)),
                    'relative_path': str(file_path.relative_to(search_path))
                })
                
            except (OSError, PermissionError):
                # Skip files we can't access
                continue
    
    return recent_files

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB"

def format_time_ago(mod_time: datetime) -> str:
    """Format how long ago a file was modified."""
    now = datetime.now()
    delta = now - mod_time
    
    if delta.days > 0:
        return f"{delta.days}d ago"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours}h ago"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes}m ago"
    else:
        return "just now"

def display_results(files: List[Dict], args) -> None:
    """Display the results in requested format."""
    if not files:
        if not args.quiet:
            print("No recent files found")
        return
    
    # Sort files by modification time (newest first)
    files.sort(key=lambda x: x['modified_timestamp'], reverse=True)
    
    # Apply limit if specified
    if hasattr(args, 'limit') and args.limit and args.limit > 0:
        files = files[:args.limit]
    
    if args.json:
        import json
        output = {
            'search_path': getattr(args, 'path', '.'),
            'since': args.since,
            'total_files': len(files),
            'files': files
        }
        print(json.dumps(output, indent=2, default=str))
        return
    
    # Text output
    if not args.quiet:
        print(f"📅 Recent files (modified within {args.since})")
        print(f"Found {len(files)} files")
        print()
    
    if getattr(args, 'by_dir', False):
        # Group by directory
        by_dir = {}
        for file_info in files:
            dir_path = file_info['directory']
            if dir_path not in by_dir:
                by_dir[dir_path] = []
            by_dir[dir_path].append(file_info)
        
        for dir_path in sorted(by_dir.keys()):
            print(f"📁 {dir_path}/")
            dir_files = sorted(by_dir[dir_path], key=lambda x: x['modified_timestamp'], reverse=True)
            for file_info in dir_files:
                time_str = format_time_ago(file_info['modified'])
                if getattr(args, 'show_size', False):
                    size_str = format_size(file_info['size'])
                    print(f"   {file_info['name']:<30} {size_str:>8} {time_str}")
                else:
                    print(f"   {file_info['name']:<30} {time_str}")
            print()
    
    else:
        # Simple list
        for file_info in files:
            time_str = format_time_ago(file_info['modified'])
            
            if getattr(args, 'long', False):
                size_str = format_size(file_info['size'])
                print(f"{file_info['relative_path']:<50} {size_str:>8} {time_str}")
            elif getattr(args, 'show_size', False):
                size_str = format_size(file_info['size'])
                print(f"{file_info['name']:<30} {size_str:>8} {time_str}")
            else:
                print(f"{file_info['relative_path']:<50} {time_str}")

def main():
    if HAS_STANDARD_PARSER:
        parser = create_standard_parser(
            'directory',
            'recent_files v2 - Find recently modified files',
            epilog='''
EXAMPLES:
  recent_files.py --since 4h --limit 10           # Last 10 files from 4h
  recent_files.py --since 2d ~/project            # Files in project, last 2 days  
  recent_files.py --since 1d --glob "*.py"        # Python files modified today  
  recent_files.py --since 1w --by-dir             # Group by directory  
  recent_files.py --since 6h --json --max 5       # JSON output, limit 5 results
TIME FORMATS:
  2h, 4h    - Hours ago
  1d, 3d    - Days ago  
  1w, 2w    - Weeks ago
  1m        - Month ago (approximate)
            '''
        )
    else:
        parser = argparse.ArgumentParser(description='recent_files v2 - Find recently modified files')
    
    # Add arguments specific to recent_files that aren't in standard parser
    if not HAS_STANDARD_PARSER:
        # Add all arguments if we don't have standard parser
        parser.add_argument('path', nargs='?', default='.',
                           help='Directory to search (default: current)')
    # Time specification (required) - specific to this tool
    parser.add_argument('--since', required=True,
                       help='Find files modified since (e.g., 2h, 3d, 1w)')
    
    # Display options - specific to this tool
    parser.add_argument('--by-dir', action='store_true',
                       help='Group files by directory')
    parser.add_argument('--show-size', action='store_true',
                       help='Show file sizes')
    parser.add_argument('--limit', '--max', dest='limit', type=int,
                       help='Limit number of results shown')
    
    args = parser.parse_args()
    
    # Apply configuration
    apply_config_to_args('recent_files', args, parser)
    
    try:
        # Find recent files
        if getattr(args, 'verbose', False):
            print(f"Searching for files modified since {args.since}...", file=sys.stderr)
        
        recent_files = find_recent_files(args)
        
        # Display results
        display_results(recent_files, args)
        
    except KeyboardInterrupt:
        print("\\nSearch interrupted", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()