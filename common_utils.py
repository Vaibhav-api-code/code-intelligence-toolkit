#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Common utilities for the smart code analysis toolkit.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
import shutil
import subprocess
import tempfile
import hashlib
import json
import time
import signal
import resource
import threading
from pathlib import Path
from collections import Counter
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Optional, Union, Tuple, Any

# ============================================================================
# SECURITY UTILITIES
# ============================================================================

def validate_path(path: Union[str, Path], base_dir: Optional[Path] = None) -> Path:
    """
    Validate and sanitize a file path to prevent path traversal attacks.
    
    Args:
        path: Path to validate
        base_dir: Optional base directory to restrict paths within
        
    Returns:
        Validated Path object
        
    Raises:
        ValueError: If path is invalid or outside base_dir
    """
    try:
        # Convert to Path and resolve to absolute
        p = Path(path).resolve()
        
        # Check for null bytes
        if '\0' in str(path):
            raise ValueError("Path contains null bytes")
            
        # If base_dir specified, ensure path is within it
        if base_dir:
            base = Path(base_dir).resolve()
            try:
                p.relative_to(base)
            except ValueError:
                raise ValueError(f"Path '{p}' is outside base directory '{base}'")
                
        return p
    except Exception as e:
        raise ValueError(f"Invalid path: {e}")

def sanitize_command_arg(arg: str) -> str:
    """
    Sanitize a command line argument to prevent injection attacks.
    
    Args:
        arg: Argument to sanitize
        
    Returns:
        Sanitized argument
    """
    # Remove potentially dangerous characters
    dangerous_chars = ['$', '`', '\\', '"', "'", '\n', '\r', ';', '|', '&', '<', '>', '(', ')']
    sanitized = arg
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    return sanitized

def safe_path_join(*parts: Union[str, Path]) -> Path:
    """
    Safely join path components preventing directory traversal.
    
    Args:
        *parts: Path components to join
        
    Returns:
        Joined path
        
    Raises:
        ValueError: If resulting path would traverse directories
    """
    # Remove any '..' components
    safe_parts = []
    for part in parts:
        part_str = str(part)
        if '..' in part_str or part_str.startswith('/'):
            raise ValueError(f"Unsafe path component: {part}")
        safe_parts.append(part_str)
        
    return Path(*safe_parts)

def is_safe_filename(filename: str) -> bool:
    """
    Check if a filename is safe (no special characters that could cause issues).
    
    Args:
        filename: Filename to check
        
    Returns:
        True if filename is safe
    """
    # Allow only alphanumeric, dash, underscore, dot
    safe_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
    return bool(safe_pattern.match(filename))

# ============================================================================
# SUBPROCESS HANDLING
# ============================================================================

class SubprocessTimeout(Exception):
    """Raised when a subprocess times out."""
    pass

def run_subprocess(
    cmd: List[str],
    timeout: int = 120,
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    capture_output: bool = True,
    max_memory_mb: int = 512,
    check: bool = True
) -> subprocess.CompletedProcess:
    """
    Run a subprocess with comprehensive safety features.
    
    Args:
        cmd: Command and arguments as list
        timeout: Timeout in seconds
        cwd: Working directory
        env: Environment variables
        capture_output: Whether to capture stdout/stderr
        max_memory_mb: Maximum memory usage in MB
        check: Whether to raise on non-zero exit
        
    Returns:
        CompletedProcess instance
        
    Raises:
        SubprocessTimeout: If process times out
        subprocess.CalledProcessError: If check=True and process fails
    """
    # Validate command
    if not cmd or not isinstance(cmd, list):
        raise ValueError("Command must be a non-empty list")
        
    # Sanitize command arguments
    safe_cmd = [cmd[0]]  # Keep program name as-is
    safe_cmd.extend(sanitize_command_arg(arg) for arg in cmd[1:])
    
    # Set up resource limits (only on Linux, macOS doesn't support RLIMIT_AS)
    def set_limits():
        # Only set memory limits on Linux
        if sys.platform.startswith('linux') and hasattr(resource, 'RLIMIT_AS'):
            try:
                resource.setrlimit(resource.RLIMIT_AS, (max_memory_mb * 1024 * 1024, max_memory_mb * 1024 * 1024))
            except Exception:
                pass  # Silently ignore if not supported
        
    # Prepare subprocess arguments
    kwargs = {
        'timeout': timeout,
        'check': check,
        'cwd': str(cwd) if cwd else None,
        'env': env
    }
    
    # Only add preexec_fn on Unix-like systems (not Windows)
    if sys.platform != 'win32':
        kwargs['preexec_fn'] = set_limits
    
    if capture_output:
        kwargs['capture_output'] = True
        kwargs['text'] = True
        
    try:
        return subprocess.run(safe_cmd, **kwargs)
    except subprocess.TimeoutExpired as e:
        raise SubprocessTimeout(f"Command timed out after {timeout}s: {' '.join(cmd)}")

