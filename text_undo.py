#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Text Undo - Multi-level undo management for text operations

This tool provides SafeGIT-style undo capabilities for all text editing operations.
It allows you to view history, undo specific operations, and manage backups.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-28
Updated: 2025-07-28
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
# import humanize  # Optional dependency
import textwrap

try:
    from text_operation_history import (
        TextOperationHistory, OperationType, get_history_instance
    )
except ImportError:
    print("Error: text_operation_history module not found.", file=sys.stderr)
    print("This tool requires the text operation history system.", file=sys.stderr)
    sys.exit(1)

try:
    from interactive_utils import (
        safe_input, get_confirmation, check_auto_yes_env,
        get_tool_env_var, get_numbered_selection, Colors
    )
except ImportError:
    # Fallback for older installations
    print("Warning: interactive_utils module not found. Using basic input handling.", file=sys.stderr)
    safe_input = input
    def get_confirmation(prompt, **kwargs):
        response = input(prompt + " [y/N]: ").strip().lower()
        return response in ['y', 'yes']
    def check_auto_yes_env(tool_name, args):
        pass
    def get_tool_env_var(tool_name):
        return f"{tool_name.upper()}_ASSUME_YES"
    def get_numbered_selection(prompt, items, **kwargs):
        # Basic fallback implementation
        for i, item in enumerate(items, 1):
            print(f"{i}. {item}")
        try:
            choice = input(f"{prompt} (1-{len(items)}) or 'q' to quit: ")
            if choice.lower() == 'q':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return idx
        except (ValueError, EOFError, KeyboardInterrupt):
            pass
        return None

