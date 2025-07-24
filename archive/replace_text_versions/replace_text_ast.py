#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
AST-enhanced text replacement tool with scope-aware variable renaming.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import os
import re
import ast
import difflib
import shutil
import tempfile
import argparse
import logging
import subprocess
import copy
import time
import errno
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any

# ────────────────────────────  logging  ────────────────────────────

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

LOG = logging.getLogger("replace_text_ast")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s"
)

# Load common configuration system
try:
    from common_config import load_config, apply_config_to_args
except ImportError:
    # Graceful fallback if common_config is not available
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass

# Try to import javalang for Java AST support
try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False

# Try to import rope for advanced Python refactoring
try:
    import rope.base.project
    import rope.base.libutils
    import rope.refactor.rename
    import rope
    
    # Rope doesn't expose __version__ directly, assume it's recent enough
    # Version 1.13+ is required for Python 3.10+ match-case syntax
    ROPE_AVAILABLE = True
    ROPE_SAFE_VERSION = True
except ImportError:
    ROPE_AVAILABLE = False
    ROPE_SAFE_VERSION = False

# Import AST context finder
try:
    from ast_context_finder import ASTContextFinder
    HAS_AST_CONTEXT = True
except ImportError:
    HAS_AST_CONTEXT = False

class PythonScopeAnalyzer:
    """Analyzes Python code to understand variable scopes."""
    
    def __init__(self, code: str):
        self.code = code
        self.tree = None
        self.scopes = {}  # Maps (line, name) to scope info
        self.scope_hierarchy = {}  # Maps scope to parent scope
        self.variable_declarations = {}  # Maps variable name to declaring scope
        
    def analyze(self):
        """Analyze the code to build scope information."""
        try:
            self.tree = ast.parse(self.code)
            self._build_scopes()
        except SyntaxError as e:
            raise ValueError(f"Python syntax error: {e}")
    
    def _build_scopes(self):
        """Build scope information for all variables."""
        
        class ScopeVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.scope_stack = []
                self.current_scope = 'module'
                self.analyzer.scope_hierarchy['module'] = None  # Module has no parent
                
            def visit_FunctionDef(self, node):
                # Enter function scope
                parent_scope = self.current_scope
                self.scope_stack.append(self.current_scope)
                self.current_scope = f"function:{node.name}:{node.lineno}"
                
                # Record scope hierarchy
                self.analyzer.scope_hierarchy[self.current_scope] = parent_scope
                
                # Record function parameters
                for arg in node.args.args:
                    self.analyzer.scopes[(arg.lineno, arg.arg)] = {
                        'scope': self.current_scope,
                        'type': 'parameter',
                        'declaration_line': arg.lineno
                    }
                    # Track parameter declarations
                    if arg.arg not in self.analyzer.variable_declarations:
                        self.analyzer.variable_declarations[arg.arg] = []
                    self.analyzer.variable_declarations[arg.arg].append(
                        (arg.lineno, self.current_scope)
                    )
                
                self.generic_visit(node)
                
                # Exit function scope
                self.current_scope = self.scope_stack.pop()
                
            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)
                
            def visit_ClassDef(self, node):
                # Enter class scope
                parent_scope = self.current_scope
                self.scope_stack.append(self.current_scope)
                self.current_scope = f"class:{node.name}:{node.lineno}"
                
                # Record scope hierarchy
                self.analyzer.scope_hierarchy[self.current_scope] = parent_scope
                
                self.generic_visit(node)
                
                # Exit class scope
                self.current_scope = self.scope_stack.pop()
                
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store):
                    # Variable assignment
                    key = (node.lineno, node.id)
                    if key not in self.analyzer.scopes:
                        self.analyzer.scopes[key] = {
                            'scope': self.current_scope,
                            'type': 'variable',
                            'declaration_line': node.lineno
                        }
                        # Track variable declarations (only if not already declared in this scope)
                        if node.id not in self.analyzer.variable_declarations:
                            self.analyzer.variable_declarations[node.id] = []
                        self.analyzer.variable_declarations[node.id].append(
                            (node.lineno, self.current_scope)
                        )
                
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                # Track self.attribute assignments
                if (isinstance(node.ctx, ast.Store) and 
                    isinstance(node.value, ast.Name) and node.value.id == 'self'):
                    key = (node.lineno, node.attr)
                    if key not in self.analyzer.scopes:
                        self.analyzer.scopes[key] = {
                            'scope': self.current_scope,
                            'type': 'instance_variable',
                            'declaration_line': node.lineno
                        }
                        # Track instance variable declarations
                        if node.attr not in self.analyzer.variable_declarations:
                            self.analyzer.variable_declarations[node.attr] = []
                        self.analyzer.variable_declarations[node.attr].append(
                            (node.lineno, self.current_scope)
                        )
                
                self.generic_visit(node)
                
            def visit_For(self, node):
                # Handle loop variables
                if isinstance(node.target, ast.Name):
                    self.analyzer.scopes[(node.target.lineno, node.target.id)] = {
                        'scope': self.current_scope,
                        'type': 'loop_variable',
                        'declaration_line': node.target.lineno
                    }
                    # Track loop variable declarations  
                    if node.target.id not in self.analyzer.variable_declarations:
                        self.analyzer.variable_declarations[node.target.id] = []
                    self.analyzer.variable_declarations[node.target.id].append(
                        (node.target.lineno, self.current_scope)
                    )
                
                self.generic_visit(node)
        
        visitor = ScopeVisitor(self)
        visitor.visit(self.tree)
    
    def find_variable_scope(self, var_name: str, line_number: int) -> Optional[Dict]:
        """Find the scope of a variable at a given line."""
        # Look for the most recent declaration before this line
        best_match = None
        best_line = -1
        
        for (line, name), scope_info in self.scopes.items():
            if name == var_name and line <= line_number:
                if line > best_line:
                    best_match = scope_info
                    best_line = line
        
        return best_match
    
    def is_scope_accessible_from(self, target_scope: str, current_scope: str) -> bool:
        """Check if a variable in target_scope is accessible from current_scope.
        
        This implements lexical scoping rules where inner scopes can access
        variables from outer scopes, but not vice versa.
        """
        if target_scope == current_scope:
            return True
        
        # Walk up the scope hierarchy from current_scope
        # to see if we can reach target_scope
        checking_scope = current_scope
        visited = set()  # Prevent infinite loops
        
        while checking_scope is not None and checking_scope not in visited:
            visited.add(checking_scope)
            parent_scope = self.scope_hierarchy.get(checking_scope)
            if parent_scope == target_scope:
                return True
            checking_scope = parent_scope
        
        return False
    
    def find_accessible_variable_scope(self, var_name: str, line_number: int, current_scope: str) -> Optional[Dict]:
        """Find the most specific scope where var_name is declared and accessible from current_scope."""
        # Look for all declarations of this variable
        candidates = []
        for (line, name), scope_info in self.scopes.items():
            if name == var_name and line <= line_number:
                candidates.append((line, scope_info))
        
        # Sort by declaration line (most recent first)
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Find the first candidate that's accessible from current_scope
        # Use lexical scoping rules: inner scopes can access outer scope variables
        for line, scope_info in candidates:
            declaring_scope = scope_info['scope']
            
            # Check if the variable is accessible:
            # 1. If we're in the same scope
            # 2. If we're in an inner scope that can access the declaring scope
            if (declaring_scope == current_scope or 
                self.is_scope_accessible_from(declaring_scope, current_scope)):
                return scope_info
        
        return None
    
    def rename_variable_in_scope(self, var_name: str, new_name: str, 
                               declaration_line: int) -> Tuple[str, int]:
        """
        Rename a variable only within its scope.
        
        Args:
            var_name: Original variable name
            new_name: New variable name
            declaration_line: Line where the variable is declared
            
        Returns:
            Modified code and number of replacements
        """
        if not self.tree:
            raise ValueError("Code not analyzed yet")
        
        # Find the variable's scope
        scope_info = self.find_variable_scope(var_name, declaration_line)
        if not scope_info:
            return self.code, 0
        
        # Create a modified AST
        class RenameTransformer(ast.NodeTransformer):
            def __init__(self, target_name, new_name, target_scope, analyzer):
                self.target_name = target_name
                self.new_name = new_name
                self.target_scope = target_scope
                self.analyzer = analyzer
                self.current_scope = 'module'
                self.scope_stack = []
                self.replacements = 0
                
            def visit_FunctionDef(self, node):
                self.scope_stack.append(self.current_scope)
                self.current_scope = f"function:{node.name}:{node.lineno}"
                
                # Transform function body
                self.generic_visit(node)
                
                self.current_scope = self.scope_stack.pop()
                return node
                
            def visit_ClassDef(self, node):
                self.scope_stack.append(self.current_scope)
                self.current_scope = f"class:{node.name}:{node.lineno}"
                
                self.generic_visit(node)
                
                self.current_scope = self.scope_stack.pop()
                return node
                
            def visit_Name(self, node):
                # Check if this is our target variable
                if node.id == self.target_name:
                    # For Store context (assignment), only rename if in exact scope
                    if isinstance(node.ctx, ast.Store):
                        if self.current_scope == self.target_scope:
                            node.id = self.new_name
                            self.replacements += 1
                    # For Load context (usage), check if the target variable is accessible
                    elif isinstance(node.ctx, ast.Load):
                        # Find which variable this reference resolves to
                        resolved_scope = self.analyzer.find_accessible_variable_scope(
                            node.id, node.lineno, self.current_scope
                        )
                        if resolved_scope and resolved_scope['scope'] == self.target_scope:
                            node.id = self.new_name
                            self.replacements += 1
                return node
            
            def visit_Attribute(self, node):
                # Handle self.attribute renaming
                if (isinstance(node.value, ast.Name) and node.value.id == 'self' and
                    node.attr == self.target_name and 
                    self.current_scope == self.target_scope):
                    node.attr = self.new_name
                    self.replacements += 1
                self.generic_visit(node)
                return node
        
        # Apply the transformation
        transformer = RenameTransformer(var_name, new_name, scope_info['scope'], self)
        new_tree = transformer.visit(copy.deepcopy(self.tree))
        
        # Convert back to code
        if hasattr(ast, 'unparse'):
            # Python 3.9+
            new_code = ast.unparse(new_tree)
        else:
            # Fallback: manual replacement with scope checking
            new_code = self._manual_scope_rename(var_name, new_name, scope_info)
            transformer.replacements = new_code.count(new_name) - self.code.count(new_name)
        
        return new_code, transformer.replacements
    
    def _manual_scope_rename(self, var_name: str, new_name: str, 
                           scope_info: Dict) -> str:
        """Manual scope-aware renaming for older Python versions."""
        # This is a simplified version - for production use, 
        # consider using the rope library
        lines = self.code.splitlines()
        
        # Determine scope boundaries
        if scope_info['scope'].startswith('function:'):
            # Find function boundaries
            func_name = scope_info['scope'].split(':')[1]
            func_line = int(scope_info['scope'].split(':')[2])
            
            # Simple approach: rename within function body
            # In production, use proper AST traversal
            pattern = r'\b' + re.escape(var_name) + r'\b'
            replacement_count = 0
            in_function = False
            brace_level = 0
            
            for i in range(len(lines)):
                if i + 1 >= func_line:
                    if 'def ' + func_name in lines[i]:
                        in_function = True
                    
                    if in_function:
                        # Track indentation to find function end
                        if lines[i].strip() and not lines[i].startswith(' '):
                            # Back to module level
                            break
                        
                        # Replace in this line
                        lines[i] = re.sub(pattern, new_name, lines[i])
        
        return '\n'.join(lines)

