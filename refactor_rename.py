#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Refactor Rename Tool - Code-aware file and symbol renaming.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import re
import sys
import ast
import argparse
import subprocess
import logging
import json
import time
import tempfile
import stat
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import shutil
import errno
from contextlib import contextmanager

# ────────────────────────────  atomic operations  ────────────────────────────

class AtomicWriteError(Exception):
    """Custom exception for atomic write operations."""
    pass

class FileOperationError(Exception):
    """Custom exception for file operations with retry context."""
    def __init__(self, message, original_error=None, attempts=0):
        super().__init__(message)
        self.original_error = original_error
        self.attempts = attempts

@contextmanager
def atomic_write(file_path: Path, mode: str = 'w', encoding: str = 'utf-8', 
                max_retries: int = None, retry_delay: float = None):
    """
    Context manager for atomic file writes with retry logic.
    
    Args:
        file_path: Target file path
        mode: File open mode ('w' for text, 'wb' for binary)
        encoding: Text encoding (only used for text mode)
        max_retries: Maximum retry attempts (env: REFACTOR_MAX_RETRIES)
        retry_delay: Delay between retries in seconds (env: REFACTOR_RETRY_DELAY)
    
    Raises:
        AtomicWriteError: If atomic write fails after all retries
        FileOperationError: If file operations fail with context
    """
    # Get retry parameters from environment or use defaults
    if max_retries is None:
        max_retries = int(os.getenv('REFACTOR_MAX_RETRIES', '3'))
    if retry_delay is None:
        retry_delay = float(os.getenv('REFACTOR_RETRY_DELAY', '0.1'))
    
    file_path = Path(file_path)
    temp_file = None
    attempts = 0
    last_error = None
    
    while attempts <= max_retries:
        try:
            # Create temporary file in same directory for atomic move
            temp_dir = file_path.parent
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            with tempfile.NamedTemporaryFile(
                mode=mode,
                encoding=encoding if 'b' not in mode else None,
                dir=temp_dir,
                prefix=f'.{file_path.name}.',
                suffix='.tmp',
                delete=False
            ) as temp_file:
                temp_path = Path(temp_file.name)
                
                try:
                    yield temp_file
                    temp_file.flush()
                    os.fsync(temp_file.fileno())
                except Exception as e:
                    # Clean up temp file on write error
                    try:
                        temp_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                    raise AtomicWriteError(f"Failed to write to temporary file: {e}") from e
            
            # Check if target file exists and get its permissions
            original_stat = None
            if file_path.exists():
                try:
                    original_stat = file_path.stat()
                except OSError as e:
                    if attempts == max_retries:
                        raise FileOperationError(
                            f"Cannot access target file {file_path}: {e}",
                            e, attempts + 1
                        )
                    LOG.warning(f"Attempt {attempts + 1}/{max_retries + 1}: Cannot stat {file_path}: {e}")
                    last_error = e
                    attempts += 1
                    time.sleep(retry_delay)
                    continue
            
            # Atomic move with retry logic
            try:
                # On Windows, we might need to remove the target first
                if os.name == 'nt' and file_path.exists():
                    file_path.unlink()
                
                # Atomic move
                os.replace(str(temp_path), str(file_path))
                
                # Restore original permissions if they existed
                if original_stat is not None:
                    try:
                        os.chmod(file_path, stat.S_IMODE(original_stat.st_mode))
                    except OSError:
                        # Permission restoration is best-effort
                        pass
                
                LOG.debug(f"Successfully wrote {file_path} after {attempts + 1} attempts")
                return
                
            except OSError as e:
                # Clean up temp file
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
                
                if is_file_locked(file_path, e):
                    if attempts == max_retries:
                        raise FileOperationError(
                            f"File {file_path} is locked and cannot be written after {attempts + 1} attempts",
                            e, attempts + 1
                        )
                    LOG.warning(f"Attempt {attempts + 1}/{max_retries + 1}: File {file_path} appears locked, retrying...")
                else:
                    if attempts == max_retries:
                        raise AtomicWriteError(
                            f"Failed to atomically write {file_path} after {attempts + 1} attempts: {e}"
                        ) from e
                    LOG.warning(f"Attempt {attempts + 1}/{max_retries + 1}: Write failed: {e}")
                
                last_error = e
                attempts += 1
                if attempts <= max_retries:
                    time.sleep(retry_delay)
                
        except (AtomicWriteError, FileOperationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Clean up temp file for any other error
            if temp_file and hasattr(temp_file, 'name'):
                try:
                    Path(temp_file.name).unlink(missing_ok=True)
                except OSError:
                    pass
            
            if attempts == max_retries:
                raise AtomicWriteError(
                    f"Unexpected error during atomic write of {file_path}: {e}"
                ) from e
            
            LOG.warning(f"Attempt {attempts + 1}/{max_retries + 1}: Unexpected error: {e}")
            last_error = e
            attempts += 1
            if attempts <= max_retries:
                time.sleep(retry_delay)
    
    # If we get here, all retries failed
    raise AtomicWriteError(
        f"Failed to write {file_path} after {max_retries + 1} attempts. Last error: {last_error}"
    )

def is_file_locked(file_path: Path, error: OSError) -> bool:
    """
    Determine if a file operation failed due to file locking.
    
    Args:
        file_path: Path that failed to be accessed
        error: The OSError that occurred
    
    Returns:
        True if the error appears to be due to file locking
    """
    # Windows error codes for file locking
    windows_lock_errors = {
        errno.EACCES,   # Permission denied
        errno.EBUSY,    # Device or resource busy
        32,             # ERROR_SHARING_VIOLATION
        33,             # ERROR_LOCK_VIOLATION
    }
    
    # Unix error codes for file locking
    unix_lock_errors = {
        errno.EACCES,   # Permission denied
        errno.EBUSY,    # Device or resource busy
        errno.ETXTBSY,  # Text file busy
        errno.EAGAIN,   # Resource temporarily unavailable
        errno.EWOULDBLOCK,  # Operation would block
    }
    
    error_code = getattr(error, 'errno', None)
    
    # Check both direct errno and winerror for Windows
    if os.name == 'nt':  # Windows
        winerror = getattr(error, 'winerror', None)
        return (error_code in windows_lock_errors or 
                winerror in {32, 33} or  # Windows-specific error codes
                error_code in windows_lock_errors)
    else:  # Unix-like systems
        return error_code in unix_lock_errors

def safe_atomic_move(src: Path, dst: Path, max_retries: int = None, retry_delay: float = None) -> None:
    """
    Atomically move a file with retry logic.
    
    Args:
        src: Source file path
        dst: Destination file path
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries in seconds
    
    Raises:
        FileOperationError: If move fails after all retries
    """
    if max_retries is None:
        max_retries = int(os.getenv('REFACTOR_MAX_RETRIES', '3'))
    if retry_delay is None:
        retry_delay = float(os.getenv('REFACTOR_RETRY_DELAY', '0.1'))
    
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        raise FileOperationError(f"Source file {src} does not exist")
    
    if dst.exists():
        raise FileOperationError(f"Destination file {dst} already exists")
    
    attempts = 0
    last_error = None
    
    while attempts <= max_retries:
        try:
            # Use os.replace for atomic move on most platforms
            os.replace(str(src), str(dst))
            LOG.debug(f"Successfully moved {src} to {dst} after {attempts + 1} attempts")
            return
            
        except OSError as e:
            if is_file_locked(src, e) or is_file_locked(dst, e):
                if attempts == max_retries:
                    raise FileOperationError(
                        f"File move failed due to file locking after {attempts + 1} attempts",
                        e, attempts + 1
                    )
                LOG.warning(f"Attempt {attempts + 1}/{max_retries + 1}: File appears locked, retrying...")
            else:
                if attempts == max_retries:
                    raise FileOperationError(
                        f"File move failed after {attempts + 1} attempts: {e}",
                        e, attempts + 1
                    )
                LOG.warning(f"Attempt {attempts + 1}/{max_retries + 1}: Move failed: {e}")
            
            last_error = e
            attempts += 1
            if attempts <= max_retries:
                time.sleep(retry_delay)
    
    raise FileOperationError(
        f"Failed to move {src} to {dst} after {max_retries + 1} attempts. Last error: {last_error}"
    )

# ────────────────────────────  logging  ────────────────────────────

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

LOG = logging.getLogger("refactor_rename")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s"
)

