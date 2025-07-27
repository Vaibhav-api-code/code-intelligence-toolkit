#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Safe File Manager - A comprehensive, enterprise-grade file management utility.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os

# Import for config loading
try:
    from common_config import apply_config_to_args
except ImportError:
    apply_config_to_args = None
import sys
import json
import shutil
import argparse
import logging
import threading
import time
import hashlib
import errno
import signal
import stat
import subprocess
import tempfile
import zipfile
import tarfile
import mimetypes

# Platform-specific imports
if sys.platform != 'win32':
    try:
        import fcntl
    except ImportError:
        fcntl = None
else:
    fcntl = None
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable, Union, Set, Iterable, Iterable
from glob import glob
from contextlib import contextmanager
from collections import defaultdict, Counter
from functools import wraps, lru_cache
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto

# Import optional dependencies
try:
    import yaml
except ImportError:
    yaml = None

# Cross-process locking
try:
    from fasteners import InterProcessLock
except ImportError:
    InterProcessLock = None  # fallback to threading.Lock

# Import enhanced capabilities from existing tools
try:
    from security_base import SecureFileHandler, validate_path
except ImportError:
    SecureFileHandler = object
    def validate_path(path): return path

# ─────────────────────────── Helper Functions ─────────────────────────────

def _to_path(p: Union[str, Path]) -> Path:
    """Convert string or Path to Path object."""
    return p if isinstance(p, Path) else Path(p)

def _to_paths(items: Union[Iterable[Union[str, Path]], str, Path]) -> List[Path]:
    """Convert iterable of strings/Paths to list of Paths."""
    if isinstance(items, (str, Path)):
        return [_to_path(items)]
    return [_to_path(i) for i in items]

def _sha256(path: Path, chunk: int = 1024*1024) -> str:
    """Calculate SHA256 hash of a file."""
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()

def _fsync_dir(d: Path) -> None:
    """Fsync a directory to ensure metadata changes are persisted."""
    try:
        fd = os.open(str(d), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except Exception:
        pass

# Environment variables for configuration
CONFIG_VARS = {
    'MAX_RETRIES': ('SAFE_FILE_MAX_RETRIES', 3, int),
    'RETRY_DELAY': ('SAFE_FILE_RETRY_DELAY', 0.5, float),
    'OPERATION_TIMEOUT': ('SAFE_FILE_TIMEOUT', 30, int),
    'CHECKSUM_VERIFY': ('SAFE_FILE_VERIFY_CHECKSUM', True, lambda x: x.lower() == 'true'),
    'CHECKSUM_MAX_RETRIES': ('SAFE_FILE_CHECKSUM_MAX_RETRIES', 5, int),
    'CHECKSUM_RETRY_DELAY': ('SAFE_FILE_CHECKSUM_RETRY_DELAY', 0.2, float),
    'CONCURRENT_OPERATIONS': ('SAFE_FILE_CONCURRENT_OPS', 4, int),
    'CHUNK_SIZE': ('SAFE_FILE_CHUNK_SIZE', 4096, int),
    'MAX_HISTORY_SIZE': ('SAFE_FILE_MAX_HISTORY', 1000, int),
    'AUTO_BACKUP': ('SAFE_FILE_AUTO_BACKUP', True, lambda x: x.lower() == 'true'),
    'GIT_AWARE': ('SAFE_FILE_GIT_AWARE', True, lambda x: x.lower() == 'true'),
}

# Load configuration from environment
CONFIG = {}
for key, (env_var, default, converter) in CONFIG_VARS.items():
    value = os.getenv(env_var)
    CONFIG[key] = converter(value) if value else default

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

# Set up logging
LOG = logging.getLogger("safe_file_manager")
LOG_LEVEL = os.getenv("SAFE_FILE_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s"
)

# Operation risk levels
class RiskLevel(Enum):
    SAFE = 1      # No confirmation needed
    LOW = 2       # Simple y/n confirmation
    MEDIUM = 3    # Requires --yes or typed confirmation
    HIGH = 4      # Requires --force or typed phrase
    CRITICAL = 5  # Multiple confirmations required

# Operation types
class OperationType(Enum):
    MOVE = "move"
    COPY = "copy"
    DELETE = "delete"
    TRASH = "trash"
    RENAME = "rename"
    ORGANIZE = "organize"
    SYNC = "sync"
    ARCHIVE = "archive"
    EXTRACT = "extract"
    PERMISSION = "permission"
    LINK = "link"
    MKDIR = "mkdir"
    TOUCH = "touch"
    CREATE = "create"
    VIEW = "view"
    OWNERSHIP = "ownership"
    RMDIR = "rmdir"

@dataclass
class OperationResult:
    """Result of a file operation"""
    success: bool
    operation: OperationType
    source: Path
    destination: Optional[Path] = None
    checksum_verified: bool = False
    checksum: Optional[str] = None
    size: Optional[int] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SafetyCheck:
    """Result of pre-operation safety analysis"""
    is_safe: bool
    risk_level: RiskLevel
    warnings: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    required_space: int = 0
    available_space: int = 0
    permissions_ok: bool = True
    git_status: Optional[Dict[str, Any]] = None

# ─────────────────────────── Core Utilities ───────────────────────────

def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes is None or size_bytes < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def get_file_info(path: Path) -> Dict[str, Any]:
    """Get comprehensive file information."""
    try:
        stat_info = path.stat()
        return {
            'size': stat_info.st_size,
            'mode': stat.filemode(stat_info.st_mode),
            'uid': stat_info.st_uid,
            'gid': stat_info.st_gid,
            'mtime': datetime.fromtimestamp(stat_info.st_mtime),
            'ctime': datetime.fromtimestamp(stat_info.st_ctime),
            'type': 'directory' if path.is_dir() else 'file' if path.is_file() else 'other',
            'mime_type': mimetypes.guess_type(str(path))[0] if path.is_file() else None,
        }
    except Exception as e:
        return {'error': str(e)}

# ─────────────────────────── File Locking ─────────────────────────────

def is_file_locked(file_path: Path) -> Tuple[bool, str]:
    """Check if a file is locked by another process."""
    if not file_path.exists():
        return False, "File does not exist"
    
    if sys.platform == 'win32':
        # Windows-specific lock checking
        try:
            # Try to open the file exclusively
            handle = os.open(str(file_path), os.O_RDWR | os.O_EXCL)
            os.close(handle)
            return False, "File is not locked"
        except OSError as e:
            if e.errno in (errno.EACCES, errno.EPERM):
                return True, f"File is locked (Windows)"
            return False, f"Lock check failed: {e}"
    else:
        # Unix-like systems
        if fcntl is None:
            # fcntl not available, assume file is not locked
            return False, "Lock checking not available on this platform"
        
        try:
            with open(file_path, 'r+b') as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    return False, "File is not locked"
                except IOError as e:
                    if e.errno in (errno.EAGAIN, errno.EACCES):
                        return True, f"File is locked (errno: {e.errno})"
                    return False, f"Lock check failed: {e}"
        except (IOError, OSError) as e:
            return False, f"Cannot check lock status: {e}"

def wait_for_file_unlock(file_path: Path, max_wait: float = 10.0) -> bool:
    """Wait for a file to become unlocked."""
    start_time = time.time()
    check_interval = 0.1
    
    while time.time() - start_time < max_wait:
        is_locked, _ = is_file_locked(file_path)
        if not is_locked:
            return True
        time.sleep(check_interval)
        # Exponential backoff up to 1 second
        check_interval = min(check_interval * 1.5, 1.0)
    
    return False

# ─────────────────────────── Checksum Operations ──────────────────────

def calculate_checksum(file_path: Path, algorithm: str = 'sha256') -> Optional[str]:
    """Calculate file checksum with retry logic."""
    if not file_path.is_file():
        return None
    
    algorithms = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512,
    }
    
    if algorithm not in algorithms:
        algorithm = 'sha256'
    
    hasher = algorithms[algorithm]()
    
    def perform_calculation():
        if not wait_for_file_unlock(file_path, CONFIG['OPERATION_TIMEOUT'] / 3):
            raise FileOperationError(f"File {file_path} is locked")
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(CONFIG['CHUNK_SIZE']):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    try:
        return retry_operation(
            perform_calculation,
            max_retries=CONFIG['CHECKSUM_MAX_RETRIES'],
            retry_delay=CONFIG['CHECKSUM_RETRY_DELAY'],
            operation_name=f"checksum calculation for {file_path}"
        )
    except Exception as e:
        LOG.warning(f"Failed to calculate checksum for {file_path}: {e}")
        return None

# ─────────────────────────── Retry Logic ──────────────────────────────

class FileOperationError(Exception):
    """Base exception for file operations"""
    pass

class ChecksumMismatchError(FileOperationError):
    """Raised when checksums don't match"""
    pass

class InsufficientSpaceError(FileOperationError):
    """Raised when there's not enough disk space"""
    pass

class PermissionError(FileOperationError):
    """Raised when permission is denied"""
    pass

def retry_operation(
    operation: Callable,
    max_retries: int = None,
    retry_delay: float = None,
    operation_name: str = "operation",
    exceptions: Tuple[Exception, ...] = (IOError, OSError, FileOperationError)
) -> Any:
    """Retry an operation with exponential backoff."""
    if max_retries is None:
        max_retries = CONFIG['MAX_RETRIES']
    if retry_delay is None:
        retry_delay = CONFIG['RETRY_DELAY']
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = retry_delay * (2 ** attempt)
                LOG.warning(
                    f"Attempt {attempt + 1} of {operation_name} failed: {e}. "
                    f"Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
            else:
                LOG.error(f"All {max_retries + 1} attempts of {operation_name} failed")
    
    raise last_exception

# ─────────────────────────── Timeout Handler ──────────────────────────

@contextmanager
def timeout_handler(timeout_seconds: int):
    """Context manager for operation timeout."""
    # Check if we're in the main thread
    is_main_thread = threading.current_thread() is threading.main_thread()
    
    if sys.platform == 'win32' or not is_main_thread:
        # Windows or non-main thread: use threading instead
        timer = None
        timed_out = threading.Event()
        
        def timeout_callback():
            timed_out.set()
        
        timer = threading.Timer(timeout_seconds, timeout_callback)
        timer.start()
        
        try:
            yield timed_out
        finally:
            if timer:
                timer.cancel()
    else:
        # Unix-like systems in main thread
        def timeout_signal_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_signal_handler)
        signal.alarm(timeout_seconds)
        
        try:
            yield None
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

# ─────────────────────────── Atomic Operations ────────────────────────

@contextmanager
def atomic_write(file_path: Path, mode: str = 'w', **kwargs):
    """Context manager for atomic file writes."""
    file_path = Path(file_path)
    
    # Create a temporary file in the same directory
    temp_fd, temp_path = tempfile.mkstemp(
        dir=str(file_path.parent),
        prefix=f'.{file_path.name}.',
        suffix='.tmp'
    )
    
    temp_file = None
    try:
        # Open the temporary file
        temp_file = os.fdopen(temp_fd, mode, **kwargs)
        yield temp_file
        temp_file.close()
        temp_file = None
        
        # Get original file permissions if it exists
        if file_path.exists():
            orig_stat = file_path.stat()
            os.chmod(temp_path, orig_stat.st_mode)
        
        # Atomic replace
        Path(temp_path).replace(file_path)
        _fsync_dir(file_path.parent)
        
    except Exception:
        # Clean up on error
        if temp_file:
            temp_file.close()
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

