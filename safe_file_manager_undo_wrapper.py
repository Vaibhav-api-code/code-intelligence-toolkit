#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Safe File Manager Undo Wrapper - Adds undo support to safe_file_manager operations.

This wrapper intercepts safe_file_manager.py operations and tracks them in the
multi-level undo system for recovery capabilities.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple
import json

# Import the undo system
try:
    from text_operation_history import (
        TextOperationHistory, OperationType, get_history_instance
    )
    HAS_UNDO_SYSTEM = True
except ImportError:
    HAS_UNDO_SYSTEM = False
    print("Warning: text_operation_history module not found. Undo features disabled.", file=sys.stderr)

def read_file_content(file_path: Path) -> Optional[str]:
    """Read file content for undo tracking."""
    try:
        if file_path.exists():
            return file_path.read_text(encoding='utf-8')
    except Exception:
        # Binary files or permission issues
        pass
    return None

def parse_command_args(args: List[str]) -> Tuple[Optional[str], Optional[Path], List[str]]:
    """Parse command arguments to extract operation and file path."""
    if not args:
        return None, None, args
    
    # Skip flags to find the command
    cmd_idx = 0
    while cmd_idx < len(args) and args[cmd_idx].startswith('-'):
        cmd_idx += 1
    
    if cmd_idx >= len(args):
        return None, None, args
    
    command = args[cmd_idx]
    
    # Map commands to their file path argument positions
    file_commands = {
        'create': 1,  # create <file>
        'write': 1,   # write <file>
        'cat': 1,     # cat <file>
        'view': 1,    # view <file>
        'copy': 1,    # copy <src> <dst> (track source)
        'cp': 1,      # cp <src> <dst>
        'move': 1,    # move <src> <dst>
        'mv': 1,      # mv <src> <dst>
        'trash': 1,   # trash <file>
        'rm': 1,      # rm <file>
        'chmod': 2,   # chmod <mode> <file>
        'chown': 2,   # chown <owner> <file>
    }
    
    if command not in file_commands:
        return command, None, args
    
    file_idx = cmd_idx + file_commands[command]
    if file_idx < len(args) and not args[file_idx].startswith('-'):
        return command, Path(args[file_idx]), args
    
    return command, None, args

def track_operation(command: str, file_path: Path, args: List[str], 
                   exit_code: int) -> Optional[str]:
    """Track the operation in the undo system."""
    if not HAS_UNDO_SYSTEM or exit_code != 0:
        return None
    
    # Determine operation type
    op_type_map = {
        'create': OperationType.WRITE_FILE,
        'write': OperationType.WRITE_FILE,
        'copy': OperationType.WRITE_FILE,
        'cp': OperationType.WRITE_FILE,
        'move': OperationType.WRITE_FILE,
        'mv': OperationType.WRITE_FILE,
        'trash': OperationType.DELETE_FILE,
        'rm': OperationType.DELETE_FILE,
        'chmod': OperationType.WRITE_FILE,
        'chown': OperationType.WRITE_FILE,
    }
    
    op_type = op_type_map.get(command, OperationType.WRITE_FILE)
    
    # Get content for tracking
    old_content = None
    new_content = None
    
    if command in ['create', 'write']:
        # For create/write, track the new content
        new_content = read_file_content(file_path)
    elif command in ['trash', 'rm']:
        # For delete, we would need the content before deletion
        # This is tricky without modifying safe_file_manager
        pass
    
    try:
        history = get_history_instance()
        operation = history.record_operation(
            operation_type=op_type,
            file_path=file_path,
            tool_name="safe_file_manager",
            command_args=args,
            old_content=old_content,
            new_content=new_content,
            changes_count=1,
            description=f"safe_file_manager {command} {file_path}"
        )
        
        if operation:
            print(f"✓ Operation tracked for undo: {operation.operation_id}")
            return operation.operation_id
    except Exception as e:
        print(f"Warning: Could not track undo operation: {e}", file=sys.stderr)
    
    return None

def main():
    """Wrapper main that adds undo tracking."""
    # Check if undo is disabled
    if os.getenv("SFM_NO_UNDO") == "1":
        # Direct passthrough
        result = subprocess.run(
            [sys.executable, "safe_file_manager.py"] + sys.argv[1:],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode
    
    # Parse command to determine what we're tracking
    command, file_path, args = parse_command_args(sys.argv[1:])
    
    # For operations that modify files, capture state before
    old_content = None
    if command in ['write', 'trash', 'rm', 'move', 'mv'] and file_path and file_path.exists():
        old_content = read_file_content(file_path)
    
    # Run the actual safe_file_manager
    result = subprocess.run(
        [sys.executable, "safe_file_manager.py"] + sys.argv[1:],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # Track the operation if successful
    if result.returncode == 0 and command and file_path:
        track_operation(command, file_path, sys.argv[1:], result.returncode)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
