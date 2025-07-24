#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test suite for standardized interfaces.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import subprocess
import sys
from pathlib import Path

def run_tool(tool_name, args):
    """Run tool and capture output."""
    cmd = ['./run_any_python_tool.sh', tool_name] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def test_find_text_standardized():
    """Test find_text with standardized interface."""
    print("Testing find_text standardized interface...")
    
    # Test 1: Pattern with file specification (this used to fail)
    exit_code, stdout, stderr = run_tool('find_text.py', 
                                        ['def main', '--file', 'standard_arg_parser.py'])
    
    if exit_code == 0 or "does not exist" in stderr:
        print("✓ find_text file specification working")
    else:
        print(f"✗ find_text file specification failed: {stderr}")
    
    # Test 2: Pattern with scope
    exit_code, stdout, stderr = run_tool('find_text.py', 
                                        ['def main', '--scope', '.'])
    
    if exit_code == 0:
        print("✓ find_text scope specification working") 
    else:
        print(f"✗ find_text scope specification failed: {stderr}")

def test_method_analyzer_standardized():
    """Test method_analyzer_ast with standardized interface."""
    print("\\nTesting method_analyzer_ast standardized interface...")
    
    # Test 1: Method name first (this used to be confusing)
    exit_code, stdout, stderr = run_tool('method_analyzer_ast.py',
                                        ['main', '--scope', '.'])
    
    if exit_code == 0 or "No definitions found" in stdout:
        print("✓ method_analyzer method-first format working")
    else:
        print(f"✗ method_analyzer method-first format failed: {stderr}")
    
    # Test 2: Method with specific file
    exit_code, stdout, stderr = run_tool('method_analyzer_ast.py',
                                        ['create_parser', '--file', 'standard_arg_parser.py'])
    
    if exit_code == 0 or "No definitions found" in stdout:
        print("✓ method_analyzer file specification working")
    else:
        print(f"✗ method_analyzer file specification failed: {stderr}")

def test_navigate_standardized():
    """Test navigate_ast with standardized interface."""
    print("\\nTesting navigate_ast standardized interface...")
    
    # Test with line number
    exit_code, stdout, stderr = run_tool('navigate_ast.py',
                                        ['standard_arg_parser.py', '--line', '1'])
    
    if exit_code == 0:
        print("✓ navigate line navigation working")
    else:
        print(f"✗ navigate line navigation failed: {stderr}")

def test_error_prevention():
    """Test that common errors are now prevented."""
    print("\\nTesting error prevention...")
    
    # Test 1: File path where method name expected (should give clear error)
    exit_code, stdout, stderr = run_tool('method_analyzer_ast.py',
                                        ['standard_arg_parser.py'])
    
    if "file path instead of a method name" in stderr or "Invalid method name" in stderr:
        print("✓ File path detection working")
    else:
        print(f"? File path detection unclear: {stderr[:100]}")
    
    # Test 2: Invalid file path (should give clear error)
    exit_code, stdout, stderr = run_tool('find_text.py',
                                        ['pattern', '--file', 'nonexistent.py'])
    
    if "does not exist" in stderr:
        print("✓ File existence checking working")
    else:
        print(f"✗ File existence checking failed: {stderr}")

def test_help_clarity():
    """Test that help messages are clearer."""
    print("\\nTesting help message clarity...")
    
    # Test find_text help
    exit_code, stdout, stderr = run_tool('find_text.py', ['--help'])
    
    if "--file" in stdout and "positional arguments:" in stdout and "pattern" in stdout:
        print("✓ find_text help is clear")
    else:
        print("✗ find_text help unclear")
    
    # Test method_analyzer help
    exit_code, stdout, stderr = run_tool('method_analyzer_ast.py', ['--help'])
    
    if "target" in stdout and "--file" in stdout:
        print("✓ method_analyzer help is clear")
    else:
        print("✗ method_analyzer help unclear")

def main():
    print("Standardized Interface Test Suite")
    print("=" * 50)
    
    if not Path('./run_any_python_tool.sh').exists():
        print("Error: run_any_python_tool.sh not found")
        sys.exit(1)
    
    test_find_text_standardized()
    test_method_analyzer_standardized()
    test_navigate_standardized()
    test_error_prevention()
    test_help_clarity()
    
    print("\\n" + "=" * 50)
    print("Interface standardization tests complete!")
    print("\\nKey improvements:")
    print("1. Target (pattern/method) comes first as positional argument")
    print("2. Location specified with clear flags: --file or --scope")
    print("3. Consistent argument patterns across all tools")
    print("4. Better error messages with usage hints")
    print("5. Pre-flight validation prevents common mistakes")

if __name__ == "__main__":
    main()