def atomic_file_operation(
    src: Path,
    dst: Path,
    operation: OperationType,
    verify_checksum: bool = None,
    preserve_attrs: bool = True
) -> OperationResult:
    """Perform an atomic file operation."""
    if verify_checksum is None:
        verify_checksum = CONFIG['CHECKSUM_VERIFY']
    
    start_time = time.time()
    src_checksum = None
    
    # Calculate source checksum if needed
    if verify_checksum and src.is_file():
        src_checksum = calculate_checksum(src)
    
    # Get source info
    src_info = get_file_info(src)
    
    def perform_operation():
        # Create parent directory if needed
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate unique temporary name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        tmp = dst.with_name(f'.{dst.name}.tmp_{timestamp}')
        
        try:
            # Perform the operation
            if operation == OperationType.COPY:
                if src.is_dir():
                    shutil.copytree(src, tmp, symlinks=preserve_attrs)
                else:
                    shutil.copy2(src, tmp) if preserve_attrs else shutil.copy(src, tmp)
            
            elif operation == OperationType.MOVE:
                # Try rename first (atomic on same filesystem)
                try:
                    src.rename(tmp)
                except OSError:
                    # Fall back to copy+delete
                    if src.is_dir():
                        shutil.copytree(src, tmp, symlinks=preserve_attrs)
                        shutil.rmtree(src)
                    else:
                        shutil.copy2(src, tmp) if preserve_attrs else shutil.copy(src, tmp)
                        src.unlink()
            
            # Verify checksum if needed
            if verify_checksum and src_checksum and tmp.is_file():
                tmp_checksum = calculate_checksum(tmp)
                if src_checksum != tmp_checksum:
                    raise ChecksumMismatchError(
                        f"Checksum mismatch: source={src_checksum}, temp={tmp_checksum}"
                    )
            
            # Atomic replace
            if dst.exists():
                # Backup existing file to trash
                if CONFIG['AUTO_BACKUP']:
                    backup_to_trash(dst)
            
            tmp.replace(dst)
            
            return OperationResult(
                success=True,
                operation=operation,
                source=src,
                destination=dst,
                checksum_verified=verify_checksum and bool(src_checksum),
                checksum=src_checksum,
                size=src_info.get('size', 0),
                duration=time.time() - start_time,
                metadata=src_info
            )
            
        except Exception as e:
            # Clean up temporary file on error
            if tmp.exists():
                try:
                    if tmp.is_dir():
                        shutil.rmtree(tmp)
                    else:
                        tmp.unlink()
                except OSError:
                    pass
            raise
    
    # Execute with timeout
    with timeout_handler(CONFIG['OPERATION_TIMEOUT']) as timed_out:
        # Check for timeout on platforms/threads that use Event
        if timed_out and timed_out.is_set():
            raise TimeoutError("Operation timed out")
        
        return retry_operation(
            perform_operation,
            operation_name=f"{operation.value} {src} -> {dst}"
        )

# ─────────────────────────── Git Integration ──────────────────────────

