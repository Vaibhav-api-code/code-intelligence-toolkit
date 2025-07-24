#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Find recently modified/created files with smart filtering.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import stat

# Load common configuration system
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    # Graceful fallback if common_config is not available
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"

def get_time_ago_str(dt: datetime) -> str:
    """Get human readable 'time ago' string."""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return f"{diff.seconds}s ago"

def should_skip_directory(dir_path: Path, args) -> bool:
    """Check if directory should be skipped."""
    dir_name = dir_path.name
    
    # Skip hidden directories unless --all is specified
    if not args.all and dir_name.startswith('.'):
        return True
    
    # Skip common build/cache directories
    skip_dirs = {
        '__pycache__', '.git', '.svn', '.hg', '.bzr',
        'node_modules', 'target', 'build', 'dist', '.gradle',
        '.idea', '.vscode', '.settings', 'bin', 'obj',
        '.tox', '.coverage', '.pytest_cache', '.mypy_cache'
    }
    if dir_name in skip_dirs:
        return True
    
    return False

def get_file_info(file_path: Path) -> Optional[Dict]:
    """Get comprehensive file information."""
    try:
        stat_info = file_path.stat()
        
        mtime = datetime.fromtimestamp(stat_info.st_mtime)
        ctime = datetime.fromtimestamp(stat_info.st_ctime)
        
        # Use the more recent of mtime or ctime
        recent_time = max(mtime, ctime)
        
        return {
            'path': str(file_path),
            'name': file_path.name,
            'size': stat_info.st_size,
            'size_formatted': format_size(stat_info.st_size),
            'mtime': mtime,
            'ctime': ctime,
            'recent_time': recent_time,
            'time_ago': get_time_ago_str(recent_time),
            'mtime_formatted': mtime.strftime('%Y-%m-%d %H:%M:%S'),
            'ctime_formatted': ctime.strftime('%Y-%m-%d %H:%M:%S'),
            'recent_formatted': recent_time.strftime('%Y-%m-%d %H:%M:%S'),
            'is_dir': file_path.is_dir(),
            'is_file': file_path.is_file(),
            'extension': file_path.suffix.lower(),
            'parent': str(file_path.parent)
        }
    except (OSError, PermissionError):
        return None

def find_recent_files(search_paths: List[Path], since: datetime, args) -> List[Dict]:
    """Find files modified since the given datetime."""
    found_files = []
    
    for search_path in search_paths:
        if not search_path.exists():
            print(f"Warning: Path '{search_path}' does not exist", file=sys.stderr)
            continue
        
        if search_path.is_file():
            # Single file
            file_info = get_file_info(search_path)
            if file_info and file_info['recent_time'] >= since:
                found_files.append(file_info)
        else:
            # Directory traversal
            try:
                for root, dirs, files in os.walk(search_path):
                    root_path = Path(root)
                    
                    # Skip directories
                    dirs[:] = [d for d in dirs if not should_skip_directory(root_path / d, args)]
                    
                    # Respect max depth
                    if args.max_depth is not None:
                        current_depth = len(root_path.relative_to(search_path).parts)
                        if current_depth >= args.max_depth:
                            dirs.clear()
                    
                    # Process files
                    for file_name in files:
                        file_path = root_path / file_name
                        
                        # Skip hidden files unless --all
                        if not args.all and file_name.startswith('.'):
                            continue
                        
                        # Skip by extension if specified
                        if args.exclude_ext:
                            exclude_exts = [ext.strip().lower() for ext in args.exclude_ext.split(',')]
                            file_ext = file_path.suffix.lower().lstrip('.')
                            if file_ext in exclude_exts:
                                continue
                        
                        # Include only specific extensions if specified
                        if args.ext:
                            include_exts = [ext.strip().lower() for ext in args.ext.split(',')]
                            file_ext = file_path.suffix.lower().lstrip('.')
                            if file_ext not in include_exts:
                                continue
                        
                        file_info = get_file_info(file_path)
                        if file_info and file_info['recent_time'] >= since:
                            found_files.append(file_info)
                            
            except PermissionError:
                print(f"Warning: Permission denied accessing '{search_path}'", file=sys.stderr)
                continue
    
    return found_files

