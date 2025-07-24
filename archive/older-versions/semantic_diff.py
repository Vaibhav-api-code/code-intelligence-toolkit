#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Semantic Diff V3 - Ultimate Semantic Code Analysis Tool

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-22
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import ast
import os
import sys
import json
import time
import re
import subprocess
import difflib
import hashlib
import pickle
import threading
import multiprocessing
from typing import Dict, List, Set, Tuple, Optional, Any, Union, NamedTuple, Iterator
from dataclasses import dataclass, field
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
from datetime import datetime
from enum import Enum, auto
import argparse
import tempfile
import shutil
import traceback
import warnings
from functools import lru_cache, partial
from itertools import chain, groupby
from contextlib import contextmanager
from abc import ABC, abstractmethod

# Optional numpy import

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

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    warnings.warn("numpy not installed - some features disabled")

# Optional imports for advanced features
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    warnings.warn("networkx not installed - graph visualization disabled")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    warnings.warn("pandas not installed - advanced analytics disabled")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    warnings.warn("scikit-learn not installed - ML features disabled")

try:
    import pygments
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False
    warnings.warn("pygments not installed - syntax highlighting disabled")

# Language-specific parsers
try:
    import javalang
    HAS_JAVA = True
except ImportError:
    HAS_JAVA = False
    warnings.warn("javalang not installed - Java support limited")

try:
    import esprima
    HAS_JS = True
except ImportError:
    HAS_JS = False
    warnings.warn("esprima not installed - JavaScript support limited")

try:
    from tree_sitter import Language, Parser as TSParser
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False
    warnings.warn("tree-sitter not installed - advanced parsing disabled")

class ChangeType(Enum):
    """Types of semantic changes"""
    ADDED = auto()
    REMOVED = auto()
    MODIFIED = auto()
    MOVED = auto()
    RENAMED = auto()
    REFACTORED = auto()
    SIGNATURE_CHANGED = auto()
    BEHAVIOR_CHANGED = auto()
    PERFORMANCE_IMPACT = auto()
    API_BREAKING = auto()
    SECURITY_IMPACT = auto()
    TEST_IMPACT = auto()

