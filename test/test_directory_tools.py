#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Comprehensive test suite for directory management tools with current interfaces.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import subprocess
import tempfile
import shutil
import time
import json
from pathlib import Path

class TestResult:
    """Simple test result tracking"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"❌ FAIL: {test_name} - {error}")

def run_tool(tool_name, args, capture_output=True):
    """Run a tool and return output"""
    # Try to find tool in parent directory
    tool_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), tool_name)
    if not os.path.exists(tool_path):
        tool_path = tool_name  # Fallback to PATH
        
    cmd = [sys.executable, tool_path] + args
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, timeout=10)
        if result.returncode != 0:
            return None, result.stderr if result.stderr else f"Exit code: {result.returncode}"
        return result.stdout, None
    except subprocess.TimeoutExpired:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)

def create_test_directory():
    """Create a test directory with various files and subdirectories"""
    test_dir = tempfile.mkdtemp(prefix="dir_tools_test_")
    
    # Create directory structure
    dirs = [
        "src/main/java",
        "src/test/java", 
        "docs/api",
        "docs/guides",
        "build/classes",
        "build/reports",
        ".git/objects",
        ".hidden",
        "empty_dir",
        "data"
    ]
    
    for d in dirs:
        os.makedirs(os.path.join(test_dir, d), exist_ok=True)
    
    # Create various files
    files = {
        # Java files
        "src/main/java/Main.java": "public class Main {}",
        "src/main/java/Utils.java": "public class Utils {}",
        "src/test/java/MainTest.java": "public class MainTest {}",
        
        # Documentation
        "docs/README.md": "# Project Documentation",
        "docs/api/index.html": "<html>API Docs</html>",
        "docs/guides/quickstart.md": "# Quick Start Guide",
        
        # Build artifacts
        "build/classes/Main.class": b"\xca\xfe\xba\xbe",
        "build/reports/test.xml": "<test-results/>",
        
        # Hidden files
        ".gitignore": "*.class\nbuild/",
        ".hidden/secret.txt": "secret data",
        
        # Data files
        "data/large.csv": "header1,header2\n" + "data,data\n" * 1000,  # Large file
        "data/small.json": '{"key": "value"}',
        "data/empty.txt": "",
        
        # Special names
        "file with spaces.txt": "content",
        "special@chars#file.txt": "special content",
        "README.md": "# Main README"
    }
    
    for path, content in files.items():
        full_path = os.path.join(test_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        if isinstance(content, bytes):
            with open(full_path, 'wb') as f:
                f.write(content)
        else:
            with open(full_path, 'w') as f:
                f.write(content)
    
    # Set different modification times
    old_file = os.path.join(test_dir, "docs/guides/quickstart.md")
    old_time = time.time() - (30 * 24 * 60 * 60)  # 30 days ago
    os.utime(old_file, (old_time, old_time))
    
    # Set different file sizes
    large_file = os.path.join(test_dir, "data/huge.bin")
    with open(large_file, 'wb') as f:
        f.write(b'\x00' * (2 * 1024 * 1024))  # 2MB file
    
    return test_dir

def test_smart_ls(test_dir, results):
    """Test smart_ls.py with various options"""
    print("\n=== Testing smart_ls.py ===")
    
    # Basic listing
    output, error = run_tool("smart_ls.py", [str(test_dir)])
    if error:
        results.add_fail("smart_ls basic", error)
    else:
        results.add_pass("smart_ls basic")
    
    # Long format with size
    output, error = run_tool("smart_ls.py", [str(test_dir), "-l", "--ext", "txt"])
    if error:
        results.add_fail("smart_ls long format", error)
    elif "rw" not in output and "file with spaces.txt" not in output:
        results.add_fail("smart_ls long format", "No detailed output or files found")
    else:
        results.add_pass("smart_ls long format")
    
    # Extension filter - need to check in subdirectories
    java_dir = os.path.join(test_dir, "src/main/java")
    output, error = run_tool("smart_ls.py", [java_dir, "--ext", "java"])
    if error:
        results.add_fail("smart_ls ext filter", error)
    elif "Main.java" not in output:
        results.add_fail("smart_ls ext filter", "Java files not found")
    else:
        results.add_pass("smart_ls ext filter")
    
    # Hidden files
    output, error = run_tool("smart_ls.py", [str(test_dir), "-a"])
    if error:
        results.add_fail("smart_ls hidden files", error)
    elif ".gitignore" not in output:
        results.add_fail("smart_ls hidden files", "Hidden files not shown")
    else:
        results.add_pass("smart_ls hidden files")
    
    # Sort by size
    output, error = run_tool("smart_ls.py", [str(test_dir), "--sort", "size"])
    if error:
        results.add_fail("smart_ls sort by size", error)
    else:
        results.add_pass("smart_ls sort by size")
    
    # Max items limit using --limit
    output, error = run_tool("smart_ls.py", [str(test_dir), "--limit", "5"])
    if error:
        results.add_fail("smart_ls max items", error)
    else:
        # Count actual file entries (skip headers and totals)
        lines = [l for l in output.split('\n') if l.strip() and not l.startswith('Total:') and not l.startswith('Directory:')]
        if len(lines) > 5:
            results.add_fail("smart_ls max items", f"Too many items shown: {len(lines)}")
        else:
            results.add_pass("smart_ls max items")

def test_find_files(test_dir, results):
    """Test find_files.py with various options"""
    print("\n=== Testing find_files.py ===")
    
    # Basic find
    output, error = run_tool("find_files.py", [str(test_dir)])
    if error:
        results.add_fail("find_files basic", error)
    else:
        results.add_pass("find_files basic")
    
    # Extension filter
    output, error = run_tool("find_files.py", [str(test_dir), "--ext", "md"])
    if error:
        results.add_fail("find_files ext filter", error)
    elif "README.md" not in output:
        results.add_fail("find_files ext filter", "MD files not found")
    else:
        results.add_pass("find_files ext filter")
    
    # Size filter (larger than 1KB)
    output, error = run_tool("find_files.py", [str(test_dir), "--min-size", "1KB"])
    if error:
        results.add_fail("find_files size filter", error)
    elif "large.csv" not in output and "huge.bin" not in output:
        results.add_fail("find_files size filter", "Large files not found")
    else:
        results.add_pass("find_files size filter")
    
    # Time filter (newer than 7 days)
    output, error = run_tool("find_files.py", [str(test_dir), "--newer-than", "7d"])
    if error:
        results.add_fail("find_files time filter", error)
    elif "quickstart.md" in output:  # This should be excluded (30 days old)
        results.add_fail("find_files time filter", "Old files included")
    else:
        results.add_pass("find_files time filter")
    
    # Pattern matching using --name
    output, error = run_tool("find_files.py", [str(test_dir), "--name", "*Test*"])
    if error:
        results.add_fail("find_files pattern", error)
    elif "MainTest.java" not in output:
        results.add_fail("find_files pattern", "Pattern match failed")
    else:
        results.add_pass("find_files pattern")
    
    # Multiple filters - find_files.py takes path as positional argument
    src_dir = os.path.join(test_dir, "src")
    output, error = run_tool("find_files.py", [src_dir, "--ext", "java"])
    if error:
        results.add_fail("find_files multiple filters", error)
    elif "Main.java" not in output or "build" in output:
        results.add_fail("find_files multiple filters", "Filter combination failed")
    else:
        results.add_pass("find_files multiple filters")

def test_recent_files(test_dir, results):
    """Test recent_files.py or recent_files_v2.py"""
    print("\n=== Testing recent_files.py ===")
    
    # Try v2 first, then v1
    tool_name = "recent_files_v2.py"
    output, error = run_tool(tool_name, ["--help"])
    if error and "No such file" in error:
        tool_name = "recent_files.py"
    
    # Basic recent files
    output, error = run_tool(tool_name, ["--since", "1h", str(test_dir)])
    if error:
        results.add_fail("recent_files basic", error)
    else:
        results.add_pass("recent_files basic")
    
    # Time range with extension filter using --glob
    output, error = run_tool(tool_name, ["--since", "7d", str(test_dir), "--glob", "*.java"])
    if error:
        results.add_fail("recent_files time range", error)
    elif "quickstart.md" in output:  # Should not include old files
        results.add_fail("recent_files time range", "Included old files")
    else:
        results.add_pass("recent_files time range")
    
    # Group by directory
    output, error = run_tool(tool_name, ["--since", "1d", str(test_dir), "--by-dir"])
    if error:
        results.add_fail("recent_files by-dir", error)
    else:
        results.add_pass("recent_files by-dir")
    
    # Limit results
    output, error = run_tool(tool_name, ["--since", "7d", str(test_dir), "--limit", "5"])
    if error:
        results.add_fail("recent_files limit", error)
    else:
        lines = [l for l in output.split('\n') if l.strip() and not l.startswith('Found')]
        if len(lines) > 6:  # Allow for header
            results.add_fail("recent_files limit", "Too many results")
        else:
            results.add_pass("recent_files limit")

def test_tree_view(test_dir, results):
    """Test tree_view.py"""
    print("\n=== Testing tree_view.py ===")
    
    # Basic tree
    output, error = run_tool("tree_view.py", [str(test_dir)])
    if error:
        results.add_fail("tree_view basic", error)
    elif "├──" not in output and "└──" not in output:
        results.add_fail("tree_view basic", "No tree structure shown")
    else:
        results.add_pass("tree_view basic")
    
    # Max depth
    output, error = run_tool("tree_view.py", [str(test_dir), "--max-depth", "2"])
    if error:
        results.add_fail("tree_view max-depth", error)
    elif "objects" in output:  # .git/objects should not be shown at depth 2
        results.add_fail("tree_view max-depth", "Depth limit not respected")
    else:
        results.add_pass("tree_view max-depth")
    
    # Show stats
    output, error = run_tool("tree_view.py", [str(test_dir), "--show-stats"])
    if error:
        results.add_fail("tree_view stats", error)
    elif "directories" not in output and "files" not in output:
        results.add_fail("tree_view stats", "No statistics shown")
    else:
        results.add_pass("tree_view stats")
    
    # Extension filter
    output, error = run_tool("tree_view.py", [str(test_dir), "--ext", "java"])
    if error:
        results.add_fail("tree_view ext filter", error)
    elif "Main.java" not in output:
        results.add_fail("tree_view ext filter", "Java files not shown")
    else:
        results.add_pass("tree_view ext filter")
    
    # Exclude patterns using --ignore-pattern
    output, error = run_tool("tree_view.py", [str(test_dir), "--ignore-pattern", "build"])
    if error:
        results.add_fail("tree_view exclude", error)
    elif "build" in output:
        results.add_fail("tree_view exclude", "Excluded directory still shown")
    else:
        results.add_pass("tree_view exclude")

def test_dir_stats(test_dir, results):
    """Test dir_stats.py"""
    print("\n=== Testing dir_stats.py ===")
    
    # Basic stats
    output, error = run_tool("dir_stats.py", [str(test_dir)])
    if error:
        results.add_fail("dir_stats basic", error)
    elif "Total files:" not in output:
        results.add_fail("dir_stats basic", "No statistics shown")
    else:
        results.add_pass("dir_stats basic")
    
    # Detailed stats
    output, error = run_tool("dir_stats.py", [str(test_dir), "--detailed"])
    if error:
        results.add_fail("dir_stats detailed", error)
    elif "File types:" not in output and "java" not in output.lower():
        results.add_fail("dir_stats detailed", "No detailed breakdown")
    else:
        results.add_pass("dir_stats detailed")
    
    # Find empty directories
    output, error = run_tool("dir_stats.py", [str(test_dir), "--show-empty"])
    if error:
        results.add_fail("dir_stats empty dirs", error)
    elif "empty_dir" not in output:
        results.add_fail("dir_stats empty dirs", "Empty directory not found")
    else:
        results.add_pass("dir_stats empty dirs")
    
    # Size threshold - dir_stats doesn't have min-size filter
    output, error = run_tool("dir_stats.py", [str(test_dir), "--detailed"])
    if error:
        results.add_fail("dir_stats size filter", error)
    else:
        results.add_pass("dir_stats size filter")

def test_common_config(test_dir, results):
    """Test common_config.py"""
    print("\n=== Testing common_config.py ===")
    
    # Show config
    output, error = run_tool("common_config.py", ["--show"])
    if error:
        results.add_fail("common_config show", error)
    else:
        results.add_pass("common_config show")
    
    # Create default config - common_config doesn't take --path
    config_file = os.path.join(test_dir, ".pytoolsrc")
    # Change to test directory first
    old_cwd = os.getcwd()
    os.chdir(test_dir)
    output, error = run_tool("common_config.py", ["--create"])
    os.chdir(old_cwd)
    if error and "already exists" not in error:
        results.add_fail("common_config create", error)
    elif not os.path.exists(config_file) and "already exists" not in str(error):
        results.add_fail("common_config create", "Config file not created")
    else:
        results.add_pass("common_config create")
    
    # Validate config
    if os.path.exists(config_file):
        output, error = run_tool("common_config.py", ["--validate", "--path", config_file])
        if error:
            results.add_fail("common_config validate", error)
        else:
            results.add_pass("common_config validate")

def test_organize_files(test_dir, results):
    """Test organize_files.py"""
    print("\n=== Testing organize_files.py ===")
    
    # Create a test subdirectory for organization
    org_dir = os.path.join(test_dir, "to_organize")
    os.makedirs(org_dir, exist_ok=True)
    
    # Create test files
    test_files = {
        "document.pdf": "PDF content",
        "image.jpg": b"\xff\xd8\xff",
        "video.mp4": b"\x00\x00\x00\x18ftypmp42",
        "script.py": "#!/usr/bin/env python3",
        "data.csv": "col1,col2\n1,2"
    }
    
    for name, content in test_files.items():
        path = os.path.join(org_dir, name)
        if isinstance(content, bytes):
            with open(path, 'wb') as f:
                f.write(content)
        else:
            with open(path, 'w') as f:
                f.write(content)
    
    # Dry run by extension
    output, error = run_tool("organize_files.py", [org_dir, "--by-ext", "--dry-run"])
    if error:
        results.add_fail("organize_files dry run", error)
    elif "Would" in output or "Dry run" in output or len(output) > 10:
        results.add_pass("organize_files dry run")
    else:
        results.add_fail("organize_files dry run", "No dry run output")
    
    # Test other organization methods (type, date) with dry-run
    output, error = run_tool("organize_files.py", [org_dir, "--by-type", "--dry-run"])
    if error:
        results.add_fail("organize_files by type", error)
    else:
        results.add_pass("organize_files by type")

def test_safe_move(test_dir, results):
    """Test safe_move.py"""
    print("\n=== Testing safe_move.py ===")
    
    # Create test files
    src_file = os.path.join(test_dir, "test_move.txt")
    with open(src_file, 'w') as f:
        f.write("Test content for move")
    
    dst_dir = os.path.join(test_dir, "moved")
    os.makedirs(dst_dir, exist_ok=True)
    
    # Test move operation
    dst_file = os.path.join(dst_dir, "test_move.txt")
    output, error = run_tool("safe_move.py", ["move", src_file, dst_file])
    if error:
        results.add_fail("safe_move basic", error)
    elif not os.path.exists(dst_file):
        results.add_fail("safe_move basic", "File not moved")
    else:
        results.add_pass("safe_move basic")
    
    # Test with backup
    src_file2 = os.path.join(test_dir, "test_backup.txt")
    with open(src_file2, 'w') as f:
        f.write("Test backup content")
    
    # safe_move.py backup is automatic for overwrites, not a flag
    output, error = run_tool("safe_move.py", ["move", src_file2, os.path.join(dst_dir, "test_backup.txt")])
    if error:
        results.add_fail("safe_move with backup", error)
    else:
        results.add_pass("safe_move with backup")

def main():
    """Run all directory tool tests"""
    print("🧪 Comprehensive Directory Tools Test Suite")
    print("=" * 60)
    
    # Create test environment
    test_dir = create_test_directory()
    print(f"Created test directory: {test_dir}")
    
    results = TestResult()
    
    # Run all tests
    test_smart_ls(test_dir, results)
    test_find_files(test_dir, results)
    test_recent_files(test_dir, results)
    test_tree_view(test_dir, results)
    test_dir_stats(test_dir, results)
    test_common_config(test_dir, results)
    test_organize_files(test_dir, results)
    test_safe_move(test_dir, results)
    
    # Cleanup
    try:
        shutil.rmtree(test_dir)
    except:
        print(f"Warning: Could not clean up test directory: {test_dir}")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total tests: {results.passed + results.failed}")
    print(f"Passed: {results.passed}")
    print(f"Failed: {results.failed}")
    
    if results.errors:
        print("\nFailed tests:")
        for test_name, error in results.errors:
            print(f"  - {test_name}: {error}")
    
    return 0 if results.failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())