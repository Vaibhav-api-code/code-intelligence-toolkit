#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced semantic code comparison tool using AST parsing for accurate analysis.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import sys
import argparse
from pathlib import Path
from collections import OrderedDict
from typing import Dict, Tuple, List, Optional, Set
import difflib
import ast
import json
import gc
from dataclasses import dataclass
from enum import Enum

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Try to import language-specific parsers
try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False


class ChangeType(Enum):
    """Types of changes detected in semantic diff."""
    LOGIC = "logic"
    STRUCTURE = "structure"
    FORMATTING = "formatting"
    COMMENTS = "comments"
    VARIABLES = "variables"
    IMPORTS = "imports"


class RiskLevel(Enum):
    """Risk assessment levels for changes."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SemanticDiffScore:
    """Comprehensive scoring for semantic diff analysis."""
    logic_changes_pct: float
    formatting_pct: float
    comment_pct: float
    structure_pct: float
    variable_pct: float
    import_pct: float
    
    complexity_delta: int
    lines_added: int
    lines_removed: int
    lines_modified: int
    
    methods_added: int
    methods_removed: int
    methods_modified: int
    
    risk_score: RiskLevel
    impact_score: float  # 0-100 scale
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'change_distribution': {
                'logic_changes_pct': self.logic_changes_pct,
                'formatting_pct': self.formatting_pct,
                'comment_pct': self.comment_pct,
                'structure_pct': self.structure_pct,
                'variable_pct': self.variable_pct,
                'import_pct': self.import_pct,
            },
            'code_metrics': {
                'complexity_delta': self.complexity_delta,
                'lines_added': self.lines_added,
                'lines_removed': self.lines_removed,
                'lines_modified': self.lines_modified,
            },
            'method_metrics': {
                'methods_added': self.methods_added,
                'methods_removed': self.methods_removed,
                'methods_modified': self.methods_modified,
            },
            'assessment': {
                'risk_score': self.risk_score.value,
                'impact_score': self.impact_score,
            }
        }


class SemanticDiffScorer:
    """Calculates semantic diff scores and impact analysis."""
    
    def __init__(self):
        self.change_weights = {
            ChangeType.LOGIC: 1.0,      # Highest impact
            ChangeType.STRUCTURE: 0.8,  # High impact
            ChangeType.VARIABLES: 0.6,  # Medium impact
            ChangeType.IMPORTS: 0.5,    # Medium impact
            ChangeType.FORMATTING: 0.2, # Low impact
            ChangeType.COMMENTS: 0.1,   # Lowest impact
        }
    
    def calculate_impact_score(self, added_methods: Dict, removed_methods: Dict, 
                             modified_methods: Dict) -> SemanticDiffScore:
        """
        Calculate comprehensive impact score for semantic changes.
        
        Args:
            added_methods: Dictionary of added methods
            removed_methods: Dictionary of removed methods  
            modified_methods: Dictionary of modified methods with change analysis
            
        Returns:
            SemanticDiffScore with comprehensive analysis
        """
        
        # Count different types of changes
        change_counts = {change_type: 0 for change_type in ChangeType}
        total_changes = 0
        
        complexity_delta = 0
        lines_added = len(added_methods)
        lines_removed = len(removed_methods)
        lines_modified = 0
        
        # Analyze modified methods
        for method_sig, changes in modified_methods.items():
            change_types = changes.get('change_types', {})
            lines_modified += 1
            
            for change_type_str, has_change in change_types.items():
                if has_change:
                    try:
                        change_type = ChangeType(change_type_str)
                        change_counts[change_type] += 1
                        total_changes += 1
                    except ValueError:
                        # Handle any change types not in our enum
                        total_changes += 1
            
            # Estimate complexity delta (simplified)
            if change_types.get('logic_change', False):
                complexity_delta += 2
            elif change_types.get('structure_change', False):
                complexity_delta += 1
        
        # Calculate percentages
        if total_changes > 0:
            logic_pct = (change_counts[ChangeType.LOGIC] / total_changes) * 100
            formatting_pct = (change_counts[ChangeType.FORMATTING] / total_changes) * 100
            comment_pct = (change_counts[ChangeType.COMMENTS] / total_changes) * 100
            structure_pct = (change_counts[ChangeType.STRUCTURE] / total_changes) * 100
            variable_pct = (change_counts[ChangeType.VARIABLES] / total_changes) * 100
            import_pct = (change_counts[ChangeType.IMPORTS] / total_changes) * 100
        else:
            logic_pct = formatting_pct = comment_pct = 0.0
            structure_pct = variable_pct = import_pct = 0.0
        
        # Calculate overall impact score (0-100)
        weighted_impact = 0.0
        for change_type, count in change_counts.items():
            if total_changes > 0:
                weight = self.change_weights[change_type]
                impact = (count / total_changes) * weight * 100
                weighted_impact += impact
        
        # Factor in method additions/removals
        method_impact = (lines_added + lines_removed) * 5  # Each method change = 5 impact points
        weighted_impact += min(method_impact, 20)  # Cap method impact at 20 points
        
        # Factor in complexity changes
        complexity_impact = abs(complexity_delta) * 3  # Each complexity change = 3 impact points
        weighted_impact += min(complexity_impact, 15)  # Cap complexity impact at 15 points
        
        # Ensure impact score is within 0-100 range
        impact_score = min(weighted_impact, 100.0)
        
        # Determine risk level
        risk_score = self._calculate_risk_level(
            logic_pct, lines_added + lines_removed, complexity_delta, impact_score
        )
        
        return SemanticDiffScore(
            logic_changes_pct=logic_pct,
            formatting_pct=formatting_pct,
            comment_pct=comment_pct,
            structure_pct=structure_pct,
            variable_pct=variable_pct,
            import_pct=import_pct,
            complexity_delta=complexity_delta,
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_modified=lines_modified,
            methods_added=len(added_methods),
            methods_removed=len(removed_methods),
            methods_modified=len(modified_methods),
            risk_score=risk_score,
            impact_score=impact_score
        )
    
    def _calculate_risk_level(self, logic_pct: float, method_changes: int, 
                             complexity_delta: int, impact_score: float) -> RiskLevel:
        """Calculate risk level based on change characteristics."""
        
        # Critical risk indicators
        if (logic_pct > 70 or 
            method_changes > 20 or 
            complexity_delta > 10 or 
            impact_score > 80):
            return RiskLevel.CRITICAL
        
        # High risk indicators
        if (logic_pct > 40 or 
            method_changes > 10 or 
            complexity_delta > 5 or 
            impact_score > 60):
            return RiskLevel.HIGH
        
        # Medium risk indicators
        if (logic_pct > 20 or 
            method_changes > 5 or 
            complexity_delta > 2 or 
            impact_score > 30):
            return RiskLevel.MEDIUM
        
        # Low risk
        return RiskLevel.LOW
    
    def format_score_report(self, score: SemanticDiffScore, show_json: bool = False) -> str:
        """Format the scoring results into a readable report."""
        
        if show_json:
            return json.dumps(score.to_dict(), indent=2)
        
        report = []
        report.append("📊 SEMANTIC DIFF IMPACT ANALYSIS")
        report.append("=" * 50)
        
        # Risk assessment
        risk_colors = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡", 
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴"
        }
        
        risk_icon = risk_colors.get(score.risk_score, "⚪")
        report.append(f"\n{risk_icon} RISK LEVEL: {score.risk_score.value}")
        report.append(f"🎯 IMPACT SCORE: {score.impact_score:.1f}/100")
        
        # Change distribution
        report.append(f"\n📈 CHANGE DISTRIBUTION:")
        if score.logic_changes_pct > 0:
            report.append(f"  Logic Changes:    {score.logic_changes_pct:5.1f}%")
        if score.structure_pct > 0:
            report.append(f"  Structure:        {score.structure_pct:5.1f}%")
        if score.variable_pct > 0:
            report.append(f"  Variables:        {score.variable_pct:5.1f}%")
        if score.import_pct > 0:
            report.append(f"  Imports:          {score.import_pct:5.1f}%")
        if score.formatting_pct > 0:
            report.append(f"  Formatting:       {score.formatting_pct:5.1f}%")
        if score.comment_pct > 0:
            report.append(f"  Comments:         {score.comment_pct:5.1f}%")
        
        # Method changes
        report.append(f"\n🔄 METHOD CHANGES:")
        report.append(f"  Added:            {score.methods_added}")
        report.append(f"  Removed:          {score.methods_removed}")
        report.append(f"  Modified:         {score.methods_modified}")
        
        # Code metrics
        report.append(f"\n📏 CODE METRICS:")
        report.append(f"  Lines Added:      {score.lines_added}")
        report.append(f"  Lines Removed:    {score.lines_removed}")
        report.append(f"  Lines Modified:   {score.lines_modified}")
        report.append(f"  Complexity Δ:     {score.complexity_delta:+d}")
        
        # Recommendations
        report.append(f"\n💡 RECOMMENDATIONS:")
        if score.risk_score == RiskLevel.CRITICAL:
            report.append("  • Requires extensive testing and code review")
            report.append("  • Consider breaking into smaller changes")
            report.append("  • Implement gradual rollout strategy")
        elif score.risk_score == RiskLevel.HIGH:
            report.append("  • Thorough testing required")
            report.append("  • Senior developer review recommended")
            report.append("  • Monitor production deployment closely")
        elif score.risk_score == RiskLevel.MEDIUM:
            report.append("  • Standard testing and review process")
            report.append("  • Monitor for unexpected behavior")
        else:
            report.append("  • Standard review and testing sufficient")
        
        return "\n".join(report)

# Import utilities if available
try:
    from common_utils import safe_get_file_content, detect_language
except ImportError:
    def safe_get_file_content(filepath: str, max_size_mb: float = 10) -> Optional[str]:
        """Read file content safely with size limits."""
        try:
            path = Path(filepath)
            if not path.exists():
                return None
            
            # Check file size
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > max_size_mb:
                print(f"Warning: File too large ({size_mb:.1f}MB), skipping", file=sys.stderr)
                return None
            
            return path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return None


class PythonASTAnalyzer:
    """AST-based analyzer for Python code."""
    
    @staticmethod
    def extract_elements(code: str) -> Dict[str, List]:
        """Extract logical elements using Python's AST."""
        elements = {
            'control_structures': [],
            'method_calls': [],
            'assignments': [],
            'declarations': [],
            'exceptions': [],
            'loops': [],
            'conditions': [],
            'returns': [],
            'functions': OrderedDict(),
            'classes': OrderedDict()
        }
        
        try:
            tree = ast.parse(code)
            
            class ElementVisitor(ast.NodeVisitor):
                def __init__(self, elements):
                    self.elements = elements
                    self.current_function = None
                
                def visit_FunctionDef(self, node):
                    func_name = node.name
                    args = [arg.arg for arg in node.args.args]
                    self.elements['functions'][func_name] = {
                        'name': func_name,
                        'args': args,
                        'lineno': node.lineno,
                        'body': ast.unparse(node) if hasattr(ast, 'unparse') else None
                    }
                    self.current_function = func_name
                    self.generic_visit(node)
                    self.current_function = None
                
                def visit_AsyncFunctionDef(self, node):
                    self.visit_FunctionDef(node)  # Treat async functions similarly
                
                def visit_ClassDef(self, node):
                    self.elements['classes'][node.name] = {
                        'name': node.name,
                        'bases': [ast.unparse(base) if hasattr(ast, 'unparse') else str(base) 
                                 for base in node.bases],
                        'lineno': node.lineno
                    }
                    self.generic_visit(node)
                
                def visit_If(self, node):
                    self.elements['control_structures'].append('if')
                    self.generic_visit(node)
                
                def visit_For(self, node):
                    self.elements['loops'].append('for')
                    self.generic_visit(node)
                
                def visit_While(self, node):
                    self.elements['loops'].append('while')
                    self.generic_visit(node)
                
                def visit_Try(self, node):
                    self.elements['exceptions'].append('try')
                    self.generic_visit(node)
                
                def visit_ExceptHandler(self, node):
                    self.elements['exceptions'].append('except')
                    self.generic_visit(node)
                
                def visit_Raise(self, node):
                    self.elements['exceptions'].append('raise')
                    self.generic_visit(node)
                
                def visit_Call(self, node):
                    if isinstance(node.func, ast.Name):
                        self.elements['method_calls'].append(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        self.elements['method_calls'].append(node.func.attr)
                    self.generic_visit(node)
                
                def visit_Assign(self, node):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.elements['assignments'].append(target.id)
                    self.generic_visit(node)
                
                def visit_AnnAssign(self, node):
                    if isinstance(node.target, ast.Name):
                        self.elements['declarations'].append(node.target.id)
                    self.generic_visit(node)
                
                def visit_Return(self, node):
                    self.elements['returns'].append('return')
                    self.generic_visit(node)
                
                def visit_Compare(self, node):
                    for op in node.ops:
                        op_name = op.__class__.__name__
                        self.elements['conditions'].append(op_name)
                    self.generic_visit(node)
            
            visitor = ElementVisitor(elements)
            visitor.visit(tree)
            
        except SyntaxError as e:
            print(f"Warning: Python syntax error at line {e.lineno}: {e.msg}", file=sys.stderr)
            return extract_logic_elements_regex(code)
        except (RecursionError, MemoryError) as e:
            print(f"Warning: AST parsing failed due to resource limits: {e}", file=sys.stderr)
            return extract_logic_elements_regex(code)
        except Exception as e:
            print(f"Warning: Unexpected AST parsing error: {e}", file=sys.stderr)
            return extract_logic_elements_regex(code)
        finally:
            # Force garbage collection to free memory
            gc.collect()
        
        return elements


class JavaASTAnalyzer:
    """AST-based analyzer for Java code using javalang."""
    
    @staticmethod
    def extract_elements(code: str) -> Dict[str, List]:
        """Extract logical elements using javalang AST."""
        elements = {
            'control_structures': [],
            'method_calls': [],
            'assignments': [],
            'declarations': [],
            'exceptions': [],
            'loops': [],
            'conditions': [],
            'returns': [],
            'methods': OrderedDict(),
            'classes': OrderedDict()
        }
        
        if not JAVALANG_AVAILABLE:
            return extract_logic_elements_regex(code)
        
        try:
            tree = javalang.parse.parse(code)
            # Store code lines for body extraction
            code_lines = code.splitlines()
            
            # Walk the AST
            for path, node in tree:
                node_type = type(node).__name__
                
                if node_type == 'MethodDeclaration':
                    method_sig = f"{' '.join(node.modifiers)} {node.return_type.name if node.return_type else 'void'} {node.name}"
                    
                    # Extract method body using position information
                    start_line = node.position.line - 1 if node.position else 0
                    body_content = JavaASTAnalyzer._extract_method_body(code_lines, start_line, node)
                    
                    elements['methods'][method_sig] = {
                        'name': node.name,
                        'modifiers': list(node.modifiers),
                        'return_type': node.return_type.name if node.return_type else 'void',
                        'parameters': [(p.type.name, p.name) for p in node.parameters],
                        'body': body_content,
                        'start_line': start_line + 1,
                        'position': node.position
                    }
                
                elif node_type == 'ClassDeclaration':
                    elements['classes'][node.name] = {
                        'name': node.name,
                        'modifiers': list(node.modifiers),
                        'extends': node.extends.name if node.extends else None,
                        'implements': [i.name for i in node.implements] if node.implements else []
                    }
                
                elif node_type == 'IfStatement':
                    elements['control_structures'].append('if')
                
                elif node_type == 'SwitchStatement':
                    elements['control_structures'].append('switch')
                
                elif node_type == 'ForStatement' or node_type == 'EnhancedForControl':
                    elements['loops'].append('for')
                
                elif node_type == 'WhileStatement':
                    elements['loops'].append('while')
                
                elif node_type == 'DoStatement':
                    elements['loops'].append('do')
                
                elif node_type == 'TryStatement':
                    elements['exceptions'].append('try')
                
                elif node_type == 'CatchClause':
                    elements['exceptions'].append('catch')
                
                elif node_type == 'ThrowStatement':
                    elements['exceptions'].append('throw')
                
                elif node_type == 'MethodInvocation':
                    elements['method_calls'].append(node.member)
                
                elif node_type == 'Assignment':
                    if hasattr(node, 'expressionl') and hasattr(node.expressionl, 'member'):
                        elements['assignments'].append(node.expressionl.member)
                
                elif node_type == 'LocalVariableDeclaration':
                    for declarator in node.declarators:
                        elements['declarations'].append(declarator.name)
                
                elif node_type == 'ReturnStatement':
                    elements['returns'].append('return')
                
                elif node_type in ['BinaryOperation', 'TernaryExpression']:
                    if hasattr(node, 'operator'):
                        elements['conditions'].append(node.operator)
        
        except Exception as e:
            print(f"Java parsing error: {e}", file=sys.stderr)
            # Fall back to regex parsing
            return extract_logic_elements_regex(code)
        
        return elements
    
    @staticmethod
    def _extract_method_body(code_lines: List[str], start_line: int, node) -> str:
        """
        Extract method body using AST node positions when available,
        falling back to brace counting.
        
        Args:
            code_lines: List of code lines
            start_line: Starting line of method (0-indexed)
            node: Method node from AST
            
        Returns:
            The complete method body including signature
        """
        if start_line >= len(code_lines):
            return ""
        
        # Try to use node positions if available
        if hasattr(node, 'body') and node.body:
            try:
                # Walk through the body to find the last position
                last_line = start_line
                last_col = 0
                
                # Find the maximum line number in the method body
                for path, child in node.body:
                    if hasattr(child, 'position') and child.position:
                        if hasattr(child.position, 'line'):
                            last_line = max(last_line, child.position.line - 1)  # Convert to 0-indexed
                
                # If we found a meaningful range, extract it
                if last_line > start_line:
                    # Look for the closing brace after the last statement
                    for i in range(last_line, min(last_line + 10, len(code_lines))):
                        if '}' in code_lines[i]:
                            last_line = i
                            break
                    
                    # Extract the method
                    return '\n'.join(code_lines[start_line:last_line + 1])
            except Exception:
                # If position-based extraction fails, fall back to brace counting
                pass
        
        # Fallback to brace counting method
        brace_count = 0
        method_start = start_line
        in_method = False
        result_lines = []
        
        for i in range(start_line, len(code_lines)):
            line = code_lines[i]
            result_lines.append(line)
            
            # Count braces
            for char in line:
                if char == '{':
                    brace_count += 1
                    in_method = True
                elif char == '}':
                    brace_count -= 1
            
            # Method ends when brace count returns to 0
            if in_method and brace_count == 0:
                break
        
        return '\n'.join(result_lines)


def extract_logic_elements_regex(code: str) -> Dict[str, List[str]]:
    """
    Original regex-based extraction as fallback for unsupported languages.
    """
    elements = {
        'control_structures': [],
        'method_calls': [],
        'assignments': [],
        'declarations': [],
        'exceptions': [],
        'loops': [],
        'conditions': [],
        'returns': []
    }
    
    # Control structures
    control_pattern = r'\b(if|else if|else|switch|case)(?=\s*\()'
    elements['control_structures'] = re.findall(control_pattern, code)
    
    # Method calls
    method_pattern = r'\b(\w+)\s*\([^)]*\)'
    all_methods = re.findall(method_pattern, code)
    exclude_patterns = {'if', 'else', 'switch', 'while', 'for', 'catch', 'synchronized', 
                       'with', 'return', 'throw', 'new', 'typeof', 'instanceof', 'sizeof'}
    elements['method_calls'] = [m for m in all_methods if m not in exclude_patterns]
    
    # Variable assignments
    assignment_pattern = r'(\w+)\s*=(?!=)\s*[^=]'
    elements['assignments'] = re.findall(assignment_pattern, code)
    
    # Variable/field declarations (Java-style)
    java_decl_pattern = r'\b(?:public|private|protected|static|final)?\s*(\w+)\s+(\w+)\s*[;=]'
    declarations = [f"{match[0]} {match[1]}" for match in re.findall(java_decl_pattern, code)]
    elements['declarations'].extend(declarations)
    
    # Exception handling
    exception_pattern = r'\b(try|catch|finally|throw|throws)\b'
    elements['exceptions'] = re.findall(exception_pattern, code)
    
    # Loops
    loop_pattern = r'\b(for|while|do)\s*\('
    elements['loops'] = re.findall(loop_pattern, code)
    
    # Conditional expressions
    condition_pattern = r'([<>!=]=?|&&|\|\|)'
    elements['conditions'] = re.findall(condition_pattern, code)
    
    # Return statements
    return_pattern = r'\breturn\s+([^;]+);'
    elements['returns'] = re.findall(return_pattern, code)
    
    return elements


def extract_logic_elements(code: str, language: str) -> Dict[str, List]:
    """
    Extract logical elements using appropriate parser based on language.
    """
    if language == 'python':
        return PythonASTAnalyzer.extract_elements(code)
    elif language == 'java' and JAVALANG_AVAILABLE:
        return JavaASTAnalyzer.extract_elements(code)
    else:
        # Fall back to regex for other languages
        return extract_logic_elements_regex(code)


def normalize_code(code: str, remove_comments: bool = True) -> str:
    """
    Normalizes code by removing comments and standardizing whitespace.
    """
    if remove_comments:
        # Remove single-line comments
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        # Remove multi-line comments
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)
        # Remove Python-style comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    
    # Normalize whitespace
    code = re.sub(r'\s+', ' ', code)
    # Remove leading/trailing whitespace
    code = code.strip()
    
    return code


