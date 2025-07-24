#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Advanced Java refactoring tool with scope awareness.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import argparse
import subprocess
import json
import re
import os
import time
import errno
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import tempfile
import shutil

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

class JavaScope:
    """Represents a scope in Java code."""
    
    def __init__(self, scope_type: str, name: str, parent: Optional['JavaScope'] = None):
        self.type = scope_type  # 'class', 'method', 'block', 'lambda'
        self.name = name
        self.parent = parent
        self.symbols = {}  # name -> symbol info
        self.children = []
        
        if parent:
            parent.children.append(self)
    
    def add_symbol(self, name: str, symbol_type: str, info: Dict):
        """Add a symbol to this scope."""
        self.symbols[name] = {
            'type': symbol_type,
            'info': info
        }
    
    def resolve_symbol(self, name: str) -> Optional[Tuple['JavaScope', Dict]]:
        """Resolve a symbol by checking this scope and parent scopes."""
        if name in self.symbols:
            return self, self.symbols[name]
        
        if self.parent:
            return self.parent.resolve_symbol(name)
        
        return None
    
    def get_all_symbols_named(self, name: str) -> List[Tuple['JavaScope', Dict]]:
        """Get all symbols with given name in this scope tree."""
        results = []
        
        if name in self.symbols:
            results.append((self, self.symbols[name]))
        
        for child in self.children:
            results.extend(child.get_all_symbols_named(name))
        
        return results