class RiskLevel(Enum):
    """Risk levels for changes"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    CSHARP = "csharp"
    RUBY = "ruby"
    PHP = "php"

@dataclass
class CodeEntity:
    """Represents a code entity (class, function, variable, etc.)"""
    name: str
    type: str  # class, function, method, variable, etc.
    language: Language
    file_path: str
    start_line: int
    end_line: int
    parent: Optional['CodeEntity'] = None
    children: List['CodeEntity'] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    ast_node: Optional[Any] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    annotations: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    
    def __hash__(self):
        return hash((self.name, self.type, self.file_path, self.start_line))
    
    def full_name(self) -> str:
        """Get fully qualified name"""
        if self.parent:
            return f"{self.parent.full_name()}.{self.name}"
        return self.name
    
    def calculate_complexity(self) -> float:
        """Calculate cyclomatic complexity"""
        if not self.ast_node:
            return 1.0
        
        # Simplified complexity calculation
        complexity = 1.0
        if hasattr(self.ast_node, 'body'):
            for node in ast.walk(self.ast_node):
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    complexity += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity += 1
        
        return complexity

@dataclass
class SemanticChange:
    """Represents a semantic change between two code versions"""
    change_type: ChangeType
    entity_before: Optional[CodeEntity]
    entity_after: Optional[CodeEntity]
    description: str
    risk_level: RiskLevel
    impact_score: float
    affected_files: Set[str] = field(default_factory=set)
    affected_entities: Set[str] = field(default_factory=set)
    related_changes: List['SemanticChange'] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    test_coverage_impact: Optional[float] = None
    performance_impact: Optional[float] = None
    security_implications: List[str] = field(default_factory=list)

@dataclass
class DiffReport:
    """Comprehensive diff report"""
    changes: List[SemanticChange]
    summary: Dict[str, Any]
    dependency_graph: Optional[Any] = None  # networkx graph
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    files_analyzed: int = 0
    total_entities: int = 0
    breaking_changes: List[SemanticChange] = field(default_factory=list)
    refactoring_patterns: List[Dict[str, Any]] = field(default_factory=list)

class UnifiedASTParser(ABC):
    """Abstract base class for language-specific parsers"""
    
    @abstractmethod
    def parse(self, code: str, file_path: str) -> List[CodeEntity]:
        """Parse code and return list of entities"""
        pass
    
    @abstractmethod
    def extract_dependencies(self, ast_node: Any) -> Set[str]:
        """Extract dependencies from AST node"""
        pass
    
    @abstractmethod
    def compare_behavior(self, node1: Any, node2: Any) -> float:
        """Compare behavioral similarity of two AST nodes"""
        pass

class PythonASTParser(UnifiedASTParser):
    """Python-specific AST parser"""
    
    def parse(self, code: str, file_path: str) -> List[CodeEntity]:
        """Parse Python code"""
        entities = []
        try:
            tree = ast.parse(code)
            entities = self._extract_entities(tree, file_path)
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
        return entities
    
    def _extract_entities(self, node: ast.AST, file_path: str, 
                         parent: Optional[CodeEntity] = None) -> List[CodeEntity]:
        """Extract entities from AST"""
        entities = []
        
        # Direct iteration over node body to avoid recursion issues
        for child in ast.iter_child_nodes(node):
            entity = None
            
            if isinstance(child, ast.ClassDef):
                entity = CodeEntity(
                    name=child.name,
                    type="class",
                    language=Language.PYTHON,
                    file_path=file_path,
                    start_line=child.lineno,
                    end_line=getattr(child, 'end_lineno', child.lineno),
                    parent=parent,
                    ast_node=child,
                    docstring=ast.get_docstring(child),
                    annotations=self._extract_annotations(child)
                )
                
            elif isinstance(child, ast.FunctionDef):
                entity = CodeEntity(
                    name=child.name,
                    type="function" if not parent else "method",
                    language=Language.PYTHON,
                    file_path=file_path,
                    start_line=child.lineno,
                    end_line=getattr(child, 'end_lineno', child.lineno),
                    parent=parent,
                    ast_node=child,
                    signature=self._extract_signature(child),
                    docstring=ast.get_docstring(child),
                    annotations=self._extract_annotations(child)
                )
            
            if entity:
                entities.append(entity)
                # Recursively extract nested entities
                if hasattr(child, 'body'):
                    nested = self._extract_entities(child, file_path, entity)
                    entities.extend(nested)
                    entity.children.extend(nested)
        
        return entities
    
    def _extract_signature(self, func_node: ast.FunctionDef) -> str:
        """Extract function signature"""
        args = []
        for arg in func_node.args.args:
            arg_str = arg.arg
            if hasattr(arg, 'annotation') and arg.annotation:
                try:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                except:
                    pass  # Skip if unparse fails
            args.append(arg_str)
        
        return f"{func_node.name}({', '.join(args)})"
    
    def _extract_annotations(self, node: Any) -> Dict[str, Any]:
        """Extract type annotations"""
        annotations = {}
        
        if isinstance(node, ast.FunctionDef):
            if hasattr(node, 'returns') and node.returns:
                try:
                    annotations['return'] = ast.unparse(node.returns)
                except:
                    pass
            
            if hasattr(node, 'args'):
                for arg in node.args.args:
                    if hasattr(arg, 'annotation') and arg.annotation:
                        try:
                            annotations[arg.arg] = ast.unparse(arg.annotation)
                        except:
                            pass
        
        return annotations
    
    def extract_dependencies(self, ast_node: Any) -> Set[str]:
        """Extract dependencies from Python AST"""
        dependencies = set()
        
        for node in ast.walk(ast_node):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    dependencies.add(f"{module}.{alias.name}")
            elif isinstance(node, ast.Name):
                dependencies.add(node.id)
        
        return dependencies
    
    def compare_behavior(self, node1: Any, node2: Any) -> float:
        """Compare behavioral similarity of two Python AST nodes"""
        if type(node1) != type(node2):
            return 0.0
        
        # Simple similarity based on AST structure
        similarity = 1.0
        
        # Compare node attributes
        for attr in node1._fields:
            val1 = getattr(node1, attr, None)
            val2 = getattr(node2, attr, None)
            
            if isinstance(val1, list) and isinstance(val2, list):
                if len(val1) != len(val2):
                    similarity *= 0.8
                else:
                    for v1, v2 in zip(val1, val2):
                        if isinstance(v1, ast.AST):
                            similarity *= self.compare_behavior(v1, v2)
            elif isinstance(val1, ast.AST) and isinstance(val2, ast.AST):
                similarity *= self.compare_behavior(val1, val2)
            elif val1 != val2:
                similarity *= 0.9
        
        return similarity

class JavaASTParser(UnifiedASTParser):
    """Java-specific AST parser"""
    
    def __init__(self):
        if not HAS_JAVA:
            raise ImportError("javalang required for Java parsing")
    
    def parse(self, code: str, file_path: str) -> List[CodeEntity]:
        """Parse Java code"""
        entities = []
        try:
            tree = javalang.parse.parse(code)
            entities = self._extract_entities(tree, file_path)
        except Exception as e:
            print(f"Error parsing Java file {file_path}: {e}")
        return entities
    
    def _extract_entities(self, tree: Any, file_path: str) -> List[CodeEntity]:
        """Extract entities from Java AST"""
        entities = []
        
        for path, node in tree.filter(javalang.tree.ClassDeclaration):
            entity = CodeEntity(
                name=node.name,
                type="class",
                language=Language.JAVA,
                file_path=file_path,
                start_line=node.position.line if node.position else 0,
                end_line=node.position.line if node.position else 0,
                ast_node=node
            )
            entities.append(entity)
            
            # Extract methods
            for method in node.methods:
                method_entity = CodeEntity(
                    name=method.name,
                    type="method",
                    language=Language.JAVA,
                    file_path=file_path,
                    start_line=method.position.line if method.position else 0,
                    end_line=method.position.line if method.position else 0,
                    parent=entity,
                    ast_node=method,
                    signature=self._extract_java_signature(method)
                )
                entities.append(method_entity)
                entity.children.append(method_entity)
        
        return entities
    
    def _extract_java_signature(self, method: Any) -> str:
        """Extract Java method signature"""
        params = []
        if hasattr(method, 'parameters'):
            for param in method.parameters:
                param_type = param.type.name if hasattr(param.type, 'name') else str(param.type)
                params.append(f"{param_type} {param.name}")
        
        return f"{method.name}({', '.join(params)})"
    
    def extract_dependencies(self, ast_node: Any) -> Set[str]:
        """Extract dependencies from Java AST"""
        dependencies = set()
        # Simplified - would need full implementation
        return dependencies
    
    def compare_behavior(self, node1: Any, node2: Any) -> float:
        """Compare behavioral similarity of two Java AST nodes"""
        # Simplified implementation
        return 0.5 if type(node1) == type(node2) else 0.0

class MultiLanguageParser:
    """Unified parser supporting multiple languages"""
    
    def __init__(self):
        self.parsers = {
            Language.PYTHON: PythonASTParser(),
            Language.JAVA: JavaASTParser() if HAS_JAVA else None,
            # Add more parsers as needed
        }
    
    def parse_file(self, file_path: str) -> List[CodeEntity]:
        """Parse file based on extension"""
        language = self._detect_language(file_path)
        if not language or language not in self.parsers:
            return []
        
        parser = self.parsers[language]
        if not parser:
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            return parser.parse(code, file_path)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []
    
    def _detect_language(self, file_path: str) -> Optional[Language]:
        """Detect language from file extension"""
        ext_map = {
            '.py': Language.PYTHON,
            '.java': Language.JAVA,
            '.js': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.go': Language.GO,
            '.rs': Language.RUST,
            '.cpp': Language.CPP,
            '.cs': Language.CSHARP,
            '.rb': Language.RUBY,
            '.php': Language.PHP,
        }
        
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext)

class PatternRecognizer:
    """ML-based pattern recognition for common refactorings"""
    
    def __init__(self):
        self.patterns = {
            'extract_method': self._detect_extract_method,
            'rename': self._detect_rename,
            'move_method': self._detect_move_method,
            'extract_class': self._detect_extract_class,
            'inline': self._detect_inline,
            'pull_up': self._detect_pull_up,
            'push_down': self._detect_push_down,
        }
        
        # Initialize ML components if available
        if HAS_SKLEARN:
            self.vectorizer = TfidfVectorizer(max_features=100)
            self.similarity_threshold = 0.8
    
    def detect_patterns(self, changes: List[SemanticChange]) -> List[Dict[str, Any]]:
        """Detect refactoring patterns in changes"""
        patterns = []
        
        for pattern_name, detector in self.patterns.items():
            detected = detector(changes)
            if detected:
                patterns.extend(detected)
        
        return patterns
    
    def _detect_extract_method(self, changes: List[SemanticChange]) -> List[Dict[str, Any]]:
        """Detect extract method refactoring"""
        patterns = []
        
        # Look for new methods with code similar to modified methods
        new_methods = [c for c in changes if c.change_type == ChangeType.ADDED 
                      and c.entity_after and c.entity_after.type in ('method', 'function')]
        modified_methods = [c for c in changes if c.change_type == ChangeType.MODIFIED 
                           and c.entity_before and c.entity_before.type in ('method', 'function')]
        
        for new_method in new_methods:
            for modified_method in modified_methods:
                similarity = self._calculate_code_similarity(
                    new_method.entity_after,
                    modified_method.entity_before
                )
                
                if similarity > 0.7:
                    patterns.append({
                        'type': 'extract_method',
                        'confidence': similarity,
                        'source': modified_method.entity_before.full_name(),
                        'extracted': new_method.entity_after.full_name(),
                        'description': f"Extracted method {new_method.entity_after.name} from {modified_method.entity_before.name}"
                    })
        
        return patterns
    
    def _detect_rename(self, changes: List[SemanticChange]) -> List[Dict[str, Any]]:
        """Detect rename refactoring"""
        patterns = []
        
        # Look for removed and added entities with similar structure
        removed = [c for c in changes if c.change_type == ChangeType.REMOVED and c.entity_before]
        added = [c for c in changes if c.change_type == ChangeType.ADDED and c.entity_after]
        
        for rem in removed:
            for add in added:
                if (rem.entity_before.type == add.entity_after.type and
                    self._similar_structure(rem.entity_before, add.entity_after)):
                    
                    patterns.append({
                        'type': 'rename',
                        'confidence': 0.9,
                        'old_name': rem.entity_before.full_name(),
                        'new_name': add.entity_after.full_name(),
                        'description': f"Renamed {rem.entity_before.name} to {add.entity_after.name}"
                    })
        
        return patterns
    
    def _detect_move_method(self, changes: List[SemanticChange]) -> List[Dict[str, Any]]:
        """Detect move method refactoring"""
        patterns = []
        # Implementation would detect methods moved between classes
        return patterns
    
    def _detect_extract_class(self, changes: List[SemanticChange]) -> List[Dict[str, Any]]:
        """Detect extract class refactoring"""
        patterns = []
        # Implementation would detect new classes with methods from existing classes
        return patterns
    
    def _detect_inline(self, changes: List[SemanticChange]) -> List[Dict[str, Any]]:
        """Detect inline refactoring"""
        patterns = []
        # Implementation would detect inlined methods/variables
        return patterns
    
    def _detect_pull_up(self, changes: List[SemanticChange]) -> List[Dict[str, Any]]:
        """Detect pull up refactoring"""
        patterns = []
        # Implementation would detect methods moved to parent class
        return patterns
    
    def _detect_push_down(self, changes: List[SemanticChange]) -> List[Dict[str, Any]]:
        """Detect push down refactoring"""
        patterns = []
        # Implementation would detect methods moved to child classes
        return patterns
    
    def _calculate_code_similarity(self, entity1: CodeEntity, entity2: CodeEntity) -> float:
        """Calculate similarity between two code entities"""
        if not HAS_SKLEARN:
            # Simple text similarity
            return self._simple_similarity(str(entity1.ast_node), str(entity2.ast_node))
        
        # Use TF-IDF for better similarity
        texts = [str(entity1.ast_node), str(entity2.ast_node)]
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        return float(similarity)
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity without ML"""
        tokens1 = set(text1.split())
        tokens2 = set(text2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union)
    
    def _similar_structure(self, entity1: CodeEntity, entity2: CodeEntity) -> bool:
        """Check if two entities have similar structure"""
        # Compare signatures, children count, etc.
        if entity1.signature and entity2.signature:
            sig1_params = entity1.signature.count(',')
            sig2_params = entity2.signature.count(',')
            if abs(sig1_params - sig2_params) > 1:
                return False
        
        if abs(len(entity1.children) - len(entity2.children)) > 2:
            return False
        
        return True

