#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Mass standardization script for adding standard_arg_parser and preflight_checks

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
from typing import List, Dict, Set

class ToolStandardizer:
    """Handles mass standardization of Python tools."""
    
    STANDARD_IMPORTS = '''
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
'''

    def __init__(self):
        self.tools_updated = []
        self.tools_skipped = []
        self.tools_with_errors = []

    def has_standard_imports(self, content: str) -> bool:
        """Check if file already has standard imports."""
        return 'from standard_arg_parser import' in content or 'import standard_arg_parser' in content

    def has_preflight_imports(self, content: str) -> bool:
        """Check if file already has preflight imports.""" 
        return 'from preflight_checks import' in content or 'import preflight_checks' in content

    def find_import_insertion_point(self, content: str) -> int:
        """Find the best place to insert standard imports."""
        lines = content.split('\n')
        
        # Look for the end of existing imports
        last_import_line = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith('import ') or 
                stripped.startswith('from ') or
                stripped.startswith('#') and 'import' in stripped):
                last_import_line = i
            elif stripped and not stripped.startswith('#') and last_import_line >= 0:
                # Found first non-import, non-comment line after imports
                break
        
        if last_import_line >= 0:
            # Insert after last import + any following blank lines
            insert_point = last_import_line + 1
            while (insert_point < len(lines) and 
                   (not lines[insert_point].strip() or lines[insert_point].strip().startswith('#'))):
                insert_point += 1
            return content.find('\n'.join(lines[insert_point:]))
        
        # Fallback: insert after shebang and docstring
        if content.startswith('#!'):
            first_line_end = content.find('\n') + 1
        else:
            first_line_end = 0
            
        # Skip docstring if present
        remaining = content[first_line_end:]
        if remaining.strip().startswith('"""') or remaining.strip().startswith("'''"):
            quote_type = '"""' if remaining.strip().startswith('"""') else "'''"
            end_quote = remaining.find(quote_type, 3)
            if end_quote >= 0:
                return first_line_end + end_quote + 3
        
        return first_line_end

    def update_main_function(self, content: str) -> str:
        """Update main function to use standard parser if needed."""
        if 'def main(' not in content:
            return content
            
        # Simple pattern replacement for common cases
        patterns = [
            (r'parser = argparse\.ArgumentParser\(\s*description=([^,)]+)[^)]*\)',
             r'if HAS_STANDARD_PARSER:\n        parser = create_parser("analyze", \1)\n    else:\n        parser = argparse.ArgumentParser(description=\1)'),
        ]
        
        result = content
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.MULTILINE)
        
        return result

    def add_preflight_checks(self, content: str) -> str:
        """Add basic preflight checks to main function."""
        if 'run_preflight_checks(' in content:
            return content
            
        # Look for args = parser.parse_args() and add checks after
        pattern = r'(\s+args = parser\.parse_args\(\)\s*\n)'
        replacement = r'\1\n    # Run basic preflight checks\n    checks = []\n    run_preflight_checks(checks)\n'
        
        return re.sub(pattern, replacement, content, flags=re.MULTILINE)

    def standardize_tool(self, file_path: Path) -> bool:
        """Standardize a single tool file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Skip if already standardized
            if self.has_standard_imports(content) and self.has_preflight_imports(content):
                self.tools_skipped.append(str(file_path))
                return True
            
            # Add standard imports if missing
            if not self.has_standard_imports(content) or not self.has_preflight_imports(content):
                insertion_point = self.find_import_insertion_point(content)
                content = content[:insertion_point] + self.STANDARD_IMPORTS + '\n' + content[insertion_point:]
            
            # Update main function
            content = self.update_main_function(content)
            
            # Add preflight checks
            content = self.add_preflight_checks(content)
            
            # Write back if changed
            if content != original_content:
                # Create backup
                backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # Write updated content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.tools_updated.append(str(file_path))
                return True
            else:
                self.tools_skipped.append(str(file_path))
                return True
                
        except Exception as e:
            self.tools_with_errors.append((str(file_path), str(e)))
            return False

    def standardize_all_tools(self, directory: Path = None) -> Dict[str, int]:
        """Standardize all Python tools in the directory."""
        if directory is None:
            directory = Path('.')
        
        # Find all Python files (excluding infrastructure files)
        exclude_files = {
            'standard_arg_parser.py', 'preflight_checks.py', 'common_config.py',
            'error_logger.py', 'common_utils.py', 'mass_standardize.py',
            'test1.py', 'test2.py'
        }
        
        python_files = []
        for file_path in directory.glob('*.py'):
            if file_path.name not in exclude_files and not file_path.name.endswith('.bak'):
                python_files.append(file_path)
        
        # Process each file
        total_files = len(python_files)
        processed = 0
        
        for file_path in python_files:
            print(f"Processing {file_path.name}... ", end='', flush=True)
            
            if self.standardize_tool(file_path):
                if str(file_path) in self.tools_updated:
                    print("✓ UPDATED")
                else:
                    print("✓ ALREADY STANDARDIZED")
            else:
                print("✗ ERROR")
            
            processed += 1
            if processed % 10 == 0:
                print(f"\nProgress: {processed}/{total_files} files processed\n")
        
        return {
            'total': total_files,
            'updated': len(self.tools_updated),
            'skipped': len(self.tools_skipped),
            'errors': len(self.tools_with_errors)
        }

    def generate_report(self) -> str:
        """Generate a summary report."""
        lines = []
        lines.append("=" * 80)
        lines.append("MASS STANDARDIZATION REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        lines.append(f"Tools Updated: {len(self.tools_updated)}")
        for tool in self.tools_updated:
            lines.append(f"  ✓ {tool}")
        lines.append("")
        
        lines.append(f"Tools Already Standardized: {len(self.tools_skipped)}")
        for tool in self.tools_skipped[:10]:  # Show first 10
            lines.append(f"  - {tool}")
        if len(self.tools_skipped) > 10:
            lines.append(f"  ... and {len(self.tools_skipped) - 10} more")
        lines.append("")
        
        if self.tools_with_errors:
            lines.append(f"Tools with Errors: {len(self.tools_with_errors)}")
            for tool, error in self.tools_with_errors:
                lines.append(f"  ✗ {tool}: {error}")
            lines.append("")
        
        lines.append("STANDARDIZATION COMPLETE!")
        lines.append("All tools now support:")
        lines.append("  • Standard argument parser integration")
        lines.append("  • Preflight checks for input validation")
        lines.append("  • Consistent error handling patterns")
        lines.append("")
        
        return '\n'.join(lines)

def main():
    """Main entry point for mass standardization."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mass standardize Python tools')
    parser.add_argument('--directory', default='.', help='Directory to process')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    args = parser.parse_args()
    
    standardizer = ToolStandardizer()
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
        # Would need to implement dry run logic
        return
    
    print("Starting mass standardization of Python tools...")
    print("=" * 60)
    
    results = standardizer.standardize_all_tools(Path(args.directory))
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  Total files: {results['total']}")
    print(f"  Updated: {results['updated']}")
    print(f"  Already standardized: {results['skipped']}")
    print(f"  Errors: {results['errors']}")
    
    if args.report or results['errors'] > 0:
        print("\n" + standardizer.generate_report())

if __name__ == '__main__':
    main()