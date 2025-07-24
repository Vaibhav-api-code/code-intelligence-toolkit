#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Wrapper to run Python tools with automatic error logging.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import subprocess
import json
import traceback
from pathlib import Path
from error_logger import get_logger
import argparse

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

def run_tool_with_logging(tool_path: str, args: list):
    """Run a Python tool with error logging enabled."""
    tool_name = Path(tool_path).name
    logger = get_logger()
    
    # Build command
    cmd = [sys.executable, tool_path] + args
    
    try:
        # Run the tool
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False  # Don't raise on non-zero exit
        )
        
        # Check for errors
        if result.returncode != 0:
            # Log the error
            error_id = logger.log_error(
                tool_name=tool_name,
                error_type="SubprocessError",
                error_message=f"Tool exited with code {result.returncode}",
                command_args=args,
                stack_trace=result.stderr,
                additional_context={
                    "stdout": result.stdout[-1000:] if result.stdout else None,  # Last 1000 chars
                    "stderr": result.stderr[-1000:] if result.stderr else None,
                    "exit_code": result.returncode
                }
            )
            
            # Print original stderr
            if result.stderr:
                print(result.stderr, file=sys.stderr, end='')
            
            # Add error logging info
            print(f"\n[Error logged with ID: {error_id}]", file=sys.stderr)
            print(f"[View errors: python analyze_errors.py --recent 5]", file=sys.stderr)
            
            # Exit with same code
            sys.exit(result.returncode)
        else:
            # Success - print stdout normally
            if result.stdout:
                print(result.stdout, end='')
                
    except FileNotFoundError:
        error_id = logger.log_error(
            tool_name=tool_name,
            error_type="FileNotFoundError",
            error_message=f"Tool not found: {tool_path}",
            command_args=args,
            stack_trace=traceback.format_exc()
        )
        print(f"Error: Tool not found: {tool_path}", file=sys.stderr)
        print(f"[Error logged with ID: {error_id}]", file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:
        error_id = logger.log_error(
            tool_name=tool_name,
            error_type=type(e).__name__,
            error_message=str(e),
            command_args=args,
            stack_trace=traceback.format_exc()
        )
        print(f"Error running tool: {e}", file=sys.stderr)
        print(f"[Error logged with ID: {error_id}]", file=sys.stderr)
        sys.exit(1)

def main():
    """Main entry point."""
    # Simple approach: first argument is tool path, rest are tool args
    if len(sys.argv) < 2:
        print("Usage: run_with_error_logging.py <tool_path> [tool_args...]", file=sys.stderr)
        sys.exit(1)
    
    tool_path = sys.argv[1]
    tool_args = sys.argv[2:]
    
    # Handle help for the wrapper itself
    if tool_path in ['-h', '--help']:
        print("""Run Python tools with automatic error logging.

Usage: run_with_error_logging.py <tool_path> [tool_args...]

Examples:
  run_with_error_logging.py find_text.py "pattern" --file MyClass.java
  run_with_error_logging.py analyze_errors.py --recent 10
  run_with_error_logging.py replace_text.py "old" "new" file.py
""")
        sys.exit(0)
    
    run_tool_with_logging(tool_path, tool_args)

if __name__ == "__main__":
    main()