def java_ast_rename_with_engine(file_path: str, old_name: str, new_name: str,
                                line_number: int, is_method: bool = False,
                                source_dirs: Optional[List[str]] = None,
                                jar_paths: Optional[List[str]] = None,
                                dry_run: bool = False) -> Tuple[str, int]:
    """
    Performs scope-aware rename by calling the external Java refactoring engine.
    
    Args:
        file_path: Path to the Java file
        old_name: Original name to rename
        new_name: New name
        line_number: Line number where the symbol is declared
        is_method: True if renaming a method, False for variables
        source_dirs: Optional list of source directories for better symbol resolution
        jar_paths: Optional list of JAR files for dependency resolution
        
    Returns:
        Modified content and number of replacements
    """
    # Use only Spoon engine for Java refactoring
    spoon_engine_path = os.path.join(os.path.dirname(__file__), 'spoon-refactor-engine.jar')
    
    engine_jar_path = None
    engine_type = None
    
    if os.path.exists(spoon_engine_path):
        engine_jar_path = spoon_engine_path
        engine_type = 'spoon'
        print("Info: Using Spoon refactoring engine", file=sys.stderr)
    else:
        # Fallback to basic regex-based approach if Spoon not available
        print("Warning: Spoon refactoring engine not found. Using basic refactoring.", file=sys.stderr)
        print("To enable Spoon-based Java refactoring, run: ./build_java_engine_gradle.sh", file=sys.stderr)
    
    if engine_jar_path is None:
        # Fall back to the simple JavaScopeAnalyzer
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        analyzer = JavaScopeAnalyzer(content)
        analyzer.analyze()
        return analyzer.rename_variable_in_scope(old_name, new_name, line_number)

    # Use new format if source dirs or jars are provided, otherwise use legacy format
    if source_dirs or jar_paths:
        cmd = [
            'java', '-jar', engine_jar_path,
            '--file', str(file_path),
            '--line', str(line_number),
            '--old-name', old_name,
            '--new-name', new_name
        ]
        
        if is_method:
            cmd.append('--method')
            
        # Add source directories
        if source_dirs:
            for src_dir in source_dirs:
                cmd.extend(['--source-dir', src_dir])
                
        # Add JAR paths
        if jar_paths:
            for jar in jar_paths:
                cmd.extend(['--jar', jar])
    else:
        # Legacy format for backward compatibility
        cmd = [
            'java', '-jar', engine_jar_path,
            str(file_path), str(line_number), old_name, new_name
        ]
        
        if is_method:
            cmd.append('--method')

    try:
        # Debug information
        if os.environ.get('DEBUG_SPOON'):
            print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr)
            
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if os.environ.get('DEBUG_SPOON'):
            print(f"DEBUG: Return code: {result.returncode}", file=sys.stderr)
            print(f"DEBUG: Stdout length: {len(result.stdout)}", file=sys.stderr)
            print(f"DEBUG: Stderr: {result.stderr}", file=sys.stderr)
        
        if result.returncode != 0:
            # If Java engine fails, fall back to basic approach
            print(f"Warning: Java refactoring engine failed (return code {result.returncode}): {result.stderr}", file=sys.stderr)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            analyzer = JavaScopeAnalyzer(content)
            analyzer.analyze()
            return analyzer.rename_variable_in_scope(old_name, new_name, line_number)
        
        # The Java engine prints the full modified source to stdout
        modified_content = result.stdout
        
        # CRITICAL: Validate that we got non-empty output to prevent file corruption
        if not modified_content or not modified_content.strip():
            print(f"Warning: Java refactoring engine returned empty output. Checking for output files...", file=sys.stderr)
            print(f"Engine stderr: {result.stderr}", file=sys.stderr)
            
            # Check if the engine wrote to a file instead of stdout
            result_file = file_path + ".spoon_result"
            if os.path.exists(result_file):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    if file_content and file_content.strip():
                        print(f"Found result in {result_file}, using it instead of stdout", file=sys.stderr)
                        modified_content = file_content
                        # Clean up the result file
                        os.remove(result_file)
                    else:
                        print(f"Result file {result_file} is empty", file=sys.stderr)
                except Exception as e:
                    print(f"Error reading result file {result_file}: {e}", file=sys.stderr)
            
            # If still no content, check for backup files that might indicate successful processing
            if not modified_content or not modified_content.strip():
                backup_files = []
                for backup_ext in ['.bak', '.backup', '.orig']:
                    backup_file = file_path + backup_ext
                    if os.path.exists(backup_file):
                        backup_files.append(backup_file)
                
                if backup_files:
                    print(f"Found backup files: {backup_files}. The Spoon engine may have processed the file but failed to output results.", file=sys.stderr)
                    print(f"CRITICAL: Preserving original file to prevent data loss.", file=sys.stderr)
                
                print(f"Falling back to basic approach due to empty output.", file=sys.stderr)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                analyzer = JavaScopeAnalyzer(content)
                analyzer.analyze()
                return analyzer.rename_variable_in_scope(old_name, new_name, line_number)
        
        # Count replacements by comparing original and modified
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Additional safety check: ensure the modified content has reasonable size
        if len(modified_content) < len(original_content) * 0.5:
            print(f"Warning: Modified content is suspiciously small ({len(modified_content)} vs {len(original_content)} chars). Falling back to basic approach.", file=sys.stderr)
            analyzer = JavaScopeAnalyzer(original_content)
            analyzer.analyze()
            return analyzer.rename_variable_in_scope(old_name, new_name, line_number)
        
        # Count how many times the old name was replaced
        original_count = original_content.count(old_name)
        modified_count = modified_content.count(old_name)
        replacements = original_count - modified_count
        
        return modified_content, replacements
        
    except FileNotFoundError:
        print("Warning: Java not found. Using basic refactoring.", file=sys.stderr)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            analyzer = JavaScopeAnalyzer(content)
            analyzer.analyze()
            return analyzer.rename_variable_in_scope(old_name, new_name, line_number)
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to read original file for fallback: {e}", file=sys.stderr)
            raise ValueError(f"Cannot process file: {e}")
    except Exception as e:
        print(f"CRITICAL ERROR: Unexpected error in Java refactoring engine: {e}", file=sys.stderr)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            analyzer = JavaScopeAnalyzer(content)
            analyzer.analyze()
            return analyzer.rename_variable_in_scope(old_name, new_name, line_number)
        except Exception as fallback_e:
            print(f"CRITICAL ERROR: Fallback also failed: {fallback_e}", file=sys.stderr)
            raise ValueError(f"Cannot process file: {fallback_e}")

