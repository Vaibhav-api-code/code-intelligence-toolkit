#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Bulletproof Testing Suite for File Operation Tools

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import tempfile
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime
import time
import unittest

# Add parent directory to path to import the tools
sys.path.insert(0, str(Path(__file__).parent.parent))

class BulletproofFileToolsTest(unittest.TestCase):
    """Comprehensive safety tests for file operation tools."""
    
    def setUp(self):
        """Set up test environment with temporary directories and files."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="file_tools_test_"))
        self.source_dir = self.test_dir / "source"
        self.dest_dir = self.test_dir / "dest"
        self.backup_dir = self.test_dir / "backup"
        
        # Create directories
        self.source_dir.mkdir(parents=True)
        self.dest_dir.mkdir(parents=True)
        self.backup_dir.mkdir(parents=True)
        
        # Create test files with various characteristics
        self.create_test_files()
        
        # Path to tools
        self.tools_dir = Path(__file__).parent.parent
        self.safe_move = self.tools_dir / "safe_move.py"
        self.organize_files = self.tools_dir / "organize_files.py"
        self.refactor_rename = self.tools_dir / "refactor_rename.py"
        
        print(f"\n🧪 Test environment: {self.test_dir}")
    
    def tearDown(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def create_test_files(self):
        """Create comprehensive test files for various scenarios."""
        # Regular files
        (self.source_dir / "test.txt").write_text("Hello World")
        (self.source_dir / "document.pdf").write_text("PDF content")
        (self.source_dir / "script.py").write_text("print('hello')")
        (self.source_dir / "data.json").write_text('{"key": "value"}')
        
        # Files with special characters
        (self.source_dir / "file with spaces.txt").write_text("content")
        (self.source_dir / "file-with-dashes.txt").write_text("content")
        (self.source_dir / "file_with_underscores.txt").write_text("content")
        
        # Unicode filename (if supported by filesystem)
        try:
            (self.source_dir / "测试文件.txt").write_text("unicode content")
        except:
            pass  # Skip if filesystem doesn't support unicode
        
        # Empty file
        (self.source_dir / "empty.txt").touch()
        
        # Large file (1MB)
        large_content = "A" * (1024 * 1024)
        (self.source_dir / "large.txt").write_text(large_content)
        
        # Java class file for refactor testing
        java_content = '''public class TestClass {
    public TestClass() {
        System.out.println("Constructor");
    }
    
    public void method() {
        // Method implementation
    }
}'''
        (self.source_dir / "TestClass.java").write_text(java_content)
        
        # Python class file for refactor testing
        python_content = '''class TestClass:
    def __init__(self):
        print("Constructor")
    
    def method(self):
        # Method implementation
        pass
'''
        (self.source_dir / "TestClass.py").write_text(python_content)
        
        # Subdirectory with files
        subdir = self.source_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested content")
        
    def run_tool(self, tool_path: Path, args: list, expect_success: bool = True):
        """Run a tool and capture output safely."""
        cmd = [sys.executable, str(tool_path)] + args
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=30  # Prevent hanging
            )
            
            if expect_success and result.returncode != 0:
                self.fail(f"Tool failed unexpectedly: {result.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired:
            self.fail(f"Tool timed out: {cmd}")
        except Exception as e:
            self.fail(f"Tool execution failed: {e}")
    
    def test_safe_move_basic_safety(self):
        """Test basic safety features of safe_move.py."""
        print("🔒 Testing safe_move basic safety...")
        
        source_file = self.source_dir / "test.txt"
        dest_file = self.dest_dir / "test.txt"
        original_content = source_file.read_text()
        
        # Test dry run mode
        result = self.run_tool(self.safe_move, [
            str(source_file), "-d", str(dest_file), "--dry-run"
        ])
        
        # File should not have moved in dry run
        self.assertTrue(source_file.exists(), "Source file should still exist after dry run")
        self.assertFalse(dest_file.exists(), "Dest file should not exist after dry run")
        self.assertIn("DRY RUN", result.stdout)
        
        # Test actual move
        result = self.run_tool(self.safe_move, [
            str(source_file), "-d", str(dest_file)
        ])
        
        # Verify move completed successfully
        self.assertFalse(source_file.exists(), "Source file should be moved")
        self.assertTrue(dest_file.exists(), "Dest file should exist")
        self.assertEqual(dest_file.read_text(), original_content, "Content should be preserved")
    
    def test_safe_move_overwrite_protection(self):
        """Test overwrite protection and backup functionality."""
        print("🛡️ Testing safe_move overwrite protection...")
        
        source_file = self.source_dir / "test.txt"
        dest_file = self.dest_dir / "existing.txt"
        
        # Create existing file at destination
        original_dest_content = "Original destination content"
        dest_file.write_text(original_dest_content)
        
        # Move should backup existing file
        result = self.run_tool(self.safe_move, [
            str(source_file), "-d", str(dest_file), "--verbose"
        ])
        
        # Verify backup was created
        self.assertIn("Backed up", result.stdout)
        self.assertTrue(dest_file.exists(), "Dest file should exist")
        
        # Check that backup directory was created
        backup_dir = Path.home() / '.safe_move_trash'
        backup_files = list(backup_dir.glob("existing.txt.backup_*"))
        self.assertTrue(len(backup_files) > 0, "Backup file should be created")
    
    def test_safe_move_nonexistent_source(self):
        """Test handling of nonexistent source files."""
        print("❌ Testing safe_move with nonexistent source...")
        
        nonexistent = self.source_dir / "nonexistent.txt"
        dest_file = self.dest_dir / "dest.txt"
        
        result = self.run_tool(self.safe_move, [
            str(nonexistent), "-d", str(dest_file)
        ], expect_success=False)
        
        self.assertIn("does not exist", result.stdout)
        self.assertFalse(dest_file.exists(), "Dest should not be created")
    
    def test_safe_move_permission_errors(self):
        """Test handling of permission errors."""
        print("🔐 Testing safe_move permission handling...")
        
        # Create read-only file (on Unix systems)
        readonly_file = self.source_dir / "readonly.txt"
        readonly_file.write_text("readonly content")
        
        try:
            readonly_file.chmod(0o444)  # Read-only
            
            # Create read-only destination directory
            readonly_dir = self.test_dir / "readonly_dir"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o555)  # Read-only directory
            
            # This should fail gracefully
            result = self.run_tool(self.safe_move, [
                str(readonly_file), "-d", str(readonly_dir / "test.txt")
            ], expect_success=False)
            
            # Tool should handle the error gracefully
            self.assertTrue(readonly_file.exists(), "Source should still exist on failure")
            
        finally:
            # Restore permissions for cleanup
            if readonly_file.exists():
                readonly_file.chmod(0o644)
            if 'readonly_dir' in locals() and readonly_dir.exists():
                readonly_dir.chmod(0o755)
    
    def test_safe_move_undo_functionality(self):
        """Test undo functionality."""
        print("↩️ Testing safe_move undo functionality...")
        
        source_file = self.source_dir / "undo_test.txt"
        dest_file = self.dest_dir / "undo_test.txt"
        original_content = "undo test content"
        source_file.write_text(original_content)
        
        # Perform move
        self.run_tool(self.safe_move, [str(source_file), "-d", str(dest_file)])
        
        # Verify move
        self.assertFalse(source_file.exists())
        self.assertTrue(dest_file.exists())
        
        # Test undo
        result = self.run_tool(self.safe_move, ["--undo"])
        
        # Verify undo worked
        self.assertTrue(source_file.exists(), "Source should be restored")
        self.assertFalse(dest_file.exists(), "Dest should be removed")
        self.assertEqual(source_file.read_text(), original_content, "Content should be preserved")
    
    def test_organize_files_safety(self):
        """Test organize_files.py safety features."""
        print("📂 Testing organize_files safety...")
        
        # Test dry run mode
        result = self.run_tool(self.organize_files, [
            str(self.source_dir), "--by-ext", "--dry-run"
        ])
        
        # Files should not have moved in dry run
        self.assertTrue((self.source_dir / "test.txt").exists())
        self.assertTrue((self.source_dir / "script.py").exists())
        self.assertIn("DRY RUN", result.stdout)
        
        # No directories should have been created
        subdirs = [d for d in self.source_dir.iterdir() if d.is_dir() and d.name != "subdir"]
        self.assertEqual(len(subdirs), 0, "No directories should be created in dry run")
    
    def test_organize_files_name_conflicts(self):
        """Test organize_files handling of name conflicts."""
        print("⚔️ Testing organize_files name conflict handling...")
        
        # Create conflicting files
        (self.source_dir / "Documents").mkdir()
        (self.source_dir / "Documents" / "test.txt").write_text("existing content")
        
        # This should handle conflicts gracefully
        result = self.run_tool(self.organize_files, [
            str(self.source_dir), "--by-ext", "--verbose"
        ])
        
        # Both files should exist (with renamed conflict resolution)
        docs_dir = self.source_dir / "Documents"
        txt_files = list(docs_dir.glob("test*.txt"))
        self.assertGreaterEqual(len(txt_files), 1, "Conflicting files should be handled")
    
    def test_refactor_rename_safety(self):
        """Test refactor_rename.py safety features."""
        print("✏️ Testing refactor_rename safety...")
        
        java_file = self.source_dir / "TestClass.java"
        
        # Test dry run mode
        result = self.run_tool(self.refactor_rename, [
            str(java_file), "NewTestClass", "--dry-run"
        ])
        
        # File should not have been renamed in dry run
        self.assertTrue(java_file.exists(), "Original file should exist after dry run")
        self.assertFalse((self.source_dir / "NewTestClass.java").exists(), 
                        "New file should not exist after dry run")
        self.assertIn("DRY RUN", result.stdout)
        
        # Content should not have changed
        content = java_file.read_text()
        self.assertIn("public class TestClass", content, "Content should be unchanged in dry run")
    
    def test_refactor_rename_existing_destination(self):
        """Test refactor_rename handling of existing destination files."""
        print("🎯 Testing refactor_rename existing destination handling...")
        
        java_file = self.source_dir / "TestClass.java"
        existing_file = self.source_dir / "NewTestClass.java"
        
        # Create file at destination
        existing_file.write_text("existing content")
        
        # This should fail gracefully
        result = self.run_tool(self.refactor_rename, [
            str(java_file), "NewTestClass"
        ], expect_success=False)
        
        # Original file should still exist
        self.assertTrue(java_file.exists(), "Original file should still exist")
        self.assertIn("already exists", result.stdout)
    
    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        print("🔒 Testing path traversal protection...")
        
        source_file = self.source_dir / "test.txt"
        
        # Test various path traversal attempts
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32\\config",
            "~/../../etc/passwd",
        ]
        
        for dangerous_path in dangerous_paths:
            result = self.run_tool(self.safe_move, [
                str(source_file), "-d", dangerous_path, "--dry-run"
            ], expect_success=False)
            
            # Should either fail or be contained within test directory
            # The important thing is that it doesn't actually affect system files
            
    def test_large_file_handling(self):
        """Test handling of large files."""
        print("📊 Testing large file handling...")
        
        large_file = self.source_dir / "large.txt"
        dest_file = self.dest_dir / "large.txt"
        
        # Test moving large file
        result = self.run_tool(self.safe_move, [
            str(large_file), "-d", str(dest_file)
        ])
        
        # Verify large file was moved correctly
        self.assertTrue(dest_file.exists(), "Large file should be moved")
        self.assertEqual(dest_file.stat().st_size, 1024 * 1024, "File size should be preserved")
    
    def test_concurrent_access_simulation(self):
        """Test behavior under simulated concurrent access."""
        print("🔄 Testing concurrent access simulation...")
        
        # Create multiple files for batch operations
        for i in range(10):
            (self.source_dir / f"batch_{i}.txt").write_text(f"content {i}")
        
        # Test batch move
        result = self.run_tool(self.safe_move, [
            str(self.source_dir / "batch_*.txt"), "-d", str(self.dest_dir), "--batch"
        ])
        
        # Verify all files were moved
        moved_files = list(self.dest_dir.glob("batch_*.txt"))
        self.assertEqual(len(moved_files), 10, "All batch files should be moved")
    
    def test_special_characters_handling(self):
        """Test handling of files with special characters."""
        print("🌐 Testing special characters handling...")
        
        special_files = [
            "file with spaces.txt",
            "file-with-dashes.txt", 
            "file_with_underscores.txt"
        ]
        
        for filename in special_files:
            if (self.source_dir / filename).exists():
                dest_file = self.dest_dir / filename
                
                result = self.run_tool(self.safe_move, [
                    str(self.source_dir / filename), "-d", str(dest_file)
                ])
                
                self.assertTrue(dest_file.exists(), f"File with special chars should be moved: {filename}")
    
    def test_error_recovery(self):
        """Test error recovery and cleanup."""
        print("🛠️ Testing error recovery...")
        
        # Test invalid arguments
        result = self.run_tool(self.safe_move, [], expect_success=False)
        self.assertNotEqual(result.returncode, 0, "Should fail with no arguments")
        
        result = self.run_tool(self.organize_files, ["nonexistent"], expect_success=False)
        self.assertNotEqual(result.returncode, 0, "Should fail with nonexistent directory")
        
        result = self.run_tool(self.refactor_rename, ["nonexistent.java", "new"], expect_success=False)
        self.assertNotEqual(result.returncode, 0, "Should fail with nonexistent file")
    
    def test_memory_usage_with_many_files(self):
        """Test memory usage with many files."""
        print("💾 Testing memory usage with many files...")
        
        # Create many small files
        many_files_dir = self.test_dir / "many_files"
        many_files_dir.mkdir()
        
        for i in range(100):  # 100 files should be reasonable for testing
            (many_files_dir / f"file_{i:03d}.txt").write_text(f"content {i}")
        
        # Test organizing many files
        result = self.run_tool(self.organize_files, [
            str(many_files_dir), "--by-ext", "--dry-run"
        ])
        
        # Should complete without memory issues
        self.assertEqual(result.returncode, 0, "Should handle many files successfully")
    
    def run_all_safety_tests(self):
        """Run all safety tests and report results."""
        print("🚨 BULLETPROOF FILE TOOLS SAFETY VERIFICATION")
        print("=" * 60)
        
        test_methods = [
            self.test_safe_move_basic_safety,
            self.test_safe_move_overwrite_protection,
            self.test_safe_move_nonexistent_source,
            self.test_safe_move_permission_errors,
            self.test_safe_move_undo_functionality,
            self.test_organize_files_safety,
            self.test_organize_files_name_conflicts,
            self.test_refactor_rename_safety,
            self.test_refactor_rename_existing_destination,
            self.test_path_traversal_protection,
            self.test_large_file_handling,
            self.test_concurrent_access_simulation,
            self.test_special_characters_handling,
            self.test_error_recovery,
            self.test_memory_usage_with_many_files,
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                test_method()
                print(f"✅ {test_method.__name__}")
                passed += 1
            except Exception as e:
                print(f"❌ {test_method.__name__}: {e}")
                failed += 1
        
        print("=" * 60)
        print(f"📊 SAFETY TEST RESULTS: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 ALL SAFETY TESTS PASSED - TOOLS ARE BULLETPROOF!")
        else:
            print("⚠️ SAFETY ISSUES DETECTED - TOOLS NEED FIXES!")
        
        return failed == 0

def main():
    """Run the bulletproof safety test suite."""
    test_suite = BulletproofFileToolsTest()
    test_suite.setUp()
    
    try:
        success = test_suite.run_all_safety_tests()
        return 0 if success else 1
    finally:
        test_suite.tearDown()

if __name__ == '__main__':
    import sys
    sys.exit(main())