def compare_ast_elements(elements1: Dict, elements2: Dict) -> Dict[str, Dict]:
    """
    Compare two sets of AST-extracted elements.
    """
    changes = {}
    
    # Compare simple lists
    for category in ['control_structures', 'loops', 'exceptions', 'method_calls', 
                    'assignments', 'declarations', 'conditions', 'returns']:
        if category in elements1 and category in elements2:
            set1 = set(elements1.get(category, []))
            set2 = set(elements2.get(category, []))
            
            if set1 != set2:
                changes[category] = {
                    'added': list(set2 - set1),
                    'removed': list(set1 - set2),
                    'changed': len(set1 ^ set2) > 0
                }
    
    # Compare functions/methods
    for key in ['functions', 'methods']:
        if key in elements1 or key in elements2:
            funcs1 = elements1.get(key, {})
            funcs2 = elements2.get(key, {})
            
            added_funcs = set(funcs2.keys()) - set(funcs1.keys())
            removed_funcs = set(funcs1.keys()) - set(funcs2.keys())
            
            if added_funcs or removed_funcs:
                changes[key] = {
                    'added': list(added_funcs),
                    'removed': list(removed_funcs),
                    'changed': True
                }
    
    return changes


def detect_change_types_ast(code1: str, code2: str, language: str) -> Dict[str, bool]:
    """
    Detect change types using AST analysis when possible.
    """
    # Normalize for comparison
    norm1 = normalize_code(code1, remove_comments=True)
    norm2 = normalize_code(code2, remove_comments=True)
    
    # If normalized versions are identical, only comments changed
    if norm1 == norm2:
        return {
            'comment_only_change': True,
            'logic_change': False,
            'structure_change': False,
            'ast_analysis': False,
            'whitespace_only': normalize_code(code1, remove_comments=False) == normalize_code(code2, remove_comments=False)
        }
    
    # Extract and compare elements using AST if possible
    elements1 = extract_logic_elements(code1, language)
    elements2 = extract_logic_elements(code2, language)
    element_changes = compare_ast_elements(elements1, elements2)
    
    # Determine if AST was used
    ast_used = False
    if language == 'python' and ('functions' in elements1 or 'classes' in elements1):
        ast_used = True
    elif language == 'java' and JAVALANG_AVAILABLE and ('methods' in elements1 or 'classes' in elements1):
        ast_used = True
    
    # Determine change types
    structure_changed = any(
        element_changes.get(cat, {}).get('changed', False) 
        for cat in ['control_structures', 'loops', 'exceptions']
    )
    
    logic_changed = any(
        element_changes.get(cat, {}).get('changed', False) 
        for cat in ['conditions', 'returns', 'method_calls', 'functions', 'methods']
    )
    
    return {
        'comment_only_change': False,
        'logic_change': logic_changed,
        'structure_change': structure_changed,
        'variable_change': element_changes.get('assignments', {}).get('changed', False),
        'declaration_change': element_changes.get('declarations', {}).get('changed', False),
        'element_changes': element_changes,
        'ast_analysis': ast_used
    }