class JavaScopeAnalyzer:
    """Analyzes Java code to understand variable scopes."""
    
    def __init__(self, code: str):
        self.code = code
        self.tree = None
        self.scopes = {}
        
    def analyze(self):
        """Analyze the code to build scope information."""
        if not JAVALANG_AVAILABLE:
            raise ValueError("javalang not installed. Install with: pip install javalang")
        
        try:
            self.tree = javalang.parse.parse(self.code)
            self._build_scopes()
        except Exception as e:
            raise ValueError(f"Java parsing error: {e}")
    
    def _build_scopes(self):
        """Build scope information for Java variables."""
        # Track current scope path
        scope_path = []
        
        for path, node in self.tree:
            # Update scope based on node type
            if isinstance(node, javalang.tree.ClassDeclaration):
                scope_path = [f"class:{node.name}"]
            elif isinstance(node, javalang.tree.MethodDeclaration):
                if scope_path:
                    current_scope = f"{scope_path[0]}.method:{node.name}"
                else:
                    current_scope = f"method:{node.name}"
                    
                # Record method parameters
                for param in node.parameters:
                    if hasattr(node, 'position'):
                        self.scopes[(node.position.line, param.name)] = {
                            'scope': current_scope,
                            'type': 'parameter'
                        }
            elif isinstance(node, javalang.tree.LocalVariableDeclaration):
                # Local variable declaration
                for declarator in node.declarators:
                    if hasattr(node, 'position'):
                        scope = scope_path[-1] if scope_path else 'file'
                        self.scopes[(node.position.line, declarator.name)] = {
                            'scope': scope,
                            'type': 'local_variable'
                        }
    
    def rename_variable_in_scope(self, var_name: str, new_name: str, 
                               declaration_line: int) -> Tuple[str, int]:
        """Rename a Java variable within its scope."""
        # For Java, we'll use a regex-based approach with scope awareness
        # In production, consider using JavaParser or similar tools
        
        lines = self.code.splitlines()
        pattern = r'\b' + re.escape(var_name) + r'\b'
        replacements = 0
        
        # Find the variable's scope
        scope_info = None
        for (line, name), info in self.scopes.items():
            if name == var_name and line == declaration_line:
                scope_info = info
                break
        
        if not scope_info:
            return self.code, 0
        
        # Simple scope-based replacement
        # This is a basic implementation - for production, use proper Java AST tools
        if 'method:' in scope_info['scope']:
            # Replace within method scope
            method_name = scope_info['scope'].split('method:')[1]
            in_method = False
            brace_count = 0
            
            for i in range(len(lines)):
                if method_name in lines[i] and '(' in lines[i]:
                    in_method = True
                
                if in_method:
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    
                    # Replace in this line
                    new_line, count = re.subn(pattern, new_name, lines[i])
                    if count > 0:
                        lines[i] = new_line
                        replacements += count
                    
                    if brace_count == 0 and '{' in ' '.join(lines[:i+1]):
                        # End of method
                        break
        
        return '\n'.join(lines), replacements

