#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test script to verify Java nested class support in cross_file_analysis_ast.py

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import os
from pathlib import Path

# Add current directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from cross_file_analysis_ast import CallerIdentifier
    print("✓ Successfully imported CallerIdentifier")
except ImportError as e:
    print(f"✗ Failed to import CallerIdentifier: {e}")
    sys.exit(1)

def test_nested_class_identification():
    """Test the enhanced Java nested class support."""
    
    test_file = "test_data/NestedClassExample.java"
    
    if not os.path.exists(test_file):
        print(f"✗ Test file {test_file} not found")
        return False
    
    print(f"\n🧪 Testing Java nested class identification with {test_file}")
    print("=" * 60)
    
    # Test cases: (line_number, expected_result)
    test_cases = [
        (4, "OrderManager.<init>"),  # Constructor
        (10, "OrderManager.processOrder"),  # Method call in main class
        (21, "OrderManager.OrderValidator.validateOrderDetails"),  # Method in static nested class
        (32, "OrderManager.OrderValidator.FieldValidator.validateField"),  # Deep nesting
        (37, "OrderManager.OrderValidator.FieldValidator.performValidation"),  # Method in deeply nested class
        (46, "OrderManager.OrderProcessor.executeOrder"),  # Method in inner class
        (59, None),  # Inside anonymous class - might be tricky to detect
        (68, "OrderManager.main"),  # Main method
    ]
    
    results = []
    
    for line_num, expected in test_cases:
        try:
            result = CallerIdentifier.find_enclosing_function_java(test_file, line_num)
            
            # Check if result matches expectation
            if result == expected:
                status = "✓ PASS"
                color = "\033[92m"  # Green
            else:
                status = "✗ FAIL"
                color = "\033[91m"  # Red
            
            reset_color = "\033[0m"
            
            print(f"{color}Line {line_num:2d}: {status}{reset_color}")
            print(f"    Expected: {expected}")
            print(f"    Got:      {result}")
            
            if result != expected:
                # Show the actual line for context
                with open(test_file, 'r') as f:
                    lines = f.readlines()
                    if line_num <= len(lines):
                        line_content = lines[line_num - 1].strip()
                        print(f"    Line:     {line_content}")
            
            print()
            
            results.append((line_num, expected, result, result == expected))
            
        except Exception as e:
            print(f"✗ ERROR at line {line_num}: {e}")
            results.append((line_num, expected, f"ERROR: {e}", False))
    
    # Summary
    passed = sum(1 for _, _, _, success in results if success)
    total = len(results)
    
    print("=" * 60)
    print(f"📊 SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Java nested class support is working correctly.")
        return True
    else:
        failed_tests = [(line, exp, got) for line, exp, got, success in results if not success]
        print("\n❌ Failed tests:")
        for line, expected, got in failed_tests:
            print(f"    Line {line}: expected '{expected}', got '{got}'")
        return False

def test_python_functionality():
    """Quick test to ensure Python functionality still works."""
    
    print("\n🐍 Testing Python functionality (should still work)")
    print("=" * 50)
    
    # Create a simple test Python file
    test_py_content = '''
def outer_function():
    def inner_function():
        print("inner")  # Line 4
    inner_function()

class TestClass:
    def method(self):
        print("method")  # Line 9
        
outer_function()
'''
    
    test_py_file = "test_data/test_python.py"
    
    # Write test file
    os.makedirs("test_data", exist_ok=True)
    with open(test_py_file, 'w') as f:
        f.write(test_py_content)
    
    try:
        # Test Python function detection
        result = CallerIdentifier.find_enclosing_function_python(test_py_file, 4)
        expected = "inner_function"
        
        if result == expected:
            print(f"✓ Python inner function detection: {result}")
            python_success = True
        else:
            print(f"✗ Python test failed: expected '{expected}', got '{result}'")
            python_success = False
            
        # Test Python method detection
        result = CallerIdentifier.find_enclosing_function_python(test_py_file, 9)
        expected = "method"
        
        if result == expected:
            print(f"✓ Python method detection: {result}")
            python_success = python_success and True
        else:
            print(f"✗ Python method test failed: expected '{expected}', got '{result}'")
            python_success = False
            
    except Exception as e:
        print(f"✗ Python test error: {e}")
        python_success = False
    
    return python_success

def main():
    print("🔍 Java Nested Class Support Test Suite")
    print("Testing enhanced CallerIdentifier functionality")
    
    # Check if javalang is available
    try:
        import javalang
        print("✓ javalang library available")
    except ImportError:
        print("✗ javalang library not available - Java tests will be skipped")
        print("  Install with: pip install javalang")
        return
    
    # Run tests
    java_success = test_nested_class_identification()
    python_success = test_python_functionality()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS")
    print(f"Java nested class support: {'✓ WORKING' if java_success else '✗ NEEDS WORK'}")
    print(f"Python functionality:      {'✓ WORKING' if python_success else '✗ BROKEN'}")
    
    if java_success and python_success:
        print("\n🚀 All systems go! The enhanced CallerIdentifier is ready for production.")
    else:
        print("\n🔧 Some issues detected. Please review the failed tests above.")

if __name__ == "__main__":
    main()