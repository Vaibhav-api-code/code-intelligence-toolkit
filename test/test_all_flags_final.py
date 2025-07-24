#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Comprehensive test of all replace_text.py flags with the hardened version."""

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import subprocess
import tempfile
import os
import sys
import time

class FlagTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
        
    def create_test_file(self, content):
        """Create a temporary test file."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False)
        f.write(content)
        f.close()
        return f.name
    
    def run_replace(self, filepath, old, new, flags=[]):
        """Run replace_text.py with given flags."""
        cmd = ["python3", "replace_text.py", filepath, old, new] + flags
        result = subprocess.run(cmd, capture_output=True, text=True, input="y\n")  # Auto-confirm
        return result
    
    def test_flag(self, name, test_func):
        """Run a test and record results."""
        try:
            test_func()
            self.passed += 1
            self.results.append(f"✓ {name}")
            print(f"✓ {name}")
        except AssertionError as e:
            self.failed += 1
            self.results.append(f"✗ {name}: {e}")
            print(f"✗ {name}: {e}")
        except Exception as e:
            self.failed += 1
            self.results.append(f"✗ {name}: ERROR: {e}")
            print(f"✗ {name}: ERROR: {e}")
    
    def test_basic_flags(self):
        """Test individual basic flags."""
        
        # Test --dry-run
        def test_dry_run():
            content = "public class Test { String oldValue = null; }"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "oldValue", "newValue", ["--dry-run"])
            
            # Should show changes but not apply them
            assert result.returncode == 0
            assert "Changes to be made:" in result.stdout
            assert "Dry run - no changes applied" in result.stdout
            
            # File should be unchanged
            with open(filepath, 'r') as f:
                assert "oldValue" in f.read()
            
            os.unlink(filepath)
        
        # Test --backup
        def test_backup():
            content = "public class Test { String oldValue = null; }"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "oldValue", "newValue", ["--backup"])
            
            assert result.returncode == 0
            assert os.path.exists(filepath + ".bak")
            
            # Backup should have original content
            with open(filepath + ".bak", 'r') as f:
                assert "oldValue" in f.read()
            
            os.unlink(filepath)
            os.unlink(filepath + ".bak")
        
        # Test --quiet
        def test_quiet():
            content = "public class Test { String oldValue = null; }"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "oldValue", "newValue", ["--quiet"])
            
            assert result.returncode == 0
            assert result.stdout.strip() == ""  # No output
            
            # Changes should be applied
            with open(filepath, 'r') as f:
                assert "newValue" in f.read()
            
            os.unlink(filepath)
        
        # Test --force
        def test_force():
            # Create file with 60 replacements (above threshold)
            content = " ".join(["oldValue"] * 60)
            filepath = self.create_test_file(f"public class Test {{ String data = \"{content}\"; }}")
            
            result = self.run_replace(filepath, "oldValue", "newValue", ["--force"])
            
            assert result.returncode == 0
            assert "This will make" not in result.stdout  # No prompt
            
            os.unlink(filepath)
        
        # Test --verbose
        def test_verbose():
            content = """public class Test {
    String old1 = null;
    String old2 = null;
    String old3 = null;
}"""
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "old", "new", ["--verbose"])
            
            assert result.returncode == 0
            assert "Changes made:" in result.stdout
            # Should show all 3 changes, not truncated
            assert "Line 2:" in result.stdout
            assert "Line 3:" in result.stdout
            assert "Line 4:" in result.stdout
            assert "... and" not in result.stdout  # No truncation message
            
            os.unlink(filepath)
        
        self.test_flag("--dry-run", test_dry_run)
        self.test_flag("--backup", test_backup)
        self.test_flag("--quiet", test_quiet)
        self.test_flag("--force", test_force)
        self.test_flag("--verbose", test_verbose)
    
    def test_replacement_strategy_flags(self):
        """Test replacement strategy flags."""
        
        # Test --whole-word
        def test_whole_word():
            content = "oldValue oldValueExtra prefixOldValue"
            filepath = self.create_test_file(f"// {content}")
            
            result = self.run_replace(filepath, "oldValue", "newValue", ["--whole-word"])
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert "newValue " in content  # First word replaced
                assert "oldValueExtra" in content  # Not replaced
                assert "prefixOldValue" in content  # Not replaced
            
            os.unlink(filepath)
        
        # Test --regex
        def test_regex():
            content = "value123 value456"
            filepath = self.create_test_file(f"// {content}")
            
            result = self.run_replace(filepath, r"value\d+", "VALUE", ["--regex"])
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert "VALUE VALUE" in content
            
            os.unlink(filepath)
        
        # Test --comments-only
        def test_comments_only():
            content = """public class Test {
    // oldValue in comment
    String s = "oldValue in string";
    /* oldValue in block comment */
    private int oldValue = 42;
}"""
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "oldValue", "newValue", ["--comments-only"])
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert "// newValue in comment" in content
                assert "/* newValue in block comment */" in content
                assert '"oldValue in string"' in content  # String unchanged
                assert "private int oldValue" in content  # Code unchanged
            
            os.unlink(filepath)
        
        # Test --strings-only
        def test_strings_only():
            content = """public class Test {
    // oldValue in comment
    String s = "oldValue in string";
    private int oldValue = 42;
}"""
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "oldValue", "newValue", ["--strings-only"])
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert "// oldValue in comment" in content  # Comment unchanged
                assert '"newValue in string"' in content  # String changed
                assert "private int oldValue" in content  # Code unchanged
            
            os.unlink(filepath)
        
        self.test_flag("--whole-word", test_whole_word)
        self.test_flag("--regex", test_regex)
        self.test_flag("--comments-only", test_comments_only)
        self.test_flag("--strings-only", test_strings_only)
    
    def test_regex_modifier_flags(self):
        """Test regex modifier flags."""
        
        # Test --case-insensitive (-i)
        def test_case_insensitive():
            content = "Test TEST test"
            filepath = self.create_test_file(f"// {content}")
            
            result = self.run_replace(filepath, "test", "demo", ["--regex", "-i"])
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert "demo demo demo" in content
            
            os.unlink(filepath)
        
        # Test --multiline (-m)
        def test_multiline():
            content = """start
