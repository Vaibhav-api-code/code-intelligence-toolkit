#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Fix remaining syntax errors in standardized files.

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

def fix_file_structure(file_path):
    """Fix major structural issues in Python files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix ast_refactor.py - has corrupted help text
        if 'ast_refactor.py' in str(file_path):
            # Remove the broken help text that got merged into the code
            content = re.sub(
                r'(parser = argparse\.ArgumentParser\([^)]+\))([^"]*?)TRANSFORM TYPES:.*?attribute  - Attribute access.*?\n',
                r'\1\n    ',
                content,
                flags=re.DOTALL
            )
            
        # Fix organize_files.py - has broken parser line
        elif 'organize_files.py' in str(file_path):
            content = re.sub(
                r'(parser = argparse\.ArgumentParser\([^)]+\))\s+organize_files\.py.*?\n',
                r'\1\n    ',
                content
            )
            
        # Fix pattern_analysis.py - has similar issues
        elif 'pattern_analysis.py' in str(file_path):
            content = re.sub(
                r'(parser = argparse\.ArgumentParser\([^)]+\))s.*?\n',
                r'\1\n    ',
                content
            )
            
        # Fix java_scope_refactor.py
        elif 'java_scope_refactor.py' in str(file_path):
            content = re.sub(
                r'(parser = argparse\.ArgumentParser\([^)]+\))s.*?\n',
                r'\1\n    ',
                content
            )
        
        # Generic fix for bullet points
        content = re.sub(r'^\s*[•●]\s+.*?\n', '', content, flags=re.MULTILINE)
        
        # Generic fix for orphaned help text
        content = re.sub(r'\s*(formatter_class=argparse\.RawDescriptionHelpFormatter\s*\)\s*)+', 
                        '\n        formatter_class=argparse.RawDescriptionHelpFormatter\n    )', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False
    
    return False

def main():
    """Fix remaining syntax errors."""
    fixed_files = []
    
    # List of problematic files
    problem_files = [
        'ast_refactor.py',
        'organize_files.py', 
        'pattern_analysis.py',
        'java_scope_refactor.py'
    ]
    
    for filename in problem_files:
        file_path = Path(filename)
        if file_path.exists():
            if fix_file_structure(file_path):
                fixed_files.append(file_path)
                print(f"Fixed {file_path}")
    
    if fixed_files:
        print(f"\nFixed {len(fixed_files)} files with structural issues")
    else:
        print("No files needed fixing")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())