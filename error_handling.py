#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Error Handling Module for Java Intelligence Analysis Toolkit

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import time
import traceback
import functools
import contextlib
import signal
from typing import Any, Callable, Optional, Type, Union, Dict, List, Tuple
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime
from enum import Enum
import argparse

# Try to import error logger if available

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

try:
    from error_logger import log_error, ErrorLogger
    HAS_ERROR_LOGGER = True
except ImportError:
    HAS_ERROR_LOGGER = False
    
    # Fallback error logging
    def log_error(func_name: str, error: Exception, **context):
        """Fallback error logging when error_logger is not available"""
        timestamp = datetime.now().isoformat()
        error_msg = f"[{timestamp}] ERROR in {func_name}: {type(error).__name__}: {str(error)}"
        if context:
            error_msg += f"\nContext: {json.dumps(context, indent=2, default=str)}"
        print(error_msg, file=sys.stderr)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ToolkitError(Exception):
    """Base exception class for all toolkit errors"""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, **context):
        super().__init__(message)
        self.severity = severity
        self.context = context
        self.timestamp = datetime.now()

class FileOperationError(ToolkitError):
    """Raised when file operations fail"""
    pass

class ParseError(ToolkitError):
    """Raised when parsing operations fail"""
    pass

class ValidationError(ToolkitError):
    """Raised when validation fails"""
    pass

class ConfigurationError(ToolkitError):
    """Raised when configuration is invalid"""
    pass

class TimeoutError(ToolkitError):
    """Raised when operations timeout"""
    pass

class RecoverableError(ToolkitError):
    """Base class for errors that can be recovered from"""
    
    def __init__(self, message: str, recovery_hint: str = "", **context):
        super().__init__(message, severity=ErrorSeverity.LOW, **context)
        self.recovery_hint = recovery_hint

