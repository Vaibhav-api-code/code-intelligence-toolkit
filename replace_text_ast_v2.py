#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced AST-based text replacement tool (v2) with synergistic improvements.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-23
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
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any

# ────────────────────────────  logging  ────────────────────────────
LOG = logging.getLogger("replace_text_ast_v2")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s"
)

# Import shared modules (new in v2)
try:
    from ripgrep_integration import (
        execute_ripgrep_search, find_ripgrep, simple_search,
        regex_search, multi_file_search
    )
    HAS_RIPGREP_INTEGRATION = True
except ImportError:
    HAS_RIPGREP_INTEGRATION = False
    print("Warning: ripgrep_integration module not found. Some features may be limited.", file=sys.stderr)

# Import block extraction (from V7 compatibility)
try:
    from block_extraction import CodeBlockExtractor
    HAS_BLOCK_EXTRACTION = True
except ImportError:
    HAS_BLOCK_EXTRACTION = False
    print("Warning: block_extraction module not found. Block-aware features will be limited.", file=sys.stderr)

try:
    from block_extraction import (
        extract_block_for_line, detect_language,
        format_block_output
    )
    HAS_BLOCK_EXTRACTION = True
except ImportError:
    HAS_BLOCK_EXTRACTION = False
    print("Warning: block_extraction module not found. Block context features disabled.", file=sys.stderr)

try:
    from json_pipeline import (
        load_search_results_from_file, load_search_results_from_stdin,
        SearchResults, SearchMatch, validate_search_results
    )
    HAS_JSON_PIPELINE = True
except ImportError:
    HAS_JSON_PIPELINE = False
    print("Warning: json_pipeline module not found. JSON pipeline features disabled.", file=sys.stderr)

# Enhanced standard argument parser
try:
    from enhanced_standard_arg_parser import create_analyze_parser
    HAS_ENHANCED_PARSER = True
except ImportError:
    try:
        from standard_arg_parser import create_standard_parser as create_parser
        HAS_ENHANCED_PARSER = False
        HAS_STANDARD_PARSER = True
    except ImportError:
        HAS_ENHANCED_PARSER = False
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

# Load common configuration system
try:
    from common_config import load_config, apply_config_to_args
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False
    def load_config():
        return None
    def apply_config_to_args(tool_name, args, parser, config=None):
        pass
    
    def get_config_value(key, default, section, config):
        return default

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

# ────────────────────────────  Enhanced V2 Features  ────────────────────────────

def discover_symbol_locations(symbol_name: str, file_paths: List[str], 
                             language: str = 'auto') -> List[Dict[str, Any]]:
    """
    Use ripgrep to discover all locations where a symbol appears (NEW IN V2).
    
    Args:
        symbol_name: Symbol to search for
        file_paths: List of files to search in
        language: Programming language for context
        
    Returns:
        List of symbol locations with metadata
    """
    if not HAS_RIPGREP_INTEGRATION:
        LOG.warning("Ripgrep integration not available, using basic search")
        return []
    
    try:
        # Use word boundary search to find exact symbol matches
        pattern = rf'\b{re.escape(symbol_name)}\b'
        
        all_results = []
        for file_path in file_paths:
            results = regex_search(pattern, file_path, context=2)
            
            # Enhance results with language-specific information
            for result in results:
                result['symbol_name'] = symbol_name
                result['language'] = detect_language(file_path) if language == 'auto' else language
                
                # Add block context if available
                if HAS_BLOCK_EXTRACTION:
                    try:
                        with open(result['file_path'], 'r', encoding='utf-8') as f:
                            content = f.read()
                        block = extract_block_for_line(result['file_path'], content, result['line_number'])
                        if block:
                            result['block_context'] = {
                                'block_type': block['block_type'],
                                'start_line': block['start_line'],
                                'end_line': block['end_line']
                            }
                    except Exception:
                        pass
                
                all_results.append(result)
        
        return all_results
        
    except Exception as e:
        LOG.error(f"Symbol discovery failed: {e}")
        return []

def analyze_symbol_scope_context(file_path: str, symbol_name: str, 
                                target_line: int) -> Dict[str, Any]:
    """
    Enhanced scope analysis with block and AST context (NEW IN V2).
    
    Args:
        file_path: Path to file
        symbol_name: Symbol being analyzed
        target_line: Line number of symbol declaration/usage
        
    Returns:
        Enhanced scope context information
    """
    context = {
        'symbol_name': symbol_name,
        'target_line': target_line,
        'file_path': file_path,
        'language': detect_language(file_path),
        'ast_context': None,
        'block_context': None,
        'scope_type': 'unknown'
    }
    
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add AST context if available
        if HAS_AST_CONTEXT:
            try:
                context_finder = ASTContextFinder()
                context_parts = context_finder.get_context_for_line(file_path, target_line)
                if context_parts:
                    context['ast_context'] = context_finder._format_context_parts(context_parts)
                    
                    # Determine scope type from AST context
                    for part in context_parts:
                        if part.node_type == 'class':
                            context['class_name'] = part.name
                        elif part.node_type in ['method', 'function']:
                            context['method_name'] = part.name
                            context['scope_type'] = 'method'
                        elif part.node_type == 'module':
                            context['scope_type'] = 'module'
            except Exception as e:
                LOG.debug(f"AST context extraction failed: {e}")
        
        # Add block context if available
        if HAS_BLOCK_EXTRACTION:
            try:
                block = extract_block_for_line(file_path, content, target_line)
                if block:
                    context['block_context'] = {
                        'block_type': block['block_type'],
                        'start_line': block['start_line'],
                        'end_line': block['end_line'],
                        'line_count': block['line_count']
                    }
            except Exception as e:
                LOG.debug(f"Block context extraction failed: {e}")
        
        return context
        
    except Exception as e:
        LOG.error(f"Scope context analysis failed: {e}")
        return context

def process_json_pipeline_for_ast(json_input: str) -> List[Dict[str, Any]]:
    """
    Process JSON pipeline input for AST-based operations (NEW IN V2).
    
    Args:
        json_input: JSON input from find_text or file path
        
    Returns:
        List of enhanced symbol locations
    """
    if not HAS_JSON_PIPELINE:
        raise ValueError("JSON pipeline support not available")
    
    try:
        if json_input == '-':
            results = load_search_results_from_stdin()
        elif os.path.isfile(json_input):
            results = load_search_results_from_file(json_input)
        else:
            from json_pipeline import deserialize_search_results
            results = deserialize_search_results(json_input)
        
        # Validate results
        errors = validate_search_results(results)
        if errors:
            raise ValueError(f"Invalid search results: {'; '.join(errors)}")
        
        # Convert to enhanced symbol locations
        locations = []
        for match in results.matches:
            location = {
                'file_path': match.file_path,
                'line_number': match.line_number,
                'content': match.content,
                'symbol_name': results.search_pattern,  # Assume pattern is the symbol
                'language': detect_language(match.file_path),
                'source': 'find_text_pipeline'
            }
            
            # Add existing context if available
            if match.context:
                if match.context.ast_context:
                    location['ast_context'] = match.context.ast_context
                if match.context.block_type:
                    location['block_context'] = {
                        'block_type': match.context.block_type,
                        'start_line': match.context.block_start,
                        'end_line': match.context.block_end
                    }
                if match.context.method_name:
                    location['method_name'] = match.context.method_name
                if match.context.class_name:
                    location['class_name'] = match.context.class_name
            
            locations.append(location)
        
        return locations
        
    except Exception as e:
        raise ValueError(f"Error processing JSON pipeline for AST: {e}")

