#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
public class MyClass {

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

from java_parsing_utils import find_closing_brace

def test_find_closing_brace():
    content = """
    public class MyClass {
        public void myMethod() {
            if (true) {
                // some code
            }
        }
    }
    """
    # Test case 1: Simple method
    start_pos = content.find("{") 
    end_pos = find_closing_brace(content, start_pos)
    print(f"Test 1: Start: {start_pos}, End: {end_pos}")
    assert end_pos == content.rfind("}")

    # Test case 2: Nested braces
    start_pos = content.find("if (true) {") + len("if (true) {") - 1
    end_pos = find_closing_brace(content, start_pos)
    print(f"Test 2: Start: {start_pos}, End: {end_pos}")
    assert end_pos == content.find("}")

    # Test case 3: No closing brace
    start_pos = content.find("public class MyClass {") + len("public class MyClass {") - 1
    content_no_close = content[:start_pos+1] + content[start_pos+2:].replace("}", "", 1)
    end_pos = find_closing_brace(content_no_close, start_pos)
    print(f"Test 3: Start: {start_pos}, End: {end_pos}")
    assert end_pos == -1

test_find_closing_brace()
