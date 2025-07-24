#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Pre-flight checks module for Python tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import os
import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
import argparse

logger = logging.getLogger(__name__)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

class PreflightChecker:
    """Common pre-flight checks for tools."""
    
    @staticmethod
    def check_path_exists(path: str, path_type: str = "path") -> Tuple[bool, str]:
        """
        Check if a path exists.
        
        Args:
            path: Path to check
            path_type: Description of path type (e.g., "file", "directory")
            
        Returns:
            (success, error_message)
        """
        path_obj = Path(path)
        if not path_obj.exists():
            return False, f"Error: {path_type.capitalize()} '{path}' does not exist"
        return True, ""
    
    @staticmethod
    def check_file_readable(path: str) -> Tuple[bool, str]:
        """Check if file exists and is readable."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return False, f"Error: File '{path}' does not exist"
        
        if not path_obj.is_file():
            return False, f"Error: '{path}' is not a file"
        
        try:
            with open(path_obj, 'r') as f:
                f.read(1)  # Try to read one byte
            return True, ""
        except PermissionError:
            return False, f"Error: Permission denied reading '{path}'"
        except Exception as e:
            return False, f"Error: Cannot read '{path}': {e}"
    
    @staticmethod
    def check_directory_accessible(path: str) -> Tuple[bool, str]:
        """Check if directory exists and is accessible."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return False, f"Error: Directory '{path}' does not exist"
        
        if not path_obj.is_dir():
            return False, f"Error: '{path}' is not a directory"
        
        try:
            list(path_obj.iterdir())  # Try to list contents
            return True, ""
        except PermissionError:
            return False, f"Error: Permission denied accessing '{path}'"
        except Exception as e:
            return False, f"Error: Cannot access '{path}': {e}"
    
    @staticmethod
    def check_file_size(path: str, max_size_mb: float = 100) -> Tuple[bool, str]:
        """Check if file size is reasonable."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return True, ""  # Let other checks handle existence
        
        try:
            size_mb = path_obj.stat().st_size / (1024 * 1024)
            if size_mb > max_size_mb:
                return False, f"Warning: File '{path}' is very large ({size_mb:.1f}MB). This may be slow."
            return True, ""
        except Exception:
            return True, ""  # Don't fail on size check errors
    
    @staticmethod
    def validate_method_name(name: str) -> Tuple[bool, str]:
        """Check if string looks like a valid method/identifier name."""
        if not name:
            return False, "Error: Method name cannot be empty"
        
        # Check for file path indicators
        if any(sep in name for sep in ('/', '\\')):
            return False, "Error: Name appears to contain path separators – expected a bare identifier."
        
        # Check for file extensions
        if name.endswith(('.java', '.py', '.js', '.cpp', '.c', '.go', '.rs')):
            return False, f"Error: Please provide just the method name, not a file name.\nRemove the '{Path(name).suffix}' extension."
        
        # Check for valid identifier
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            # Allow dots for qualified names
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$', name):
                return False, f"Error: '{name}' is not a valid method name"
        
        return True, ""

    @staticmethod
    def is_path_within_base(path: Path, 
                            base: Path) -> Tuple[bool, str]:
        """Rejects traversal outside the allowed base dir."""
        try:
            path = path.resolve()
            base = base.resolve()
        except Exception:
            return False, "Error: Unable to resolve paths for security check"
        if not str(path).startswith(str(base)):
            return False, f"SecurityError: '{path}' is outside '{base}'"
        return True, ""
    
    @staticmethod
    def validate_line_number(line_str: str) -> Tuple[bool, str]:
        """Check if string is a valid line number."""
        try:
            line_num = int(line_str)
            if line_num <= 0:
                return False, f"Error: Line number must be positive, got {line_num}"
            return True, ""
        except ValueError:
            return False, f"Error: '{line_str}' is not a valid line number"
    
    @staticmethod
    def check_ripgrep_installed() -> Tuple[bool, str]:
        """Check if ripgrep is installed."""
        import shutil
        if not shutil.which('rg'):
            return False, "Error: ripgrep (rg) is not installed. Please install it first."
        return True, ""
    
    @staticmethod
    def check_file_extension(path: str, allowed_extensions: List[str]) -> Tuple[bool, str]:
        """Check if file has allowed extension."""
        path_obj = Path(path)
        ext = path_obj.suffix.lower()
        
        if ext not in allowed_extensions:
            return False, f"Error: File must have one of these extensions: {', '.join(allowed_extensions)}"
        
        return True, ""
    
    @staticmethod
    def check_regex_pattern(pattern: str) -> Tuple[bool, str]:
        """Validate a regular expression pattern."""
        try:
            re.compile(pattern)
            return True, ""
        except re.error as e:
            return False, f"Error: Invalid regex pattern '{pattern}': {e}"
    
    @staticmethod
    def check_glob_pattern(pattern: str) -> Tuple[bool, str]:
        """Validate a glob pattern."""
        # Check for common glob pattern issues
        if pattern.count('*') > 10:
            return False, f"Error: Glob pattern '{pattern}' may be too complex"
        
        # Check for invalid characters in glob
        invalid_chars = '\x00'
        if any(c in pattern for c in invalid_chars):
            return False, f"Error: Glob pattern contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def check_git_repository(path: str = ".") -> Tuple[bool, str]:
        """Check if path is within a git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--is-inside-work-tree'],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, ""
            else:
                return False, f"Error: '{path}' is not within a git repository"
        except subprocess.TimeoutExpired:
            return False, "Error: Git check timed out"
        except FileNotFoundError:
            return False, "Error: Git is not installed"
        except Exception as e:
            return False, f"Error: Git check failed: {e}"
    
    @staticmethod
    def check_binary_file(path: str) -> Tuple[bool, str]:
        """Check if file appears to be binary."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return True, ""  # Let other checks handle existence
        
        try:
            with open(path_obj, 'rb') as f:
                chunk = f.read(8192)  # Read first 8KB
                
            # Check for null bytes (common in binary files)
            if b'\x00' in chunk:
                return False, f"Warning: '{path}' appears to be a binary file"
            
            # Check if mostly non-text characters
            text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
            non_text_count = sum(1 for byte in chunk if byte not in text_chars)
            
            if non_text_count / len(chunk) > 0.3:
                return False, f"Warning: '{path}' may be a binary file"
            
            return True, ""
        except Exception:
            return True, ""  # Don't fail on binary check errors
    
    @staticmethod
    def check_encoding(path: str, encoding: str = 'utf-8') -> Tuple[bool, str]:
        """Check if file can be read with specified encoding."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return True, ""  # Let other checks handle existence
        
        try:
            with open(path_obj, 'r', encoding=encoding) as f:
                f.read(1024)  # Try to read first 1KB
            return True, ""
        except UnicodeDecodeError:
            return False, f"Error: '{path}' cannot be decoded as {encoding}"
        except Exception:
            return True, ""  # Don't fail on encoding check errors
    
    @staticmethod
    def check_disk_space(path: str, required_mb: float = 100) -> Tuple[bool, str]:
        """Check if there's enough disk space."""
        try:
            stat = shutil.disk_usage(path)
            free_mb = stat.free / (1024 * 1024)
            
            if free_mb < required_mb:
                return False, f"Warning: Low disk space ({free_mb:.1f}MB free, {required_mb:.1f}MB recommended)"
            
            return True, ""
        except Exception:
            return True, ""  # Don't fail on disk space check
    
    @staticmethod
    def check_python_version(min_version: Tuple[int, int] = (3, 7)) -> Tuple[bool, str]:
        """Check if Python version meets requirements."""
        current = sys.version_info[:2]
        
        if current < min_version:
            return False, f"Error: Python {min_version[0]}.{min_version[1]}+ required, but {current[0]}.{current[1]} found"
        
        return True, ""
    
    @staticmethod
    def check_import_available(module_name: str) -> Tuple[bool, str]:
        """Check if a Python module can be imported."""
        try:
            __import__(module_name)
            return True, ""
        except ImportError:
            return False, f"Error: Required module '{module_name}' is not installed"
        except Exception as e:
            return False, f"Error: Failed to import '{module_name}': {e}"
    
    @staticmethod
    def check_command_available(command: str) -> Tuple[bool, str]:
        """Check if a system command is available."""
        if shutil.which(command):
            return True, ""
        else:
            return False, f"Error: Command '{command}' is not installed or not in PATH"
    
    @staticmethod
    def check_file_not_too_new(path: str, max_age_seconds: float = 1.0) -> Tuple[bool, str]:
        """Check if file is not too recently modified (to avoid race conditions)."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return True, ""
        
        try:
            import time
            mtime = path_obj.stat().st_mtime
            age = time.time() - mtime
            
            if age < max_age_seconds:
                return False, f"Warning: File '{path}' was modified {age:.1f}s ago (may still be writing)"
            
            return True, ""
        except Exception:
            return True, ""
    
    @staticmethod
    def check_memory_available(required_mb: float = 500) -> Tuple[bool, str]:
        """Check if there's enough available memory."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            available_mb = mem.available / (1024 * 1024)
            
            if available_mb < required_mb:
                return False, f"Warning: Low memory ({available_mb:.1f}MB available, {required_mb:.1f}MB recommended)"
            
            return True, ""
        except ImportError:
            # psutil not available, skip check
            return True, ""
        except Exception:
            return True, ""
    
    @staticmethod
    def check_file_permissions(path: str, need_write: bool = False) -> Tuple[bool, str]:
        """Check file permissions more thoroughly."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            # Check parent directory permissions for new files
            parent = path_obj.parent
            if not parent.exists():
                return False, f"Error: Parent directory '{parent}' does not exist"
            
            if not os.access(str(parent), os.W_OK):
                return False, f"Error: Cannot write to directory '{parent}'"
            
            return True, ""
        
        # Check read permission
        if not os.access(str(path_obj), os.R_OK):
            return False, f"Error: No read permission for '{path}'"
        
        # Check write permission if needed
        if need_write and not os.access(str(path_obj), os.W_OK):
            return False, f"Error: No write permission for '{path}'"
        
        return True, ""
    
    @staticmethod
    def suggest_alternative(args: argparse.Namespace, error_msg: str) -> Optional[str]:
        """Suggest alternative based on common mistakes."""
        suggestions = []
        
        # Common flag mistakes
        if "-F" in sys.argv and "find_text" in sys.argv[0]:
            suggestions.append("Did you mean '--in-files' instead of '-F'?")
        
        if "unrecognized arguments" in error_msg:
            # Check for common pattern mistakes
            if any(arg.startswith('-') and len(arg) > 2 and arg[1] != '-' for arg in sys.argv[1:]):
                suggestions.append("Note: Single-dash flags should be single characters. Use double-dash for long options.")
            
            # Check for file path as positional argument
            if any('/' in arg or '\\' in arg for arg in sys.argv[1:] if not arg.startswith('-')):
                suggestions.append("Tip: File paths usually go after flag options, not as positional arguments.")
        
        if suggestions:
            return "\n".join(suggestions)
        return None

def run_preflight_checks(checks: List[Tuple[callable, tuple]], exit_on_fail: bool = True) -> bool:
    """
    Run a list of pre-flight checks.
    
    Args:
        checks: List of (check_function, args) tuples
        exit_on_fail: Whether to exit immediately on failure
        
    Returns:
        True if all checks passed
    """
    all_passed = True
    
    for check_func, args in checks:
        success, message = check_func(*args)
        
        if not success:
            print(message, file=sys.stderr)
            
            # Add suggestions if available
            if hasattr(PreflightChecker, 'suggest_alternative'):
                suggestion = PreflightChecker.suggest_alternative(None, message)
                if suggestion:
                    print(f"\n{suggestion}", file=sys.stderr)
            
            if exit_on_fail:
                sys.exit(1)
            all_passed = False
        elif message and message.startswith("Warning:"):
            print(message, file=sys.stderr)
    
    return all_passed

# Convenience functions for common patterns
def check_input_file(path: str, max_size_mb: float = 100) -> None:
    """Standard checks for input file."""
    run_preflight_checks([
        (PreflightChecker.check_file_readable, (path,)),
        (PreflightChecker.check_file_size, (path, max_size_mb))
    ])

def check_output_directory(path: str) -> None:
    """Standard checks for output directory."""
    path_obj = Path(path)
    
    if path_obj.exists():
        run_preflight_checks([
            (PreflightChecker.check_directory_accessible, (path,))
        ])
    else:
        # Try to create it
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error: Cannot create directory '{path}': {e}", file=sys.stderr)
            sys.exit(1)

def check_method_name(name: str) -> None:
    """Standard checks for method name arguments."""
    run_preflight_checks([
        (PreflightChecker.validate_method_name, (name,))
    ])

def check_ripgrep() -> None:
    """Standard check for ripgrep dependency."""
    run_preflight_checks([
        (PreflightChecker.check_ripgrep_installed, ())
    ])

def check_regex_pattern(pattern: str) -> None:
    """Standard check for regex pattern validity."""
    run_preflight_checks([
        (PreflightChecker.check_regex_pattern, (pattern,))
    ])

def check_glob_pattern(pattern: str) -> None:
    """Standard check for glob pattern validity."""
    run_preflight_checks([
        (PreflightChecker.check_glob_pattern, (pattern,))
    ])

def check_git_repo(path: str = ".") -> None:
    """Standard check for git repository."""
    run_preflight_checks([
        (PreflightChecker.check_git_repository, (path,))
    ])

def check_text_file(path: str, encoding: str = 'utf-8') -> None:
    """Standard checks for text file (not binary, correct encoding)."""
    run_preflight_checks([
        (PreflightChecker.check_file_readable, (path,)),
        (PreflightChecker.check_binary_file, (path,)),
        (PreflightChecker.check_encoding, (path, encoding))
    ])

def check_writable_file(path: str) -> None:
    """Standard checks for a file that will be written to."""
    run_preflight_checks([
        (PreflightChecker.check_file_permissions, (path, True))
    ])

def check_system_resources(disk_mb: float = 100, memory_mb: float = 500) -> None:
    """Standard checks for system resources."""
    run_preflight_checks([
        (PreflightChecker.check_disk_space, (".", disk_mb)),
        (PreflightChecker.check_memory_available, (memory_mb,))
    ])

def check_python_env(min_version: Tuple[int, int] = (3, 7), 
                     required_modules: Optional[List[str]] = None) -> None:
    """Standard checks for Python environment."""
    checks = [(PreflightChecker.check_python_version, (min_version,))]
    
    if required_modules:
        for module in required_modules:
            checks.append((PreflightChecker.check_import_available, (module,)))
    
    run_preflight_checks(checks)

def check_tool_dependencies(commands: List[str]) -> None:
    """Standard checks for required system commands."""
    checks = []
    for cmd in commands:
        checks.append((PreflightChecker.check_command_available, (cmd,)))
    
    run_preflight_checks(checks)

if __name__ == "__main__":
    # Example usage / self-test
    import sys
    
    print("PreflightChecker module - comprehensive self test")
    print("=" * 60)
    
    # Group tests by category
    print("\n📁 File and Directory Checks:")
    print("-" * 40)
    tests = [
        ("Path exists", PreflightChecker.check_path_exists, (".", "directory")),
        ("File readable", PreflightChecker.check_file_readable, (__file__,)),
        ("Directory accessible", PreflightChecker.check_directory_accessible, (".",)),
        ("File size check", PreflightChecker.check_file_size, (__file__, 10)),
        ("File permissions (read)", PreflightChecker.check_file_permissions, (__file__, False)),
        ("File extension check", PreflightChecker.check_file_extension, (__file__, [".py", ".pyw"])),
    ]
    
    for test_name, func, args in tests:
        success, msg = func(*args)
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {msg if msg else 'OK'}")
    
    print("\n🔤 Pattern and Name Validation:")
    print("-" * 40)
    tests = [
        ("Valid method name", PreflightChecker.validate_method_name, ("calculateValue",)),
        ("Invalid method name", PreflightChecker.validate_method_name, ("file.java",)),
        ("Line number valid", PreflightChecker.validate_line_number, ("42",)),
        ("Line number invalid", PreflightChecker.validate_line_number, ("abc",)),
        ("Valid regex", PreflightChecker.check_regex_pattern, (r"test\d+",)),
        ("Invalid regex", PreflightChecker.check_regex_pattern, (r"test[",)),
        ("Valid glob", PreflightChecker.check_glob_pattern, ("*.py",)),
        ("Complex glob", PreflightChecker.check_glob_pattern, ("*" * 20,)),
    ]
    
    for test_name, func, args in tests:
        success, msg = func(*args)
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {msg if msg else 'OK'}")
    
    print("\n🔧 System and Environment Checks:")
    print("-" * 40)
    tests = [
        ("Python version", PreflightChecker.check_python_version, ((3, 6),)),
        ("Git repository", PreflightChecker.check_git_repository, (".",)),
        ("Ripgrep installed", PreflightChecker.check_ripgrep_installed, ()),
        ("Command available (ls)", PreflightChecker.check_command_available, ("ls",)),
        ("Command not available", PreflightChecker.check_command_available, ("definitely_not_a_command",)),
        ("Import available (os)", PreflightChecker.check_import_available, ("os",)),
        ("Import not available", PreflightChecker.check_import_available, ("definitely_not_a_module",)),
    ]
    
    for test_name, func, args in tests:
        success, msg = func(*args)
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {msg if msg else 'OK'}")
    
    print("\n💾 Resource Checks:")
    print("-" * 40)
    tests = [
        ("Disk space", PreflightChecker.check_disk_space, (".", 50)),
        ("Memory available", PreflightChecker.check_memory_available, (100,)),
    ]
    
    for test_name, func, args in tests:
        success, msg = func(*args)
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {msg if msg else 'OK'}")
    
    print("\n📄 File Content Checks:")
    print("-" * 40)
    tests = [
        ("Text file (not binary)", PreflightChecker.check_binary_file, (__file__,)),
        ("UTF-8 encoding", PreflightChecker.check_encoding, (__file__, "utf-8")),
    ]
    
    for test_name, func, args in tests:
        success, msg = func(*args)
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {msg if msg else 'OK'}")
    
    print("\n🔒 Security Checks:")
    print("-" * 40)
    # Create test paths for security check
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        inside_path = base / "subdir" / "file.txt"
        outside_path = Path("/tmp/outside.txt")
        
        tests = [
            ("Path within base (inside)", PreflightChecker.is_path_within_base, (inside_path, base)),
            ("Path within base (outside)", PreflightChecker.is_path_within_base, (outside_path, base)),
        ]
        
        for test_name, func, args in tests:
            success, msg = func(*args)
            status = "✓" if success else "✗"
            print(f"{status} {test_name}: {msg if msg else 'OK'}")
    
    print("\n" + "=" * 60)
    print("Self-test complete!")
    
    # Demonstrate convenience functions
    if "--demo" in sys.argv:
        print("\n📚 Demonstrating convenience functions:")
        print("-" * 40)
        
        print("\nChecking input file...")
        try:
            check_input_file(__file__)
            print("✓ Input file checks passed")
        except SystemExit:
            print("✗ Input file checks failed")
        
        print("\nChecking Python environment...")
        try:
            check_python_env((3, 6), ["os", "sys", "pathlib"])
            print("✓ Python environment checks passed")
        except SystemExit:
            print("✗ Python environment checks failed")
        
        print("\nChecking tool dependencies...")
        try:
            check_tool_dependencies(["ls", "pwd"])
            print("✓ Tool dependency checks passed")
        except SystemExit:
            print("✗ Tool dependency checks failed")