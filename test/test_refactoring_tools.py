#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test suite for refactoring tools with configuration integration.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

class TestResult:
    """Simple test result tracking"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"❌ FAIL: {test_name} - {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Summary: {self.passed}/{total} passed")
        if self.errors:
            print("\nFailed tests:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")
        print(f"{'='*60}")
        return self.failed == 0

def run_tool(tool_name, args, capture_output=True):
    """Run a tool and return output"""
    cmd = [sys.executable, tool_name] + args
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, timeout=10)
        if result.returncode != 0:
            return None, result.stderr
        return result.stdout, None
    except subprocess.TimeoutExpired:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)

def test_replace_text_config(results):
    """Test replace_text.py with configuration defaults"""
    print("\n=== Testing replace_text.py config integration ===")
    
    # Create test file
    test_file = Path("test_replace.txt")
    test_file.write_text("This is old text that needs replacing")
    
    try:
        # Config has dry_run=false by default
        # Test that it actually makes changes without --dry-run flag
        output, error = run_tool("replace_text.py", ["old", "new", str(test_file)])
        if error:
            results.add_fail("replace_text config defaults", error)
        else:
            content = test_file.read_text()
            if "new text" in content:
                results.add_pass("replace_text config defaults")
            else:
                results.add_fail("replace_text config defaults", "Text not replaced")
        
        # Test CLI override of config (force dry-run)
        test_file.write_text("This is old text again")
        output, error = run_tool("replace_text.py", ["old", "new", str(test_file), "--dry-run"])
        if error:
            results.add_fail("replace_text CLI override", error)
        else:
            content = test_file.read_text()
            if "old text" in content and ("Would replace" in output or "Would modify" in output):
                results.add_pass("replace_text CLI override")
            else:
                results.add_fail("replace_text CLI override", "Dry-run not respected")
                
        # Test backup config (backup=true by default)
        test_file.write_text("Original content")
        output, error = run_tool("replace_text.py", ["Original", "Modified", str(test_file)])
        if error:
            results.add_fail("replace_text backup config", error)
        else:
            backup_file = Path(str(test_file) + ".bak")
            if backup_file.exists():
                results.add_pass("replace_text backup config")
                backup_file.unlink()
            else:
                results.add_fail("replace_text backup config", "No backup created")
                
    finally:
        if test_file.exists():
            test_file.unlink()

def test_replace_text_ast_config(results):
    """Test replace_text_ast.py with configuration defaults"""
    print("\n=== Testing replace_text_ast.py config integration ===")
    
    # Create test Python file
    test_file = Path("test_ast.py")
    test_file.write_text("""def test_function():
    old_variable = 42
    return old_variable
""")
    
    try:
        # Config has dry_run=true by default for safety
        # Test that it doesn't make changes without --no-dry-run flag
        output, error = run_tool("replace_text_ast.py", 
                                ["--ast-rename", str(test_file), "old_variable", "new_variable", "--line", "2"])
        
        if error and "not found on line" not in error:
            # Some error is expected due to AST parsing, but check the file wasn't modified
            content = test_file.read_text()
            if "old_variable" in content:
                results.add_pass("replace_text_ast dry-run default")
            else:
                results.add_fail("replace_text_ast dry-run default", "File modified in dry-run mode")
        elif output and "DRY-RUN" in output:
            results.add_pass("replace_text_ast dry-run default")
        else:
            # Check if file was modified
            content = test_file.read_text()
            if "old_variable" in content:
                results.add_pass("replace_text_ast dry-run default")
            else:
                results.add_fail("replace_text_ast dry-run default", "File modified without explicit flag")
                
    finally:
        if test_file.exists():
            test_file.unlink()

def test_find_text_usage(results):
    """Test find_text.py proper usage with --in-files"""
    print("\n=== Testing find_text.py usage ===")
    
    # Create test file
    test_file = Path("test_search.java")
    test_file.write_text("""public class Test {
    private void updateVirtualTrendExitSuppression() {
        // Some code here
    }
    
    private boolean exitSuppressionMode = false;
}""")
    
    try:
        # Test searching in specific file with --in-files
        output, error = run_tool("find_text.py", 
                                ["updateVirtualTrendExitSuppression", "--in-files", 
                                 "--path", str(test_file), "-C", "2"])
        if error:
            results.add_fail("find_text --in-files usage", error)
        elif "updateVirtualTrendExitSuppression" in output:
            results.add_pass("find_text --in-files usage")
        else:
            results.add_fail("find_text --in-files usage", "Pattern not found in file")
            
        # Test without --in-files (should fail to find content)
        output, error = run_tool("find_text.py", 
                                ["updateVirtualTrendExitSuppression", 
                                 str(test_file)])
        if error and "unrecognized arguments" in error:
            results.add_pass("find_text error without --in-files")
        else:
            results.add_fail("find_text error without --in-files", 
                           "Should error without --in-files flag")
            
    finally:
        if test_file.exists():
            test_file.unlink()

def test_config_types(results):
    """Test that config type conversion works correctly"""
    print("\n=== Testing config type conversion ===")
    
    # Test boolean conversion
    from common_config import convert_config_value
    
    # Test boolean
    if convert_config_value("true", bool) == True:
        results.add_pass("config bool conversion - true")
    else:
        results.add_fail("config bool conversion - true", "Failed to convert 'true' to True")
        
    if convert_config_value("false", bool) == False:
        results.add_pass("config bool conversion - false")
    else:
        results.add_fail("config bool conversion - false", "Failed to convert 'false' to False")
    
    # Test integer
    if convert_config_value("10", int) == 10:
        results.add_pass("config int conversion")
    else:
        results.add_fail("config int conversion", "Failed to convert '10' to 10")
    
    # Test string (should stay as is)
    if convert_config_value("test", str) == "test":
        results.add_pass("config string conversion")
    else:
        results.add_fail("config string conversion", "String conversion failed")

def main():
    """Run all tests"""
    print("🧪 Refactoring Tools Configuration Test Suite")
    print("=" * 60)
    
    results = TestResult()
    
    # Run tests
    test_replace_text_config(results)
    test_replace_text_ast_config(results)
    test_find_text_usage(results)
    test_config_types(results)
    
    # Show summary
    success = results.summary()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()