#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
AST-based refactoring tool for intelligent code transformations.

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
from typing import List, Set, Dict, Any, Optional
import re

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
    import astor
except ImportError:
    print("Warning: astor not installed. Install with: pip install astor")
    astor = None

class PythonASTAnalyzer(ast.NodeVisitor):
    """Analyzes Python AST to find all references to identifiers."""
    
    def __init__(self):
        self.functions: Set[str] = set()
        self.classes: Set[str] = set()
        self.variables: Set[str] = set()
        self.method_calls: Dict[str, List[int]] = {}
        self.function_calls: Dict[str, List[int]] = {}
        self.imports: Set[str] = set()
        
    def visit_FunctionDef(self, node):
        self.functions.add(node.name)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        self.classes.add(node.name)
        self.generic_visit(node)
    
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.variables.add(node.id)
        self.generic_visit(node)
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name not in self.function_calls:
                self.function_calls[func_name] = []
            self.function_calls[func_name].append(node.lineno)
        elif isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            if method_name not in self.method_calls:
                self.method_calls[method_name] = []
            self.method_calls[method_name].append(node.lineno)
        self.generic_visit(node)
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module)
        self.generic_visit(node)

class PythonASTTransformer(ast.NodeTransformer):
    """Transforms Python AST for refactoring operations."""
    
    def __init__(self, old_name: str, new_name: str, transform_type: str):
        self.old_name = old_name
        self.new_name = new_name
        self.transform_type = transform_type
        self.changes_made = 0
    
    def visit_FunctionDef(self, node):
        if self.transform_type in ['function', 'all'] and node.name == self.old_name:
            node.name = self.new_name
            self.changes_made += 1
        return self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        if self.transform_type in ['class', 'all'] and node.name == self.old_name:
            node.name = self.new_name
            self.changes_made += 1
        return self.generic_visit(node)
    
    def visit_Name(self, node):
        if self.transform_type in ['variable', 'all'] and node.id == self.old_name:
            node.id = self.new_name
            self.changes_made += 1
        return node
    
    def visit_Call(self, node):
        # Function calls
        if isinstance(node.func, ast.Name) and self.transform_type in ['function', 'all']:
            if node.func.id == self.old_name:
                node.func.id = self.new_name
                self.changes_made += 1
        
        # Method calls
        elif isinstance(node.func, ast.Attribute) and self.transform_type in ['method', 'all']:
            if node.func.attr == self.old_name:
                node.func.attr = self.new_name
                self.changes_made += 1
        
        return self.generic_visit(node)
    
    def visit_Attribute(self, node):
        if self.transform_type in ['attribute', 'all'] and node.attr == self.old_name:
            node.attr = self.new_name
            self.changes_made += 1
        return self.generic_visit(node)

