#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced AST refactoring tool that leverages rope when available.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import ast
import sys
import os
import time
import errno
import tempfile
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import subprocess

# Try to import rope for advanced refactoring

# Import standard argument parser
try:
    from standard_arg_parser import create_standard_parser as create_parser
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False
    
    def create_parser(tool_type, description):
        return argparse.ArgumentParser(description=description)

# Import atomic write from common_utils
try:
    from common_utils import atomic_write
    HAS_ATOMIC_WRITE = True
except ImportError:
    HAS_ATOMIC_WRITE = False

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

try:
    from rope.base.project import Project
    from rope.refactor.rename import Rename
    from rope.base.exceptions import RopeError
    ROPE_AVAILABLE = True
except ImportError:
    ROPE_AVAILABLE = False

# Keep existing AST functionality
try:
    import astor
    ASTOR_AVAILABLE = True
except ImportError:
    ASTOR_AVAILABLE = False

# Import our existing AST classes
from ast_refactor import (
    PythonASTAnalyzer, 
    PythonASTTransformer,
    ASTRefactoring
)

class RopeBackend:
    """Production-ready refactoring using rope library."""
    
    def __init__(self, project_path: str = "."):
        self.project = Project(project_path)
        self.project_path = Path(project_path).resolve()
    
    def rename_symbol(self, file_path: Path, old_name: str, new_name: str, 
                     transform_type: str = 'all', offset: Optional[int] = None) -> tuple[str, int]:
        """
        Rename symbol with full scope awareness using rope.
        
        Returns:
            Tuple of (new_content, changes_count)
        """
        try:
            # Get resource from rope
            from rope.base import libutils
            resource = libutils.path_to_resource(self.project, str(file_path))
            
            content = resource.read()
            
            # If no offset provided, find first occurrence of the name
            if offset is None:
                # Find the appropriate occurrence based on type
                if transform_type == 'all':
                    # For 'all', use first occurrence
                    offset = content.find(old_name)
                else:
                    # For specific types, find the definition
                    offset = self._find_definition_offset(content, old_name, transform_type)
            
            if offset == -1:
                return content, 0
            
            # Create rename refactoring
            try:
                rename = Rename(self.project, resource, offset)
                changes = rename.get_changes(new_name)
                
                # Count changes
                changes_count = len(changes.changes[0].get_description().split('\n')) - 1
                
                # Get the new content without applying to project
                # (to match our existing API)
                new_content = changes.changes[0].get_new_contents()
                
                return new_content, changes_count
                
            except RopeError as e:
                print(f"Rope refactoring error: {e}")
                return content, 0
                
        except Exception as e:
            print(f"Error using rope backend: {e}")
            # Fall back to AST-based refactoring
            return None, 0
    
    def _find_definition_offset(self, content: str, name: str, transform_type: str) -> int:
        """Find the offset of a definition based on type."""
        import re
        
        if transform_type == 'function':
            # Look for function definition
            pattern = rf'^def\s+{re.escape(name)}\s*\('
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                # Return position after 'def '
                return match.start() + 4
        
        elif transform_type == 'class':
            # Look for class definition
            pattern = rf'^class\s+{re.escape(name)}[\s\(:]'
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                # Return position after 'class '
                return match.start() + 6
        
        elif transform_type == 'variable':
            # For variables, find first assignment at module or function level
            # This is more complex - for now use simple approach
            pattern = rf'^{re.escape(name)}\s*='
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.start()
        
        # Fallback to simple find
        return content.find(name)
    
    def _get_offset(self, lines: List[str], lineno: int, col_offset: int) -> int:
        """Convert line/column to character offset."""
        offset = sum(len(lines[i]) for i in range(lineno - 1))
        offset += col_offset
        return offset
    
    def close(self):
        """Clean up project resources."""
        self.project.close()

