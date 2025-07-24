#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Comprehensive test runner for all Python tools in the toolkit.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import subprocess
import sys
import os
from pathlib import Path
import json
import time

# Base directory for test files
TEST_DIR = Path("test_code")
JAVA_DIR = TEST_DIR / "java"
PYTHON_DIR = TEST_DIR / "python"
MIXED_DIR = TEST_DIR / "mixed"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def run_tool(tool_name, args, expected_success=True):
    """Run a tool and return success status."""
    cmd = ["python3", tool_name] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        success = result.returncode == 0
        
        if expected_success and not success:
            print(f"{RED}✗ {tool_name}: Failed with return code {result.returncode}{RESET}")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}...")
        elif not expected_success and success:
            print(f"{YELLOW}⚠ {tool_name}: Succeeded when failure was expected{RESET}")
        else:
            print(f"{GREEN}✓ {tool_name}: {'Success' if success else 'Failed as expected'}{RESET}")
            
        return success == expected_success
    except subprocess.TimeoutExpired:
        print(f"{RED}✗ {tool_name}: Timeout after 10 seconds{RESET}")
        return False
    except Exception as e:
        print(f"{RED}✗ {tool_name}: Exception - {str(e)}{RESET}")
        return False

def test_search_tools():
    """Test all search and find tools."""
    print(f"\n{BLUE}=== Testing Search/Find Tools ==={RESET}")
    
    tests = [
        # find_text.py
        ("find_text.py", ["TODO", "--scope", str(JAVA_DIR), "-g", "*.java"]),
        ("find_text.py", ["processOrder", "--file", str(JAVA_DIR / "OrderProcessor.java")]),
        
        # find_files.py
        ("find_files.py", [str(TEST_DIR), "--ext", "java"]),
        ("find_files.py", [str(TEST_DIR), "--newer-than", "1d"]),
        
        # find_references_rg.py
        ("find_references_rg.py", ["calculate", "--scope", str(JAVA_DIR)]),
        
        # pattern_analysis.py
        ("pattern_analysis.py", ["TODO", "--scope", str(TEST_DIR), "--summary-only"]),
        
        # cross_file_analysis_ast.py
        ("cross_file_analysis_ast.py", ["process_data", "--scope", str(PYTHON_DIR), "--language", "python"]),
    ]
    
    return sum(run_tool(tool, args) for tool, args in tests)

def test_ast_tools():
    """Test all AST-based tools."""
    print(f"\n{BLUE}=== Testing AST Tools ==={RESET}")
    
    tests = [
        # navigate_ast_v2.py
        ("navigate_ast_v2.py", [str(PYTHON_DIR / "test_module.py"), "--to", "process_data"]),
        ("navigate_ast_v2.py", [str(JAVA_DIR / "Calculator.java"), "--to", "calculate"]),
        
        # method_analyzer_ast_v2.py
        ("method_analyzer_ast_v2.py", ["process", "--file", str(PYTHON_DIR / "data_processor.py")]),
        
        # show_structure_ast_v4.py
        ("show_structure_ast_v4.py", [str(PYTHON_DIR / "ast_test.py"), "--max-depth", "3"]),
        ("show_structure_ast_v4.py", [str(JAVA_DIR / "TestClass.java")]),
        
        # ast_context_finder.py (needs dummy target when using standard parser)
        ("ast_context_finder.py", ["dummy", "--file", str(PYTHON_DIR / "test_module.py"), "50"]),
        
        # replace_text_ast.py (dry run)
        ("replace_text_ast.py", ["myVar", "my_variable", "--file", str(PYTHON_DIR / "refactor_example.py"), "--line", "10", "--dry-run"]),
    ]
    
    return sum(run_tool(tool, args) for tool, args in tests)

def test_file_tools():
    """Test file and directory management tools."""
    print(f"\n{BLUE}=== Testing File/Directory Tools ==={RESET}")
    
    tests = [
        # smart_ls.py
        ("smart_ls.py", [str(TEST_DIR), "--ext", "java"]),
        ("smart_ls.py", [str(MIXED_DIR), "--long", "--sort", "size"]),
        
        # tree_view.py
        ("tree_view.py", [str(TEST_DIR), "--max-depth", "2"]),
        
        # dir_stats.py
        ("dir_stats.py", [str(TEST_DIR), "--detailed"]),
        
        # recent_files_v2.py
        ("recent_files_v2.py", ["--since", "1d", str(TEST_DIR), "--limit", "5"]),
        
        # organize_files.py (dry run)
        ("organize_files.py", [str(MIXED_DIR), "--by-ext", "--dry-run"]),
    ]
    
    return sum(run_tool(tool, args) for tool, args in tests)