class ASTRefactoring:
    """Main class for AST-based refactoring operations."""
    
    def __init__(self):
        self.supported_languages = ['python']
    
    def _read_file_with_retry(self, path: Path, max_retries: int = None, retry_delay: float = None) -> str:
        """Read file with retry logic for locked files.
        
        Args:
            path: File path to read
            max_retries: Maximum number of retries if file is locked (env: AST_REFACTOR_READ_MAX_RETRIES)
            retry_delay: Delay in seconds between retries (env: AST_REFACTOR_READ_RETRY_DELAY)
        
        Returns:
            str: File content
        
        Raises:
            OSError: If file remains locked after all retries
            IOError: If file cannot be read
        """
        # Get retry settings from environment or use defaults
        if max_retries is None:
            max_retries = int(os.getenv('AST_REFACTOR_READ_MAX_RETRIES', 
                                      os.getenv('AST_REFACTOR_MAX_RETRIES', '3')))
        if retry_delay is None:
            retry_delay = float(os.getenv('AST_REFACTOR_READ_RETRY_DELAY', 
                                        os.getenv('AST_REFACTOR_RETRY_DELAY', '1.0')))
        
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
    
    def analyze_python_file(self, file_path: Path) -> PythonASTAnalyzer:
        """Analyze a Python file and return AST analysis."""
        try:
            content = self._read_file_with_retry(file_path)
            
            tree = ast.parse(content, filename=str(file_path))
            analyzer = PythonASTAnalyzer()
            analyzer.visit(tree)
            return analyzer
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def _atomic_write_file(self, path: Path, data: str, max_retries: int = None, retry_delay: float = None) -> None:
        """Write file atomically with retry logic for locked files.
        
        Args:
            path: Target file path
            data: Content to write
            max_retries: Maximum number of retries if file is locked (env: AST_REFACTOR_MAX_RETRIES)
            retry_delay: Delay in seconds between retries (env: AST_REFACTOR_RETRY_DELAY)
        
        Raises:
            OSError: If file remains locked after all retries
        """
        # Get retry settings from environment or use defaults
        if max_retries is None:
            max_retries = int(os.getenv('AST_REFACTOR_MAX_RETRIES', '3'))
        if retry_delay is None:
            retry_delay = float(os.getenv('AST_REFACTOR_RETRY_DELAY', '1.0'))
        
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
    
    def refactor_python_file(self, file_path: Path, old_name: str, new_name: str, 
                           transform_type: str, dry_run: bool = True, max_retries: int = 3, 
                           retry_delay: float = 1.0) -> tuple[str, int]:
        """Refactor a Python file using AST transformations."""
        
        if not astor:
            raise ImportError("astor library required for Python refactoring. Install with: pip install astor")
        
        try:
            content = self._read_file_with_retry(file_path, max_retries, retry_delay)
            
            tree = ast.parse(content, filename=str(file_path))
            transformer = PythonASTTransformer(old_name, new_name, transform_type)
            new_tree = transformer.visit(tree)
            
            # Convert back to source code
            new_content = astor.to_source(new_tree)
            
            if not dry_run and transformer.changes_made > 0:
                self._atomic_write_file(file_path, new_content, max_retries, retry_delay)
            
            return new_content, transformer.changes_made
            
        except Exception as e:
            print(f"Error refactoring {file_path}: {e}")
            return content if 'content' in locals() else "", 0
    
    def find_references(self, file_path: Path, identifier: str) -> Dict[str, List[int]]:
        """Find all references to an identifier in a file."""
        analyzer = self.analyze_python_file(file_path)
        if not analyzer:
            return {}
        
        references = {}
        
        # Check function calls
        if identifier in analyzer.function_calls:
            references['function_calls'] = analyzer.function_calls[identifier]
        
        # Check method calls
        if identifier in analyzer.method_calls:
            references['method_calls'] = analyzer.method_calls[identifier]
        
        # Check if it's a defined function/class
        if identifier in analyzer.functions:
            references['function_definition'] = True
        
        if identifier in analyzer.classes:
            references['class_definition'] = True
        
        return references
    
    def safe_rename(self, file_paths: List[Path], old_name: str, new_name: str, 
                   transform_type: str = 'all', dry_run: bool = True, max_retries: int = 3, 
                   retry_delay: float = 1.0) -> Dict[str, Any]:
        """Safely rename an identifier across multiple files."""
        
        results = {
            'files_processed': 0,
            'total_changes': 0,
            'files_with_changes': [],
            'errors': []
        }
        
        for file_path in file_paths:
            if file_path.suffix == '.py':
                try:
                    new_content, changes = self.refactor_python_file(
                        file_path, old_name, new_name, transform_type, dry_run, max_retries, retry_delay
                    )
                    
                    results['files_processed'] += 1
                    results['total_changes'] += changes
                    
                    if changes > 0:
                        results['files_with_changes'].append({
                            'file': str(file_path),
                            'changes': changes
                        })
                
                except Exception as e:
                    results['errors'].append({
                        'file': str(file_path),
                        'error': str(e)
                    })
            else:
                # For non-Python files, fall back to text-based replacement
                # Could add Java AST support here in the future
                pass
        
        return results

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'AST-based refactoring tool for type-aware code transformations')
    else:
        parser = argparse.ArgumentParser(description='AST-based refactoring tool for type-aware code transformations')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Rename command
    rename_parser = subparsers.add_parser('rename', help='Rename identifiers using AST')
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
    
    # Find command
    find_parser = subparsers.add_parser('find', help='Find all references to an identifier')
    find_parser.add_argument('files', nargs='+', help='Files to search')
    find_parser.add_argument('--name', required=True, help='Identifier to find')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze file structure')
    analyze_parser.add_argument('file', help='File to analyze')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    refactorer = ASTRefactoring()
    
    if args.command == 'rename':
        # Collect all files
        file_paths = []
        for file_pattern in args.files:
            path = Path(file_pattern)
            if path.is_file():
                file_paths.append(path)
            elif path.is_dir():
                file_paths.extend(path.rglob('*.py'))
            else:
                # Handle glob patterns
                file_paths.extend(Path('.').glob(file_pattern))
        
        if not file_paths:
            print("No files found to process")
            return
        
        print(f"Processing {len(file_paths)} files...")
        results = refactorer.safe_rename(
            file_paths, args.old_name, args.new_name, args.type, args.dry_run,
            args.max_retries, args.retry_delay
        )
        
        print(f"\nResults:")
        print(f"Files processed: {results['files_processed']}")
        print(f"Total changes: {results['total_changes']}")
        
        if results['files_with_changes']:
            print(f"\nFiles with changes:")
            for item in results['files_with_changes']:
                print(f"  {item['file']}: {item['changes']} changes")
        
        if results['errors']:
            print(f"\nErrors:")
            for error in results['errors']:
                print(f"  {error['file']}: {error['error']}")
        
        if args.dry_run and results['total_changes'] > 0:
            print(f"\nDry run complete. Use without --dry-run to apply changes.")
    
    elif args.command == 'find':
        file_paths = []
        for file_pattern in args.files:
            path = Path(file_pattern)
            if path.is_file():
                file_paths.append(path)
            elif path.is_dir():
                file_paths.extend(path.rglob('*.py'))
            else:
                file_paths.extend(Path('.').glob(file_pattern))
        
        total_references = 0
        for file_path in file_paths:
            references = refactorer.find_references(file_path, args.name)
            if references:
                print(f"\n{file_path}:")
                for ref_type, ref_data in references.items():
                    if isinstance(ref_data, list):
                        print(f"  {ref_type}: lines {ref_data}")
                        total_references += len(ref_data)
                    else:
                        print(f"  {ref_type}: {ref_data}")
                        total_references += 1
        
        print(f"\nTotal references found: {total_references}")
    
    elif args.command == 'analyze':
        file_path = Path(args.file)
        analyzer = refactorer.analyze_python_file(file_path)
        
        if analyzer:
            print(f"Analysis of {file_path}:")
            print(f"Functions: {sorted(analyzer.functions)}")
            print(f"Classes: {sorted(analyzer.classes)}")
            print(f"Variables: {sorted(list(analyzer.variables)[:10])}{'...' if len(analyzer.variables) > 10 else ''}")
            print(f"Function calls: {dict(list(analyzer.function_calls.items())[:5])}")
            print(f"Method calls: {dict(list(analyzer.method_calls.items())[:5])}")
            print(f"Imports: {sorted(analyzer.imports)}")

if __name__ == '__main__':
    main()