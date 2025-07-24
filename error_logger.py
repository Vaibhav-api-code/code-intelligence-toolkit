#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Centralized error logging system for all Python tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import json
import traceback
import datetime
import functools
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import platform

# Try to import psutil for system info, but make it optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class ErrorLogger:
    """Centralized error logger for Python tools."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize error logger with configurable log directory."""
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            # Default to ~/.pytoolserrors or current directory
            home = Path.home()
            self.log_dir = home / ".pytoolserrors"
            
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log files
        self.error_log = self.log_dir / "errors.jsonl"
        self.summary_log = self.log_dir / "error_summary.json"
        
    def log_error(self, 
                  tool_name: str,
                  error_type: str,
                  error_message: str,
                  command_args: list,
                  stack_trace: Optional[str] = None,
                  additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an error with full context.
        
        Returns:
            Error ID for reference
        """
        # Generate unique error ID
        error_id = self._generate_error_id(tool_name, error_message)
        
        # Capture system context
        system_context = self._get_system_context()
        
        # Build error record
        error_record = {
            "error_id": error_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "tool_name": tool_name,
            "error_type": error_type,
            "error_message": error_message,
            "command_args": command_args,
            "stack_trace": stack_trace,
            "system_context": system_context,
            "additional_context": additional_context or {},
            "python_version": sys.version,
            "cwd": os.getcwd()
        }
        
        # Write to JSONL file (append mode)
        try:
            with open(self.error_log, 'a', encoding='utf-8') as f:
                json.dump(error_record, f)
                f.write('\n')
        except Exception as e:
            # Fallback to stderr if logging fails
            print(f"Failed to write to error log: {e}", file=sys.stderr)
            
        # Update summary
        self._update_summary(tool_name, error_type)
        
        return error_id
    
    def _generate_error_id(self, tool_name: str, error_message: str) -> str:
        """Generate a unique error ID based on tool and error."""
        content = f"{tool_name}:{error_message}:{datetime.datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _get_system_context(self) -> Dict[str, Any]:
        """Capture system context for debugging."""
        try:
            context = {
                "platform": platform.platform(),
                "processor": platform.processor(),
                "cpu_count": os.cpu_count(),
                "env_vars": {
                    "PATH": os.environ.get("PATH", ""),
                    "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
                    "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV", ""),
                    "DEBUG_CONFIG": os.environ.get("DEBUG_CONFIG", "")
                }
            }
            
            # Add psutil info if available
            if PSUTIL_AVAILABLE:
                try:
                    context["memory_available"] = psutil.virtual_memory().available
                    context["memory_total"] = psutil.virtual_memory().total
                    context["disk_usage"] = psutil.disk_usage('/').percent
                except:
                    pass
                    
            return context
        except:
            return {"error": "Failed to capture system context"}
    
    def _update_summary(self, tool_name: str, error_type: str):
        """Update error summary statistics."""
        try:
            # Load existing summary
            if self.summary_log.exists():
                with open(self.summary_log, 'r') as f:
                    summary = json.load(f)
                
                # Ensure all required fields exist (handle corrupted/incomplete files)
                if "total_errors" not in summary:
                    summary["total_errors"] = 0
                if "by_tool" not in summary:
                    summary["by_tool"] = {}
                if "by_type" not in summary:
                    summary["by_type"] = {}
                if "first_error" not in summary:
                    summary["first_error"] = datetime.datetime.now().isoformat()
                if "last_error" not in summary:
                    summary["last_error"] = None
            else:
                summary = {
                    "total_errors": 0,
                    "by_tool": {},
                    "by_type": {},
                    "first_error": datetime.datetime.now().isoformat(),
                    "last_error": None
                }
            
            # Update counts
            summary["total_errors"] += 1
            summary["last_error"] = datetime.datetime.now().isoformat()
            
            # Update by tool
            if tool_name not in summary["by_tool"]:
                summary["by_tool"][tool_name] = {"count": 0, "types": {}}
            summary["by_tool"][tool_name]["count"] += 1
            
            # Update by type
            if error_type not in summary["by_type"]:
                summary["by_type"][error_type] = 0
            summary["by_type"][error_type] += 1
            
            # Update tool-specific error types
            tool_types = summary["by_tool"][tool_name]["types"]
            if error_type not in tool_types:
                tool_types[error_type] = 0
            tool_types[error_type] += 1
            
            # Save updated summary
            with open(self.summary_log, 'w') as f:
                json.dump(summary, f, indent=2)
                
        except Exception as e:
            print(f"Failed to update error summary: {e}", file=sys.stderr)
    
    def get_recent_errors(self, count: int = 10) -> list:
        """Get the most recent errors."""
        errors = []
        if self.error_log.exists():
            with open(self.error_log, 'r') as f:
                for line in f:
                    try:
                        errors.append(json.loads(line))
                    except:
                        pass
        
        return errors[-count:]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics."""
        if self.summary_log.exists():
            with open(self.summary_log, 'r') as f:
                return json.load(f)
        return {}

# Global logger instance
_logger = None

def get_logger(log_dir: Optional[str] = None) -> ErrorLogger:
    """Get or create the global error logger instance."""
    global _logger
    if _logger is None:
        _logger = ErrorLogger(log_dir)
    return _logger

def log_tool_error(tool_name: str):
    """
    Decorator to automatically log errors from tool main functions.
    
    Usage:
        @log_tool_error("my_tool")
        def main():
            # tool code
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SystemExit as e:
                # Don't log normal exits
                if e.code != 0:
                    logger = get_logger()
                    error_id = logger.log_error(
                        tool_name=tool_name,
                        error_type="SystemExit",
                        error_message=f"Exit code: {e.code}",
                        command_args=sys.argv[1:],
                        stack_trace=traceback.format_exc()
                    )
                    print(f"\nError logged with ID: {error_id}", file=sys.stderr)
                    print(f"Log location: {logger.error_log}", file=sys.stderr)
                raise
            except Exception as e:
                logger = get_logger()
                error_id = logger.log_error(
                    tool_name=tool_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    command_args=sys.argv[1:],
                    stack_trace=traceback.format_exc()
                )
                print(f"\nError logged with ID: {error_id}", file=sys.stderr)
                print(f"Log location: {logger.error_log}", file=sys.stderr)
                raise
        return wrapper
    return decorator

def log_error_context(tool_name: str, **context):
    """
    Context manager to log errors with additional context.
    
    Usage:
        with log_error_context("my_tool", file_path=path, operation="read"):
            # code that might fail
    """
    class ErrorContext:
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                logger = get_logger()
                error_id = logger.log_error(
                    tool_name=tool_name,
                    error_type=exc_type.__name__,
                    error_message=str(exc_val),
                    command_args=sys.argv[1:],
                    stack_trace=traceback.format_exc(),
                    additional_context=context
                )
                print(f"\nError logged with ID: {error_id}", file=sys.stderr)
                print(f"Log location: {logger.error_log}", file=sys.stderr)
            return False  # Don't suppress the exception
    
    return ErrorContext()

if __name__ == "__main__":
    # Test the error logger
    logger = get_logger()
    
    # Simulate an error
    error_id = logger.log_error(
        tool_name="test_tool",
        error_type="TestError", 
        error_message="This is a test error",
        command_args=["--test", "arg1", "arg2"],
        stack_trace="Test stack trace\nLine 2\nLine 3",
        additional_context={"test_key": "test_value"}
    )
    
    print(f"Test error logged with ID: {error_id}")
    print(f"Log location: {logger.error_log}")
    
    # Show summary
    summary = logger.get_error_summary()
    print("\nError Summary:")
    print(json.dumps(summary, indent=2))
    
    # Show recent errors
    recent = logger.get_recent_errors(5)
    print(f"\nLast {len(recent)} errors:")
    for error in recent:
        print(f"  - {error['timestamp']}: {error['tool_name']} - {error['error_message']}")