def enhanced_scope_aware_rename(file_path: str, old_name: str, new_name: str,
                               target_line: int, language: str = 'auto',
                               scope_context: Dict[str, Any] = None) -> Tuple[str, int]:
    """
    Enhanced scope-aware renaming with improved context analysis (NEW IN V2).
    
    Args:
        file_path: Path to file
        old_name: Original symbol name
        new_name: New symbol name  
        target_line: Line number of symbol declaration
        language: Programming language
        scope_context: Enhanced scope context from analysis
        
    Returns:
        Modified content and number of replacements
    """
    # Get enhanced scope context if not provided
    if not scope_context:
        scope_context = analyze_symbol_scope_context(file_path, old_name, target_line)
    
    # Log the enhanced context for debugging
    if not os.getenv('QUIET_MODE'):
        print(f"🔍 Enhanced scope analysis for '{old_name}':")
        print(f"   Language: {scope_context['language']}")
        print(f"   Scope type: {scope_context['scope_type']}")
        if scope_context.get('ast_context'):
            print(f"   AST context: {scope_context['ast_context']}")
        if scope_context.get('block_context'):
            print(f"   Block: {scope_context['block_context']['block_type']} "
                  f"(lines {scope_context['block_context']['start_line']}-{scope_context['block_context']['end_line']})")
    
    # Use the original AST rename function but with enhanced context
    try:
        return perform_ast_rename(
            file_path, old_name, new_name, target_line, 
            scope_context['language'], dry_run=False
        )
    except Exception as e:
        LOG.error(f"Enhanced AST rename failed: {e}")
        raise

def batch_symbol_rename(symbol_locations: List[Dict[str, Any]], old_name: str, 
                       new_name: str, confirm_each: bool = True,
                       non_interactive: bool = False, auto_yes: bool = False) -> Dict[str, Any]:
    """
    Perform batch symbol renaming across multiple locations (NEW IN V2).
    
    Args:
        symbol_locations: List of symbol locations from discovery
        old_name: Original symbol name
        new_name: New symbol name
        confirm_each: Whether to confirm each file individually
        
    Returns:
        Batch operation results
    """
    results = {
        'total_files': 0,
        'successful_files': 0,
        'failed_files': 0,
        'total_replacements': 0,
        'file_results': [],
        'errors': []
    }
    
    # Group locations by file
    files_map = {}
    for location in symbol_locations:
        file_path = location['file_path']
        if file_path not in files_map:
            files_map[file_path] = []
        files_map[file_path].append(location)
    
    results['total_files'] = len(files_map)
    
    # Process each file
    for file_path, locations in files_map.items():
        try:
            # Show file info
            print(f"\n📁 Processing {file_path}")
            print(f"   Found {len(locations)} location(s) of '{old_name}'")
            
            # Show locations with context
            for i, loc in enumerate(locations, 1):
                print(f"   {i}. Line {loc['line_number']}: {loc['content'].strip()}")
                if loc.get('ast_context'):
                    print(f"      Context: {loc['ast_context']}")
            
            # Confirm if requested
            if confirm_each and not auto_yes:
                if non_interactive:
                    print(f"\n❌ Cannot prompt for confirmation in non-interactive mode")
                    print("💡 Use --yes or --no-confirm to skip prompts")
                    print("Skipping file.")
                    continue
                    
                try:
                    response = input(f"\nRename '{old_name}' to '{new_name}' in this file? [y/N/q] ")
                    if response.lower() == 'q':
                        print("Batch operation cancelled.")
                        break
                    elif response.lower() != 'y':
                        print("Skipping file.")
                        continue
                except (EOFError, KeyboardInterrupt):
                    print("\nBatch operation cancelled.")
                    break
            
            # Use the first location's line number for scope analysis
            # (assuming all are in the same scope - could be enhanced)
            primary_location = locations[0]
            
            # Perform the rename
            modified_content, replacements = enhanced_scope_aware_rename(
                file_path, old_name, new_name, 
                primary_location['line_number'],
                primary_location.get('language', 'auto'),
                primary_location
            )
            
            if replacements > 0:
                # Write the modified content
                try:
                    _atomic_write(Path(file_path), modified_content, bak=True)
                    results['successful_files'] += 1
                    results['total_replacements'] += replacements
                    
                    file_result = {
                        'file_path': file_path,
                        'status': 'success',
                        'replacements': replacements,
                        'locations_processed': len(locations)
                    }
                    results['file_results'].append(file_result)
                    
                    print(f"✅ Successfully renamed {replacements} occurrence(s)")
                    
                except Exception as e:
                    results['failed_files'] += 1
                    error_msg = f"Failed to write {file_path}: {e}"
                    results['errors'].append(error_msg)
                    print(f"❌ {error_msg}")
            else:
                print("ℹ️  No changes needed")
                
        except Exception as e:
            results['failed_files'] += 1
            error_msg = f"Error processing {file_path}: {e}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    return results

# ────────────────────────────  Original AST Classes and Functions (Preserved)  ────────────────────────────

