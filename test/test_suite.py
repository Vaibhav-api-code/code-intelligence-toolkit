#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Comprehensive test suite for the smart code analysis toolkit.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import pytest
import subprocess
import tempfile
import os
import json
from pathlib import Path
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from common_utils import (
    check_ripgrep, detect_language, classify_file_type, 
    detect_primary_language, safe_get_file_content,
    find_closing_brace, format_file_size, validate_regex_pattern
)


class TestCommonUtils:
    """Test the common utilities module."""
    
    def test_detect_language(self):
        """Test language detection from file extensions."""
        assert detect_language("test.java") == "java"
        assert detect_language("test.py") == "python"
        assert detect_language("test.js") == "javascript"
        assert detect_language("test.unknown") == "unknown"
        assert detect_language("") == "unknown"
    
    def test_classify_file_type(self):
        """Test file type classification."""
        assert classify_file_type("TestFile.java") == "test"
        assert classify_file_type("src/main/java/File.java") == "source"
        assert classify_file_type("config.properties") == "config"
        assert classify_file_type("app.log") == "log"
        assert classify_file_type("README.md") == "documentation"
        assert classify_file_type("build/output.jar") == "build"
    
    def test_find_closing_brace(self):
        """Test brace matching functionality."""
        content = "class Test { public void method() { if (true) { } } }"
        
        # Test main class brace
        assert find_closing_brace(content, 11) == len(content) - 1
        
        # Test method brace  
        assert find_closing_brace(content, 37) == len(content) - 3
        
        # Test if statement brace
        if_brace = content.index('{', 40)  # Find the if brace
        if_close = content.index('}', if_brace)
        assert find_closing_brace(content, if_brace) == if_close
        
        # Test invalid input
        assert find_closing_brace(content, 0) == -1  # Not a brace
        assert find_closing_brace("{ no close", 0) == -1  # Unmatched
    
    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(512) == "512 B"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(2 * 1024 * 1024) == "2.0 MB"
        assert format_file_size(3 * 1024 * 1024 * 1024) == "3.0 GB"
    
    def test_validate_regex_pattern(self):
        """Test regex pattern validation."""
        assert validate_regex_pattern(r"test") == True
        assert validate_regex_pattern(r"\d+") == True
        assert validate_regex_pattern(r"[a-z]+") == True
        assert validate_regex_pattern(r"[") == False  # Invalid regex
        assert validate_regex_pattern(r"*") == False  # Invalid regex
    
    def test_safe_get_file_content(self):
        """Test safe file content reading."""
        # Test with non-existent file
        assert safe_get_file_content("nonexistent.txt") is None
        
        # Test with existing test file
        test_file = Path(__file__).parent / "test_data" / "sample_python.py"
        if test_file.exists():
            content = safe_get_file_content(str(test_file))
            assert content is not None
            assert "SamplePythonClass" in content


