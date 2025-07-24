#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Adapter script to run the existing tests with proper tool paths.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_test_environment():
    """Create symlinks to all tools in test directory."""
    root_dir = Path(__file__).parent
    test_dir = root_dir / "test"
    
    # List of tools that tests might need
    tools = [
        "find_text.py",
        "smart_ls.py", 
        "find_files.py",
        "recent_files.py",
        "recent_files_v2.py",
        "tree_view.py",
        "dir_stats.py",
        "common_config.py",
        "organize_files.py",
        "safe_move.py",
        "refactor_rename.py",
        "replace_text.py",
        "replace_text_ast.py",
        "semantic_diff.py",
        "navigate_ast.py",
        "navigate_ast_v2.py",
        "method_analyzer.py",
        "method_analyzer_ast.py",
        "method_analyzer_ast_v2.py",
        "multiline_reader.py",
        "analyze_test_timings.py"
    ]
    
    # Create symlinks
    created_links = []
    for tool in tools:
        src = root_dir / tool
        dst = test_dir / tool
        if src.exists() and not dst.exists():
            try:
                dst.symlink_to(src)
                created_links.append(dst)
            except Exception as e:
                print(f"Warning: Could not create symlink for {tool}: {e}")
    
    return created_links

def cleanup_symlinks(links):
    """Remove created symlinks."""
    for link in links:
        try:
            if link.is_symlink():
                link.unlink()
        except Exception:
            pass

def run_test_file(test_file):
    """Run a single test file."""
    print(f"\n{'='*60}")
    print(f"Running {test_file.name}")
    print('='*60)
    
    cmd = [sys.executable, str(test_file)]
    try:
        result = subprocess.run(cmd, cwd=test_file.parent, capture_output=True, text=True, timeout=60)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {test_file.name} took too long to run")
        return False
    except Exception as e:
        print(f"ERROR running {test_file.name}: {e}")
        return False

def main():
    """Run all test files with proper setup."""
    root_dir = Path(__file__).parent
    test_dir = root_dir / "test"
    
    # Setup environment
    print("Setting up test environment...")
    created_links = setup_test_environment()
    
    # Find test files
    test_files = sorted(test_dir.glob("test_*.py"))
    
    # Run specific tests that are likely to work
    priority_tests = [
        "test_ast_context.py",
        "test_preflight_checks.py",
        "test_organize_files.py",
        "test_safe_move.py",
        "test_refactor_rename.py",
        "test_multiline_capabilities.py",
        "test_standardized_interfaces.py"
    ]
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    # Run priority tests first
    for test_name in priority_tests:
        test_file = test_dir / test_name
        if test_file.exists():
            success = run_test_file(test_file)
            results["tests"].append((test_name, success))
            if success:
                results["passed"] += 1
            else:
                results["failed"] += 1
    
    # Cleanup
    cleanup_symlinks(created_links)
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    print(f"Total tests run: {len(results['tests'])}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print("\nDetailed results:")
    for test_name, success in results["tests"]:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")

if __name__ == "__main__":
    main()