class EnhancedASTRefactoring(ASTRefactoring):
    """Enhanced refactoring that uses rope when available, AST otherwise."""
    
    def __init__(self):
        super().__init__()
        self.rope_backend = None
        if ROPE_AVAILABLE:
            print("✓ Rope library detected - using scope-aware refactoring")
        else:
            print("ℹ Type-aware refactoring mode (install rope for scope-aware refactoring)")
    
    def _read_file_with_retry(self, path: Path, max_retries: int = None, retry_delay: float = None) -> str:
        """Read file with retry logic for locked files.
        
        Args:
            path: File path to read
            max_retries: Maximum number of retries if file is locked (env: AST_ENHANCED_READ_MAX_RETRIES)
            retry_delay: Delay in seconds between retries (env: AST_ENHANCED_READ_RETRY_DELAY)
        
        Returns:
            str: File content
        
        Raises:
            OSError: If file remains locked after all retries
            IOError: If file cannot be read
        """
        # Get retry settings from environment or use defaults
        if max_retries is None:
            max_retries = int(os.getenv('AST_ENHANCED_READ_MAX_RETRIES', 
                                      os.getenv('AST_ENHANCED_MAX_RETRIES', '3')))
        if retry_delay is None:
            retry_delay = float(os.getenv('AST_ENHANCED_READ_RETRY_DELAY', 
                                        os.getenv('AST_ENHANCED_RETRY_DELAY', '1.0')))
        
        last_error = None
        for attempt in range(max_retries):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except OSError as e:
                last_error = e
                # Check if it's a permission/locking error
                if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY, errno.ETXTBSY):
                    if attempt < max_retries - 1:
                        # File is locked, wait and retry
                        if not os.getenv('QUIET_MODE'):
                            print(f"File {path} appears to be locked for reading, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                # For other errors or final attempt, raise immediately
                raise
            except Exception as e:
                # For non-OSError exceptions (encoding issues, etc.), don't retry
                raise
        
        # If we get here, all retries failed
        raise OSError(f"Failed to read {path} after {max_retries} attempts. Last error: {last_error}")
    
    def _atomic_write_file(self, path: Path, data: str, max_retries: int = None, retry_delay: float = None) -> None:
        """Write file atomically with retry logic for locked files.
        
        Args:
            path: Target file path
            data: Content to write
            max_retries: Maximum number of retries if file is locked (env: AST_ENHANCED_MAX_RETRIES)
            retry_delay: Delay in seconds between retries (env: AST_ENHANCED_RETRY_DELAY)
        
        Raises:
            OSError: If file remains locked after all retries
        """
        # Get retry settings from environment or use defaults
        if max_retries is None:
            max_retries = int(os.getenv('AST_ENHANCED_MAX_RETRIES', '3'))
        if retry_delay is None:
            retry_delay = float(os.getenv('AST_ENHANCED_RETRY_DELAY', '1.0'))
        
        # Use common_utils atomic_write if available
        if HAS_ATOMIC_WRITE:
            try:
                with atomic_write(path) as f:
                    f.write(data)
                return
            except Exception as e:
                print(f"Warning: atomic_write failed, falling back to custom implementation: {e}")
        
        # Fallback to custom atomic write implementation
        # Create temp file in same directory for atomic operation
        tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        tmp = Path(tmp_path)
        
        try:
            # Write data to temp file
            with os.fdopen(tmp_fd, 'w', encoding='utf-8', newline='') as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
        except Exception:
            # Clean up temp file on write error
            try:
                os.close(tmp_fd)
            except:
                pass
            try:
                tmp.unlink()
            except:
                pass
            raise
        
        # Create backup if path exists
        if path.exists():
            try:
                backup_path = path.with_suffix(path.suffix + ".bak")
                shutil.copy2(path, backup_path)
            except Exception as e:
                # Clean up temp file and re-raise
                try:
                    tmp.unlink()
                except:
                    pass
                raise Exception(f"Failed to create backup: {e}")
        
        # Attempt atomic replacement with retry logic
        last_error = None
        for attempt in range(max_retries):
            try:
                # Use os.replace for true atomic operation (works on both Unix and Windows)
                os.replace(str(tmp), str(path))
                return  # Success!
            except OSError as e:
                last_error = e
                # Check if it's a permission/locking error
                if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY, errno.ETXTBSY):
                    if attempt < max_retries - 1:
                        # File is locked, wait and retry
                        if not os.getenv('QUIET_MODE'):
                            print(f"File {path} appears to be locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                # For other errors or final attempt, clean up and raise
                try:
                    tmp.unlink()
                except:
                    pass
                raise
        
        # If we get here, all retries failed
        try:
            tmp.unlink()
        except:
            pass
        raise OSError(f"Failed to write {path} after {max_retries} attempts. Last error: {last_error}")
    
    def safe_rename(self, file_paths: List[Path], old_name: str, new_name: str, 
                   transform_type: str = 'all', dry_run: bool = True, max_retries: int = 3, 
                   retry_delay: float = 1.0) -> Dict:
        """Enhanced rename that uses rope when available."""
        
        # Initialize rope backend if available and not already initialized
        if ROPE_AVAILABLE and not self.rope_backend:
            # Find project root (directory containing .git or current directory)
            project_root = Path.cwd()
            for parent in Path.cwd().parents:
                if (parent / '.git').exists():
                    project_root = parent
                    break
            
            try:
                self.rope_backend = RopeBackend(str(project_root))
            except Exception as e:
                print(f"Warning: Could not initialize rope: {e}")
                self.rope_backend = None
        
        results = {
            'files_processed': 0,
            'total_changes': 0,
            'files_with_changes': [],
            'errors': [],
            'backend': 'rope' if self.rope_backend else 'ast'
        }
        
        for file_path in file_paths:
            if file_path.suffix == '.py':
                try:
                    original_content = self._read_file_with_retry(file_path, max_retries, retry_delay)
                    
                    # Try rope first if available
                    if self.rope_backend:
                        new_content, changes = self.rope_backend.rename_symbol(
                            file_path, old_name, new_name, transform_type
                        )
                        
                        # If rope failed, fall back to AST
                        if new_content is None:
                            new_content, changes = self.refactor_python_file(
                                file_path, old_name, new_name, transform_type, dry_run=True
                            )
                            results['backend'] = 'ast (rope fallback)'
                    else:
                        # Use AST-based refactoring
                        new_content, changes = self.refactor_python_file(
                            file_path, old_name, new_name, transform_type, dry_run=True
                        )
                    
                    results['files_processed'] += 1
                    results['total_changes'] += changes
                    
                    if changes > 0:
                        results['files_with_changes'].append({
                            'file': str(file_path),
                            'changes': changes,
                            'preview': self._generate_preview(original_content, new_content)
                        })
                        
                        # Apply changes if not dry run
                        if not dry_run:
                            self._atomic_write_file(file_path, new_content, max_retries, retry_delay)
                
                except Exception as e:
                    results['errors'].append({
                        'file': str(file_path),
                        'error': str(e)
                    })
        
        # Clean up rope backend
        if self.rope_backend:
            self.rope_backend.close()
            self.rope_backend = None
        
        return results
    
    def _generate_preview(self, original: str, modified: str, max_lines: int = 5) -> List[str]:
        """Generate a preview of changes."""
        import difflib
        
        diff = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            n=1
        ))
        
        # Extract only changed lines (skip header)
        preview = []
        for line in diff[3:]:  # Skip header lines
            if line.startswith('+') or line.startswith('-'):
                preview.append(line.rstrip())
                if len(preview) >= max_lines:
                    preview.append('...')
                    break
        
        return preview

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Enhanced AST refactoring with optional scope-aware support via rope')
    else:
        parser = argparse.ArgumentParser(
            description='Enhanced AST refactoring with optional scope-aware support via rope',
            epilog='''
REFACTORING MODES:
  - With rope: Full scope-aware refactoring (recommended)
  - Without rope: Type-aware refactoring (current implementation)

INSTALL ROPE:
  pip install rope    # Get scope-aware refactoring immediately!

ADVANTAGES WITH ROPE:
  - True scope awareness - only renames specific variable bindings
  - Handles imports, global/nonlocal declarations correctly  
  - Cross-file refactoring with dependency tracking
  - Production-tested on millions of lines of code
        ''',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
    
    # Add check-backend option
    parser.add_argument('--check-backend', action='store_true',
                       help='Check which refactoring backend is available')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Existing rename command
    rename_parser = subparsers.add_parser('rename', help='Rename identifiers')
    rename_parser.add_argument('files', nargs='+', help='Files to process')
    rename_parser.add_argument('--old-name', required=True, help='Current identifier name')
    rename_parser.add_argument('--new-name', required=True, help='New identifier name')
    rename_parser.add_argument('--type', choices=['function', 'class', 'variable', 'any'], default='any',
                              help='Type of identifier to rename')
    rename_parser.add_argument('--dry-run', action='store_true', help='Show what would be renamed without doing it')
    rename_parser.add_argument('--max-retries', type=int, default=3, 
                              help='Maximum retries for file lock conflicts (default: 3)')
    rename_parser.add_argument('--retry-delay', type=float, default=1.0,
                              help='Delay between retries in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    if args.check_backend:
        print("REFACTORING BACKEND STATUS")
        print("=" * 40)
        print(f"Rope available: {'✓ YES' if ROPE_AVAILABLE else '✗ NO'}")
        print(f"Astor available: {'✓ YES' if ASTOR_AVAILABLE else '✗ NO'}")
        print()
        
        if ROPE_AVAILABLE:
            print("✓ Scope-aware refactoring is available!")
            print("  You have IDE-quality refactoring capabilities.")
        else:
            print("ℹ Currently using type-aware refactoring.")
            print("  This is safer than text replacement but not scope-aware.")
            print()
            print("To enable scope-aware refactoring:")
            print("  pip install rope")
        
        return
    
    if not args.command:
        parser.print_help()
        return
    
    refactorer = EnhancedASTRefactoring()
    
    if args.command == 'rename':
        # Collect files
        file_paths = []
        for file_pattern in args.files:
            path = Path(file_pattern)
            if path.is_file():
                file_paths.append(path)
            elif path.is_dir():
                file_paths.extend(path.rglob('*.py'))
            else:
                file_paths.extend(Path('.').glob(file_pattern))
        
        if not file_paths:
            print("No files found to process")
            return
        
        print(f"Processing {len(file_paths)} files...")
        results = refactorer.safe_rename(
            file_paths, args.old_name, args.new_name, args.type, args.dry_run,
            args.max_retries, args.retry_delay
        )
        
        print(f"\nBackend used: {results['backend']}")
        print(f"Files processed: {results['files_processed']}")
        print(f"Total changes: {results['total_changes']}")
        
        if results['files_with_changes']:
            print(f"\nFiles with changes:")
            for item in results['files_with_changes']:
                print(f"\n  {item['file']}: {item['changes']} changes")
                if item.get('preview'):
                    print("  Preview:")
                    for line in item['preview'][:5]:
                        print(f"    {line}")
        
        if results['errors']:
            print(f"\nErrors:")
            for error in results['errors']:
                print(f"  {error['file']}: {error['error']}")
        
        if args.dry_run and results['total_changes'] > 0:
            print(f"\nDry run complete. Use without --dry-run to apply changes.")
            if not ROPE_AVAILABLE:
                print("\nTip: Install rope for scope-aware refactoring:")
                print("  pip install rope")

if __name__ == '__main__':
    main()