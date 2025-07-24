#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Migration script to update Python tools to use configuration for paths

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
import argparse

# Patterns to find and replace

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

PATTERNS_TO_REPLACE = [
    # Pattern for --scope with default='src/'
    (r"(parser\.add_argument\s*\(\s*['\"]--scope['\"].*?default\s*=\s*)['\"]src/['\"]",
     r"\1'.'"),
    
    # Update help text that mentions src/
    (r"(help\s*=\s*['\"].*?)\(default:\s*src/\)(['\"])",
     r"\1(default: current directory)\2"),
     
    # Pattern for default source paths
    (r"DEFAULT_SOURCE\s*=\s*['\"]src/['\"]",
     r"DEFAULT_SOURCE = '.'"),
]

# Files to skip (already use config or are examples)
SKIP_FILES = {
    'common_config.py',
    'analyze_dependencies_rg_configurable.py',
    'migrate_to_config_paths.py',
    '.pytoolsrc.sample'
}

def backup_file(filepath, backup_dir=None):
    """Create a backup of the file before modifying."""
    if backup_dir:
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        # Preserve relative path structure in backup
        relative_parts = filepath.parts[-2:] if len(filepath.parts) > 1 else filepath.parts
        backup_path = backup_dir / '_'.join(relative_parts)
        backup_path = backup_path.with_suffix(filepath.suffix + '.bak')
    else:
        backup_path = filepath.with_suffix(filepath.suffix + '.bak')
    shutil.copy2(filepath, backup_path)
    return backup_path

def check_has_config_import(content):
    """Check if file already imports config functions."""
    return 'from common_config import' in content or 'import common_config' in content

def add_config_import(content):
    """Add config import after other imports if not present."""
    if check_has_config_import(content):
        return content
    
    # Find the last import line
    import_pattern = re.compile(r'^(import |from .+ import )', re.MULTILINE)
    matches = list(import_pattern.finditer(content))
    
    if matches:
        last_import_end = matches[-1].end()
        # Add config import after last import
        config_import = """\n
# Import configuration support with fallback
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass
"""
        return content[:last_import_end] + config_import + content[last_import_end:]
    
    return content

def check_has_apply_config(content):
    """Check if file already calls apply_config_to_args."""
    return 'apply_config_to_args' in content

def add_apply_config_call(content, tool_name):
    """Add apply_config_to_args call after args parsing."""
    if check_has_apply_config(content):
        return content
    
    # Find args = parser.parse_args() pattern
    parse_pattern = re.compile(r'(\s*args\s*=\s*parser\.parse_args\(\)[^\n]*\n)')
    match = parse_pattern.search(content)
    
    if match:
        insert_pos = match.end()
        config_call = f"""    
    # Apply configuration after parsing arguments
    apply_config_to_args('{tool_name}', args, parser)
"""
        return content[:insert_pos] + config_call + content[insert_pos:]
    
    return content

def extract_tool_name(filepath):
    """Extract tool name from filename."""
    name = filepath.stem
    # Remove version suffixes like _v2, _rg
    name = re.sub(r'_v\d+$', '', name)
    name = re.sub(r'_rg$', '', name)
    return name

def process_file(filepath, dry_run=False, backup_dir=None):
    """Process a single Python file."""
    if filepath.name in SKIP_FILES:
        return False, "Skipped"
    
    try:
        content = filepath.read_text(encoding='utf-8')
        original_content = content
        
        # Check if file has hardcoded src/
        if 'default="src/"' not in content and "default='src/'" not in content:
            return False, "No hardcoded src/ found"
        
        # Apply replacements
        for pattern, replacement in PATTERNS_TO_REPLACE:
            content = re.sub(pattern, replacement, content)
        
        # Add config import if needed
        content = add_config_import(content)
        
        # Add apply_config call if needed
        tool_name = extract_tool_name(filepath)
        content = add_apply_config_call(content, tool_name)
        
        if content != original_content:
            if dry_run:
                return True, "Would update (dry run)"
            else:
                # Create backup
                backup_path = backup_file(filepath, backup_dir)
                
                # Write updated content
                filepath.write_text(content, encoding='utf-8')
                
                return True, f"Updated (backup: {backup_path.name})"
        else:
            return False, "No changes needed"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main migration function."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Migrate Python tools from hardcoded 'src/' paths to configuration-based paths. "
                    "This script updates Python files to use '.' as default and adds configuration support.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    
    parser.add_argument(
        '--backup-dir',
        type=str,
        help='Directory to store backup files (default: alongside original files)'
    )
    
    parser.add_argument(
        '--directory',
        type=str,
        default=None,
        help='Directory to scan for Python files (default: current script directory)'
    )
    
    args = parser.parse_args()
    
    # Determine directory to scan
    if args.directory:
        toolkit_dir = Path(args.directory).resolve()
    else:
        toolkit_dir = Path(__file__).parent
    
    print("Migration Script: Update hardcoded paths to use configuration")
    print("=" * 70)
    print(f"Scanning directory: {toolkit_dir}")
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
    if args.backup_dir:
        print(f"Backup directory: {args.backup_dir}")
    print()
    
    # Find all Python files
    python_files = list(toolkit_dir.glob("**/*.py"))
    
    updated_count = 0
    error_count = 0
    
    for filepath in sorted(python_files):
        # Skip files in certain directories
        if any(part in filepath.parts for part in ['.git', '__pycache__', 'build']):
            continue
            
        relative_path = filepath.relative_to(toolkit_dir)
        success, message = process_file(filepath, args.dry_run, args.backup_dir)
        
        if success:
            updated_count += 1
            print(f"✓ {relative_path}: {message}")
        elif "Error" in message:
            error_count += 1
            print(f"✗ {relative_path}: {message}")
        else:
            print(f"- {relative_path}: {message}")
    
    print()
    print("=" * 70)
    if args.dry_run:
        print(f"Summary (DRY RUN): {updated_count} files would be updated, {error_count} errors")
    else:
        print(f"Summary: {updated_count} files updated, {error_count} errors")
    
    if updated_count > 0 and not args.dry_run:
        print("\nNext steps:")
        print("1. Review the changes in the updated files")
        print("2. Test the modified tools to ensure they work correctly")
        print("3. Update .pytoolsrc with your project-specific paths")
        print("4. Remove backup files (*.bak) once verified")

if __name__ == "__main__":
    main()