def extract_methods(code: str, language: str = 'java') -> Dict[str, Dict]:
    """
    Extract methods from code using AST when possible.
    """
    methods = OrderedDict()
    
    if language == 'python':
        elements = PythonASTAnalyzer.extract_elements(code)
        for name, func_info in elements.get('functions', {}).items():
            methods[name] = {
                'name': name,
                'signature': name,
                'content': func_info.get('body', ''),
                'body': func_info.get('body', ''),
                'start_pos': 0,
                'end_pos': 0
            }
    
    elif language == 'java' and JAVALANG_AVAILABLE:
        elements = JavaASTAnalyzer.extract_elements(code)
        for sig, method_info in elements.get('methods', {}).items():
            body_content = method_info.get('body', '')
            methods[sig] = {
                'name': method_info['name'],
                'signature': sig,
                'content': body_content,
                'body': body_content,
                'start_pos': 0,
                'end_pos': 0
            }
    
    # If AST parsing didn't find methods or isn't available, fall back to regex
    if not methods:
        if language == 'java':
            pattern = r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        elif language == 'python':
            pattern = r'def\s+(\w+)\s*\([^)]*\):\n((?:\s{4,}.*\n)*)'
        else:
            pattern = r'(\w+)\s*\([^)]*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        for match in re.finditer(pattern, code, re.MULTILINE | re.DOTALL):
            method_name = match.group(1)
            method_body = match.group(2)
            signature = match.group(0).split('{')[0].strip()
            
            methods[signature] = {
                'name': method_name,
                'signature': signature,
                'content': match.group(0),
                'body': method_body,
                'start_pos': match.start(),
                'end_pos': match.end()
            }
    
    return methods