def run_with_timeout(func, args=(), kwargs=None, timeout=60):
    """
    Run a function with a timeout using threading.
    
    Args:
        func: Function to run
        args: Positional arguments
        kwargs: Keyword arguments
        timeout: Timeout in seconds
        
    Returns:
        Function result
        
    Raises:
        TimeoutError: If function doesn't complete in time
    """
    kwargs = kwargs or {}
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
            
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        raise TimeoutError(f"Function timed out after {timeout}s")
        
    if exception[0]:
        raise exception[0]
        
    return result[0]

# ============================================================================
# FILE OPERATIONS
# ============================================================================

@contextmanager
def atomic_write(filepath: Path, mode: str = 'w', encoding: str = 'utf-8'):
    """
    Context manager for atomic file writing.
    Writes to a temporary file and moves it atomically.
    
    Args:
        filepath: Target file path
        mode: File mode
        encoding: Text encoding
        
    Yields:
        File handle for writing
    """
    filepath = Path(filepath)
    temp_fd, temp_path = tempfile.mkstemp(
        dir=filepath.parent,
        prefix=f'.{filepath.name}.',
        suffix='.tmp'
    )
    
    try:
        with open(temp_fd, mode, encoding=encoding) as f:
            yield f
            
        # Atomic move
        Path(temp_path).replace(filepath)
    except Exception:
        # Clean up temp file on error
        try:
            Path(temp_path).unlink()
        except Exception:
            pass
        raise

def safe_file_backup(filepath: Path, backup_dir: Optional[Path] = None) -> Path:
    """
    Create a backup of a file with timestamp.
    
    Args:
        filepath: File to backup
        backup_dir: Directory for backups (default: same as file)
        
    Returns:
        Path to backup file
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
        
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{filepath.stem}.{timestamp}{filepath.suffix}"
    
    # Determine backup location
    if backup_dir:
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / backup_name
    else:
        backup_path = filepath.parent / backup_name
        
    # Copy file
    shutil.copy2(filepath, backup_path)
    return backup_path

def calculate_file_hash(filepath: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of a file.
    
    Args:
        filepath: File to hash
        algorithm: Hash algorithm (sha256, md5, etc.)
        
    Returns:
        Hex digest of file hash
    """
    filepath = Path(filepath)
    hasher = hashlib.new(algorithm)
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            hasher.update(chunk)
            
    return hasher.hexdigest()