def perform_ast_rename(file_path: str, old_name: str, new_name: str, 
                      line_number: int, language: str = 'auto', dry_run: bool = False,
                      use_rope: bool = False, source_dirs: Optional[List[str]] = None,
                      jar_paths: Optional[List[str]] = None) -> Tuple[str, int]:
    """
    Perform AST-based scope-aware variable renaming.
    
    Args:
        file_path: Path to the file
        old_name: Original variable name
        new_name: New variable name
        line_number: Line where the variable is declared
        language: Programming language ('python', 'java', or 'auto')
        
    Returns:
        Modified content and number of replacements
    """
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")
    
    # Auto-detect language if needed
    if language == 'auto':
        file_path_str = str(file_path)
        if file_path_str.endswith('.py'):
            language = 'python'
        elif file_path_str.endswith('.java'):
            language = 'java'
        else:
            raise ValueError("Cannot auto-detect language. Please specify --language")
    
    # Perform language-specific AST analysis and renaming
    if language == 'python':
        # Try rope first if available (default for Python)
        if ROPE_AVAILABLE:
            try:
                return rope_rename_variable(file_path, old_name, new_name, line_number, dry_run)
            except Exception as e:
                print(f"Warning: Rope failed ({e}), falling back to built-in AST", file=sys.stderr)
                # Fall through to built-in AST
        
        # Use built-in AST as fallback
        analyzer = PythonScopeAnalyzer(content)
        analyzer.analyze()
        return analyzer.rename_variable_in_scope(old_name, new_name, line_number)
    
    elif language == 'java':
        # Try the external Java engine first for best results
        return java_ast_rename_with_engine(file_path, old_name, new_name, line_number, 
                                         source_dirs=source_dirs, jar_paths=jar_paths, dry_run=dry_run)
    
    else:
        raise ValueError(f"Unsupported language: {language}")

