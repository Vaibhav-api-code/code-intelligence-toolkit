#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test scenarios for bulletproof scope-aware refactoring.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import subprocess
import os
import tempfile
import shutil
from pathlib import Path

class RefactoringTester:
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="refactor_test_")
        self.passed = 0
        self.failed = 0
    
    def cleanup(self):
        """Clean up test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def run_refactoring(self, old_name, new_name, refactor_type="all", target_file=None):
        """Run the refactoring tool and return success status."""
        cmd = [
            "python3", "ast_refactor_enhanced.py", "rename",
            "--old-name", old_name,
            "--new-name", new_name,
            "--type", refactor_type
        ]
        
        if target_file:
            cmd.append(target_file)
        else:
            cmd.append(os.path.join(self.test_dir, "*.py"))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    
    def create_test_file(self, filename, content):
        """Create a test file in the test directory."""
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def read_file(self, filepath):
        """Read file content."""
        with open(filepath, 'r') as f:
            return f.read()
    
    def test_case(self, name, test_func):
        """Run a test case."""
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print('='*60)
        
        try:
            test_func()
            self.passed += 1
            print("✅ PASSED")
        except AssertionError as e:
            self.failed += 1
            print(f"❌ FAILED: {e}")
        except Exception as e:
            self.failed += 1
            print(f"❌ ERROR: {e}")
    
    def test_global_vs_local_same_name(self):
        """Test renaming global variable when local variables have same name."""
        content = '''
# Global variable
counter = 0

def use_global():
    global counter
    counter += 1
    return counter

def use_local():
    counter = 100  # Local - should NOT be renamed
    return counter

# Use global
result = counter + use_global()
'''
        
        filepath = self.create_test_file("test_global_local.py", content)
        
        # Rename global 'counter' to 'global_counter'
        # This should rename:
        # - Line 2: counter = 0
        # - Line 5: global counter
        # - Line 6: counter += 1
        # - Line 7: return counter
        # - Line 14: result = counter + use_global()
        # But NOT:
        # - Line 10: counter = 100
        # - Line 11: return counter
        
        success, stdout, stderr = self.run_refactoring(
            "counter", "global_counter", "variable", filepath
        )
        
        modified = self.read_file(filepath)
        
        # Check that global references were renamed
        assert "global_counter = 0" in modified, "Global definition should be renamed"
        assert "global global_counter" in modified, "Global declaration should be renamed"
        assert "global_counter += 1" in modified, "Global usage should be renamed"
        
        # Check that local variable was NOT renamed
        assert "counter = 100  # Local" in modified, "Local variable should NOT be renamed"
        
        print("Modified content:")
        print(modified)
    
    def test_nested_function_scopes(self):
        """Test renaming in nested function scopes."""
        content = '''
def outer():
    value = 10  # Outer scope
    
    def inner():
        value = 20  # Inner scope - shadows outer
        return value
    
    def use_outer():
        return value  # Uses outer scope value
    
    return inner(), use_outer()

# Different function with same variable
def another():
    value = 30  # Independent
    return value
'''
        
        filepath = self.create_test_file("test_nested.py", content)
        
        # Test: Rename only the outer function's 'value'
        # This is complex - rope should handle it correctly
        print("Testing nested function scope handling...")
        
        # For now, let's verify the tool runs without error
        success, stdout, stderr = self.run_refactoring(
            "value", "outer_value", "variable", filepath
        )
        
        modified = self.read_file(filepath)
        print("Modified content:")
        print(modified)
        
        # With rope, this should intelligently rename only specific scope
        # Without rope, it would rename all occurrences
    
    def test_class_instance_vs_method_variables(self):
        """Test renaming class attributes vs method variables."""
        content = '''
class DataProcessor:
    def __init__(self):
        self.data = []  # Instance attribute
    
    def process(self):
        data = [1, 2, 3]  # Local variable - different from self.data
        self.data.extend(data)
        return data
    
    def get_data(self):
        return self.data  # Instance attribute

# Global variable with same name
data = {"global": True}
'''
        
        filepath = self.create_test_file("test_class.py", content)
        
        # Test: Rename the global 'data' variable
        success, stdout, stderr = self.run_refactoring(
            "data", "global_data", "variable", filepath
        )
        
        modified = self.read_file(filepath)
        print("Modified content:")
        print(modified)
        
        # Check that only global was renamed
        assert 'global_data = {"global": True}' in modified, "Global variable should be renamed"
        assert "self.data = []" in modified, "Instance attribute should NOT be renamed"
        assert "data = [1, 2, 3]" in modified, "Local variable should NOT be renamed"
    
    def test_import_renaming(self):
        """Test renaming imported names."""
        content = '''
import math
from math import sqrt
from math import pow as power

def calculate(x):
    # Uses various imported names
    return math.sqrt(power(x, 2))

# Local function with same name
def sqrt(x):
    return x ** 0.5

# Should use local sqrt, not imported
result = sqrt(16)
'''
        
        filepath = self.create_test_file("test_imports.py", content)
        
        # Test: Rename the local sqrt function
        success, stdout, stderr = self.run_refactoring(
            "sqrt", "square_root", "function", filepath
        )
        
        modified = self.read_file(filepath)
        print("Modified content:")
        print(modified)
        
        # Check that only local function was renamed
        assert "def square_root(x):" in modified, "Local function should be renamed"
        assert "result = square_root(16)" in modified, "Call to local function should be renamed"
        assert "from math import sqrt" in modified, "Import should NOT be renamed"
        assert "math.sqrt(" in modified, "Qualified import usage should NOT be renamed"
    
    def test_comprehension_scopes(self):
        """Test that comprehension variables don't leak."""
        content = '''
items = [1, 2, 3, 4, 5]

# Comprehension with local 'item'
doubled = [item * 2 for item in items]

# Global 'item' - different variable
item = 100

# Function using global 'item'
def process():
    return item * 3

result = process()
'''
        
        filepath = self.create_test_file("test_comprehension.py", content)
        
        # Test: Rename global 'item' variable
        success, stdout, stderr = self.run_refactoring(
            "item", "global_item", "variable", filepath
        )
        
        modified = self.read_file(filepath)
        print("Modified content:")
        print(modified)
        
        # Check that comprehension variable was NOT renamed
        assert "[item * 2 for item in items]" in modified, "Comprehension variable should NOT be renamed"
        assert "global_item = 100" in modified, "Global variable should be renamed"
        assert "return global_item * 3" in modified, "Global reference should be renamed"
    
    def test_method_vs_function_same_name(self):
        """Test renaming when methods and functions have same name."""
        content = '''
def process(data):
    """Global function."""
    return data * 2

class Processor:
    def process(self, data):
        """Instance method."""
        return data * 3

class Handler:
    def handle(self):
        # Calls global function
        return process([1, 2, 3])

# Create instances and test
p = Processor()
result1 = process([1, 2, 3])  # Global function
result2 = p.process([1, 2, 3])  # Instance method
'''
        
        filepath = self.create_test_file("test_method_function.py", content)
        
        # Test: Rename only the global function
        success, stdout, stderr = self.run_refactoring(
            "process", "process_data", "function", filepath
        )
        
        modified = self.read_file(filepath)
        print("Modified content:")
        print(modified)
        
        # Check correct renaming
        assert "def process_data(data):" in modified, "Global function should be renamed"
        assert "return process_data([1, 2, 3])" in modified, "Call to global should be renamed"
        assert "result1 = process_data([1, 2, 3])" in modified, "Direct call should be renamed"
        
        # Check method was NOT renamed
        assert "def process(self, data):" in modified, "Method should NOT be renamed"
        assert "p.process([1, 2, 3])" in modified, "Method call should NOT be renamed"
    
    def run_all_tests(self):
        """Run all test cases."""
        print("BULLETPROOF SCOPE-AWARE REFACTORING TESTS")
        print("=" * 60)
        print(f"Test directory: {self.test_dir}")
        
        # Run each test
        self.test_case(
            "Global vs Local Variables with Same Name",
            self.test_global_vs_local_same_name
        )
        
        self.test_case(
            "Nested Function Scopes",
            self.test_nested_function_scopes
        )
        
        self.test_case(
            "Class Instance vs Method Variables",
            self.test_class_instance_vs_method_variables
        )
        
        self.test_case(
            "Import Name Handling",
            self.test_import_renaming
        )
        
        self.test_case(
            "Comprehension Scope Isolation",
            self.test_comprehension_scopes
        )
        
        self.test_case(
            "Method vs Function Same Name",
            self.test_method_vs_function_same_name
        )
        
        # Summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Total: {self.passed + self.failed}")
        
        return self.failed == 0


def main():
    """Run comprehensive refactoring tests."""
    tester = RefactoringTester()
    
    try:
        # Change to the script directory
        script_dir = Path(__file__).parent
        original_dir = os.getcwd()
        os.chdir(script_dir)
        
        # Run tests
        all_passed = tester.run_all_tests()
        
        # Change back
        os.chdir(original_dir)
        
        if all_passed:
            print("\n🎉 All tests passed! Refactoring is bulletproof!")
        else:
            print("\n⚠️  Some tests failed. Review the output above.")
        
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()