class ImpactAnalyzer:
    """Analyze cross-file impact of changes"""
    
    def __init__(self, parser: MultiLanguageParser):
        self.parser = parser
        self.dependency_graph = nx.DiGraph() if HAS_NETWORKX else None
        self.entity_map: Dict[str, CodeEntity] = {}
        self.file_dependencies: Dict[str, Set[str]] = defaultdict(set)
    
    def analyze_impact(self, changes: List[SemanticChange], 
                      project_root: str) -> Dict[str, Any]:
        """Analyze impact of changes across the project"""
        # Build dependency graph
        self._build_dependency_graph(project_root)
        
        # Analyze direct impact
        direct_impact = self._analyze_direct_impact(changes)
        
        # Analyze transitive impact
        transitive_impact = self._analyze_transitive_impact(changes)
        
        # Calculate risk scores
        risk_analysis = self._calculate_risk_scores(changes, transitive_impact)
        
        # Identify critical paths
        critical_paths = self._find_critical_paths(changes)
        
        return {
            'direct_impact': direct_impact,
            'transitive_impact': transitive_impact,
            'risk_analysis': risk_analysis,
            'critical_paths': critical_paths,
            'affected_files': len(set(chain.from_iterable(
                change.affected_files for change in changes
            ))),
            'total_impact_score': sum(change.impact_score for change in changes)
        }
    
    def _build_dependency_graph(self, project_root: str):
        """Build project-wide dependency graph"""
        if not self.dependency_graph:
            return
        
        # Parse all files in project
        for root, _, files in os.walk(project_root):
            for file in files:
                file_path = os.path.join(root, file)
                entities = self.parser.parse_file(file_path)
                
                for entity in entities:
                    entity_id = entity.full_name()
                    self.entity_map[entity_id] = entity
                    self.dependency_graph.add_node(entity_id, entity=entity)
                    
                    # Add dependencies
                    for dep in entity.dependencies:
                        if dep in self.entity_map:
                            self.dependency_graph.add_edge(entity_id, dep)
    
    def _analyze_direct_impact(self, changes: List[SemanticChange]) -> Dict[str, Any]:
        """Analyze direct impact of changes"""
        impact = {
            'affected_entities': set(),
            'affected_files': set(),
            'by_type': defaultdict(int)
        }
        
        for change in changes:
            if change.entity_before:
                impact['affected_entities'].add(change.entity_before.full_name())
                impact['affected_files'].add(change.entity_before.file_path)
            
            if change.entity_after:
                impact['affected_entities'].add(change.entity_after.full_name())
                impact['affected_files'].add(change.entity_after.file_path)
            
            impact['by_type'][change.change_type.name] += 1
        
        return dict(impact)
    
    def _analyze_transitive_impact(self, changes: List[SemanticChange]) -> Dict[str, Set[str]]:
        """Analyze transitive impact through dependency graph"""
        if not self.dependency_graph:
            return {}
        
        transitive_impact = defaultdict(set)
        
        for change in changes:
            entity_name = None
            if change.entity_before:
                entity_name = change.entity_before.full_name()
            elif change.entity_after:
                entity_name = change.entity_after.full_name()
            
            if entity_name and entity_name in self.dependency_graph:
                # Find all nodes that depend on this entity
                dependents = nx.ancestors(self.dependency_graph, entity_name)
                transitive_impact[entity_name] = dependents
        
        return dict(transitive_impact)
    
    def _calculate_risk_scores(self, changes: List[SemanticChange], 
                              transitive_impact: Dict[str, Set[str]]) -> Dict[str, Any]:
        """Calculate risk scores for changes"""
        risk_scores = {
            'total_risk': 0.0,
            'high_risk_changes': [],
            'risk_by_file': defaultdict(float)
        }
        
        for change in changes:
            # Base risk from change type
            base_risk = self._get_base_risk(change.change_type)
            
            # Amplify by impact
            entity_name = (change.entity_before.full_name() if change.entity_before 
                          else change.entity_after.full_name() if change.entity_after 
                          else "")
            
            impact_multiplier = 1.0
            if entity_name in transitive_impact:
                impact_multiplier = 1.0 + (len(transitive_impact[entity_name]) * 0.1)
            
            total_risk = base_risk * impact_multiplier * change.impact_score
            risk_scores['total_risk'] += total_risk
            
            if total_risk > 5.0:
                risk_scores['high_risk_changes'].append({
                    'change': change.description,
                    'risk_score': total_risk,
                    'reason': self._explain_risk(change, transitive_impact.get(entity_name, set()))
                })
            
            # Risk by file
            for file in change.affected_files:
                risk_scores['risk_by_file'][file] += total_risk
        
        return dict(risk_scores)
    
    def _get_base_risk(self, change_type: ChangeType) -> float:
        """Get base risk score for change type"""
        risk_map = {
            ChangeType.ADDED: 1.0,
            ChangeType.REMOVED: 2.0,
            ChangeType.MODIFIED: 1.5,
            ChangeType.MOVED: 1.5,
            ChangeType.RENAMED: 1.0,
            ChangeType.REFACTORED: 2.0,
            ChangeType.SIGNATURE_CHANGED: 3.0,
            ChangeType.BEHAVIOR_CHANGED: 4.0,
            ChangeType.PERFORMANCE_IMPACT: 3.0,
            ChangeType.API_BREAKING: 5.0,
            ChangeType.SECURITY_IMPACT: 5.0,
            ChangeType.TEST_IMPACT: 2.0,
        }
        return risk_map.get(change_type, 1.0)
    
    def _explain_risk(self, change: SemanticChange, dependents: Set[str]) -> str:
        """Explain why a change is risky"""
        reasons = []
        
        if change.change_type == ChangeType.API_BREAKING:
            reasons.append("Breaking API change")
        
        if change.change_type == ChangeType.SECURITY_IMPACT:
            reasons.append("Security implications")
        
        if len(dependents) > 10:
            reasons.append(f"Affects {len(dependents)} dependent components")
        
        if change.risk_level == RiskLevel.CRITICAL:
            reasons.append("Critical risk level")
        
        return "; ".join(reasons) if reasons else "General risk"
    
    def _find_critical_paths(self, changes: List[SemanticChange]) -> List[Dict[str, Any]]:
        """Find critical paths affected by changes"""
        if not self.dependency_graph:
            return []
        
        critical_paths = []
        
        # Find paths between changed entities
        changed_entities = set()
        for change in changes:
            if change.entity_before:
                changed_entities.add(change.entity_before.full_name())
            if change.entity_after:
                changed_entities.add(change.entity_after.full_name())
        
        # Find shortest paths between pairs of changed entities
        for entity1 in changed_entities:
            for entity2 in changed_entities:
                if entity1 != entity2 and entity1 in self.dependency_graph and entity2 in self.dependency_graph:
                    try:
                        path = nx.shortest_path(self.dependency_graph, entity1, entity2)
                        if len(path) > 1:
                            critical_paths.append({
                                'from': entity1,
                                'to': entity2,
                                'path': path,
                                'length': len(path)
                            })
                    except nx.NetworkXNoPath:
                        pass
        
        return critical_paths

