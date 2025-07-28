#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced text replacement tool (v9) with multi-level undo support.

This is a complete superset of v8 that adds SafeGIT-style multi-level undo 
capabilities to all text operations. It includes all v8 functionality plus:
- Automatic operation tracking with unique IDs
- Full backup before any modification
- Multi-level undo via text_undo.py
- Operation history and statistics

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-28
License: Mozilla Public License 2.0 (MPL-2.0)
"""

# First, let's copy the entire v8 file content but modify the atomic_write function
import sys
import os

# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
v8_path = os.path.join(script_dir, 'replace_text_v8.py')

# Read v8 source code
with open(v8_path, 'r') as f:
    v8_source = f.read()

# Import undo system
try:
    from text_operation_history import (
        TextOperationHistory, OperationType, get_history_instance
    )
    HAS_UNDO_SYSTEM = True
except ImportError:
    HAS_UNDO_SYSTEM = False
    print("Warning: text_operation_history module not found. Undo features disabled.", file=sys.stderr)

# Track operations globally
_operations_in_session = []
_undo_enabled = True

# Modify the v8 source to inject our undo tracking into _atomic_write
modified_source = v8_source.replace(
    'def _atomic_write(path: Path, data: str, bak: bool = False, max_retries: int = 3, retry_delay: float = 1.0) -> None:',
    '''def _atomic_write_v8_original(path: Path, data: str, bak: bool = False, max_retries: int = 3, retry_delay: float = 1.0) -> None:'''
)

# Add our enhanced atomic_write
undo_atomic_write = '''

def _atomic_write(path: Path, data: str, bak: bool = False, max_retries: int = 3, retry_delay: float = 1.0) -> None:
    """Enhanced atomic write with undo support."""
    global _operations_in_session, _undo_enabled
    
    # Track operations if undo is enabled
    if HAS_UNDO_SYSTEM and _undo_enabled and path.exists():
        try:
            original_content = path.read_text(encoding='utf-8')
            
            # Get command line args
            import sys
            cmd_args = sys.argv[1:]
            
            # Extract old/new text from args if available
            old_text = ""
            new_text = ""
            if len(cmd_args) >= 2:
                old_text = cmd_args[0]
                new_text = cmd_args[1]
            
            # Record operation
            history = get_history_instance()
            operation = history.record_operation(
                operation_type=OperationType.REPLACE_TEXT,
                file_path=path,
                tool_name="replace_text_v9",
                command_args=cmd_args,
                old_content=original_content,
                new_content=data,
                changes_count=1,
                description=f"Replace '{old_text[:30]}...' with '{new_text[:30]}...'" if old_text else "Text replacement"
            )
            
            if operation and operation.operation_id not in _operations_in_session:
                _operations_in_session.append(operation.operation_id)
                if not os.getenv('QUIET_MODE'):
                    print(f"[Undo ID: {operation.operation_id}] Use 'text_undo.py --operation {operation.operation_id}' to undo.")
        except Exception as e:
            # Don't fail the operation if undo tracking fails
            if not os.getenv('QUIET_MODE'):
                print(f"Warning: Could not track undo operation: {e}", file=sys.stderr)
    
    # Call the original v8 atomic_write
    _atomic_write_v8_original(path, data, bak, max_retries, retry_delay)
'''

# Also update the version in docstring and add undo argument parsing
modified_source = modified_source.replace(
    'Enhanced text replacement tool (v7)',
    'Enhanced text replacement tool (v9)'
).replace(
    'Enhanced text replacement tool (v8)',
    'Enhanced text replacement tool (v9)'
)

# Add argument for disabling undo
parser_addition = '''
    parser.add_argument('--no-undo', action='store_true',
                       help='Disable undo tracking for this operation')
    parser.add_argument('--undo-description',
                       help='Custom description for undo history')
'''

# Find where to inject the new arguments (after --no-check-compile)
import re
pattern = r"(parser\.add_argument\('--no-check-compile'[^)]+\))"
replacement = r"\1\n" + parser_addition

modified_source = re.sub(pattern, replacement, modified_source)

# Add code to handle --no-undo flag
no_undo_handler = '''
    
    # Handle undo flags (v9 feature)
    global _undo_enabled
    if hasattr(args, 'no_undo') and args.no_undo:
        _undo_enabled = False
'''

# Find where to inject (after args parsing)
pattern2 = r"(args = parser\.parse_args\(\))"
replacement2 = r"\1" + no_undo_handler

modified_source = re.sub(pattern2, replacement2, modified_source)

# Add the enhanced atomic_write function
modified_source = modified_source.replace(
    "def _atomic_write_v8_original",
    undo_atomic_write + "\ndef _atomic_write_v8_original"
)

# Add summary at the end of main
end_main_addition = '''
    
    # Show undo summary if operations were tracked (v9 feature)
    if HAS_UNDO_SYSTEM and _operations_in_session and not args.quiet:
        print(f"\\n✅ Tracked {len(_operations_in_session)} operation(s) with undo support.")
        print("📊 Use 'text_undo.py history' to view all operations.")
'''

# Find the end of main function and add summary
# This is tricky, so let's add it before the final main execution
modified_source = modified_source.replace(
    "if __name__ == '__main__':",
    end_main_addition + "\n\nif __name__ == '__main__':"
)

# Execute the modified v8 code
exec(modified_source, globals())

# The main function and everything else from v8 is now available
# with our undo enhancements injected