def test_analysis_tools():
    """Test code analysis tools."""
    print(f"\n{BLUE}=== Testing Analysis Tools ==={RESET}")
    
    tests = [
        # dead_code_detector.py
        ("dead_code_detector.py", [str(JAVA_DIR), "--language", "java"]),
        ("dead_code_detector.py", [str(PYTHON_DIR), "--language", "python", "--confidence", "high"]),
        
        # suggest_refactoring.py
        ("suggest_refactoring.py", [str(JAVA_DIR / "RefactoringCandidate.java")]),
        
        # analyze_unused_methods_with_timeout.py
        ("analyze_unused_methods_with_timeout.py", [str(JAVA_DIR / "UnusedCodeExample.java")]),
        
        # trace_calls_with_timeout.py
        ("trace_calls_with_timeout.py", ["processOrder", "--scope", str(JAVA_DIR), "--max-depth", "3"]),
        
        # analyze_internal_usage.py
        ("analyze_internal_usage.py", ["--file", str(JAVA_DIR / "Calculator.java")]),
        
        # method_analyzer.py
        ("method_analyzer.py", ["calculate", "--scope", str(JAVA_DIR)]),
    ]
    
    return sum(run_tool(tool, args) for tool, args in tests)

def test_java_specific_tools():
    """Test Java-specific tools."""
    print(f"\n{BLUE}=== Testing Java-Specific Tools ==={RESET}")
    
    tests = [
        # check_java_structure.py
        ("check_java_structure.py", ["TestClass", "--file", str(JAVA_DIR / "TestClass.java")]),
        
        # java_tools_batch.py
        ("java_tools_batch.py", ["check-structure", str(JAVA_DIR)]),
        
        # extract_class_structure.py
        ("extract_class_structure.py", [str(JAVA_DIR / "OrderProcessor.java")]),
    ]
    
    return sum(run_tool(tool, args) for tool, args in tests)

def test_utility_tools():
    """Test utility and special-purpose tools."""
    print(f"\n{BLUE}=== Testing Utility Tools ==={RESET}")
    
    tests = [
        # log_analyzer.py
        ("log_analyzer.py", ["--pattern", "ERROR", "--files", str(MIXED_DIR / "log_file.log")]),
        
        # multiline_reader.py
        ("multiline_reader.py", [str(MIXED_DIR / "README.md"), "--pattern", "Configuration"]),
        
        # semantic_diff.py
        ("semantic_diff.py", [str(JAVA_DIR / "Calculator.java"), str(JAVA_DIR / "TestClass.java")]),
        
        # pattern_counter.py (if it exists)
        # ("pattern_counter.py", ["TODO", "--scope", str(TEST_DIR)]),
    ]
    
    return sum(run_tool(tool, args) for tool, args in tests)

def main():
    """Run all tests and report results."""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Python Toolkit Comprehensive Test Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Check if test directory exists
    if not TEST_DIR.exists():
        print(f"{RED}Error: Test directory '{TEST_DIR}' not found!{RESET}")
        sys.exit(1)
    
    # Run all test categories
    results = {
        "Search/Find Tools": test_search_tools(),
        "AST Tools": test_ast_tools(),
        "File/Directory Tools": test_file_tools(),
        "Analysis Tools": test_analysis_tools(),
        "Java-Specific Tools": test_java_specific_tools(),
        "Utility Tools": test_utility_tools(),
    }
    
    # Calculate totals
    test_counts = {
        "Search/Find Tools": 7,
        "AST Tools": 7,
        "File/Directory Tools": 6,
        "Analysis Tools": 7,
        "Java-Specific Tools": 3,
        "Utility Tools": 3
    }
    total_tests = sum(test_counts.values())
    total_passed = sum(results.values())
    
    # Print summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    for category, passed in results.items():
        print(f"{category}: {passed} tests passed")
    
    print(f"\n{BLUE}Overall: {total_passed}/{total_tests} tests passed ({total_passed/total_tests*100:.1f}%){RESET}")
    
    if total_passed == total_tests:
        print(f"\n{GREEN}✅ All tests passed! The toolkit is fully functional.{RESET}")
    else:
        print(f"\n{RED}❌ Some tests failed. Please review the output above.{RESET}")
    
    return 0 if total_passed == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())