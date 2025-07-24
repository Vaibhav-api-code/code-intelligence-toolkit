#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Diagnostic script to identify parsing issues in show_structure_ast_v4.py

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import os
import argparse
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

def diagnose_file(filepath):
    """Diagnose potential issues with a file"""
    print(f"🔍 Diagnosing file: {filepath}")
    
    # Check file existence
    path = Path(filepath)
    if not path.exists():
        print(f"❌ File does not exist: {filepath}")
        return False
    
    print(f"✅ File exists")
    
    # Check file size
    size = path.stat().st_size
    print(f"📏 File size: {size:,} bytes ({size/1024:.1f} KB)")
    
    # Check file permissions
    if not path.is_file():
        print(f"❌ Not a regular file")
        return False
    
    if not os.access(filepath, os.R_OK):
        print(f"❌ File is not readable")
        return False
    
    print(f"✅ File is readable")
    
    # Check file extension
    suffix = path.suffix.lower()
    print(f"📝 File extension: {suffix}")
    
    supported_extensions = ['.py', '.java', '.js', '.jsx', '.ts', '.tsx']
    if suffix not in supported_extensions:
        print(f"❌ Unsupported file type. Supported: {', '.join(supported_extensions)}")
        return False
    
    print(f"✅ Supported file type")
    
    # Try to read file content
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"❌ Unicode decode error - file might have encoding issues")
        try:
            with open(filepath, 'r', encoding='latin1') as f:
                content = f.read()
            print(f"⚠️  File readable with latin1 encoding")
        except Exception as e:
            print(f"❌ Cannot read file with any encoding: {e}")
            return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    print(f"✅ File content readable")
    print(f"📊 Content length: {len(content):,} characters")
    print(f"📊 Line count: {content.count(chr(10)) + 1:,}")
    
    # Check if file is empty
    if not content.strip():
        print(f"❌ File is empty or contains only whitespace")
        return False
    
    # Check for basic code patterns
    if suffix == '.java':
        if 'class ' not in content and 'interface ' not in content and 'enum ' not in content:
            print(f"⚠️  No class/interface/enum declarations found")
        else:
            print(f"✅ Java code patterns detected")
    
    # Check for syntax issues (basic)
    if suffix == '.java':
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            print(f"⚠️  Brace mismatch: {open_braces} open, {close_braces} close")
        else:
            print(f"✅ Brace count balanced")
    
    # Show first few lines for context
    lines = content.split('\n')
    print(f"\n📋 First 5 lines of file:")
    for i, line in enumerate(lines[:5], 1):
        print(f"  {i:2d}: {line}")
    
    if len(lines) > 10:
        print(f"  ... ({len(lines) - 10} more lines)")
        print(f"📋 Last 5 lines of file:")
        for i, line in enumerate(lines[-5:], len(lines) - 4):
            print(f"  {i:2d}: {line}")
    
    return True

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Diagnostic tool to identify parsing issues in source files. "
                    "Checks file existence, readability, encoding, syntax, and structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s MyClass.java       - Diagnose a Java file
  %(prog)s script.py          - Diagnose a Python file
  %(prog)s component.jsx      - Diagnose a JavaScript file
        """
    )
    
    # Add positional argument for file path
    parser.add_argument(
        'file_path',
        help='Path to the source file to diagnose'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    filepath = args.file_path
    
    print("🔧 Parsing Issue Diagnostic Tool")
    print("=" * 50)
    
    success = diagnose_file(filepath)
    
    if success:
        print(f"\n✅ File appears to be valid for parsing")
        print(f"💡 Try running with --verbose flag to see detailed parsing errors")
    else:
        print(f"\n❌ File has issues that may prevent parsing")
        print(f"💡 Address the issues above and try again")

if __name__ == '__main__':
    main()