def enhanced_method_comparison(methods1: Dict, methods2: Dict, language: str) -> Tuple[Dict, Dict, Dict]:
    """
    Enhanced comparison using AST analysis when possible.
    """
    added = OrderedDict()
    removed = OrderedDict()
    modified = OrderedDict()
    
    # Find removed methods
    for sig, method in methods1.items():
        if sig not in methods2:
            removed[sig] = method
    
    # Find added methods
    for sig, method in methods2.items():
        if sig not in methods1:
            added[sig] = method
    
    # Find modified methods
    for sig, method1 in methods1.items():
        if sig in methods2:
            method2 = methods2[sig]
            
            # Quick check if content is identical
            if method1.get('content') == method2.get('content'):
                continue
            
            # Perform semantic analysis
            change_types = detect_change_types_ast(
                method1.get('content', ''), 
                method2.get('content', ''),
                language
            )
            
            modified[sig] = {
                'old': method1,
                'new': method2,
                'change_types': change_types,
                'diff': list(difflib.unified_diff(
                    method1.get('content', '').splitlines(keepends=True),
                    method2.get('content', '').splitlines(keepends=True),
                    fromfile=f"{sig} (old)",
                    tofile=f"{sig} (new)",
                    lineterm=''
                ))
            }
    
    return added, removed, modified