def get_git_status(path: Path) -> Optional[Dict[str, Any]]:
    """Get git status for a path."""
    if not CONFIG['GIT_AWARE']:
        return None
    
    try:
        # Find git root
        git_root = path if path.is_dir() else path.parent
        while git_root != git_root.parent:
            if (git_root / '.git').exists():
                break
            git_root = git_root.parent
        else:
            return None
        
        # Get file status
        result = subprocess.run(
            ['git', 'status', '--porcelain', str(path)],
            cwd=str(git_root),
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            status = result.stdout.strip()
            return {
                'git_root': git_root,
                'is_tracked': bool(status),
                'is_modified': 'M' in status,
                'is_staged': status.startswith('M') or status.startswith('A'),
                'status': status
            }
    except Exception as e:
        LOG.debug(f"Git status check failed: {e}")
    
    return None

# ─────────────────────────── Safety Analysis ──────────────────────────

def analyze_safety(
    sources: List[Path],
    destination: Optional[Path],
    operation: OperationType
) -> SafetyCheck:
    """Perform comprehensive safety analysis before operation."""
    warnings = []
    conflicts = []
    risk_level = RiskLevel.LOW
    
    # Normalize sources list
    sources = _to_paths(sources)
    
    # Calculate total size
    total_size = 0
    for src in sources:
        if src.is_file():
            total_size += src.stat().st_size
        elif src.is_dir():
            total_size += sum(f.stat().st_size for f in src.rglob('*') if f.is_file())
    
    # Check permissions
    permissions_ok = True
    for src in sources:
        if not os.access(src, os.R_OK):
            warnings.append(f"No read permission for '{src}'")
            permissions_ok = False
    
    if destination:
        parent = destination.parent if destination.exists() else destination
        if not os.access(parent, os.W_OK):
            warnings.append(f"No write permission for '{parent}'")
            permissions_ok = False
    
    # Check disk space
    available_space = 0
    if destination:
        stat_info = shutil.disk_usage(destination.parent if destination.exists() else Path.cwd())
        available_space = stat_info.free
        
        if operation in [OperationType.COPY, OperationType.MOVE]:
            if total_size > available_space:
                warnings.append(
                    f"Insufficient disk space: need {format_size(total_size)}, "
                    f"have {format_size(available_space)}"
                )
                risk_level = RiskLevel.HIGH
    
    # Check for conflicts
    if destination:
        for src in sources:
            if operation in [OperationType.MOVE, OperationType.COPY]:
                dst_path = destination / src.name if destination.is_dir() else destination
                if dst_path.exists():
                    conflicts.append(f"Destination '{dst_path}' already exists")
                    if RiskLevel.MEDIUM.value > risk_level.value:
                        risk_level = RiskLevel.MEDIUM
    
    # Check git status
    git_status = {}
    if CONFIG['GIT_AWARE']:
        for src in sources:
            status = get_git_status(src)
            if status:
                git_status[str(src)] = status
                if status['is_modified'] and not status['is_staged']:
                    warnings.append(f"'{src}' has unstaged changes in git")
                    if RiskLevel.MEDIUM.value > risk_level.value:
                        risk_level = RiskLevel.MEDIUM
    
    # Adjust risk level based on operation
    if operation in [OperationType.DELETE, OperationType.TRASH]:
        if any(src.is_dir() and list(src.rglob('*')) for src in sources):
            if RiskLevel.HIGH.value > risk_level.value:
                risk_level = RiskLevel.HIGH
    
    if operation == OperationType.PERMISSION:
        risk_level = RiskLevel.HIGH
    
    # Check for special files
    special_patterns = [
        '.git', '.env', 'node_modules', '__pycache__',
        '*.key', '*.pem', '*.crt', 'id_rsa*'
    ]
    for src in sources:
        for pattern in special_patterns:
            if src.match(pattern) or any(src.rglob(pattern)):
                warnings.append(f"'{src}' contains special files matching '{pattern}'")
                if RiskLevel.HIGH.value > risk_level.value:
                    risk_level = RiskLevel.HIGH
    
    return SafetyCheck(
        is_safe=len(warnings) == 0 and len(conflicts) == 0,
        risk_level=risk_level,
        warnings=warnings,
        conflicts=conflicts,
        required_space=total_size,
        available_space=available_space,
        permissions_ok=permissions_ok,
        git_status=git_status if git_status else None
    )

# ─────────────────────────── Manifest System ──────────────────────────

class OperationManifest:
    """Manages operation manifests for bulk operations and recovery."""
    
    def __init__(self, manifest_path: Optional[Path] = None):
        self.manifest_path = manifest_path or self._default_manifest_path()
        self.operations: List[OperationResult] = []
        self.metadata: Dict[str, Any] = {
            'created': datetime.now().isoformat(),
            'version': '1.0',
            'total_operations': 0,
            'completed_operations': 0,
            'failed_operations': 0,
        }
        self._lock = threading.Lock()
        self._load_existing()
    
    def _default_manifest_path(self) -> Path:
        manifest_dir = Path.home() / '.safe_file_manager' / 'manifests'
        manifest_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return manifest_dir / f'manifest_{timestamp}.json'
    
    def _load_existing(self):
        """Load existing manifest if it exists."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r') as f:
                    data = json.load(f)
                    self.metadata = data.get('metadata', self.metadata)
                    self.operations = [
                        OperationResult(**op) for op in data.get('operations', [])
                    ]
            except Exception as e:
                LOG.warning(f"Failed to load manifest: {e}")
    
    def add_operation(self, result: OperationResult):
        """Add an operation result to the manifest."""
        with self._lock:
            self.operations.append(result)
            self.metadata['total_operations'] += 1
            if result.success:
                self.metadata['completed_operations'] += 1
            else:
                self.metadata['failed_operations'] += 1
            self._save()
    
    def _save(self):
        """Save manifest to disk atomically."""
        data = {
            'metadata': self.metadata,
            'operations': [
                {
                    'success': op.success,
                    'operation': op.operation.value,
                    'source': str(op.source),
                    'destination': str(op.destination) if op.destination else None,
                    'checksum_verified': op.checksum_verified,
                    'checksum': op.checksum,
                    'size': op.size,
                    'duration': op.duration,
                    'error': op.error,
                    'metadata': op.metadata,
                }
                for op in self.operations
            ]
        }
        
        with atomic_write(self.manifest_path, 'w') as f:
            json.dump(data, f, indent=2, cls=DateTimeEncoder)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get operation summary."""
        return {
            'total': self.metadata['total_operations'],
            'completed': self.metadata['completed_operations'],
            'failed': self.metadata['failed_operations'],
            'total_size': sum(op.size or 0 for op in self.operations),
            'total_duration': sum(op.duration or 0 for op in self.operations),
            'operations_by_type': Counter(op.operation.value for op in self.operations),
        }

# ─────────────────────────── Trash System ─────────────────────────────

def get_trash_dir() -> Path:
    """Get the trash directory path."""
    trash_dir = Path(os.environ.get(
        "SAFE_FILE_TRASH",
        Path.home() / ".safe_file_manager" / "trash"
    )).expanduser().resolve()
    trash_dir.mkdir(parents=True, exist_ok=True)
    return trash_dir

def backup_to_trash(path: Path) -> Optional[Path]:
    """Backup a file to trash before overwriting."""
    if not path.exists():
        return None
    
    trash_dir = get_trash_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    trash_name = f"{path.name}.{timestamp}"
    trash_path = trash_dir / trash_name
    
    try:
        if path.is_dir():
            shutil.copytree(path, trash_path)
        else:
            shutil.copy2(path, trash_path)
        
        # Save metadata
        metadata = {
            'original_path': str(path),
            'trashed_at': datetime.now().isoformat(),
            'size': path.stat().st_size if path.is_file() else None,
            'info': get_file_info(path),
        }
        
        with atomic_write(trash_path.with_suffix('.meta'), 'w') as f:
            json.dump(metadata, f, indent=2, cls=DateTimeEncoder)
        
        return trash_path
    except Exception as e:
        LOG.warning(f"Failed to backup to trash: {e}")
        return None

# ─────────────────────────── History System ───────────────────────────

class OperationHistory:
    """Manages operation history for undo capabilities."""
    
    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or self._default_history_file()
        self.history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._load_history()
    
    def _default_history_file(self) -> Path:
        history_dir = Path.home() / '.safe_file_manager'
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir / 'operation_history.json'
    
    def _load_history(self):
        """Load operation history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
                    # Trim to max size
                    if len(self.history) > CONFIG['MAX_HISTORY_SIZE']:
                        self.history = self.history[-CONFIG['MAX_HISTORY_SIZE']:]
            except Exception as e:
                LOG.warning(f"Failed to load history: {e}")
    
    def add_operation(
        self,
        operation: OperationType,
        source: Path,
        destination: Optional[Path] = None,
        result: Optional[OperationResult] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add an operation to history."""
        with self._lock:
            entry = {
                'id': len(self.history) + 1,
                'timestamp': datetime.now().isoformat(),
                'operation': operation.value,
                'source': str(source),
                'destination': str(destination) if destination else None,
                'success': result.success if result else True,
                'metadata': metadata or {},
            }
            
            if result:
                entry['checksum'] = result.checksum
                entry['size'] = result.size
                entry['duration'] = result.duration
            
            self.history.append(entry)
            self._save_history()
    
    def _save_history(self):
        """Save history to file atomically."""
        # Trim to max size
        if len(self.history) > CONFIG['MAX_HISTORY_SIZE']:
            self.history = self.history[-CONFIG['MAX_HISTORY_SIZE']:]
        
        with atomic_write(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2, cls=DateTimeEncoder)
    
    def get_recent(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent operations."""
        return self.history[-count:]
    
    def find_operations(
        self,
        operation: Optional[OperationType] = None,
        path: Optional[Path] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Find operations matching criteria."""
        results = []
        
        for entry in self.history:
            # Filter by operation type
            if operation and entry['operation'] != operation.value:
                continue
            
            # Filter by path
            if path:
                path_str = str(path)
                if (entry['source'] != path_str and 
                    entry.get('destination') != path_str):
                    continue
            
            # Filter by time
            if since:
                entry_time = datetime.fromisoformat(entry['timestamp'])
                if entry_time < since:
                    continue
            
            results.append(entry)
        
        return results

# ─────────────────────────── Main Operations ──────────────────────────

class SafeFileManager(SecureFileHandler):
    """Main class for safe file operations."""
    
    def __init__(self, 
                 base_dir=None,
                 trash_dir=None, 
                 journal_dir=None,
                 dry_run: bool = False,
                 paranoid: bool = False,
                 sandbox_roots: Optional[List[Union[str, Path]]] = None,
                 allow_symlinks: bool = False,
                 auto_confirm: bool = False,
                 **kwargs):
        super().__init__() if SecureFileHandler != object else None
        
        # Configuration
        self.base_dir = _to_path(base_dir) if base_dir else Path.cwd()
        self.trash_dir = _to_path(trash_dir) if trash_dir else get_trash_dir()
        self.journal_dir = _to_path(journal_dir) if journal_dir else (Path.home() / '.safe_file_manager' / 'journal')
        
        self.dry_run = dry_run or kwargs.get('dry_run', False)
        self.verbose = kwargs.get('verbose', False)
        self.quiet = kwargs.get('quiet', False)
        self.non_interactive = kwargs.get('non_interactive', False)
        self.assume_yes = kwargs.get('assume_yes', False)
        self.force = kwargs.get('force', False)
        self.verify_checksum = kwargs.get('verify_checksum', CONFIG['CHECKSUM_VERIFY'])
        self.preserve_attrs = kwargs.get('preserve_attrs', True)
        self.follow_symlinks = kwargs.get('follow_symlinks', False)
        
        # Enhanced security features
        self.paranoid = paranoid  # Extra verification
        self.allow_symlinks = allow_symlinks  # Symlink restrictions
        
        # Sandbox roots with default to base_dir
        if sandbox_roots is not None:
            self.sandbox_roots = _to_paths(sandbox_roots)
        else:
            self.sandbox_roots = [self.base_dir]
        
        # Non-interactive mode for CI/tests
        self.auto_confirm = auto_confirm or bool(os.getenv("SFM_ASSUME_YES", ""))
        
        # Systems
        self.history = OperationHistory()
        self.current_manifest = None
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        
        # Cross-process locking
        if InterProcessLock:
            self._lock = InterProcessLock(str(self.journal_dir / '.lock'))
        else:
            self._lock = threading.Lock()
        
        # Thread pool for concurrent operations
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=CONFIG['CONCURRENT_OPERATIONS']
        )
        
        # Recover incomplete transactions on startup
        self._recover_incomplete_transactions()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown(wait=True)
    
    def _recover_incomplete_transactions(self):
        """Recover incomplete transactions from journal on startup."""
        if not self.journal_dir.exists():
            return
        
        # Look for transaction files
        recovered = 0
        for journal_file in self.journal_dir.glob("txn_*.json"):
            try:
                with open(journal_file, 'r') as f:
                    txn_data = json.load(f)
                
                # Check transaction status
                status = txn_data.get('status', 'unknown')
                if status == 'started':
                    # Mark as aborted since it wasn't completed
                    txn_data['status'] = 'aborted'
                    txn_data['aborted_at'] = datetime.now().isoformat()
                    txn_data['abort_reason'] = 'Incomplete transaction found on startup'
                    
                    # Write back the updated status
                    with open(journal_file, 'w') as f:
                        json.dump(txn_data, f, indent=2)
                    
                    recovered += 1
                    
                    # Log the recovery
                    self._print(
                        f"Marked incomplete transaction as aborted: {txn_data.get('id', 'unknown')} "
                        f"({txn_data.get('operation', 'unknown')} operation)",
                        'warning'
                    )
                
            except Exception as e:
                self._print(f"Error recovering transaction from {journal_file}: {e}", 'error')
        
        if recovered > 0:
            self._print(f"Recovered {recovered} incomplete transaction(s)", 'info')
    
    def _print(self, message: str, level: str = 'info'):
        """Print message based on verbosity settings."""
        if self.quiet and level != 'error':
            return
        
        if level == 'error':
            print(f"❌ {message}", file=sys.stderr)
        elif level == 'warning':
            print(f"⚠️  {message}")
        elif level == 'success':
            print(f"✅ {message}")
        elif level == 'info' and not self.quiet:
            print(f"ℹ️  {message}")
        elif level == 'verbose' and self.verbose:
            print(f"🔍 {message}")
    
    def _get_confirmation(
        self,
        prompt: str,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        typed_response: Optional[str] = None
    ) -> bool:
        """Get user confirmation based on risk level."""
        # Check auto_confirm first
        if self.auto_confirm or os.getenv("SFM_ASSUME_YES") == "1":
            return True
            
        if self.non_interactive:
            # Non-interactive mode logic
            if risk_level.value >= RiskLevel.HIGH.value and not self.force:
                self._print(
                    f"High-risk operation requires --force flag in non-interactive mode",
                    'error'
                )
                return False
            elif risk_level.value >= RiskLevel.MEDIUM.value and not self.assume_yes and not self.force:
                self._print(
                    f"Medium-risk operation requires --yes flag in non-interactive mode",
                    'error'
                )
                return False
            else:
                self._print(f"Auto-confirming: {prompt} [yes]", 'verbose')
                return True
        
        # Interactive mode
        if risk_level.value == RiskLevel.SAFE.value:
            return True
        elif risk_level.value == RiskLevel.LOW.value:
            response = input(f"{prompt} [Y/n]: ").strip().lower()
            return response in ['', 'y', 'yes']
        elif risk_level.value == RiskLevel.MEDIUM.value:
            if typed_response:
                response = input(f"{prompt}\nType '{typed_response}' to confirm: ").strip()
                return response == typed_response
            else:
                response = input(f"{prompt} [y/N]: ").strip().lower()
                return response in ['y', 'yes']
        elif risk_level.value >= RiskLevel.HIGH.value:
            if not typed_response:
                typed_response = "CONFIRM"
            response = input(
                f"⚠️  HIGH RISK OPERATION ⚠️\n{prompt}\n"
                f"Type '{typed_response}' to confirm: "
            ).strip()
            return response == typed_response
    
    def _execute_operation(
        self,
        operation_func: Callable,
        sources: List[Path],
        destination: Optional[Path] = None,
        operation_type: OperationType = OperationType.MOVE,
        manifest: Optional[OperationManifest] = None
    ) -> List[OperationResult]:
        """Execute file operations with safety checks."""
        # Safety analysis
        safety = analyze_safety(sources, destination, operation_type)
        
        # Show warnings
        if safety.warnings:
            self._print("Safety warnings:", 'warning')
            for warning in safety.warnings:
                self._print(f"  - {warning}", 'warning')
        
        if safety.conflicts:
            self._print("Conflicts detected:", 'warning')
            for conflict in safety.conflicts:
                self._print(f"  - {conflict}", 'warning')
        
        # Get confirmation
        total_size = sum(
            src.stat().st_size if src.is_file() else 
            sum(f.stat().st_size for f in src.rglob('*') if f.is_file())
            for src in sources
        )
        
        prompt = (
            f"Perform {operation_type.value} operation on {len(sources)} item(s) "
            f"({format_size(total_size)})?"
        )
        
        if not self._get_confirmation(prompt, safety.risk_level):
            self._print("Operation cancelled", 'info')
            return []
        
        # Dry run mode
        if self.dry_run:
            self._print(f"[DRY RUN] Would perform {operation_type.value} operation", 'info')
            for src in sources:
                if destination:
                    self._print(f"  {src} -> {destination}", 'verbose')
                else:
                    self._print(f"  {src}", 'verbose')
            return []
        
        # Execute operations
        results = []
        if len(sources) > 1 and CONFIG['CONCURRENT_OPERATIONS'] > 1:
            # Concurrent execution for multiple files
            futures = []
            for src in sources:
                future = self.executor.submit(operation_func, src, destination)
                futures.append((src, future))
            
            for src, future in futures:
                try:
                    result = future.result(timeout=CONFIG['OPERATION_TIMEOUT'])
                    results.append(result)
                    if manifest:
                        manifest.add_operation(result)
                    self._print(
                        f"{operation_type.value.capitalize()}d: {src}",
                        'success' if result.success else 'error'
                    )
                except Exception as e:
                    result = OperationResult(
                        success=False,
                        operation=operation_type,
                        source=src,
                        destination=destination,
                        error=str(e)
                    )
                    results.append(result)
                    if manifest:
                        manifest.add_operation(result)
                    self._print(f"Failed: {src} - {e}", 'error')
        else:
            # Sequential execution
            for src in sources:
                try:
                    result = operation_func(src, destination)
                    results.append(result)
                    if manifest:
                        manifest.add_operation(result)
                    self._print(
                        f"{operation_type.value.capitalize()}d: {src}",
                        'success' if result.success else 'error'
                    )
                except Exception as e:
                    result = OperationResult(
                        success=False,
                        operation=operation_type,
                        source=src,
                        destination=destination,
                        error=str(e)
                    )
                    results.append(result)
                    if manifest:
                        manifest.add_operation(result)
                    self._print(f"Failed: {src} - {e}", 'error')
        
        # Add to history
        for result in results:
            self.history.add_operation(
                operation_type,
                result.source,
                result.destination,
                result
            )
        
        return results
    
    # ─────────────────────── Test-Compatible Methods ─────────────────────
    
    def _start_record(self, op_type, targets, meta):
        """Test-compatible wrapper for _start_transaction."""
        # Convert string op_type to OperationType if needed
        if isinstance(op_type, str):
            op_type = OperationType.CREATE  # Default for test compatibility
        return self._start_transaction(op_type, targets, meta)
    
    def _finalize_record(self, rec, status, error=None):
        """Test-compatible wrapper for commit/abort transaction."""
        if status == "committed":
            self._commit_transaction(rec)
        else:
            # Create a dummy exception for abort
            exc = Exception(error) if error else Exception("Transaction aborted")
            self._abort_transaction(rec, exc)
    
    def _simple_delete(self, sources, to_trash: bool = True, recursive: bool = False, secure: bool = False):
        """Simplified delete for test compatibility."""
        sources = _to_paths(sources)
        results = []
        for src in sources:
            p = self._assert_safe_path(src)
            with self.transaction("DELETE", [p], {"to_trash": to_trash, "recursive": recursive, "secure": secure}):
                if self.dry_run:
                    results.append(True)
                    continue
                if to_trash:
                    self._move_to_trash(p)
                else:
                    import shutil
                    if p.is_dir() and recursive:
                        shutil.rmtree(p)
                    else:
                        try:
                            p.unlink()
                        except IsADirectoryError:
                            if recursive:
                                shutil.rmtree(p)
                            else:
                                raise
                results.append(True)
        return results
    
    # ─────────────────────── Test-Compatible Simple Methods ─────────────────────
    
    def _simple_copy(self, sources, destination, overwrite: bool = False):
        """Simplified copy for test compatibility."""
        sources = _to_paths(sources)
        destination = _to_path(destination)
        with self.transaction("COPY", [destination], {"overwrite": overwrite, "count": len(sources)}):
            if self.dry_run:
                return True
            for src in sources:
                src = self._assert_safe_path(src)
                dst = destination / src.name if (destination.is_dir() or len(sources) > 1) else destination
                self._atomic_copy(src, dst, overwrite=overwrite)
        return True
    
    def _simple_move(self, sources, destination, overwrite: bool = False):
        """Simplified move for test compatibility."""
        sources = _to_paths(sources) 
        destination = _to_path(destination)
        with self.transaction("MOVE", [destination], {"overwrite": overwrite, "count": len(sources)}):
            if self.dry_run:
                return True
            for src in sources:
                src = self._assert_safe_path(src)
                dst = destination / src.name if (destination.is_dir() or len(sources) > 1) else destination
                try:
                    os.replace(str(src), str(dst))
                except OSError:
                    self._atomic_copy(src, dst, overwrite=overwrite)
                    src.unlink()
                _fsync_dir(dst.parent)
        return True
    
    # ─────────────────────── Enterprise Helper Methods ─────────────────────
    
    def _move_to_trash(self, src: Path) -> Path:
        """Atomically move a file/dir to trash avoiding name collisions."""
        dst = self.trash_dir / src.name
        if dst.exists():
            import uuid
            dst = self.trash_dir / f"{src.name}.{uuid.uuid4().hex}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(src), str(dst))
        _fsync_dir(dst.parent)
        
        # Save metadata
        metadata = {
            'original_path': str(src),
            'original_name': src.name,
            'trashed_at': datetime.now().isoformat(),
            'size': src.stat().st_size if src.is_file() else None
        }
        meta_path = dst.with_suffix(dst.suffix + '.meta')
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return dst
    
    def _assert_safe_path(self, path: Union[str, Path]) -> Path:
        """Assert that path is within allowed sandbox roots and handle symlinks safely."""
        p = _to_path(path)
        
        # Check symlinks BEFORE resolving
        if not self.allow_symlinks and p.exists() and p.is_symlink():
            raise PermissionError(f"Symlink operation blocked: {p}")
        
        # Allow if sandbox list empty (defensive)
        if self.sandbox_roots:
            real = p.resolve(strict=False)
            if not any(str(real).startswith(str(r.resolve())) for r in self.sandbox_roots):
                raise PermissionError(f"Path {p} escapes sandbox roots {self.sandbox_roots}")
        
        return p
    
    def _write_journal(self, record: Dict[str, Any]) -> None:
        """Write journal entry atomically with fsync and locking."""
        path = self.journal_dir / f"{record['id']}.json"
        tmp = path.with_suffix(".tmp")
        data = json.dumps(record, cls=DateTimeEncoder, indent=2)
        
        # Use lock only during the critical section
        with self._lock:
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
            _fsync_dir(path.parent)
    
    @contextmanager
    def transaction(self, op_type: Union[str, OperationType], targets: List[Path], meta: Dict[str, Any] = None):
        """Context manager for atomic operations with journaling."""
        # Support test-style usage with string op_type
        if isinstance(op_type, str):
            rec = self._start_record(op_type, targets, meta or {})
            try:
                yield
            except BaseException as exc:
                self._finalize_record(rec, "aborted", repr(exc))
                raise
            else:
                self._finalize_record(rec, "committed")
        else:
            # Standard usage with OperationType
            rec = self._start_transaction(op_type, targets, meta or {})
            try:
                yield rec
            except BaseException as exc:
                self._abort_transaction(rec, exc)
                raise
            else:
                self._commit_transaction(rec)
    
    def _verify_checksum(self, path: Path, expected: str, algorithm: str = 'sha256') -> bool:
        """Verify file checksum with retries."""
        if not self.paranoid and not self.verify_checksum:
            return True
        
        actual = calculate_checksum(path, algorithm)
        if actual != expected:
            if self.paranoid:
                # Try multiple times in paranoid mode
                for _ in range(3):
                    time.sleep(0.1)
                    actual = calculate_checksum(path, algorithm)
                    if actual == expected:
                        return True
                raise ChecksumMismatchError(f"Checksum verification failed after 3 attempts")
            else:
                LOG.warning(f"Checksum mismatch for {path}")
                return False
        return True
    
    def _perform_atomic_write(self, content: Union[str, bytes], destination: Path, 
                             mode: str = 'w', rollback_tracker=None) -> Path:
        """Perform atomic write with rollback tracking."""
        backup_path = None
        
        # Backup existing file
        if destination.exists():
            backup_path = destination.with_suffix(f'.backup.{uuid.uuid4().hex[:8]}')
            shutil.copy2(destination, backup_path)
            if rollback_tracker:
                rollback_tracker.add({
                    'type': 'restore',
                    'path': str(destination),
                    'backup': str(backup_path)
                })
        
        # Write atomically
        with atomic_write(destination, mode) as f:
            f.write(content)
        
        # Ensure written data is persisted
        os.fsync(destination.open().fileno())
        
        # Also fsync the directory
        os.fsync(destination.parent.open().fileno())
        
        # Clean up backup on success
        if backup_path:
            backup_path.unlink()
        
        return destination
    
    def _handle_safety_check(self, safety: SafetyCheck, operation: str) -> bool:
        """Handle safety check results and get user confirmation."""
        if self.dry_run:
            return True
        
        if not safety.safe:
            self._print(f"Safety check failed for {operation}:", 'error')
            for warning in safety.warnings:
                self._print(f"  - {warning}", 'warning')
            return False
        
        # Print warnings
        for warning in safety.warnings:
            self._print(warning, 'warning')
        
        # Get confirmation based on risk level
        if safety.risk_level.value >= RiskLevel.CRITICAL.value:
            prompt = f"This is a CRITICAL operation. Type 'DELETE ALL DATA' to proceed"
            return self._get_confirmation(prompt, safety.risk_level, "DELETE ALL DATA")
        elif safety.risk_level.value >= RiskLevel.HIGH.value:
            prompt = f"High-risk {operation} operation. Type 'PROCEED' to continue"
            return self._get_confirmation(prompt, safety.risk_level, "PROCEED")
        elif safety.risk_level.value >= RiskLevel.MEDIUM.value:
            return self._get_confirmation(
                f"Proceed with {operation} operation?",
                safety.risk_level
            )
        
        return True
    
    # ─────────────────────── Core Operations ───────────────────────────
    
    def move(self, sources: Union[Iterable[Union[str, Path]], str, Path], destination: Union[str, Path]) -> List[OperationResult]:
        """Move files or directories."""
        # Normalize inputs
        sources = _to_paths(sources)
        destination = _to_path(destination)
        
        def move_single(src: Path, dst: Path) -> OperationResult:
            final_dst = dst / src.name if dst.is_dir() else dst
            return atomic_file_operation(src, final_dst, OperationType.MOVE, self.verify_checksum)
        
        return self._execute_operation(
            move_single,
            sources,
            destination,
            OperationType.MOVE
        )
    
    def copy(self, sources: Union[Iterable[Union[str, Path]], str, Path], destination: Union[str, Path], overwrite: bool = False) -> List[OperationResult]:
        """
        Copy sources -> destination.
        - sources: Path or list of Paths
        - destination: Path
        - overwrite: allow replacing existing destination file(s)
        """
        # Normalize inputs
        sources = _to_paths(sources)
        destination = _to_path(destination)
        
        def copy_single(src: Path, dst: Path) -> OperationResult:
            final_dst = dst / src.name if dst.is_dir() else dst
            try:
                # Use _atomic_copy which handles overwrite parameter
                self._atomic_copy(src, final_dst, overwrite=overwrite)
                
                # Get file info for the result
                src_info = get_file_info(src)
                src_checksum = calculate_checksum(src) if self.verify_checksum and src.is_file() else None
                
                return OperationResult(
                    success=True,
                    operation=OperationType.COPY,
                    source=src,
                    destination=final_dst,
                    checksum_verified=self.verify_checksum and bool(src_checksum),
                    checksum=src_checksum,
                    size=src_info.get('size', 0),
                    duration=0,  # Will be updated by _execute_operation
                    metadata=src_info
                )
            except Exception as e:
                return OperationResult(
                    success=False,
                    operation=OperationType.COPY,
                    source=src,
                    destination=final_dst,
                    error=str(e)
                )
        
        return self._execute_operation(
            copy_single,
            sources,
            destination,
            OperationType.COPY
        )
    
    def trash(self, sources: Union[str, Path, List[Union[str, Path]]]) -> List[OperationResult]:
        """Move files to trash."""
        # Normalize inputs
        if isinstance(sources, (str, Path)):
            sources = [sources]
        sources = _to_paths(sources)
        
        trash_dir = get_trash_dir()
        
        def trash_single(src: Path, _: Optional[Path]) -> OperationResult:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            trash_name = f"{src.name}.{timestamp}"
            trash_path = trash_dir / trash_name
            
            # Move to trash
            result = atomic_file_operation(src, trash_path, OperationType.MOVE, False)
            
            # Save metadata
            metadata = {
                'original_path': str(src),
                'trashed_at': datetime.now().isoformat(),
                'git_status': get_git_status(src),
            }
            
            with atomic_write(trash_path.with_suffix('.meta'), 'w') as f:
                json.dump(metadata, f, indent=2, cls=DateTimeEncoder)
            
            return result
        
        return self._execute_operation(
            trash_single,
            sources,
            None,
            OperationType.TRASH
        )
    
    def delete(self, sources,
               to_trash: bool = True,
               recursive: bool = False,
               secure: bool = False):
        """Backwards compatible delete: move to trash by default."""
        sources = _to_paths(sources)
        results = []
        for src in sources:
            src = self._assert_safe_path(src)
            with self.transaction(OperationType.DELETE,
                                  [src], {"to_trash": to_trash, "recursive": recursive, "secure": secure}):
                if self.dry_run:
                    results.append(OperationResult(
                        success=True,
                        operation=OperationType.DELETE,
                        source=src,
                        dry_run=True
                    ))
                    continue
                if to_trash:
                    trash_path = self._move_to_trash(src)
                    results.append(OperationResult(
                        success=True,
                        operation=OperationType.TRASH,
                        source=src,
                        destination=trash_path,
                        metadata={'unique_name': trash_path.name}
                    ))
                else:
                    # secure or normal delete
                    if src.is_dir() and recursive:
                        shutil.rmtree(src)
                    else:
                        try:
                            src.unlink()
                        except IsADirectoryError:
                            if recursive:
                                shutil.rmtree(src)
                            else:
                                raise
                    results.append(OperationResult(
                        success=True,
                        operation=OperationType.DELETE,
                        source=src
                    ))
        return results
    
    def organize(
        self,
        source_dir: Path,
        organization_type: str = 'extension',
        custom_rules: Optional[Path] = None
    ) -> List[OperationResult]:
        """Organize files in a directory based on rules."""
        manifest = OperationManifest()
        
        # Load custom rules if provided
        rules = {}
        if custom_rules and custom_rules.exists():
            with open(custom_rules, 'r') as f:
                if custom_rules.suffix == '.yaml':
                    if yaml:
                        rules = yaml.safe_load(f)
                    else:
                        self._print("YAML support not available. Please use JSON format.", 'error')
                        return []
                else:
                    rules = json.load(f)
        
        # Collect files to organize
        files_to_organize = []
        for item in source_dir.iterdir():
            if item.is_file():
                files_to_organize.append(item)
        
        self._print(f"Found {len(files_to_organize)} files to organize", 'info')
        
        # Organize based on type
        results = []
        for file_path in files_to_organize:
            try:
                if organization_type == 'extension':
                    # Organize by file extension
                    ext = file_path.suffix[1:] if file_path.suffix else 'no_extension'
                    dest_dir = source_dir / ext
                    
                elif organization_type == 'date':
                    # Organize by modification date
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    dest_dir = source_dir / mtime.strftime('%Y') / mtime.strftime('%m')
                    
                elif organization_type == 'size':
                    # Organize by file size
                    size = file_path.stat().st_size
                    if size < 1024 * 1024:  # < 1MB
                        dest_dir = source_dir / 'small'
                    elif size < 100 * 1024 * 1024:  # < 100MB
                        dest_dir = source_dir / 'medium'
                    else:
                        dest_dir = source_dir / 'large'
                
                elif organization_type == 'mime':
                    # Organize by MIME type
                    mime_type = mimetypes.guess_type(str(file_path))[0] or 'unknown'
                    mime_category = mime_type.split('/')[0] if '/' in mime_type else 'unknown'
                    dest_dir = source_dir / mime_category
                
                elif organization_type == 'custom' and rules:
                    # Organize based on custom rules
                    dest_dir = source_dir / 'other'  # Default
                    for pattern, destination in rules.items():
                        if file_path.match(pattern):
                            dest_dir = source_dir / destination
                            break
                else:
                    continue
                
                # Create destination directory
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                # Move file
                result = atomic_operation(
                    file_path,
                    dest_dir / file_path.name,
                    OperationType.MOVE,
                    False
                )
                results.append(result)
                manifest.add_operation(result)
                
                self._print(
                    f"Organized: {file_path.name} -> {dest_dir.name}/",
                    'success' if result.success else 'error'
                )
                
            except Exception as e:
                result = OperationResult(
                    success=False,
                    operation=OperationType.ORGANIZE,
                    source=file_path,
                    error=str(e)
                )
                results.append(result)
                manifest.add_operation(result)
                self._print(f"Failed to organize {file_path.name}: {e}", 'error')
        
        # Show summary
        summary = manifest.get_summary()
        self._print(
            f"\nOrganization complete: {summary['completed']} succeeded, "
            f"{summary['failed']} failed",
            'info'
        )
        
        return results
    
    def sync(
        self,
        source: Path,
        destination: Path,
        delete: bool = False,
        exclude: Optional[List[str]] = None
    ) -> List[OperationResult]:
        """Sync source directory to destination (like rsync)."""
        manifest = OperationManifest()
        results = []
        
        # Build exclusion set
        exclude_patterns = set(exclude or [])
        
        # Collect all source files
        source_files = {}
        for file_path in source.rglob('*'):
            if file_path.is_file():
                # Check exclusions
                if any(file_path.match(pattern) for pattern in exclude_patterns):
                    continue
                
                rel_path = file_path.relative_to(source)
                source_files[rel_path] = file_path
        
        # Sync files
        for rel_path, src_file in source_files.items():
            dst_file = destination / rel_path
            
            try:
                # Check if sync needed
                sync_needed = False
                if not dst_file.exists():
                    sync_needed = True
                else:
                    # Compare modification times and sizes
                    src_stat = src_file.stat()
                    dst_stat = dst_file.stat()
                    
                    if (src_stat.st_mtime > dst_stat.st_mtime or
                        src_stat.st_size != dst_stat.st_size):
                        sync_needed = True
                
                if sync_needed:
                    result = atomic_operation(
                        src_file,
                        dst_file,
                        OperationType.COPY,
                        self.verify_checksum
                    )
                    results.append(result)
                    manifest.add_operation(result)
                    self._print(f"Synced: {rel_path}", 'success')
                
            except Exception as e:
                result = OperationResult(
                    success=False,
                    operation=OperationType.SYNC,
                    source=src_file,
                    destination=dst_file,
                    error=str(e)
                )
                results.append(result)
                manifest.add_operation(result)
                self._print(f"Failed to sync {rel_path}: {e}", 'error')
        
        # Delete extra files if requested
        if delete:
            dst_files = set()
            for file_path in destination.rglob('*'):
                if file_path.is_file():
                    if any(file_path.match(pattern) for pattern in exclude_patterns):
                        continue
                    dst_files.add(file_path.relative_to(destination))
            
            extra_files = dst_files - set(source_files.keys())
            
            if extra_files and self._get_confirmation(
                f"Delete {len(extra_files)} extra files in destination?",
                RiskLevel.HIGH
            ):
                for rel_path in extra_files:
                    dst_file = destination / rel_path
                    try:
                        dst_file.unlink()
                        self._print(f"Deleted extra: {rel_path}", 'info')
                    except Exception as e:
                        self._print(f"Failed to delete {rel_path}: {e}", 'error')
        
        # Show summary
        summary = manifest.get_summary()
        self._print(
            f"\nSync complete: {summary['completed']} files synced, "
            f"{summary['failed']} failed",
            'info'
        )
        
        return results
    
    def restore_from_trash(self, pattern: Optional[str] = None) -> bool:
        """Restore files from trash."""
        trash_dir = get_trash_dir()
        
        # Find items in trash
        items = []
        for item in trash_dir.iterdir():
            if item.suffix == '.meta':
                continue
            
            # Load metadata
            meta_file = item.with_suffix('.meta')
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                # Filter by pattern if provided
                if pattern and pattern not in str(item.name):
                    continue
                
                items.append((item, metadata))
        
        if not items:
            self._print("No items found in trash", 'info')
            return False
        
        # Sort by trash time (newest first)
        items.sort(key=lambda x: x[1]['trashed_at'], reverse=True)
        
        # Show items
        self._print("Items in trash:", 'info')
        for i, (item, metadata) in enumerate(items):
            orig_path = metadata['original_path']
            trashed_at = metadata['trashed_at']
            size = format_size(metadata.get('size', 0))
            self._print(f"{i+1:3d}. {item.name} (from {orig_path}, {size}, {trashed_at})", 'info')
        
        # Get selection
        if self.non_interactive:
            self._print("Cannot restore interactively in non-interactive mode", 'error')
            return False
        
        try:
            choice = input("Enter number to restore (0 to cancel): ").strip()
            if choice == '0':
                return False
            
            index = int(choice) - 1
            if 0 <= index < len(items):
                item, metadata = items[index]
                orig_path = Path(metadata['original_path'])
                
                # Restore to original location or current directory
                if orig_path.parent.exists():
                    restore_path = orig_path
                else:
                    restore_path = Path.cwd() / orig_path.name
                    self._print(
                        f"Original directory doesn't exist, restoring to {restore_path}",
                        'warning'
                    )
                
                # Perform restore
                result = atomic_operation(
                    item,
                    restore_path,
                    OperationType.MOVE,
                    False
                )
                
                if result.success:
                    # Remove metadata file
                    meta_file = item.with_suffix('.meta')
                    if meta_file.exists():
                        meta_file.unlink()
                    
                    self._print(f"Restored: {restore_path}", 'success')
                    return True
                else:
                    self._print(f"Failed to restore: {result.error}", 'error')
                    return False
            
        except (ValueError, IndexError):
            self._print("Invalid selection", 'error')
            return False
    
    def list_directory(
        self,
        path: Path,
        long_format: bool = False,
        all_files: bool = False,
        human_readable: bool = True,
        sort_by: str = 'name'
    ):
        """List directory contents (safe replacement for ls)."""
        if not path.exists():
            self._print(f"Path does not exist: {path}", 'error')
            return
        
        if not path.is_dir():
            # List single file
            if long_format:
                info = get_file_info(path)
                if 'error' in info:
                    self._print(f"Error getting info for {path.name}: {info['error']}", 'error')
                else:
                    self._print(
                        f"{info['mode']} {format_size(info['size'])} "
                        f"{info['mtime'].strftime('%Y-%m-%d %H:%M')} {path.name}",
                        'info'
                    )
            else:
                self._print(str(path), 'info')
            return
        
        # List directory contents
        items = list(path.iterdir())
        
        # Filter hidden files
        if not all_files:
            items = [item for item in items if not item.name.startswith('.')]
        
        # Sort items
        if sort_by == 'name':
            items.sort(key=lambda x: x.name.lower())
        elif sort_by == 'size':
            items.sort(key=lambda x: x.stat().st_size if x.is_file() else 0, reverse=True)
        elif sort_by == 'time':
            items.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        elif sort_by == 'extension':
            items.sort(key=lambda x: (x.suffix.lower(), x.name.lower()))
        
        # Display items
        if long_format:
            total_size = 0
            for item in items:
                info = get_file_info(item)
                size = info.get('size', 0)
                if item.is_file():
                    total_size += size
                
                if 'error' in info:
                    self._print(f"Error getting info for {item.name}: {info['error']}", 'error')
                    continue
                
                size_str = format_size(size) if human_readable else str(size)
                type_indicator = '/' if item.is_dir() else '@' if item.is_symlink() else ''
                
                # Check git status
                git_indicator = ''
                if CONFIG['GIT_AWARE']:
                    git_status = get_git_status(item)
                    if git_status:
                        if git_status['is_modified']:
                            git_indicator = 'M'
                        elif not git_status['is_tracked']:
                            git_indicator = '?'
                
                self._print(
                    f"{info['mode']} {size_str:>9} "
                    f"{info['mtime'].strftime('%Y-%m-%d %H:%M')} "
                    f"{git_indicator:1} {item.name}{type_indicator}",
                    'info'
                )
            
            self._print(f"\nTotal: {format_size(total_size)}", 'info')
        else:
            # Simple listing
            for item in items:
                type_indicator = '/' if item.is_dir() else '@' if item.is_symlink() else ''
                self._print(f"{item.name}{type_indicator}", 'info')
    
    def mkdir(self, directories: List[Path], parents: bool = False, mode: int = 0o755) -> List[OperationResult]:
        """Create directories safely."""
        results = []
        
        for directory in directories:
            try:
                if directory.exists():
                    if directory.is_dir():
                        self._print(f"Directory already exists: {directory}", 'warning')
                        results.append(OperationResult(
                            success=True,
                            operation=OperationType.MKDIR,
                            source=directory,
                            metadata={'already_existed': True}
                        ))
                        continue
                    else:
                        raise FileOperationError(f"Path exists but is not a directory: {directory}")
                
                if self.dry_run:
                    self._print(f"[DRY RUN] Would create directory: {directory}", 'info')
                    results.append(OperationResult(
                        success=True,
                        operation=OperationType.MKDIR,
                        source=directory,
                        metadata={'dry_run': True}
                    ))
                    continue
                
                # Create directory
                directory.mkdir(parents=parents, mode=mode, exist_ok=True)
                
                # Log operation
                result = OperationResult(
                    success=True,
                    operation=OperationType.MKDIR,
                    source=directory,
                    metadata={'mode': oct(mode), 'parents': parents}
                )
                results.append(result)
                self.history.add_operation(OperationType.MKDIR, directory, result=result)
                self._print(f"Created directory: {directory}", 'success')
                
            except Exception as e:
                result = OperationResult(
                    success=False,
                    operation=OperationType.MKDIR,
                    source=directory,
                    error=str(e)
                )
                results.append(result)
                self._print(f"Failed to create directory {directory}: {e}", 'error')
        
        return results
    
    def touch(self, files: List[Path], no_create: bool = False) -> List[OperationResult]:
        """Create empty files or update timestamps."""
        results = []
        
        for file_path in files:
            try:
                exists = file_path.exists()
                
                if self.dry_run:
                    action = "update timestamp of" if exists else "create"
                    self._print(f"[DRY RUN] Would {action}: {file_path}", 'info')
                    results.append(OperationResult(
                        success=True,
                        operation=OperationType.TOUCH,
                        source=file_path,
                        metadata={'dry_run': True, 'existed': exists}
                    ))
                    continue
                
                if no_create and not exists:
                    self._print(f"File does not exist (no-create mode): {file_path}", 'warning')
                    continue
                
                # Create parent directory if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Touch the file
                file_path.touch(exist_ok=True)
                
                # Log operation
                result = OperationResult(
                    success=True,
                    operation=OperationType.TOUCH,
                    source=file_path,
                    metadata={'existed': exists, 'no_create': no_create}
                )
                results.append(result)
                self.history.add_operation(OperationType.TOUCH, file_path, result=result)
                
                action = "Updated timestamp" if exists else "Created file"
                self._print(f"{action}: {file_path}", 'success')
                
            except Exception as e:
                result = OperationResult(
                    success=False,
                    operation=OperationType.TOUCH,
                    source=file_path,
                    error=str(e)
                )
                results.append(result)
                self._print(f"Failed to touch {file_path}: {e}", 'error')
        
        return results
    
    def create(self, file_path: Union[str, Path], content: Optional[str] = None, from_stdin: bool = False, encoding: str = 'utf-8') -> OperationResult:
        """Create a file with content.
        
        Args:
            file_path: Path to the file to create
            content: Content to write (if provided)
            from_stdin: Read content from stdin
            encoding: Text encoding (default: utf-8)
        
        Returns:
            OperationResult indicating success/failure
        
        Examples:
            # Simple single-line content
            manager.create('file.txt', content='Hello, World!')
            
            # Multi-line content with --from-stdin (RECOMMENDED for complex content)
            cat << 'EOF' | ./safe_file_manager.py create script.py --from-stdin
            #!/usr/bin/env python3
            '''Complex multi-line Python code'''
            if condition:
                pass
            elif other_condition:
                pass
            EOF
            
            # ⚠️ IMPORTANT: The 'EOF' marker must be on its own line
            # Do NOT indent the EOF line or include it in your content
            # If you see 'EOF < /dev/null' in created files, you've copied the delimiter
            
            # Avoid shell parsing issues with complex content by using --from-stdin
            # instead of --content with shell-special characters like elif, done, etc.
        """
        file_path = _to_path(file_path)
        file_path = self._assert_safe_path(file_path)
        
        # Get content
        if from_stdin:
            # Read from stdin
            import sys
            content = sys.stdin.read()
        elif content is None:
            # No content provided
            content = ""
        
        # Check if file exists
        exists = file_path.exists()
        
        if exists and not self.force:
            # File exists, need confirmation
            if not self._get_confirmation(
                f"File '{file_path}' already exists. Overwrite?",
                RiskLevel.MEDIUM
            ):
                return OperationResult(
                    success=False,
                    operation=OperationType.CREATE,
                    source=file_path,
                    error="Operation cancelled by user"
                )
            
            # Backup existing file to trash
            if self.paranoid or CONFIG['AUTO_BACKUP']:
                backup_path = backup_to_trash(file_path)
                if backup_path:
                    self._print(f"Backed up existing file to: {backup_path}", 'info')
        
        # Perform safety check
        safety = analyze_safety([file_path], None, OperationType.CREATE)
        if not safety.is_safe and safety.risk_level.value >= RiskLevel.HIGH.value:
            self._print("Safety check failed:", 'error')
            for warning in safety.warnings:
                self._print(f"  - {warning}", 'warning')
            if not self.force:
                return OperationResult(
                    success=False,
                    operation=OperationType.CREATE,
                    source=file_path,
                    error="Safety check failed"
                )
        
        if self.dry_run:
            self._print(f"[DRY RUN] Would create file: {file_path} ({len(content)} bytes)", 'info')
            return OperationResult(
                success=True,
                operation=OperationType.CREATE,
                source=file_path,
                metadata={'dry_run': True, 'size': len(content)}
            )
        
        # Create parent directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content atomically
        try:
            with self.transaction(OperationType.CREATE, [file_path], {'size': len(content)}):
                with atomic_write(file_path, 'w', encoding=encoding) as f:
                    f.write(content)
                
                # Verify if paranoid
                if self.paranoid and content:
                    # Read back and verify
                    with open(file_path, 'r', encoding=encoding) as f:
                        written_content = f.read()
                    if written_content != content:
                        raise IOError("Content verification failed after write")
                
                self._print(f"Created: {file_path} ({len(content)} bytes)", 'success')
                
                # Add to history
                self.history.add_operation(
                    OperationType.CREATE,
                    file_path,
                    metadata={
                        'size': len(content),
                        'existed': exists,
                        'encoding': encoding
                    }
                )
                
                return OperationResult(
                    success=True,
                    operation=OperationType.CREATE,
                    source=file_path,
                    size=len(content),
                    metadata={
                        'existed': exists,
                        'encoding': encoding
                    }
                )
                
        except Exception as e:
            self._print(f"Failed to create file: {e}", 'error')
            return OperationResult(
                success=False,
                operation=OperationType.CREATE,
                source=file_path,
                error=str(e)
            )
    
    def cat(self, files: List[Path], number_lines: bool = False) -> List[OperationResult]:
        """View file contents safely."""
        results = []
        
        for file_path in files:
            try:
                if not file_path.exists():
                    raise FileOperationError(f"File does not exist: {file_path}")
                
                if not file_path.is_file():
                    raise FileOperationError(f"Not a file: {file_path}")
                
                # Check if file is binary
                mime_type = mimetypes.guess_type(str(file_path))[0]
                if mime_type and not mime_type.startswith('text'):
                    self._print(f"Warning: {file_path} appears to be a binary file", 'warning')
                    if not self._get_confirmation("Display anyway?", RiskLevel.LOW):
                        continue
                
                # Read and display file
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        if number_lines:
                            for i, line in enumerate(f, 1):
                                print(f"{i:6d}  {line}", end='')
                        else:
                            print(f.read(), end='')
                except KeyboardInterrupt:
                    print()  # New line after interrupted output
                    raise
                
                result = OperationResult(
                    success=True,
                    operation=OperationType.VIEW,
                    source=file_path,
                    metadata={'number_lines': number_lines}
                )
                results.append(result)
                
            except Exception as e:
                result = OperationResult(
                    success=False,
                    operation=OperationType.VIEW,
                    source=file_path,
                    error=str(e)
                )
                results.append(result)
                self._print(f"Failed to read {file_path}: {e}", 'error')
        
        return results
    
    def _parse_symbolic_mode(self, mode_str: str, current_mode: int) -> int:
        """Parse symbolic chmod mode string (e.g., +x, u+rwx, go-w).
        
        Args:
            mode_str: Symbolic mode string
            current_mode: Current file permissions as integer
            
        Returns:
            New permissions as integer
            
        Examples:
            +x -> add execute for all
            u+rwx -> add read/write/execute for user
            go-w -> remove write for group and other
            a+r -> add read for all (user, group, other)
        """
        # Start with current permissions
        new_mode = current_mode
        
        # Define permission bits
        perms = {
            'r': 4,  # read
            'w': 2,  # write
            'x': 1   # execute
        }
        
        # Define who bits
        who_masks = {
            'u': 0o700,  # user
            'g': 0o070,  # group
            'o': 0o007,  # other
            'a': 0o777   # all
        }
        
        # Parse symbolic mode parts (can have multiple like "u+x,go-w")
        for part in mode_str.split(','):
            part = part.strip()
            if not part:
                continue
                
            # Find the operator
            op = None
            op_idx = -1
            for i, char in enumerate(part):
                if char in '+-=':
                    op = char
                    op_idx = i
                    break
                    
            if op is None:
                raise ValueError(f"Invalid symbolic mode: {part} (missing operator +/-/=)")
                
            # Extract who and permissions
            who_part = part[:op_idx] if op_idx > 0 else 'a'  # default to 'all' if no who specified
            perm_part = part[op_idx + 1:]
            
            # Parse who
            who_mask = 0
            if who_part == '':  # e.g., "+x" means all
                who_mask = 0o777
            else:
                for who_char in who_part:
                    if who_char not in who_masks:
                        raise ValueError(f"Invalid 'who' character: {who_char}")
                    who_mask |= who_masks[who_char]
            
            # Parse permissions
            perm_value = 0
            for perm_char in perm_part:
                if perm_char not in perms:
                    raise ValueError(f"Invalid permission character: {perm_char}")
                perm_value |= perms[perm_char]
                
            # Apply the permission value to the appropriate positions
            if who_mask & 0o700:  # user
                perm_value_user = perm_value << 6
            else:
                perm_value_user = 0
                
            if who_mask & 0o070:  # group
                perm_value_group = perm_value << 3
            else:
                perm_value_group = 0
                
            if who_mask & 0o007:  # other
                perm_value_other = perm_value
            else:
                perm_value_other = 0
                
            combined_perm = perm_value_user | perm_value_group | perm_value_other
            
            # Apply the operation
            if op == '+':
                new_mode |= combined_perm
            elif op == '-':
                new_mode &= ~combined_perm
            elif op == '=':
                # For '=', we clear the affected bits first, then set new ones
                new_mode &= ~who_mask
                new_mode |= combined_perm
                
        return new_mode

    def chmod(self, files: List[Path], mode: str, recursive: bool = False) -> List[OperationResult]:
        """Change file permissions safely.
        
        Supports both octal (755, 644) and symbolic (+x, u+rwx, go-w) modes.
        
        Note: When running in non-interactive environments (CI/CD, scripts),
        use --yes flag to auto-confirm or set SFM_ASSUME_YES=1 to avoid
        EOF errors when the tool waits for confirmation.
        """
        # Convert to Path objects and validate
        files = _to_paths(files)
        files = [self._assert_safe_path(f) for f in files]
        
        results = []
        
        # Check if mode is octal or symbolic
        is_octal = mode.startswith('0') or (mode.isdigit() and len(mode) <= 4)
        
        # Process files
        def process_path(path: Path) -> OperationResult:
            try:
                if not path.exists():
                    raise FileOperationError(f"Path does not exist: {path}")
                
                old_mode = path.stat().st_mode & 0o777
                
                # Parse mode for this specific file
                try:
                    if is_octal:
                        # Octal mode
                        new_mode = int(mode, 8)
                    else:
                        # Symbolic mode - use our parser
                        new_mode = self._parse_symbolic_mode(mode, old_mode)
                except ValueError as e:
                    raise FileOperationError(f"Invalid mode '{mode}': {e}")
                
                if self.dry_run:
                    self._print(
                        f"[DRY RUN] Would change permissions of {path} from {oct(old_mode)} to {oct(new_mode)}",
                        'info'
                    )
                    return OperationResult(
                        success=True,
                        operation=OperationType.PERMISSION,
                        source=path,
                        metadata={'dry_run': True, 'old_mode': oct(old_mode), 'new_mode': oct(new_mode)}
                    )
                
                # Change permissions within transaction
                with self.transaction(OperationType.PERMISSION, [path], {'old_mode': oct(old_mode), 'new_mode': oct(new_mode)}):
                    os.chmod(path, new_mode)
                
                # Log operation
                result = OperationResult(
                    success=True,
                    operation=OperationType.PERMISSION,
                    source=path,
                    metadata={'old_mode': oct(old_mode), 'new_mode': oct(new_mode)}
                )
                self.history.add_operation(OperationType.PERMISSION, path, result=result)
                self._print(f"Changed permissions of {path} to {oct(new_mode)}", 'success')
                return result
                
            except Exception as e:
                self._print(f"Failed to chmod {path}: {e}", 'error')
                return OperationResult(
                    success=False,
                    operation=OperationType.PERMISSION,
                    source=path,
                    error=str(e)
                )
        
        # Get confirmation for permission changes
        prompt = f"Change permissions of {len(files)} item(s) to {mode}?"
        if not self._get_confirmation(prompt, RiskLevel.MEDIUM):
            return results
        
        # Process each file
        for file_path in files:
            if recursive and file_path.is_dir():
                # Process directory recursively
                for item in file_path.rglob('*'):
                    results.append(process_path(item))
            results.append(process_path(file_path))
        
        return results
    
    def chown(self, files: List[Path], owner: str, group: Optional[str] = None, recursive: bool = False) -> List[OperationResult]:
        """Change file ownership safely."""
        # Convert to Path objects and validate
        files = _to_paths(files)
        files = [self._assert_safe_path(f) for f in files]
        
        results = []
        
        # Platform check for Windows
        if sys.platform == 'win32':
            self._print("chown is not supported on Windows.", 'error')
            self._print("On Windows, use file permissions through Security properties or icacls command.", 'info')
            for path in files:
                results.append(OperationResult(
                    success=False,
                    operation=OperationType.OWNERSHIP,
                    source=path,
                    error="chown not supported on Windows"
                ))
            return results
        
        # Parse owner and group
        if ':' in owner:
            owner, group = owner.split(':', 1)
        
        # Get uid and gid
        try:
            import pwd, grp
            uid = pwd.getpwnam(owner).pw_uid if owner else -1
            gid = grp.getgrnam(group).gr_gid if group else -1
        except (KeyError, ImportError) as e:
            self._print(f"Invalid owner/group: {e}", 'error')
            return results
        
        # Process files
        def process_path(path: Path) -> OperationResult:
            try:
                if not path.exists():
                    raise FileOperationError(f"Path does not exist: {path}")
                
                stat_info = path.stat()
                old_uid, old_gid = stat_info.st_uid, stat_info.st_gid
                
                if self.dry_run:
                    self._print(
                        f"[DRY RUN] Would change ownership of {path} from {old_uid}:{old_gid} to {uid}:{gid}",
                        'info'
                    )
                    return OperationResult(
                        success=True,
                        operation=OperationType.OWNERSHIP,
                        source=path,
                        metadata={'dry_run': True, 'old_uid': old_uid, 'old_gid': old_gid, 'new_uid': uid, 'new_gid': gid}
                    )
                
                # Change ownership within transaction
                with self.transaction(OperationType.OWNERSHIP, [path], {'old_uid': old_uid, 'old_gid': old_gid, 'new_uid': uid, 'new_gid': gid}):
                    os.chown(path, uid, gid)
                
                # Log operation
                result = OperationResult(
                    success=True,
                    operation=OperationType.OWNERSHIP,
                    source=path,
                    metadata={'old_uid': old_uid, 'old_gid': old_gid, 'new_uid': uid, 'new_gid': gid}
                )
                self.history.add_operation(OperationType.OWNERSHIP, path, result=result)
                self._print(f"Changed ownership of {path} to {owner}:{group or ''}", 'success')
                return result
                
            except Exception as e:
                self._print(f"Failed to chown {path}: {e}", 'error')
                return OperationResult(
                    success=False,
                    operation=OperationType.OWNERSHIP,
                    source=path,
                    error=str(e)
                )
        
        # Get confirmation
        prompt = f"Change ownership of {len(files)} item(s) to {owner}:{group or ''}?"
        if not self._get_confirmation(prompt, RiskLevel.HIGH):
            return results
        
        # Process each file
        for file_path in files:
            if recursive and file_path.is_dir():
                # Process directory recursively
                for item in file_path.rglob('*'):
                    results.append(process_path(item))
            results.append(process_path(file_path))
        
        return results
    
    def ln(self, source: Path, destination: Path, symbolic: bool = True, force: bool = False) -> OperationResult:
        """Create links safely."""
        try:
            # Validate source
            if symbolic:
                # For symlinks, source doesn't need to exist
                pass
            else:
                # For hard links, source must exist and be a file
                if not source.exists():
                    raise FileOperationError(f"Source does not exist: {source}")
                if not source.is_file():
                    raise FileOperationError(f"Hard links can only be created for files: {source}")
            
            # Check destination
            if destination.exists():
                if not force:
                    if not self._get_confirmation(
                        f"Destination {destination} exists. Overwrite?",
                        RiskLevel.MEDIUM
                    ):
                        return OperationResult(
                            success=False,
                            operation=OperationType.LINK,
                            source=source,
                            destination=destination,
                            error="User cancelled"
                        )
                
                # Backup existing file
                if CONFIG['AUTO_BACKUP']:
                    backup_to_trash(destination)
                
                destination.unlink()
            
            if self.dry_run:
                link_type = "symbolic link" if symbolic else "hard link"
                self._print(f"[DRY RUN] Would create {link_type}: {destination} -> {source}", 'info')
                return OperationResult(
                    success=True,
                    operation=OperationType.LINK,
                    source=source,
                    destination=destination,
                    metadata={'dry_run': True, 'symbolic': symbolic}
                )
            
            # Create link
            if symbolic:
                destination.symlink_to(source)
            else:
                # Use os.link for hard links (Python 3.10+ has Path.hardlink_to)
                os.link(source, destination)
            
            # Log operation
            result = OperationResult(
                success=True,
                operation=OperationType.LINK,
                source=source,
                destination=destination,
                metadata={'symbolic': symbolic}
            )
            self.history.add_operation(OperationType.LINK, source, destination, result)
            
            link_type = "symbolic link" if symbolic else "hard link"
            self._print(f"Created {link_type}: {destination} -> {source}", 'success')
            return result
            
        except Exception as e:
            self._print(f"Failed to create link: {e}", 'error')
            return OperationResult(
                success=False,
                operation=OperationType.LINK,
                source=source,
                destination=destination,
                error=str(e)
            )
    
    def rmdir(self, directories: List[Path]) -> List[OperationResult]:
        """Remove empty directories safely."""
        results = []
        
        # Get confirmation
        prompt = f"Remove {len(directories)} empty director{'ies' if len(directories) > 1 else 'y'}?"
        if not self._get_confirmation(prompt, RiskLevel.MEDIUM):
            return results
        
        for directory in directories:
            try:
                if not directory.exists():
                    self._print(f"Directory does not exist: {directory}", 'warning')
                    continue
                
                if not directory.is_dir():
                    raise FileOperationError(f"Not a directory: {directory}")
                
                # Check if directory is empty
                if any(directory.iterdir()):
                    raise FileOperationError(f"Directory not empty: {directory}")
                
                if self.dry_run:
                    self._print(f"[DRY RUN] Would remove empty directory: {directory}", 'info')
                    results.append(OperationResult(
                        success=True,
                        operation=OperationType.RMDIR,
                        source=directory,
                        metadata={'dry_run': True}
                    ))
                    continue
                
                # Remove directory
                directory.rmdir()
                
                # Log operation
                result = OperationResult(
                    success=True,
                    operation=OperationType.RMDIR,
                    source=directory
                )
                results.append(result)
                self.history.add_operation(OperationType.RMDIR, directory, result=result)
                self._print(f"Removed empty directory: {directory}", 'success')
                
            except Exception as e:
                result = OperationResult(
                    success=False,
                    operation=OperationType.RMDIR,
                    source=directory,
                    error=str(e)
                )
                results.append(result)
                self._print(f"Failed to remove directory {directory}: {e}", 'error')
        
        return results
    
    def _start_transaction(self, op_type, targets, meta):
        """Start a new transaction and write to journal."""
        rec = {
            "id": str(uuid.uuid4()),
            "op": op_type.name if hasattr(op_type, "name") else str(op_type),
            "targets": [str(t) for t in targets],
            "meta": meta,
            "start_ts": datetime.utcnow(),
            "status": "started"
        }
        # Lock is already handled inside _write_journal
        self._write_journal(rec)
        return rec
    
    def _commit_transaction(self, rec):
        """Commit a transaction."""
        rec["end_ts"] = datetime.utcnow()
        rec["status"] = "committed"
        # Lock is already handled inside _write_journal
        self._write_journal(rec)
    
    def _abort_transaction(self, rec, exc):
        """Abort a transaction due to an exception."""
        rec["end_ts"] = datetime.utcnow()
        rec["status"] = "aborted"
        rec["error"] = repr(exc)
        # Lock is already handled inside _write_journal
        self._write_journal(rec)
    
    def _atomic_copy(self, src: Path, dst: Path, overwrite: bool = False):
        """Perform atomic copy with checksum verification."""
        if dst.exists() and not overwrite:
            raise FileExistsError(dst)
        
        if src.is_dir():
            # For directories, use copytree
            if dst.exists():
                if overwrite:
                    shutil.rmtree(dst)
                else:
                    raise FileExistsError(dst)
            shutil.copytree(src, dst, symlinks=self.preserve_attrs)
        else:
            # For files, use atomic copy with temp file
            tmp = dst.with_suffix(dst.suffix + f".{os.getpid()}.tmp")
            shutil.copy2(src, tmp)
            
            # Verify checksum if paranoid mode
            if self.paranoid:
                if _sha256(src) != _sha256(tmp):
                    tmp.unlink(missing_ok=True)
                    raise IOError("Checksum mismatch after copy")
            
            os.replace(tmp, dst)
            _fsync_dir(dst.parent)

# ─────────────────────────── CLI Interface ────────────────────────────

def create_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Safe File Manager - Enterprise-grade file management utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Move files safely
  %(prog)s move file1.txt file2.txt destination/
  
  # Copy with checksum verification
  %(prog)s copy --verify-checksum src/* dest/
  
  # Create file with simple content
  %(prog)s create config.txt --content "key=value"
  
  # Create file with multi-line content (RECOMMENDED for complex content)
  cat << 'EOF' | %(prog)s create script.py --from-stdin
  #!/usr/bin/env python3
  '''Multi-line Python script'''
  if condition:
      pass
  elif other_condition:
      pass
  EOF
  # NOTE: 'EOF' must be alone on its line - it's the delimiter, not file content!
  
  # Organize files by type
  %(prog)s organize ~/Downloads --by extension
  
  # Sync directories
  %(prog)s sync source/ backup/ --delete --exclude "*.tmp"
  
  # Restore from trash
  %(prog)s restore "important"

Shell Parsing Note:
  When using --content with complex strings containing shell keywords (elif, done, fi, etc.),
  the shell may fail to parse the command. Use --from-stdin with here-docs for complex content.
        """
    )
    
    # Global options
    parser.add_argument('--version', action='version', version='%(prog)s 2.0')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    parser.add_argument('--dry-run', action='store_true', help='Preview operations without executing')
    parser.add_argument('-y', '--yes', action='store_true', help='Auto-confirm medium-risk operations')
    parser.add_argument('--force', action='store_true', help='Auto-confirm high-risk operations')
    parser.add_argument('--non-interactive', action='store_true', help='Non-interactive mode for automation')
    parser.add_argument('--no-checksum', dest='verify_checksum', action='store_false',
                       help='Disable checksum verification')
    parser.add_argument('--no-preserve', dest='preserve_attrs', action='store_false',
                       help='Do not preserve file attributes')
    
    # Create subcommands
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')
    
    # Move command
    p_move = subparsers.add_parser('move', aliases=['mv'], help='Move files or directories')
    p_move.add_argument('sources', nargs='+', type=Path, help='Source files/directories')
    p_move.add_argument('destination', type=Path, help='Destination path')
    
    # Copy command
    p_copy = subparsers.add_parser('copy', aliases=['cp'], help='Copy files or directories')
    p_copy.add_argument('sources', nargs='+', type=Path, help='Source files/directories')
    p_copy.add_argument('destination', type=Path, help='Destination path')
    p_copy.add_argument('-r', '--recursive', action='store_true', help='Copy directories recursively')
    p_copy.add_argument('--overwrite', action='store_true', help='Overwrite existing destination files')
    
    # Delete/Trash commands
    p_trash = subparsers.add_parser('trash', aliases=['rm'], help='Move files to trash')
    p_trash.add_argument('sources', nargs='+', type=Path, help='Files/directories to trash')
    
    p_delete = subparsers.add_parser('delete', help='Permanently delete files')
    p_delete.add_argument('sources', nargs='+', type=Path, help='Files/directories to delete')
    p_delete.add_argument('--secure', action='store_true', help='Secure wipe before deletion')
    
    # List command
    p_list = subparsers.add_parser('list', aliases=['ls'], help='List directory contents')
    p_list.add_argument('path', nargs='?', type=Path, default=Path.cwd(), help='Directory to list')
    p_list.add_argument('-l', '--long', action='store_true', help='Long format')
    p_list.add_argument('-a', '--all', action='store_true', help='Show hidden files')
    p_list.add_argument('-H', '--human-readable', action='store_true', default=True,
                       help='Human-readable sizes')
    p_list.add_argument('--sort', choices=['name', 'size', 'time', 'extension'],
                       default='name', help='Sort order')
    
    # Organize command
    p_organize = subparsers.add_parser('organize', help='Organize files by criteria')
    p_organize.add_argument('directory', type=Path, help='Directory to organize')
    p_organize.add_argument('--by', choices=['extension', 'date', 'size', 'mime', 'custom'],
                           default='extension', help='Organization method')
    p_organize.add_argument('--rules', type=Path, help='Custom rules file (JSON/YAML)')
    
    # Sync command
    p_sync = subparsers.add_parser('sync', help='Synchronize directories')
    p_sync.add_argument('source', type=Path, help='Source directory')
    p_sync.add_argument('destination', type=Path, help='Destination directory')
    p_sync.add_argument('--delete', action='store_true', help='Delete extra files in destination')
    p_sync.add_argument('--exclude', nargs='+', help='Patterns to exclude')
    
    # Restore command
    p_restore = subparsers.add_parser('restore', help='Restore files from trash')
    p_restore.add_argument('pattern', nargs='?', help='Pattern to match files')
    
    # History command
    p_history = subparsers.add_parser('history', help='Show operation history')
    p_history.add_argument('--count', type=int, default=10, help='Number of entries to show')
    p_history.add_argument('--operation', choices=[op.value for op in OperationType],
                          help='Filter by operation type')
    p_history.add_argument('--path', type=Path, help='Filter by path')
    p_history.add_argument('--since', help='Show operations since date (YYYY-MM-DD)')
    
    # Info command
    p_info = subparsers.add_parser('info', help='Show file/directory information')
    p_info.add_argument('paths', nargs='+', type=Path, help='Paths to inspect')
    
    # Mkdir command
    p_mkdir = subparsers.add_parser('mkdir', help='Create directories')
    p_mkdir.add_argument('directories', nargs='+', type=Path, help='Directories to create')
    p_mkdir.add_argument('-p', '--parents', action='store_true', help='Create parent directories as needed')
    p_mkdir.add_argument('-m', '--mode', default='755', help='Set permissions (octal)')
    
    # Touch command
    p_touch = subparsers.add_parser('touch', help='Create files or update timestamps')
    p_touch.add_argument('files', nargs='+', type=Path, help='Files to touch')
    p_touch.add_argument('-c', '--no-create', action='store_true', help='Do not create files')
    
    # Create command
    p_create = subparsers.add_parser('create', help='Create file with content')
    p_create.add_argument('file', type=Path, help='File to create')
    p_create.add_argument('--content', '-c', help='Content to write to file')
    p_create.add_argument('--from-stdin', action='store_true', help='Read content from stdin')
    p_create.add_argument('--encoding', default='utf-8', help='Text encoding (default: utf-8)')
    
    # Cat command
    p_cat = subparsers.add_parser('cat', aliases=['view'], help='View file contents')
    p_cat.add_argument('files', nargs='+', type=Path, help='Files to display')
    p_cat.add_argument('-n', '--number', action='store_true', help='Number output lines')
    
    # Chmod command
    p_chmod = subparsers.add_parser('chmod', help='Change file permissions')
    p_chmod.add_argument('mode', help='Permissions (octal: 755, 644 or symbolic: +x, u+rwx, go-w)')
    p_chmod.add_argument('files', nargs='+', type=Path, help='Files to modify')
    p_chmod.add_argument('-R', '--recursive', action='store_true', help='Apply recursively')
    
    # Chown command
    p_chown = subparsers.add_parser('chown', help='Change file ownership')
    p_chown.add_argument('owner', help='Owner[:group]')
    p_chown.add_argument('files', nargs='+', type=Path, help='Files to modify')
    p_chown.add_argument('-R', '--recursive', action='store_true', help='Apply recursively')
    
    # Ln command
    p_ln = subparsers.add_parser('ln', help='Create links')
    p_ln.add_argument('source', type=Path, help='Source file/directory')
    p_ln.add_argument('destination', type=Path, help='Link destination')
    p_ln.add_argument('-s', '--symbolic', action='store_true', default=True, help='Create symbolic link (default)')
    p_ln.add_argument('-H', '--hard', action='store_true', help='Create hard link')
    p_ln.add_argument('-f', '--force', action='store_true', help='Force overwrite existing')
    
    # Rmdir command
    p_rmdir = subparsers.add_parser('rmdir', help='Remove empty directories')
    p_rmdir.add_argument('directories', nargs='+', type=Path, help='Empty directories to remove')

    # Change directory command
    p_cd = subparsers.add_parser('cd', help='Change directory (validates and returns absolute path)')
    p_cd.add_argument('directory', type=Path, help='Target directory to change to')

    # Print working directory command
    p_pwd = subparsers.add_parser('pwd', help='Print current working directory')
    
    return parser

def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Apply config file settings first (command-line args override)
    if apply_config_to_args is not None:
        apply_config_to_args('safe_file_manager', args, parser)
    
    # Handle environment variables
    if os.getenv('SAFE_FILE_NONINTERACTIVE') == '1':
        args.non_interactive = True
    if os.getenv('SAFE_FILE_ASSUME_YES') == '1':
        args.yes = True
    if os.getenv('SAFE_FILE_FORCE') == '1':
        args.force = True
    
    # Create manager instance
    manager_kwargs = {
        'dry_run': args.dry_run,
        'verbose': args.verbose,
        'quiet': args.quiet,
        'non_interactive': args.non_interactive,
        'assume_yes': args.yes,
        'force': args.force,
    }
    
    # Add command-specific options
    if hasattr(args, 'verify_checksum'):
        manager_kwargs['verify_checksum'] = args.verify_checksum
    if hasattr(args, 'preserve_attrs'):
        manager_kwargs['preserve_attrs'] = args.preserve_attrs
    
    try:
        with SafeFileManager(**manager_kwargs) as manager:
            # Execute command
            if args.command in ['move', 'mv']:
                manager.move(args.sources, args.destination)
            
            elif args.command in ['copy', 'cp']:
                manager.copy(args.sources, args.destination, overwrite=getattr(args, 'overwrite', False))
            
            elif args.command in ['trash', 'rm']:
                manager.trash(args.sources)
            
            elif args.command == 'delete':
                manager.delete(args.sources, secure=args.secure)
            
            elif args.command in ['list', 'ls']:
                manager.list_directory(
                    args.path,
                    long_format=args.long,
                    all_files=args.all,
                    human_readable=args.human_readable,
                    sort_by=args.sort
                )
            
            elif args.command == 'organize':
                manager.organize(
                    args.directory,
                    organization_type=args.by,
                    custom_rules=args.rules
                )
            
            elif args.command == 'sync':
                manager.sync(
                    args.source,
                    args.destination,
                    delete=args.delete,
                    exclude=args.exclude
                )
            
            elif args.command == 'restore':
                manager.restore_from_trash(args.pattern)
            
            elif args.command == 'history':
                # Parse since date if provided
                since = None
                if args.since:
                    try:
                        since = datetime.strptime(args.since, '%Y-%m-%d')
                    except ValueError:
                        print(f"❌ Invalid date format: {args.since}", file=sys.stderr)
                        sys.exit(1)
                
                # Get operation type
                op_type = None
                if args.operation:
                    op_type = OperationType(args.operation)
                
                # Find operations
                history = manager.history.find_operations(
                    operation=op_type,
                    path=args.path,
                    since=since
                )
                
                # Display history
                if not history:
                    print("No operations found matching criteria")
                else:
                    print(f"Found {len(history)} operations:")
                    for entry in history[-args.count:]:
                        op = entry['operation']
                        src = entry['source']
                        dst = entry.get('destination', '')
                        time = entry['timestamp']
                        success = '✅' if entry['success'] else '❌'
                        
                        print(f"{success} {time} {op:8} {src} {'→ ' + dst if dst else ''}")
            
            elif args.command == 'info':
                for path in args.paths:
                    if not path.exists():
                        print(f"❌ Path does not exist: {path}", file=sys.stderr)
                        continue
                    
                    info = get_file_info(path)
                    git_status = get_git_status(path)
                    
                    print(f"\n📁 {path}")
                    print(f"   Type: {info.get('type', 'unknown')}")
                    print(f"   Size: {format_size(info.get('size', 0))}")
                    print(f"   Mode: {info.get('mode', 'unknown')}")
                    print(f"   Modified: {info.get('mtime', 'unknown')}")
                    
                    if info.get('mime_type'):
                        print(f"   MIME: {info['mime_type']}")
                    
                    if git_status:
                        print(f"   Git: {'tracked' if git_status['is_tracked'] else 'untracked'}")
                        if git_status['is_modified']:
                            print(f"        modified {'(staged)' if git_status['is_staged'] else '(unstaged)'}")
                    
                    # Calculate checksum for files
                    if path.is_file() and path.stat().st_size < 100 * 1024 * 1024:  # < 100MB
                        checksum = calculate_checksum(path)
                        if checksum:
                            print(f"   SHA256: {checksum}")
            
            elif args.command == 'mkdir':
                mode = int(args.mode, 8) if args.mode else 0o755
                manager.mkdir(args.directories, parents=args.parents, mode=mode)
            
            elif args.command == 'touch':
                manager.touch(args.files, no_create=args.no_create)
            
            elif args.command == 'create':
                result = manager.create(
                    args.file,
                    content=args.content,
                    from_stdin=args.from_stdin,
                    encoding=args.encoding
                )
                if not result.success:
                    sys.exit(1)
            
            elif args.command in ['cat', 'view']:
                manager.cat(args.files, number_lines=args.number)
            
            elif args.command == 'chmod':
                manager.chmod(args.files, args.mode, recursive=args.recursive)
            
            elif args.command == 'chown':
                manager.chown(args.files, args.owner, recursive=args.recursive)
            
            elif args.command == 'ln':
                symbolic = not args.hard
                manager.ln(args.source, args.destination, symbolic=symbolic, force=args.force)
            
            elif args.command == 'rmdir':
                manager.rmdir(args.directories)

            elif args.command == 'cd':
                # Validate directory exists and is accessible
                directory = args.directory.resolve()
                if not directory.exists():
                    print(f"❌ Directory does not exist: {directory}", file=sys.stderr)
                    sys.exit(1)
                if not directory.is_dir():
                    print(f"❌ Not a directory: {directory}", file=sys.stderr)
                    sys.exit(1)
                if not os.access(directory, os.R_OK | os.X_OK):
                    print(f"❌ Directory is not accessible: {directory}", file=sys.stderr)
                    sys.exit(1)
                # Print absolute path for shell function to use
                print(str(directory))

            elif args.command == 'pwd':
                # Print current working directory
                print(str(Path.cwd()))
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()