middle
end"""
            filepath = self.create_test_file(f"/* {content} */")
            
            result = self.run_replace(filepath, "^middle$", "MIDDLE", ["--regex", "-m"])
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert "MIDDLE" in content
            
            os.unlink(filepath)
        
        # Test --dotall (-s)
        def test_dotall():
            content = """line1
line2"""
            filepath = self.create_test_file(f"/* {content} */")
            
            result = self.run_replace(filepath, "line1.*line2", "MATCHED", ["--regex", "-s"])
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert "MATCHED" in content
            
            os.unlink(filepath)
        
        self.test_flag("--case-insensitive", test_case_insensitive)
        self.test_flag("--multiline", test_multiline)
        self.test_flag("--dotall", test_dotall)
    
    def test_range_flags(self):
        """Test line range flags."""
        
        # Test --start-line and --end-line
        def test_line_range():
            content = """line1 old
line2 old
line3 old
line4 old
line5 old"""
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "old", "new", ["--start-line", "2", "--end-line", "4"])
            
            with open(filepath, 'r') as f:
                lines = f.read().split('\n')
                assert "old" in lines[0]  # Line 1 unchanged
                assert "new" in lines[1]  # Line 2 changed
                assert "new" in lines[2]  # Line 3 changed
                assert "new" in lines[3]  # Line 4 changed
                assert "old" in lines[4]  # Line 5 unchanged
            
            os.unlink(filepath)
        
        # Test --count
        def test_count():
            content = "old old old old old"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "old", "new", ["--count", "3"])
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert content.count("new") == 3
                assert content.count("old") == 2
            
            os.unlink(filepath)
        
        self.test_flag("--start-line/--end-line", test_line_range)
        self.test_flag("--count", test_count)
    
    def test_flag_combinations(self):
        """Test various flag combinations."""
        
        # Test --regex with --whole-word (should work together)
        def test_regex_whole_word():
            content = "test testing"
            filepath = self.create_test_file(content)
            
            # These flags should work together
            result = self.run_replace(filepath, r"\btest\b", "demo", ["--regex", "--whole-word"])
            
            assert result.returncode == 0
            
            os.unlink(filepath)
        
        # Test --quiet with --dry-run
        def test_quiet_dry_run():
            content = "old value"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "old", "new", ["--quiet", "--dry-run"])
            
            assert result.returncode == 0
            assert result.stdout.strip() == ""  # No output
            
            # File should be unchanged
            with open(filepath, 'r') as f:
                assert "old" in f.read()
            
            os.unlink(filepath)
        
        # Test --backup with --dry-run (backup shouldn't be created)
        def test_backup_dry_run():
            content = "old value"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "old", "new", ["--backup", "--dry-run"])
            
            assert result.returncode == 0
            assert not os.path.exists(filepath + ".bak")  # No backup in dry-run
            
            os.unlink(filepath)
        
        # Test --verbose with --quiet (quiet should win)
        def test_verbose_quiet():
            content = "old value"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "old", "new", ["--verbose", "--quiet"])
            
            assert result.returncode == 0
            assert result.stdout.strip() == ""  # Quiet wins
            
            os.unlink(filepath)
        
        # Test multiple regex flags
        def test_multiple_regex_flags():
            content = """TEST