def safe_execution(
    default_return: Any = None,
    max_retries: int = 0,
    retry_delay: float = 1.0,
    exponential_backoff: bool = False,
    catch_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    log_errors: bool = True,
    error_message: Optional[str] = None,
    recovery_handler: Optional[Callable[[Exception], Any]] = None
):
    """
    Decorator for safe execution with comprehensive error handling
    
    Args:
        default_return: Value to return on error
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        exponential_backoff: Use exponential backoff for retries
        catch_exceptions: Tuple of exception types to catch
        log_errors: Whether to log errors
        error_message: Custom error message
        recovery_handler: Function to call for error recovery
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            attempt = 0
            
            while attempt <= max_retries:
                try:
                    return func(*args, **kwargs)
                    
                except catch_exceptions as e:
                    last_error = e
                    attempt += 1
                    
                    # Log the error
                    if log_errors:
                        context = {
                            'function': func.__name__,
                            'attempt': attempt,
                            'max_retries': max_retries,
                            'args': str(args)[:200],
                            'kwargs': str(kwargs)[:200]
                        }
                        
                        if HAS_ERROR_LOGGER:
                            log_error(func.__name__, e, **context)
                        else:
                            log_error(func.__name__, e, **context)
                    
                    # Try recovery handler
                    if recovery_handler:
                        try:
                            recovery_result = recovery_handler(e)
                            if recovery_result is not None:
                                return recovery_result
                        except Exception as recovery_error:
                            if log_errors:
                                log_error(f"{func.__name__}_recovery", recovery_error)
                    
                    # Check if we should retry
                    if attempt <= max_retries:
                        delay = retry_delay
                        if exponential_backoff:
                            delay = retry_delay * (2 ** (attempt - 1))
                        
                        if error_message:
                            print(f"{error_message} (attempt {attempt}/{max_retries + 1})", file=sys.stderr)
                        
                        time.sleep(delay)
                    else:
                        # Max retries exceeded
                        if error_message:
                            print(f"{error_message} (all {max_retries + 1} attempts failed)", file=sys.stderr)
                        break
            
            return default_return
            
        return wrapper
    return decorator

def timeout_handler(timeout_seconds: int):
    """
    Decorator to add timeout handling to functions
    
    Args:
        timeout_seconds: Maximum execution time in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def timeout_callback(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
            
            # Set up signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_callback)
            signal.alarm(timeout_seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Restore original handler and cancel alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
            
        return wrapper
    return decorator

@contextlib.contextmanager
def safe_file_operation(file_path: Union[str, Path], operation: str = "read"):
    """
    Context manager for safe file operations with automatic cleanup
    
    Args:
        file_path: Path to the file
        operation: Type of operation (read, write, modify)
    """
    file_path = Path(file_path)
    backup_path = None
    temp_file = None
    
    try:
        if operation in ["write", "modify"] and file_path.exists():
            # Create backup for existing files
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            shutil.copy2(file_path, backup_path)
        
        if operation == "write":
            # Use temporary file for writing
            temp_fd, temp_path = tempfile.mkstemp(
                dir=file_path.parent,
                prefix=f".{file_path.name}.",
                suffix=".tmp"
            )
            os.close(temp_fd)
            temp_file = Path(temp_path)
            yield temp_file
            
            # Atomic move
            temp_file.replace(file_path)
            temp_file = None
            
        else:
            yield file_path
            
    except Exception as e:
        # Restore from backup if available
        if backup_path and backup_path.exists():
            try:
                shutil.copy2(backup_path, file_path)
            except Exception as restore_error:
                log_error("safe_file_operation_restore", restore_error)
        
        raise FileOperationError(
            f"Failed to {operation} file {file_path}: {str(e)}",
            severity=ErrorSeverity.HIGH,
            file_path=str(file_path),
            operation=operation
        )
        
    finally:
        # Cleanup
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass
                
        if backup_path and backup_path.exists():
            try:
                backup_path.unlink()
            except Exception:
                pass

@contextlib.contextmanager
def error_context(context_name: str, **context_data):
    """
    Context manager that adds context information to errors
    
    Args:
        context_name: Name of the context
        **context_data: Additional context data
    """
    try:
        yield
    except Exception as e:
        # Add context to error
        if hasattr(e, 'context'):
            e.context.update(context_data)
        else:
            e.context = context_data
        
        # Log with context
        log_error(context_name, e, **context_data)
        
        # Re-raise with additional info
        raise type(e)(f"[{context_name}] {str(e)}") from e

def validate_file_path(file_path: Union[str, Path], must_exist: bool = False) -> Path:
    """
    Validate a file path with security checks
    
    Args:
        file_path: Path to validate
        must_exist: Whether the file must exist
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        path = Path(file_path).resolve()
        
        # Security check - prevent path traversal
        if ".." in str(file_path):
            raise ValidationError(
                f"Path traversal detected in {file_path}",
                severity=ErrorSeverity.CRITICAL,
                file_path=str(file_path)
            )
        
        # Existence check
        if must_exist and not path.exists():
            raise ValidationError(
                f"File does not exist: {path}",
                severity=ErrorSeverity.HIGH,
                file_path=str(path)
            )
        
        # Readability check
        if must_exist and not os.access(path, os.R_OK):
            raise ValidationError(
                f"File is not readable: {path}",
                severity=ErrorSeverity.HIGH,
                file_path=str(path)
            )
        
        return path
        
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(
            f"Invalid file path: {file_path}: {str(e)}",
            severity=ErrorSeverity.HIGH,
            file_path=str(file_path)
        )

def create_error_report(
    error: Exception,
    include_traceback: bool = True,
    include_system_info: bool = True
) -> Dict[str, Any]:
    """
    Create a comprehensive error report
    
    Args:
        error: The exception to report
        include_traceback: Include full traceback
        include_system_info: Include system information
        
    Returns:
        Dictionary containing error details
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'severity': getattr(error, 'severity', ErrorSeverity.MEDIUM).value
    }
    
    # Add error context if available
    if hasattr(error, 'context'):
        report['context'] = error.context
    
    # Add traceback
    if include_traceback:
        report['traceback'] = traceback.format_exc()
    
    # Add system info
    if include_system_info:
        report['system_info'] = {
            'platform': sys.platform,
            'python_version': sys.version,
            'cwd': os.getcwd()
        }
    
    return report

class ErrorRecoveryManager:
    """
    Manager for coordinating error recovery strategies
    """
    
    def __init__(self):
        self.recovery_strategies: Dict[Type[Exception], List[Callable]] = {}
        self.fallback_strategies: List[Callable] = []
    
    def register_recovery(
        self,
        exception_type: Type[Exception],
        recovery_func: Callable[[Exception], Any]
    ):
        """Register a recovery function for a specific exception type"""
        if exception_type not in self.recovery_strategies:
            self.recovery_strategies[exception_type] = []
        self.recovery_strategies[exception_type].append(recovery_func)
    
    def register_fallback(self, recovery_func: Callable[[Exception], Any]):
        """Register a fallback recovery function"""
        self.fallback_strategies.append(recovery_func)
    
    def attempt_recovery(self, error: Exception) -> Optional[Any]:
        """
        Attempt to recover from an error
        
        Args:
            error: The exception to recover from
            
        Returns:
            Recovery result if successful, None otherwise
        """
        # Try specific recovery strategies
        for exc_type in type(error).__mro__:
            if exc_type in self.recovery_strategies:
                for strategy in self.recovery_strategies[exc_type]:
                    try:
                        result = strategy(error)
                        if result is not None:
                            return result
                    except Exception as recovery_error:
                        log_error("recovery_attempt", recovery_error)
        
        # Try fallback strategies
        for strategy in self.fallback_strategies:
            try:
                result = strategy(error)
                if result is not None:
                    return result
            except Exception as recovery_error:
                log_error("fallback_recovery", recovery_error)
        
        return None

# Global recovery manager instance
recovery_manager = ErrorRecoveryManager()

def recoverable_operation(
    operation_name: str,
    recovery_strategies: Optional[List[Callable]] = None
):
    """
    Decorator for operations that can be recovered from
    
    Args:
        operation_name: Name of the operation
        recovery_strategies: List of recovery functions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error
                log_error(operation_name, e)
                
                # Try recovery strategies
                if recovery_strategies:
                    for strategy in recovery_strategies:
                        try:
                            result = strategy(e, *args, **kwargs)
                            if result is not None:
                                return result
                        except Exception as recovery_error:
                            log_error(f"{operation_name}_recovery", recovery_error)
                
                # Try global recovery manager
                result = recovery_manager.attempt_recovery(e)
                if result is not None:
                    return result
                
                # Re-raise if no recovery succeeded
                raise RecoverableError(
                    f"Operation {operation_name} failed: {str(e)}",
                    recovery_hint="Check error context and retry with different parameters",
                    operation=operation_name,
                    original_error=str(e)
                )
        
        return wrapper
    return decorator

# Utility functions for common error scenarios

def handle_file_not_found(default_content: str = ""):
    """Recovery handler for file not found errors"""
    def handler(error: Exception) -> Optional[str]:
        if isinstance(error, (FileNotFoundError, IOError)):
            return default_content
        return None
    return handler

def handle_parse_error(default_value: Any = None):
    """Recovery handler for parse errors"""
    def handler(error: Exception) -> Optional[Any]:
        if isinstance(error, (json.JSONDecodeError, ValueError, ParseError)):
            return default_value
        return None
    return handler

def retry_with_cleanup(cleanup_func: Callable):
    """Recovery handler that performs cleanup before retry"""
    def handler(error: Exception) -> None:
        try:
            cleanup_func()
        except Exception as cleanup_error:
            log_error("cleanup_before_retry", cleanup_error)
        return None
    return handler

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Error Handling Module - Comprehensive error handling utilities for Java Intelligence Analysis Toolkit",
        epilog="""
This module provides error handling decorators and utilities. It is designed to be imported and used by other tools.

Available Decorators:
  @safe_execution        - Provides error handling with retries and default returns
  @timeout_handler       - Adds timeout protection to functions
  @recoverable_operation - Marks operations that can be recovered from

Available Context Managers:
  safe_file_operation - Safe file operations with automatic backup/restore
  error_context       - Adds context information to errors

Available Exception Classes:
  ToolkitError        - Base exception class
  FileOperationError  - File operation failures
  ParseError          - Parsing failures
  ValidationError     - Validation failures
  ConfigurationError  - Configuration issues
  TimeoutError        - Operation timeouts
  RecoverableError    - Recoverable errors

Example Usage:
  from error_handling import safe_execution, ValidationError
  
  @safe_execution(default_return=[], max_retries=3)
  def process_data(data):
      if not data:
          raise ValidationError("No data provided")
      return [item.upper() for item in data]

For more examples, see the module documentation.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add example argument to demonstrate usage
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demonstration of error handling features"
    )
    
    args = parser.parse_args()
    
    if args.demo:
        print("Running error handling demonstrations...\n")
        
        # Demo 1: Safe execution with retries
        print("1. Safe execution with retries:")
        @safe_execution(
            default_return="Failed",
            max_retries=2,
            retry_delay=0.5,
            error_message="Demo operation failed"
        )
        def flaky_operation():
            import random
            if random.random() < 0.7:  # 70% failure rate
                raise RuntimeError("Random failure")
            return "Success"
        
        result = flaky_operation()
        print(f"   Result: {result}\n")
        
        # Demo 2: Timeout handling
        print("2. Timeout handling:")
        @timeout_handler(timeout_seconds=1)
        def quick_operation():
            time.sleep(0.5)
            return "Completed in time"
        
        try:
            result = quick_operation()
            print(f"   Result: {result}")
        except TimeoutError as e:
            print(f"   Caught timeout: {e}")
        
        # Demo 3: File operation safety
        print("\n3. Safe file operations:")
        temp_file = Path("/tmp/demo_error_handling.json")
        test_data = {"demo": "data", "timestamp": datetime.now().isoformat()}
        
        try:
            with safe_file_operation(temp_file, "write") as path:
                with open(path, 'w') as f:
                    json.dump(test_data, f)
            print("   Successfully wrote to temporary file")
            
            # Clean up
            if temp_file.exists():
                temp_file.unlink()
                print("   Cleaned up temporary file")
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\nDemonstration complete!")
    else:
        # Just show module status
        print("Error Handling Module")
        print("=" * 50)
        print(f"Module loaded: Yes")
        print(f"Error logging available: {HAS_ERROR_LOGGER}")
        print(f"Standard parser available: {HAS_STANDARD_PARSER}")
        print("\nThis is a utility module designed to be imported by other tools.")
        print("Use --help to see available features or --demo to run demonstrations.")