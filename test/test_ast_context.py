#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test file for AST context functionality"""

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-08
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

class TestClass:
    def __init__(self):
        self.counter = 0
        self.data = []
    
    def process_data(self, item):
        """Process a data item"""
        local_var = f"Processing: {item}"
        print(local_var)
        self.counter += 1
        self._helper_method()
        return local_var
    
    def _helper_method(self):
        """Helper method"""
        helper_var = "helper"
        print(helper_var)
        # Note: unused_method is never called
    
    def unused_method(self):
        """This method is never used"""
        return "never used"
    
    def get_counter(self):
        """Get the current counter value"""
        return self.counter

def standalone_function():
    """A standalone function outside the class"""
    test = TestClass()
    test.process_data("item1")
    print(f"Counter: {test.get_counter()}")
    
if __name__ == "__main__":
    standalone_function()