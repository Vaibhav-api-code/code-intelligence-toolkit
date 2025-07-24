#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Directory analysis tool for comprehensive statistics and insights.

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
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
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
    
    if not args.all and dir_name.startswith('.'):
        return True
    
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

def analyze_directory(path: Path, args) -> Dict:
    """Perform comprehensive directory analysis."""
    stats = {
        'total_files': 0,
        'total_dirs': 0,
        'total_size': 0,
        'file_sizes': [],
        'file_types': Counter(),
        'dir_sizes': defaultdict(int),
        'largest_files': [],
        'smallest_files': [],
        'newest_files': [],
        'oldest_files': [],
        'empty_dirs': [],
        'large_dirs': [],
        'file_age_distribution': {
            'last_day': 0,
            'last_week': 0,
            'last_month': 0,
            'last_year': 0,
            'older': 0
        }
    }
    
    now = datetime.now()
    
    try:
        for root, dirs, files in os.walk(path):
            root_path = Path(root)
            
            # Skip directories
            dirs[:] = [d for d in dirs if not should_skip_directory(root_path / d, args)]
            
            # Respect max depth
            if args.max_depth is not None:
                current_depth = len(root_path.relative_to(path).parts)
                if current_depth >= args.max_depth:
                    dirs.clear()
            
            # Check if directory is empty
            if not files and not dirs and root_path != path:
                stats['empty_dirs'].append(str(root_path))
            
            # Analyze files
            dir_size = 0
            for file_name in files:
                file_path = root_path / file_name
                
                # Skip hidden files unless --all
                if not args.all and file_name.startswith('.'):
                    continue
                
                try:
                    file_stat = file_path.stat()
                    file_size = file_stat.st_size
                    file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    stats['total_files'] += 1
                    stats['total_size'] += file_size
                    stats['file_sizes'].append(file_size)
                    dir_size += file_size
                    
                    # File type analysis
                    extension = file_path.suffix.lower() or 'no extension'
                    stats['file_types'][extension] += 1
                    
                    # Track largest/smallest files
                    file_info = {
                        'path': str(file_path),
                        'size': file_size,
                        'mtime': file_mtime
                    }
                    
                    stats['largest_files'].append(file_info)
                    stats['smallest_files'].append(file_info)
                    stats['newest_files'].append(file_info)
                    stats['oldest_files'].append(file_info)
                    
                    # Age distribution
                    age = now - file_mtime
                    if age <= timedelta(days=1):
                        stats['file_age_distribution']['last_day'] += 1
                    elif age <= timedelta(days=7):
                        stats['file_age_distribution']['last_week'] += 1
                    elif age <= timedelta(days=30):
                        stats['file_age_distribution']['last_month'] += 1
                    elif age <= timedelta(days=365):
                        stats['file_age_distribution']['last_year'] += 1
                    else:
                        stats['file_age_distribution']['older'] += 1
                
                except (OSError, PermissionError):
                    continue
            
            # Directory size tracking
            if dir_size > 0:
                stats['dir_sizes'][str(root_path)] = dir_size
            
            stats['total_dirs'] += 1
    
    except PermissionError:
        print(f"Warning: Permission denied accessing some parts of '{path}'", file=sys.stderr)
    
    # Sort and limit tracked lists
    stats['largest_files'].sort(key=lambda x: x['size'], reverse=True)
    stats['largest_files'] = stats['largest_files'][:20]
    
    stats['smallest_files'] = [f for f in stats['smallest_files'] if f['size'] > 0]
    stats['smallest_files'].sort(key=lambda x: x['size'])
    stats['smallest_files'] = stats['smallest_files'][:20]
    
    stats['newest_files'].sort(key=lambda x: x['mtime'], reverse=True)
    stats['newest_files'] = stats['newest_files'][:20]
    
    stats['oldest_files'].sort(key=lambda x: x['mtime'])
    stats['oldest_files'] = stats['oldest_files'][:20]
    
    # Large directories
    large_dirs = [(path, size) for path, size in stats['dir_sizes'].items() if size > 1024*1024]  # >1MB
    large_dirs.sort(key=lambda x: x[1], reverse=True)
    stats['large_dirs'] = large_dirs[:20]
    
    return stats