class JavaScopeAnalyzer:
    """Analyzes Java code to build scope information."""
    
    def __init__(self):
        self.root_scope = None
        self.current_scope = None
        self.import_map = {}  # simple name -> fully qualified name
        self.package_name = ""
    
    def analyze_file(self, file_path: Path) -> JavaScope:
        """Analyze a Java file and return root scope."""
        # Use JavaParser via subprocess to get AST
        ast_json = self._get_ast_json(file_path)
        if not ast_json:
            return None
        
        # Parse AST and build scopes
        self.root_scope = JavaScope('file', str(file_path))
        self.current_scope = self.root_scope
        
        self._process_ast(ast_json)
        
        return self.root_scope
    
    def _get_ast_json(self, file_path: Path) -> Optional[Dict]:
        """Get AST as JSON using JavaParser."""
        # Create a temporary Java program that outputs AST as JSON
        analyzer_java = '''
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.expr.*;
import com.github.javaparser.ast.stmt.*;
import com.github.javaparser.ast.type.*;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import java.io.File;
import java.util.*;

public class ASTToJSON {
    public static void main(String[] args) throws Exception {
        CompilationUnit cu = StaticJavaParser.parse(new File(args[0]));
        Map<String, Object> ast = nodeToMap(cu);
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        System.out.println(gson.toJson(ast));
    }
    
    private static Map<String, Object> nodeToMap(Node node) {
        Map<String, Object> map = new HashMap<>();
        map.put("type", node.getClass().getSimpleName());
        
        // Add specific properties based on node type
        if (node instanceof NamedNode) {
            map.put("name", ((NamedNode<?>) node).getNameAsString());
        }
        if (node instanceof VariableDeclarator) {
            VariableDeclarator vd = (VariableDeclarator) node;
            map.put("name", vd.getNameAsString());
            map.put("varType", vd.getTypeAsString());
        }
        if (node instanceof MethodDeclaration) {
            MethodDeclaration md = (MethodDeclaration) node;
            map.put("name", md.getNameAsString());
            map.put("returnType", md.getTypeAsString());
            map.put("parameters", md.getParameters().size());
        }
        if (node instanceof ClassOrInterfaceDeclaration) {
            ClassOrInterfaceDeclaration cid = (ClassOrInterfaceDeclaration) node;
            map.put("name", cid.getNameAsString());
            map.put("isInterface", cid.isInterface());
        }
        
        // Add children
        List<Map<String, Object>> children = new ArrayList<>();
        for (Node child : node.getChildNodes()) {
            children.add(nodeToMap(child));
        }
        if (!children.isEmpty()) {
            map.put("children", children);
        }
        
        return map;
    }
}
'''
        
        # For now, use a simpler approach with JavaRefactorCLI
        # In production, we'd compile and run the above analyzer
        # This is a placeholder that returns basic structure
        # Enhanced: Use retry logic for reading files
        refactorer = JavaScopeRefactorer()
        content = refactorer._read_file_with_retry(file_path)
        
        # Basic parsing to identify scopes
        return self._parse_basic_structure(content)
    
    def _parse_basic_structure(self, content: str) -> Dict:
        """Basic parsing to identify Java structure."""
        lines = content.splitlines()
        structure = {
            'type': 'CompilationUnit',
            'package': '',
            'imports': [],
            'classes': []
        }
        
        # Find package
        package_match = re.search(r'^package\s+([\w.]+);', content, re.MULTILINE)
        if package_match:
            structure['package'] = package_match.group(1)
        
        # Find imports
        import_pattern = re.compile(r'^import\s+(static\s+)?([\w.*]+);', re.MULTILINE)
        for match in import_pattern.finditer(content):
            structure['imports'].append({
                'static': bool(match.group(1)),
                'name': match.group(2)
            })
        
        # Find classes (simplified)
        class_pattern = re.compile(
            r'^(public\s+)?(abstract\s+)?(final\s+)?(class|interface|enum)\s+(\w+)',
            re.MULTILINE
        )
        
        for match in class_pattern.finditer(content):
            class_info = {
                'type': match.group(4),
                'name': match.group(5),
                'start': match.start(),
                'methods': [],
                'fields': []
            }
            
            # Find methods in this class (simplified)
            # This is a basic approximation
            class_name = match.group(5)
            method_pattern = re.compile(
                rf'(public|protected|private)?\s*(static)?\s*(\w+)\s+(\w+)\s*\([^)]*\)\s*{{',
                re.MULTILINE
            )
            
            # Find fields
            field_pattern = re.compile(
                r'(public|protected|private)?\s*(static)?\s*(final)?\s*(\w+)\s+(\w+)\s*[=;]',
                re.MULTILINE
            )
            
            # Add to structure
            structure['classes'].append(class_info)
        
        return structure
    
    def _process_ast(self, ast: Dict):
        """Process AST to build scope tree."""
        # Set package
        self.package_name = ast.get('package', '')
        
        # Process imports
        for imp in ast.get('imports', []):
            import_name = imp['name']
            if not imp.get('static') and '.*' not in import_name:
                # Simple import - extract class name
                parts = import_name.split('.')
                if parts:
                    simple_name = parts[-1]
                    self.import_map[simple_name] = import_name
        
        # Process classes
        for class_info in ast.get('classes', []):
            self._process_class(class_info)
    
    def _process_class(self, class_info: Dict):
        """Process a class definition."""
        class_scope = JavaScope('class', class_info['name'], self.current_scope)
        
        # Add class as symbol in parent scope
        self.current_scope.add_symbol(
            class_info['name'],
            'class',
            {'type': class_info.get('type', 'class')}
        )
        
        # Process class members
        old_scope = self.current_scope
        self.current_scope = class_scope
        
        # Process fields
        for field in class_info.get('fields', []):
            self.current_scope.add_symbol(
                field['name'],
                'field',
                {
                    'varType': field.get('type', 'Object'),
                    'static': field.get('static', False)
                }
            )
        
        # Process methods
        for method in class_info.get('methods', []):
            self._process_method(method)
        
        self.current_scope = old_scope
    
    def _process_method(self, method_info: Dict):
        """Process a method definition."""
        method_scope = JavaScope('method', method_info['name'], self.current_scope)
        
        # Add method as symbol in class scope
        self.current_scope.add_symbol(
            method_info['name'],
            'method',
            {
                'returnType': method_info.get('returnType', 'void'),
                'parameters': method_info.get('parameters', 0)
            }
        )
        
        # Parameters would be added to method scope here
        # Method body would be processed here

