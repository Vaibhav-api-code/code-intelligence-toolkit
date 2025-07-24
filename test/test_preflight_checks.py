#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test script for preflight validation in run_any_python_tool.sh"""

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import subprocess

def test_preflight():
    """Test various preflight scenarios"""
    
    script_path = "../../run_any_python_tool.sh"
    
    # Test 1: Valid tool
    print("Test 1: Valid tool with preflight checks")
    result = subprocess.run([script_path, "smart_ls.py", "--help"], 
                          capture_output=True, text=True)
    assert "Preflight checks passed" in result.stdout
    assert result.returncode == 0
    print("✅ PASSED\n")
    
    # Test 2: Skip preflight
    print("Test 2: Skip preflight checks")
    result = subprocess.run([script_path, "--skip-preflight", "smart_ls.py", "--help"], 
                          capture_output=True, text=True)
    assert "Preflight checks" not in result.stdout
    assert result.returncode == 0
    print("✅ PASSED\n")
    
    # Test 3: Non-existent tool
    print("Test 3: Non-existent tool")
    result = subprocess.run([script_path, "nonexistent_tool.py"], 
                          capture_output=True, text=True)
    assert "Tool not found" in result.stdout or "Tool not found" in result.stderr
    assert result.returncode != 0
    print("✅ PASSED\n")
    
    # Test 4: Path traversal detection
    print("Test 4: Path traversal in tool name")
    result = subprocess.run([script_path, "../../../etc/passwd"], 
                          capture_output=True, text=True)
    assert "Path traversal detected" in result.stdout or "Path traversal detected" in result.stderr
    assert result.returncode != 0
    print("✅ PASSED\n")
    
    # Test 5: Path traversal in arguments (warning only)
    print("Test 5: Path traversal in arguments (warning)")
    result = subprocess.run([script_path, "smart_ls.py", "../../../"], 
                          capture_output=True, text=True)
    assert "Warning: Potential path traversal" in result.stdout
    # Should still run (just a warning)
    assert "Preflight checks passed" in result.stdout
    print("✅ PASSED\n")
    
    print("All preflight tests passed! 🎉")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    test_preflight()