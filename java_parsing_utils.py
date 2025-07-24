#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Java parsing utility functions.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import argparse

# Import standard argument parser
try:
    from standard_arg_parser import create_standard_parser as create_parser
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False
    
    def create_parser(tool_type, description):
        return argparse.ArgumentParser(description=description)

# Import preflight checks
try:
    from preflight_checks import run_preflight_checks, PreflightChecker
except ImportError:
    def run_preflight_checks(checks, exit_on_fail=True):
        pass
    class PreflightChecker:
        @staticmethod
        def check_file_readable(path):
            return True, ""
        @staticmethod
        def check_directory_accessible(path):
            return True, ""
        @staticmethod
        def check_ripgrep_installed():
            return True, ""
        @staticmethod
        def check_regex_pattern(pattern):
            return True, ""

def extract_method_body(content, method_match):
    """
    Extract the complete method body from content given a regex match.
    
    Args:
        content (str): The complete file content
        method_match: A regex match object for the method signature
        
    Returns:
        dict: Method information including content, start_line, etc.
              Returns None if extraction fails
    """
    try:
        # Get the position after the method signature
        sig_end = method_match.end()
        
        # Find the opening brace
        brace_pos = content.find('{', sig_end)
        if brace_pos == -1:
            return None
            
        # Find the matching closing brace
        close_pos = find_closing_brace(content, brace_pos)
        if close_pos == -1:
            return None
            
        # Extract method content
        method_content = content[method_match.start():close_pos + 1]
        
        # Count lines before method
        lines_before = content[:method_match.start()].count('\n')
        
        return {
            'content': method_content,
            'start_line': lines_before + 1,
            'end_line': lines_before + method_content.count('\n') + 1,
            'name': method_match.group(5) if method_match.lastindex >= 5 else 'unknown'
        }
    except Exception:
        return None

def find_closing_brace(content, open_brace_pos):
    """
    Find the position of the matching closing brace '{' for a given opening brace.

    Args:
        content (str): The code content to search within.
        open_brace_pos (int): The index of the opening brace.

    Returns:
        int: The index of the matching closing brace, or -1 if not found.
    """
    if content[open_brace_pos] != '{':
        return -1

    brace_level = 1
    for i in range(open_brace_pos + 1, len(content)):
        char = content[i]
        if char == '{':
            brace_level += 1
        elif char == '}':
            brace_level -= 1
        
        if brace_level == 0:
            return i
    
    return -1  # Not found


if __name__ == "__main__":
    """
    This is a utility module containing Java parsing helper functions.
    It is not meant to be run directly, but imported by other tools.
    """
    parser = argparse.ArgumentParser(
        description="Java Parsing Utilities - Helper functions for parsing Java code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ABOUT THIS MODULE:
This module provides utility functions for parsing Java source code.
It is designed to be imported by other tools in the java-intelligence-analysis-toolkit.

AVAILABLE FUNCTIONS:
- extract_method_body(content, method_match): Extract complete method body from a regex match
- find_closing_brace(content, open_brace_pos): Find matching closing brace for an opening brace

USAGE EXAMPLES:

1. Import in your Python script:
   from java_parsing_utils import extract_method_body, find_closing_brace

2. Extract a method body:
   import re
   
   # Read Java file content
   with open("MyClass.java", "r") as f:
       content = f.read()
   
   # Find method signatures
   method_pattern = r"(public|private|protected)?\s*(static)?\s*(final)?\s*(\w+)\s+(\w+)\s*\("
   matches = re.finditer(method_pattern, content)
   
   for match in matches:
       method_info = extract_method_body(content, match)
       if method_info:
           print(f"Method: {method_info['name']}")
           print(f"Lines: {method_info['start_line']}-{method_info['end_line']}")
           print(f"Content:\\n{method_info['content']}")

3. Find matching braces:
   # Find the closing brace for an opening brace at position 100
   close_pos = find_closing_brace(content, 100)
   if close_pos != -1:
       block_content = content[100:close_pos+1]

DEMO:
Run with --demo to see a simple demonstration of the parsing functions.
        """
    )
    
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a simple demonstration of the parsing functions"
    )
    
    args = parser.parse_args()
    
    if args.demo:
        print("Java Parsing Utils Demo")
        print("=" * 50)
        
        # Demo Java code
        demo_code = """
public class DemoClass {
    private int value;
    
    public void setValue(int newValue) {
        this.value = newValue;
        System.out.println("Value set to: " + newValue);
    }
    
    public int getValue() {
        return this.value;
    }
}
"""
        
        print("Demo Java code:")
        print(demo_code)
        print("\n" + "=" * 50 + "\n")
        
        # Demonstrate method extraction
        import re
        method_pattern = r"(public|private|protected)?\s*(static)?\s*(final)?\s*(\w+)\s+(\w+)\s*\("
        matches = list(re.finditer(method_pattern, demo_code))
        
        print(f"Found {len(matches)} methods:\n")
        
        for match in matches:
            method_info = extract_method_body(demo_code, match)
            if method_info:
                print(f"Method: {method_info['name']}")
                print(f"Lines: {method_info['start_line']}-{method_info['end_line']}")
                print("Content:")
                print(method_info['content'])
                print("-" * 30)
        
        # Demonstrate brace finding
        print("\nBrace matching demo:")
        first_brace = demo_code.find("{")
        closing_brace = find_closing_brace(demo_code, first_brace)
        print(f"First opening brace at position: {first_brace}")
        print(f"Matching closing brace at position: {closing_brace}")
        print(f"Class block length: {closing_brace - first_brace + 1} characters")
    else:
        parser.print_help()
        print("\nNote: This is a utility module meant to be imported by other tools.")
        print("Use --demo to see a demonstration of the available functions.")