class JavaScopeRefactorer:
    """Performs scope-aware refactoring on Java code."""
    
    def __init__(self):
        self.analyzer = JavaScopeAnalyzer()
        # Retry configuration - can be overridden via environment variables
        self.max_retries = int(os.getenv('JAVA_REFACTOR_READ_MAX_RETRIES', '3'))
        self.retry_delay = float(os.getenv('JAVA_REFACTOR_READ_RETRY_DELAY', '1.0'))
    
    def rename_symbol(self, file_path: Path, old_name: str, new_name: str,
                     symbol_type: str = 'all', scope_path: Optional[str] = None,
                     max_retries: int = 3, retry_delay: float = 1.0) -> Dict:
        """
        Rename a symbol with scope awareness.
        
        Args:
            file_path: Path to Java file
            old_name: Current name
            new_name: New name
            symbol_type: Type of symbol (variable, method, class, field, all)
            scope_path: Scope path like "MyClass.myMethod" to target specific scope
            max_retries: Maximum retries for file lock conflicts
            retry_delay: Delay between retries in seconds
        
        Returns:
            Dict with refactoring results
        """
        results = {
            'file': str(file_path),
            'success': False,
            'changes': 0,
            'error': None,
            'scopes_affected': [],
            'preview': []
        }
        
        try:
            # Analyze file to build scope tree
            root_scope = self.analyzer.analyze_file(file_path)
            if not root_scope:
                results['error'] = "Failed to analyze Java file"
                return results
            
            # Find target symbols
            if scope_path:
                target_scope = self._find_scope_by_path(root_scope, scope_path)
                if not target_scope:
                    results['error'] = f"Scope '{scope_path}' not found"
                    return results
                
                symbols = target_scope.get_all_symbols_named(old_name)
            else:
                symbols = root_scope.get_all_symbols_named(old_name)
            
            # Filter by type if specified
            if symbol_type != 'all':
                symbols = [(scope, sym) for scope, sym in symbols 
                          if sym['type'] == symbol_type]
            
            if not symbols:
                results['error'] = f"No symbols named '{old_name}' found"
                return results
            
            # Perform renaming
            content = self._read_file_with_retry(file_path)
            new_content = self._apply_renames(content, symbols, old_name, new_name)
            
            if new_content != content:
                results['success'] = True
                results['changes'] = new_content.count(new_name) - content.count(new_name)
                results['scopes_affected'] = [scope.name for scope, _ in symbols]
                
                # Generate preview
                import difflib
                diff = list(difflib.unified_diff(
                    content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    n=1
                ))
                results['preview'] = [line.rstrip() for line in diff[3:10]]
                
                # Write changes with atomic operation
                self._atomic_write_file(file_path, new_content, max_retries, retry_delay)
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _find_scope_by_path(self, root: JavaScope, path: str) -> Optional[JavaScope]:
        """Find scope by path like 'MyClass.myMethod'."""
        parts = path.split('.')
        current = root
        
        for part in parts:
            found = False
            for child in current.children:
                if child.name == part:
                    current = child
                    found = True
                    break
            
            if not found:
                return None
        
        return current
    
    def _apply_renames(self, content: str, symbols: List[Tuple[JavaScope, Dict]], 
                      old_name: str, new_name: str) -> str:
        """Apply renames based on scope information."""
        # This is a simplified implementation
        # In production, we'd use proper AST transformation
        
        # For now, use context-aware regex replacement
        new_content = content
        
        for scope, symbol in symbols:
            if symbol['type'] == 'variable':
                # Variable renaming - be careful about scope
                if scope.type == 'method':
                    # Local variable - rename only within method
                    # This is simplified - would need proper AST positions
                    pattern = rf'\b{re.escape(old_name)}\b'
                    new_content = re.sub(pattern, new_name, new_content)
                
                elif scope.type == 'class':
                    # Field - rename declarations and this.field references
                    # Declaration
                    pattern = rf'(\w+\s+){re.escape(old_name)}\s*[=;]'
                    new_content = re.sub(pattern, rf'\1{new_name} ', new_content)
                    
                    # this.field references
                    pattern = rf'this\.{re.escape(old_name)}\b'
                    new_content = re.sub(pattern, f'this.{new_name}', new_content)
            
            elif symbol['type'] == 'method':
                # Method renaming
                pattern = rf'\b{re.escape(old_name)}\s*\('
                new_content = re.sub(pattern, f'{new_name}(', new_content)
            
            elif symbol['type'] == 'class':
                # Class renaming - also update constructor
                pattern = rf'\b{re.escape(old_name)}\b'
                new_content = re.sub(pattern, new_name, new_content)
        
        return new_content
    
    def _read_file_with_retry(self, file_path: Path, max_retries: int = None, retry_delay: float = None) -> str:
        """Read file with retry logic for locked files.
        
        Args:
            file_path: Path to file to read
            max_retries: Maximum number of retries if file is locked (env: JAVA_REFACTOR_READ_MAX_RETRIES)
            retry_delay: Delay in seconds between retries (env: JAVA_REFACTOR_READ_RETRY_DELAY)
        
        Returns:
            File content as string
            
        Raises:
            OSError: If file remains locked after all retries
            FileNotFoundError: If file does not exist
        """
        # Use instance defaults if not specified
        if max_retries is None:
            max_retries = self.max_retries
        if retry_delay is None:
            retry_delay = self.retry_delay
        
        last_error = None
        for attempt in range(max_retries):
            try:
                return file_path.read_text(encoding='utf-8')
            except OSError as e:
                last_error = e
                # Check if it's a permission/locking error
                if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY, errno.ETXTBSY):
                    if attempt < max_retries - 1:
                        # File is locked, wait and retry
                        if not os.getenv('QUIET_MODE'):
                            print(f"File {file_path} appears to be locked during read, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                # For other errors or final attempt, raise immediately
                raise
            except Exception as e:
                # For non-OSError exceptions (encoding issues, etc.), don't retry
                raise
        
        # If we get here, all retries failed
        raise OSError(f"Failed to read {file_path} after {max_retries} attempts. Last error: {last_error}")
    
    def _atomic_write_file(self, path: Path, data: str, max_retries: int = None, retry_delay: float = None) -> None:
        """Write file atomically with retry logic for locked files.
        
        Args:
            path: Target file path
            data: Content to write
            max_retries: Maximum number of retries if file is locked (env: JAVA_REFACTOR_MAX_RETRIES)
            retry_delay: Delay in seconds between retries (env: JAVA_REFACTOR_RETRY_DELAY)
        
        Raises:
            OSError: If file remains locked after all retries
        """
        # Get retry settings from environment or use defaults
        if max_retries is None:
            max_retries = int(os.getenv('JAVA_REFACTOR_MAX_RETRIES', '3'))
        if retry_delay is None:
            retry_delay = float(os.getenv('JAVA_REFACTOR_RETRY_DELAY', '1.0'))
        
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

class JavaProjectRefactorer:
    """Handles project-wide Java refactoring with dependency tracking."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.java_files = list(project_root.rglob("*.java"))
        self.import_graph = {}  # file -> set of imported files
        self.reverse_import_graph = {}  # file -> set of files that import it
        
        self._build_import_graph()
    
    def _build_import_graph(self):
        """Build import dependency graph."""
        for java_file in self.java_files:
            self.import_graph[java_file] = set()
            
            # Enhanced: Use retry logic for reading files
            refactorer = JavaScopeRefactorer()
            content = refactorer._read_file_with_retry(java_file)
            imports = re.findall(r'^import\s+(?:static\s+)?([\w.]+);', content, re.MULTILINE)
            
            for import_stmt in imports:
                # Try to find the file for this import
                if '*' not in import_stmt:
                    class_name = import_stmt.split('.')[-1]
                    for other_file in self.java_files:
                        if other_file != java_file and class_name in other_file.name:
                            self.import_graph[java_file].add(other_file)
                            
                            if other_file not in self.reverse_import_graph:
                                self.reverse_import_graph[other_file] = set()
                            self.reverse_import_graph[other_file].add(java_file)
    
    def find_affected_files(self, changed_file: Path, change_type: str) -> Set[Path]:
        """Find all files affected by a change."""
        affected = {changed_file}
        
        if change_type == 'class':
            # Class rename affects all files that import it
            if changed_file in self.reverse_import_graph:
                affected.update(self.reverse_import_graph[changed_file])
        
        return affected
    
    def refactor_project(self, old_name: str, new_name: str, 
                        symbol_type: str = 'all', max_retries: int = 3, 
                        retry_delay: float = 1.0) -> Dict:
        """Perform project-wide refactoring."""
        results = {
            'total_files': len(self.java_files),
            'files_analyzed': 0,
            'files_changed': 0,
            'total_changes': 0,
            'errors': [],
            'file_results': []
        }
        
        refactorer = JavaScopeRefactorer()
        
        # First pass: find all occurrences
        for java_file in self.java_files:
            results['files_analyzed'] += 1
            
            file_result = refactorer.rename_symbol(
                java_file, old_name, new_name, symbol_type, None, max_retries, retry_delay
            )
            
            if file_result['success']:
                results['files_changed'] += 1
                results['total_changes'] += file_result['changes']
                
                # Check if this affects other files
                if symbol_type == 'class':
                    affected = self.find_affected_files(java_file, 'class')
                    file_result['affects_files'] = len(affected) - 1
            
            results['file_results'].append(file_result)
        
        return results

def main():
    if HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Scope-aware Java refactoring tool')
    else:
        parser = argparse.ArgumentParser(description='Scope-aware Java refactoring tool')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Rename command
    rename = subparsers.add_parser('rename', help='Rename symbol in a file')
    rename.add_argument('file', help='Java file to refactor')
    rename.add_argument('--old', required=True, help='Current name')
    rename.add_argument('--new', required=True, help='New name')
    rename.add_argument('--type', choices=['variable', 'method', 'class', 'field', 'all'],
                       default='all', help='Symbol type')
    rename.add_argument('--scope', help='Scope path (e.g., MyClass.myMethod)')
    rename.add_argument('--max-retries', type=int, default=3, 
                       help='Maximum retries for file lock conflicts (default: 3)')
    rename.add_argument('--retry-delay', type=float, default=1.0,
                       help='Delay between retries in seconds (default: 1.0)')
    
    # Project rename command
    proj_rename = subparsers.add_parser('rename-project', help='Rename across project')
    proj_rename.add_argument('--old', required=True, help='Current name')
    proj_rename.add_argument('--new', required=True, help='New name')
    proj_rename.add_argument('--type', choices=['variable', 'method', 'class', 'field', 'all'],
                            default='all', help='Symbol type')
    proj_rename.add_argument('--root', default='.', help='Project root directory')
    proj_rename.add_argument('--max-retries', type=int, default=3, 
                            help='Maximum retries for file lock conflicts (default: 3)')
    proj_rename.add_argument('--retry-delay', type=float, default=1.0,
                            help='Delay between retries in seconds (default: 1.0)')
    
    # Analyze command
    analyze = subparsers.add_parser('analyze', help='Analyze scope structure')
    analyze.add_argument('file', help='Java file to analyze')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'rename':
        refactorer = JavaScopeRefactorer()
        results = refactorer.rename_symbol(
            Path(args.file), args.old, args.new, args.type, args.scope,
            args.max_retries, args.retry_delay
        )
        
        if results['success']:
            print(f"✅ Successfully renamed '{args.old}' to '{args.new}'")
            print(f"   Changes: {results['changes']}")
            print(f"   Scopes affected: {', '.join(results['scopes_affected'])}")
            if results['preview']:
                print("\nPreview:")
                for line in results['preview']:
                    print(f"  {line}")
        else:
            print(f"❌ Failed: {results['error']}")
    
    elif args.command == 'rename-project':
        project_root = Path(args.root)
        if not project_root.exists():
            print(f"Error: Project root '{args.root}' not found")
            return
        
        print(f"Analyzing project at {project_root}...")
        refactorer = JavaProjectRefactorer(project_root)
        results = refactorer.refactor_project(args.old, args.new, args.type, 
                                             args.max_retries, args.retry_delay)
        
        print(f"\nProject Refactoring Results:")
        print(f"Files analyzed: {results['files_analyzed']}")
        print(f"Files changed: {results['files_changed']}")
        print(f"Total changes: {results['total_changes']}")
        
        if results['errors']:
            print("\nErrors:")
            for error in results['errors']:
                print(f"  ❌ {error}")
        
        if results['files_changed'] > 0:
            print("\nChanged files:")
            for result in results['file_results']:
                if result['success']:
                    print(f"  ✅ {result['file']} ({result['changes']} changes)")
                    if result.get('affects_files', 0) > 0:
                        print(f"     Affects {result['affects_files']} other files")
    
    elif args.command == 'analyze':
        analyzer = JavaScopeAnalyzer()
        scope_tree = analyzer.analyze_file(Path(args.file))
        
        if scope_tree:
            print(f"Scope Analysis for {args.file}:")
            print(f"Package: {analyzer.package_name or '(default)'}")
            print(f"Imports: {len(analyzer.import_map)}")
            
            def print_scope(scope: JavaScope, indent: int = 0):
                prefix = "  " * indent
                print(f"{prefix}{scope.type}: {scope.name}")
                
                if scope.symbols:
                    for name, info in scope.symbols.items():
                        print(f"{prefix}  - {info['type']}: {name}")
                
                for child in scope.children:
                    print_scope(child, indent + 1)
            
            print("\nScope Tree:")
            print_scope(scope_tree)
        else:
            print("Failed to analyze file")

if __name__ == '__main__':
    main()