#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Smart directory listing tool with enhanced filtering and formatting.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
import stat
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import fnmatch

# Load common configuration system

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
    from common_config import load_config, apply_config_to_args
except ImportError:
    # Graceful fallback if common_config is not available
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass

# Import pre-flight checks
try:
    from preflight_checks import PreflightChecker, run_preflight_checks
except ImportError:
    PreflightChecker = None
    run_preflight_checks = None

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"

def get_file_type_icon(path: Path) -> str:
    """Get emoji icon for file type."""
    if path.is_dir():
        return "📁"
    
    suffix = path.suffix.lower()
    
    # Programming files
    if suffix in ['.py', '.pyw']:
        return "🐍"
    elif suffix in ['.java', '.class']:
        return "☕"
    elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
        return "🟨"
    elif suffix in ['.html', '.htm']:
        return "🌐"
    elif suffix in ['.css', '.scss', '.sass']:
        return "🎨"
    elif suffix in ['.json', '.yaml', '.yml', '.toml']:
        return "⚙️"
    elif suffix in ['.md', '.txt', '.rst']:
        return "📄"
    elif suffix in ['.xml', '.xsd', '.xsl']:
        return "📋"
    
    # Build/config files
    elif suffix in ['.gradle', '.maven', '.pom']:
        return "🔧"
    elif suffix in ['.jar', '.war', '.zip', '.tar', '.gz']:
        return "📦"
    elif suffix in ['.sh', '.bat', '.cmd']:
        return "⚡"
    
    # Data files
    elif suffix in ['.csv', '.tsv']:
        return "📊"
    elif suffix in ['.sql', '.db', '.sqlite']:
        return "🗄️"
    elif suffix in ['.log']:
        return "📜"
    
    # Media files
    elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.svg']:
        return "🖼️"
    elif suffix in ['.mp4', '.avi', '.mov', '.mkv']:
        return "🎬"
    elif suffix in ['.mp3', '.wav', '.flac']:
        return "🎵"
    
    # Documents
    elif suffix in ['.pdf']:
        return "📕"
    elif suffix in ['.doc', '.docx']:
        return "📘"
    elif suffix in ['.xls', '.xlsx']:
        return "📗"
    
    else:
        return "📄"

def get_file_info(path: Path) -> Dict:
    """Get comprehensive file information."""
    try:
        stat_info = path.stat()
        
        # Permissions
        mode = stat_info.st_mode
        permissions = stat.filemode(mode)
        
        # Times
        mtime = datetime.fromtimestamp(stat_info.st_mtime)
        
        # File type detection
        is_symlink = path.is_symlink()
        is_executable = os.access(path, os.X_OK)
        
        return {
            'name': path.name,
            'path': str(path),
            'size': stat_info.st_size,
            'size_formatted': format_size(stat_info.st_size),
            'mtime': mtime,
            'mtime_formatted': mtime.strftime('%Y-%m-%d %H:%M'),
            'permissions': permissions,
            'is_dir': path.is_dir(),
            'is_file': path.is_file(),
            'is_symlink': is_symlink,
            'is_executable': is_executable,
            'is_hidden': path.name.startswith('.'),
            'icon': get_file_type_icon(path),
            'suffix': path.suffix.lower()
        }
    except (OSError, PermissionError) as e:
        return {
            'name': path.name,
            'path': str(path),
            'error': str(e),
            'icon': "❌"
        }

def filter_files(files: List[Dict], args) -> List[Dict]:
    """Apply filters to file list."""
    filtered = files
    
    # Hidden files filter
    # Use 'all' from standard parser (all_files)
    show_all = getattr(args, 'all', False) or getattr(args, 'all_files', False)
    if not show_all:
        filtered = [f for f in filtered if not f.get('is_hidden', False)]
    
    # Type filters
    if args.dirs_only:
        filtered = [f for f in filtered if f.get('is_dir', False)]
    elif args.files_only:
        filtered = [f for f in filtered if f.get('is_file', False)]
    
    # Pattern filter
    if args.pattern:
        filtered = [f for f in filtered if fnmatch.fnmatch(f['name'], args.pattern)]
    
    # Extension filter (only apply to files, not directories)
    # Use ext from standard parser (ext_filter)
    ext_filter = getattr(args, 'ext', None) or getattr(args, 'ext_filter', None)
    if ext_filter and ext_filter.strip():  # Check for non-empty extension
        ext = ext_filter if ext_filter.startswith('.') else f'.{ext_filter}'
        filtered = [f for f in filtered if f.get('is_dir', False) or f.get('suffix') == ext.lower()]
    
    # Size filters
    if args.min_size:
        min_bytes = parse_size(args.min_size)
        filtered = [f for f in filtered if f.get('size', 0) >= min_bytes]
    
    if args.max_size:
        max_bytes = parse_size(args.max_size)
        filtered = [f for f in filtered if f.get('size', 0) <= max_bytes]
    
    return filtered

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
    
    # Try parsing as plain number (assume bytes)
    try:
        return int(size_str)
    except ValueError:
        print(f"Warning: Could not parse size '{size_str}', ignoring", file=sys.stderr)
        return 0