# Import Colors from interactive_utils if not already imported
if 'Colors' not in locals():
    # Fallback Colors class for older installations
    class Colors:
        HEADER = '\033[95m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        END = '\033[0m'

def format_timestamp(timestamp: float) -> str:
    """Format timestamp in human-readable form."""
    dt = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    
    # Simple relative times without humanize
    diff = now - dt
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_size(size_bytes: int) -> str:
    """Format size in human-readable form."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def print_operation_details(op):
    """Print detailed information about an operation."""
    print(f"\n{Colors.BOLD}Operation ID:{Colors.END} {op.operation_id}")
    print(f"{Colors.BOLD}Timestamp:{Colors.END} {format_timestamp(op.timestamp)}")
    print(f"{Colors.BOLD}Type:{Colors.END} {op.operation_type.value}")
    print(f"{Colors.BOLD}Tool:{Colors.END} {op.tool_name}")
    print(f"{Colors.BOLD}File:{Colors.END} {op.file_path}")
    
    if op.description:
        print(f"{Colors.BOLD}Description:{Colors.END} {op.description}")
    
    print(f"{Colors.BOLD}Changes:{Colors.END} {op.changes_count} ({op.lines_affected} lines affected)")
    print(f"{Colors.BOLD}Can Undo:{Colors.END} {'✅ Yes' if op.can_undo else '❌ No'}")
    
    if op.backup_path:
        backup_path = Path(op.backup_path)
        if backup_path.exists():
            size = backup_path.stat().st_size
            print(f"{Colors.BOLD}Backup:{Colors.END} {op.backup_path} ({format_size(size)})")
        else:
            print(f"{Colors.BOLD}Backup:{Colors.END} {op.backup_path} (⚠️  Missing)")
    
    if op.command_args:
        print(f"{Colors.BOLD}Command:{Colors.END} {' '.join(op.command_args)}")
    
    if op.can_undo:
        print(f"\n{Colors.GREEN}To undo:{Colors.END} text_undo.py undo --operation {op.operation_id}")

def cmd_history(args):
    """Show operation history."""
    history = get_history_instance()
    
    # Parse time filter
    since = None
    if args.since:
        if args.since.endswith('h'):
            hours = int(args.since[:-1])
            since = datetime.now().timestamp() - (hours * 3600)
        elif args.since.endswith('d'):
            days = int(args.since[:-1])
            since = datetime.now().timestamp() - (days * 86400)
        else:
            print(f"Invalid time format: {args.since}. Use format like '2h' or '3d'", file=sys.stderr)
            return 1
    
    # Get filtered history
    operations = history.get_history(
        limit=args.limit,
        file_path=Path(args.file) if args.file else None,
        tool_name=args.tool,
        since=since
    )
    
    if not operations:
        print("No operations found matching the criteria.")
        return 0
    
    # Display format
    if args.detailed:
        for op in operations:
            print_operation_details(op)
            print("-" * 80)
    else:
        # Table format
        print(f"\n{Colors.BOLD}{'ID':20} {'Time':20} {'Tool':15} {'File':30} {'Changes':8} {'Undo':6}{Colors.END}")
        print("=" * 100)
        
        for op in operations:
            file_name = Path(op.file_path).name
            if len(file_name) > 30:
                file_name = file_name[:27] + "..."
            
            undo_status = "✅" if op.can_undo else "❌"
            
            print(f"{op.operation_id:20} {format_timestamp(op.timestamp):20} "
                  f"{op.tool_name:15} {file_name:30} {op.changes_count:8} {undo_status:6}")
    
    # Show summary
    stats = history.get_statistics()
    print(f"\n{Colors.CYAN}Total operations: {stats['total_operations']}")
    print(f"Undoable operations: {stats['can_undo_count']}")
    print(f"Backup storage: {format_size(stats['backup_size_bytes'])}{Colors.END}")
    
    return 0

def cmd_undo(args):
    """Undo a specific operation."""
    history = get_history_instance()
    
    if args.interactive:
        # Show recent operations and let user choose
        operations = history.get_history(limit=20)
        undoable = [op for op in operations if op.can_undo]
        
        if not undoable:
            print("No undoable operations found.")
            return 1
        
        print(f"\n{Colors.BOLD}Recent undoable operations:{Colors.END}")
        
        # Prepare items for numbered selection
        items = []
        for op in undoable:
            file_name = Path(op.file_path).name
            item = f"[{op.operation_id}] {format_timestamp(op.timestamp)} - {file_name} ({op.changes_count} changes)"
            items.append(item)
        
        # Use get_numbered_selection for interactive choice
        idx = get_numbered_selection(
            "Select operation to undo",
            items,
            allow_quit=True,
            tool_name='text_undo',
            env_var='TEXT_UNDO',
            flag_hint='--operation ID'
        )
        if idx is None:
            print("Cancelled.")
            return 0
        operation_id = undoable[idx].operation_id
    
    elif args.operation:
        operation_id = args.operation
    
    elif args.last:
        # Undo the last operation
        operations = history.get_history(limit=1)
        if not operations or not operations[0].can_undo:
            print("No undoable operations found.")
            return 1
        operation_id = operations[0].operation_id
    
    else:
        print("Please specify --operation ID, --last, or --interactive")
        return 1
    
    # Show what will be undone
    operations = history.get_history(limit=1000)
    target_op = None
    for op in operations:
        if op.operation_id == operation_id:
            target_op = op
            break
    
    if not target_op:
        print(f"Operation {operation_id} not found.")
        return 1
    
    print(f"\n{Colors.YELLOW}About to undo:{Colors.END}")
    print_operation_details(target_op)
    
    # Check environment variable
    check_auto_yes_env('text_undo', args)
    
    if not args.yes:
        if not get_confirmation(
            f"\n{Colors.BOLD}Proceed with undo?{Colors.END}",
            default=False,
            tool_name='text_undo',
            env_var=get_tool_env_var('text_undo'),
            flag_hint='--yes'
        ):
            print("Cancelled.")
            return 0
    
    # Perform the undo
    success, message = history.undo_operation(operation_id)
    
    if success:
        print(f"\n{Colors.GREEN}✅ {message}{Colors.END}")
        print(f"File {target_op.file_path} has been restored to its previous state.")
    else:
        print(f"\n{Colors.RED}❌ {message}{Colors.END}")
        return 1
    
    return 0

def cmd_show(args):
    """Show details of a specific operation."""
    history = get_history_instance()
    
    # Find the operation
    operations = history.get_history(limit=10000)
    target_op = None
    
    for op in operations:
        if op.operation_id == args.operation:
            target_op = op
            break
    
    if not target_op:
        print(f"Operation {args.operation} not found.")
        return 1
    
    print_operation_details(target_op)
    
    # Show recovery script if available
    recovery_script = Path(history.recovery_dir) / f"recover_{args.operation}.sh"
    if recovery_script.exists() and args.show_script:
        print(f"\n{Colors.BOLD}Recovery Script:{Colors.END}")
        print("-" * 80)
        with open(recovery_script, 'r') as f:
            print(f.read())
    
    return 0

def cmd_stats(args):
    """Show statistics about the undo system."""
    history = get_history_instance()
    stats = history.get_statistics()
    
    print(f"\n{Colors.BOLD}Text Operation History Statistics{Colors.END}")
    print("=" * 50)
    
    print(f"\n{Colors.CYAN}Overview:{Colors.END}")
    print(f"  Total operations: {stats['total_operations']}")
    print(f"  Undoable operations: {stats['can_undo_count']}")
    print(f"  Total changes made: {stats['total_changes']}")
    print(f"  Backup storage used: {format_size(stats['backup_size_bytes'])}")
    
    if stats['operations_by_type']:
        print(f"\n{Colors.CYAN}Operations by Type:{Colors.END}")
        for op_type, count in sorted(stats['operations_by_type'].items()):
            print(f"  {op_type}: {count}")
    
    if stats['operations_by_tool']:
        print(f"\n{Colors.CYAN}Operations by Tool:{Colors.END}")
        for tool, count in sorted(stats['operations_by_tool'].items(), 
                                 key=lambda x: x[1], reverse=True):
            print(f"  {tool}: {count}")
    
    # Show configuration
    print(f"\n{Colors.CYAN}Configuration:{Colors.END}")
    print(f"  History directory: {history.history_dir}")
    print(f"  Max history size: {history.max_history_size} operations")
    print(f"  Backup retention: {history.max_backup_age_days} days")
    print(f"  Compression threshold: {format_size(history.compression_threshold)}")
    
    return 0

def cmd_clean(args):
    """Clean up old operations and backups."""
    history = get_history_instance()
    
    print(f"{Colors.YELLOW}Cleaning up old operations and backups...{Colors.END}")
    
    # Get current stats
    stats_before = history.get_statistics()
    
    # Perform cleanup
    history._cleanup_old_operations()
    
    # Get new stats
    stats_after = history.get_statistics()
    
    # Report results
    ops_removed = stats_before['total_operations'] - stats_after['total_operations']
    space_freed = stats_before['backup_size_bytes'] - stats_after['backup_size_bytes']
    
    print(f"\n{Colors.GREEN}Cleanup complete:{Colors.END}")
    print(f"  Operations removed: {ops_removed}")
    print(f"  Space freed: {format_size(space_freed)}")
    print(f"  Remaining operations: {stats_after['total_operations']}")
    print(f"  Remaining backup size: {format_size(stats_after['backup_size_bytes'])}")
    
    return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Text Undo - Multi-level undo for text operations',
        epilog=textwrap.dedent("""
        Examples:
          # Show recent operations
          %(prog)s history
          
          # Show operations for a specific file
          %(prog)s history --file script.py
          
          # Undo the last operation
          %(prog)s undo --last
          
          # Interactive undo
          %(prog)s undo --interactive
          
          # Show statistics
          %(prog)s stats
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show operation history')
    history_parser.add_argument('--limit', type=int, default=50, 
                               help='Number of operations to show (default: 50)')
    history_parser.add_argument('--file', help='Filter by file path')
    history_parser.add_argument('--tool', help='Filter by tool name')
    history_parser.add_argument('--since', help='Show operations since (e.g., 2h, 3d)')
    history_parser.add_argument('--detailed', action='store_true',
                               help='Show detailed information for each operation')
    
    # Undo command
    undo_parser = subparsers.add_parser('undo', help='Undo an operation')
    undo_parser.add_argument('--operation', help='Operation ID to undo')
    undo_parser.add_argument('--last', action='store_true', 
                            help='Undo the last operation')
    undo_parser.add_argument('--interactive', action='store_true',
                            help='Choose operation to undo interactively')
    undo_parser.add_argument('--yes', '-y', action='store_true',
                            help='Skip confirmation')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show operation details')
    show_parser.add_argument('operation', help='Operation ID')
    show_parser.add_argument('--show-script', action='store_true',
                            help='Show recovery script content')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show system statistics')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean up old operations')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Dispatch to command handler
    handlers = {
        'history': cmd_history,
        'undo': cmd_undo,
        'show': cmd_show,
        'stats': cmd_stats,
        'clean': cmd_clean
    }
    
    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())