# Try to import javalang for Java AST parsing
try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False

def check_compile_status(file_path, language=None):
    """Check if file compiles/has valid syntax. Returns (success, short_message).
    
    This function is designed to NEVER break tool functionality:
    - All exceptions are caught and handled gracefully
    - Returns False for unknown languages or when compilers are missing (honest feedback)
    - Uses timeouts to prevent hanging on problematic files
    - Cleans up temporary files (like .class files)
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return False, "Cannot check - file not found"
        
        # Check file size to avoid hanging on huge files
        try:
            file_size = path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                return False, "Cannot check - file too large"
        except OSError:
            return False, "Cannot check - size unknown"
        
        # Auto-detect language if not specified
        if not language:
            suffix = path.suffix.lower()
            if suffix == '.py':
                language = 'python'
            elif suffix == '.java':
                language = 'java'
            elif suffix in ['.js', '.jsx']:
                language = 'javascript'
            elif suffix in ['.ts', '.tsx']:
                language = 'typescript'
            else:
                return False, "Cannot check - unknown language"
        
        # Python syntax check
        if language == 'python':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Skip empty files
                if not content.strip():
                    return False, "Cannot check - empty file"
                
                ast.parse(content)
                return True, "Compiles"
            except SyntaxError:
                return False, "Syntax Error"
            except UnicodeDecodeError:
                return False, "Cannot check - encoding issue"
            except Exception:
                return False, "Cannot check - parse failed"
        
        # Java compilation check
        elif language == 'java':
            try:
                # Check if javac is available
                result = subprocess.run(
                    ['javac', '-version'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode != 0:
                    return False, "Cannot check - javac unavailable"
                
                # Compile the file
                result = subprocess.run(
                    ['javac', '-cp', '.', str(file_path)],
                    capture_output=True, text=True, timeout=30
                )
                
                # Always clean up .class files
                class_file = path.with_suffix('.class')
                if class_file.exists():
                    try:
                        class_file.unlink()
                    except OSError:
                        pass  # Ignore cleanup errors
                
                if result.returncode == 0:
                    return True, "Compiles"
                else:
                    return False, "Compile Error"
                    
            except subprocess.TimeoutExpired:
                return False, "Cannot check - compile timeout"
            except FileNotFoundError:
                return False, "Cannot check - javac not found"
            except Exception:
                return False, "Cannot check - compile failed"
        
        # JavaScript/TypeScript syntax check
        elif language in ['javascript', 'typescript']:
            try:
                if language == 'javascript':
                    # Check if node is available
                    result = subprocess.run(
                        ['node', '--version'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode != 0:
                        return False, "Cannot check - node unavailable"
                    
                    result = subprocess.run(
                        ['node', '-c', str(file_path)],
                        capture_output=True, text=True, timeout=15
                    )
                else:  # typescript
                    # Check if tsc is available
                    result = subprocess.run(
                        ['tsc', '--version'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode != 0:
                        return False, "Cannot check - tsc unavailable"
                    
                    result = subprocess.run(
                        ['tsc', '--noEmit', str(file_path)],
                        capture_output=True, text=True, timeout=20
                    )
                
                if result.returncode == 0:
                    return True, "Compiles"
                else:
                    return False, "Syntax Error"
                    
            except subprocess.TimeoutExpired:
                return False, "Cannot check - timeout"
            except FileNotFoundError:
                return False, "Cannot check - compiler not found"
            except Exception:
                return False, "Cannot check - check failed"
        
        # Default for unknown languages
        return False, "Cannot check - unsupported language"
    
    except Exception:
        # Ultimate fallback - never break the tool
        return False, "Cannot check - internal error"

class CodeRefactorRenamer:
    """Handles code-aware renaming of files and symbols."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False, check_compile: bool = True,
                 max_retries: int = None, retry_delay: float = None):
        self.dry_run = dry_run
        self.verbose = verbose
        self.check_compile = check_compile
        self.max_retries = max_retries if max_retries is not None else int(os.getenv('REFACTOR_MAX_RETRIES', '3'))
        self.retry_delay = retry_delay if retry_delay is not None else float(os.getenv('REFACTOR_RETRY_DELAY', '0.1'))
        
        # Read retry configuration
        self.read_max_retries = int(os.getenv('REFACTOR_READ_MAX_RETRIES', str(self.max_retries)))
        self.read_retry_delay = float(os.getenv('REFACTOR_READ_RETRY_DELAY', str(self.retry_delay)))
        
        self.operations = []
    
    def _read_file_with_retry(self, file_path: Path, max_retries: int = None, retry_delay: float = None) -> str:
        """Read file content with retry logic for locked files."""
        if max_retries is None:
            max_retries = self.read_max_retries
        if retry_delay is None:
            retry_delay = self.read_retry_delay
        
        last_error = None
        for attempt in range(max_retries):
            try:
                return file_path.read_text(encoding='utf-8')
            except OSError as e:
                last_error = e
                if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY, errno.ETXTBSY):
                    if attempt < max_retries - 1:
                        if not os.getenv('QUIET_MODE'):
                            print(f"File {file_path} is locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                raise FileOperationError(f"Failed to read {file_path} after {max_retries} attempts: {e}")
            except Exception as e:
                raise FileOperationError(f"Failed to read {file_path}: {e}")
        
        raise FileOperationError(f"Failed to read {file_path} after {max_retries} attempts: {last_error}")
    
    def log_operation(self, operation: str, details: str):
        """Log an operation for reporting."""
        self.operations.append((operation, details))
        if self.verbose:
            print(f"  {operation}: {details}")
    
    def find_related_files(self, file_path: Path, old_name: str) -> List[Path]:
        """Find files that might be related to the renamed file."""
        related_files = []
        base_dir = file_path.parent
        
        # Common patterns for related files
        patterns = [
            f"{old_name}Test.*",      # Test files
            f"{old_name}Impl.*",      # Implementation files
            f"{old_name}Interface.*", # Interface files
            f"{old_name}Base.*",      # Base classes
            f"{old_name}Abstract.*",  # Abstract classes
            f"Test{old_name}.*",      # Alternative test naming
            f"I{old_name}.*",         # Interface naming convention
        ]
        
        for pattern in patterns:
            import fnmatch
            for item in base_dir.rglob('*'):
                if item.is_file() and fnmatch.fnmatch(item.name, pattern):
                    related_files.append(item)
        
        return related_files
    
    def rename_java_class_content(self, content: str, old_name: str, new_name: str) -> Tuple[str, int]:
        """Rename Java class/interface/enum declarations in content."""
        changes = 0
        
        if JAVALANG_AVAILABLE:
            # Use AST-based approach for more accurate renaming
            try:
                tree = javalang.parse.parse(content)
                
                # Find class declarations to rename
                for path, node in tree:
                    if isinstance(node, (javalang.tree.ClassDeclaration, 
                                       javalang.tree.InterfaceDeclaration,
                                       javalang.tree.EnumDeclaration)):
                        if node.name == old_name:
                            # Use regex for replacement since javalang doesn't support modification
                            pattern = rf'\b(public\s+|private\s+|protected\s+)?(class|interface|enum)\s+{re.escape(old_name)}\b'
                            content = re.sub(pattern, rf'\1\2 {new_name}', content)
                            changes += 1
                
            except Exception as e:
                if self.verbose:
                    print(f"  Warning: AST parsing failed, falling back to regex: {e}")
                # Fall back to regex approach
                return self.rename_java_class_content_regex(content, old_name, new_name)
        else:
            # Use regex approach
            return self.rename_java_class_content_regex(content, old_name, new_name)
        
        return content, changes
    
    def rename_java_class_content_regex(self, content: str, old_name: str, new_name: str) -> Tuple[str, int]:
        """Rename Java class using regex (fallback method)."""
        # Match class, interface, or enum declarations
        patterns = [
            rf'\b(public\s+|private\s+|protected\s+)?(class|interface|enum)\s+{re.escape(old_name)}\b',
            rf'\b(public\s+|private\s+|protected\s+|static\s+)*{re.escape(old_name)}\s*\(',  # Constructor
        ]
        
        changes = 0
        for pattern in patterns:
            new_content, count = re.subn(pattern, lambda m: m.group(0).replace(old_name, new_name), content)
            content = new_content
            changes += count
        
        return content, changes
    
    def rename_python_class_content(self, content: str, old_name: str, new_name: str) -> Tuple[str, int]:
        """Rename Python class definitions in content."""
        try:
            tree = ast.parse(content)
            changes = 0
            
            # Find class definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == old_name:
                    # Use regex for replacement since AST doesn't support modification
                    pattern = rf'\bclass\s+{re.escape(old_name)}\b'
                    content = re.sub(pattern, f'class {new_name}', content)
                    changes += 1
            
            return content, changes
            
        except SyntaxError:
            # Fall back to regex if AST parsing fails
            pattern = rf'\bclass\s+{re.escape(old_name)}\b'
            new_content, changes = re.subn(pattern, f'class {new_name}', content)
            return new_content, changes
    
    def rename_file_content(self, file_path: Path, old_name: str, new_name: str) -> bool:
        """Rename symbols within a file based on its type."""
        try:
            content = self._read_file_with_retry(file_path)
            original_content = content
            changes = 0
            
            if file_path.suffix.lower() == '.java':
                content, changes = self.rename_java_class_content(content, old_name, new_name)
            elif file_path.suffix.lower() == '.py':
                content, changes = self.rename_python_class_content(content, old_name, new_name)
            else:
                # For other file types, use simple text replacement
                content = content.replace(old_name, new_name)
                changes = 1 if content != original_content else 0
            
            if changes > 0:
                if not self.dry_run:
                    # Use atomic write with retry logic
                    try:
                        with atomic_write(file_path, mode='w', encoding='utf-8',
                                        max_retries=getattr(self, 'max_retries', None),
                                        retry_delay=getattr(self, 'retry_delay', None)) as f:
                            f.write(content)
                        
                        # Check compilation if enabled
                        if self.check_compile:
                            try:
                                compile_success, compile_msg = check_compile_status(file_path)
                                compile_status = f"✓ {compile_msg}" if compile_success else f"✗ {compile_msg}"
                                # Always show compile check results (not just in verbose mode)
                                LOG.info("%s", compile_status)
                                self.log_operation("COMPILE CHECK", f"{file_path.name} - {compile_status}")
                            except Exception as e:
                                compile_fail_msg = f"✗ Check failed: {str(e)[:50]}"
                                LOG.error("%s", compile_fail_msg)
                                self.log_operation("COMPILE CHECK", f"{file_path.name} - {compile_fail_msg}")
                    
                    except (AtomicWriteError, FileOperationError) as e:
                        error_msg = f"Failed to write {file_path}: {e}"
                        LOG.error(error_msg)
                        self.log_operation("WRITE ERROR", f"{file_path.name} - {error_msg}")
                        print(f"❌ {error_msg}")
                        return False
                
                self.log_operation("CONTENT UPDATED", f"{file_path.name} ({changes} changes)")
                return True
            else:
                self.log_operation("NO CHANGES", f"{file_path.name} (no matching symbols found)")
                return False
                
        except Exception as e:
            print(f"❌ Error updating content in {file_path}: {e}")
            return False
    
    def rename_file(
        self,
        file_path: Path,
        new_name: Union[str, Path],
        update_content: bool = True,
    ) -> Optional[Path]:
        """Rename a file and optionally update its content."""
        if not file_path.exists():
            print(f"❌ Error: File '{file_path}' does not exist.")
            return None
        
        old_name = file_path.stem
        # Accept both Path and str for convenience
        new_base = Path(new_name).stem if isinstance(new_name, (str, Path)) else str(new_name)
        new_file_path = file_path.with_name(f"{new_base}{file_path.suffix}")
        
        # Check if destination already exists
        if new_file_path.exists():
            print(f"❌ Error: Destination '{new_file_path}' already exists.")
            return None
        
        # Update content first (if requested)
        content_updated = False
        if update_content:
            content_updated = self.rename_file_content(file_path, old_name, new_name)
        
        # Rename the file
        if self.dry_run:
            self.log_operation("WOULD RENAME", f"{file_path.name} → {new_file_path.name}")
        else:
            try:
                # Use atomic move with retry logic
                safe_atomic_move(file_path, new_file_path, 
                               max_retries=self.max_retries, 
                               retry_delay=self.retry_delay)
                
                # Check compilation if enabled (for renamed file)
                if self.check_compile:
                    try:
                        compile_success, compile_msg = check_compile_status(new_file_path)
                        compile_status = f"✓ {compile_msg}" if compile_success else f"✗ {compile_msg}"
                        # Always show compile check results (not just in verbose mode)
                        LOG.info("%s", compile_status)
                        self.log_operation("COMPILE CHECK", f"{new_file_path.name} - {compile_status}")
                    except Exception as e:
                        compile_fail_msg = f"✗ Check failed: {str(e)[:50]}"
                        LOG.error("%s", compile_fail_msg)
                        self.log_operation("COMPILE CHECK", f"{new_file_path.name} - {compile_fail_msg}")
                
                self.log_operation("RENAMED", f"{file_path.name} → {new_file_path.name}")
            except FileOperationError as e:
                error_msg = f"Failed to rename {file_path} to {new_file_path}: {e}"
                if hasattr(e, 'attempts') and e.attempts > 1:
                    error_msg += f" (attempted {e.attempts} times)"
                LOG.error(error_msg)
                self.log_operation("RENAME ERROR", error_msg)
                print(f"❌ {error_msg}")
                return None
            except Exception as e:
                print(f"❌ Error renaming file: {e}")
                return None
        
        return new_file_path
    
    def rename_with_related(self, file_path: Path, new_name: str, 
                          rename_related: bool = True) -> List[Path]:
        """Rename a file and optionally its related files."""
        old_name = file_path.stem
        renamed_files = []
        
        # Find related files first
        related_files = []
        if rename_related:
            related_files = self.find_related_files(file_path, old_name)
            if related_files:
                print(f"🔗 Found {len(related_files)} related files:")
                for related in related_files:
                    print(f"  - {related.name}")
        
        # Rename main file
        new_file_path = self.rename_file(file_path, new_name)
        if new_file_path:
            renamed_files.append(new_file_path)
        
        # Rename related files
        for related_file in related_files:
            related_old_name = related_file.stem
            related_new_name = related_old_name.replace(old_name, new_name)
            
            if related_new_name != related_old_name:
                new_related_path = self.rename_file(related_file, related_new_name)
                if new_related_path:
                    renamed_files.append(new_related_path)
        
        return renamed_files
    
    def batch_rename(self, pattern: str, replacement: str, directory: Path,
                    file_pattern: str = "*", recursive: bool = False) -> List[Path]:
        """Rename multiple files using pattern matching."""
        renamed_files = []
        
        # Find files matching the pattern
        if recursive:
            files = list(directory.rglob(file_pattern))
        else:
            files = list(directory.glob(file_pattern))
        
        files = [f for f in files if f.is_file() and pattern in f.stem]
        
        print(f"📋 Found {len(files)} files matching pattern '{pattern}' in '{directory}'")
        
        for file_path in files:
            old_name = file_path.stem
            new_name = old_name.replace(pattern, replacement)
            
            if new_name != old_name:
                new_file_path = self.rename_file(file_path, new_name)
                if new_file_path:
                    renamed_files.append(new_file_path)
        
        return renamed_files
    
    def code_aware_replace(self, old_symbol: str, new_symbol: str, target_pattern: str, 
                          symbol_type: str = 'auto') -> List[Path]:
        """Code-aware search and replace for variables, methods, or classes."""
        import glob
        
        # Find target files
        target_files = []
        for pattern in target_pattern.split(','):
            target_files.extend([Path(f) for f in glob.glob(pattern.strip(), recursive=True)])
        
        # Remove duplicates and filter for files
        target_files = list(set([f for f in target_files if f.is_file()]))
        
        if not target_files:
            print(f"❌ No files found matching pattern: {target_pattern}")
            return []
        
        print(f"🔍 Processing {len(target_files)} files for symbol replacement...")
        
        modified_files = []
        
        for file_path in target_files:
            if self.replace_symbol_in_file(file_path, old_symbol, new_symbol, symbol_type):
                modified_files.append(file_path)
        
        return modified_files
    
    def replace_symbol_in_file(self, file_path: Path, old_symbol: str, new_symbol: str, 
                              symbol_type: str) -> bool:
        """Replace symbol in a single file using AST when possible."""
        try:
            content = self._read_file_with_retry(file_path)
            original_content = content
            
            # Determine file type
            file_ext = file_path.suffix.lower()
            
            if file_ext == '.py':
                content = self.replace_python_symbol(content, old_symbol, new_symbol, symbol_type)
            elif file_ext == '.java':
                content = self.replace_java_symbol(content, old_symbol, new_symbol, symbol_type)
            else:
                # Fallback to safe text replacement for other file types
                content = self.safe_text_replace(content, old_symbol, new_symbol)
            
            # Check if content was modified
            if content != original_content:
                if self.dry_run:
                    self.log_operation("WOULD REPLACE", str(file_path))
                else:
                    # Use atomic write with retry logic
                    try:
                        with atomic_write(file_path, mode='w', encoding='utf-8',
                                        max_retries=self.max_retries,
                                        retry_delay=self.retry_delay) as f:
                            f.write(content)
                        
                        # Check compilation if enabled
                        if self.check_compile:
                            try:
                                compile_success, compile_msg = check_compile_status(file_path)
                                compile_status = f"✓ {compile_msg}" if compile_success else f"✗ {compile_msg}"
                                # Always show compile check results (not just in verbose mode)
                                LOG.info("%s", compile_status)
                                self.log_operation("COMPILE CHECK", f"{file_path.name} - {compile_status}")
                            except Exception as e:
                                compile_fail_msg = f"✗ Check failed: {str(e)[:50]}"
                                LOG.error("%s", compile_fail_msg)
                                self.log_operation("COMPILE CHECK", f"{file_path.name} - {compile_fail_msg}")
                        
                        self.log_operation("REPLACED", str(file_path))
                    
                    except (AtomicWriteError, FileOperationError) as e:
                        error_msg = f"Failed to write {file_path}: {e}"
                        LOG.error(error_msg)
                        self.log_operation("WRITE ERROR", f"{file_path.name} - {error_msg}")
                        if self.verbose:
                            print(f"❌ {error_msg}")
                        return False
                return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error processing {file_path}: {e}")
        
        return False
    
    def replace_python_symbol(self, content: str, old_symbol: str, new_symbol: str, 
                             symbol_type: str) -> str:
        """Replace Python symbols using AST analysis."""
        try:
            tree = ast.parse(content)
            replacements = []
            
            class SymbolReplacer(ast.NodeVisitor):
                def visit_Name(self, node):
                    if node.id == old_symbol:
                        # Calculate position for replacement
                        replacements.append((node.lineno, node.col_offset, len(old_symbol)))
                    self.generic_visit(node)
                
                def visit_FunctionDef(self, node):
                    if symbol_type in ['method', 'function', 'auto'] and node.name == old_symbol:
                        replacements.append((node.lineno, node.col_offset, len(old_symbol)))
                    self.generic_visit(node)
                
                def visit_ClassDef(self, node):
                    if symbol_type in ['class', 'auto'] and node.name == old_symbol:
                        replacements.append((node.lineno, node.col_offset, len(old_symbol)))
                    self.generic_visit(node)
            
            replacer = SymbolReplacer()
            replacer.visit(tree)
            
            if replacements:
                # Apply replacements from end to beginning to maintain positions
                lines = content.split('\n')
                for line_num, col_offset, length in reversed(replacements):
                    line = lines[line_num - 1]  # AST uses 1-based line numbers
                    if line[col_offset:col_offset + length] == old_symbol:
                        lines[line_num - 1] = (line[:col_offset] + new_symbol + 
                                              line[col_offset + length:])
                
                return '\n'.join(lines)
            
        except SyntaxError:
            # Fallback to safe text replacement for invalid syntax
            return self.safe_text_replace(content, old_symbol, new_symbol)
        
        return content
    
    def replace_java_symbol(self, content: str, old_symbol: str, new_symbol: str, 
                           symbol_type: str) -> str:
        """Replace Java symbols using javalang if available."""
        if not JAVALANG_AVAILABLE:
            return self.safe_text_replace(content, old_symbol, new_symbol)
        
        try:
            tree = javalang.parse.parse(content)
            replacements = []
            
            # Walk the AST to find symbol usages
            for path, node in tree.filter(javalang.tree.ReferenceType):
                if hasattr(node, 'name') and node.name == old_symbol:
                    if hasattr(node, 'position'):
                        replacements.append(node.position)
            
            for path, node in tree.filter(javalang.tree.MethodDeclaration):
                if node.name == old_symbol and symbol_type in ['method', 'auto']:
                    if hasattr(node, 'position'):
                        replacements.append(node.position)
            
            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                if node.name == old_symbol and symbol_type in ['class', 'auto']:
                    if hasattr(node, 'position'):
                        replacements.append(node.position)
            
            # Apply replacements if found
            if replacements:
                lines = content.split('\n')
                for pos in reversed(sorted(replacements, key=lambda x: (x.line, x.column))):
                    line_idx = pos.line - 1
                    col_idx = pos.column - 1
                    line = lines[line_idx]
                    
                    if line[col_idx:col_idx + len(old_symbol)] == old_symbol:
                        lines[line_idx] = (line[:col_idx] + new_symbol + 
                                          line[col_idx + len(old_symbol):])
                
                return '\n'.join(lines)
            
        except Exception:
            # Fallback to safe text replacement
            return self.safe_text_replace(content, old_symbol, new_symbol)
        
        return content
    
    def safe_text_replace(self, content: str, old_symbol: str, new_symbol: str) -> str:
        """Safe text replacement that avoids partial matches."""
        import re
        
        # Use word boundaries to avoid partial replacements
        pattern = r'\b' + re.escape(old_symbol) + r'\b'
        
        # Avoid replacements inside strings and comments (basic heuristic)
        lines = content.split('\n')
        result_lines = []
        
        for line in lines:
            # Skip lines that are clearly comments or strings
            stripped = line.strip()
            if (stripped.startswith('#') or stripped.startswith('//') or 
                stripped.startswith('*') or stripped.startswith('/*')):
                result_lines.append(line)
                continue
            
            # Simple check to avoid replacements inside string literals
            in_string = False
            quote_char = None
            new_line = ""
            i = 0
            
            while i < len(line):
                char = line[i]
                
                if not in_string and char in ['"', "'"]:
                    in_string = True
                    quote_char = char
                elif in_string and char == quote_char and (i == 0 or line[i-1] != '\\'):
                    in_string = False
                    quote_char = None
                
                new_line += char
                i += 1
            
            # Apply replacement only if we're not inside a string
            if not in_string:
                new_line = re.sub(pattern, new_symbol, line)
            else:
                new_line = line
            
            result_lines.append(new_line)
        
        return '\n'.join(result_lines)
    
    def print_summary(self):
        """Print operation summary."""
        print(f"\n📊 Rename Summary:")
        print("-" * 40)
        
        operation_counts = {}
        for operation, _ in self.operations:
            operation_counts[operation] = operation_counts.get(operation, 0) + 1
        
        for operation, count in operation_counts.items():
            print(f"  {operation}: {count}")
        
        print(f"\nTotal operations: {len(self.operations)}")

def confirm_action(prompt: str, auto_yes: bool = False) -> bool:
    """Ask user for confirmation. Returns True in non-interactive environments or if auto_yes is True."""
    try:
        # Auto-confirm if requested
        if auto_yes:
            print(f"{prompt} [y/N]: y (auto-confirmed)")
            return True
        
        # Check if we're in a non-interactive environment
        import sys
        if not sys.stdin.isatty():
            print(f"{prompt} [y/N]: y (auto-confirmed in non-interactive mode)")
            return True
        
        while True:
            response = input(f"{prompt} [y/N]: ").lower().strip()
            if response in ['y', 'yes']:
                return True
            if response in ['n', 'no', '']:
                return False
    except (EOFError, KeyboardInterrupt):
        # Handle EOF or interrupt gracefully
        print("\n🛑 Operation cancelled.")
        return False

def main():
    # Don't use standard parser due to custom argument structure
    parser = argparse.ArgumentParser(description="Code-aware file and symbol renaming")
    
    # Main arguments
    parser.add_argument('file', nargs='?', help='File to rename')
    parser.add_argument('new_name', nargs='?', help='New name (without extension)')
    
    # Batch mode
    parser.add_argument('--batch', nargs=4, metavar=('PATTERN', 'REPLACEMENT', 'DIRECTORY', 'FILE_PATTERN'),
                       help='Batch rename: pattern replacement directory file_pattern')
    
    # Code-aware search and replace
    parser.add_argument('--replace', nargs=2, metavar=('OLD_SYMBOL', 'NEW_SYMBOL'),
                       help='Code-aware search and replace for variables/methods')
    parser.add_argument('--in', dest='target_files', metavar='PATTERN',
                       help='Target files pattern for replace operation (e.g., "src/**/*.py")')
    parser.add_argument('--symbol-type', choices=['variable', 'method', 'class', 'auto'], 
                       default='auto', help='Type of symbol to replace (default: auto)')
    
    # Options
    parser.add_argument('--related', action='store_true',
                       help='Also rename related files (e.g., tests)')
    parser.add_argument('--content-only', action='store_true',
                       help='Update file content only, do not rename file')
    parser.add_argument('--no-content', action='store_true',
                       help='Rename file only, do not update content')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Recursively search directories (for batch operations)')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format (for CI/CD integration)')
    
    # Compile checking options
    parser.add_argument('--check-compile', action='store_true', default=True,
                       help='Check syntax/compilation after operations (default: enabled)')
    parser.add_argument('--no-check-compile', action='store_true',
                       help='Disable compile checking')
    
    # Automation options
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm all operations (for automation)')
    
    # Retry control options
    parser.add_argument('--max-retries', type=int, metavar='N',
                       help='Maximum retry attempts for file operations (default: 3, env: REFACTOR_MAX_RETRIES)')
    parser.add_argument('--retry-delay', type=float, metavar='SECONDS',
                       help='Delay between retries in seconds (default: 0.1, env: REFACTOR_RETRY_DELAY)')
    
    # Dry run option
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    # Handle compile check flags
    check_compile = getattr(args, 'check_compile', True)  # Default to True
    if getattr(args, 'no_check_compile', False):
        check_compile = False
    
    # Validate arguments
    if args.replace:
        if not args.target_files:
            print("❌ Error: --replace requires --in to specify target files.")
            return 1
        if args.batch or args.file or args.new_name:
            print("❌ Error: Cannot use --replace with other rename operations.")
            return 1
    elif args.batch:
        if args.file or args.new_name:
            print("❌ Error: Cannot use --batch with individual file arguments.")
            return 1
    else:
        if not args.file or not args.new_name:
            parser.print_help()
            return 1
    
    # Initialize renamer in forced dry-run mode first to gather operations
    renamer = CodeRefactorRenamer(
        dry_run=True, 
        verbose=args.verbose, 
        check_compile=check_compile,
        max_retries=getattr(args, 'max_retries', None),
        retry_delay=getattr(args, 'retry_delay', None)
    )
    if not args.dry_run:
        print("🔍 Analyzing changes...")
    
    # Execute operation
    # This first pass is always a dry run to log potential operations
    if args.replace:
        old_symbol, new_symbol = args.replace
        renamer.code_aware_replace(old_symbol, new_symbol, args.target_files, args.symbol_type)
    elif args.batch:
        pattern, replacement, directory_str, file_pattern = args.batch
        directory = Path(directory_str)
        if not directory.exists():
            print(f"❌ Error: Directory '{directory}' does not exist.")
            return 1
        renamer.batch_rename(pattern, replacement, directory, file_pattern, args.recursive)
    else:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Error: File '{file_path}' does not exist.")
            return 1
        if args.content_only:
            old_name = file_path.stem
            renamer.rename_file_content(file_path, old_name, args.new_name)
        else:
            update_content = not args.no_content
            if args.related:
                renamer.rename_with_related(file_path, args.new_name, True)
            else:
                renamer.rename_file(file_path, args.new_name, update_content)
    
    # --- Confirmation Step ---
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be changed")
        renamer.print_summary()
        return 0

    if not renamer.operations:
        print("\n⚠️  No applicable files or symbols found to rename.")
        return 0

    renamer.print_summary()
    if not confirm_action("\nProceed with these changes?", args.yes):
        print("🛑 Aborted by user.")
        return 1

    # --- Execute for Real ---
    print("\n🚀 Executing changes...")
    renamer.dry_run = False
    renamer.check_compile = check_compile  # Re-enable compile checking for actual execution
    renamer.operations = [] # Clear logged operations for a clean summary
    renamed_files = []
    
    # Log retry configuration if non-default
    if renamer.max_retries != 3 or renamer.retry_delay != 0.1:
        LOG.info(f"Using retry configuration: max_retries={renamer.max_retries}, retry_delay={renamer.retry_delay}s")

    if args.replace:
        old_symbol, new_symbol = args.replace
        renamed_files = renamer.code_aware_replace(old_symbol, new_symbol, args.target_files, args.symbol_type)
    elif args.batch:
        pattern, replacement, directory_str, file_pattern = args.batch
        renamed_files = renamer.batch_rename(pattern, replacement, Path(directory_str), file_pattern, args.recursive)
    else:
        file_path = Path(args.file)
        update_content = not args.no_content
        if args.content_only:
            if renamer.rename_file_content(file_path, file_path.stem, args.new_name):
                renamed_files = [file_path]
        elif args.related:
            renamed_files = renamer.rename_with_related(file_path, args.new_name, True)
        else:
            new_file = renamer.rename_file(file_path, args.new_name, update_content)
            if new_file:
                renamed_files.append(new_file)

    # ──────── summary ────────
    if args.json:
        # JSON output for CI/CD integration
        output = {
            "processed": len(renamed_files),
            "operations": [(op[0], op[1]) for op in renamer.operations],  # Convert tuples to lists
            "files": [str(f) for f in renamed_files],
            "success": len(renamed_files) > 0
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        renamer.print_summary()
        if renamed_files:
            LOG.info("✅ Successfully processed %d files", len(renamed_files))
            if args.verbose:
                for file_path in renamed_files:
                    print(f"  - {file_path}")
        else:
            LOG.warning("⚠️  No files were processed")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())