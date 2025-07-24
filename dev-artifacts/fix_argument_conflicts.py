#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Fix argument conflicts by updating tools to use enhanced standard parser

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
from typing import Dict, List, Set

class ConflictResolver:
    """Resolves argument conflicts in Python tools."""
    
    # Arguments that should be removed from individual tools (provided by standard parser)
    STANDARD_ARGS_TO_REMOVE = {
        '--verbose', '-v', '--quiet', '-q', '--json', '--dry-run',
        '--file', '--scope', '--type', '--ignore-case', '-i',
        '--context', '-C', '--after-context', '-A', '--before-context', '-B',
        '--recursive', '-r', '--max-depth', '--show-callers', '--show-callees',
        '--include', '--glob', '-g', '--exclude', '--whole-word', '-w',
        '--long', '-l', '--all', '-a', '--sort'
    }
    
    # Tools that need to use enhanced parser instead of standard parser
    TOOLS_NEED_ENHANCED_PARSER = [
        'find_text.py', 'find_text_v4.py', 'pattern_analysis.py',
        'organize_files.py', 'cross_file_analysis_ast.py',
        'method_analyzer_ast_v2.py', 'smart_ls.py', 'dir_stats.py',
        'tree_view.py', 'find_files.py'
    ]
    
    def __init__(self):
        self.fixed_files = []
        self.errors = []
    
    def remove_conflicting_arguments(self, file_path: Path) -> bool:
        """Remove argument definitions that conflict with standard parser."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Remove add_argument calls for standard arguments
            for std_arg in self.STANDARD_ARGS_TO_REMOVE:
                # Pattern to match add_argument calls with this flag
                patterns = [
                    # Single quotes
                    rf"parser\.add_argument\(\s*'{re.escape(std_arg)}'[^)]*\)\s*\n?",
                    # Double quotes
                    rf'parser\.add_argument\(\s*"{re.escape(std_arg)}"[^)]*\)\s*\n?',
                    # Multi-line with single quotes
                    rf"parser\.add_argument\(\s*'{re.escape(std_arg)}'[^)]*?\n[^)]*\)\s*\n?",
                    # Multi-line with double quotes
                    rf'parser\.add_argument\(\s*"{re.escape(std_arg)}"[^)]*?\n[^)]*\)\s*\n?',
                    # Lines that start with the flag (continuation lines)
                    rf"\s*'{re.escape(std_arg)}'[^,\n]*,?\s*\n",
                    rf'\s*"{re.escape(std_arg)}"[^,\n]*,?\s*\n'
                ]
                
                for pattern in patterns:
                    content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove empty argument group additions
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
        except Exception as e:
            self.errors.append(f"Error processing {file_path}: {e}")
            return False
        
        return False
    
    def update_parser_import(self, file_path: Path) -> bool:
        """Update tools to use enhanced parser where needed."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            if file_path.name in self.TOOLS_NEED_ENHANCED_PARSER:
                # Update import to use enhanced parser
                content = re.sub(
                    r'from standard_arg_parser import create_standard_parser as create_parser',
                    'from enhanced_standard_arg_parser import create_standard_parser as create_parser',
                    content
                )
                
                # Update specific parser creation calls for different tool types
                if file_path.name in ['find_text.py', 'find_text_v4.py']:
                    content = re.sub(
                        r'create_parser\(\'search\'',
                        'create_search_parser(',
                        content
                    )
                    content = re.sub(
                        r'from enhanced_standard_arg_parser import create_standard_parser as create_parser',
                        'from enhanced_standard_arg_parser import create_search_parser as create_parser',
                        content
                    )
                
                elif file_path.name in ['method_analyzer_ast_v2.py', 'cross_file_analysis_ast.py']:
                    content = re.sub(
                        r'create_parser\(\'analyze\'',
                        'create_analyze_parser(',
                        content
                    )
                    content = re.sub(
                        r'from enhanced_standard_arg_parser import create_standard_parser as create_parser',
                        'from enhanced_standard_arg_parser import create_analyze_parser as create_parser',
                        content
                    )
                
                elif file_path.name in ['smart_ls.py', 'dir_stats.py', 'tree_view.py', 'find_files.py']:
                    content = re.sub(
                        r'create_parser\(\'analyze\'',
                        'create_directory_parser(',
                        content
                    )
                    content = re.sub(
                        r'from enhanced_standard_arg_parser import create_standard_parser as create_parser',
                        'from enhanced_standard_arg_parser import create_directory_parser as create_parser',
                        content
                    )
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
        except Exception as e:
            self.errors.append(f"Error updating parser import for {file_path}: {e}")
            return False
        
        return False
    
    def fix_tool(self, file_path: Path) -> bool:
        """Fix a single tool by removing conflicts and updating parser."""
        fixed = False
        
        # Remove conflicting arguments
        if self.remove_conflicting_arguments(file_path):
            fixed = True
            print(f"✓ Removed conflicting arguments from {file_path.name}")
        
        # Update parser imports
        if self.update_parser_import(file_path):
            fixed = True
            print(f"✓ Updated parser import for {file_path.name}")
        
        return fixed
    
    def fix_all_tools(self) -> None:
        """Fix all Python tools in the current directory."""
        print("🔧 Fixing argument conflicts across all tools")
        print("=" * 60)
        
        python_files = list(Path('.').glob('*.py'))
        
        # Skip utility files
        skip_files = {
            'standard_arg_parser.py', 'enhanced_standard_arg_parser.py',
            'analyze_conflicts.py', 'fix_argument_conflicts.py',
            'fix_syntax_errors.py', 'fix_remaining_syntax.py'
        }
        
        for file_path in python_files:
            if file_path.name in skip_files:
                continue
            
            if self.fix_tool(file_path):
                self.fixed_files.append(file_path.name)
        
        print(f"\n📊 Summary:")
        print(f"  Fixed files: {len(self.fixed_files)}")
        if self.errors:
            print(f"  Errors: {len(self.errors)}")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"    - {error}")
        
        if self.fixed_files:
            print(f"\n✅ Fixed files:")
            for filename in sorted(self.fixed_files):
                print(f"  - {filename}")


def main():
    """Fix all argument conflicts."""
    resolver = ConflictResolver()
    resolver.fix_all_tools()
    
    print(f"\n🎯 Next steps:")
    print("1. Test key tools to ensure they work correctly")
    print("2. Update any remaining tools that have specific conflicts")
    print("3. Consider updating documentation with new argument patterns")
    
    return len(resolver.errors)

if __name__ == '__main__':
    errors = main()
    sys.exit(1 if errors > 0 else 0)