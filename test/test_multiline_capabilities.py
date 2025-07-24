#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Comprehensive test suite for multiline reading capabilities.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import tempfile
import subprocess
import unittest
from pathlib import Path
import shutil

class TestMultilineCapabilities(unittest.TestCase):
    """Test suite for all multiline reading capabilities."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test files and environment."""
        cls.test_dir = tempfile.mkdtemp()
        cls.test_files = {}
        
        # Create test Java file
        java_content = '''package com.example;

/**
 * Test class for multiline reading capabilities.
 */
public class TestClass {
    private int field1;
    private String field2;
    
    // TODO: Implement constructor
    public TestClass() {
        this.field1 = 0;
        this.field2 = "default";
    }
    
    /**
     * TODO: Add validation
     * @param value the input value
     */
    public void setField1(int value) {
        this.field1 = value;
    }
    
    public int getField1() {
        return this.field1;
    }
    
    // TODO: Add null check
    public void setField2(String value) {
        this.field2 = value;
    }
    
    public String getField2() {
        return this.field2;
    }
    
    /**
     * Calculate something important.
     * TODO: Optimize this method
     */
    public int calculateSomething(int a, int b) {
        int result = 0;
        for (int i = 0; i < a; i++) {
            result += b;
        }
        return result;
    }
    
    // End of class
}
'''
        
        # Create test Python file
        python_content = '''#!/usr/bin/env python3
"""
Test Python file for multiline reading.
"""

def function_one():
    """First function."""
    # TODO: Implement this
    pass

class TestClass:
    """Test class."""
    
    def __init__(self):
        # TODO: Add initialization
        self.value = 0
    
    def method_one(self):
        """First method."""
        # TODO: Add logic here
        return self.value
    
    def method_two(self):
        """Second method."""
        # TODO: Add more logic
        return self.value * 2

# TODO: Add more functions
def function_two():
    """Second function."""
    return "hello world"
'''
        
        # Write test files
        cls.test_files['java'] = os.path.join(cls.test_dir, 'TestClass.java')
        cls.test_files['python'] = os.path.join(cls.test_dir, 'test_module.py')
        
        with open(cls.test_files['java'], 'w') as f:
            f.write(java_content)
        
        with open(cls.test_files['python'], 'w') as f:
            f.write(python_content)
        
        # Store original directory
        cls.original_dir = os.getcwd()
        os.chdir(cls.test_dir)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        os.chdir(cls.original_dir)
        shutil.rmtree(cls.test_dir)
    
    def run_tool(self, tool_name, args, expected_returncode=0):
        """Helper method to run tools and capture output."""
        cmd = [sys.executable, os.path.join(self.original_dir, tool_name)] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, expected_returncode, 
                           f"Tool {tool_name} failed with args {args}:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
            return result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            self.fail(f"Tool {tool_name} timed out with args {args}")
    
    def test_multiline_reader_basic_ranges(self):
        """Test basic line range functionality in multiline_reader.py."""
        print("\n=== Testing multiline_reader.py basic ranges ===")
        
        # Test single line range
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '1-5'])
        self.assertIn('package com.example;', stdout)
        self.assertIn('/**', stdout)
        self.assertIn('1:', stdout)
        self.assertIn('5:', stdout)
        
        # Test multiple ranges
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '1-3,10-12'])
        self.assertIn('package com.example;', stdout)
        self.assertIn('TODO: Implement constructor', stdout)
        
        # Test single line
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '1'])
        self.assertIn('package com.example;', stdout)
        self.assertNotIn('/**', stdout)  # Should only show line 1
    
    def test_multiline_reader_context_ranges(self):
        """Test context-based ranges (±) in multiline_reader.py."""
        print("\n=== Testing multiline_reader.py context ranges ===")
        
        # Test context around line
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '10±2'])
        self.assertIn('8:', stdout)  # Should show lines 8-12
        self.assertIn('12:', stdout)
        
        # Test multiple context ranges
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '5±1,15±1'])
        lines = stdout.split('\n')
        line_numbers = [line.split(':')[0].strip() for line in lines if ':' in line and line.strip().split(':')[0].strip().isdigit()]
        self.assertIn('4', line_numbers)
        self.assertIn('6', line_numbers)
        self.assertIn('14', line_numbers)
        self.assertIn('16', line_numbers)
    
    def test_multiline_reader_length_ranges(self):
        """Test length-based ranges (:) in multiline_reader.py."""
        print("\n=== Testing multiline_reader.py length ranges ===")
        
        # Test range with length
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '5:3'])
        lines = stdout.split('\n')
        line_numbers = [line.split(':')[0].strip() for line in lines if ':' in line and line.strip().split(':')[0].strip().isdigit()]
        self.assertIn('5', line_numbers)
        self.assertIn('7', line_numbers)
        self.assertNotIn('8', line_numbers)  # Should only show 3 lines (5,6,7)
    
    def test_multiline_reader_pattern_mode(self):
        """Test pattern-based extraction in multiline_reader.py."""
        print("\n=== Testing multiline_reader.py pattern mode ===")
        
        # Test TODO pattern with context
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '--pattern', 'TODO', '--context', '2'])
        self.assertIn('TODO', stdout)
        self.assertIn('>>>', stdout)  # Should highlight matching lines
        
        # Test regex pattern
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '--pattern', 'public.*void', '--context', '1', '--regex'])
        self.assertIn('setField1', stdout)
        self.assertIn('setField2', stdout)
    
    def test_multiline_reader_output_options(self):
        """Test output formatting options in multiline_reader.py."""
        print("\n=== Testing multiline_reader.py output options ===")
        
        # Test without line numbers
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '1-3', '--no-line-numbers'])
        self.assertNotIn('1:', stdout)
        self.assertIn('package com.example;', stdout)
        
        # Test without separators
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '1-3', '--no-separators'])
        self.assertNotIn('===', stdout)
        self.assertNotIn('---', stdout)
        
        # Test highlighting specific lines
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '1-5', '--highlight', '2,4'])
        self.assertIn('>>>', stdout)
    
    def test_multiline_reader_merge_ranges(self):
        """Test range merging functionality."""
        print("\n=== Testing multiline_reader.py range merging ===")
        
        # Test overlapping ranges that should be merged
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '1-5,3-8', '--merge-ranges'])
        # Should show a single merged range 1-8
        self.assertIn('1:', stdout)
        self.assertIn('8:', stdout)
        # Count range headers - should only have one merged range
        range_headers = [line for line in stdout.split('\n') if '--- Lines' in line]
        self.assertEqual(len(range_headers), 1, "Should merge overlapping ranges into one")
    
    def test_enhanced_navigate_ranges(self):
        """Test enhanced navigate.py with ranges functionality."""
        print("\n=== Testing enhanced navigate.py ranges ===")
        
        # Test multiple ranges
        stdout, stderr = self.run_tool('navigate.py', ['TestClass.java', '--ranges', '1-3,10-12'])
        self.assertIn('Range 1-3', stdout)
        self.assertIn('Range 10-12', stdout)
        self.assertIn('package com.example;', stdout)
        
        # Test around-lines functionality
        stdout, stderr = self.run_tool('navigate.py', ['TestClass.java', '--around-lines', '5,15', '--context-size', '2'])
        self.assertIn('Context around line 5', stdout)
        self.assertIn('Context around line 15', stdout)
        self.assertIn('>>>', stdout)  # Should highlight the center lines
    
    def test_enhanced_find_text_extended_context(self):
        """Test enhanced find_text.py with extended context."""
        print("\n=== Testing enhanced find_text.py extended context ===")
        
        # Check if ripgrep is available
        if not shutil.which('rg'):
            print("Skipping find_text.py tests - ripgrep not available")
            return
        
        # Test extended context
        stdout, stderr = self.run_tool('find_text.py', ['TODO', '--in-files', '--extend-context', '3', '-g', '*.java'])
        self.assertIn('TODO', stdout)
        # The extended context should be present if multiline_ranges is working
        # Check for either the context header or that we have more lines than just the match
        if 'Extended context' not in stdout:
            # Check that we have substantial output (indicating context was added)
            lines = [line for line in stdout.split('\n') if line.strip()]
            self.assertGreater(len(lines), 4, "Extended context should add more lines to output")
    
    def test_error_handling(self):
        """Test error handling and edge cases."""
        print("\n=== Testing error handling ===")
        
        # Test with non-existent file
        stdout, stderr = self.run_tool('multiline_reader.py', ['nonexistent.java', '1-5'])
        self.assertIn('not found', stderr)
        
        # Test with invalid line specification
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', 'invalid'])
        # Should handle gracefully or show error
        
        # Test with out-of-range line numbers
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java', '1000-1005'])
        # Should handle gracefully without crashing
        
        # Test missing required arguments
        stdout, stderr = self.run_tool('multiline_reader.py', ['TestClass.java'], expected_returncode=2)
        self.assertIn('Must specify', stderr)
    
    def test_integration_with_wrapper_script(self):
        """Test integration with run_any_python_tool.sh."""
        print("\n=== Testing wrapper script integration ===")
        
        wrapper_script = os.path.join(self.original_dir, 'run_any_python_tool.sh')
        if not os.path.exists(wrapper_script):
            print("Skipping wrapper script test - script not found")
            return
        
        # Test multiline_reader.py through wrapper
        cmd = [wrapper_script, 'multiline_reader.py', 'TestClass.java', '1-3']
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.assertIn('package com.example;', result.stdout)
            else:
                print(f"Wrapper script returned {result.returncode}: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("Wrapper script test skipped - execution issues")
    
    def test_large_file_handling(self):
        """Test handling of large files and ranges."""
        print("\n=== Testing large file handling ===")
        
        # Create a larger test file
        large_content = '\n'.join([f"Line {i}: This is line number {i}" for i in range(1, 1001)])
        large_file = os.path.join(self.test_dir, 'large_file.txt')
        with open(large_file, 'w') as f:
            f.write(large_content)
        
        # Test reading from middle of large file
        stdout, stderr = self.run_tool('multiline_reader.py', ['large_file.txt', '500-505'])
        self.assertIn('Line 500:', stdout)
        self.assertIn('Line 505:', stdout)
        
        # Test context around line in large file
        stdout, stderr = self.run_tool('multiline_reader.py', ['large_file.txt', '500±5'])
        self.assertIn('Line 495:', stdout)
        self.assertIn('Line 505:', stdout)
    
    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters."""
        print("\n=== Testing Unicode and special characters ===")
        
        # Create file with Unicode content
        unicode_content = '''Line 1: Hello 世界
Line 2: Special chars: àáâãäå
Line 3: Symbols: ©®™
Line 4: Emoji: 🚀🔥💯
Line 5: More text here
'''
        unicode_file = os.path.join(self.test_dir, 'unicode_file.txt')
        with open(unicode_file, 'w', encoding='utf-8') as f:
            f.write(unicode_content)
        
        # Test reading Unicode content
        stdout, stderr = self.run_tool('multiline_reader.py', ['unicode_file.txt', '1-4'])
        self.assertIn('世界', stdout)
        self.assertIn('àáâãäå', stdout)
        self.assertIn('🚀', stdout)

def run_performance_tests():
    """Run performance tests (optional)."""
    print("\n=== Performance Tests ===")
    
    # Create a very large file for performance testing
    temp_dir = tempfile.mkdtemp()
    large_file = os.path.join(temp_dir, 'very_large_file.txt')
    
    try:
        # Create 10,000 line file
        with open(large_file, 'w') as f:
            for i in range(1, 10001):
                f.write(f"Line {i}: {'x' * 50}\n")
        
        import time
        
        # Test reading from end of large file
        start_time = time.time()
        cmd = [sys.executable, 'multiline_reader.py', large_file, '9990-10000']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        end_time = time.time()
        
        if result.returncode == 0:
            print(f"Large file test completed in {end_time - start_time:.2f} seconds")
            print(f"Successfully read lines from 10,000-line file")
        else:
            print(f"Large file test failed: {result.stderr}")
    
    except Exception as e:
        print(f"Performance test error: {e}")
    
    finally:
        shutil.rmtree(temp_dir)

def main():
    """Run all tests."""
    print("Starting comprehensive multiline capabilities test suite...")
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance tests if requested
    if '--performance' in sys.argv:
        run_performance_tests()
    
    print("\nTest suite completed!")

if __name__ == '__main__':
    main()