def rope_rename_variable(file_path: str, old_name: str, new_name: str, 
                        line_number: int, dry_run: bool = False) -> Tuple[str, int]:
    """Use rope library for advanced Python refactoring."""
    import re  # Import re at function level
    
    # Create a temporary directory with just the target file to avoid project-wide issues
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Copy the target file to temporary directory
            file_path_obj = Path(file_path).resolve()
            temp_file = Path(temp_dir) / file_path_obj.name
            shutil.copy2(file_path_obj, temp_file)
            
            # Configure rope with minimal settings
            prefs = {
                'ignored_resources': ['*.pyc', '*~', '.git', '__pycache__'],
                'python_files': ['*.py'],
                'save_objectdb': False,
                'compress_objectdb': False,
                'automatic_soa': False,
                'soa_followed_calls': 0,
                'perform_doa': False,
                'validate_objectdb': False,
                'max_history_items': 0,
                'save_history': False,
                'compress_history': False,
                'indent_size': 4,
                'extension_modules': [],
                'import_dynload_stdmods': False,
                'ignore_syntax_errors': True,
                'ignore_bad_imports': True
            }
            
            # Create rope project in temp directory
            project = rope.base.project.Project(
                temp_dir, 
                ropefolder=None,
                prefs=prefs
            )
            
            # Get the resource (file)
            resource = project.get_file(temp_file.name)
            
            # Calculate offset from line number
            content = resource.read()
            lines = content.splitlines(keepends=True)
        
            # Find the variable on the specified line
            if line_number > len(lines):
                raise ValueError(f"Line {line_number} does not exist in file")
            
            line_start_offset = sum(len(line) for line in lines[:line_number-1])
            line_content = lines[line_number-1]
            
            # Find the variable in the line
            match = re.search(r'\b' + re.escape(old_name) + r'\b', line_content)
            if not match:
                raise ValueError(f"Variable '{old_name}' not found on line {line_number}")
            
            offset = line_start_offset + match.start()
            
            # Create rename refactoring
            rename = rope.refactor.rename.Rename(project, resource, offset)
            
            # Get changes
            changes = rename.get_changes(new_name)
            
            # Get the new content
            if dry_run:
                # Apply changes to see result without saving
                project.do(changes)
                new_content = resource.read()
                # Don't save - this is just preview
            else:
                # Apply changes
                project.do(changes)
                new_content = resource.read()
                # Copy modified file back to original location
                shutil.copy2(temp_file, file_path_obj)
            
            # Count replacements by comparing word boundaries to avoid counting substrings
            old_pattern = r'\b' + re.escape(old_name) + r'\b'
            original_count = len(re.findall(old_pattern, content))
            modified_count = len(re.findall(old_pattern, new_content))
            replacements = original_count - modified_count
            
            project.close()
            
            return new_content, replacements
            
        except Exception as e:
            if 'project' in locals():
                project.close()
            raise ValueError(f"Rope refactoring error: {e}")

