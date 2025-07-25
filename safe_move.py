#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Safe Move Tool - Smart file operations with undo capability and safety features.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import json
import shutil
import argparse
import logging
import subprocess
import threading
import time
import hashlib
import fcntl
import errno
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable
from glob import glob
from contextlib import contextmanager

# ────────────────────────────  logging  ────────────────────────────

# Environment variables for configuration
DEFAULT_MAX_RETRIES = int(os.getenv("SAFE_MOVE_MAX_RETRIES", "3"))
DEFAULT_RETRY_DELAY = float(os.getenv("SAFE_MOVE_RETRY_DELAY", "0.5"))
DEFAULT_OPERATION_TIMEOUT = int(os.getenv("SAFE_MOVE_TIMEOUT", "30"))
DEFAULT_CHECKSUM_VERIFY = os.getenv("SAFE_MOVE_VERIFY_CHECKSUM", "true").lower() == "true"

# Non-interactive mode environment variables
DEFAULT_ASSUME_YES = os.getenv("SAFE_MOVE_ASSUME_YES", "false").lower() == "true"
DEFAULT_NONINTERACTIVE = os.getenv("SAFE_MOVE_NONINTERACTIVE", "false").lower() == "true"

# Specific environment variables for checksum operations
DEFAULT_CHECKSUM_MAX_RETRIES = int(os.getenv("SAFE_MOVE_CHECKSUM_MAX_RETRIES", "5"))
DEFAULT_CHECKSUM_RETRY_DELAY = float(os.getenv("SAFE_MOVE_CHECKSUM_RETRY_DELAY", "0.2"))

# Note: Using clean ArgumentParser instead of standard_arg_parser 
# to avoid confusing method analysis options in file operations tool

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

# Import common config
try:
    from common_config import load_config, get_config_value
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False
    def load_config(project_root=None):
        return None
    def get_config_value(key, default=None, tool_name=None, config=None):
        return default

LOG = logging.getLogger("safe_move")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s"
)

# Centralized validation
try:
    from preflight_checks import PreflightChecker, run_preflight_checks
    HAS_PREFLIGHT = True
except ImportError:
    HAS_PREFLIGHT = False

# --- configuration is per-instance, not module-global -------------
_UNDO_LOCK = threading.Lock()          # still global – guards any history file

# -------------------------------------------------------------------
# safety helpers and enhanced atomic operations
# -------------------------------------------------------------------
def _require(cmd: str):
    """Abort early if an external dependency is missing."""
    if shutil.which(cmd) is None:
        LOG.critical("Required executable '%s' not found in PATH – aborting", cmd)
        sys.exit(2)

class FileOperationError(Exception):
    """Custom exception for file operation failures."""
    pass

class FileLockError(FileOperationError):
    """Exception for file lock conflicts."""
    pass

class ChecksumMismatchError(FileOperationError):
    """Exception for checksum verification failures."""
    pass

@contextmanager
def timeout_handler(timeout_seconds: int):
    """Context manager for operation timeout."""
    def timeout_signal_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
    
    # Set up signal handler for timeout
    old_handler = signal.signal(signal.SIGALRM, timeout_signal_handler)
    signal.alarm(timeout_seconds)
    
    try:
        yield
    finally:
        # Restore original handler and cancel alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def _is_file_locked(file_path: Path) -> Tuple[bool, str]:
    """Check if a file is locked by another process."""
    try:
        if not file_path.exists():
            return False, "File does not exist"
        
        with open(file_path, 'r+b') as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return False, "File is not locked"
            except IOError as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EACCES:
                    return True, f"File is locked by another process (errno: {e.errno})"
                else:
                    return False, f"Lock check failed: {e}"
    except (IOError, OSError) as e:
        return False, f"Cannot check lock status: {e}"

def _calculate_checksum(
    file_path: Path, 
    max_retries: int = DEFAULT_CHECKSUM_MAX_RETRIES,
    retry_delay: float = DEFAULT_CHECKSUM_RETRY_DELAY
) -> str:
    """Calculate MD5 checksum of a file with enhanced read-retry logic."""
    
    def perform_checksum_calculation():
        hash_md5 = hashlib.md5()
        
        # Check if file is locked before attempting to read
        is_locked, lock_info = _is_file_locked(file_path)
        if is_locked:
            LOG.warning(f"File appears locked during checksum calculation: {lock_info}")
            # Wait briefly for file to become unlocked
            if not _wait_for_file_unlock(file_path, max_wait_seconds=2):
                raise FileLockError(f"Cannot calculate checksum: file {file_path} is locked: {lock_info}")
        
        try:
            with open(file_path, "rb") as f:
                while True:
                    try:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        hash_md5.update(chunk)
                    except (IOError, OSError) as e:
                        # Handle specific read errors that might indicate file locks or I/O issues
                        if e.errno in (errno.EAGAIN, errno.EACCES, errno.EBUSY):
                            raise FileLockError(f"File read blocked during checksum calculation: {e}")
                        else:
                            raise FileOperationError(f"I/O error during checksum calculation: {e}")
            
            return hash_md5.hexdigest()
            
        except (IOError, OSError) as e:
            # Re-raise as specific exceptions for retry logic
            if e.errno in (errno.EAGAIN, errno.EACCES, errno.EBUSY):
                raise FileLockError(f"File access blocked during checksum calculation: {e}")
            else:
                raise FileOperationError(f"Failed to read file for checksum calculation: {e}")
    
    # Use the retry operation with specific error handling for checksum calculation
    try:
        return _retry_operation(
            perform_checksum_calculation,
            max_retries=max_retries,
            retry_delay=retry_delay,
            operation_name=f"checksum calculation for {file_path}"
        )
    except (FileLockError, FileOperationError) as e:
        # Enhance error message with recovery suggestions
        error_msg = f"Failed to calculate checksum for {file_path}: {e}"
        if "lock" in str(e).lower():
            error_msg += f"\n💡 Recovery suggestion: File may be in use by another process. Try again in a moment."
        raise FileOperationError(error_msg)

