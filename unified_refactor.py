#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Unified Refactoring Tool - Comprehensive AST-based refactoring for multiple languages.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
import ast
import json
import subprocess
import tempfile
import shutil
import time
import errno
import re
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Set
from dataclasses import dataclass
from enum import Enum

# Standard infrastructure imports
try:
    from standard_arg_parser import create_standard_parser
    HAS_STANDARD_PARSER = True
except ImportError:
    HAS_STANDARD_PARSER = False
    def create_standard_parser(tool_type, description):
        return argparse.ArgumentParser(description=description)

try:
    from common_utils import (
        setup_logging, log_error, log_info, log_debug,
        AtomicFileWriter, FileBackupManager
    )
    HAS_COMMON_UTILS = True
except ImportError:
    HAS_COMMON_UTILS = False
    # Fallback logging
    import logging
    logging.basicConfig(level=logging.INFO)
    def log_error(msg): logging.error(msg)
    def log_info(msg): logging.info(msg)  
    def log_debug(msg): logging.debug(msg)

def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

try:
    from preflight_checks import run_preflight_checks, PreflightChecker
    HAS_PREFLIGHT = True
except ImportError:
    HAS_PREFLIGHT = False
    def run_preflight_checks(checks, exit_on_fail=True): pass
    class PreflightChecker:
        @staticmethod
        def check_file_readable(path): return True, ""
        @staticmethod
        def check_directory_accessible(path): return True, ""

# Optional dependencies for enhanced functionality
try:
    import rope.base.project
    import rope.refactor.rename
    HAS_ROPE = True
except ImportError:
    HAS_ROPE = False

try:
    import astor
    HAS_ASTOR = True
except ImportError:
    HAS_ASTOR = False


class RefactorEngine(Enum):
    """Available refactoring engines."""
    AUTO = "auto"
    PYTHON_AST = "python_ast"
    JAVA_SCOPE = "java_scope" 
    ROPE = "rope"
    TEXT_BASED = "text_based"


class SymbolType(Enum):
    """Symbol types for refactoring."""
    VARIABLE = "variable"
    METHOD = "method"
    FUNCTION = "function"
    CLASS = "class"
    FIELD = "field"
    ATTRIBUTE = "attribute"
    ANY = "any"
    ALL = "all"


@dataclass
class RefactorResult:
    """Result of a refactoring operation."""
    success: bool
    files_modified: List[str]
    changes_count: int
    error_message: Optional[str] = None
    preview: Optional[str] = None
    engine_used: Optional[str] = None


@dataclass
class JavaScope:
    """Represents a scope in Java code with symbol table."""
    name: str
    start_line: int
    end_line: int
    parent: Optional['JavaScope'] = None
    children: List['JavaScope'] = None
    symbols: Dict[str, str] = None  # symbol_name -> symbol_type
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.symbols is None:
            self.symbols = {}


