#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Demo of the Multi-Level Undo System for Text Operations

This script demonstrates how the undo system tracks all text modifications
and allows recovery to any previous state.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-28
Updated: 2025-07-28
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# ANSI colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RED = '\033[91m'
BOLD = '\033[1m'
END = '\033[0m'

def run_command(cmd, description):
    """Run a command and show its output."""
    print(f"\n{BLUE}▶ {description}{END}")
    print(f"{YELLOW}$ {cmd}{END}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"{RED}Error: {result.stderr}{END}")
    
    return result.returncode == 0

def main():
    print(f"{BOLD}=== Multi-Level Undo System Demo ==={END}")
    print("This demo shows how every text operation is tracked and can be undone.")
    
    # Create a test file
    test_file = Path("undo_test.txt")
    print(f"\n{GREEN}1. Creating test file...{END}")
    
    original_content = """Version 1.0 - Original Content
This is the original version of our test file.
It contains some sample text that we'll modify.

Important data:
- Status: Active
- Value: 100
- Mode: Production

This content will be changed multiple times."""
    
    with open(test_file, 'w') as f:
        f.write(original_content)
    
    print(f"Created {test_file}")
    
    # Make first change
    print(f"\n{GREEN}2. Making first modification...{END}")
    if not run_command(
        f'python3 replace_text_v9.py "Version 1.0" "Version 2.0" {test_file} --yes',
        "Updating version number"
    ):
        print("Note: replace_text_v9 needs proper integration")
    
    # For demo purposes, let's use the history system directly
    print(f"\n{GREEN}3. Demonstrating direct history tracking...{END}")
    
    # Import and use the history system
    try:
        from text_operation_history import (
            TextOperationHistory, OperationType, get_history_instance
        )
        
        history = get_history_instance()
        
        # Make a change and track it
        modified_content = original_content.replace("Version 1.0", "Version 2.0")
        modified_content = modified_content.replace("Value: 100", "Value: 200")
        
        # Record the operation
        operation = history.record_operation(
            operation_type=OperationType.REPLACE_TEXT,
            file_path=test_file,
            tool_name="demo_script",
            command_args=["demo", "Version 1.0 -> 2.0, Value 100 -> 200"],
            old_content=original_content,
            new_content=modified_content,
            changes_count=2,
            description="Demo: Updated version and value"
        )
        
        # Write the modified content
        with open(test_file, 'w') as f:
            f.write(modified_content)
        
        print(f"{GREEN}✓ Operation recorded with ID: {operation.operation_id}{END}")
        
        # Make another change
        print(f"\n{GREEN}4. Making second modification...{END}")
        
        modified_content2 = modified_content.replace("Mode: Production", "Mode: Development")
        modified_content2 = modified_content2.replace("Status: Active", "Status: Testing")
        
        operation2 = history.record_operation(
            operation_type=OperationType.REPLACE_TEXT,
            file_path=test_file,
            tool_name="demo_script",
            command_args=["demo", "Mode and Status update"],
            old_content=modified_content,
            new_content=modified_content2,
            changes_count=2,
            description="Demo: Changed mode and status"
        )
        
        with open(test_file, 'w') as f:
            f.write(modified_content2)
        
        print(f"{GREEN}✓ Operation recorded with ID: {operation2.operation_id}{END}")
        
        # Show history
        print(f"\n{GREEN}5. Viewing operation history...{END}")
        run_command("python3 text_undo.py history --limit 10", "Recent operations")
        
        # Show current file content
        print(f"\n{GREEN}6. Current file content:{END}")
        with open(test_file, 'r') as f:
            content = f.read()
            for line in content.split('\n')[:5]:
                print(f"  {line}")
        print("  ...")
        
        # Undo last operation
        print(f"\n{GREEN}7. Undoing last operation...{END}")
        success, message = history.undo_operation(operation2.operation_id)
        if success:
            print(f"{GREEN}✓ {message}{END}")
        else:
            print(f"{RED}✗ {message}{END}")
        
        # Show restored content
        print(f"\n{GREEN}8. File after undo:{END}")
        with open(test_file, 'r') as f:
            content = f.read()
            for line in content.split('\n')[:5]:
                print(f"  {line}")
        print("  ...")
        
        # Show statistics
        print(f"\n{GREEN}9. System statistics:{END}")
        stats = history.get_statistics()
        print(f"  Total operations: {stats['total_operations']}")
        print(f"  Undoable operations: {stats['can_undo_count']}")
        print(f"  Backup storage: {stats['backup_size_bytes']} bytes")
        
        # Interactive undo option
        print(f"\n{GREEN}10. Interactive undo available:{END}")
        print(f"  Run: {YELLOW}python3 text_undo.py undo --interactive{END}")
        print(f"  Or undo specific operation: {YELLOW}python3 text_undo.py undo --operation {operation.operation_id}{END}")
        
    except ImportError as e:
        print(f"{RED}Error: Could not import text operation history: {e}{END}")
        print("Make sure text_operation_history.py is in the same directory")
    
    except Exception as e:
        print(f"{RED}Error during demo: {e}{END}")
    
    finally:
        # Cleanup
        if test_file.exists():
            print(f"\n{YELLOW}Cleaning up test file...{END}")
            test_file.unlink()

if __name__ == "__main__":
    main()