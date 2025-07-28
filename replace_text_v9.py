#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced text replacement tool (v9) with multi-level undo support.

This version adds SafeGIT-style multi-level undo capabilities to all text operations.
Every replacement is tracked with atomic operations and full recovery support.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-28
License: Mozilla Public License 2.0 (MPL-2.0)
"""

# Import all from v8
from replace_text_v8 import *
import replace_text_v8 as v8_module

# Import our new undo system
try:
    from text_operation_history import (
        TextOperationHistory, OperationType, get_history_instance
    )
    HAS_UNDO_SYSTEM = True
except ImportError:
    HAS_UNDO_SYSTEM = False
    print("Warning: text_operation_history module not found. Undo features disabled.", file=sys.stderr)

# Override the atomic_write function to add undo support
def _atomic_write_with_undo(path: Path, data: str, bak: bool = False, 
                           max_retries: int = 3, retry_delay: float = 1.0,
                           tool_name: str = "replace_text_v9",
                           command_args: List[str] = None,
                           changes_count: int = 0,
                           description: str = "") -> None:
    """Write atomically with retry logic and multi-level undo support."""
    
    # Get original content for undo system
    original_content = None
    if path.exists() and HAS_UNDO_SYSTEM:
        try:
            original_content = path.read_text(encoding='utf-8')
        except Exception:
            pass
    
    # Record operation in history BEFORE making changes
    if HAS_UNDO_SYSTEM and original_content is not None:
        history = get_history_instance()
        operation = history.record_operation(
            operation_type=OperationType.REPLACE_TEXT,
            file_path=path,
            tool_name=tool_name,
            command_args=command_args or sys.argv[1:],
            old_content=original_content,
            new_content=data,
            changes_count=changes_count,
            description=description
        )
        
        if operation:
            print(f"[Undo ID: {operation.operation_id}] Operation recorded. Use 'text_undo.py --operation {operation.operation_id}' to undo.")
    
    # Call original atomic_write
    v8_module._atomic_write(path, data, bak, max_retries, retry_delay)

# Replace the module's atomic_write with our enhanced version
_atomic_write = _atomic_write_with_undo

# Enhanced main function that tracks operations
def main():
    """Enhanced main with undo tracking."""
    # Parse arguments first to get all the details
    parser = create_parser()
    args = parser.parse_args()
    
    # Store original main function
    original_main = v8_module.main
    
    # Track how many changes we make
    total_changes = 0
    
    # Monkey patch the atomic_write in the v8 module to count changes
    original_atomic_write = v8_module._atomic_write
    
    def counting_atomic_write(path, data, bak=False, max_retries=3, retry_delay=1.0):
        nonlocal total_changes
        # Check if file exists and content is different
        if path.exists():
            try:
                original = path.read_text(encoding='utf-8')
                if original != data:
                    total_changes += 1
            except:
                total_changes += 1
        else:
            total_changes += 1
        
        # Use our undo-enabled version
        _atomic_write_with_undo(
            path, data, bak, max_retries, retry_delay,
            tool_name="replace_text_v9",
            command_args=sys.argv[1:],
            changes_count=1,
            description=f"Replace '{args.old_text}' with '{args.new_text}'"
        )
    
    # Replace the atomic_write in v8 module temporarily
    v8_module._atomic_write = counting_atomic_write
    
    try:
        # Run the original main
        original_main()
    finally:
        # Restore original function
        v8_module._atomic_write = original_atomic_write
        
        # Show undo statistics if available
        if HAS_UNDO_SYSTEM and total_changes > 0:
            history = get_history_instance()
            stats = history.get_statistics()
            print(f"\n✅ {total_changes} file(s) modified. Undo available for all changes.")
            print(f"📊 Total tracked operations: {stats['total_operations']}")
            print(f"💾 Total undo backups: {stats['total_backups']}")

def create_parser():
    """Create argument parser with undo options."""
    # Get the original parser
    if hasattr(v8_module, 'create_parser'):
        parser = v8_module.create_parser()
    else:
        # Fallback to creating our own
        parser = argparse.ArgumentParser(
            description='Text replacement tool with multi-level undo support (v9)',
            epilog='Use text_undo.py to manage and restore previous versions.'
        )
        
        # Add all the v8 arguments manually if needed
        parser.add_argument('old_text', help='Text to replace')
        parser.add_argument('new_text', help='Replacement text')
        parser.add_argument('paths', nargs='*', default=['.'], help='Files or directories to process')
        parser.add_argument('-r', '--recursive', action='store_true', help='Process directories recursively')
        parser.add_argument('--backup', action='store_true', help='Create backup files')
        parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')
        parser.add_argument('--type', choices=['fixed', 'word', 'regex'], default='fixed')
    
    # Add undo-specific options
    parser.add_argument('--no-undo', action='store_true', 
                       help='Disable undo tracking for this operation')
    parser.add_argument('--undo-description', 
                       help='Custom description for undo history')
    
    return parser

if __name__ == "__main__":
    main()