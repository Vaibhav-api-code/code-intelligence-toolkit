#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Quick fix script for syntax errors introduced during mass standardization.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import re
import sys
from pathlib import Path

def fix_file(file_path):
    """Fix common syntax errors in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixed = False
        
        # Fix escaped quotes in create_parser calls
        content = re.sub(r"create_parser\(\\'([^']+)\\'", r"create_parser('\1'", content)
        if content != original_content:
            fixed = True
            print(f"Fixed escaped quotes in: {file_path}")
        
        # Fix broken main function structure where help text got merged into code
        patterns_to_remove = [
            r'\s*# Rename a class with dry-run preview\s*\n\s*%\(prog\)s.*?src/.*?\n',
            r'\s*# Find all references to an identifier\s*\n\s*%\(prog\)s.*?src/.*?\n',
            r'\s*# Analyze a Python file\'s structure\s*\n\s*%\(prog\)s.*?file\.py.*?\n',
            r'\s*organize_files\.py.*?# Organize by.*?\n',
            r'\s*%\(prog\)s.*?\n',
        ]
        
        for pattern in patterns_to_remove:
            old_content = content
            content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
            if content != old_content:
                fixed = True
                print(f"Removed help text fragments from: {file_path}")
        
        # Fix incomplete if-else blocks
        content = re.sub(
            r'(\s+)else:\s*\n\s*# Fallback parser\s*\n\s*if HAS_STANDARD_PARSER:\s*\n.*?\)\s*\n\s*\)\s*\n\s*else:\s*\n\s*parser = argparse\.ArgumentParser.*?\)\s*\n',
            r'\1else:\n\1    parser = argparse.ArgumentParser(description=description)\n',
            content,
            flags=re.MULTILINE | re.DOTALL
        )
        
        if content != original_content and fixed:
            # Write the fixed content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False
    
    return False

def main():
    """Fix syntax errors in Python files."""
    fixed_files = []
    
    # Find all Python files in current directory
    python_files = list(Path('.').glob('*.py'))
    
    for file_path in python_files:
        if fix_file(file_path):
            fixed_files.append(file_path)
    
    print(f"\nFixed {len(fixed_files)} files:")
    for file_path in fixed_files:
        print(f"  - {file_path}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())