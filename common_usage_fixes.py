#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Common usage fixes for Python tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import re
from pathlib import Path

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

def suggest_find_text_fix(args):
    """Suggest fixes for common find_text.py mistakes."""
    suggestions = []
    
    # Check for -F flag (doesn't exist)
    if '-F' in args:
        suggestions.append("The -F flag doesn't exist. Did you mean '--in-files' to search within files?")
        args = [arg for arg in args if arg != '-F']
    
    # Check for file path after --in-files without --path
    if '--in-files' in args:
        for i, arg in enumerate(args):
            if (not arg.startswith('-') and 
                (arg.endswith('.java') or arg.endswith('.py') or '/' in arg) and
                i > 0 and args[i-1] not in ['--path', '-g']):
                suggestions.append(f"To search in a specific file, use: --path {arg}")
                suggestions.append(f"Or to search in all {Path(arg).suffix} files, use: -g '*{Path(arg).suffix}'")
    
    # Check for patterns with special characters that need --regex
    pattern = args[0] if args and not args[0].startswith('-') else None
    if pattern and any(char in pattern for char in ['|', '.*', '+', '?', '[', ']', '(', ')']):
        if '--regex' not in args:
            suggestions.append("Your pattern contains regex characters. Add '--regex' flag.")
    
    return suggestions

def suggest_extract_methods_fix(args):
    """Suggest fixes for extract_methods.py usage."""
    suggestions = []
    
    if '--help' in args:
        return []  # Help is valid
    
    if len(args) < 2:
        suggestions.append("Usage: extract_methods.py <file> <method_name>")
        suggestions.append("Or: extract_methods.py <file> --list")
    elif len(args) == 1:
        suggestions.append("Missing method name. Either provide a method name or use --list")
        suggestions.append(f"Example: extract_methods.py {args[0]} initialize")
    
    return suggestions

def suggest_method_analyzer_ast_fix(args):
    """Suggest fixes for method_analyzer_ast.py usage."""
    suggestions = []
    
    # Check if file path is provided instead of method name
    if args and (args[0].endswith('.java') or args[0].endswith('.py') or '/' in args[0]):
        suggestions.append("method_analyzer_ast.py expects a method name, not a file path")
        suggestions.append(f"Usage: method_analyzer_ast.py <method_name> [options]")
        suggestions.append(f"Example: method_analyzer_ast.py processData --scope src/")
    
    return suggestions

def suggest_navigate_ast_fix(args):
    """Suggest fixes for navigate_ast.py usage."""
    suggestions = []
    
    # Check for old --find syntax
    if '--find' in args and 'navigate_ast.py' in ' '.join(sys.argv):
        # This is fixed in newer version
        suggestions.append("Update: navigate_ast.py now supports --find flag")
        suggestions.append("Make sure you're using the latest version")
    
    return suggestions

def suggest_replace_text_ast_fix(args):
    """Suggest fixes for replace_text_ast.py usage."""
    suggestions = []
    
    # Check for AST rename without proper flags
    if len(args) >= 3 and not any(arg.startswith('--') for arg in args[:3]):
        suggestions.append("For AST-based renaming, use: --ast-rename <file> <old_name> <new_name> --line <line_number>")
        suggestions.append(f"Example: replace_text_ast.py --ast-rename {args[0]} old_var new_var --line 42")
    
    return suggestions

def main():
    """Analyze command and suggest fixes."""
    if len(sys.argv) < 2:
        print("Usage: common_usage_fixes.py <tool_name> [args...]")
        return
    
    tool = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    suggestions = []
    
    if 'find_text' in tool:
        suggestions = suggest_find_text_fix(args)
    elif 'extract_methods' in tool:
        suggestions = suggest_extract_methods_fix(args)
    elif 'method_analyzer_ast' in tool:
        suggestions = suggest_method_analyzer_ast_fix(args)
    elif 'navigate_ast' in tool:
        suggestions = suggest_navigate_ast_fix(args)
    elif 'replace_text_ast' in tool:
        suggestions = suggest_replace_text_ast_fix(args)
    
    if suggestions:
        print("\n=== USAGE SUGGESTIONS ===")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
        print()

if __name__ == "__main__":
    main()