def is_file_locked(filepath):
    """Check if a file is currently locked for writing.
    
    Returns:
        (is_locked, process_info): Tuple of lock status and process info string
    """
    # Platform-specific file locking check
    import platform
    
    if platform.system() != 'Windows':
        # Unix-like systems (Linux, macOS)
        try:
            # Try to open file for exclusive write access
            with open(filepath, 'r+b') as f:
                # Try to acquire an exclusive lock (non-blocking)
                try:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    return False, None
                except IOError:
                    # File is locked
                    try:
                        # Try to get process info using lsof (if available)
                        result = subprocess.run(['lsof', '-t', str(filepath)], 
                                              capture_output=True, text=True, timeout=1)
                        if result.returncode == 0 and result.stdout.strip():
                            pids = result.stdout.strip().split('\n')
                            return True, f"locked by process(es): {', '.join(pids)}"
                    except:
                        pass
                    return True, "locked by another process"
                except ImportError:
                    # fcntl not available, try alternative method
                    pass
        except PermissionError:
            return True, "permission denied"
        except Exception:
            pass
    
    # Windows or fallback method: try to open for exclusive write
    try:
        # Try to open the file in exclusive mode
        test_fd = os.open(str(filepath), os.O_RDWR | os.O_EXCL)
        os.close(test_fd)
        return False, None
    except OSError as e:
        if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY):
            return True, "locked or in use by another process"
        elif e.errno == errno.ENOENT:
            return False, "file does not exist"
    except Exception:
        pass
    
    # Final fallback: try to rename the file to itself
    try:
        os.rename(str(filepath), str(filepath))
        return False, None
    except OSError:
        return True, "file is in use"
    except Exception:
        pass
    
    return False, None

def _atomic_write(path: Path, data: str, bak: bool = False, max_retries: int = 3, retry_delay: float = 1.0) -> None:
    """Write atomically with retry logic for locked files; optionally create .bak.
    
    Args:
        path: Target file path
        data: Content to write
        bak: Whether to create backup
        max_retries: Maximum number of retries if file is locked
        retry_delay: Delay in seconds between retries
    
    Raises:
        OSError: If file remains locked after all retries
    """
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
    
    # Create backup if requested
    if bak and path.exists():
        try:
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
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
    raise OSError(f"Failed to write {path} after {max_retries} attempts: {last_error}")