def format_semantic_diff_report(added: Dict, removed: Dict, modified: Dict,
                              show_logic_only: bool = False,
                              show_details: bool = True) -> str:
    """
    Format report with AST analysis indicators.
    """
    output = []
    
    # Header
    output.append("=" * 80)
    output.append("SEMANTIC CODE COMPARISON REPORT (AST-Enhanced)")
    output.append("=" * 80)
    
    # Check if AST was used
    ast_used = any(
        m.get('change_types', {}).get('ast_analysis', False) 
        for m in modified.values()
    )
    
    if ast_used:
        output.append("\n✨ Using AST analysis for accurate semantic comparison")
    else:
        output.append("\n⚠️  AST parser not available - using regex fallback")
    
    # Summary
    output.append("\n📊 SUMMARY")
    output.append("-" * 40)
    
    # Count logic changes
    logic_changes = sum(1 for m in modified.values() 
                       if m['change_types'].get('logic_change', False))
    comment_only = sum(1 for m in modified.values() 
                      if m['change_types'].get('comment_only_change', False))
    structure_changes = sum(1 for m in modified.values() 
                          if m['change_types'].get('structure_change', False))
    
    output.append(f"Methods Added: {len(added)}")
    output.append(f"Methods Removed: {len(removed)}")
    output.append(f"Methods Modified: {len(modified)}")
    if modified:
        output.append(f"  - Logic Changes: {logic_changes}")
        output.append(f"  - Structure Changes: {structure_changes}")
        output.append(f"  - Comment-Only Changes: {comment_only}")
    
    # Added methods
    if added:
        output.append("\n➕ ADDED METHODS")
        output.append("-" * 40)
        for sig, method in added.items():
            output.append(f"  + {sig}")
    
    # Removed methods
    if removed:
        output.append("\n➖ REMOVED METHODS")
        output.append("-" * 40)
        for sig, method in removed.items():
            output.append(f"  - {sig}")
    
    # Modified methods
    if modified:
        output.append("\n🔄 MODIFIED METHODS")
        output.append("-" * 40)
        
        for sig, changes in modified.items():
            change_types = changes['change_types']
            
            # Skip if only showing logic changes and this isn't one
            if show_logic_only and not change_types.get('logic_change', False):
                continue
            
            # Method header with change indicators
            indicators = []
            if change_types.get('logic_change'):
                indicators.append("LOGIC")
            if change_types.get('structure_change'):
                indicators.append("STRUCTURE")
            if change_types.get('comment_only_change'):
                indicators.append("COMMENTS")
            if change_types.get('variable_change'):
                indicators.append("VARIABLES")
            
            ast_marker = " [AST]" if change_types.get('ast_analysis') else " [Regex]"
            output.append(f"\n  {'*' if change_types.get('logic_change') else '○'} {sig}{ast_marker}")
            if indicators:
                output.append(f"    Changes: {', '.join(indicators)}")
            
            # Show detailed changes if requested
            if show_details and change_types.get('element_changes'):
                element_changes = change_types['element_changes']
                for category, changes in element_changes.items():
                    if changes.get('added') or changes.get('removed'):
                        output.append(f"    {category.replace('_', ' ').title()}:")
                        if changes.get('added'):
                            output.append(f"      + Added: {', '.join(changes['added'][:3])}")
                        if changes.get('removed'):
                            output.append(f"      - Removed: {', '.join(changes['removed'][:3])}")
    
    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(
        description='Semantic code comparison with AST support - Compare code based on logic rather than text',
        epilog='''
EXAMPLES:
  # Basic semantic comparison (auto-detects language)
  %(prog)s FileV1.java FileV2.java
  
  # Show only logic changes
  %(prog)s FileV1.java FileV2.java --logic-only
  
  # Show detailed change analysis
  %(prog)s FileV1.java FileV2.java --show-details
  
  # Compare Python files (uses AST)
  %(prog)s old_version.py new_version.py --language python
  
  # Show traditional diff for methods with logic changes
  %(prog)s FileV1.java FileV2.java --show-diff
  
  # Calculate impact scoring and risk assessment
  %(prog)s FileV1.java FileV2.java --score
  
  # Get scoring as JSON for automation
  %(prog)s FileV1.java FileV2.java --score-json
  
  # Only show if risk level is HIGH or CRITICAL
  %(prog)s FileV1.java FileV2.java --score --risk-threshold HIGH
  
AST SUPPORT:
  - Python: Built-in ast module (always available)
  - Java: javalang library (install with: pip install javalang)
  - Others: Regex-based analysis
  
IMPACT SCORING:
  Analyzes changes and provides:
  - Risk assessment (LOW/MEDIUM/HIGH/CRITICAL)
  - Impact score (0-100)
  - Change distribution (logic vs formatting vs comments)
  - Recommendations for review and testing
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('file1', help='First file to compare')
    parser.add_argument('file2', help='Second file to compare')
    
    # Comparison options
    parser.add_argument('--language', '--lang', 
                       choices=['java', 'python', 'javascript', 'cpp', 'auto'],
                       default='auto', help='Programming language (default: auto-detect)')
    parser.add_argument('--logic-only', action='store_true',
                       help='Show only methods with logic changes')
    parser.add_argument('--show-details', action='store_true', default=True,
                       help='Show detailed change information (default: true)')
    parser.add_argument('--show-diff', action='store_true',
                       help='Show unified diff for modified methods')
    
    # Output options
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output')
    
    # Scoring options
    parser.add_argument('--score', action='store_true',
                       help='Calculate and show impact scoring analysis')
    parser.add_argument('--score-json', action='store_true',
                       help='Output scoring analysis as JSON')
    parser.add_argument('--risk-threshold', choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
                       help='Only show results if risk level meets or exceeds threshold')
    
    args = parser.parse_args()
    
    try:
        # Read files
        content1 = safe_get_file_content(args.file1)
        content2 = safe_get_file_content(args.file2)
        
        if content1 is None:
            print(f"Error: Cannot read file '{args.file1}'", file=sys.stderr)
            sys.exit(1)
        
        if content2 is None:
            print(f"Error: Cannot read file '{args.file2}'", file=sys.stderr)
            sys.exit(1)
        
        # Auto-detect language if needed
        if args.language == 'auto':
            if args.file1.endswith('.py') or args.file2.endswith('.py'):
                args.language = 'python'
            elif args.file1.endswith('.java') or args.file2.endswith('.java'):
                args.language = 'java'
            elif args.file1.endswith(('.js', '.jsx', '.ts', '.tsx')):
                args.language = 'javascript'
            elif args.file1.endswith(('.c', '.cpp', '.cc', '.cxx', '.h', '.hpp')):
                args.language = 'cpp'
            else:
                args.language = 'java'  # Default
        
        # Extract methods
        if not args.quiet:
            print(f"Analyzing {args.file1} vs {args.file2} (language: {args.language})...", file=sys.stderr)
        
        methods1 = extract_methods(content1, args.language)
        methods2 = extract_methods(content2, args.language)
        
        # Perform comparison
        added, removed, modified = enhanced_method_comparison(methods1, methods2, args.language)
        
        # Calculate scoring if requested
        scorer = None
        score = None
        if args.score or args.score_json or args.risk_threshold:
            scorer = SemanticDiffScorer()
            score = scorer.calculate_impact_score(added, removed, modified)
            
            # Check risk threshold
            if args.risk_threshold:
                threshold_levels = {
                    'LOW': [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL],
                    'MEDIUM': [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL],
                    'HIGH': [RiskLevel.HIGH, RiskLevel.CRITICAL],
                    'CRITICAL': [RiskLevel.CRITICAL]
                }
                
                if score.risk_score not in threshold_levels[args.risk_threshold]:
                    if not args.quiet:
                        print(f"Risk level {score.risk_score.value} does not meet threshold {args.risk_threshold}", file=sys.stderr)
                    sys.exit(0)
        
        # Generate and show main report
        if not args.score_json:  # Don't show regular report if JSON-only output
            report = format_semantic_diff_report(
                added, removed, modified,
                show_logic_only=args.logic_only,
                show_details=args.show_details
            )
            print(report)
        
        # Show scoring analysis
        if score and (args.score or args.score_json):
            if args.score_json:
                print(scorer.format_score_report(score, show_json=True))
            else:
                print("\n" + "=" * 60)
                print(scorer.format_score_report(score, show_json=False))
        
        # Show diffs if requested
        if args.show_diff and modified:
            print("\n" + "=" * 80)
            print("DETAILED DIFFS FOR MODIFIED METHODS")
            print("=" * 80)
            
            for sig, changes in modified.items():
                if args.logic_only and not changes['change_types'].get('logic_change'):
                    continue
                
                print(f"\n{sig}:")
                print('\n'.join(changes['diff']))
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()