class TestCoverageAnalyzer:
    """Analyze test coverage impact of changes"""
    
    def __init__(self):
        self.test_patterns = [
            re.compile(r'test_\w+'),
            re.compile(r'\w+_test'),
            re.compile(r'\w+Test'),
            re.compile(r'Test\w+'),
        ]
    
    def analyze_test_impact(self, changes: List[SemanticChange], 
                           project_root: str) -> Dict[str, Any]:
        """Analyze impact on test coverage"""
        # Find test files
        test_files = self._find_test_files(project_root)
        
        # Map tests to source files
        test_mapping = self._build_test_mapping(test_files)
        
        # Analyze which tests are affected
        affected_tests = self._find_affected_tests(changes, test_mapping)
        
        # Calculate coverage impact
        coverage_impact = self._calculate_coverage_impact(changes, affected_tests)
        
        return {
            'affected_tests': affected_tests,
            'coverage_impact': coverage_impact,
            'test_recommendations': self._generate_test_recommendations(changes, affected_tests),
            'missing_tests': self._find_missing_tests(changes, test_mapping)
        }
    
    def _find_test_files(self, project_root: str) -> List[str]:
        """Find all test files in project"""
        test_files = []
        
        for root, dirs, files in os.walk(project_root):
            # Skip common non-test directories
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv'}]
            
            for file in files:
                file_path = os.path.join(root, file)
                if self._is_test_file(file_path):
                    test_files.append(file_path)
        
        return test_files
    
    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file"""
        file_name = os.path.basename(file_path)
        
        # Check patterns
        for pattern in self.test_patterns:
            if pattern.search(file_name):
                return True
        
        # Check directory structure
        path_parts = Path(file_path).parts
        return 'test' in path_parts or 'tests' in path_parts
    
    def _build_test_mapping(self, test_files: List[str]) -> Dict[str, List[str]]:
        """Map source files to their tests"""
        mapping = defaultdict(list)
        
        for test_file in test_files:
            # Extract what this test might be testing
            test_name = Path(test_file).stem
            
            # Remove test prefixes/suffixes
            source_name = test_name
            for prefix in ['test_', 'Test']:
                if source_name.startswith(prefix):
                    source_name = source_name[len(prefix):]
            for suffix in ['_test', 'Test']:
                if source_name.endswith(suffix):
                    source_name = source_name[:-len(suffix)]
            
            mapping[source_name].append(test_file)
        
        return dict(mapping)
    
    def _find_affected_tests(self, changes: List[SemanticChange], 
                            test_mapping: Dict[str, List[str]]) -> List[str]:
        """Find tests affected by changes"""
        affected_tests = set()
        
        for change in changes:
            # Get source file name
            if change.entity_before:
                source_file = Path(change.entity_before.file_path).stem
            elif change.entity_after:
                source_file = Path(change.entity_after.file_path).stem
            else:
                continue
            
            # Find related tests
            if source_file in test_mapping:
                affected_tests.update(test_mapping[source_file])
        
        return list(affected_tests)
    
    def _calculate_coverage_impact(self, changes: List[SemanticChange], 
                                  affected_tests: List[str]) -> Dict[str, Any]:
        """Calculate coverage impact"""
        # This would integrate with actual coverage tools
        # For now, return estimates
        
        return {
            'estimated_coverage_change': -len(changes) * 0.5,  # Pessimistic estimate
            'uncovered_changes': len([c for c in changes if c.change_type == ChangeType.ADDED]),
            'test_execution_time_impact': len(affected_tests) * 2.0  # seconds
        }
    
    def _generate_test_recommendations(self, changes: List[SemanticChange], 
                                     affected_tests: List[str]) -> List[str]:
        """Generate test recommendations"""
        recommendations = []
        
        # Check for new functionality without tests
        new_functions = [c for c in changes if c.change_type == ChangeType.ADDED 
                        and c.entity_after and c.entity_after.type in ('function', 'method')]
        
        if new_functions:
            recommendations.append(f"Add tests for {len(new_functions)} new functions/methods")
        
        # Check for signature changes
        sig_changes = [c for c in changes if c.change_type == ChangeType.SIGNATURE_CHANGED]
        if sig_changes:
            recommendations.append(f"Update {len(sig_changes)} tests for signature changes")
        
        # Check for behavior changes
        behavior_changes = [c for c in changes if c.change_type == ChangeType.BEHAVIOR_CHANGED]
        if behavior_changes:
            recommendations.append(f"Review {len(behavior_changes)} tests for behavior changes")
        
        return recommendations
    
    def _find_missing_tests(self, changes: List[SemanticChange], 
                           test_mapping: Dict[str, List[str]]) -> List[str]:
        """Find entities without tests"""
        missing = []
        
        for change in changes:
            entity = change.entity_after or change.entity_before
            if not entity:
                continue
            
            source_file = Path(entity.file_path).stem
            if source_file not in test_mapping or not test_mapping[source_file]:
                missing.append(entity.full_name())
        
        return missing

class GitIntegration:
    """Git integration for analyzing commits and branches"""
    
    def __init__(self):
        self.git_available = self._check_git()
    
    def _check_git(self) -> bool:
        """Check if git is available"""
        try:
            # NOTE: Using direct git for version check only - safe read-only operation
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_commit_diff(self, commit1: str, commit2: str = 'HEAD') -> Dict[str, str]:
        """Get diff between commits"""
        if not self.git_available:
            return {}
        
        try:
            # Get list of changed files
            result = subprocess.run(
                ['git', 'diff', '--name-only', commit1, commit2],
                capture_output=True, text=True, check=True
            )
            changed_files = result.stdout.strip().split('\n')
            
            # Get diff for each file
            diffs = {}
            for file in changed_files:
                if file:
                    file_diff = subprocess.run(
                        ['git', 'diff', commit1, commit2, '--', file],
                        capture_output=True, text=True
                    )
                    diffs[file] = file_diff.stdout
            
            return diffs
        except subprocess.CalledProcessError:
            return {}
    
    def get_file_at_commit(self, file_path: str, commit: str) -> Optional[str]:
        """Get file content at specific commit"""
        if not self.git_available:
            return None
        
        try:
            result = subprocess.run(
                ['git', 'show', f'{commit}:{file_path}'],
                capture_output=True, text=True, check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return None
    
    def analyze_commit_range(self, start_commit: str, end_commit: str = 'HEAD') -> List[Dict[str, Any]]:
        """Analyze all commits in range"""
        if not self.git_available:
            return []
        
        try:
            # Get commit list
            result = subprocess.run(
                ['git', 'log', '--pretty=format:%H|%s|%an|%ae|%at', f'{start_commit}..{end_commit}'],
                capture_output=True, text=True, check=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1],
                        'author': parts[2],
                        'email': parts[3],
                        'timestamp': int(parts[4])
                    })
            
            return commits
        except subprocess.CalledProcessError:
            return []

class ReportGenerator:
    """Generate visual reports in HTML and Markdown"""
    
    def __init__(self):
        self.css_style = """
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .summary { background: #f0f0f0; padding: 15px; border-radius: 5px; }
            .change { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .added { border-left: 5px solid #28a745; }
            .removed { border-left: 5px solid #dc3545; }
            .modified { border-left: 5px solid #ffc107; }
            .high-risk { background: #ffe6e6; }
            .medium-risk { background: #fff4e6; }
            .low-risk { background: #e6ffe6; }
            .code-diff { background: #f8f8f8; padding: 10px; font-family: monospace; }
            .metrics { display: flex; justify-content: space-around; }
            .metric-box { text-align: center; padding: 20px; background: #f9f9f9; border-radius: 5px; }
            .metric-value { font-size: 2em; font-weight: bold; }
            .impact-graph { margin: 20px 0; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background: #f2f2f2; }
            .tree { font-family: monospace; }
            .tree-node { margin-left: 20px; }
        </style>
        """
    
    def generate_html_report(self, report: DiffReport, output_path: str):
        """Generate interactive HTML report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Semantic Diff Report - {report.timestamp.strftime('%Y-%m-%d %H:%M')}</title>
            {self.css_style}
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <h1>Semantic Diff Analysis Report</h1>
            
            {self._generate_summary_html(report)}
            {self._generate_metrics_html(report)}
            {self._generate_changes_html(report)}
            {self._generate_impact_html(report)}
            {self._generate_recommendations_html(report)}
            
            <footer>
                <p>Generated by Semantic Diff V3 at {report.timestamp}</p>
            </footer>
        </body>
        </html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def generate_markdown_report(self, report: DiffReport, output_path: str):
        """Generate Markdown report"""
        md_content = f"""# Semantic Diff Analysis Report

Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M')}

## Summary

- **Files Analyzed**: {report.files_analyzed}
- **Total Entities**: {report.total_entities}
- **Total Changes**: {len(report.changes)}
- **Breaking Changes**: {len(report.breaking_changes)}
- **Risk Level**: {self._calculate_overall_risk(report)}

## Metrics

{self._generate_metrics_markdown(report)}

## Changes by Type

{self._generate_changes_markdown(report)}

## Impact Analysis

{self._generate_impact_markdown(report)}

## Recommendations

{self._generate_recommendations_markdown(report)}

## Refactoring Patterns Detected

{self._generate_patterns_markdown(report)}

---
*Generated by Semantic Diff V3*
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def _generate_summary_html(self, report: DiffReport) -> str:
        """Generate summary section HTML"""
        risk_level = self._calculate_overall_risk(report)
        risk_class = risk_level.lower().replace(' ', '-')
        
        return f"""
        <div class="summary {risk_class}">
            <h2>Summary</h2>
            <div class="metrics">
                <div class="metric-box">
                    <div class="metric-value">{report.files_analyzed}</div>
                    <div>Files Analyzed</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{len(report.changes)}</div>
                    <div>Total Changes</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{len(report.breaking_changes)}</div>
                    <div>Breaking Changes</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{risk_level}</div>
                    <div>Overall Risk</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_metrics_html(self, report: DiffReport) -> str:
        """Generate metrics visualization HTML"""
        # Would include charts using Chart.js
        return """
        <div class="metrics-charts">
            <h2>Metrics</h2>
            <canvas id="changeTypeChart"></canvas>
            <canvas id="riskDistributionChart"></canvas>
        </div>
        """
    
    def _generate_changes_html(self, report: DiffReport) -> str:
        """Generate changes section HTML"""
        html = "<h2>Changes</h2>"
        
        for change in report.changes[:50]:  # Limit to first 50
            risk_class = change.risk_level.name.lower()
            change_class = change.change_type.name.lower()
            
            html += f"""
            <div class="change {change_class} {risk_class}-risk">
                <h3>{change.description}</h3>
                <p><strong>Type:</strong> {change.change_type.name}</p>
                <p><strong>Risk:</strong> {change.risk_level.name}</p>
                <p><strong>Impact Score:</strong> {change.impact_score:.2f}</p>
                """
            
            if change.suggestions:
                html += "<p><strong>Suggestions:</strong></p><ul>"
                for suggestion in change.suggestions:
                    html += f"<li>{suggestion}</li>"
                html += "</ul>"
            
            html += "</div>"
        
        return html
    
    def _generate_impact_html(self, report: DiffReport) -> str:
        """Generate impact analysis HTML"""
        if not report.impact_analysis:
            return ""
        
        html = "<h2>Impact Analysis</h2>"
        
        # Add dependency graph visualization if available
        if report.dependency_graph and HAS_NETWORKX:
            html += "<div class='impact-graph'>"
            # Would generate graph visualization
            html += "</div>"
        
        return html
    
    def _generate_recommendations_html(self, report: DiffReport) -> str:
        """Generate recommendations HTML"""
        if not report.recommendations:
            return ""
        
        html = "<h2>Recommendations</h2><ol>"
        for rec in report.recommendations:
            html += f"<li>{rec}</li>"
        html += "</ol>"
        
        return html
    
    def _generate_metrics_markdown(self, report: DiffReport) -> str:
        """Generate metrics section for Markdown"""
        lines = []
        
        # Change type distribution
        change_types = defaultdict(int)
        for change in report.changes:
            change_types[change.change_type.name] += 1
        
        lines.append("### Changes by Type")
        lines.append("")
        lines.append("| Type | Count |")
        lines.append("|------|-------|")
        for change_type, count in sorted(change_types.items()):
            lines.append(f"| {change_type} | {count} |")
        
        return "\n".join(lines)
    
    def _generate_changes_markdown(self, report: DiffReport) -> str:
        """Generate changes section for Markdown"""
        lines = []
        
        # Group by risk level
        by_risk = defaultdict(list)
        for change in report.changes:
            by_risk[change.risk_level].append(change)
        
        for risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]:
            if risk_level in by_risk:
                lines.append(f"### {risk_level.name} Risk Changes")
                lines.append("")
                
                for change in by_risk[risk_level][:10]:  # Limit to 10 per category
                    lines.append(f"- **{change.description}**")
                    lines.append(f"  - Type: {change.change_type.name}")
                    lines.append(f"  - Impact Score: {change.impact_score:.2f}")
                    if change.suggestions:
                        lines.append(f"  - Suggestions: {'; '.join(change.suggestions)}")
                    lines.append("")
        
        return "\n".join(lines)
    
    def _generate_impact_markdown(self, report: DiffReport) -> str:
        """Generate impact analysis for Markdown"""
        if not report.impact_analysis:
            return "No impact analysis available."
        
        lines = []
        impact = report.impact_analysis
        
        if 'direct_impact' in impact:
            lines.append(f"- **Directly Affected Files**: {len(impact['direct_impact'].get('affected_files', []))}")
            lines.append(f"- **Directly Affected Entities**: {len(impact['direct_impact'].get('affected_entities', []))}")
        
        if 'risk_analysis' in impact:
            lines.append(f"- **Total Risk Score**: {impact['risk_analysis'].get('total_risk', 0):.2f}")
        
        return "\n".join(lines)
    
    def _generate_recommendations_markdown(self, report: DiffReport) -> str:
        """Generate recommendations for Markdown"""
        if not report.recommendations:
            return "No recommendations."
        
        lines = []
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")
        
        return "\n".join(lines)
    
    def _generate_patterns_markdown(self, report: DiffReport) -> str:
        """Generate refactoring patterns for Markdown"""
        if not report.refactoring_patterns:
            return "No refactoring patterns detected."
        
        lines = []
        for pattern in report.refactoring_patterns:
            lines.append(f"- **{pattern['type']}**: {pattern['description']}")
            lines.append(f"  - Confidence: {pattern['confidence']:.2%}")
        
        return "\n".join(lines)
    
    def _calculate_overall_risk(self, report: DiffReport) -> str:
        """Calculate overall risk level"""
        if report.breaking_changes:
            return "CRITICAL"
        
        high_risk = sum(1 for c in report.changes if c.risk_level == RiskLevel.HIGH)
        if high_risk > 5:
            return "HIGH"
        elif high_risk > 0:
            return "MEDIUM"
        
        return "LOW"

class SemanticDiffAnalyzer:
    """Main semantic diff analyzer"""
    
    def __init__(self):
        self.parser = MultiLanguageParser()
        self.pattern_recognizer = PatternRecognizer()
        self.impact_analyzer = ImpactAnalyzer(self.parser)
        self.test_analyzer = TestCoverageAnalyzer()
        self.git_integration = GitIntegration()
        self.report_generator = ReportGenerator()
    
    def analyze_files(self, file1: str, file2: str) -> DiffReport:
        """Analyze semantic differences between two files"""
        # Parse both files
        entities1 = self.parser.parse_file(file1)
        entities2 = self.parser.parse_file(file2)
        
        # Build entity maps
        entity_map1 = {e.full_name(): e for e in entities1}
        entity_map2 = {e.full_name(): e for e in entities2}
        
        # Find changes
        changes = self._find_changes(entity_map1, entity_map2)
        
        # Detect patterns
        patterns = self.pattern_recognizer.detect_patterns(changes)
        
        # Analyze impact
        impact = self.impact_analyzer.analyze_impact(changes, os.path.dirname(file1))
        
        # Create report
        report = DiffReport(
            changes=changes,
            summary=self._generate_summary(changes),
            impact_analysis=impact,
            refactoring_patterns=patterns,
            files_analyzed=2,
            total_entities=len(entities1) + len(entities2)
        )
        
        # Add recommendations
        report.recommendations = self._generate_recommendations(report)
        
        # Identify breaking changes
        report.breaking_changes = [c for c in changes if c.change_type == ChangeType.API_BREAKING]
        
        return report
    
    def analyze_directory(self, dir1: str, dir2: str, 
                         extensions: Optional[List[str]] = None) -> DiffReport:
        """Analyze semantic differences between two directories"""
        all_changes = []
        files_analyzed = 0
        total_entities = 0
        
        # Find matching files
        files1 = self._find_files(dir1, extensions)
        files2 = self._find_files(dir2, extensions)
        
        # Process files in parallel
        with ProcessPoolExecutor() as executor:
            futures = []
            
            for rel_path in files1.keys() & files2.keys():
                file1 = files1[rel_path]
                file2 = files2[rel_path]
                
                future = executor.submit(self._analyze_file_pair, file1, file2)
                futures.append((rel_path, future))
            
            for rel_path, future in futures:
                try:
                    changes, entity_count = future.result()
                    all_changes.extend(changes)
                    total_entities += entity_count
                    files_analyzed += 2
                except Exception as e:
                    print(f"Error analyzing {rel_path}: {e}")
        
        # Handle added/removed files
        for rel_path in files1.keys() - files2.keys():
            changes = self._handle_removed_file(files1[rel_path])
            all_changes.extend(changes)
            files_analyzed += 1
        
        for rel_path in files2.keys() - files1.keys():
            changes = self._handle_added_file(files2[rel_path])
            all_changes.extend(changes)
            files_analyzed += 1
        
        # Detect patterns across all changes
        patterns = self.pattern_recognizer.detect_patterns(all_changes)
        
        # Analyze impact
        impact = self.impact_analyzer.analyze_impact(all_changes, dir1)
        
        # Create report
        report = DiffReport(
            changes=all_changes,
            summary=self._generate_summary(all_changes),
            impact_analysis=impact,
            refactoring_patterns=patterns,
            files_analyzed=files_analyzed,
            total_entities=total_entities
        )
        
        # Add recommendations
        report.recommendations = self._generate_recommendations(report)
        
        # Identify breaking changes
        report.breaking_changes = [c for c in all_changes if c.change_type == ChangeType.API_BREAKING]
        
        return report
    
    def analyze_git_commits(self, commit1: str, commit2: str = 'HEAD') -> DiffReport:
        """Analyze semantic differences between git commits"""
        if not self.git_integration.git_available:
            raise RuntimeError("Git not available")
        
        # Get diffs
        diffs = self.git_integration.get_commit_diff(commit1, commit2)
        
        all_changes = []
        files_analyzed = 0
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for file_path, diff in diffs.items():
                # Get file content at both commits
                content1 = self.git_integration.get_file_at_commit(file_path, commit1)
                content2 = self.git_integration.get_file_at_commit(file_path, commit2)
                
                if content1 is not None and content2 is not None:
                    # Write to temp files
                    temp1 = os.path.join(tmpdir, f"{commit1}_{os.path.basename(file_path)}")
                    temp2 = os.path.join(tmpdir, f"{commit2}_{os.path.basename(file_path)}")
                    
                    with open(temp1, 'w') as f:
                        f.write(content1)
                    with open(temp2, 'w') as f:
                        f.write(content2)
                    
                    # Analyze
                    changes, _ = self._analyze_file_pair(temp1, temp2)
                    all_changes.extend(changes)
                    files_analyzed += 2
        
        # Create report
        report = DiffReport(
            changes=all_changes,
            summary=self._generate_summary(all_changes),
            files_analyzed=files_analyzed
        )
        
        return report
    
    def _find_files(self, directory: str, extensions: Optional[List[str]] = None) -> Dict[str, str]:
        """Find files in directory"""
        files = {}
        
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if extensions:
                    if not any(filename.endswith(ext) for ext in extensions):
                        continue
                
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, directory)
                files[rel_path] = file_path
        
        return files
    
    def _analyze_file_pair(self, file1: str, file2: str) -> Tuple[List[SemanticChange], int]:
        """Analyze a pair of files"""
        # Parse both files
        entities1 = self.parser.parse_file(file1)
        entities2 = self.parser.parse_file(file2)
        
        # Build entity maps
        entity_map1 = {e.full_name(): e for e in entities1}
        entity_map2 = {e.full_name(): e for e in entities2}
        
        # Find changes
        changes = self._find_changes(entity_map1, entity_map2)
        
        return changes, len(entities1) + len(entities2)
    
    def _find_changes(self, entities1: Dict[str, CodeEntity], 
                     entities2: Dict[str, CodeEntity]) -> List[SemanticChange]:
        """Find semantic changes between entity maps"""
        changes = []
        
        # Find removed entities
        for name, entity in entities1.items():
            if name not in entities2:
                change = SemanticChange(
                    change_type=ChangeType.REMOVED,
                    entity_before=entity,
                    entity_after=None,
                    description=f"Removed {entity.type} '{entity.name}'",
                    risk_level=RiskLevel.MEDIUM,
                    impact_score=2.0,
                    affected_files={entity.file_path}
                )
                changes.append(change)
        
        # Find added entities
        for name, entity in entities2.items():
            if name not in entities1:
                change = SemanticChange(
                    change_type=ChangeType.ADDED,
                    entity_before=None,
                    entity_after=entity,
                    description=f"Added {entity.type} '{entity.name}'",
                    risk_level=RiskLevel.LOW,
                    impact_score=1.0,
                    affected_files={entity.file_path}
                )
                changes.append(change)
        
        # Find modified entities
        for name in entities1.keys() & entities2.keys():
            entity1 = entities1[name]
            entity2 = entities2[name]
            
            # Check for changes
            entity_changes = self._compare_entities(entity1, entity2)
            changes.extend(entity_changes)
        
        return changes
    
    def _compare_entities(self, entity1: CodeEntity, entity2: CodeEntity) -> List[SemanticChange]:
        """Compare two entities for changes"""
        changes = []
        
        # Check signature changes
        if entity1.signature != entity2.signature:
            risk = RiskLevel.HIGH if entity1.type in ('method', 'function') else RiskLevel.MEDIUM
            change = SemanticChange(
                change_type=ChangeType.SIGNATURE_CHANGED,
                entity_before=entity1,
                entity_after=entity2,
                description=f"Signature changed for {entity1.type} '{entity1.name}'",
                risk_level=risk,
                impact_score=3.0,
                affected_files={entity1.file_path, entity2.file_path}
            )
            
            # Check if it's API breaking
            if self._is_api_breaking(entity1, entity2):
                change.change_type = ChangeType.API_BREAKING
                change.risk_level = RiskLevel.CRITICAL
                change.impact_score = 5.0
            
            changes.append(change)
        
        # Check behavior changes
        if entity1.ast_node and entity2.ast_node:
            parser = self.parser.parsers.get(entity1.language)
            if parser:
                similarity = parser.compare_behavior(entity1.ast_node, entity2.ast_node)
                
                if similarity < 0.8:  # Significant change
                    change = SemanticChange(
                        change_type=ChangeType.BEHAVIOR_CHANGED,
                        entity_before=entity1,
                        entity_after=entity2,
                        description=f"Behavior changed for {entity1.type} '{entity1.name}'",
                        risk_level=RiskLevel.HIGH,
                        impact_score=4.0 * (1 - similarity),
                        affected_files={entity1.file_path, entity2.file_path}
                    )
                    changes.append(change)
        
        return changes
    
    def _is_api_breaking(self, entity1: CodeEntity, entity2: CodeEntity) -> bool:
        """Check if change is API breaking"""
        # Check for removed parameters
        if entity1.signature and entity2.signature:
            params1 = entity1.signature.count(',')
            params2 = entity2.signature.count(',')
            
            if params1 > params2:  # Parameters removed
                return True
        
        # Check for type changes
        if entity1.annotations != entity2.annotations:
            # Return type changed
            if entity1.annotations.get('return') != entity2.annotations.get('return'):
                return True
        
        return False
    
    def _handle_removed_file(self, file_path: str) -> List[SemanticChange]:
        """Handle removed file"""
        changes = []
        entities = self.parser.parse_file(file_path)
        
        for entity in entities:
            change = SemanticChange(
                change_type=ChangeType.REMOVED,
                entity_before=entity,
                entity_after=None,
                description=f"Removed {entity.type} '{entity.name}' (file deleted)",
                risk_level=RiskLevel.HIGH,
                impact_score=3.0,
                affected_files={file_path}
            )
            changes.append(change)
        
        return changes
    
    def _handle_added_file(self, file_path: str) -> List[SemanticChange]:
        """Handle added file"""
        changes = []
        entities = self.parser.parse_file(file_path)
        
        for entity in entities:
            change = SemanticChange(
                change_type=ChangeType.ADDED,
                entity_before=None,
                entity_after=entity,
                description=f"Added {entity.type} '{entity.name}' (new file)",
                risk_level=RiskLevel.LOW,
                impact_score=1.0,
                affected_files={file_path}
            )
            changes.append(change)
        
        return changes
    
    def _generate_summary(self, changes: List[SemanticChange]) -> Dict[str, Any]:
        """Generate summary statistics"""
        summary = {
            'total_changes': len(changes),
            'by_type': defaultdict(int),
            'by_risk': defaultdict(int),
            'affected_files': len(set(chain.from_iterable(c.affected_files for c in changes))),
            'total_impact_score': sum(c.impact_score for c in changes)
        }
        
        for change in changes:
            summary['by_type'][change.change_type.name] += 1
            summary['by_risk'][change.risk_level.name] += 1
        
        return dict(summary)
    
    def _generate_recommendations(self, report: DiffReport) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Check for high-risk changes
        high_risk = [c for c in report.changes if c.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
        if high_risk:
            recommendations.append(f"Review {len(high_risk)} high-risk changes carefully")
        
        # Check for breaking changes
        if report.breaking_changes:
            recommendations.append(f"Update documentation for {len(report.breaking_changes)} breaking API changes")
            recommendations.append("Consider versioning strategy for breaking changes")
        
        # Check for missing tests
        if hasattr(report, 'test_coverage_impact'):
            recommendations.append("Add tests for new functionality")
        
        # Check for performance impact
        perf_changes = [c for c in report.changes if c.change_type == ChangeType.PERFORMANCE_IMPACT]
        if perf_changes:
            recommendations.append(f"Run performance benchmarks for {len(perf_changes)} performance-sensitive changes")
        
        # Check for security impact
        sec_changes = [c for c in report.changes if c.change_type == ChangeType.SECURITY_IMPACT]
        if sec_changes:
            recommendations.append(f"Conduct security review for {len(sec_changes)} security-sensitive changes")
        
        return recommendations

def main():
    """Main entry point"""
    # Don't use standard parser for semantic_diff as it needs custom arguments
    parser = argparse.ArgumentParser(description="Semantic Diff V3 - Advanced semantic code analysis")
    
    # Input options
    parser.add_argument('input1', nargs='?', help='First file/directory')
    parser.add_argument('input2', nargs='?', help='Second file/directory')
    
    # Git options
    parser.add_argument('--git', nargs=2, metavar=('COMMIT1', 'COMMIT2'),
                       help='Compare git commits')
    
    # Filtering options
    parser.add_argument('--extensions', nargs='+', metavar='EXT',
                       help='File extensions to analyze (e.g., .py .java)')
    # Analysis options
    parser.add_argument('--test-impact', action='store_true',
                       help='Analyze test coverage impact')
    parser.add_argument('--performance', action='store_true',
                       help='Analyze performance impact')
    parser.add_argument('--security', action='store_true',
                       help='Analyze security implications')
    parser.add_argument('--dependencies', action='store_true',
                       help='Build full dependency graph')
    
    # Output options
    parser.add_argument('--output', '-o', metavar='FILE',
                       help='Output file for report')
    parser.add_argument('--format', choices=['text', 'json', 'html', 'markdown'],
                       default='text', help='Output format')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Quiet mode - minimal output')
    # Advanced options
    parser.add_argument('--parallel', type=int, metavar='N',
                       help='Number of parallel workers')
    parser.add_argument('--cache', action='store_true',
                       help='Use caching for large projects')
    parser.add_argument('--streaming', action='store_true',
                       help='Use streaming for huge files')
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.git:
        if args.input1 or args.input2:
            parser.error("Cannot specify files with --git option")
    elif not (args.input1 and args.input2):
        parser.error("Must specify two files/directories or use --git")
    
    # Create analyzer
    analyzer = SemanticDiffAnalyzer()
    
    try:
        # Perform analysis
        if args.git:
            report = analyzer.analyze_git_commits(args.git[0], args.git[1])
        elif os.path.isdir(args.input1) and os.path.isdir(args.input2):
            report = analyzer.analyze_directory(args.input1, args.input2, args.extensions)
        else:
            report = analyzer.analyze_files(args.input1, args.input2)
        
        # Additional analysis if requested
        if args.test_impact:
            test_impact = analyzer.test_analyzer.analyze_test_impact(
                report.changes, 
                os.path.dirname(args.input1) if not args.git else '.'
            )
            report.impact_analysis['test_impact'] = test_impact
        
        # Generate output
        if args.format == 'json':
            # JSON output
            output = {
                'timestamp': report.timestamp.isoformat(),
                'summary': report.summary,
                'changes': [
                    {
                        'type': c.change_type.name,
                        'description': c.description,
                        'risk': c.risk_level.name,
                        'impact_score': c.impact_score,
                        'files': list(c.affected_files)
                    }
                    for c in report.changes
                ],
                'recommendations': report.recommendations
            }
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(output, f, indent=2)
            else:
                print(json.dumps(output, indent=2))
        
        elif args.format == 'html':
            if not args.output:
                args.output = 'semantic_diff_report.html'
            analyzer.report_generator.generate_html_report(report, args.output)
            print(f"HTML report generated: {args.output}")
        
        elif args.format == 'markdown':
            if not args.output:
                args.output = 'semantic_diff_report.md'
            analyzer.report_generator.generate_markdown_report(report, args.output)
            print(f"Markdown report generated: {args.output}")
        
        else:
            # Text output
            if not args.quiet:
                print(f"\n{'='*60}")
                print(f"SEMANTIC DIFF ANALYSIS REPORT")
                print(f"{'='*60}\n")
                
                print(f"Files Analyzed: {report.files_analyzed}")
                print(f"Total Changes: {len(report.changes)}")
                print(f"Breaking Changes: {len(report.breaking_changes)}")
                print(f"Overall Risk: {analyzer.report_generator._calculate_overall_risk(report)}")
                
                print(f"\n{'Changes by Type':^30}")
                print(f"{'-'*30}")
                for change_type, count in report.summary['by_type'].items():
                    print(f"{change_type:<20} {count:>10}")
                
                print(f"\n{'Changes by Risk':^30}")
                print(f"{'-'*30}")
                for risk_level, count in report.summary['by_risk'].items():
                    print(f"{risk_level:<20} {count:>10}")
                
                if report.recommendations:
                    print(f"\n{'Recommendations':^30}")
                    print(f"{'-'*30}")
                    for i, rec in enumerate(report.recommendations, 1):
                        print(f"{i}. {rec}")
                
                if args.verbose:
                    print(f"\n{'Detailed Changes':^30}")
                    print(f"{'-'*30}")
                    for change in report.changes[:20]:  # Show first 20
                        print(f"\n{change.change_type.name}: {change.description}")
                        print(f"  Risk: {change.risk_level.name}")
                        print(f"  Impact: {change.impact_score:.2f}")
                        if change.suggestions:
                            print(f"  Suggestions: {'; '.join(change.suggestions)}")
        
        return 0
    
    except Exception as e:
        if args.verbose:
            traceback.print_exc()
        else:
            print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())