class PythonScopeAnalyzer:
    """Analyzes Python code to understand variable scopes."""
    
    def __init__(self, code: str):
        self.code = code
        self.tree = None
        self.scopes = {}
        self.scope_hierarchy = {}
        self.variable_declarations = {}
        
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
                self.analyzer.scope_hierarchy['module'] = None
                
            def visit_FunctionDef(self, node):
                parent_scope = self.current_scope
                self.scope_stack.append(self.current_scope)
                self.current_scope = f"function:{node.name}:{node.lineno}"
                
                self.analyzer.scope_hierarchy[self.current_scope] = parent_scope
                
                for arg in node.args.args:
                    self.analyzer.scopes[(arg.lineno, arg.arg)] = {
                        'scope': self.current_scope,
                        'type': 'parameter',
                        'declaration_line': arg.lineno
                    }
                    if arg.arg not in self.analyzer.variable_declarations:
                        self.analyzer.variable_declarations[arg.arg] = []
                    self.analyzer.variable_declarations[arg.arg].append(
                        (arg.lineno, self.current_scope)
                    )
                
                self.generic_visit(node)
                self.current_scope = self.scope_stack.pop()
                
            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)
                
            def visit_ClassDef(self, node):
                parent_scope = self.current_scope
                self.scope_stack.append(self.current_scope)
                self.current_scope = f"class:{node.name}:{node.lineno}"
                
                self.analyzer.scope_hierarchy[self.current_scope] = parent_scope
                
                self.generic_visit(node)
                self.current_scope = self.scope_stack.pop()
                
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store):
                    key = (node.lineno, node.id)
                    if key not in self.analyzer.scopes:
                        self.analyzer.scopes[key] = {
                            'scope': self.current_scope,
                            'type': 'variable',
                            'declaration_line': node.lineno
                        }
                        if node.id not in self.analyzer.variable_declarations:
                            self.analyzer.variable_declarations[node.id] = []
                        self.analyzer.variable_declarations[node.id].append(
                            (node.lineno, self.current_scope)
                        )
                
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                if (isinstance(node.ctx, ast.Store) and 
                    isinstance(node.value, ast.Name) and node.value.id == 'self'):
                    key = (node.lineno, node.attr)
                    if key not in self.analyzer.scopes:
                        self.analyzer.scopes[key] = {
                            'scope': self.current_scope,
                            'type': 'instance_variable',
                            'declaration_line': node.lineno
                        }
                        if node.attr not in self.analyzer.variable_declarations:
                            self.analyzer.variable_declarations[node.attr] = []
                        self.analyzer.variable_declarations[node.attr].append(
                            (node.lineno, self.current_scope)
                        )
                
                self.generic_visit(node)
                
            def visit_For(self, node):
                if isinstance(node.target, ast.Name):
                    self.analyzer.scopes[(node.target.lineno, node.target.id)] = {
                        'scope': self.current_scope,
                        'type': 'loop_variable',
                        'declaration_line': node.target.lineno
                    }
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
        best_match = None
        best_line = -1
        
        for (line, name), scope_info in self.scopes.items():
            if name == var_name and line <= line_number:
                if line > best_line:
                    best_match = scope_info
                    best_line = line
        
        return best_match
    
    def is_scope_accessible_from(self, target_scope: str, current_scope: str) -> bool:
        """Check if a variable in target_scope is accessible from current_scope."""
        if target_scope == current_scope:
            return True
        
        checking_scope = current_scope
        visited = set()
        
        while checking_scope is not None and checking_scope not in visited:
            visited.add(checking_scope)
            parent_scope = self.scope_hierarchy.get(checking_scope)
            if parent_scope == target_scope:
                return True
            checking_scope = parent_scope
        
        return False
    
    def find_accessible_variable_scope(self, var_name: str, line_number: int, current_scope: str) -> Optional[Dict]:
        """Find the most specific scope where var_name is declared and accessible from current_scope."""
        candidates = []
        for (line, name), scope_info in self.scopes.items():
            if name == var_name and line <= line_number:
                candidates.append((line, scope_info))
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        for line, scope_info in candidates:
            declaring_scope = scope_info['scope']
            
            if (declaring_scope == current_scope or 
                self.is_scope_accessible_from(declaring_scope, current_scope)):
                return scope_info
        
        return None
    
    def rename_variable_in_scope(self, var_name: str, new_name: str, 
                               declaration_line: int) -> Tuple[str, int]:
        """Rename a variable only within its scope."""
        if not self.tree:
            raise ValueError("Code not analyzed yet")
        
        scope_info = self.find_variable_scope(var_name, declaration_line)
        if not scope_info:
            return self.code, 0
        
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
                if node.id == self.target_name:
                    if isinstance(node.ctx, ast.Store):
                        if self.current_scope == self.target_scope:
                            node.id = self.new_name
                            self.replacements += 1
                    elif isinstance(node.ctx, ast.Load):
                        resolved_scope = self.analyzer.find_accessible_variable_scope(
                            node.id, node.lineno, self.current_scope
                        )
                        if resolved_scope and resolved_scope['scope'] == self.target_scope:
                            node.id = self.new_name
                            self.replacements += 1
                return node
            
            def visit_Attribute(self, node):
                if (isinstance(node.value, ast.Name) and node.value.id == 'self' and
                    node.attr == self.target_name and 
                    self.current_scope == self.target_scope):
                    node.attr = self.new_name
                    self.replacements += 1
                self.generic_visit(node)
                return node
        
        transformer = RenameTransformer(var_name, new_name, scope_info['scope'], self)
        new_tree = transformer.visit(copy.deepcopy(self.tree))
        
        if hasattr(ast, 'unparse'):
            new_code = ast.unparse(new_tree)
        else:
            new_code = self._manual_scope_rename(var_name, new_name, scope_info)
            transformer.replacements = new_code.count(new_name) - self.code.count(new_name)
        
        return new_code, transformer.replacements
    
    def _manual_scope_rename(self, var_name: str, new_name: str, 
                           scope_info: Dict) -> str:
        """Manual scope-aware renaming for older Python versions."""
        lines = self.code.splitlines()
        
        if scope_info['scope'].startswith('function:'):
            func_name = scope_info['scope'].split(':')[1]
            func_line = int(scope_info['scope'].split(':')[2])
            
            pattern = r'\b' + re.escape(var_name) + r'\b'
            replacement_count = 0
            in_function = False
            brace_level = 0
            
            for i in range(len(lines)):
                if i + 1 >= func_line:
                    if 'def ' + func_name in lines[i]:
                        in_function = True
                    
                    if in_function:
                        if lines[i].strip() and not lines[i].startswith(' '):
                            break
                        
                        lines[i] = re.sub(pattern, new_name, lines[i])
        
        return '\n'.join(lines)

def java_ast_rename_with_engine(file_path: str, old_name: str, new_name: str,
                                line_number: int, is_method: bool = False,
                                source_dirs: Optional[List[str]] = None,
                                jar_paths: Optional[List[str]] = None,
                                dry_run: bool = False) -> Tuple[str, int]:
    """Performs scope-aware rename by calling the external Java refactoring engine."""
    spoon_engine_path = os.path.join(os.path.dirname(__file__), 'spoon-refactor-engine.jar')
    
    engine_jar_path = None
    engine_type = None
    
    if os.path.exists(spoon_engine_path):
        engine_jar_path = spoon_engine_path
        engine_type = 'spoon'
        print("Info: Using Spoon refactoring engine", file=sys.stderr)
    else:
        print("Warning: Spoon refactoring engine not found. Using basic refactoring.", file=sys.stderr)
        print("To enable Spoon-based Java refactoring, run: ./build_java_engine_gradle.sh", file=sys.stderr)
    
    if engine_jar_path is None:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        analyzer = JavaScopeAnalyzer(content)
        analyzer.analyze()
        return analyzer.rename_variable_in_scope(old_name, new_name, line_number)

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
            
        if source_dirs:
            for src_dir in source_dirs:
                cmd.extend(['--source-dir', src_dir])
                
        if jar_paths:
            for jar in jar_paths:
                cmd.extend(['--jar', jar])
    else:
        cmd = [
            'java', '-jar', engine_jar_path,
            str(file_path), str(line_number), old_name, new_name
        ]
        
        if is_method:
            cmd.append('--method')

    try:
        if os.environ.get('DEBUG_SPOON'):
            print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr)
            
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if os.environ.get('DEBUG_SPOON'):
            print(f"DEBUG: Return code: {result.returncode}", file=sys.stderr)
            print(f"DEBUG: Stdout length: {len(result.stdout)}", file=sys.stderr)
            print(f"DEBUG: Stderr: {result.stderr}", file=sys.stderr)
        
        if result.returncode != 0:
            print(f"Warning: Java refactoring engine failed (return code {result.returncode}): {result.stderr}", file=sys.stderr)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            analyzer = JavaScopeAnalyzer(content)
            analyzer.analyze()
            return analyzer.rename_variable_in_scope(old_name, new_name, line_number)
        
        modified_content = result.stdout
        
        if not modified_content or not modified_content.strip():
            print(f"Warning: Java refactoring engine returned empty output. Checking for output files...", file=sys.stderr)
            print(f"Engine stderr: {result.stderr}", file=sys.stderr)
            
            result_file = file_path + ".spoon_result"
            if os.path.exists(result_file):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    if file_content and file_content.strip():
                        print(f"Found result in {result_file}, using it instead of stdout", file=sys.stderr)
                        modified_content = file_content
                        os.remove(result_file)
                    else:
                        print(f"Result file {result_file} is empty", file=sys.stderr)
                except Exception as e:
                    print(f"Error reading result file {result_file}: {e}", file=sys.stderr)
            
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
        
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        if len(modified_content) < len(original_content) * 0.5:
            print(f"Warning: Modified content is suspiciously small ({len(modified_content)} vs {len(original_content)} chars). Falling back to basic approach.", file=sys.stderr)
            analyzer = JavaScopeAnalyzer(original_content)
            analyzer.analyze()
            return analyzer.rename_variable_in_scope(old_name, new_name, line_number)
        
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
        scope_path = []
        
        for path, node in self.tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                scope_path = [f"class:{node.name}"]
            elif isinstance(node, javalang.tree.MethodDeclaration):
                if scope_path:
                    current_scope = f"{scope_path[0]}.method:{node.name}"
                else:
                    current_scope = f"method:{node.name}"
                    
                for param in node.parameters:
                    if hasattr(node, 'position'):
                        self.scopes[(node.position.line, param.name)] = {
                            'scope': current_scope,
                            'type': 'parameter'
                        }
            elif isinstance(node, javalang.tree.LocalVariableDeclaration):
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
        lines = self.code.splitlines()
        pattern = r'\b' + re.escape(var_name) + r'\b'
        replacements = 0
        
        scope_info = None
        for (line, name), info in self.scopes.items():
            if name == var_name and line == declaration_line:
                scope_info = info
                break
        
        if not scope_info:
            return self.code, 0
        
        if 'method:' in scope_info['scope']:
            method_name = scope_info['scope'].split('method:')[1]
            in_method = False
            brace_count = 0
            
            for i in range(len(lines)):
                if method_name in lines[i] and '(' in lines[i]:
                    in_method = True
                
                if in_method:
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    
                    new_line, count = re.subn(pattern, new_name, lines[i])
                    if count > 0:
                        lines[i] = new_line
                        replacements += count
                    
                    if brace_count == 0 and '{' in ' '.join(lines[:i+1]):
                        break
        
        return '\n'.join(lines), replacements