test"""
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "^test$", "DEMO", ["--regex", "-i", "-m"])
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert content.count("DEMO") == 2  # Both lines matched
            
            os.unlink(filepath)
        
        self.test_flag("--regex + --whole-word", test_regex_whole_word)
        self.test_flag("--quiet + --dry-run", test_quiet_dry_run)
        self.test_flag("--backup + --dry-run", test_backup_dry_run)
        self.test_flag("--verbose + --quiet", test_verbose_quiet)
        self.test_flag("multiple regex flags", test_multiple_regex_flags)
    
    def test_edge_cases(self):
        """Test edge cases with various flags."""
        
        # Test empty file
        def test_empty_file():
            filepath = self.create_test_file("")
            
            result = self.run_replace(filepath, "old", "new", [])
            
            assert result.returncode == 0
            assert "No changes made" in result.stdout
            
            os.unlink(filepath)
        
        # Test file with no matches
        def test_no_matches():
            content = "some other content"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "notfound", "new", ["--verbose"])
            
            assert result.returncode == 0
            assert "No changes made" in result.stdout
            
            os.unlink(filepath)
        
        # Test invalid regex
        def test_invalid_regex():
            content = "test"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "[invalid", "new", ["--regex"])
            
            assert result.returncode == 1
            assert "Invalid regex" in result.stderr or "error" in result.stderr.lower()
            
            os.unlink(filepath)
        
        # Test non-existent file
        def test_nonexistent_file():
            result = self.run_replace("nonexistent.java", "old", "new", ["--force"])
            
            assert result.returncode == 1
            assert "not found" in result.stderr
        
        # Test zero-width pattern protection
        def test_zero_width_pattern():
            content = "test"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "", "X", ["--regex"])
            
            assert result.returncode == 1
            assert "Zero-width pattern" in result.stderr
            
            os.unlink(filepath)
        
        # Test recursive replacement fix
        def test_recursive_replacement():
            # The old recursive bug would turn "a" -> "aa" into infinite replacements
            # Our fix prevents this by finding all positions first
            content = "a b a"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "a", "aa", [])
            
            assert result.returncode == 0
            
            with open(filepath, 'r') as f:
                content = f.read()
                # Should be "aa b aa", not "aaaa b aaaa" or infinite
                assert content == "aa b aa"
            
            os.unlink(filepath)
        
        self.test_flag("empty file", test_empty_file)
        self.test_flag("no matches", test_no_matches)
        self.test_flag("invalid regex", test_invalid_regex)
        self.test_flag("non-existent file", test_nonexistent_file)
        self.test_flag("zero-width pattern protection", test_zero_width_pattern)
        self.test_flag("recursive replacement fix", test_recursive_replacement)
    
    def test_new_safety_features(self):
        """Test the new safety features we added."""
        
        # Test line ending preservation
        def test_line_ending_preservation():
            # Create file with Windows line endings
            with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, newline='') as f:
                f.write("line1\r\nline2\r\n")
                filepath = f.name
            
            result = self.run_replace(filepath, "line1", "first", [])
            
            assert result.returncode == 0
            
            # Check that line endings are preserved
            with open(filepath, 'rb') as f:
                content = f.read()
                assert b'\r\n' in content  # Windows line endings preserved
            
            os.unlink(filepath)
        
        # Test large file warning
        def test_large_file_warning():
            # Create a file just over 100MB would be too slow, so we'll test the logic differently
            # This is more of a manual test
            pass
        
        # Test catastrophic backtracking warning
        def test_backtracking_warning():
            content = "aaaaaab"
            filepath = self.create_test_file(content)
            
            result = self.run_replace(filepath, "(a+)+b", "MATCH", ["--regex"])
            
            # Should work but show warning
            assert result.returncode == 0
            assert "may cause performance issues" in result.stderr
            
            os.unlink(filepath)
        
        self.test_flag("line ending preservation", test_line_ending_preservation)
        self.test_flag("catastrophic backtracking warning", test_backtracking_warning)
    
    def run_all_tests(self):
        """Run all flag tests."""
        print("Testing all replace_text.py flags after hardening...")
        print("=" * 70)
        
        print("\n1. Testing basic flags...")
        self.test_basic_flags()
        
        print("\n2. Testing replacement strategy flags...")
        self.test_replacement_strategy_flags()
        
        print("\n3. Testing regex modifier flags...")
        self.test_regex_modifier_flags()
        
        print("\n4. Testing range/count flags...")
        self.test_range_flags()
        
        print("\n5. Testing flag combinations...")
        self.test_flag_combinations()
        
        print("\n6. Testing edge cases...")
        self.test_edge_cases()
        
        print("\n7. Testing new safety features...")
        self.test_new_safety_features()
        
        print("\n" + "=" * 70)
        print(f"TOTAL TESTS: {self.passed + self.failed}")
        print(f"PASSED: {self.passed}")
        print(f"FAILED: {self.failed}")
        print("=" * 70)
        
        if self.failed > 0:
            print("\nFailed tests:")
            for result in self.results:
                if result.startswith("✗"):
                    print(f"  {result}")
        
        return self.failed == 0

def main():
    tester = FlagTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()