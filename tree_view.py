#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Directory tree visualization with smart filtering and customization.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Set
import fnmatch

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

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"

def get_file_icon(path: Path) -> str:
    """Get appropriate icon for file/directory."""
    if path.is_dir():
        # Special directory icons
        name = path.name.lower()
        if name in ['src', 'source']:
            return "📦"
        elif name in ['test', 'tests']:
            return "🧪"
        elif name in ['doc', 'docs', 'documentation']:
            return "📚"
        elif name in ['config', 'configuration', 'conf']:
            return "⚙️"
        elif name in ['build', 'dist', 'target']:
            return "🏗️"
        elif name in ['.git', '.svn', '.hg']:
            return "🔗"
        elif name.startswith('.'):
            return "🔸"
        else:
            return "📁"
    
    # File icons based on extension
    suffix = path.suffix.lower()
    
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
    elif suffix in ['.json', '.yaml', '.yml']:
        return "⚙️"
    elif suffix in ['.md', '.txt', '.rst']:
        return "📄"
    elif suffix in ['.xml', '.xsd']:
        return "📋"
    elif suffix in ['.gradle', '.maven']:
        return "🔧"
    elif suffix in ['.jar', '.war', '.zip']:
        return "📦"
    elif suffix in ['.sh', '.bat']:
        return "⚡"
    elif suffix in ['.log']:
        return "📜"
    elif suffix in ['.jpg', '.png', '.gif']:
        return "🖼️"
    else:
        return "📄"

def should_skip_path(path: Path, args) -> bool:
    """Check if path should be skipped based on filters."""
    name = path.name
    
    # Hidden files/directories
    if not args.all and name.startswith('.'):
        return True
    
    # Build/cache directories
    if not args.include_build:
        skip_dirs = {
            '__pycache__', '.git', '.svn', '.hg', '.bzr',
            'node_modules', 'target', 'build', 'dist', '.gradle',
            '.idea', '.vscode', '.settings', 'bin', 'obj',
            '.tox', '.coverage', '.pytest_cache', '.mypy_cache'
        }
        if path.is_dir() and name in skip_dirs:
            return True
    
    # Pattern filters
    if args.ignore_pattern:
        patterns = [p.strip() for p in args.ignore_pattern.split(',')]
        if any(fnmatch.fnmatch(name, pattern) for pattern in patterns):
            return True
    
    if args.only_pattern:
        patterns = [p.strip() for p in args.only_pattern.split(',')]
        if not any(fnmatch.fnmatch(name, pattern) for pattern in patterns):
            return True
    
    # Extension filters for files
    if path.is_file():
        if args.ext:
            extensions = [ext.strip().lower() for ext in args.ext.split(',')]
            file_ext = path.suffix.lower().lstrip('.')
            if file_ext not in extensions:
                return True
    
    return False

def get_directory_stats(path: Path, args) -> Dict:
    """Get statistics for a directory."""
    stats = {
        'total_files': 0,
        'total_dirs': 0,
        'total_size': 0,
        'file_types': {}
    }
    
    try:
        for item in path.iterdir():
            if should_skip_path(item, args):
                continue
            
            if item.is_dir():
                stats['total_dirs'] += 1
            elif item.is_file():
                stats['total_files'] += 1
                try:
                    size = item.stat().st_size
                    stats['total_size'] += size
                    
                    ext = item.suffix.lower() or 'no extension'
                    stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                except (OSError, PermissionError):
                    pass
    
    except PermissionError:
        pass
    
    return stats

def build_tree(path: Path, args, current_depth: int = 0, prefix: str = "", is_last: bool = True) -> List[str]:
    """Recursively build the tree structure."""
    lines = []
    
    # Check depth limit
    if args.max_depth is not None and current_depth >= args.max_depth:
        return lines
    
    try:
        # Get and sort directory contents
        items = []
        for item in path.iterdir():
            if not should_skip_path(item, args):
                items.append(item)
        
        # Sort: directories first, then files, alphabetically
        items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        
        # Limit items if specified
        if args.limit and len(items) > args.limit:
            items = items[:args.limit]
            truncated = True
        else:
            truncated = False
        
        for i, item in enumerate(items):
            is_last_item = (i == len(items) - 1) and not truncated
            
            # Build the line
            if current_depth == 0:
                line_prefix = ""
                child_prefix = ""
            else:
                line_prefix = prefix + ("└── " if is_last_item else "├── ")
                child_prefix = prefix + ("    " if is_last_item else "│   ")
            
            # Get item info
            icon = get_file_icon(item)
            name = item.name
            
            # Add size info if requested
            size_info = ""
            if args.show_size and item.is_file():
                try:
                    size = item.stat().st_size
                    size_info = f" ({format_size(size)})"
                except (OSError, PermissionError):
                    pass
            
            # Add directory stats if requested
            dir_info = ""
            if args.show_stats and item.is_dir():
                stats = get_directory_stats(item, args)
                if stats['total_files'] > 0 or stats['total_dirs'] > 0:
                    dir_info = f" [{stats['total_files']}f, {stats['total_dirs']}d]"
            
            line = f"{line_prefix}{icon} {name}{size_info}{dir_info}"
            lines.append(line)
            
            # Recurse into directories
            if item.is_dir() and (args.dirs_only or True):
                child_lines = build_tree(item, args, current_depth + 1, child_prefix, is_last_item)
                lines.extend(child_lines)
        
        # Show truncation indicator
        if truncated:
            if current_depth == 0:
                trunc_prefix = ""
            else:
                trunc_prefix = prefix + "└── "
            lines.append(f"{trunc_prefix}... ({len(list(path.iterdir())) - args.limit} more items)")
    
    except PermissionError:
        if current_depth > 0:
            line_prefix = prefix + ("└── " if is_last else "├── ")
            lines.append(f"{line_prefix}❌ Permission denied")
    
    return lines