class AtomicFileOperations:
    """Atomic file operations with retry logic."""
    
    def __init__(self, max_retries: int = None, retry_delay: float = None):
        self.max_retries = max_retries or int(os.environ.get('REFACTOR_MAX_RETRIES', '3'))
        self.retry_delay = retry_delay or float(os.environ.get('REFACTOR_RETRY_DELAY', '0.1'))
    
    def write_file_atomic(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """Write file atomically with retry logic using secure temp file creation."""
        for attempt in range(self.max_retries):
            temp_fd = None
            temp_path = None
            try:
                # Create secure temporary file in same directory for atomic move
                file_dir = os.path.dirname(os.path.abspath(file_path))
                temp_fd, temp_path = tempfile.mkstemp(
                    suffix=f'.tmp.{attempt}',
                    prefix=f'.{os.path.basename(file_path)}.',
                    dir=file_dir,
                    text=False  # We'll handle encoding ourselves
                )
                
                # Write content to temp file
                with os.fdopen(temp_fd, 'w', encoding=encoding) as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                temp_fd = None  # File is closed now
                
                # Atomic move using os.replace (cross-platform atomic)
                os.replace(temp_path, file_path)
                return True
                
            except (OSError, IOError) as e:
                # Clean up temp file descriptor if still open
                if temp_fd is not None:
                    try:
                        os.close(temp_fd)
                    except:
                        pass
                
                # Clean up temp file if it exists
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                
                if attempt < self.max_retries - 1:
                    log_debug(f"Write attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    log_error(f"Failed to write {file_path} after {self.max_retries} attempts: {e}")
                    return False
        
        return False
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """Create backup of file before modification."""
        backup_path = file_path + '.bak'
        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            log_error(f"Failed to create backup of {file_path}: {e}")
            return None


class PythonASTAnalyzer(ast.NodeVisitor):
    """Analyzes Python AST for identifier references."""
    
    def __init__(self, target_name: str, symbol_type: SymbolType = SymbolType.ANY):
        self.target_name = target_name
        self.symbol_type = symbol_type
        self.references = []
        self.definitions = []
        self.imports = []
        self.current_scope = []
        # TODO: Implement proper scope/symbol table for more accurate analysis
        # Current implementation tracks basic scope hierarchy but doesn't maintain
        # full symbol tables for proper variable resolution
    
    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        if node.name == self.target_name and self.symbol_type in [SymbolType.FUNCTION, SymbolType.ANY]:
            self.definitions.append({
                'type': 'function',
                'name': node.name,
                'line': node.lineno,
                'col_offset': getattr(node, 'col_offset', 0),
                'end_col_offset': getattr(node, 'end_col_offset', None),
                'scope': self.current_scope.copy()
            })
        
        self.current_scope.append(node.name)
        self.generic_visit(node)
        self.current_scope.pop()
    
    def visit_ClassDef(self, node):
        """Visit class definitions."""
        if node.name == self.target_name and self.symbol_type in [SymbolType.CLASS, SymbolType.ANY]:
            self.definitions.append({
                'type': 'class',
                'name': node.name,
                'line': node.lineno,
                'col_offset': getattr(node, 'col_offset', 0),
                'end_col_offset': getattr(node, 'end_col_offset', None),
                'scope': self.current_scope.copy()
            })
        
        self.current_scope.append(node.name)
        self.generic_visit(node)
        self.current_scope.pop()
    
    def visit_Name(self, node):
        """Visit name references."""
        if node.id == self.target_name:
            self.references.append({
                'type': 'name',
                'name': node.id,
                'line': getattr(node, 'lineno', 0),
                'col_offset': getattr(node, 'col_offset', 0),
                'end_col_offset': getattr(node, 'end_col_offset', None),
                'scope': self.current_scope.copy(),
                'context': type(node.ctx).__name__
            })
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Visit attribute references."""
        if node.attr == self.target_name and self.symbol_type in [SymbolType.ATTRIBUTE, SymbolType.ANY]:
            self.references.append({
                'type': 'attribute',
                'name': node.attr,
                'line': getattr(node, 'lineno', 0),
                'col_offset': getattr(node, 'col_offset', 0),
                'end_col_offset': getattr(node, 'end_col_offset', None),
                'scope': self.current_scope.copy()
            })
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node):
        """Visit annotated assignments (Python 3.6+)."""
        if isinstance(node.target, ast.Name) and node.target.id == self.target_name:
            self.definitions.append({
                'type': 'annotated_assignment',
                'name': node.target.id,
                'line': getattr(node, 'lineno', 0),
                'col_offset': getattr(node, 'col_offset', 0),
                'end_col_offset': getattr(node, 'end_col_offset', None),
                'scope': self.current_scope.copy()
            })
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node):
        """Visit exception handlers with variable binding."""
        if node.name and node.name == self.target_name:
            self.definitions.append({
                'type': 'exception_handler',
                'name': node.name,
                'line': getattr(node, 'lineno', 0),
                'col_offset': getattr(node, 'col_offset', 0),
                'end_col_offset': getattr(node, 'end_col_offset', None),
                'scope': self.current_scope.copy()
            })
        self.generic_visit(node)
    
    def visit_alias(self, node):
        """Visit import aliases."""
        # Handle 'import x as y' and 'from x import y as z'
        if node.asname == self.target_name:
            self.imports.append({
                'type': 'import_alias',
                'name': node.asname,
                'original_name': node.name,
                'line': getattr(node, 'lineno', 0),
                'col_offset': getattr(node, 'col_offset', 0),
                'scope': self.current_scope.copy()
            })
        elif node.name == self.target_name and not node.asname:
            self.imports.append({
                'type': 'import_name',
                'name': node.name,
                'line': getattr(node, 'lineno', 0),
                'col_offset': getattr(node, 'col_offset', 0),
                'scope': self.current_scope.copy()
            })
        self.generic_visit(node)
    
    def visit_arg(self, node):
        """Visit function arguments."""
        if node.arg == self.target_name:
            self.definitions.append({
                'type': 'function_argument',
                'name': node.arg,
                'line': getattr(node, 'lineno', 0),
                'col_offset': getattr(node, 'col_offset', 0),
                'end_col_offset': getattr(node, 'end_col_offset', None),
                'scope': self.current_scope.copy()
            })
        self.generic_visit(node)


class PythonASTTransformer(ast.NodeTransformer):
    """Transforms Python AST for refactoring operations."""
    
    def __init__(self, old_name: str, new_name: str, symbol_type: SymbolType = SymbolType.ANY):
        self.old_name = old_name
        self.new_name = new_name
        self.symbol_type = symbol_type
        self.changes_count = 0
    
    def visit_FunctionDef(self, node):
        """Transform function definitions."""
        if (node.name == self.old_name and 
            self.symbol_type in [SymbolType.FUNCTION, SymbolType.METHOD, SymbolType.ANY]):
            node.name = self.new_name
            self.changes_count += 1
        return self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Transform class definitions."""
        if (node.name == self.old_name and 
            self.symbol_type in [SymbolType.CLASS, SymbolType.ANY]):
            node.name = self.new_name
            self.changes_count += 1
        return self.generic_visit(node)
    
    def visit_Name(self, node):
        """Transform name references."""
        if node.id == self.old_name:
            node.id = self.new_name
            self.changes_count += 1
        return node
    
    def visit_Attribute(self, node):
        """Transform attribute references."""
        if (node.attr == self.old_name and 
            self.symbol_type in [SymbolType.ATTRIBUTE, SymbolType.ANY]):
            node.attr = self.new_name
            self.changes_count += 1
        return self.generic_visit(node)


class JavaScopeAnalyzer:
    """Builds scope tree from Java files using external JavaParser."""
    
    def __init__(self):
        self.java_parser_available = self._check_java_parser()
    
    def _check_java_parser(self) -> bool:
        """Check if Java parser is available."""
        try:
            # Check for Java refactor engine jars in current directory and common locations
            jar_paths = [
                'java-refactor-engine.jar',
                'simple-java-refactor.jar', 
                'spoon-refactor-engine.jar',
                './lib/java-refactor-engine.jar',
                './tools/java-refactor-engine.jar'
            ]
            
            for jar_path in jar_paths:
                if os.path.exists(jar_path):
                    # Verify the jar is executable
                    try:
                        result = subprocess.run([
                            'java', '-jar', jar_path, '--version'
                        ], capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            log_debug(f"Java parser available: {jar_path}")
                            return True
                    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                        log_debug(f"Java parser jar found but not executable: {jar_path}")
                        continue
            
            log_debug("No working Java refactor engine found")
            return False
        except Exception as e:
            log_debug(f"Java parser check failed: {e}")
            return False
    
    def analyze_file(self, file_path: str) -> List[JavaScope]:
        """Analyze Java file and return scope tree."""
        if not self.java_parser_available:
            log_error("Java parser not available")
            return []
        
        try:
            # Use external Java parser
            result = subprocess.run([
                'java', '-jar', 'java-refactor-engine.jar',
                '--file', file_path, '--analyze'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse JSON output from Java analyzer
                analysis_data = json.loads(result.stdout)
                return self._build_scope_tree(analysis_data)
            else:
                log_error(f"Java analysis failed: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            log_error(f"Java analysis timed out for {file_path}")
            return []
        except Exception as e:
            log_error(f"Java analysis error: {e}")
            return []
    
    def _build_scope_tree(self, analysis_data: Dict) -> List[JavaScope]:
        """Build scope tree from analysis data."""
        scopes = []
        
        def build_scope(scope_data: Dict, parent: Optional[JavaScope] = None) -> JavaScope:
            """Recursively build JavaScope objects from scope data."""
            # Create the JavaScope object
            scope = JavaScope(
                name=scope_data.get("name", ""),
                start_line=scope_data.get("startLine", 0),
                end_line=scope_data.get("endLine", 0),
                parent=parent,
                children=[],
                symbols={}
            )
            
            # Add symbols if present
            if "symbols" in scope_data:
                for symbol in scope_data["symbols"]:
                    symbol_name = symbol.get("name", "")
                    symbol_type = symbol.get("type", "")
                    if symbol_name:
                        scope.symbols[symbol_name] = symbol_type
            
            # Process child scopes recursively
            if "children" in scope_data:
                for child_data in scope_data["children"]:
                    child_scope = build_scope(child_data, scope)
                    scope.children.append(child_scope)
            
            return scope
        
        # Handle different possible JSON structures
        if isinstance(analysis_data, dict):
            # If analysis_data has a "scopes" key with a list
            if "scopes" in analysis_data and isinstance(analysis_data["scopes"], list):
                for scope_data in analysis_data["scopes"]:
                    scope = build_scope(scope_data)
                    scopes.append(scope)
            # If analysis_data has a single "scope" key
            elif "scope" in analysis_data:
                scope = build_scope(analysis_data["scope"])
                scopes.append(scope)
            # If analysis_data itself is a scope
            elif "name" in analysis_data and "startLine" in analysis_data:
                scope = build_scope(analysis_data)
                scopes.append(scope)
            # If analysis_data has a "classes" key (alternative structure)
            elif "classes" in analysis_data:
                for class_data in analysis_data["classes"]:
                    scope = build_scope(class_data)
                    scopes.append(scope)
        elif isinstance(analysis_data, list):
            # If analysis_data is directly a list of scopes
            for scope_data in analysis_data:
                scope = build_scope(scope_data)
                scopes.append(scope)
        
        return scopes


class RopeBackend:
    """Production-ready refactoring using rope library."""
    
    def __init__(self, project_root: str, dry_run: bool = False):
        self.project_root = Path(project_root)
        self.project = None
        self.available = HAS_ROPE
        self.dry_run = dry_run
        
        if self.available:
            try:
                # Configure rope to ignore certain files
                prefs = {
                    'ignored_resources': ['*.pyc', '*~', '.ropeproject', '.git', '__pycache__', 'venv', 'env'],
                    'python_files': ['*.py'],
                    'save_objectdb': False,
                    'compress_objectdb': False,
                    'automatic_soa': False,
                    'import_dynload_stdmods': False,
                }
                self.project = rope.base.project.Project(str(self.project_root), prefs=prefs)
            except Exception as e:
                log_error(f"Failed to initialize rope project: {e}")
                self.available = False
    
    def __del__(self):
        """Clean up rope project on deletion."""
        if self.project:
            try:
                self.project.close()
            except:
                pass
    
    def _generate_unified_diff(self, original_content: str, new_content: str, file_path: str) -> str:
        """Generate unified diff between original and new content."""
        original_lines = original_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{os.path.basename(file_path)}",
            tofile=f"b/{os.path.basename(file_path)}",
            n=3  # context lines
        )
        
        return ''.join(diff)
    
    def rename_symbol(self, file_path: str, offset: int, old_name: str, new_name: str) -> RefactorResult:
        """Rename symbol using rope."""
        if not self.available:
            return RefactorResult(
                success=False,
                files_modified=[],
                changes_count=0,
                error_message="Rope library not available"
            )
        
        try:
            # Convert file path to absolute and then get relative path
            abs_file_path = Path(file_path).absolute()
            try:
                rel_path = abs_file_path.relative_to(self.project_root)
            except ValueError:
                # File is not under project root, try using it directly
                return RefactorResult(
                    success=False,
                    files_modified=[],
                    changes_count=0,
                    error_message=f"File '{file_path}' is not under project root '{self.project_root}'"
                )
            
            resource = self.project.get_resource(str(rel_path))
            renamer = rope.refactor.rename.Rename(self.project, resource, offset)
            
            changes = renamer.get_changes(new_name)
            
            if changes:
                # Preview changes - we'll build a unified diff
                preview_parts = []
                preview_parts.append(changes.get_description())
                preview_parts.append("\n" + "=" * 80 + "\n")
                
                if not self.dry_run:
                    # Apply changes to rope's internal model
                    self.project.do(changes)
                
                # Now we need to write the changes back to disk
                modified_files = []
                changes_count = 0
                unified_diffs = []
                
                # Get all resources that were modified
                for change in changes.changes:
                    if hasattr(change, 'new_contents'):
                        # This is a file change
                        resource_path = change.get_description().split()[1]  # Extract path from description
                        if hasattr(change, 'resource'):
                            resource = change.resource
                            new_content = change.new_contents
                            
                            # Convert rope resource path to actual file path
                            actual_file_path = str(self.project_root / resource.path)
                            
                            # Read original content for diff generation
                            try:
                                with open(actual_file_path, 'r', encoding='utf-8') as f:
                                    original_content = f.read()
                                
                                # Generate unified diff
                                diff = self._generate_unified_diff(original_content, new_content, actual_file_path)
                                if diff:
                                    unified_diffs.append(diff)
                            except Exception as e:
                                log_error(f"Failed to generate diff for {actual_file_path}: {e}")
                            
                            if not self.dry_run:
                                # Write the changes to disk using atomic operations
                                file_ops = AtomicFileOperations()
                                backup_path = file_ops.create_backup(actual_file_path)
                                if backup_path:
                                    log_info(f"Backup created: {backup_path}")
                                
                                if file_ops.write_file_atomic(actual_file_path, new_content):
                                    modified_files.append(actual_file_path)
                                    changes_count += 1
                                else:
                                    log_error(f"Failed to write changes to {actual_file_path}")
                            else:
                                # In dry-run mode, just track what would be modified
                                modified_files.append(actual_file_path)
                                changes_count += 1
                
                # Combine all diffs into the preview
                if unified_diffs:
                    preview_parts.append("\nUnified Diffs:\n")
                    preview_parts.extend(unified_diffs)
                
                preview = ''.join(preview_parts)
                
                return RefactorResult(
                    success=True,
                    files_modified=modified_files,
                    changes_count=changes_count,
                    preview=preview,
                    engine_used="rope"
                )
            else:
                return RefactorResult(
                    success=True,
                    files_modified=[],
                    changes_count=0,
                    engine_used="rope"
                )
                
        except Exception as e:
            # Common rope errors - provide helpful messages
            error_msg = str(e)
            if "Not a resolvable python identifier" in error_msg:
                error_msg = f"Cannot find '{old_name}' at the specified location. Try specifying a line number or using python_ast backend."
            elif "Syntax error" in error_msg:
                error_msg = f"Rope detected syntax errors in the project. Consider using python_ast backend instead."
            else:
                error_msg = f"Rope refactoring failed: {error_msg}"
            
            return RefactorResult(
                success=False,
                files_modified=[],
                changes_count=0,
                error_message=error_msg,
                engine_used="rope"
            )
        finally:
            if self.project:
                self.project.close()


class UnifiedRefactor:
    """Main unified refactoring orchestration class."""
    
    def __init__(self, engine: RefactorEngine = RefactorEngine.AUTO, 
                 max_retries: int = 3, retry_delay: float = 0.1,
                 dry_run: bool = False):
        self.engine = engine
        self.dry_run = dry_run
        self.file_ops = AtomicFileOperations(max_retries, retry_delay)
        self.java_analyzer = JavaScopeAnalyzer()
    
    def _generate_unified_diff(self, original_content: str, new_content: str, file_path: str) -> str:
        """Generate unified diff between original and new content."""
        original_lines = original_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{os.path.basename(file_path)}",
            tofile=f"b/{os.path.basename(file_path)}",
            n=3  # context lines
        )
        
        return ''.join(diff)
        
    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        suffix = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp'
        }
        return language_map.get(suffix, 'unknown')
    
    def select_engine(self, file_path: str, symbol_type: SymbolType) -> RefactorEngine:
        """Select best refactoring engine for the given context."""
        if self.engine != RefactorEngine.AUTO:
            return self.engine
        
        language = self.detect_language(file_path)
        
        if language == 'java' and self.java_analyzer.java_parser_available:
            return RefactorEngine.JAVA_SCOPE
        elif language == 'python' and HAS_ROPE:
            return RefactorEngine.ROPE
        elif language == 'python':
            return RefactorEngine.PYTHON_AST
        else:
            return RefactorEngine.TEXT_BASED
    
    def rename_symbol(self, files: List[str], old_name: str, new_name: str,
                     symbol_type: SymbolType = SymbolType.ANY,
                     scope_path: Optional[str] = None,
                     line_number: Optional[int] = None) -> RefactorResult:
        """Rename symbol across multiple files."""
        
        if not files:
            return RefactorResult(
                success=False,
                files_modified=[],
                changes_count=0,
                error_message="No files specified"
            )
        
        # Select engine based on first file
        engine = self.select_engine(files[0], symbol_type)
        log_info(f"Using engine: {engine.value}")
        
        if engine == RefactorEngine.ROPE:
            # If no line number provided and rope is selected, fall back to Python AST
            # as rope needs precise location information
            if line_number is None:
                log_info("No line number provided for rope, falling back to Python AST")
                return self._rename_with_python_ast(files, old_name, new_name, symbol_type)
            return self._rename_with_rope(files[0], old_name, new_name, line_number)
        elif engine == RefactorEngine.JAVA_SCOPE:
            return self._rename_with_java_scope(files, old_name, new_name, symbol_type, scope_path)
        elif engine == RefactorEngine.PYTHON_AST:
            return self._rename_with_python_ast(files, old_name, new_name, symbol_type)
        else:
            return self._rename_with_text(files, old_name, new_name)
    
    def _rename_with_rope(self, file_path: str, old_name: str, new_name: str,
                         line_number: Optional[int] = None) -> RefactorResult:
        """Rename using rope backend."""
        project_root = self._find_project_root(file_path)
        rope_backend = RopeBackend(project_root, dry_run=self.dry_run)
        
        if not rope_backend.available:
            log_info("Rope not available, falling back to Python AST")
            return self._rename_with_python_ast([file_path], old_name, new_name, SymbolType.ANY)
        
        # Calculate offset using AST for more precise location
        offset = 0
        if line_number:
            try:
                # Use AST analyzer to find precise location
                with open(file_path, 'r') as f:
                    source_code = f.read()
                
                # Parse the AST
                tree = ast.parse(source_code, file_path)
                analyzer = PythonASTAnalyzer(old_name, SymbolType.ANY)
                analyzer.visit(tree)
                
                # Find the reference closest to the specified line
                closest_ref = None
                min_distance = float('inf')
                
                # Check all references and definitions
                all_occurrences = analyzer.references + analyzer.definitions
                for occurrence in all_occurrences:
                    if 'line' in occurrence:
                        distance = abs(occurrence['line'] - line_number)
                        if distance < min_distance:
                            min_distance = distance
                            closest_ref = occurrence
                
                # If we found a close reference, calculate its exact offset
                if closest_ref and min_distance <= 2:  # Within 2 lines
                    # Calculate offset to the line
                    lines = source_code.splitlines(keepends=True)
                    offset = sum(len(line) for line in lines[:closest_ref['line']-1])
                    
                    # Use AST column info if available, otherwise fall back to string search
                    if 'col_offset' in closest_ref and closest_ref['col_offset'] is not None:
                        offset += closest_ref['col_offset']
                    else:
                        # Fall back to string search within the line
                        target_line = lines[closest_ref['line']-1] if closest_ref['line'] <= len(lines) else ""
                        symbol_pos = target_line.find(old_name)
                        if symbol_pos >= 0:
                            offset += symbol_pos
                else:
                    # Fall back to simple string search if AST didn't help
                    lines = source_code.splitlines(keepends=True)
                    for i, line in enumerate(lines[:line_number-1]):
                        offset += len(line)
                    target_line = lines[line_number-1] if line_number <= len(lines) else ""
                    symbol_pos = target_line.find(old_name)
                    if symbol_pos >= 0:
                        offset += symbol_pos
            except Exception as e:
                log_error(f"Failed to calculate offset: {e}")
        
        return rope_backend.rename_symbol(file_path, offset, old_name, new_name)
    
    def _rename_with_java_scope(self, files: List[str], old_name: str, new_name: str,
                               symbol_type: SymbolType, scope_path: Optional[str]) -> RefactorResult:
        """Rename using Java scope analysis."""
        modified_files = []
        total_changes = 0
        
        for file_path in files:
            if not file_path.endswith('.java'):
                continue
                
            try:
                # Use external Java refactor engine
                cmd = [
                    'java', '-jar', 'java-refactor-engine.jar',
                    '--file', file_path,
                    '--old', old_name,
                    '--new', new_name,
                    '--type', symbol_type.value
                ]
                
                if self.dry_run:
                    cmd.append('--dry-run')
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    if not self.dry_run:
                        modified_files.append(file_path)
                    # Parse changes count from output
                    output_lines = result.stdout.strip().split('\n')
                    for line in output_lines:
                        if 'changes:' in line.lower():
                            try:
                                total_changes += int(line.split(':')[-1].strip())
                            except ValueError:
                                total_changes += 1
                else:
                    log_error(f"Java refactoring failed for {file_path}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                log_error(f"Java refactoring timed out for {file_path}")
            except Exception as e:
                log_error(f"Java refactoring error for {file_path}: {e}")
        
        return RefactorResult(
            success=len(modified_files) > 0 or self.dry_run,
            files_modified=modified_files,
            changes_count=total_changes,
            engine_used="java_scope"
        )
    
    def _rename_with_python_ast(self, files: List[str], old_name: str, new_name: str,
                               symbol_type: SymbolType) -> RefactorResult:
        """Rename using Python AST transformation."""
        modified_files = []
        total_changes = 0
        preview_parts = []
        preview_parts.append(f"Python AST Refactoring: {old_name} → {new_name}\n")
        preview_parts.append("=" * 80 + "\n")
        
        for file_path in files:
            if not file_path.endswith('.py'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                # Parse AST
                tree = ast.parse(source_code)
                
                # Transform AST
                transformer = PythonASTTransformer(old_name, new_name, symbol_type)
                new_tree = transformer.visit(tree)
                
                if transformer.changes_count > 0:
                    # Convert back to source code
                    if HAS_ASTOR:
                        new_source = astor.to_source(new_tree)
                    else:
                        # Cannot generate source code without astor
                        log_error(f"Cannot refactor {file_path}: astor module required for Python AST transformation")
                        log_info("Install astor with: pip install astor")
                        continue  # Skip this file
                    
                    if not self.dry_run:
                        # Create backup
                        backup_path = self.file_ops.create_backup(file_path)
                        if backup_path:
                            log_info(f"Backup created: {backup_path}")
                        
                        # Write modified file
                        if self.file_ops.write_file_atomic(file_path, new_source):
                            modified_files.append(file_path)
                            total_changes += transformer.changes_count
                        else:
                            log_error(f"Failed to write {file_path}")
                    else:
                        # In dry-run, track files that would be modified
                        if transformer.changes_count > 0:
                            modified_files.append(file_path)
                        total_changes += transformer.changes_count
                    
                    # Generate diff for preview
                    if transformer.changes_count > 0:
                        diff = self._generate_unified_diff(source_code, new_source, file_path)
                        if diff:
                            preview_parts.append(f"\n{file_path}:\n")
                            preview_parts.append(diff)
                        
            except SyntaxError as e:
                log_error(f"Syntax error in {file_path}: {e}")
            except Exception as e:
                log_error(f"AST refactoring error for {file_path}: {e}")
        
        preview = ''.join(preview_parts) if preview_parts else None
        
        return RefactorResult(
            success=len(modified_files) > 0 or (self.dry_run and total_changes > 0),
            files_modified=modified_files,
            changes_count=total_changes,
            preview=preview,
            engine_used="python_ast"
        )
    
    def _rename_with_text(self, files: List[str], old_name: str, new_name: str) -> RefactorResult:
        """Rename using simple text replacement (fallback)."""
        modified_files = []
        total_changes = 0
        preview_parts = []
        preview_parts.append(f"Text-based Refactoring: {old_name} → {new_name}\n")
        preview_parts.append("=" * 80 + "\n")
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple word boundary replacement
                import re
                pattern = r'\b' + re.escape(old_name) + r'\b'
                new_content, count = re.subn(pattern, new_name, content)
                
                if count > 0:
                    if not self.dry_run:
                        # Create backup
                        backup_path = self.file_ops.create_backup(file_path)
                        if backup_path:
                            log_info(f"Backup created: {backup_path}")
                        
                        # Write modified file
                        if self.file_ops.write_file_atomic(file_path, new_content):
                            modified_files.append(file_path)
                            total_changes += count
                        else:
                            log_error(f"Failed to write {file_path}")
                    else:
                        # In dry-run, track files that would be modified
                        modified_files.append(file_path)
                        total_changes += count
                    
                    # Generate diff for preview
                    diff = self._generate_unified_diff(content, new_content, file_path)
                    if diff:
                        preview_parts.append(f"\n{file_path}:\n")
                        preview_parts.append(diff)
                        
            except Exception as e:
                log_error(f"Text refactoring error for {file_path}: {e}")
        
        preview = ''.join(preview_parts) if preview_parts else None
        
        return RefactorResult(
            success=len(modified_files) > 0 or (self.dry_run and total_changes > 0),
            files_modified=modified_files,
            changes_count=total_changes,
            preview=preview,
            engine_used="text_based"
        )
    
    def _find_project_root(self, file_path: str) -> str:
        """Find project root directory."""
        current = Path(file_path).parent.absolute()
        
        while current != current.parent:
            # Look for common project markers
            if any((current / marker).exists() for marker in ['.git', '.project', 'setup.py', 'pom.xml']):
                return str(current)
            current = current.parent
        
        return str(Path(file_path).parent)
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze file and return symbol information."""
        language = self.detect_language(file_path)
        
        if language == 'python':
            return self._analyze_python_file(file_path)
        elif language == 'java':
            return self._analyze_java_file(file_path)
        else:
            return {'language': language, 'symbols': []}
    
    def _analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Python file using AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            symbols = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    symbols.append({
                        'type': 'function',
                        'name': node.name,
                        'line': node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    symbols.append({
                        'type': 'class',
                        'name': node.name,
                        'line': node.lineno
                    })
            
            return {
                'language': 'python',
                'symbols': symbols,
                'file_path': file_path
            }
            
        except Exception as e:
            return {
                'language': 'python',
                'symbols': [],
                'error': str(e)
            }
    
    def _analyze_java_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Java file using external parser."""
        if not self.java_analyzer.java_parser_available:
            return {
                'language': 'java',
                'symbols': [],
                'error': 'Java parser not available'
            }
        
        try:
            result = subprocess.run([
                'java', '-jar', 'java-refactor-engine.jar',
                '--file', file_path, '--analyze'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                analysis_data = json.loads(result.stdout)
                return {
                    'language': 'java',
                    'symbols': analysis_data.get('symbols', []),
                    'file_path': file_path
                }
            else:
                return {
                    'language': 'java',
                    'symbols': [],
                    'error': result.stderr
                }
                
        except Exception as e:
            return {
                'language': 'java',
                'symbols': [],
                'error': str(e)
            }


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for unified refactor tool."""
    # Use fallback parser to avoid conflicts with standard parser subcommands
    parser = argparse.ArgumentParser(
        description="Unified refactoring tool with multiple backends and language support")
    
    # Add common arguments
    parser.add_argument('--version', action='version', version='unified_refactor 1.0.0')
    parser.add_argument('--engine', type=str, choices=[e.value for e in RefactorEngine],
                       default='auto', help='Refactoring engine to use')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying them')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum retry attempts for file operations')
    parser.add_argument('--retry-delay', type=float, default=0.1,
                       help='Delay between retry attempts (seconds)')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level')
    parser.add_argument('--check-backend', action='store_true',
                       help='Show available backends and exit')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Rename command (from all 4 original tools)
    rename_parser = subparsers.add_parser('rename', help='Rename symbols')
    rename_parser.add_argument('files', nargs='*', help='Files to process (can be provided via --from-json)')
    rename_parser.add_argument('--old', '--old-name', dest='old_name',
                              help='Old symbol name (required unless using --from-json)')
    rename_parser.add_argument('--new', '--new-name', dest='new_name',
                              help='New symbol name (required unless using --from-json)')
    rename_parser.add_argument('--type', type=str, choices=[t.value for t in SymbolType],
                              default='any', help='Symbol type to rename')
    rename_parser.add_argument('--scope', type=str, help='Scope path for Java refactoring')
    rename_parser.add_argument('--line', type=int, help='Line number for precise targeting')
    rename_parser.add_argument('--from-json', type=str, metavar='FILE',
                              help='Read rename operations from JSON file (use \'-\' for stdin)')
    
    # Rename-project command (from java_scope_refactor.py)
    rename_project_parser = subparsers.add_parser('rename-project', 
                                                 help='Rename symbols across entire project')
    rename_project_parser.add_argument('--old', required=True, dest='old_name',
                                      help='Old symbol name')
    rename_project_parser.add_argument('--new', required=True, dest='new_name',
                                      help='New symbol name')
    rename_project_parser.add_argument('--type', type=str, choices=[t.value for t in SymbolType],
                                      default='any', help='Symbol type to rename')
    rename_project_parser.add_argument('--root', type=str, default='.',
                                      help='Project root directory')
    
    # Find command (from ast_refactor.py)
    find_parser = subparsers.add_parser('find', help='Find symbol occurrences')
    find_parser.add_argument('files', nargs='+', help='Files to search')
    find_parser.add_argument('--name', required=True, help='Symbol name to find')
    find_parser.add_argument('--type', type=str, choices=[t.value for t in SymbolType],
                            default='any', help='Symbol type to find')
    
    # Analyze command (from all tools)
    analyze_parser = subparsers.add_parser('analyze', help='Analyze file structure')
    analyze_parser.add_argument('files', nargs='+', help='Files to analyze')
    analyze_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Replace command (from smart_refactor_v2.py)
    replace_parser = subparsers.add_parser('replace', help='Replace text patterns')
    replace_parser.add_argument('files', nargs='+', help='Files to process')
    replace_parser.add_argument('--old', required=True, dest='old_text',
                               help='Old text pattern')
    replace_parser.add_argument('--new', required=True, dest='new_text',
                               help='New text replacement')
    replace_parser.add_argument('--regex', action='store_true',
                               help='Use regex patterns')
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    if HAS_COMMON_UTILS:
        # Use common_utils setup_logging if available
        import logging
        log_level = getattr(logging, args.log_level.upper())
        setup_logging(log_level)
    else:
        # Use local setup_logging fallback
        import logging
        log_level = getattr(logging, args.log_level.upper())
        setup_logging(log_level)
    
    # Validate rename command arguments
    if args.command == 'rename':
        if not (hasattr(args, 'from_json') and args.from_json):
            # If not using --from-json, require manual arguments
            if not args.old_name or not args.new_name:
                parser.error("--old and --new are required unless using --from-json")
            if not args.files:
                parser.error("files argument is required unless using --from-json")
        
        # Cross-option validation for Java language/backend
        if hasattr(args, 'files') and args.files:
            java_files = [f for f in args.files if f.endswith('.java')]
            if java_files and args.engine == 'java_scope':
                # Check if Java parser is available when explicitly requested
                java_analyzer = JavaScopeAnalyzer()
                if not java_analyzer.java_parser_available:
                    parser.error("Java scope engine requested but Java parser not available. "
                               "Ensure java-refactor-engine.jar is present or use 'auto' engine.")
    
    # Handle --check-backend
    if args.check_backend:
        print("Available refactoring backends:")
        print(f"  python_ast: Built-in Python AST transformer")
        print(f"  rope: Rope library {'(available)' if HAS_ROPE else '(not installed)'}")
        print(f"  java_scope: External Java parser {'(available)' if os.path.exists('java-refactor-engine.jar') else '(not found)'}")
        print(f"  text_based: Simple text replacement (always available)")
        print(f"  auto: Automatic selection (default)")
        return 0
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Run preflight checks
    if HAS_PREFLIGHT:
        checks = []
        if hasattr(args, 'files'):
            for file_path in args.files:
                checks.append(('file_readable', file_path))
        try:
            run_preflight_checks(checks, exit_on_fail=True)
        except Exception as e:
            # Continue without preflight checks if they fail
            log_debug(f"Preflight checks failed: {e}")
    
    # Initialize refactor engine
    engine = RefactorEngine(args.engine)
    refactor = UnifiedRefactor(
        engine=engine,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        dry_run=args.dry_run
    )
    
    try:
        if args.command == 'rename':
            # Flag to track if we processed find_text.py results
            processed_find_text_results = False
            
            # Handle --from-json if provided
            if hasattr(args, 'from_json') and args.from_json:
                try:
                    if args.from_json == '-':
                        # Read from stdin

                        json_data = json.load(sys.stdin)
                    else:
                        # Read from file
                        with open(args.from_json, 'r') as f:
                            json_data = json.load(f)
                    
                    # Check if this is find_text.py output (array of matches)
                    if isinstance(json_data, list) and len(json_data) > 0 and all('file' in item and 'line' in item for item in json_data[:1]):
                        # This is find_text.py output - process each match
                        processed_find_text_results = True
                        source_name = 'stdin' if args.from_json == '-' else args.from_json
                        print(f"Processing find_text.py results from {source_name}")
                        
                        # Group matches by file
                        file_matches = {}
                        for match in json_data:
                            if 'file' in match and 'line' in match:
                                file_path = match['file']
                                if file_path not in file_matches:
                                    file_matches[file_path] = []
                                file_matches[file_path].append(match)
                        
                        # Process each file with its matches
                        total_changes = 0
                        modified_files = []
                        
                        for file_path, matches in file_matches.items():
                            # Sort matches by line number in reverse order
                            # This ensures we process from bottom to top to avoid line number shifts
                            matches.sort(key=lambda m: m['line'], reverse=True)
                            
                            print(f"\nProcessing {len(matches)} matches in {file_path}")
                            
                            # Process each match in the file
                            for match in matches:
                                line_number = match['line']
                                old_text = match.get('match', args.old_name)
                                
                                # Perform targeted rename at specific line
                                result = refactor.rename_symbol(
                                    files=[file_path],
                                    old_name=old_text,
                                    new_name=args.new_name,
                                    symbol_type=SymbolType(args.type),
                                    scope_path=getattr(args, 'scope', None),
                                    line_number=line_number
                                )
                                
                                if result.success and result.changes_count > 0:
                                    total_changes += result.changes_count
                                    if file_path not in modified_files:
                                        modified_files.append(file_path)
                                    print(f"  Line {line_number}: {old_text} → {args.new_name} ✓")
                                else:
                                    print(f"  Line {line_number}: {old_text} → {args.new_name} ✗ {result.error_message or 'No changes'}")
                        
                        # Summary
                        print(f"\nTotal: Modified {len(modified_files)} files with {total_changes} changes")
                        return 0 if total_changes > 0 else 1
                    
                    # Otherwise, treat as simple rename JSON
                    else:
                        rename_data = json_data
                        
                        # Extract rename parameters from JSON
                        if 'files' in rename_data:
                            args.files = rename_data['files']
                        if 'old_name' in rename_data:
                            args.old_name = rename_data['old_name']
                        if 'new_name' in rename_data:
                            args.new_name = rename_data['new_name']
                        if 'type' in rename_data:
                            args.type = rename_data['type']
                        if 'scope' in rename_data:
                            args.scope = rename_data['scope']
                        if 'line' in rename_data:
                            args.line = rename_data['line']
                        
                        source_name = 'stdin' if args.from_json == '-' else args.from_json
                        print(f"Loaded rename operations from {source_name}")
                        
                except FileNotFoundError:
                    if args.from_json != '-':
                        print(f"Error: JSON file '{args.from_json}' not found")
                        return 1
                    else:
                        # This shouldn't happen for stdin, but just in case
                        print("Error: Could not read from stdin")
                        return 1
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in '{args.from_json}': {e}")
                    return 1
                except Exception as e:
                    print(f"Error processing JSON file: {e}")
                    return 1
            
            # Only run regular rename if we haven't already processed find_text.py results
            if not processed_find_text_results:
                result = refactor.rename_symbol(
                    files=args.files,
                    old_name=args.old_name,
                    new_name=args.new_name,
                    symbol_type=SymbolType(args.type),
                    scope_path=getattr(args, 'scope', None),
                    line_number=getattr(args, 'line', None)
                )
                
                if result.success:
                    if args.dry_run:
                        print(f"Would modify {len(result.files_modified)} files with {result.changes_count} changes")
                        if result.files_modified:
                            print("Files that would be modified:")
                            for file_path in result.files_modified:
                                print(f"  - {file_path}")
                    else:
                        print(f"Modified {len(result.files_modified)} files with {result.changes_count} changes")
                        for file_path in result.files_modified:
                            print(f"  - {file_path}")
                    if result.engine_used:
                        print(f"Engine used: {result.engine_used}")
                    
                    # Display preview if available
                    if result.preview:
                        print("\nPreview of changes:")
                        print(result.preview)
                    
                    return 0
                else:
                    error_msg = result.error_message or "No changes found or refactoring not applicable"
                    print(f"Refactoring failed: {error_msg}", file=sys.stderr)
                    return 1
        
        elif args.command == 'rename-project':
            # Find all relevant files in project
            import glob
            project_files = []
            for pattern in ['**/*.java', '**/*.py']:
                project_files.extend(glob.glob(pattern, recursive=True))
            
            result = refactor.rename_symbol(
                files=project_files,
                old_name=args.old_name,
                new_name=args.new_name,
                symbol_type=SymbolType(args.type)
            )
            
            if result.success:
                print(f"Project refactoring completed: {len(result.files_modified)} files modified")
                return 0
            else:
                print(f"Project refactoring failed: {result.error_message}", file=sys.stderr)
                return 1
        
        elif args.command == 'find':
            # Implement find functionality
            for file_path in args.files:
                analysis = refactor.analyze_file(file_path)
                if 'error' in analysis:
                    print(f"Error analyzing {file_path}: {analysis['error']}", file=sys.stderr)
                    continue
                
                print(f"\nFile: {file_path}")
                for symbol in analysis['symbols']:
                    if symbol['name'] == args.name:
                        print(f"  {symbol['type']}: {symbol['name']} (line {symbol['line']})")
            return 0
        
        elif args.command == 'analyze':
            for file_path in args.files:
                analysis = refactor.analyze_file(file_path)
                
                if args.json:
                    print(json.dumps(analysis, indent=2))
                else:
                    print(f"\nFile: {file_path} ({analysis['language']})")
                    if 'error' in analysis:
                        print(f"  Error: {analysis['error']}")
                    else:
                        for symbol in analysis['symbols']:
                            print(f"  {symbol['type']}: {symbol['name']} (line {symbol['line']})")
            return 0
        
        elif args.command == 'replace':
            # Simple text replacement
            result = refactor._rename_with_text(args.files, args.old_text, args.new_text)
            
            if result.success:
                print(f"Replaced text in {len(result.files_modified)} files with {result.changes_count} changes")
                if result.files_modified:
                    print("Modified files:")
                    for f in result.files_modified:
                        print(f"  - {f}")
                return 0
            else:
                error_msg = result.error_message or "Unknown error"
                print(f"Text replacement failed: {error_msg}", file=sys.stderr)
                return 1
        
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())