def _wait_for_file_unlock(file_path: Path, max_wait_seconds: int = 10) -> bool:
    """Wait for a file to become unlocked."""
    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        is_locked, _ = _is_file_locked(file_path)
        if not is_locked:
            return True
        time.sleep(0.1)
    return False

def _retry_operation(
    operation: Callable,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    operation_name: str = "operation"
) -> Any:
    """Retry an operation with exponential backoff."""
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except (IOError, OSError, FileOperationError, FileLockError) as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = retry_delay * (2 ** attempt)
                LOG.warning(f"Attempt {attempt + 1} of {operation_name} failed: {e}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                LOG.error(f"All {max_retries + 1} attempts of {operation_name} failed")
    
    raise last_exception

def _atomic_replace(src: Path, dst: Path):
    """Move/replace atomically, preserving permissions."""
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    shutil.move(str(src), str(tmp))
    tmp.replace(dst)

def _enhanced_atomic_move(
    src: Path, 
    dst: Path, 
    verify_checksum: bool = DEFAULT_CHECKSUM_VERIFY,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    operation_timeout: int = DEFAULT_OPERATION_TIMEOUT
) -> Dict[str, Any]:
    """Enhanced atomic move with checksum verification and retry logic."""
    
    # Check if source file is locked
    is_locked, lock_info = _is_file_locked(src)
    if is_locked:
        LOG.warning(f"Source file appears locked: {lock_info}")
        if not _wait_for_file_unlock(src, max_wait_seconds=5):
            raise FileLockError(f"Source file {src} is locked and could not be unlocked: {lock_info}")
    
    # Calculate source checksum if verification enabled
    src_checksum = None
    if verify_checksum:
        src_checksum = _calculate_checksum(src)
    
    def perform_move():
        with timeout_handler(operation_timeout):
            # Create unique temporary file name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            tmp = dst.with_name(f"{dst.name}.tmp_{timestamp}")
            
            try:
                # Ensure destination directory exists
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy to temporary location first
                shutil.copy2(str(src), str(tmp))
                
                # Verify checksum if enabled
                if verify_checksum:
                    tmp_checksum = _calculate_checksum(tmp)
                    if src_checksum != tmp_checksum:
                        tmp.unlink()  # Clean up failed copy
                        raise ChecksumMismatchError(
                            f"Checksum mismatch: source={src_checksum}, temp={tmp_checksum}"
                        )
                
                # Atomic replace
                tmp.replace(dst)
                
                # Remove original source file
                src.unlink()
                
                return {
                    'success': True,
                    'checksum_verified': verify_checksum,
                    'src_checksum': src_checksum,
                    'tmp_file': str(tmp)
                }
                
            except Exception as e:
                # Clean up temporary file if it exists
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except OSError:
                        pass
                raise e
    
    return _retry_operation(
        perform_move,
        max_retries=max_retries,
        retry_delay=retry_delay,
        operation_name=f"atomic move {src} -> {dst}"
    )

def _enhanced_atomic_copy(
    src: Path, 
    dst: Path, 
    verify_checksum: bool = DEFAULT_CHECKSUM_VERIFY,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    operation_timeout: int = DEFAULT_OPERATION_TIMEOUT
) -> Dict[str, Any]:
    """Enhanced atomic copy with checksum verification and retry logic."""
    
    # Check if source file is locked
    is_locked, lock_info = _is_file_locked(src)
    if is_locked:
        LOG.warning(f"Source file appears locked: {lock_info}")
        # For copy operations, we can still proceed if the file is readable
    
    # Calculate source checksum if verification enabled
    src_checksum = None
    if verify_checksum:
        src_checksum = _calculate_checksum(src)
    
    def perform_copy():
        with timeout_handler(operation_timeout):
            # Create unique temporary file name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            tmp = dst.with_name(f"{dst.name}.tmp_{timestamp}")
            
            try:
                # Ensure destination directory exists
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy to temporary location
                shutil.copy2(str(src), str(tmp))
                
                # Verify checksum if enabled
                if verify_checksum:
                    tmp_checksum = _calculate_checksum(tmp)
                    if src_checksum != tmp_checksum:
                        tmp.unlink()  # Clean up failed copy
                        raise ChecksumMismatchError(
                            f"Checksum mismatch: source={src_checksum}, temp={tmp_checksum}"
                        )
                
                # Atomic replace
                tmp.replace(dst)
                
                return {
                    'success': True,
                    'checksum_verified': verify_checksum,
                    'src_checksum': src_checksum,
                    'tmp_file': str(tmp)
                }
                
            except Exception as e:
                # Clean up temporary file if it exists
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except OSError:
                        pass
                raise e
    
    return _retry_operation(
        perform_copy,
        max_retries=max_retries,
        retry_delay=retry_delay,
        operation_name=f"atomic copy {src} -> {dst}"
    )

def _default_undo_log() -> Path:
    return (Path(os.environ.get("SAFE_MOVE_HISTORY",
                                Path.home() / ".safe_move_history"))
            .expanduser().resolve())

def _default_trash_dir() -> Path:
    return (Path(os.environ.get("SAFE_MOVE_TRASH",
                                Path.home() / ".safe_move_trash"))
            .expanduser().resolve())

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
                
                import ast
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
                import subprocess
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
                import subprocess
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

class SafeMover:
    """Handles safe file operations with logging and undo capability."""
    
    def __init__(
        self,
        dry_run: bool = False,
        verbose: bool = False,
        undo_log: Optional[Path] = None,
        trash_dir: Optional[Path] = None,
        check_compile: bool = False,
        verify_checksum: bool = DEFAULT_CHECKSUM_VERIFY,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        operation_timeout: int = DEFAULT_OPERATION_TIMEOUT,
        assume_yes: bool = DEFAULT_ASSUME_YES,
        non_interactive: bool = DEFAULT_NONINTERACTIVE,
    ):
        self.dry_run = dry_run
        self.verbose = verbose
        self.check_compile = check_compile
        self.verify_checksum = verify_checksum
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.operation_timeout = operation_timeout
        self.assume_yes = assume_yes
        self.non_interactive = non_interactive
        self.operations_count = 0
        self.undo_log = (undo_log or _default_undo_log()).resolve()
        self.trash_dir = (trash_dir or _default_trash_dir()).resolve()
        self.undo_log.parent.mkdir(parents=True, exist_ok=True)
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        
        if self.verbose:
            LOG.info(f"SafeMover initialized with: retries={max_retries}, "
                    f"timeout={operation_timeout}s, checksum_verify={verify_checksum}")
        
    def _log_operation(self, op_type: str, source: Path, dest: Path, metadata: Optional[Dict[str, Any]] = None):
        """Logs an operation to the undo log."""
        if self.dry_run:
            return
            
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'op_type': op_type,
            'source': str(source),
            'dest': str(dest),
            'metadata': metadata or {}
        }
        
        with _UNDO_LOCK, self.undo_log.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def safe_backup(self, dest: Path) -> Path:
        """Safely backs up an existing file to trash."""
        if not dest.exists():
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{dest.name}.backup_{timestamp}"
        backup_path = self.trash_dir / backup_name
        
        if not self.dry_run:
            os.replace(dest, backup_path)  # atomic on-filesystem
        
        # Always show backup message (even in dry run for visibility)
        print(f"  📦 Backed up existing '{dest}' to trash as '{backup_name}'")
            
        return backup_path
    
    def safe_move(self, source: Path, dest: Path) -> bool:
        """Safely moves a file, handling overwrites with enhanced atomic operations."""
        if not source.exists():
            print(f"❌ Error: Source '{source}' does not exist.")
            return False
            
        # Handle destination directory creation
        if dest.is_dir() or str(dest).endswith('/'):
            dest = dest / source.name
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Pre-flight file lock check
        is_locked, lock_info = _is_file_locked(source)
        if is_locked:
            print(f"⚠️  Warning: Source file appears locked: {lock_info}")
            if not _wait_for_file_unlock(source, max_wait_seconds=5):
                print(f"❌ Error: Cannot proceed with locked file: {source}")
                return False
            print("✅ File lock released, proceeding...")
        
        backup_path = None
        if dest.exists():
            backup_path = self.safe_backup(dest)
        
        if self.dry_run:
            print(f"🔍 [DRY RUN] Would move '{source}' → '{dest}'")
            if self.verify_checksum:
                print("🔍 [DRY RUN] Would verify checksums")
        else:
            try:
                # Use enhanced atomic move with retry logic
                operation_result = _enhanced_atomic_move(
                    source, dest,
                    verify_checksum=self.verify_checksum,
                    max_retries=self.max_retries,
                    retry_delay=self.retry_delay,
                    operation_timeout=self.operation_timeout
                )
                
                # Log the operation
                metadata = {
                    'backup_path': str(backup_path) if backup_path else None,
                    'checksum_verified': operation_result.get('checksum_verified', False),
                    'src_checksum': operation_result.get('src_checksum'),
                    'operation_result': operation_result
                }
                self._log_operation('move', source, dest, metadata)
                
                # Build success message with detailed feedback
                success_msg = f"✅ Moved '{source}' → '{dest}'"
                
                if operation_result.get('checksum_verified'):
                    success_msg += f"\n🔐 Checksum verified: {operation_result['src_checksum'][:8]}..."
                
                # Check compilation if requested
                if self.check_compile:
                    try:
                        compile_success, compile_msg = check_compile_status(dest)
                        compile_status = f"✓ {compile_msg}" if compile_success else f"✗ {compile_msg}"
                        success_msg += f"\n{compile_status}"
                    except Exception as e:
                        # Never let compile check break the tool
                        success_msg += f"\n✗ Compile check failed: {str(e)[:50]}"
                
                print(success_msg)
                
            except (FileOperationError, FileLockError, ChecksumMismatchError, TimeoutError) as e:
                print(f"❌ Enhanced operation failed for '{source}': {e}")
                if "retry" in str(e).lower():
                    print(f"💡 Recovery suggestion: Try with --max-retries {self.max_retries * 2}")
                if "checksum" in str(e).lower():
                    print(f"💡 Recovery suggestion: Try with --no-verify-checksum")
                if "timeout" in str(e).lower():
                    print(f"💡 Recovery suggestion: Try with --timeout {self.operation_timeout * 2}")
                return False
            except Exception as e:
                print(f"❌ Unexpected error moving '{source}': {e}")
                return False
                
        self.operations_count += 1
        return True
    
    def safe_copy(self, source: Path, dest: Path) -> bool:
        """Safely copies a file, handling overwrites with enhanced atomic operations."""
        if not source.exists():
            print(f"❌ Error: Source '{source}' does not exist.")
            return False
            
        # Handle destination directory creation
        if dest.is_dir() or str(dest).endswith('/'):
            dest = dest / source.name
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Pre-flight file lock check (less strict for copy operations)
        is_locked, lock_info = _is_file_locked(source)
        if is_locked:
            print(f"⚠️  Warning: Source file appears locked: {lock_info}")
            print("ℹ️  Proceeding with copy operation (read-only access)...")
        
        backup_path = None
        if dest.exists():
            backup_path = self.safe_backup(dest)
        
        if self.dry_run:
            print(f"🔍 [DRY RUN] Would copy '{source}' → '{dest}'")
            if self.verify_checksum:
                print("🔍 [DRY RUN] Would verify checksums")
        else:
            try:
                # Use enhanced atomic copy with retry logic
                operation_result = _enhanced_atomic_copy(
                    source, dest,
                    verify_checksum=self.verify_checksum,
                    max_retries=self.max_retries,
                    retry_delay=self.retry_delay,
                    operation_timeout=self.operation_timeout
                )
                
                # Log the operation
                metadata = {
                    'backup_path': str(backup_path) if backup_path else None,
                    'checksum_verified': operation_result.get('checksum_verified', False),
                    'src_checksum': operation_result.get('src_checksum'),
                    'operation_result': operation_result
                }
                self._log_operation('copy', source, dest, metadata)
                
                # Build success message with detailed feedback
                success_msg = f"✅ Copied '{source}' → '{dest}'"
                
                if operation_result.get('checksum_verified'):
                    success_msg += f"\n🔐 Checksum verified: {operation_result['src_checksum'][:8]}..."
                
                # Check compilation if requested
                if self.check_compile:
                    try:
                        compile_success, compile_msg = check_compile_status(dest)
                        compile_status = f"✓ {compile_msg}" if compile_success else f"✗ {compile_msg}"
                        success_msg += f"\n{compile_status}"
                    except Exception as e:
                        # Never let compile check break the tool
                        success_msg += f"\n✗ Compile check failed: {str(e)[:50]}"
                
                print(success_msg)
                
            except (FileOperationError, ChecksumMismatchError, TimeoutError) as e:
                print(f"❌ Enhanced operation failed for '{source}': {e}")
                if "retry" in str(e).lower():
                    print(f"💡 Recovery suggestion: Try with --max-retries {self.max_retries * 2}")
                if "checksum" in str(e).lower():
                    print(f"💡 Recovery suggestion: Try with --no-verify-checksum")
                if "timeout" in str(e).lower():
                    print(f"💡 Recovery suggestion: Try with --timeout {self.operation_timeout * 2}")
                return False
            except Exception as e:
                print(f"❌ Unexpected error copying '{source}': {e}")
                return False
                
        self.operations_count += 1
        return True
    
    def batch_move(self, sources: List[Path], dest_dir: Path) -> int:
        """Move multiple files to a destination directory."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        success_count = 0
        
        print(f"📂 Moving {len(sources)} files to '{dest_dir}'")
        
        for i, source in enumerate(sources, 1):
            if self.verbose:
                print(f"  [{i}/{len(sources)}] ", end="")
            
            if self.safe_move(source, dest_dir):
                success_count += 1
                
        return success_count

def show_undo_history(limit: int = 10):
    """Show recent operations from undo log."""
    undo_log = _default_undo_log()
    if not undo_log.exists():
        print("📝 No operation history found.")
        return
        
    print(f"📜 Last {limit} operations:")
    print("-" * 60)
    
    with open(undo_log, 'r') as f:
        lines = f.readlines()
        
    recent_ops = lines[-limit:]
    for line in recent_ops:
        try:
            op = json.loads(line.strip())
            timestamp = datetime.fromisoformat(op['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{timestamp} | {op['op_type'].upper()} | {op['source']} → {op['dest']}")
        except (json.JSONDecodeError, KeyError) as e:
            continue

def get_operation_history(limit: int = 10) -> List[Dict]:
    """Get operation history as list of dictionaries."""
    undo_log = _default_undo_log()
    if not undo_log.exists():
        return []
        
    with open(undo_log, 'r') as f:
        lines = f.readlines()
        
    operations = []
    for line in lines[-limit:]:
        try:
            op = json.loads(line.strip())
            operations.append(op)
        except (json.JSONDecodeError, KeyError):
            continue
    
    return operations

def interactive_undo(assume_yes=False, non_interactive=False):
    """Interactive mode to select which operation to undo."""
    operations = get_operation_history(10)
    
    if not operations:
        print("📝 No operation history found.")
        return False
    
    print("📜 Recent operations (most recent first):")
    print("-" * 60)
    
    # Display operations in reverse order (most recent first)
    for i, op in enumerate(reversed(operations), 1):
        timestamp = datetime.fromisoformat(op['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{i:2d}. {timestamp} | {op['op_type'].upper()}")
        print(f"    {op['source']} → {op['dest']}")
    
    if non_interactive:
        if assume_yes:
            # In non-interactive mode with assume_yes, undo the most recent operation
            print("\n🤖 Non-interactive mode: undoing most recent operation")
            selected_op = list(reversed(operations))[0]
            return undo_specific_operation(selected_op, 1)
        else:
            print("\n❌ Cannot run interactive undo in non-interactive mode without --yes")
            return False
    
    print("\n0. Cancel")
    
    while True:
        try:
            choice = input("\nSelect operation to undo (number): ").strip()
            if choice == '0':
                print("🛑 Undo cancelled.")
                return False
            
            operation_num = int(choice)
            if 1 <= operation_num <= len(operations):
                # Convert to index (reverse order)
                selected_op = list(reversed(operations))[operation_num - 1]
                return undo_specific_operation(selected_op, operation_num)
            else:
                print(f"❌ Please enter a number between 1 and {len(operations)}")
                
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n🛑 Undo cancelled.")
            return False

def undo_specific_operation(operation: Dict, operation_num: int = None) -> bool:
    """Undo a specific operation."""
    try:
        op_type = operation['op_type']
        source = Path(operation['source'])
        dest = Path(operation['dest'])
        
        if operation_num:
            print(f"🔄 Undoing operation #{operation_num}: {op_type}")
        print(f"   '{dest}' → '{source}'")
        
        if op_type == 'move':
            if dest.exists():
                # Restore backup if it exists
                backup_path = operation.get('metadata', {}).get('backup_path')
                if backup_path and Path(backup_path).exists():
                    shutil.move(str(dest), str(source))
                    shutil.move(backup_path, str(dest))
                    print(f"✅ Restored original file and moved back '{dest}' → '{source}'")
                else:
                    shutil.move(str(dest), str(source))
                    print(f"✅ Moved back '{dest}' → '{source}'")
            else:
                print(f"❌ Cannot undo: '{dest}' no longer exists.")
                return False
                
        elif op_type == 'copy':
            if dest.exists():
                dest.unlink()
                print(f"✅ Removed copied file '{dest}'")
                
                # Restore backup if it exists
                backup_path = operation.get('metadata', {}).get('backup_path')
                if backup_path and Path(backup_path).exists():
                    shutil.move(backup_path, str(dest))
                    print(f"✅ Restored original file '{dest}'")
            else:
                print(f"❌ Cannot undo: '{dest}' no longer exists.")
                return False
        
        # Remove the operation from log
        remove_operation_from_log(operation)
        return True
        
    except (KeyError, FileNotFoundError) as e:
        print(f"❌ Error undoing operation: {e}")
        return False

def remove_operation_from_log(target_operation: Dict):
    """Remove a specific operation from the undo log."""
    undo_log = _default_undo_log()
    if not undo_log.exists():
        return
        
    with open(undo_log, 'r') as f:
        lines = f.readlines()
    
    # Find and remove the target operation
    remaining_lines = []
    for line in lines:
        try:
            op = json.loads(line.strip())
            # Compare by timestamp and key details
            if (op.get('timestamp') != target_operation.get('timestamp') or
                op.get('source') != target_operation.get('source') or
                op.get('dest') != target_operation.get('dest')):
                remaining_lines.append(line)
        except json.JSONDecodeError:
            remaining_lines.append(line)
    
    with open(undo_log, 'w') as f:
        f.writelines(remaining_lines)

def undo_last_operation():
    """Undo the last operation."""
    operations = get_operation_history(1)
    
    if not operations:
        print("📝 No operations to undo.")
        return False
    
    return undo_specific_operation(operations[-1])

def undo_operation_by_number(operation_num: int):
    """Undo operation by its number in history."""
    operations = get_operation_history(10)
    
    if not operations:
        print("📝 No operation history found.")
        return False
    
    if operation_num < 1 or operation_num > len(operations):
        print(f"❌ Operation number must be between 1 and {len(operations)}")
        return False
    
    # Convert to index (reverse order - most recent first)
    selected_op = list(reversed(operations))[operation_num - 1]
    return undo_specific_operation(selected_op, operation_num)

def verify_operation_success(source: Path, dest: Path, operation_type: str, metadata: Dict[str, Any]) -> bool:
    """Verify that an operation completed successfully."""
    try:
        if operation_type == 'move':
            # For move operations, source should not exist and dest should exist
            if source.exists():
                LOG.error(f"Move operation verification failed: source {source} still exists")
                return False
            if not dest.exists():
                LOG.error(f"Move operation verification failed: destination {dest} does not exist")
                return False
        elif operation_type == 'copy':
            # For copy operations, both source and dest should exist
            if not source.exists():
                LOG.error(f"Copy operation verification failed: source {source} does not exist")
                return False
            if not dest.exists():
                LOG.error(f"Copy operation verification failed: destination {dest} does not exist")
                return False
        
        # Verify checksum if it was recorded
        if metadata.get('checksum_verified') and metadata.get('src_checksum'):
            try:
                current_checksum = _calculate_checksum(dest)
                if current_checksum != metadata['src_checksum']:
                    LOG.error(f"Checksum verification failed: expected {metadata['src_checksum']}, got {current_checksum}")
                    return False
            except Exception as e:
                LOG.warning(f"Could not verify checksum: {e}")
        
        return True
    except Exception as e:
        LOG.error(f"Operation verification failed with exception: {e}")
        return False

def get_file_status_report(file_path: Path) -> Dict[str, Any]:
    """Get comprehensive status report for a file."""
    try:
        path = Path(file_path)
        report = {
            'path': str(path),
            'exists': path.exists(),
            'absolute_path': str(path.resolve()),
        }
        
        if path.exists():
            stat = path.stat()
            report.update({
                'size_bytes': stat.st_size,
                'size_human': f"{stat.st_size / 1024:.1f}KB" if stat.st_size < 1024*1024 else f"{stat.st_size / (1024*1024):.1f}MB",
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:],
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'is_symlink': path.is_symlink(),
            })
            
            # Check if file is locked
            is_locked, lock_info = _is_file_locked(path)
            report['lock_status'] = {
                'is_locked': is_locked,
                'lock_info': lock_info
            }
            
            # Calculate checksum for files
            if path.is_file() and stat.st_size < 100 * 1024 * 1024:  # Skip very large files
                try:
                    report['checksum'] = _calculate_checksum(path)
                except Exception:
                    report['checksum'] = 'Could not calculate'
        
        return report
    except Exception as e:
        return {
            'path': str(file_path),
            'error': str(e),
            'exists': False
        }

def show_operation_diagnostics(source: Path, dest: Path, operation_type: str):
    """Show detailed diagnostics for troubleshooting failed operations."""
    print(f"\n🔍 Operation Diagnostics for {operation_type.upper()}:")
    print("-" * 60)
    
    print(f"Source File Analysis:")
    source_report = get_file_status_report(source)
    for key, value in source_report.items():
        if key != 'path':
            print(f"  {key}: {value}")
    
    print(f"\nDestination Analysis:")
    dest_report = get_file_status_report(dest)
    for key, value in dest_report.items():
        if key != 'path':
            print(f"  {key}: {value}")
    
    # Check parent directory permissions
    if dest.parent.exists():
        parent_stat = dest.parent.stat()
        print(f"\nDestination Directory ({dest.parent}):")
        print(f"  permissions: {oct(parent_stat.st_mode)[-3:]}")
        print(f"  writable: {os.access(dest.parent, os.W_OK)}")
    
    # Environment information
    print(f"\nEnvironment:")
    print(f"  Python version: {sys.version.split()[0]}")
    print(f"  Working directory: {os.getcwd()}")
    print(f"  Available disk space: ", end="")
    try:
        import shutil
        total, used, free = shutil.disk_usage(dest.parent if dest.parent.exists() else Path('.'))
        print(f"{free // (1024**3)}GB free")
    except Exception:
        print("Unknown")

def create_safe_move_parser():
    """Create a clean argument parser for file operations only."""
    # Always use a clean ArgumentParser for file operations to avoid confusing help text
    parser = argparse.ArgumentParser(
        description="Safe file operations with undo capability and atomic moves",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s move file.txt backup/                    # Move file to directory
  %(prog)s copy *.java src/                         # Copy all Java files
  %(prog)s move file.txt newname.txt                # Rename file
  %(prog)s move file.txt dest/ --max-retries 5      # Move with enhanced retry logic
  %(prog)s copy file.txt dest/ --no-verify-checksum # Copy without checksum verification
  %(prog)s move file.txt dest/ --timeout 60         # Move with 60-second timeout
  %(prog)s undo --interactive                       # Interactively undo operations
  %(prog)s undo --interactive --yes                # Undo most recent operation automatically
  %(prog)s undo --non-interactive --yes            # Non-interactive undo (for automation)
  %(prog)s history 5                                # Show last 5 operations
  %(prog)s diagnose file.txt dest.txt               # Show detailed file diagnostics

Environment Variables:
  SAFE_MOVE_MAX_RETRIES              # Default: 3 - Maximum retry attempts for operations
  SAFE_MOVE_RETRY_DELAY              # Default: 0.5 - Initial delay between retries (seconds)
  SAFE_MOVE_TIMEOUT                  # Default: 30 - Operation timeout (seconds)
  SAFE_MOVE_VERIFY_CHECKSUM          # Default: true - Enable checksum verification
  SAFE_MOVE_CHECKSUM_MAX_RETRIES     # Default: 5 - Maximum retry attempts for checksum calculation
  SAFE_MOVE_CHECKSUM_RETRY_DELAY     # Default: 0.2 - Initial delay between checksum retries (seconds)
  SAFE_MOVE_HISTORY                  # Location of operation history file
  SAFE_MOVE_TRASH                    # Location of backup/trash directory
  SAFE_MOVE_ASSUME_YES               # Default: false - Assume yes to all prompts
  SAFE_MOVE_NONINTERACTIVE           # Default: false - Run in non-interactive mode

Enhanced Features:
  • Atomic operations with retry logic and exponential backoff
  • File lock detection with automatic waiting and detailed reporting
  • Checksum verification for data integrity (MD5) with enhanced read-retry logic
  • Configurable timeouts to prevent hanging operations
  • Enhanced error reporting with recovery suggestions
  • Comprehensive operation verification and diagnostics
  • Race condition protection during checksum calculation with separate retry configuration
  • Non-interactive mode support for CI/CD and automation
  • Configuration via .pytoolsrc, environment variables, or command-line flags
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    # --- Move command ---
    parser_move = subparsers.add_parser('move', help='Move one or more files safely', aliases=['mv'])
    parser_move.add_argument('source_files', nargs='+', help='Source file(s) or glob pattern')
    parser_move.add_argument('destination', help='Destination file or directory')
    parser_move.add_argument('--dry-run', action='store_true', help='Preview operations')
    parser_move.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser_move.add_argument('--check-compile', action='store_true', default=True,
                            help='Check syntax/compilation after successful moves (default: enabled)')
    parser_move.add_argument('--no-check-compile', action='store_true',
                            help='Disable compile checking')
    # Enhanced atomic operation options
    parser_move.add_argument('--verify-checksum', action='store_true', default=DEFAULT_CHECKSUM_VERIFY,
                            help=f'Verify file integrity with checksums (default: {DEFAULT_CHECKSUM_VERIFY})')
    parser_move.add_argument('--no-verify-checksum', action='store_true',
                            help='Disable checksum verification')
    parser_move.add_argument('--max-retries', type=int, default=DEFAULT_MAX_RETRIES,
                            help=f'Maximum retry attempts for failed operations (default: {DEFAULT_MAX_RETRIES})')
    parser_move.add_argument('--retry-delay', type=float, default=DEFAULT_RETRY_DELAY,
                            help=f'Initial delay between retries in seconds (default: {DEFAULT_RETRY_DELAY})')
    parser_move.add_argument('--timeout', type=int, default=DEFAULT_OPERATION_TIMEOUT,
                            help=f'Timeout for each operation in seconds (default: {DEFAULT_OPERATION_TIMEOUT})')

    # --- Copy command ---
    parser_copy = subparsers.add_parser('copy', help='Copy one or more files safely', aliases=['cp'])
    parser_copy.add_argument('source_files', nargs='+', help='Source file(s) or glob pattern')
    parser_copy.add_argument('destination', help='Destination file or directory')
    parser_copy.add_argument('--dry-run', action='store_true', help='Preview operations')
    parser_copy.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser_copy.add_argument('--check-compile', action='store_true', default=True,
                            help='Check syntax/compilation after successful copies (default: enabled)')
    parser_copy.add_argument('--no-check-compile', action='store_true',
                            help='Disable compile checking')
    # Enhanced atomic operation options
    parser_copy.add_argument('--verify-checksum', action='store_true', default=DEFAULT_CHECKSUM_VERIFY,
                            help=f'Verify file integrity with checksums (default: {DEFAULT_CHECKSUM_VERIFY})')
    parser_copy.add_argument('--no-verify-checksum', action='store_true',
                            help='Disable checksum verification')
    parser_copy.add_argument('--max-retries', type=int, default=DEFAULT_MAX_RETRIES,
                            help=f'Maximum retry attempts for failed operations (default: {DEFAULT_MAX_RETRIES})')
    parser_copy.add_argument('--retry-delay', type=float, default=DEFAULT_RETRY_DELAY,
                            help=f'Initial delay between retries in seconds (default: {DEFAULT_RETRY_DELAY})')
    parser_copy.add_argument('--timeout', type=int, default=DEFAULT_OPERATION_TIMEOUT,
                            help=f'Timeout for each operation in seconds (default: {DEFAULT_OPERATION_TIMEOUT})')

    # --- Undo command ---
    parser_undo = subparsers.add_parser('undo', help='Undo file operations')
    parser_undo.add_argument('--interactive', action='store_true', 
                           help='Interactive mode to select which operation to undo')
    parser_undo.add_argument('--operation', type=int, 
                           help='Undo specific operation number from history')
    parser_undo.add_argument('--yes', '-y', action='store_true',
                           help='Assume yes to prompts (for non-interactive mode)')
    parser_undo.add_argument('--non-interactive', action='store_true',
                           help='Run in non-interactive mode')

    # --- History command ---
    parser_history = subparsers.add_parser('history', help='Show recent operation history')
    parser_history.add_argument('limit', type=int, nargs='?', default=10, help='Number of entries to show (default: 10)')
    
    # --- Diagnostic command ---
    parser_diag = subparsers.add_parser('diagnose', help='Show detailed diagnostic information for files')
    parser_diag.add_argument('source', help='Source file to analyze')
    parser_diag.add_argument('destination', nargs='?', help='Destination file to analyze (optional)')
    parser_diag.add_argument('--operation-type', choices=['move', 'copy'], default='move',
                           help='Type of operation for diagnostic context (default: move)')
    
    return parser

def main():
    parser = create_safe_move_parser()
    args = parser.parse_args()

    # Load config if available
    config = None
    if HAS_CONFIG:
        config = load_config()

    # Initialize mover for relevant commands
    if args.command in ['move', 'copy']:
        # Handle compile check flags
        check_compile = getattr(args, 'check_compile', True)  # Default to True
        if getattr(args, 'no_check_compile', False):
            check_compile = False
        
        # Handle checksum verification flags
        verify_checksum = getattr(args, 'verify_checksum', DEFAULT_CHECKSUM_VERIFY)
        if getattr(args, 'no_verify_checksum', False):
            verify_checksum = False
        
        # Get non-interactive settings from config or environment
        assume_yes = DEFAULT_ASSUME_YES
        non_interactive = DEFAULT_NONINTERACTIVE
        if HAS_CONFIG and config:
            assume_yes = get_config_value('assume_yes', assume_yes, 'safe_move', config)
            non_interactive = get_config_value('non_interactive', non_interactive, 'safe_move', config)
        
        mover = SafeMover(
            dry_run=args.dry_run, 
            verbose=args.verbose,
            check_compile=check_compile,
            verify_checksum=verify_checksum,
            max_retries=getattr(args, 'max_retries', DEFAULT_MAX_RETRIES),
            retry_delay=getattr(args, 'retry_delay', DEFAULT_RETRY_DELAY),
            operation_timeout=getattr(args, 'timeout', DEFAULT_OPERATION_TIMEOUT),
            assume_yes=assume_yes,
            non_interactive=non_interactive
        )
    
    # Execute command
    if args.command == 'undo':
        # Get non-interactive settings from args, config, or environment
        assume_yes = getattr(args, 'yes', DEFAULT_ASSUME_YES)
        non_interactive = getattr(args, 'non_interactive', DEFAULT_NONINTERACTIVE)
        
        if HAS_CONFIG and config:
            # Override with config values if not specified on command line
            if not hasattr(args, 'yes') or not args.yes:
                assume_yes = get_config_value('assume_yes', assume_yes, 'safe_move', config)
            if not hasattr(args, 'non_interactive') or not args.non_interactive:
                non_interactive = get_config_value('non_interactive', non_interactive, 'safe_move', config)
        
        if args.interactive:
            return 0 if interactive_undo(assume_yes=assume_yes, non_interactive=non_interactive) else 1
        elif args.operation:
            return 0 if undo_operation_by_number(args.operation) else 1
        else:
            return 0 if undo_last_operation() else 1

    elif args.command == 'history':
        show_undo_history(args.limit)
        return 0
    
    elif args.command == 'diagnose':
        source_path = Path(args.source)
        dest_path = Path(args.destination) if args.destination else source_path.with_suffix('.destination')
        show_operation_diagnostics(source_path, dest_path, args.operation_type)
        return 0

    elif args.command in ['move', 'copy']:
        # Pre-flight checks
        if HAS_PREFLIGHT:
            checks = []
            for pattern in args.source_files:
                if not ('*' in pattern or '?' in pattern):
                    checks.append((PreflightChecker.check_file_readable, (pattern,)))
            
            dest_path = Path(args.destination)
            if dest_path.exists() and dest_path.is_dir():
                checks.append((PreflightChecker.check_directory_accessible, (str(dest_path),)))

            if not run_preflight_checks(checks, exit_on_fail=True):
                return 1

        # Resolve sources from glob patterns
        resolved_sources = []
        for pattern in args.source_files:
            matches = [Path(p) for p in glob(pattern)]
            if not matches and not ('*' in pattern or '?' in pattern):
                print(f"❌ Error: Source file '{pattern}' not found.")
                return 1
            resolved_sources.extend(matches)
        
        if not resolved_sources:
            print("❌ Error: No source files matched the pattern(s).")
            return 1
        
        dest = Path(args.destination)
        is_batch = len(resolved_sources) > 1 or dest.is_dir()
        
        if args.command == 'copy':
            success_count = sum(1 for src in resolved_sources if mover.safe_copy(src, dest))
        else: # move
            success_count = sum(1 for src in resolved_sources if mover.safe_move(src, dest))

        if is_batch:
            LOG.info("📊 Summary: %d/%d operations successful", 
                     success_count, len(resolved_sources))
        
        return 0 if success_count == len(resolved_sources) else 1

if __name__ == '__main__':
    sys.exit(main())