def format_output(root_path: Path, tree_lines: List[str], args) -> str:
    """Format the complete output."""
    output = []
    
    # Header
    if args.show_stats:
        root_stats = get_directory_stats(root_path, args)
        output.append(f"🌳 TREE VIEW: {root_path}")
        output.append(f"📊 {root_stats['total_files']} files, {root_stats['total_dirs']} directories")
        if root_stats['total_size'] > 0:
            output.append(f"💾 Total size: {format_size(root_stats['total_size'])}")
    else:
        output.append(f"🌳 {root_path}")
    
    output.append("=" * 60)
    
    # Root directory
    root_icon = get_file_icon(root_path)
    output.append(f"{root_icon} {root_path.name}/")
    
    # Tree structure
    output.extend(tree_lines)
    
    # Summary
    if args.summary:
        total_lines = len([line for line in tree_lines if not line.strip().startswith('...')])
        output.append("")
        output.append(f"📈 Displayed {total_lines} items")
        
        if args.max_depth is not None:
            output.append(f"🔢 Max depth: {args.max_depth}")
    
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(
        description='Directory tree visualization with smart filtering',
        epilog='''
EXAMPLES:
  # Basic tree view
  tree_view.py
  
  # Limit depth and show sizes
  tree_view.py --max-depth 3 --show-size
  
  # Show only Python files
  tree_view.py --ext py --files-only
  
  # Include hidden files and build dirs
  tree_view.py --all --include-build
  
  # Show directory statistics
  tree_view.py --show-stats --summary
  
  # Custom patterns
  tree_view.py --only-pattern "*.java,*.py" --max-depth 2
  
  # Large directories with limits
  tree_view.py --limit 10 --show-stats
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('path', nargs='?', default='.',
                       help='Directory to show tree for (default: current)')
    
    # Depth and limits
    parser.add_argument('--max-depth', type=int, help='Maximum directory depth to search')
    parser.add_argument('--limit', '-l', '--max', type=int, dest='limit',
                       help='Limit items per directory (--max is an alias)')
    
    # Content filters
    parser.add_argument('--all', '-a', action='store_true',
                       help='Include hidden files and directories')
    parser.add_argument('--include-build', action='store_true',
                       help='Include build/cache directories')
    parser.add_argument('--dirs-only', action='store_true',
                       help='Show only directories')
    parser.add_argument('--files-only', action='store_true',
                       help='Show only files (and their parent dirs)')
    
    # Pattern filters
    parser.add_argument('--ext', help='Show only files with these extensions (comma-separated)')
    parser.add_argument('--only-pattern', help='Show only items matching patterns (comma-separated)')
    parser.add_argument('--ignore-pattern', help='Ignore items matching patterns (comma-separated)')
    
    # Display options
    parser.add_argument('--show-size', '-s', action='store_true',
                       help='Show file sizes')
    parser.add_argument('--show-stats', action='store_true',
                       help='Show directory statistics')
    parser.add_argument('--summary', action='store_true',
                       help='Show summary information')
    
    args = parser.parse_args()
    
    # Apply configuration defaults
    apply_config_to_args('tree_view', args, parser)
    
    try:
        # Validate path
        root_path = Path(args.path).resolve()
        if not root_path.exists():
            print(f"Error: Path '{args.path}' does not exist", file=sys.stderr)
            sys.exit(1)
        
        if not root_path.is_dir():
            print(f"Error: Path '{args.path}' is not a directory", file=sys.stderr)
            sys.exit(1)
        
        # Build tree
        tree_lines = build_tree(root_path, args)
        
        # Format output
        output = format_output(root_path, tree_lines, args)
        print(output)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()