def format_output(files: List[Dict], args) -> str:
    """Format the output."""
    if not files:
        time_desc = args.since if hasattr(args, 'since') else "specified time"
        return f"🕒 No recent files found since {time_desc}"
    
    output = []
    
    if args.by_dir:
        # Group by directory
        by_directory = {}
        for file_info in files:
            parent = file_info['parent']
            if parent not in by_directory:
                by_directory[parent] = []
            by_directory[parent].append(file_info)
        
        output.append(f"🕒 RECENT FILES BY DIRECTORY ({len(files)} total)")
        output.append("=" * 80)
        
        for directory in sorted(by_directory.keys()):
            dir_files = by_directory[directory]
            output.append(f"\n📁 {directory} ({len(dir_files)} files)")
            output.append("-" * 50)
            
            for file_info in sorted(dir_files, key=lambda f: f['recent_time'], reverse=True):
                name = file_info['name']
                time_ago = file_info['time_ago']
                size = file_info['size_formatted']
                
                if args.show_size:
                    output.append(f"   📄 {name} ({size}) - {time_ago}")
                else:
                    output.append(f"   📄 {name} - {time_ago}")
    
    elif args.detailed:
        # Detailed format
        output.append(f"🕒 RECENT FILES DETAILED ({len(files)} files)")
        output.append("=" * 80)
        
        for file_info in files:
            path = file_info['path']
            size = file_info['size_formatted']
            mtime_formatted = file_info['mtime_formatted']
            time_ago = file_info['time_ago']
            
            output.append(f"📄 {path}")
            output.append(f"   Size: {size}")
            output.append(f"   Modified: {mtime_formatted} ({time_ago})")
            output.append("")
    
    else:
        # Simple format (default)
        output.append(f"🕒 RECENT FILES ({len(files)} files)")
        output.append("-" * 50)
        
        for file_info in files:
            path = file_info['path']
            time_ago = file_info['time_ago']
            
            if args.show_size:
                size = file_info['size_formatted']
                output.append(f"📄 {path} ({size}) - {time_ago}")
            else:
                output.append(f"📄 {path} - {time_ago}")
    
    # Summary
    if args.summary:
        total_size = sum(f['size'] for f in files)
        extensions = {}
        for f in files:
            ext = f['extension'] or 'no extension'
            extensions[ext] = extensions.get(ext, 0) + 1
        
        output.append("")
        output.append("📊 SUMMARY")
        output.append(f"   Total files: {len(files)}")
        output.append(f"   Total size: {format_size(total_size)}")
        output.append(f"   Most common extensions:")
        
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:5]:
            output.append(f"     {ext}: {count} files")
    
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(
        description='Find recently modified/created files',
        epilog='''
EXAMPLES:
  # Files modified in last hour
  recent_files.py --since 1h
  
  # Files modified today
  recent_files.py --since 1d
  
  # Recent Python files with details
  recent_files.py --since 2h --ext py --detailed
  
  # Recent files grouped by directory
  recent_files.py --since 4h --by-dir --show-size
  
  # Last week's work excluding build files
  recent_files.py --since 1w --exclude-ext "class,jar,pyc"
  
  # Search specific directories
  recent_files.py src/ tests/ --since 2d --summary
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('paths', nargs='*', default=['.'],
                       help='Paths to search (default: current directory)')
    
    # Time options
    parser.add_argument('--since', '-s', default='1h',
                       help='Time threshold (e.g., "2h", "1d", "3w") (default: 1h)')
    
    # Filter options
    parser.add_argument('--ext', help='Include only these extensions (comma-separated)')
    parser.add_argument('--exclude-ext', help='Exclude these extensions (comma-separated)')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Include hidden files')
    parser.add_argument('--max-depth', type=int,
                       help='Maximum directory depth to search')
    
    # Output options
    parser.add_argument('--detailed', '-l', action='store_true',
                       help='Show detailed information')
    parser.add_argument('--by-dir', action='store_true',
                       help='Group results by directory')
    parser.add_argument('--show-size', action='store_true',
                       help='Show file sizes')
    parser.add_argument('--summary', action='store_true',
                       help='Show summary statistics')
    parser.add_argument('--limit', type=int, default=100,
                       help='Limit number of results (default: 100)')
    
    args = parser.parse_args()
    
    # Apply configuration defaults
    apply_config_to_args('recent_files', args, parser)
    
    try:
        # Parse time threshold
        time_str = args.since.lower().strip()
        
        multipliers = {
            's': 1,          # seconds
            'm': 60,         # minutes
            'h': 3600,       # hours
            'd': 86400,      # days
            'w': 604800,     # weeks
        }
        
        # Parse time
        delta_seconds = 0
        for suffix, seconds in multipliers.items():
            if time_str.endswith(suffix):
                try:
                    number = float(time_str[:-1])
                    delta_seconds = number * seconds
                    break
                except ValueError:
                    pass
        
        if delta_seconds == 0:
            try:
                delta_seconds = float(time_str) * 86400  # Default to days
            except ValueError:
                print(f"Error: Could not parse time '{args.since}'", file=sys.stderr)
                sys.exit(1)
        
        since = datetime.now() - timedelta(seconds=delta_seconds)
        
        # Convert paths
        search_paths = [Path(p).resolve() for p in args.paths]
        
        # Find recent files
        files = find_recent_files(search_paths, since, args)
        
        # Sort by most recent first
        files.sort(key=lambda f: f['recent_time'], reverse=True)
        
        # Apply limit
        if args.limit:
            files = files[:args.limit]
        
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