def calculate_percentiles(sizes: List[int]) -> Dict:
    """Calculate size percentiles."""
    if not sizes:
        return {}
    
    sorted_sizes = sorted(sizes)
    n = len(sorted_sizes)
    
    return {
        'min': sorted_sizes[0],
        'p25': sorted_sizes[n//4],
        'median': sorted_sizes[n//2],
        'p75': sorted_sizes[3*n//4],
        'max': sorted_sizes[-1],
        'mean': sum(sorted_sizes) / n
    }

def format_output(path: Path, stats: Dict, args) -> str:
    """Format the analysis output."""
    output = []
    
    # Header
    output.append("📊 DIRECTORY ANALYSIS")
    output.append("=" * 80)
    output.append(f"📁 Path: {path}")
    output.append(f"🕒 Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("")
    
    # Basic statistics
    output.append("📈 OVERVIEW")
    output.append("-" * 40)
    output.append(f"Total files: {stats['total_files']:,}")
    output.append(f"Total directories: {stats['total_dirs']:,}")
    output.append(f"Total size: {format_size(stats['total_size'])}")
    
    if stats['total_files'] > 0:
        avg_file_size = stats['total_size'] / stats['total_files']
        output.append(f"Average file size: {format_size(int(avg_file_size))}")
    
    # File size distribution
    if stats['file_sizes']:
        output.append("")
        output.append("📏 FILE SIZE DISTRIBUTION")
        output.append("-" * 40)
        
        percentiles = calculate_percentiles(stats['file_sizes'])
        output.append(f"Smallest: {format_size(percentiles['min'])}")
        output.append(f"25th percentile: {format_size(int(percentiles['p25']))}")
        output.append(f"Median: {format_size(int(percentiles['median']))}")
        output.append(f"75th percentile: {format_size(int(percentiles['p75']))}")
        output.append(f"Largest: {format_size(percentiles['max'])}")
        output.append(f"Mean: {format_size(int(percentiles['mean']))}")
    
    # File types
    if stats['file_types']:
        output.append("")
        output.append("📝 FILE TYPES")
        output.append("-" * 40)
        
        total_typed_files = sum(stats['file_types'].values())
        for ext, count in stats['file_types'].most_common(15):
            percentage = (count / total_typed_files) * 100
            output.append(f"{ext:20} {count:6,} files ({percentage:5.1f}%)")
    
    # Age distribution
    output.append("")
    output.append("🕰️ FILE AGE DISTRIBUTION")
    output.append("-" * 40)
    age_dist = stats['file_age_distribution']
    total_aged_files = sum(age_dist.values())
    
    if total_aged_files > 0:
        for period, count in age_dist.items():
            percentage = (count / total_aged_files) * 100
            period_name = period.replace('_', ' ').title()
            output.append(f"{period_name:15} {count:6,} files ({percentage:5.1f}%)")
    
    # Largest files
    if args.show_files and stats['largest_files']:
        output.append("")
        output.append("📊 LARGEST FILES")
        output.append("-" * 40)
        
        for i, file_info in enumerate(stats['largest_files'][:10], 1):
            size_str = format_size(file_info['size'])
            path_str = file_info['path']
            # Truncate long paths
            if len(path_str) > 60:
                path_str = "..." + path_str[-57:]
            output.append(f"{i:2d}. {size_str:>8} {path_str}")
    
    # Large directories
    if args.show_dirs and stats['large_dirs']:
        output.append("")
        output.append("📁 LARGEST DIRECTORIES")
        output.append("-" * 40)
        
        for i, (dir_path, size) in enumerate(stats['large_dirs'][:10], 1):
            size_str = format_size(size)
            # Show relative path
            try:
                rel_path = Path(dir_path).relative_to(path)
                dir_str = str(rel_path) if str(rel_path) != '.' else '(root)'
            except ValueError:
                dir_str = dir_path
            
            if len(dir_str) > 60:
                dir_str = "..." + dir_str[-57:]
            output.append(f"{i:2d}. {size_str:>8} {dir_str}")
    
    # Recent files
    if args.show_recent and stats['newest_files']:
        output.append("")
        output.append("🆕 MOST RECENT FILES")
        output.append("-" * 40)
        
        for i, file_info in enumerate(stats['newest_files'][:10], 1):
            mtime_str = file_info['mtime'].strftime('%Y-%m-%d %H:%M')
            path_str = file_info['path']
            # Show relative path
            try:
                rel_path = Path(path_str).relative_to(path)
                file_str = str(rel_path)
            except ValueError:
                file_str = path_str
            
            if len(file_str) > 50:
                file_str = "..." + file_str[-47:]
            output.append(f"{i:2d}. {mtime_str} {file_str}")
    
    # Empty directories
    if args.show_empty and stats['empty_dirs']:
        output.append("")
        output.append("📭 EMPTY DIRECTORIES")
        output.append("-" * 40)
        
        for empty_dir in stats['empty_dirs'][:10]:
            try:
                rel_path = Path(empty_dir).relative_to(path)
                output.append(f"   {rel_path}")
            except ValueError:
                output.append(f"   {empty_dir}")
        
        if len(stats['empty_dirs']) > 10:
            output.append(f"   ... and {len(stats['empty_dirs']) - 10} more")
    
    # Summary insights
    output.append("")
    output.append("💡 INSIGHTS")
    output.append("-" * 40)
    
    if stats['total_size'] > 1024**3:  # >1GB
        output.append("⚠️  Large directory (>1GB) - consider cleanup")
    
    if len(stats['empty_dirs']) > 10:
        output.append(f"📭 {len(stats['empty_dirs'])} empty directories found")
    
    if stats['file_types'].get('.log', 0) > 100:
        output.append("📜 Many log files found - consider rotation/cleanup")
    
    # Check for old files
    old_files = stats['file_age_distribution'].get('older', 0)
    if old_files > stats['total_files'] * 0.5:
        output.append("🕰️  Many old files (>1 year) - consider archiving")
    
    return "\n".join(output)

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('Comprehensive directory analysis and statistics')
    else:
        parser = argparse.ArgumentParser(
            description='Comprehensive directory analysis and statistics',
            epilog='''
EXAMPLES:
  # Basic directory analysis
  dir_stats.py
  
  # Detailed analysis with file listings
  dir_stats.py --show-files --show-dirs --show-recent
  
  # Analyze specific directory with depth limit
  dir_stats.py src/ --max-depth 3
  
  # Include hidden files and build directories
  dir_stats.py --all --include-build
  
  # Show empty directories and cleanup insights
  dir_stats.py --show-empty --insights
            ''',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
    
    # Add path argument only if not using standard parser
    if not HAS_STANDARD_PARSER:
        parser.add_argument('path', nargs='?', default='.',
                           help='Directory to analyze (default: current)')
    
    # Traversal options
    parser.add_argument('--include-build', action='store_true',
                       help='Include build/cache directories')
    
    # Display options
    parser.add_argument('--show-files', action='store_true',
                       help='Show largest files list')
    parser.add_argument('--show-dirs', action='store_true',
                       help='Show largest directories list')
    parser.add_argument('--show-recent', action='store_true',
                       help='Show most recently modified files')
    parser.add_argument('--show-empty', action='store_true',
                       help='Show empty directories')
    parser.add_argument('--detailed', action='store_true',
                       help='Show all detailed sections')
    
    args = parser.parse_args()
    
    # Handle directory path mapping for standard parser compatibility
    directory = getattr(args, 'path', getattr(args, 'directory', '.'))
    
    # Run preflight checks
    checks = [(PreflightChecker.check_directory_accessible, (directory,))]
    run_preflight_checks(checks)
    
    # Apply configuration defaults
    apply_config_to_args('dir_stats', args, parser)
    
    # If detailed mode, enable all show options
    if args.detailed:
        args.show_files = True
        args.show_dirs = True
        args.show_recent = True
        args.show_empty = True
    
    try:
        # Validate path
        path = Path(directory).resolve()
        if not path.exists():
            print(f"Error: Path '{directory}' does not exist", file=sys.stderr)
            sys.exit(1)
        
        if not path.is_dir():
            print(f"Error: Path '{directory}' is not a directory", file=sys.stderr)
            sys.exit(1)
        
        # Perform analysis
        print("Analyzing directory...", file=sys.stderr)
        stats = analyze_directory(path, args)
        
        # Format and output results
        output = format_output(path, stats, args)
        print(output)
        
    except KeyboardInterrupt:
        print("\nAnalysis cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()