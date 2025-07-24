#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Comprehensive test file for scope-aware refactoring.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

# Test 1: Global vs Local variables with same name
counter = 0  # Global counter

def increment_global():
    """Uses global counter."""
    global counter
    counter += 1
    return counter

def process_items():
    """Has local counter."""
    counter = 100  # Local counter - different from global
    
    for i in range(5):
        counter += i  # Uses local counter
    
    return counter

class Statistics:
    """Has instance counter."""
    def __init__(self):
        self.counter = 1000  # Instance attribute
    
    def update_counter(self):
        counter = 2000  # Method-local variable
        self.counter += counter
        return self.counter

# Test 2: Nested functions with closures
def outer_calculator():
    """Test nested function scopes."""
    multiplier = 2  # Outer function variable
    
    def calculate(value):
        """Uses closure variable."""
        return value * multiplier
    
    def nested_processor():
        multiplier = 10  # Shadows outer multiplier
        
        def calculate(x):
            """Different calculate function."""
            return x + multiplier
        
        return calculate(5)  # Uses nested calculate
    
    # Uses outer calculate
    result1 = calculate(20)
    result2 = nested_processor()
    
    return result1, result2

# Test 3: Class methods and static methods
class Calculator:
    """Test class-level definitions."""
    factor = 1.5  # Class variable
    
    def __init__(self):
        self.factor = 2.0  # Instance variable (different from class var)
    
    def calculate(self, value):
        """Instance method."""
        return value * self.factor
    
    @classmethod
    def calculate_with_class(cls, value):
        """Class method - uses class variable."""
        return value * cls.factor
    
    @staticmethod
    def calculate_static(value):
        """Static method - no access to instance/class."""
        factor = 3.0  # Local variable
        return value * factor

# Test 4: Import-related names
import math
from math import sqrt
from math import pow as power

def calculate_hypotenuse(a, b):
    """Uses imported names."""
    # Using different import styles
    return math.sqrt(power(a, 2) + power(b, 2))

# Test 5: Comprehensions have their own scope
values = [1, 2, 3, 4, 5]
result = [value * 2 for value in values]  # 'value' is local to comprehension
value = 100  # Different 'value' in module scope

# Test 6: Global and nonlocal declarations
def complex_scoping():
    """Test global and nonlocal keywords."""
    state = "function"
    
    def modify_global():
        global counter  # Refers to module-level counter
        counter = 999
    
    def modify_enclosing():
        nonlocal state  # Refers to complex_scoping's state
        state = "modified"
    
    def create_new_local():
        state = "local"  # New local variable
        counter = -1     # New local variable
        return state, counter
    
    modify_global()
    modify_enclosing()
    local_values = create_new_local()
    
    return state, counter, local_values

# Test 7: Same name used in different contexts
def process(data):
    """Function named 'process'."""
    return data * 2

class Processor:
    """Has method named 'process'."""
    def process(self, data):
        return data * 3

process_lambda = lambda x: x * 4  # Lambda named 'process_lambda'

# Test 8: Decorators and function references
def logger(func):
    """Decorator function."""
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@logger
def process_data(data):
    """Decorated function."""
    return process(data)  # Calls global process function

# Test 9: Type annotations and variable declarations
from typing import List, Optional

def typed_function(items: List[int]) -> Optional[int]:
    """Function with type annotations."""
    total: int = 0  # Type-annotated variable
    
    for item in items:
        total += item
    
    return total if total > 0 else None

# Test 10: Exception handling scopes
def error_handler():
    """Test exception variable scoping."""
    error = None  # Pre-defined variable
    
    try:
        risky_operation()
    except Exception as error:  # 'error' is local to except block in Python 3
        print(f"Caught: {error}")
    
    # 'error' here refers to the pre-defined one, not the exception
    return error

# Test usage of all the above
if __name__ == "__main__":
    # Test global counter
    print(f"Global counter: {counter}")
    print(f"After increment: {increment_global()}")
    print(f"Local counter result: {process_items()}")
    
    # Test class
    stats = Statistics()
    print(f"Instance counter: {stats.update_counter()}")
    
    # Test nested functions
    r1, r2 = outer_calculator()
    print(f"Nested results: {r1}, {r2}")
    
    # Test Calculator class
    calc = Calculator()
    print(f"Instance calculate: {calc.calculate(10)}")
    print(f"Class calculate: {Calculator.calculate_with_class(10)}")
    print(f"Static calculate: {Calculator.calculate_static(10)}")
    
    # Test imports
    print(f"Hypotenuse: {calculate_hypotenuse(3, 4)}")
    
    # Test complex scoping
    state, global_counter, local_vals = complex_scoping()
    print(f"Complex scoping: state={state}, counter={global_counter}, local={local_vals}")
    
    # Test different process functions
    print(f"Global process: {process(5)}")
    print(f"Class process: {Processor().process(5)}")
    print(f"Lambda process: {process_lambda(5)}")
    
    # Test decorated function
    print(f"Decorated: {process_data(5)}")
    
    # Test typed function
    print(f"Typed result: {typed_function([1, 2, 3, 4, 5])}")