def perform_ast_rename(file_path: str, old_name: str, new_name: str, 
                      line_number: int, language: str = 'auto', dry_run: bool = False,
                      use_rope: bool = False, source_dirs: Optional[List[str]] = None,
                      jar_paths: Optional[List[str]] = None) -> Tuple[str, int]:
    """Perform AST-based scope-aware variable renaming."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")
    
    if language == 'auto':
        file_path_str = str(file_path)
        if file_path_str.endswith('.py'):
            language = 'python'
        elif file_path_str.endswith('.java'):
            language = 'java'
        else:
            raise ValueError("Cannot auto-detect language. Please specify --language")
    
    if language == 'python':
        if ROPE_AVAILABLE:
            try:
                return rope_rename_variable(file_path, old_name, new_name, line_number, dry_run)
            except Exception as e:
                print(f"Warning: Rope failed ({e}), falling back to built-in AST", file=sys.stderr)
        
        analyzer = PythonScopeAnalyzer(content)
        analyzer.analyze()
        return analyzer.rename_variable_in_scope(old_name, new_name, line_number)
    
    elif language == 'java':
        return java_ast_rename_with_engine(file_path, old_name, new_name, line_number, 
                                         source_dirs=source_dirs, jar_paths=jar_paths, dry_run=dry_run)
    
    else:
        raise ValueError(f"Unsupported language: {language}")

def rope_rename_variable(file_path: str, old_name: str, new_name: str, 
                        line_number: int, dry_run: bool = False) -> Tuple[str, int]:
    """Use rope library for advanced Python refactoring."""
    import re
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            file_path_obj = Path(file_path).resolve()
            temp_file = Path(temp_dir) / file_path_obj.name
            shutil.copy2(file_path_obj, temp_file)
            
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
            
            project = rope.base.project.Project(
                temp_dir, 
                ropefolder=None,
                prefs=prefs
            )
            
            resource = project.get_file(temp_file.name)
            
            content = resource.read()
            lines = content.splitlines(keepends=True)
        
            if line_number > len(lines):
                raise ValueError(f"Line {line_number} does not exist in file")
            
            line_start_offset = sum(len(line) for line in lines[:line_number-1])
            line_content = lines[line_number-1]
            
            match = re.search(r'\b' + re.escape(old_name) + r'\b', line_content)
            if not match:
                raise ValueError(f"Variable '{old_name}' not found on line {line_number}")
            
            offset = line_start_offset + match.start()
            
            rename = rope.refactor.rename.Rename(project, resource, offset)
            
            changes = rename.get_changes(new_name)
            
            if dry_run:
                project.do(changes)
                new_content = resource.read()
            else:
                project.do(changes)
                new_content = resource.read()
                shutil.copy2(temp_file, file_path_obj)
            
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

# ────────────────────────────  Utility Functions (Preserved)  ────────────────────────────

def is_file_locked(filepath):
    """Check if a file is currently locked for writing."""
    import platform
    
    if platform.system() != 'Windows':
        try:
            with open(filepath, 'r+b') as f:
                try:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    return False, None
                except IOError:
                    try:
                        result = subprocess.run(['lsof', '-t', str(filepath)], 
                                              capture_output=True, text=True, timeout=1)
                        if result.returncode == 0 and result.stdout.strip():
                            pids = result.stdout.strip().split('\n')
                            return True, f"locked by process(es): {', '.join(pids)}"
                    except:
                        pass
                    return True, "locked by another process"
                except ImportError:
                    pass
        except PermissionError:
            return True, "permission denied"
        except Exception:
            pass
    
    try:
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
    
    try:
        os.rename(str(filepath), str(filepath))
        return False, None
    except OSError:
        return True, "file is in use"
    except Exception:
        pass
    
    return False, None

def _atomic_write(path: Path, data: str, bak: bool = False, max_retries: int = 3, retry_delay: float = 1.0) -> None:
    """Write atomically with retry logic for locked files."""
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    tmp = Path(tmp_path)
    
    try:
        with os.fdopen(tmp_fd, 'w', encoding='utf-8', newline='') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        try:
            os.close(tmp_fd)
        except:
            pass
        try:
            tmp.unlink()
        except:
            pass
        raise
    
    if bak and path.exists():
        try:
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        except Exception as e:
            try:
                tmp.unlink()
            except:
                pass
            raise Exception(f"Failed to create backup: {e}")
    
    last_error = None
    for attempt in range(max_retries):
        try:
            os.replace(str(tmp), str(path))
            return
        except OSError as e:
            last_error = e
            if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY, errno.ETXTBSY):
                if attempt < max_retries - 1:
                    if not os.getenv('QUIET_MODE'):
                        print(f"File {path} appears to be locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
            try:
                tmp.unlink()
            except:
                pass
            raise
    
    try:
        tmp.unlink()
    except:
        pass
    raise OSError(f"Failed to write {path} after {max_retries} attempts: {last_error}")

def check_compile_status(file_path, language=None):
    """Check if file compiles/has valid syntax."""
    try:
        path = Path(file_path)
        if not path.exists():
            return True, "File not found"
        
        try:
            file_size = path.stat().st_size
            if file_size > 10 * 1024 * 1024:
                return False, "Cannot check - file too large"
        except OSError:
            return False, "Cannot check - size unknown"
        
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
                return False, "Cannot check - unknown language"
        
        if language == 'python':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
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
        
        elif language == 'java':
            try:
                result = subprocess.run(
                    ['javac', '-version'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode != 0:
                    return False, "Cannot check - javac unavailable"
                
                result = subprocess.run(
                    ['javac', '-cp', '.', str(file_path)],
                    capture_output=True, text=True, timeout=30
                )
                
                class_file = path.with_suffix('.class')
                if class_file.exists():
                    try:
                        class_file.unlink()
                    except OSError:
                        pass
                
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
        
        elif language in ['javascript', 'typescript']:
            try:
                if language == 'javascript':
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
                else:
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
        
        return False, "Cannot check - unsupported language"
    
    except Exception:
        return False, "Cannot check - internal error"

def show_diff(original: str, modified: str, file_path: str, show_ast_context: bool = False) -> bool:
    """Show unified diff of changes with enhanced AST context display (V2)."""
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
        
        # V2 ENHANCEMENT: Enhanced AST context display
        context_finder = None
        if show_ast_context and HAS_AST_CONTEXT:
            try:
                context_finder = ASTContextFinder()
            except Exception:
                pass
        
        for line in diff_lines:
            # Extract line number and enhance with context
            if line.startswith('@@') and context_finder:
                match = re.search(r'\+([0-9]+)', line)
                if match:
                    line_num = int(match.group(1))
                    try:
                        context_parts = context_finder.get_context_for_line(file_path, line_num)
                        if context_parts:
                            context = context_finder._format_context_parts(context_parts)
                            
                            # V2: Add block context if available
                            block_info = ""
                            if HAS_BLOCK_EXTRACTION:
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    block = extract_block_for_line(file_path, content, line_num)
                                    if block:
                                        block_info = f" | {block['block_type']} block"
                                except Exception:
                                    pass
                            
                            print(f"{line.rstrip()} [{context}{block_info}]")
                            continue
                    except Exception:
                        pass
            
            print(line.rstrip())
    
    return bool(diff_lines)

# ────────────────────────────  Main Function  ────────────────────────────

# ═══════════════════════════════════════════════════════════════════════════════
# V7 COMPATIBILITY FUNCTIONS (copied from replace_text_v7.py)
# ═══════════════════════════════════════════════════════════════════════════════

def get_files_to_process_git(git_only: bool, staged_only: bool, language: str = None) -> List[str]:
    """Get files from git (from V7 compatibility)."""
    if not (git_only or staged_only):
        return []
    
    try:
        import subprocess
        # NOTE: Using direct git for read-only operation (getting repository root)
        # This is a safe operation that doesn't modify repository state
        git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], 
                                         text=True, stderr=subprocess.PIPE).strip()
        original_dir = os.getcwd()
        os.chdir(git_root)
        
        try:
            if staged_only:
                cmd = ['git', 'diff', '--name-only', '--cached']
            else:
                cmd = ['git', 'ls-files']
            
            result = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
            files = []
            
            # Language extensions mapping
            language_extensions = {
                'python': ['.py'], 'java': ['.java'], 'javascript': ['.js'], 
                'typescript': ['.ts'], 'cpp': ['.cpp', '.cc', '.cxx'], 'c': ['.c'],
                'go': ['.go'], 'rust': ['.rs'], 'ruby': ['.rb'], 'php': ['.php'],
                'sql': ['.sql'], 'lua': ['.lua']
            }
            
            for line in result.strip().split('\n'):
                if line:
                    file_path = Path(git_root) / line
                    if file_path.exists() and file_path.is_file():
                        if language:
                            if any(file_path.suffix == ext for ext in language_extensions.get(language, [])):
                                files.append(str(file_path))
                        else:
                            files.append(str(file_path))
            
            return files
            
        finally:
            os.chdir(original_dir)
            
    except subprocess.CalledProcessError:
        return []
    except Exception:
        return []

def get_comment_patterns(language: str = None) -> Dict[str, List[str]]:
    """Get comment patterns for different languages (from V7 compatibility)."""
    patterns = {
        'python': [r'#.*$'],
        'java': [r'//.*$', r'/\*.*?\*/'],
        'javascript': [r'//.*$', r'/\*.*?\*/'],
        'typescript': [r'//.*$', r'/\*.*?\*/'],
        'cpp': [r'//.*$', r'/\*.*?\*/'],
        'c': [r'/\*.*?\*/'],
        'go': [r'//.*$', r'/\*.*?\*/'],
        'rust': [r'//.*$', r'/\*.*?\*/'],
        'ruby': [r'#.*$'],
        'php': [r'//.*$', r'/\*.*?\*/', r'#.*$'],
        'sql': [r'--.*$', r'/\*.*?\*/'],
        'lua': [r'--.*$'],
        'default': [r'#.*$', r'//.*$', r'/\*.*?\*/']
    }
    return patterns.get(language, patterns['default'])

def get_string_patterns(language: str = None) -> Dict[str, List[str]]:
    """Get string literal patterns for different languages (from V7 compatibility).""" 
    patterns = {
        'python': [r"'([^'\\]|\\.)*'", r'"([^"\\]|\\.)*"', r'""".*?"""', r"'''.*?'''"],
        'java': [r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'"],
        'javascript': [r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'", r'`([^`\\]|\\.)*`'],
        'typescript': [r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'", r'`([^`\\]|\\.)*`'],
        'cpp': [r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'"],
        'c': [r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'"],
        'go': [r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'", r'`[^`]*`'],
        'rust': [r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'"],
        'ruby': [r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'"],
        'php': [r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'"],
        'sql': [r"'([^'\\]|\\.)*'"],
        'lua': [r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'"],
        'default': [r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'"]
    }
    return patterns.get(language, patterns['default'])

def interpret_escape_sequences(text):
    """
    Interpret common escape sequences in the text.
    Supports: \\n (newline), \\t (tab), \\r (carriage return), \\\\ (backslash),
              \\b (backspace), \\f (form feed), \\v (vertical tab), \\0 (null),
              \\xHH (hex), \\uHHHH (unicode), \\UHHHHHHHH (unicode)
    """
    if not isinstance(text, str):
        return text
    
    try:
        # First handle the double backslash to avoid conflicts
        text = text.replace('\\\\', '\x00')  # Temporary placeholder
        
        # Replace simple escape sequences
        replacements = {
            '\\n': '\n',
            '\\t': '\t', 
            '\\r': '\r',
            '\\b': '\b',
            '\\f': '\f',
            '\\v': '\v',
            '\\0': '\0',
            '\\"': '"',
            "\\'": "'"
        }
        
        result = text
        for escaped, actual in replacements.items():
            result = result.replace(escaped, actual)
        
        # Handle hex sequences (\xHH)
        hex_pattern = r'\\x([0-9a-fA-F]{2})'
        result = re.sub(hex_pattern, lambda m: chr(int(m.group(1), 16)), result)
        
        # Handle unicode sequences (\uHHHH)
        unicode_pattern = r'\\u([0-9a-fA-F]{4})'
        result = re.sub(unicode_pattern, lambda m: chr(int(m.group(1), 16)), result)
        
        # Handle long unicode sequences (\UHHHHHHHH)
        long_unicode_pattern = r'\\U([0-9a-fA-F]{8})'
        result = re.sub(long_unicode_pattern, lambda m: chr(int(m.group(1), 16)), result)
        
        # Restore double backslash
        result = result.replace('\x00', '\\')
        
        return result
        
    except Exception as e:
        # If any error occurs, log it and return original text
        LOG.warning(f"Error interpreting escape sequences: {e}")
        return text

def replace_in_comments(content: str, old_text: str, new_text: str, language: str = None) -> Tuple[str, int]:
    """Replace text only within comments (from V7 compatibility)."""
    if not content:
        return content, 0
    
    total_replacements = 0
    modified_content = content
    comment_patterns = get_comment_patterns(language)
    
    for pattern in comment_patterns:
        def replace_match(match):
            nonlocal total_replacements
            comment_text = match.group(0)
            if old_text in comment_text:
                new_comment = comment_text.replace(old_text, new_text)
                total_replacements += comment_text.count(old_text)
                return new_comment
            return comment_text
        
        modified_content = re.sub(pattern, replace_match, modified_content, flags=re.DOTALL | re.MULTILINE)
    
    return modified_content, total_replacements

def replace_in_strings(content: str, old_text: str, new_text: str, language: str = None) -> Tuple[str, int]:
    """Replace text only within string literals (from V7 compatibility)."""
    if not content:
        return content, 0
    
    total_replacements = 0
    modified_content = content
    string_patterns = get_string_patterns(language)
    
    for pattern in string_patterns:
        def replace_match(match):
            nonlocal total_replacements
            string_text = match.group(0)
            if old_text in string_text:
                new_string = string_text.replace(old_text, new_text)
                total_replacements += string_text.count(old_text)
                return new_string
            return string_text
        
        modified_content = re.sub(pattern, replace_match, modified_content, flags=re.DOTALL)
    
    return modified_content, total_replacements

def apply_block_aware_replacement(file_path: str, content: str, old_text: str, new_text: str,
                                 block_mode: str = 'preserve', target_lines: List[int] = None) -> Tuple[str, int]:
    """Apply replacement with block awareness (from V7 compatibility)."""
    if block_mode == 'preserve' or not HAS_BLOCK_EXTRACTION:
        # Standard replacement - just do simple text replacement for AST context
        return content.replace(old_text, new_text), content.count(old_text)
    
    # For more complex block modes, would need full block extraction implementation
    # For now, fallback to simple replacement
    LOG.warning(f"Block mode '{block_mode}' requires block_extraction module. Using simple replacement.")
    return content.replace(old_text, new_text), content.count(old_text)

# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Enhanced main function with v2 features."""
    # Use enhanced parser if available
    if HAS_ENHANCED_PARSER:
        parser = create_analyze_parser('Enhanced AST replacement tool (v2) with symbol discovery and batch operations')
    elif HAS_STANDARD_PARSER:
        parser = create_parser('analyze', 'Enhanced AST replacement tool (v2) with symbol discovery and batch operations')
    else:
        parser = argparse.ArgumentParser(
            description='Enhanced AST replacement tool (v2) with symbol discovery and batch operations',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s oldFunc newFunc file.py             # Rename function in specific file
  %(prog)s oldVar newVar --line 42 file.py     # Rename variable at specific line
  %(prog)s --discover-symbol oldFunc newFunc    # Auto-discover and batch rename
  %(prog)s --from-find-json results.json old new # Use JSON from find_text
  %(prog)s old new --no-confirm file.py        # Skip confirmation prompts
  %(prog)s old new --yes file.py               # Auto-confirm all prompts
  %(prog)s old new --non-interactive --yes *.py # Fully automated batch rename

Non-Interactive Mode:
  • Use --non-interactive for CI/CD automation
  • Combine with --yes to auto-confirm prompts
  • Configure via REPLACE_TEXT_AST_ASSUME_YES environment variable
  • Set defaults in .pytoolsrc under [replace_text_ast] section

Environment Variables:
  REPLACE_TEXT_AST_ASSUME_YES       # Default: false - Assume yes to all prompts
  REPLACE_TEXT_AST_NONINTERACTIVE   # Default: false - Run in non-interactive mode
            """
        )
    
    # Core AST rename arguments
    if not HAS_ENHANCED_PARSER:
        parser.add_argument("old_name", help="The original variable or method name to be replaced")
        parser.add_argument("new_name", help="The new variable or method name") 
        parser.add_argument("--ast-rename", action="store_true", help="Enable AST-based scope-aware renaming")
        
        parser.add_argument('--file', type=str, required=True,
                           help='File to perform refactoring on')
        parser.add_argument('--line', '-l', type=int,
                           help='Line number where the variable is declared for scope analysis')
        parser.add_argument('--language', '--lang', choices=['python', 'java', 'auto'],
                           default='auto', help='Programming language (default: auto-detect)')
    else:
        # Enhanced parser provides target and file arguments automatically
        parser.add_argument("old_name", help="The original variable or method name to be replaced")
        parser.add_argument("new_name", help="The new variable or method name")
        parser.add_argument('--line', '-l', type=int,
                           help='Line number where the variable is declared for scope analysis')
    
    # V2 NEW FEATURES
    v2_group = parser.add_argument_group('V2 Enhanced Features')
    v2_group.add_argument('--from-find-json', metavar='JSON_INPUT',
                         help='Use JSON output from find_text as input for batch renaming (NEW IN V2)')
    v2_group.add_argument('--discover-symbol', action='store_true',
                         help='Auto-discover symbol locations using ripgrep before renaming (NEW IN V2)')
    v2_group.add_argument('--batch-rename', action='store_true',
                         help='Perform batch renaming across multiple files (NEW IN V2)')
    v2_group.add_argument('--confirm-each', action='store_true', default=True,
                         help='Confirm each file individually in batch mode (default: enabled)')
    v2_group.add_argument('--no-confirm', action='store_true',
                         help='Skip confirmation prompts in batch mode')
    v2_group.add_argument('--yes', '-y', action='store_true',
                         help='Assume yes to all prompts (for non-interactive mode)')
    v2_group.add_argument('--non-interactive', action='store_true',
                         help='Run in non-interactive mode')
    v2_group.add_argument('--enhanced-context', action='store_true', default=True,
                         help='Show enhanced scope context with block information (NEW IN V2)')
    
    # V7 COMPATIBILITY FEATURES (added for feature parity with replace_text_v7)
    v7_compat_group = parser.add_argument_group('V7 Compatibility Features')
    v7_compat_group.add_argument('--block-mode', choices=['preserve', 'within', 'extract'],
                                default='preserve', 
                                help='Block-aware replacement mode for AST operations (from V7)')
    v7_compat_group.add_argument('--comments-only', action='store_true',
                                help='Apply AST operations only within comments (language-aware)')
    v7_compat_group.add_argument('--strings-only', action='store_true',
                                help='Apply AST operations only within string literals (language-aware)')
    v7_compat_group.add_argument('--interpret-escapes', action='store_true',
                                help='Interpret escape sequences (\\n, \\t, etc.) in old_name and new_name')
    v7_compat_group.add_argument('--git-only', action='store_true',
                                help='Only process files tracked by Git')
    v7_compat_group.add_argument('--staged-only', action='store_true',
                                help='Only process files staged in Git')
    # Only add language argument if not already present
    if not hasattr(parser, '_option_string_actions') or '--language' not in parser._option_string_actions:
        v7_compat_group.add_argument('--lang', '--language', dest='language',
                                    choices=['python', 'java', 'javascript', 'typescript', 'cpp', 'c', 'go', 'rust', 'ruby', 'php', 'sql', 'lua'],
                                    help='Language-specific processing (from V7)')
    
    # Original options
    parser.add_argument('--use-rope', action='store_true',
                       help='Use rope library for Python (if available)')
    parser.add_argument('--backup', '-b', action='store_true',
                       help='Create backup before modifying')
    parser.add_argument('--no-backup', action='store_true',
                       help='Explicitly disable backup creation')
    # Only add --ast-context if enhanced parser doesn't provide it
    if not HAS_ENHANCED_PARSER:
        parser.add_argument('--ast-context', action='store_true',
                           help='Show AST context (class/method) in diff output')
    parser.add_argument('--check-compile', action='store_true', default=True,
                       help='Check syntax/compilation after successful edits (default: enabled)')
    parser.add_argument('--no-check-compile', action='store_true',
                       help='Disable compile checking')
    
    # Only add common arguments if enhanced parser doesn't provide them
    if not HAS_ENHANCED_PARSER:
        parser.add_argument('--dry-run', action='store_true',
                           help='Preview changes without applying')
        parser.add_argument('-v', '--verbose', action='store_true',
                           help='Enable verbose output')
        parser.add_argument('-q', '--quiet', action='store_true',
                           help='Minimal output')
        parser.add_argument('--json', action='store_true',
                           help='Output in JSON format')
    
    # Retry control options
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum number of retry attempts for locked files (default: 3)')
    parser.add_argument('--retry-delay', type=float, default=1.0,
                       help='Delay in seconds between retry attempts (default: 1.0)')
    parser.add_argument('--no-retry', action='store_true',
                       help='Disable retry logic for locked files')
    
    # Java-specific options
    parser.add_argument('--source-dir', action='append', dest='source_dirs',
                       help='Add source directory for Java symbol resolution (can be specified multiple times)')
    parser.add_argument('--jar', '--jar-path', action='append', dest='jar_paths',
                       help='Add JAR file for Java dependency resolution (can be specified multiple times)')
    
    args = parser.parse_args()
    
    # Load config if available
    config = None
    if HAS_CONFIG:
        config = load_config()
    
    # Handle compile check flags
    if args.no_check_compile:
        args.check_compile = False
    
    # Handle retry configuration
    if args.no_retry:
        args.max_retries = 1
        args.retry_delay = 0.0
    
    # Handle confirmation settings
    if args.no_confirm:
        args.confirm_each = False
    
    # Get non-interactive settings from config or environment
    if not hasattr(args, 'yes'):
        args.yes = DEFAULT_ASSUME_YES
    if not hasattr(args, 'non_interactive'):
        args.non_interactive = DEFAULT_NONINTERACTIVE
    
    # Config handling disabled for now - needs proper implementation
    # if HAS_CONFIG and config:
    #     # Override with config values if not specified on command line
    #     if not args.yes:
    #         args.yes = get_config_value('assume_yes', args.yes, 'replace_text_ast', config)
    #     if not args.non_interactive:
    #         args.non_interactive = get_config_value('non_interactive', args.non_interactive, 'replace_text_ast', config)
    
    # Allow retry configuration via environment variables
    if 'FILE_WRITE_MAX_RETRIES' in os.environ:
        args.max_retries = int(os.environ['FILE_WRITE_MAX_RETRIES'])
    if 'FILE_WRITE_RETRY_DELAY' in os.environ:
        args.retry_delay = float(os.environ['FILE_WRITE_RETRY_DELAY'])
    
    # Apply configuration defaults
    apply_config_to_args('replace_text_ast_v2', args, parser)
    
    # Handle both file and file_path attributes
    file_path = getattr(args, 'file', None) or getattr(args, 'file_path', None)
    
    # Validate arguments
    if not file_path:
        parser.error("Please specify a file with --file")
    
    if not args.old_name or not args.new_name:
        parser.error("Please specify both old_name and new_name")
    
    if not args.line and not args.from_find_json and not args.comments_only and not args.strings_only:
        parser.error("--line is required for AST-based renaming (unless using --from-find-json, --comments-only, or --strings-only)")
    
    # V2 FEATURE: Handle JSON pipeline input
    if args.from_find_json:
        if not HAS_JSON_PIPELINE:
            print("Error: JSON pipeline support not available. Install required modules.", file=sys.stderr)
            sys.exit(1)
        
        try:
            locations = process_json_pipeline_for_ast(args.from_find_json)
            
            print(f"📄 Loaded {len(locations)} symbol locations from find_text results")
            
            # Perform batch rename
            results = batch_symbol_rename(locations, args.old_name, args.new_name, args.confirm_each,
                                          non_interactive=getattr(args, 'non_interactive', False), 
                                          auto_yes=getattr(args, 'yes', False))
            
            # Show results summary
            print(f"\n📊 Batch Rename Results:")
            print(f"   Files processed: {results['successful_files']}/{results['total_files']}")
            print(f"   Total replacements: {results['total_replacements']}")
            if results['failed_files'] > 0:
                print(f"   Failed files: {results['failed_files']}")
                for error in results['errors']:
                    print(f"     ❌ {error}")
            
            sys.exit(0)
            
        except Exception as e:
            print(f"Error processing JSON pipeline input: {e}", file=sys.stderr)
            sys.exit(1)
    
    # V2 FEATURE: Symbol discovery mode
    if args.discover_symbol:
        if not HAS_RIPGREP_INTEGRATION:
            print("Warning: ripgrep integration not available. Using basic discovery.", file=sys.stderr)
        
        print(f"🔍 Discovering locations of symbol '{args.old_name}'...")
        
        # Discover symbol locations
        search_files = [file_path]  # Start with the specified file
        
        # Optionally expand to include related files in the same directory
        file_dir = Path(file_path).parent
        if file_path.endswith('.py'):
            search_files.extend(file_dir.glob('*.py'))
        elif file_path.endswith('.java'):
            search_files.extend(file_dir.glob('*.java'))
        
        search_files = [str(f) for f in set(search_files)]
        
        locations = discover_symbol_locations(args.old_name, search_files, 
                                            getattr(args, 'language', 'auto'))
        
        if not locations:
            print(f"No locations found for symbol '{args.old_name}'")
            sys.exit(0)
        
        print(f"Found {len(locations)} locations:")
        for i, loc in enumerate(locations, 1):
            print(f"  {i}. {loc['file_path']}:{loc['line_number']} - {loc['content'].strip()}")
            if loc.get('ast_context'):
                print(f"     Context: {loc['ast_context']}")
        
        # Ask if user wants to proceed with batch rename
        if args.batch_rename:
            try:
                response = input(f"\nProceed with batch rename '{args.old_name}' → '{args.new_name}'? [y/N] ")
                if response.lower() == 'y':
                    results = batch_symbol_rename(locations, args.old_name, args.new_name, args.confirm_each,
                                                non_interactive=getattr(args, 'non_interactive', False),
                                                auto_yes=getattr(args, 'yes', False))
                    
                    print(f"\n📊 Batch Rename Results:")
                    print(f"   Files processed: {results['successful_files']}/{results['total_files']}")
                    print(f"   Total replacements: {results['total_replacements']}")
                    
                    sys.exit(0)
                else:
                    print("Batch rename cancelled.")
                    sys.exit(0)
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled.")
                sys.exit(0)
    
    # Standard single-file processing
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Read original content
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # V7 COMPATIBILITY: Handle git-only and staged-only filters
        if args.git_only or args.staged_only:
            git_files = get_files_to_process_git(args.git_only, args.staged_only, args.language)
            if file_path not in git_files and str(Path(file_path).resolve()) not in git_files:
                print(f"Skipping {file_path} - not in git file list")
                sys.exit(0)
        
        # V7 COMPATIBILITY: Handle comments-only or strings-only modes
        if args.comments_only:
            print(f"🔍 Applying AST operations only within comments...")
            # Apply escape sequence interpretation if requested
            old_text = interpret_escape_sequences(args.old_name) if args.interpret_escapes else args.old_name
            new_text = interpret_escape_sequences(args.new_name) if args.interpret_escapes else args.new_name
            modified_content, replacements = replace_in_comments(original_content, old_text, new_text, args.language)
            if replacements > 0:
                print(f"Made {replacements} replacements in comments")
                
                if not args.dry_run:
                    # Write the modified content using atomic write
                    try:
                        should_backup = args.backup and not getattr(args, 'no_backup', False)
                        _atomic_write(Path(file_path), modified_content, bak=should_backup, 
                                      max_retries=args.max_retries, retry_delay=args.retry_delay)
                        print(f"✅ Successfully updated {file_path}")
                    except Exception as e:
                        print(f"❌ Error writing {file_path}: {e}")
                        sys.exit(1)
                else:
                    print(f"DRY RUN: Would update {file_path}")
            else:
                print(f"No occurrences of '{args.old_name}' found in comments")
            sys.exit(0)
        elif args.strings_only:
            print(f"🔍 Applying AST operations only within string literals...")
            # Apply escape sequence interpretation if requested
            old_text = interpret_escape_sequences(args.old_name) if args.interpret_escapes else args.old_name
            new_text = interpret_escape_sequences(args.new_name) if args.interpret_escapes else args.new_name
            modified_content, replacements = replace_in_strings(original_content, old_text, new_text, args.language)
            if replacements > 0:
                print(f"Made {replacements} replacements in strings")
                
                if not args.dry_run:
                    # Write the modified content using atomic write
                    try:
                        should_backup = args.backup and not getattr(args, 'no_backup', False)
                        _atomic_write(Path(file_path), modified_content, bak=should_backup, 
                                      max_retries=args.max_retries, retry_delay=args.retry_delay)
                        print(f"✅ Successfully updated {file_path}")
                    except Exception as e:
                        print(f"❌ Error writing {file_path}: {e}")
                        sys.exit(1)
                else:
                    print(f"DRY RUN: Would update {file_path}")
            else:
                print(f"No occurrences of '{args.old_name}' found in strings")
            sys.exit(0)
        
        # V2 FEATURE: Enhanced scope analysis
        if args.enhanced_context:
            print(f"🔍 Analyzing enhanced scope context for '{args.old_name}' at line {args.line}...")
            scope_context = analyze_symbol_scope_context(file_path, args.old_name, args.line)
        else:
            scope_context = None
        
        # Perform AST-based renaming
        print(f"🔄 Performing scope-aware rename: '{args.old_name}' → '{args.new_name}'...")
        
        if args.use_rope and getattr(args, 'language', 'auto') in ['python', 'auto']:
            if not ROPE_AVAILABLE:
                print("Warning: rope not installed, falling back to built-in AST", file=sys.stderr)
        
        # V2 ENHANCEMENT: Use enhanced scope-aware rename
        if scope_context and args.enhanced_context:
            modified_content, replacements = enhanced_scope_aware_rename(
                file_path, args.old_name, args.new_name, args.line,
                getattr(args, 'language', 'auto'), scope_context
            )
        else:
            modified_content, replacements = perform_ast_rename(
                file_path, args.old_name, args.new_name, args.line, 
                getattr(args, 'language', 'auto'), args.dry_run, args.use_rope,
                args.source_dirs, args.jar_paths
            )
        
        if replacements == 0:
            print(f"No occurrences of '{args.old_name}' found in the variable's scope")
            sys.exit(0)
        
        # Get enhanced context information
        context_str = ""
        if args.ast_context and HAS_AST_CONTEXT:
            context_finder = ASTContextFinder()
            context_parts = context_finder.get_context_for_line(file_path, args.line)
            if context_parts:
                context = context_finder._format_context_parts(context_parts)
                context_str = f" in [{context}]"
        
        print(f"✨ Found {replacements} reference(s) in the variable's scope{context_str}")
        
        # V2 ENHANCEMENT: Enhanced diff display
        if show_diff(original_content, modified_content, file_path, args.ast_context or args.enhanced_context):
            if not args.dry_run:
                # Safety checks
                if not modified_content or not modified_content.strip():
                    print(f"CRITICAL ERROR: Modified content is empty! Aborting write to prevent file corruption.", file=sys.stderr)
                    sys.exit(1)
                
                if len(modified_content) < len(original_content) * 0.3:
                    print(f"CRITICAL ERROR: Modified content is suspiciously small ({len(modified_content)} vs {len(original_content)} chars). Aborting write to prevent file corruption.", file=sys.stderr)
                    sys.exit(1)
                
                # Write modified content
                try:
                    should_backup = args.backup and not getattr(args, 'no_backup', False)
                    _atomic_write(Path(file_path), modified_content, bak=should_backup, 
                                  max_retries=args.max_retries, retry_delay=args.retry_delay)
                except Exception as e:
                    error_msg = f"\nError writing {file_path}: {e}"
                    
                    is_locked, lock_info = is_file_locked(file_path)
                    if is_locked:
                        error_msg += f"\nFile appears to be {lock_info}"
                        error_msg += "\nTry closing any programs that might have this file open."
                    
                    print(error_msg, file=sys.stderr)
                    sys.exit(1)
                
                LOG.info("✅ Successfully renamed %d occurrence(s)", replacements)
                
                # Check compilation if requested
                if args.check_compile:
                    try:
                        compile_success, compile_msg = check_compile_status(file_path, getattr(args, 'language', 'auto'))
                        compile_status = f"✓ {compile_msg}" if compile_success else f"✗ {compile_msg}"
                        print(compile_status)
                    except Exception as e:
                        print(f"✗ Compile check failed: {str(e)[:50]}")
            else:
                print("\n(Dry run - no changes applied)")
        else:
            print("No changes needed")
    
    except Exception as e:
        LOG.exception("Unhandled error")
        return 2

if __name__ == '__main__':
    main()