def safe_file_operation(operation: str, source: Path, dest: Optional[Path] = None, 
                       create_backup: bool = True) -> Dict[str, Any]:
    """
    Perform a file operation safely with rollback capability.
    
    Args:
        operation: 'move', 'copy', 'delete'
        source: Source file
        dest: Destination (for move/copy)
        create_backup: Whether to create backup
        
    Returns:
        Dictionary with operation details and rollback info
    """
    source = Path(source)
    result = {
        'operation': operation,
        'source': str(source),
        'timestamp': datetime.now().isoformat(),
        'success': False
    }
    
    # Create backup if requested
    if create_backup and source.exists():
        backup_path = safe_file_backup(source)
        result['backup'] = str(backup_path)
        
    try:
        if operation == 'move':
            if not dest:
                raise ValueError("Destination required for move operation")
            dest = Path(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            source.rename(dest)
            result['dest'] = str(dest)
            
        elif operation == 'copy':
            if not dest:
                raise ValueError("Destination required for copy operation")
            dest = Path(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            result['dest'] = str(dest)
            
        elif operation == 'delete':
            source.unlink()
            
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
        
    return result

# ============================================================================
# ENHANCED FILE READING AND STATS
# ============================================================================

def check_ripgrep():
    """Check if ripgrep is installed and suggest installation."""
    if not shutil.which('rg'):
        print("Error: ripgrep (rg) is not installed or not in your PATH.", file=sys.stderr)
        print("ripgrep is a prerequisite for this script.", file=sys.stderr)
        print("Please install it from: https://github.com/BurntSushi/ripgrep#installation", file=sys.stderr)
        sys.exit(1)

def detect_language(file_path):
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    lang_map = {
        '.java': 'java',
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.cs': 'csharp',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.swift': 'swift',
        '.log': 'log',
        '.txt': 'text',
        '.md': 'markdown',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.properties': 'properties',
        '.conf': 'config',
        '.cfg': 'config'
    }
    return lang_map.get(ext, 'unknown')

def classify_file_type(file_path):
    """Classify file as source, test, config, or log."""
    path_str = str(file_path).lower()
    
    # Test files
    if any(indicator in path_str for indicator in ['test', '/tests/', '\\tests\\', 'spec']):
        return 'test'
    if path_str.endswith(('test.java', 'test.py', 'spec.js', 'spec.ts')):
        return 'test'
    
    # Log files
    if any(ext in path_str for ext in ['.log', '.txt', 'logs/', '\\logs\\']):
        return 'log'
    
    # Configuration files
    config_patterns = ['.xml', '.properties', '.json', '.yml', '.yaml', '.conf', '.cfg', '.ini']
    if any(ext in path_str for ext in config_patterns):
        return 'config'
    
    # Documentation files
    if any(ext in path_str for ext in ['.md', '.rst', '.doc', 'readme', 'changelog']):
        return 'documentation'
    
    # Source files
    if 'src/main' in path_str or '/src/' in path_str or '\\src\\' in path_str:
        return 'source'
    
    # Build/output files
    if any(pattern in path_str for pattern in ['build/', 'target/', 'dist/', 'out/', '__pycache__']):
        return 'build'
    
    return 'other'

def detect_primary_language(scope):
    """Safely detect the dominant language using pathlib, avoiding shell=True."""
    try:
        p = Path(scope)
        if not p.is_dir():
            return detect_language(str(p))
        
        # Limit scan to 1000 files for performance
        files = list(p.rglob("*"))[:1000]
        ext_counts = Counter(f.suffix for f in files if f.is_file())
        
        # Priority order for language detection
        language_priorities = [
            ('.java', 'java'),
            ('.py', 'python'), 
            ('.js', 'javascript'),
            ('.ts', 'typescript'),
            ('.cpp', 'cpp'),
            ('.c', 'c'),
            ('.go', 'go'),
            ('.rs', 'rust')
        ]
        
        for ext, lang in language_priorities:
            if ext_counts.get(ext, 0) > 0:
                return lang
                
    except Exception as e:
        print(f"Language auto-detection failed: {e}", file=sys.stderr)
    return None

def safe_get_file_content(file_path, encoding='utf-8', max_size_mb=10):
    """Safely read file content with size and encoding checks."""
    try:
        path = Path(file_path)
        if not path.exists():
            return None
            
        # Check file size (avoid loading huge files)
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            print(f"Warning: Skipping large file {file_path} ({size_mb:.1f}MB)", file=sys.stderr)
            return None
            
        return path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            return path.read_text(encoding='latin-1')
        except Exception:
            print(f"Warning: Could not read file {file_path} (encoding issues)", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Warning: Could not read file {file_path}: {e}", file=sys.stderr)
        return None

def extract_method_parameters(signature_line):
    """Extract method parameters from a method signature."""
    try:
        match = re.search(r'\(([^)]*)\)', signature_line)
        if match:
            params_str = match.group(1).strip()
            if not params_str:
                return []
            
            params = []
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    # Split type and name for Java-style parameters
                    parts = param.split()
                    if len(parts) >= 2:
                        param_type = ' '.join(parts[:-1])
                        param_name = parts[-1]
                        params.append({'type': param_type, 'name': param_name})
                    else:
                        params.append({'type': param, 'name': ''})
            return params
    except Exception:
        pass
    return []

def find_closing_brace(content, open_brace_pos):
    """Find the position of the matching closing brace for a given opening brace."""
    if open_brace_pos >= len(content) or content[open_brace_pos] != '{':
        return -1
    
    brace_level = 1
    i = open_brace_pos + 1
    
    while i < len(content) and brace_level > 0:
        char = content[i]
        if char == '{':
            brace_level += 1
        elif char == '}':
            brace_level -= 1
        i += 1
    
    return i - 1 if brace_level == 0 else -1

def normalize_path(path_str):
    """Normalize file paths for consistent comparison across platforms."""
    return str(Path(path_str)).replace('\\', '/')

def is_binary_file(file_path, chunk_size=1024):
    """Check if a file is likely binary by examining a chunk of its content."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(chunk_size)
            if b'\x00' in chunk:  # Null bytes typically indicate binary
                return True
            # Check for high ratio of non-printable characters
            non_printable = sum(1 for byte in chunk if byte < 32 and byte not in (9, 10, 13))
            return non_printable / len(chunk) > 0.3 if chunk else False
    except Exception:
        return True  # Assume binary if we can't read it

def get_file_stats(file_path):
    """Get basic statistics about a file."""
    try:
        path = Path(file_path)
        stat = path.stat()
        
        return {
            'size_bytes': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'modified_time': stat.st_mtime,
            'is_binary': is_binary_file(file_path),
            'language': detect_language(file_path),
            'file_type': classify_file_type(file_path)
        }
    except Exception as e:
        return {'error': str(e)}

def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB" 
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def validate_regex_pattern(pattern):
    """Validate that a string is a valid regex pattern."""
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False

def standardize_line_endings(content):
    """Standardize line endings to Unix format."""
    return content.replace('\r\n', '\n').replace('\r', '\n')

# ============================================================================
# ERROR HANDLING AND LOGGING
# ============================================================================

class ErrorContext:
    """Context manager for capturing and logging errors."""
    
    def __init__(self, operation: str, details: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.details = details or {}
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Log error with context
            duration = time.time() - self.start_time
            error_info = {
                'operation': self.operation,
                'error_type': exc_type.__name__,
                'error_message': str(exc_val),
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat(),
                **self.details
            }
            
            # Try to import error_logger if available
            try:
                from error_logger import log_error
                log_error(exc_val, error_info)
            except ImportError:
                # Fallback to stderr
                print(f"ERROR in {self.operation}: {exc_val}", file=sys.stderr)
                
        return False  # Don't suppress the exception

# ============================================================================
# MANIFEST AND ROLLBACK SUPPORT
# ============================================================================

class OperationManifest:
    """Track operations for potential rollback."""
    
    def __init__(self, manifest_file: Optional[Path] = None):
        self.manifest_file = manifest_file or Path.home() / '.pytools' / 'operations.json'
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        self.operations = self._load_manifest()
        
    def _load_manifest(self) -> List[Dict[str, Any]]:
        """Load existing manifest."""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []
        
    def add_operation(self, operation: Dict[str, Any]):
        """Add an operation to the manifest."""
        operation['id'] = hashlib.sha256(
            f"{operation['operation']}{operation['source']}{time.time()}".encode()
        ).hexdigest()[:8]
        
        self.operations.append(operation)
        self._save_manifest()
        return operation['id']
        
    def _save_manifest(self):
        """Save manifest to disk."""
        with atomic_write(self.manifest_file) as f:
            json.dump(self.operations, f, indent=2)
            
    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific operation by ID."""
        for op in self.operations:
            if op.get('id') == operation_id:
                return op
        return None
        
    def rollback_operation(self, operation_id: str) -> bool:
        """Attempt to rollback an operation."""
        op = self.get_operation(operation_id)
        if not op:
            return False
            
        try:
            if op['operation'] == 'move' and 'backup' in op:
                # Restore from backup
                shutil.copy2(op['backup'], op['source'])
                if 'dest' in op:
                    Path(op['dest']).unlink()
                    
            elif op['operation'] == 'delete' and 'backup' in op:
                # Restore from backup
                shutil.copy2(op['backup'], op['source'])
                
            elif op['operation'] == 'copy' and 'dest' in op:
                # Remove the copy
                Path(op['dest']).unlink()
                
            # Mark as rolled back
            op['rolled_back'] = True
            op['rollback_time'] = datetime.now().isoformat()
            self._save_manifest()
            return True
            
        except Exception as e:
            print(f"Rollback failed: {e}", file=sys.stderr)
            return False

# ============================================================================
# COMMON CLI ARGUMENT HANDLING
# ============================================================================

# Common CLI argument configurations for consistency across tools
COMMON_CLI_ARGS = {
    'scope': {
        'flag': '--scope',
        'default': '.',
        'help': 'Directory to search (default: current directory)'
    },
    'language': {
        'flag': '--language',
        'choices': ['java', 'python', 'javascript', 'typescript', 'cpp', 'c', 'go', 'rust'],
        'help': 'Programming language filter'
    },
    'ignore_case': {
        'flag': '--ignore-case',
        'short': '-i',
        'action': 'store_true',
        'help': 'Case-insensitive search'
    },
    'context': {
        'flag': '--context',
        'short': '-C',
        'type': int,
        'default': 3,
        'help': 'Lines of context around matches (default: 3)'
    },
    'max_results': {
        'flag': '--max-results',
        'type': int,
        'help': 'Maximum number of results to show'
    },
    'json_output': {
        'flag': '--json',
        'action': 'store_true',
        'help': 'Output results as JSON'
    },
    'file_pattern': {
        'flag': '--file-pattern',
        'short': '-g',
        'default': '*',
        'help': 'File pattern to include (e.g., "*.java", "*.py")'
    },
    'regex': {
        'flag': '--regex',
        'action': 'store_true',
        'help': 'Use regex pattern matching'
    },
    'timeout': {
        'flag': '--timeout',
        'type': int,
        'default': 120,
        'help': 'Timeout in seconds for search operations (default: 120)'
    },
    'verbose': {
        'flag': '--verbose',
        'short': '-v',
        'action': 'store_true',
        'help': 'Enable verbose output'
    },
    'quiet': {
        'flag': '--quiet',
        'short': '-q',
        'action': 'store_true',
        'help': 'Suppress non-essential output'
    },
    'dry_run': {
        'flag': '--dry-run',
        'action': 'store_true',
        'help': 'Show what would be done without doing it'
    },
    'force': {
        'flag': '--force',
        'short': '-f',
        'action': 'store_true',
        'help': 'Force operation without confirmation'
    },
    'backup': {
        'flag': '--backup',
        'action': 'store_true',
        'help': 'Create backup before modifying files'
    },
    'interactive': {
        'flag': '--interactive',
        'action': 'store_true',
        'help': 'Prompt for confirmation before each operation'
    }
}

def add_common_args(parser, *arg_names):
    """Add common CLI arguments to an ArgumentParser."""
    for arg_name in arg_names:
        if arg_name in COMMON_CLI_ARGS:
            config = COMMON_CLI_ARGS[arg_name].copy()
            flag = config.pop('flag')
            short = config.pop('short', None)
            
            if short:
                parser.add_argument(flag, short, **config)
            else:
                parser.add_argument(flag, **config)
        else:
            print(f"Warning: Unknown common argument '{arg_name}'", file=sys.stderr)

# ============================================================================
# RESOURCE MANAGEMENT
# ============================================================================

@contextmanager
def resource_limit(cpu_seconds: Optional[int] = None, memory_mb: Optional[int] = None):
    """
    Context manager to limit resource usage.
    Note: Memory limits (RLIMIT_AS) are only supported on Linux.
    
    Args:
        cpu_seconds: CPU time limit in seconds
        memory_mb: Memory limit in megabytes (Linux only)
    """
    old_cpu = None
    old_memory = None
    
    try:
        if cpu_seconds and hasattr(resource, 'RLIMIT_CPU'):
            try:
                old_cpu = resource.getrlimit(resource.RLIMIT_CPU)
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
            except Exception:
                pass  # Silently ignore if not supported
            
        # Memory limits only work on Linux
        if memory_mb and sys.platform.startswith('linux') and hasattr(resource, 'RLIMIT_AS'):
            try:
                old_memory = resource.getrlimit(resource.RLIMIT_AS)
                memory_bytes = memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            except Exception:
                pass  # Silently ignore if not supported
            
        yield
        
    finally:
        # Restore original limits
        if old_cpu:
            try:
                resource.setrlimit(resource.RLIMIT_CPU, old_cpu)
            except Exception:
                pass
        if old_memory:
            try:
                resource.setrlimit(resource.RLIMIT_AS, old_memory)
            except Exception:
                pass

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Simple test when run directly
    print("Common utilities for smart code analysis toolkit")
    print(f"Ripgrep available: {shutil.which('rg') is not None}")
    print(f"Current directory language: {detect_primary_language('.')}")
    
    # Test file classification
    test_files = [
        'example.java',
        'TestFile.java', 
        'config.properties',
        'log.txt',
        'README.md'
    ]
    
    print("\nFile type classification examples:")
    for file_path in test_files:
        lang = detect_language(file_path)
        file_type = classify_file_type(file_path)
        print(f"  {file_path}: {lang} ({file_type})")
        
    # Test security functions
    print("\nSecurity function tests:")
    try:
        safe_path = validate_path("./test.txt")
        print(f"  Valid path: {safe_path}")
    except ValueError as e:
        print(f"  Path validation error: {e}")
        
    print(f"  Safe filename 'test.txt': {is_safe_filename('test.txt')}")
    print(f"  Safe filename '../evil.sh': {is_safe_filename('../evil.sh')}")
    
    # Test subprocess with timeout
    print("\nSubprocess test:")
    try:
        result = run_subprocess(['echo', 'Hello, World!'], timeout=5)
        print(f"  Command output: {result.stdout.strip()}")
    except Exception as e:
        print(f"  Subprocess error: {e}")