def check_compile_status(file_path, language=None):
    """Check if file compiles/has valid syntax. Returns (success, short_message).
    
    This function is designed to NEVER break tool functionality:
    - All exceptions are caught and handled gracefully
    - Returns success=True for unknown languages or when compilers are missing
    - Uses timeouts to prevent hanging on problematic files
    - Cleans up temporary files (like .class files)
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return True, "File not found"  # Don't fail - file might be created later
        
        # Check file size to avoid hanging on huge files
        try:
            file_size = path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                return False, "Cannot check - file too large"
        except OSError:
            return False, "Cannot check - size unknown"
        
        # Auto-detect language if not specified
        if not language:
            suffix = path.suffix.lower()
            if suffix == '.py':
                language = 'python'
            elif suffix == '.java':
                language = 'java'
            elif suffix in ['.js', '.jsx']:
                language = 'javascript'
            elif suffix in ['.ts', '.tsx']:
                language = 'typescript'
            else:
                return False, "Cannot check - unknown language"  # Be honest about inability to check
        
        # Python syntax check
        if language == 'python':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Skip empty files
                if not content.strip():
                    return False, "Cannot check - empty file"
                
                ast.parse(content)
                return True, "Compiles"
            except SyntaxError:
                return False, "Syntax Error"
            except UnicodeDecodeError:
                return False, "Cannot check - encoding issue"
            except Exception:
                return False, "Cannot check - parse failed"
        
        # Java compilation check
        elif language == 'java':
            try:
                # Check if javac is available
                result = subprocess.run(
                    ['javac', '-version'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode != 0:
                    return False, "Cannot check - javac unavailable"
                
                # Compile the file
                result = subprocess.run(
                    ['javac', '-cp', '.', str(file_path)],
                    capture_output=True, text=True, timeout=30
                )
                
                # Always clean up .class files
                class_file = path.with_suffix('.class')
                if class_file.exists():
                    try:
                        class_file.unlink()
                    except OSError:
                        pass  # Ignore cleanup errors
                
                if result.returncode == 0:
                    return True, "Compiles"
                else:
                    return False, "Compile Error"
                    
            except subprocess.TimeoutExpired:
                return False, "Cannot check - compile timeout"
            except FileNotFoundError:
                return False, "Cannot check - javac not found"
            except Exception:
                return False, "Cannot check - compile failed"
        
        # JavaScript/TypeScript syntax check
        elif language in ['javascript', 'typescript']:
            try:
                if language == 'javascript':
                    # Check if node is available
                    result = subprocess.run(
                        ['node', '--version'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode != 0:
                        return False, "Cannot check - node unavailable"
                    
                    result = subprocess.run(
                        ['node', '-c', str(file_path)],
                        capture_output=True, text=True, timeout=15
                    )
                else:  # typescript
                    # Check if tsc is available
                    result = subprocess.run(
                        ['tsc', '--version'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode != 0:
                        return False, "Cannot check - tsc unavailable"
                    
                    result = subprocess.run(
                        ['tsc', '--noEmit', str(file_path)],
                        capture_output=True, text=True, timeout=20
                    )
                
                if result.returncode == 0:
                    return True, "Compiles"
                else:
                    return False, "Syntax Error"
                    
            except subprocess.TimeoutExpired:
                return False, "Cannot check - timeout"
            except FileNotFoundError:
                return False, "Cannot check - compiler not found"
            except Exception:
                return False, "Cannot check - check failed"
        
        # Default for unknown languages
        return False, "Cannot check - unsupported language"
    
    except Exception:
        # Ultimate fallback - never break the tool
        return False, "Cannot check - internal error"

def show_diff(original: str, modified: str, file_path: str, show_ast_context: bool = False) -> bool:
    """Show unified diff of changes."""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"{file_path} (original)",
        tofile=f"{file_path} (modified)",
        lineterm=''
    )
    
    diff_lines = list(diff)
    if diff_lines:
        print("\nChanges to be made:")
        
        # Initialize AST context finder if needed
        context_finder = None
        if show_ast_context and HAS_AST_CONTEXT:
            context_finder = ASTContextFinder()
        
        for line in diff_lines:
            # Extract line number from diff output if it's a change line
            if line.startswith('@@'):
                # Parse the line number from @@ -X,Y +A,B @@
                import re
                match = re.search(r'\+([0-9]+)', line)
                if match and context_finder:
                    line_num = int(match.group(1))
                    context = context_finder._format_context_parts(
                        context_finder.get_context_for_line(file_path, line_num)
                    )
                    if context:
                        print(f"{line.rstrip()} [{context}]")
                        continue
            
            print(line.rstrip())
    
    return bool(diff_lines)

def main():
    # Don't use standard parser since our argument structure is different
    if False:  # HAS_STANDARD_PARSER - disabled to use custom args
        parser = create_parser('analyze', 'AST-enhanced replacement tool with scope-aware variable renaming')
    else:
        parser = argparse.ArgumentParser(
            description='AST-enhanced replacement tool with scope-aware variable renaming',
            epilog='''
EXAMPLES:
  # Rename variable at specific line
  python3 replace_text_ast.py old_var new_var --file myfile.py --line 42
  
  # Rename with language specification  
  python3 replace_text_ast.py myVar newVar --file MyClass.java --line 15 --language java
  
  # Preview changes without applying  
  python3 replace_text_ast.py foo bar --file script.py --line 10 --dry-run
  
  # Use rope for advanced Python refactoring (if installed)
  python3 replace_text_ast.py var1 var2 --file module.py --line 25 --use-rope

AST SUPPORT:
  - Python: Built-in ast module (always available)
  - Python+: rope library for advanced refactoring (pip install rope)
  - Java: javalang library (pip install javalang)
  
BENEFITS:
  - Renames only the specific variable in its scope
  - Leaves other variables with the same name untouched
  - Understands nested scopes and shadowing
  - True semantic refactoring, not text replacement
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # AST rename mode
    parser.add_argument("old_name", help="The original variable or method name to be replaced")
    parser.add_argument("new_name", help="The new variable or method name")
    parser.add_argument("--ast-rename", action="store_true", help="Enable AST-based scope-aware renaming")
    
    # File argument
    parser.add_argument('--file', type=str, required=True,
                       help='File to perform refactoring on')
    # Options
    parser.add_argument('--line', '-l', type=int, required=True,
                       help='Line number where the variable is declared for scope analysis')
    parser.add_argument('--language', '--lang', choices=['python', 'java', 'auto'],
                       default='auto', help='Programming language (default: auto-detect)')
    parser.add_argument('--use-rope', action='store_true',
                       help='Use rope library for Python (if available)')
    parser.add_argument('--backup', '-b', action='store_true',
                       help='Create backup before modifying')
    parser.add_argument('--no-backup', action='store_true',
                       help='Explicitly disable backup creation')
    parser.add_argument('--ast-context', action='store_true',
                       help='Show AST context (class/method) in diff output')
    parser.add_argument('--check-compile', action='store_true', default=True,
                       help='Check syntax/compilation after successful edits (default: enabled)')
    parser.add_argument('--no-check-compile', action='store_true',
                       help='Disable compile checking')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying')
    
    # Retry control options
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum number of retry attempts for locked files (default: 3)')
    parser.add_argument('--retry-delay', type=float, default=1.0,
                       help='Delay in seconds between retry attempts (default: 1.0)')
    parser.add_argument('--no-retry', action='store_true',
                       help='Disable retry logic for locked files')
    
    # Java-specific options for better symbol resolution
    parser.add_argument('--source-dir', action='append', dest='source_dirs',
                       help='Add source directory for Java symbol resolution (can be specified multiple times)')
    parser.add_argument('--jar', '--jar-path', action='append', dest='jar_paths',
                       help='Add JAR file for Java dependency resolution (can be specified multiple times)')
    
    args = parser.parse_args()
    
    # Handle compile check flags
    if args.no_check_compile:
        args.check_compile = False
    
    # Handle retry configuration
    if args.no_retry:
        args.max_retries = 1
        args.retry_delay = 0.0
    
    # Allow retry configuration via environment variables (can override CLI args)
    if 'FILE_WRITE_MAX_RETRIES' in os.environ:
        args.max_retries = int(os.environ['FILE_WRITE_MAX_RETRIES'])
    if 'FILE_WRITE_RETRY_DELAY' in os.environ:
        args.retry_delay = float(os.environ['FILE_WRITE_RETRY_DELAY'])
    
    # Apply configuration defaults
    apply_config_to_args('replace_text_ast', args, parser)
    
    # Debug: print dry_run status
    if os.environ.get('DEBUG_CONFIG'):
        print(f"DEBUG: dry_run={args.dry_run}, backup={args.backup}", file=sys.stderr)
    
    # Handle both file and file_path attributes (standard parser vs custom)
    file_path = getattr(args, 'file', None) or getattr(args, 'file_path', None)
    
    # Validate arguments
    if not file_path:
        parser.error("Please specify a file with --file")
    
    if not args.old_name or not args.new_name:
        parser.error("Please specify both old_name and new_name")
    
    if not args.line:
        parser.error("--line is required for AST-based renaming")
    
    # Check file exists
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Read original content
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Perform AST-based renaming
        print(f"🔍 Analyzing scope for '{args.old_name}' at line {args.line}...")
        
        if args.use_rope and args.language in ['python', 'auto']:
            if not ROPE_AVAILABLE:
                print("Warning: rope not installed, falling back to built-in AST", file=sys.stderr)
        
        modified_content, replacements = perform_ast_rename(
            file_path,
            args.old_name,
            args.new_name,
            args.line,
            args.language,
            args.dry_run,
            args.use_rope,
            args.source_dirs,
            args.jar_paths
        )
        
        if replacements == 0:
            print(f"No occurrences of '{args.old_name}' found in the variable's scope")
            sys.exit(0)
        
        # Get context information if available
        context_str = ""
        if args.ast_context and HAS_AST_CONTEXT:
            context_finder = ASTContextFinder()
            context = context_finder._format_context_parts(
                context_finder.get_context_for_line(file_path, args.line)
            )
            if context:
                context_str = f" in [{context}]"
        
        print(f"✨ Found {replacements} reference(s) in the variable's scope{context_str}")
        
        # Show diff
        if show_diff(original_content, modified_content, file_path, args.ast_context):
            if not args.dry_run:
                # CRITICAL: Final safety check before writing to prevent data corruption
                if not modified_content or not modified_content.strip():
                    print(f"CRITICAL ERROR: Modified content is empty! Aborting write to prevent file corruption.", file=sys.stderr)
                    sys.exit(1)
                
                # Additional safety check: ensure reasonable content size
                if len(modified_content) < len(original_content) * 0.3:
                    print(f"CRITICAL ERROR: Modified content is suspiciously small ({len(modified_content)} vs {len(original_content)} chars). Aborting write to prevent file corruption.", file=sys.stderr)
                    sys.exit(1)
                
                # Write modified content with atomic operation and retry logic
                try:
                    # Handle backup logic: create backup if requested and not explicitly disabled
                    should_backup = args.backup and not getattr(args, 'no_backup', False)
                    _atomic_write(Path(file_path), modified_content, bak=should_backup, 
                                  max_retries=args.max_retries, retry_delay=args.retry_delay)
                except Exception as e:
                    # Enhanced error reporting for file write failures
                    error_msg = f"\nError writing {file_path}: {e}"
                    
                    # Check if file is locked and provide more info
                    is_locked, lock_info = is_file_locked(file_path)
                    if is_locked:
                        error_msg += f"\nFile appears to be {lock_info}"
                        error_msg += "\nTry closing any programs that might have this file open."
                    
                    print(error_msg, file=sys.stderr)
                    sys.exit(1)
                
                # Build success message
                LOG.info("✅ Successfully renamed %d occurrence(s)", replacements)
                
                # Check compilation if requested
                if args.check_compile:
                    try:
                        compile_success, compile_msg = check_compile_status(file_path, args.language)
                        compile_status = f"✓ {compile_msg}" if compile_success else f"✗ {compile_msg}"
                        print(compile_status)
                    except Exception as e:
                        # Never let compile check break the tool
                        print(f"✗ Compile check failed: {str(e)[:50]}")
            else:
                print("\n(Dry run - no changes applied)")
        else:
            print("No changes needed")
    
    except Exception as e:
        LOG.exception("Unhandled error")
        sys.exit(2)

if __name__ == '__main__':
    main()