class TestToolIntegration:
    """Integration tests for the analysis tools."""
    
    def setup_method(self):
        """Set up test environment."""
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.sample_java = self.test_data_dir / "SampleJavaClass.java"
        self.sample_python = self.test_data_dir / "sample_python.py"
        self.sample_log = self.test_data_dir / "sample_log.log"
    
    def run_tool(self, tool_name, *args, timeout=30):
        """Helper to run a tool and return output."""
        cmd = [sys.executable, tool_name] + list(args)
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=Path(__file__).parent
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as e:
            return -2, "", str(e)
    
    def test_method_analyzer_basic(self):
        """Test basic method_analyzer functionality."""
        if not self.sample_java.exists():
            pytest.skip("Sample Java file not found")
        
        returncode, stdout, stderr = self.run_tool(
            "method_analyzer.py", 
            "validateName",
            "--scope", str(self.test_data_dir),
            "--language", "java"
        )
        
        assert returncode == 0, f"Tool failed: {stderr}"
        assert "validateName" in stdout
        assert "Total calls found:" in stdout
    
    def test_method_analyzer_json_output(self):
        """Test method_analyzer JSON output."""
        if not self.sample_java.exists():
            pytest.skip("Sample Java file not found")
        
        returncode, stdout, stderr = self.run_tool(
            "method_analyzer.py",
            "processData", 
            "--scope", str(self.test_data_dir),
            "--language", "java",
            "--json"
        )
        
        assert returncode == 0, f"Tool failed: {stderr}"
        
        try:
            data = json.loads(stdout)
            assert "method_name" in data
            assert data["method_name"] == "processData"
            assert "analysis" in data
        except json.JSONDecodeError:
            pytest.fail("Invalid JSON output")
    
    def test_pattern_analysis_basic(self):
        """Test basic pattern_analysis functionality."""
        if not self.sample_log.exists():
            pytest.skip("Sample log file not found")
        
        returncode, stdout, stderr = self.run_tool(
            "pattern_analysis.py",
            "ERROR", 
            "--scope", str(self.test_data_dir),
            "--show-frequency"
        )
        
        assert returncode == 0, f"Tool failed: {stderr}"
        assert "PATTERN ANALYSIS" in stdout
        assert "Total matches found:" in stdout
    
    def test_smart_find_references_basic(self):
        """Test basic smart_find_references functionality."""
        if not self.sample_java.exists():
            pytest.skip("Sample Java file not found")
        
        returncode, stdout, stderr = self.run_tool(
            "smart_find_references.py",
            "processItem",
            "--scope", str(self.test_data_dir),
            "--language", "java"
        )
        
        assert returncode == 0, f"Tool failed: {stderr}"
        # Should find references in both main class and test class
    
    def test_log_analyzer_basic(self):
        """Test basic log_analyzer functionality."""
        if not self.sample_log.exists():
            pytest.skip("Sample log file not found")
        
        returncode, stdout, stderr = self.run_tool(
            "log_analyzer.py",
            "--pattern", "ERROR",
            "--files", str(self.sample_log),
            "--show-frequency"
        )
        
        assert returncode == 0, f"Tool failed: {stderr}"
        assert "LOG ANALYSIS" in stdout
    
    def test_navigate_basic(self):
        """Test basic navigate functionality."""
        if not self.sample_java.exists():
            pytest.skip("Sample Java file not found")
        
        returncode, stdout, stderr = self.run_tool(
            "navigate.py",
            str(self.sample_java),
            "--to", "method:validateName"
        )
        
        assert returncode == 0, f"Tool failed: {stderr}"
        assert "validateName" in stdout


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_files(self):
        """Test behavior with empty files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write("")  # Empty file
            temp_file = f.name
        
        try:
            content = safe_get_file_content(temp_file)
            assert content == ""
        finally:
            os.unlink(temp_file)
    
    def test_large_files(self):
        """Test behavior with large files."""
        # Create a file larger than the default limit
        large_content = "// Large file\n" * 100000  # ~1.3MB
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(large_content)
            temp_file = f.name
        
        try:
            # Should return None due to size limit (default 10MB, but test with smaller)
            content = safe_get_file_content(temp_file, max_size_mb=1)
            assert content is None
        finally:
            os.unlink(temp_file)
    
    def test_binary_files(self):
        """Test behavior with binary files."""
        # Create a binary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.class', delete=False) as f:
            f.write(b'\x00\x01\x02\x03\xCA\xFE\xBA\xBE')  # Java class file magic
            temp_file = f.name
        
        try:
            from common_utils import is_binary_file
            assert is_binary_file(temp_file) == True
        finally:
            os.unlink(temp_file)
    
    def test_malformed_regex(self):
        """Test handling of malformed regex patterns."""
        assert validate_regex_pattern("[") == False
        assert validate_regex_pattern("*") == False
        assert validate_regex_pattern("(") == False


class TestLanguageDetection:
    """Test language detection edge cases."""
    
    def test_detect_primary_language_java_project(self):
        """Test language detection in Java project."""
        test_dir = Path(__file__).parent / "test_data"
        if test_dir.exists():
            # Should detect Java as primary language
            lang = detect_primary_language(str(test_dir))
            assert lang in ["java", "python"]  # Either is valid depending on file counts
    
    def test_detect_primary_language_empty_dir(self):
        """Test language detection in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            lang = detect_primary_language(temp_dir)
            assert lang is None
    
    def test_detect_primary_language_single_file(self):
        """Test language detection on single file."""
        test_file = Path(__file__).parent / "test_data" / "SampleJavaClass.java"
        if test_file.exists():
            lang = detect_primary_language(str(test_file))
            assert lang == "java"


def test_ripgrep_availability():
    """Test that ripgrep is available."""
    import shutil
    assert shutil.which('rg') is not None, "ripgrep (rg) is required but not found in PATH"


if __name__ == "__main__":
    # Run tests when called directly
    pytest.main([__file__, "-v"])