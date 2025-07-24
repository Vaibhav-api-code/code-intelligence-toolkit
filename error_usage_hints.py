#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced error wrapper that provides usage hints when tools fail.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import subprocess
from pathlib import Path

# Common error patterns and their solutions

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

ERROR_HINTS = {
    "navigate_ast.py": {
        "unrecognized arguments": """
HINT: navigate_ast.py usage:
  navigate_ast.py <file> <target_name> [options]
  navigate_ast.py <file> --find <target_name> [options]
  
Example: navigate_ast.py MyClass.java calculateValue --target-type method
""",
    },
    "method_analyzer_ast.py": {
        "unrecognized arguments": """
HINT: method_analyzer_ast.py expects just the method name, not a file path.
Usage: method_analyzer_ast.py <method_name> [options]

Example: method_analyzer_ast.py calculateValue --scope src/ --trace-flow
""",
    },
    "replace_text_ast.py": {
        "unrecognized arguments": """
HINT: replace_text_ast.py usage for AST renaming:
  replace_text_ast.py --ast-rename <file> <old_name> <new_name> --line <line_number>
  
Example: replace_text_ast.py --ast-rename utils.py old_var new_var --line 42
""",
    },
    "find_text.py": {
        "-F": """
HINT: The -F flag is not valid. Did you mean:
  --in-files     Search within file contents
  -f, --files    Limit search to specific files
  
Example: find_text.py "pattern" --in-files -g "*.java"
""",
    },
    "extract_methods.py": {
        "Tool exited with code 1": """
HINT: extract_methods.py extracts entire methods from files.
Usage: extract_methods.py <file> <method_name>

Make sure:
1. The file path is correct
2. The method name exists in the file
3. For large files, consider using --list first to see available methods
""",
    },
}

def get_error_hint(tool_name: str, error_output: str) -> str:
    """Get helpful hint based on tool and error."""
    if tool_name in ERROR_HINTS:
        for pattern, hint in ERROR_HINTS[tool_name].items():
            if pattern in error_output:
                return hint
    return ""

def wrap_with_hints(tool_path: str, args: list) -> int:
    """Run tool and provide hints on error."""
    tool_name = Path(tool_path).name
    
    # Run the tool
    result = subprocess.run(
        [sys.executable, tool_path] + args,
        capture_output=True,
        text=True
    )
    
    # Print stdout
    if result.stdout:
        print(result.stdout, end='')
    
    # Handle errors with hints
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr, end='')
        
        # Add helpful hint
        hint = get_error_hint(tool_name, result.stderr or str(args))
        if hint:
            print(f"\n{hint}", file=sys.stderr)
    
    return result.returncode

if __name__ == "__main__":
    # Check for help flag
    if len(sys.argv) == 2 and sys.argv[1] in ['--help', '-h']:
        print("""usage: error_usage_hints.py [-h] <tool_path> [args...]

Enhanced error wrapper that provides usage hints when tools fail.

This tool runs other Python tools and provides helpful error messages
and usage hints when they fail with common errors.

positional arguments:
  tool_path    Path to the Python tool to run
  args         Arguments to pass to the tool

optional arguments:
  -h, --help   show this help message and exit

Examples:
  error_usage_hints.py navigate_ast.py MyClass.java calculateValue
  error_usage_hints.py find_text.py "pattern" --file config.py
  error_usage_hints.py trace_calls.py processData --scope src/

The wrapper will intercept common errors and provide helpful hints
for fixing them based on the specific tool being run.""")
        sys.exit(0)
    
    if len(sys.argv) < 2:
        print("Usage: error_usage_hints.py <tool_path> [args...]", file=sys.stderr)
        print("Try 'error_usage_hints.py --help' for more information.", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(wrap_with_hints(sys.argv[1], sys.argv[2:]))