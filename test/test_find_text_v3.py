#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test file for find_text_v3.py functionality"""

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-09
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

class TestClass:
    """A test class with various methods"""
    
    def __init__(self):
        self.value = 42
        self.name = "test"
    
    def calculate_sum(self, a, b):
        """Calculate the sum of two numbers"""
        result = a + b
        print(f"The sum is: {result}")
        return result
    
    def process_data(self, data):
        """Process some data"""
        if not data:
            print("No data to process")
            return None
        
        processed = []
        for item in data:
            if isinstance(item, int):
                processed.append(item * 2)
            else:
                processed.append(str(item).upper())
        
        print(f"Processed {len(processed)} items")
        return processed

class AnotherClass:
    """Another test class"""
    
    def method_with_pattern(self):
        """This method contains the pattern we're looking for"""
        pattern = "SEARCH_PATTERN"
        print(f"Found the {pattern} here!")
        return pattern
    
    def nested_function_example(self):
        """Example with nested function"""
        def inner_function():
            result = "SEARCH_PATTERN in nested function"
            return result
        
        return inner_function()

def standalone_function():
    """A standalone function outside of any class"""
    value = "SEARCH_PATTERN in standalone"
    print(value)
    return value

# Global variable
GLOBAL_PATTERN = "SEARCH_PATTERN at module level"

if __name__ == "__main__":
    test = TestClass()
    test.calculate_sum(10, 20)
    test.process_data([1, 2, "hello"])