def sort_files(files: List[Dict], sort_by: str, reverse: bool = False) -> List[Dict]:
    """Sort files by specified criteria."""
    if sort_by == 'name':
        key_func = lambda f: f['name'].lower()
    elif sort_by == 'size':
        key_func = lambda f: f.get('size', 0)
    elif sort_by == 'time':
        key_func = lambda f: f.get('mtime', datetime.min)
    elif sort_by == 'ext':
        key_func = lambda f: f.get('suffix', '')
    else:
        key_func = lambda f: f['name'].lower()  # Default to name
    
    # Sort directories first, then files (unless sorting by size/time)
    if sort_by in ['name', 'ext']:
        return sorted(files, key=lambda f: (not f.get('is_dir', False), key_func(f)), reverse=reverse)
    else:
        return sorted(files, key=key_func, reverse=reverse)

def format_output(files: List[Dict], args) -> str:
    """Format output based on requested style."""
    if not files:
        return "📭 Directory is empty"
    
    output = []
    
    # Use 'long' from standard parser (long_format)
    long_format = getattr(args, 'long', False) or getattr(args, 'long_format', False)
    if long_format:
        # Long format with detailed info
        output.append("📂 DETAILED LISTING")
        output.append("=" * 80)
        
        for file_info in files:
            if 'error' in file_info:
                output.append(f"❌ {file_info['name']} - Error: {file_info['error']}")
                continue
            
            icon = file_info['icon']
            name = file_info['name']
            size = file_info['size_formatted']
            mtime = file_info['mtime_formatted']
            perms = file_info['permissions']
            
            # Special markers
            markers = []
            if file_info.get('is_symlink'):
                markers.append("🔗")
            if file_info.get('is_executable') and file_info.get('is_file'):
                markers.append("⚡")
            
            marker_str = "".join(markers)
            
            output.append(f"{icon} {perms} {size:>8} {mtime} {name}{marker_str}")
    
    elif args.grid:
        # Grid format (like ls -l but compact)
        output.append("📂 GRID VIEW")
        output.append("=" * 60)
        
        max_name_len = max(len(f['name']) for f in files) if files else 10
        cols = max(1, 80 // (max_name_len + 3))
        
        for i in range(0, len(files), cols):
            row_files = files[i:i+cols]
            row = []
            for file_info in row_files:
                icon = file_info['icon']
                name = file_info['name'][:max_name_len]
                row.append(f"{icon}{name:<{max_name_len}}")
            output.append("  ".join(row))
    
    else:
        # Simple format (default)
        output.append(f"📂 LISTING ({len(files)} items)")
        output.append("-" * 40)
        
        for file_info in files:
            if 'error' in file_info:
                output.append(f"❌ {file_info['name']} - Error: {file_info['error']}")
                continue
            
            icon = file_info['icon']
            name = file_info['name']
            
            # Add size for files
            if file_info.get('is_file'):
                size = file_info['size_formatted']
                output.append(f"{icon} {name} ({size})")
            else:
                output.append(f"{icon} {name}")
    
    # Summary
    if args.summary:
        total_files = sum(1 for f in files if f.get('is_file'))
        total_dirs = sum(1 for f in files if f.get('is_dir'))
        total_size = sum(f.get('size', 0) for f in files if f.get('is_file'))
        
        output.append("")
        output.append("📊 SUMMARY")
        output.append(f"   Files: {total_files}")
        output.append(f"   Directories: {total_dirs}")
        output.append(f"   Total size: {format_size(total_size)}")
    
    return "\n".join(output)

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('Smart directory listing with enhanced filtering and formatting')
    else:
        parser = argparse.ArgumentParser(description='Smart directory listing with enhanced filtering and formatting')
        # Add path argument for fallback case
        parser.add_argument('path', nargs='?', default='.', 
                           help='Directory to list (default: current)')
    
    # Display options
    parser.add_argument('--summary', action='store_true',
                       help='Show summary statistics')
    
    # Filtering options
    parser.add_argument('--pattern', help='Filter by filename pattern (e.g., "*.py")')
    parser.add_argument('--dirs-only', action='store_true',
                       help='Show only directories')
    parser.add_argument('--files-only', action='store_true',
                       help='Show only files')
    parser.add_argument('--min-size', help='Minimum file size (e.g., "1MB")')
    parser.add_argument('--max-size', help='Maximum file size (e.g., "100KB")')
    
    # Sorting options
    parser.add_argument('--reverse', action='store_true',
                       help='Reverse sort order')
    
    # Grid layout option
    parser.add_argument('--grid', action='store_true',
                       help='Display in grid format')
    
    args = parser.parse_args()
    
    # Apply configuration defaults
    apply_config_to_args('smart_ls', args, parser)
    
    try:
        # Validate path using pre-flight checks if available
        path = Path(args.path).resolve()
        
        if PreflightChecker and run_preflight_checks:
            # Use pre-flight checks
            run_preflight_checks([
                (PreflightChecker.check_path_exists, (args.path, "path")),
                (PreflightChecker.check_directory_accessible, (args.path,))
            ])
        else:
            # Fallback to original validation
            if not path.exists():
                print(f"Error: Path '{args.path}' does not exist", file=sys.stderr)
                sys.exit(1)
            
            if not path.is_dir():
                print(f"Error: Path '{args.path}' is not a directory", file=sys.stderr)
                sys.exit(1)
        
        # Get file list
        try:
            items = list(path.iterdir())
        except PermissionError:
            print(f"Error: Permission denied accessing '{path}'", file=sys.stderr)
            sys.exit(1)
        
        # Get file info
        files = [get_file_info(item) for item in items]
        
        # Apply filters
        files = filter_files(files, args)
        
        # Sort files
        # Use 'sort' from standard parser (sort_order)  
        sort_order = getattr(args, 'sort', 'name') or getattr(args, 'sort_order', 'name')
        files = sort_files(files, sort_order, args.reverse)
        
        # Limit results
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