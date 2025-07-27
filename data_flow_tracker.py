#!/usr/bin/env python3
"""
Data Flow Tracker - Comprehensive variable dependency and data flow analysis tool

This tool performs static data flow analysis to track how values propagate through
variables, assignments, and function calls in Python and Java code. It builds a
complete dependency graph showing how data flows through your program.

Key Features:
- Bidirectional tracking: Forward (what X affects) and backward (what affects Y)
- Inter-procedural analysis: Tracks data across function/method boundaries
- Parameter mapping: Maps arguments to parameters (x → func(param) → return)
- Complex expression support: Binary ops, ternary, comparisons, method chains
- Multi-language: Full Python and Java support with AST analysis
- Multiple output formats: Text, JSON, and GraphViz visualization

Python Support:
- Classes, methods, and functions
- Global and instance variables (self.attr)
- Tuple unpacking and multiple assignments
- List/dict comprehensions and operations
- Lambda functions and closures
- Array/list indexing and slicing
- Method chaining (obj.method1().method2())
- Complex expressions with all operators

Java Support:
- Classes, methods, and fields
- Local variables and parameters
- All expression types (binary, ternary, cast)
- Method invocations and chaining
- Array access and object creation
- Static and instance members

Use Cases:
- Impact analysis: See what changes when you modify a variable
- Debugging: Trace where incorrect values come from
- Refactoring: Understand dependencies before making changes
- Documentation: Generate dependency graphs for complex calculations
- Code review: Verify data flow matches design intent
"""

import ast
import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Union, Any
from collections import defaultdict, deque
from dataclasses import dataclass, field
import re

# Try importing Java support
try:
    import javalang
    JAVA_SUPPORT = True
except ImportError:
    JAVA_SUPPORT = False

from common_utils import (
    safe_get_file_content, detect_language, classify_file_type
)

import logging
logger = logging.getLogger(__name__)

def safe_read_file(filepath):
    """Read file safely"""
    return safe_get_file_content(filepath)

def get_file_type(filepath):
    """Get file type"""
    if filepath.endswith('.py'):
        return 'python'
    elif filepath.endswith('.java'):
        return 'java'
    else:
        return 'unknown'

def handle_error(e, context=""):
    """Handle errors"""
    logger.error(f"Error {context}: {str(e)}")

@dataclass
class VarLocation:
    """Represents a location where a variable is used/defined"""
    file: str
    line: int
    col: int
    context: str  # e.g., "in method foo()" or "in class Bar"
    code: str     # The actual line of code

@dataclass
class DataFlowNode:
    """Represents a node in the data flow graph"""
    name: str
    node_type: str  # 'var', 'param', 'return', 'field', 'call'
    location: VarLocation
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    expression: Optional[str] = None  # Full expression if complex

@dataclass 
class FunctionInfo:
    """Information about a function/method"""
    name: str
    params: List[str]
    returns: List[str]  # Variables that are returned
    location: VarLocation
    calls: List[Tuple[str, Dict[str, str]]]  # (func_name, param_mapping)

class DataFlowAnalyzer:
    """Base class for data flow analysis"""
    
    def __init__(self):
        self.nodes: Dict[str, DataFlowNode] = {}
        self.functions: Dict[str, FunctionInfo] = {}
        self.current_context: List[str] = []  # Stack of contexts
        self.current_file = ""
        self.call_graph: Dict[str, List[Tuple[str, Dict[str, str]]]] = {}  # caller -> [(callee, param_map)]
        self.inter_procedural = False
        
    def add_dependency(self, var_name: str, depends_on: Set[str], 
                      location: VarLocation, expression: Optional[str] = None):
        """Add a dependency relationship"""
        if var_name not in self.nodes:
            self.nodes[var_name] = DataFlowNode(
                name=var_name,
                node_type='var',
                location=location
            )
        
        node = self.nodes[var_name]
        node.dependencies.update(depends_on)
        if expression:
            node.expression = expression
            
        # Update reverse dependencies
        for dep in depends_on:
            if dep not in self.nodes:
                # Create placeholder node
                self.nodes[dep] = DataFlowNode(
                    name=dep,
                    node_type='var',
                    location=location  # Will be updated when we find definition
                )
            self.nodes[dep].dependents.add(var_name)
    
    def track_forward(self, var_name: str, max_depth: int = -1) -> Dict[str, Any]:
        """Track forward data flow from a variable"""
        if var_name not in self.nodes:
            return {"error": f"Variable '{var_name}' not found in analysis"}
            
        visited = set()
        result = {
            "variable": var_name,
            "affects": [],
            "flow_paths": [],
            "total_affected": 0
        }
        
        def traverse(name: str, path: List[str], depth: int):
            if max_depth >= 0 and depth > max_depth:
                return
            if name in visited:
                return
                
            visited.add(name)
            node = self.nodes.get(name)
            if not node:
                return
                
            for dependent in node.dependents:
                new_path = path + [dependent]
                dep_node = self.nodes.get(dependent)
                if dep_node:
                    result["affects"].append({
                        "name": dependent,
                        "location": f"{dep_node.location.file}:{dep_node.location.line}",
                        "code": dep_node.location.code,
                        "expression": dep_node.expression
                    })
                    result["flow_paths"].append(" → ".join(new_path))
                traverse(dependent, new_path, depth + 1)
        
        traverse(var_name, [var_name], 0)
        result["total_affected"] = len(visited) - 1
        return result
    
    def track_backward(self, var_name: str, max_depth: int = -1) -> Dict[str, Any]:
        """Track backward data flow to a variable"""
        if var_name not in self.nodes:
            return {"error": f"Variable '{var_name}' not found in analysis"}
            
        visited = set()
        result = {
            "variable": var_name,
            "depends_on": [],
            "dependency_paths": [],
            "total_dependencies": 0
        }
        
        def traverse(name: str, path: List[str], depth: int):
            if max_depth >= 0 and depth > max_depth:
                return
            if name in visited:
                return
                
            visited.add(name)
            node = self.nodes.get(name)
            if not node:
                return
                
            for dependency in node.dependencies:
                new_path = [dependency] + path
                dep_node = self.nodes.get(dependency)
                if dep_node:
                    result["depends_on"].append({
                        "name": dependency,
                        "location": f"{dep_node.location.file}:{dep_node.location.line}",
                        "code": dep_node.location.code
                    })
                    result["dependency_paths"].append(" → ".join(new_path))
                traverse(dependency, new_path, depth + 1)
        
        traverse(var_name, [var_name], 0)
        result["total_dependencies"] = len(visited) - 1
        return result

class PythonDataFlowAnalyzer(DataFlowAnalyzer):
    """Python-specific data flow analyzer using AST"""
    
    def analyze_file(self, filepath: str) -> bool:
        """Analyze a Python file"""
        try:
            content = safe_read_file(filepath)
            if not content:
                return False
                
            self.current_file = filepath
            tree = ast.parse(content)
            self.visit(tree)
            return True
            
        except Exception as e:
            handle_error(e, f"analyzing {filepath}")
            return False
    
    def visit(self, node):
        """Visit AST nodes"""
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        """Called for nodes without specific visitors"""
        for child in ast.iter_child_nodes(node):
            self.visit(child)
    
    def visit_ClassDef(self, node):
        """Handle class definitions"""
        class_name = node.name
        self.current_context.append(f"class {class_name}")
        
        # Visit class body
        for stmt in node.body:
            self.visit(stmt)
            
        self.current_context.pop()
    
    def visit_FunctionDef(self, node):
        """Handle function definitions"""
        func_name = node.name
        self.current_context.append(f"function {func_name}")
        
        # Track function info
        params = [arg.arg for arg in node.args.args]
        self.functions[func_name] = FunctionInfo(
            name=func_name,
            params=params,
            returns=[],
            location=VarLocation(
                file=self.current_file,
                line=node.lineno,
                col=node.col_offset,
                context=" → ".join(self.current_context),
                code=f"def {func_name}({', '.join(params)}):"
            ),
            calls=[]
        )
        
        # Visit function body
        for stmt in node.body:
            self.visit(stmt)
            
        self.current_context.pop()
    
    def visit_Assign(self, node):
        """Handle assignments like x = y + z"""
        # Get all targets (can be multiple like x = y = z)
        targets = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                targets.append(target.id)
            elif isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        targets.append(elt.id)
        
        # Extract dependencies from the value
        dependencies = self.extract_dependencies(node.value)
        
        # Check if this is a function call assignment
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            func_name = node.value.func.id
            if func_name in self.functions:
                # Add dependency on function's return value
                return_node_name = f"{func_name}.return"
                dependencies.add(return_node_name)
        
        # Get the expression as string
        try:
            import astor
            expression = astor.to_source(node.value).strip()
        except:
            expression = str(dependencies)
        
        # Add dependencies for each target
        for target in targets:
            location = VarLocation(
                file=self.current_file,
                line=node.lineno,
                col=node.col_offset,
                context=" → ".join(self.current_context),
                code=self.get_line_content(node.lineno)
            )
            self.add_dependency(target, dependencies, location, expression)
        
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Handle function calls"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # Map arguments to parameters if we know the function
            if func_name in self.functions:
                func_info = self.functions[func_name]
                param_mapping = {}
                
                # Map positional arguments
                for i, arg in enumerate(node.args):
                    if i < len(func_info.params):
                        param_name = func_info.params[i]
                        arg_vars = self.extract_dependencies(arg)
                        if arg_vars:
                            param_mapping[param_name] = list(arg_vars)[0]  # Simplified
                
                # Track the call
                if self.current_context:
                    caller = self.current_context[-1].split()[-1]
                    if caller in self.functions:
                        self.functions[caller].calls.append((func_name, param_mapping))
        
        self.generic_visit(node)
    
    def visit_Return(self, node):
        """Handle return statements"""
        if node.value and self.current_context:
            func_name = self.current_context[-1].split()[-1]
            if func_name in self.functions:
                return_vars = self.extract_dependencies(node.value)
                self.functions[func_name].returns.extend(return_vars)
        
        self.generic_visit(node)
    
    def extract_dependencies(self, node) -> Set[str]:
        """Extract all variable names from an expression"""
        deps = set()
        
        if isinstance(node, ast.Name):
            deps.add(node.id)
        elif isinstance(node, ast.BinOp):
            deps.update(self.extract_dependencies(node.left))
            deps.update(self.extract_dependencies(node.right))
        elif isinstance(node, ast.UnaryOp):
            deps.update(self.extract_dependencies(node.operand))
        elif isinstance(node, ast.Call):
            # Extract from function name if it's an attribute (obj.method)
            if isinstance(node.func, ast.Attribute):
                deps.update(self.extract_dependencies(node.func.value))
            # Extract from arguments
            for arg in node.args:
                deps.update(self.extract_dependencies(arg))
            # Extract from keyword arguments
            for keyword in node.keywords:
                deps.update(self.extract_dependencies(keyword.value))
        elif isinstance(node, ast.Attribute):
            # For x.y.z, extract x
            deps.update(self.extract_dependencies(node.value))
        elif isinstance(node, ast.Subscript):
            # For array[index], extract both array and index
            deps.update(self.extract_dependencies(node.value))
            deps.update(self.extract_dependencies(node.slice))
        elif isinstance(node, ast.Index):
            # Python 3.8 and earlier
            deps.update(self.extract_dependencies(node.value))
        elif isinstance(node, ast.List) or isinstance(node, ast.Tuple):
            for elt in node.elts:
                deps.update(self.extract_dependencies(elt))
        elif isinstance(node, ast.Dict):
            for key in node.keys:
                if key:
                    deps.update(self.extract_dependencies(key))
            for value in node.values:
                deps.update(self.extract_dependencies(value))
        elif isinstance(node, ast.Compare):
            deps.update(self.extract_dependencies(node.left))
            for comp in node.comparators:
                deps.update(self.extract_dependencies(comp))
        elif isinstance(node, ast.IfExp):
            # Ternary: a if b else c
            deps.update(self.extract_dependencies(node.test))
            deps.update(self.extract_dependencies(node.body))
            deps.update(self.extract_dependencies(node.orelse))
        elif hasattr(node, '_fields'):
            for field in node._fields:
                child = getattr(node, field, None)
                if isinstance(child, list):
                    for item in child:
                        if isinstance(item, ast.AST):
                            deps.update(self.extract_dependencies(item))
                elif isinstance(child, ast.AST):
                    deps.update(self.extract_dependencies(child))
        
        return deps
    
    def get_line_content(self, line_no: int) -> str:
        """Get content of a specific line"""
        try:
            with open(self.current_file, 'r') as f:
                lines = f.readlines()
                if 0 <= line_no - 1 < len(lines):
                    return lines[line_no - 1].strip()
        except:
            pass
        return ""
    
    def perform_inter_procedural_analysis(self):
        """Perform inter-procedural data flow analysis"""
        if not self.inter_procedural:
            return
            
        # Track which variables receive function return values
        self.return_mappings = {}  # func_call_location -> target_var
        
        # Build call graph and connect parameters
        for func_name, func_info in self.functions.items():
            for called_func, param_map in func_info.calls:
                if called_func in self.functions:
                    called_func_info = self.functions[called_func]
                    
                    # Connect arguments to parameters
                    for param_name, arg_name in param_map.items():
                        # Create unique parameter node name to avoid conflicts
                        param_node_name = f"{called_func}.{param_name}"
                        
                        if param_node_name not in self.nodes:
                            self.nodes[param_node_name] = DataFlowNode(
                                name=param_node_name,
                                node_type='param',
                                location=called_func_info.location,
                                expression=f"parameter {param_name} of {called_func}"
                            )
                        
                        # Add dependency: parameter depends on argument
                        if arg_name in self.nodes:
                            self.nodes[param_node_name].dependencies.add(arg_name)
                            self.nodes[arg_name].dependents.add(param_node_name)
                        
                        # Also track within function
                        if param_name not in self.nodes:
                            self.nodes[param_name] = DataFlowNode(
                                name=param_name,
                                node_type='param',
                                location=called_func_info.location
                            )
                            self.nodes[param_name].dependencies.add(param_node_name)
                            self.nodes[param_node_name].dependents.add(param_name)
                    
                    # Connect return values to any variables that depend on them
                    for return_var in called_func_info.returns:
                        # Create a return node for this function
                        return_node_name = f"{called_func}.return"
                        if return_node_name not in self.nodes:
                            self.nodes[return_node_name] = DataFlowNode(
                                name=return_node_name,
                                node_type='return',
                                location=called_func_info.location,
                                expression=f"return value of {called_func}"
                            )
                        
                        # Return depends on the returned variables
                        if return_var in self.nodes:
                            self.nodes[return_node_name].dependencies.add(return_var)
                            self.nodes[return_var].dependents.add(return_node_name)

class JavaDataFlowAnalyzer(DataFlowAnalyzer):
    """Java-specific data flow analyzer"""
    
    def analyze_file(self, filepath: str) -> bool:
        """Analyze a Java file"""
        if not JAVA_SUPPORT:
            logger.error("Java support not available. Install 'javalang' package.")
            return False
            
        try:
            content = safe_read_file(filepath)
            if not content:
                return False
                
            self.current_file = filepath
            tree = javalang.parse.parse(content)
            self.analyze_node(tree)
            return True
            
        except Exception as e:
            handle_error(e, f"analyzing Java file {filepath}")
            return False
    
    def analyze_node(self, node, parent=None, context=None):
        """Analyze Java AST nodes"""
        if context is None:
            context = []
            
        # Handle different node types
        if isinstance(node, javalang.tree.CompilationUnit):
            for type_decl in node.types:
                self.analyze_node(type_decl, node, context)
                
        elif isinstance(node, javalang.tree.ClassDeclaration):
            class_context = context + [f"class {node.name}"]
            for member in node.body:
                self.analyze_node(member, node, class_context)
                
        elif isinstance(node, javalang.tree.MethodDeclaration):
            method_name = node.name
            method_context = context + [f"method {method_name}"]
            self.current_context = method_context
            
            # Track method info
            params = [param.name for param in node.parameters]
            self.functions[method_name] = FunctionInfo(
                name=method_name,
                params=params,
                returns=[],
                location=VarLocation(
                    file=self.current_file,
                    line=node.position.line if node.position else 0,
                    col=node.position.column if node.position else 0,
                    context=" → ".join(method_context),
                    code=f"{node.return_type} {method_name}({', '.join(params)})"
                ),
                calls=[]
            )
            
            # Analyze method body
            if node.body:
                for statement in node.body:
                    self.analyze_statement(statement, method_context)
                    
        elif isinstance(node, javalang.tree.FieldDeclaration):
            # Handle field declarations
            for declarator in node.declarators:
                field_name = declarator.name
                if declarator.initializer:
                    deps = self.extract_java_dependencies(declarator.initializer)
                    location = VarLocation(
                        file=self.current_file,
                        line=node.position.line if node.position else 0,
                        col=node.position.column if node.position else 0,
                        context=" → ".join(context),
                        code=f"{node.type.name} {field_name}"
                    )
                    self.add_dependency(field_name, deps, location)
    
    def analyze_statement(self, stmt, context):
        """Analyze Java statements"""
        if isinstance(stmt, javalang.tree.LocalVariableDeclaration):
            # Handle variable declarations
            for declarator in stmt.declarators:
                var_name = declarator.name
                if declarator.initializer:
                    deps = self.extract_java_dependencies(declarator.initializer)
                    location = VarLocation(
                        file=self.current_file,
                        line=stmt.position.line if stmt.position else 0,
                        col=stmt.position.column if stmt.position else 0,
                        context=" → ".join(context),
                        code=f"{stmt.type.name} {var_name} = ..."
                    )
                    self.add_dependency(var_name, deps, location)
                    
        elif isinstance(stmt, javalang.tree.Assignment):
            # Handle assignments
            if isinstance(stmt.expressionl, javalang.tree.MemberReference):
                var_name = stmt.expressionl.member
                deps = self.extract_java_dependencies(stmt.value)
                location = VarLocation(
                    file=self.current_file,
                    line=stmt.position.line if stmt.position else 0,
                    col=stmt.position.column if stmt.position else 0,
                    context=" → ".join(context),
                    code=f"{var_name} = ..."
                )
                self.add_dependency(var_name, deps, location)
                
        elif isinstance(stmt, javalang.tree.StatementExpression):
            if hasattr(stmt, 'expression'):
                self.analyze_statement(stmt.expression, context)
                
        elif isinstance(stmt, javalang.tree.BlockStatement):
            for s in stmt.statements:
                self.analyze_statement(s, context)
                
        elif isinstance(stmt, javalang.tree.ReturnStatement):
            if stmt.expression and self.current_context:
                method_name = self.current_context[-1].split()[-1]
                if method_name in self.functions:
                    return_vars = self.extract_java_dependencies(stmt.expression)
                    self.functions[method_name].returns.extend(return_vars)
    
    def extract_java_dependencies(self, node) -> Set[str]:
        """Extract variable dependencies from Java expressions"""
        deps = set()
        
        if isinstance(node, javalang.tree.MemberReference):
            if node.qualifier:
                # Handle chained references like obj.field
                deps.update(self.extract_java_dependencies(node.qualifier))
            else:
                deps.add(node.member)
        elif isinstance(node, javalang.tree.Literal):
            # Literals have no dependencies
            pass
        elif isinstance(node, javalang.tree.BinaryOperation):
            deps.update(self.extract_java_dependencies(node.operandl))
            deps.update(self.extract_java_dependencies(node.operandr))
        elif isinstance(node, javalang.tree.TernaryExpression):
            deps.update(self.extract_java_dependencies(node.condition))
            deps.update(self.extract_java_dependencies(node.if_true))
            deps.update(self.extract_java_dependencies(node.if_false))
        elif isinstance(node, javalang.tree.Assignment):
            deps.update(self.extract_java_dependencies(node.value))
        elif isinstance(node, javalang.tree.MethodInvocation):
            if node.qualifier:
                deps.update(self.extract_java_dependencies(node.qualifier))
            for arg in node.arguments:
                deps.update(self.extract_java_dependencies(arg))
        elif isinstance(node, javalang.tree.ArraySelector):
            deps.update(self.extract_java_dependencies(node.qualifier))
            deps.update(self.extract_java_dependencies(node.index))
        elif isinstance(node, javalang.tree.Cast):
            deps.update(self.extract_java_dependencies(node.expression))
        elif isinstance(node, javalang.tree.This):
            deps.add("this")
        elif isinstance(node, javalang.tree.ClassCreator):
            for arg in node.arguments or []:
                deps.update(self.extract_java_dependencies(arg))
        elif hasattr(node, 'children'):
            for child in node.children:
                if child and not isinstance(child, (str, int, bool)):
                    deps.update(self.extract_java_dependencies(child))
                    
        return deps

def create_graphviz_output(analyzer: DataFlowAnalyzer, var_name: str = None) -> str:
    """Create GraphViz dot format output"""
    lines = ["digraph DataFlow {", "  rankdir=LR;", "  node [shape=box];", ""]
    
    # Add nodes
    for name, node in analyzer.nodes.items():
        if var_name and name != var_name and var_name not in node.dependencies and var_name not in node.dependents:
            continue
            
        label = f"{name}"
        if node.expression:
            label += f"\\n{node.expression}"
        lines.append(f'  "{name}" [label="{label}"];')
    
    # Add edges
    for name, node in analyzer.nodes.items():
        if var_name and name != var_name and var_name not in node.dependencies and var_name not in node.dependents:
            continue
            
        for dep in node.dependencies:
            lines.append(f'  "{dep}" -> "{name}";')
    
    lines.append("}")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(
        description="Track data flow and variable dependencies in code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Track forward dependencies of variable 'x'
  %(prog)s --var x --file calc.py
  
  # Track backward dependencies (what affects 'result')
  %(prog)s --var result --direction backward --file calc.py
  
  # Analyze entire directory
  %(prog)s --var user_input --scope src/ --recursive
  
  # Show inter-procedural flow
  %(prog)s --var x --file math_lib.py --inter-procedural
  
  # Output as graph
  %(prog)s --var result --file module.py --format graph > flow.dot
  
  # Limit depth of analysis
  %(prog)s --var x --max-depth 3 --file calc.py
        """
    )
    
    # Main arguments
    parser.add_argument('--var', '--variable', 
                       help='Variable name to track')
    parser.add_argument('--file', nargs='+',
                       help='File(s) to analyze')
    parser.add_argument('--scope', 
                       help='Directory scope for analysis')
    
    # Analysis options
    parser.add_argument('--direction', choices=['forward', 'backward', 'both'],
                       default='forward',
                       help='Direction of data flow analysis')
    parser.add_argument('--inter-procedural', action='store_true',
                       help='Track flow across function/method calls')
    parser.add_argument('--max-depth', type=int, default=-1,
                       help='Maximum depth for dependency tracking')
    
    # Output options
    parser.add_argument('--format', choices=['text', 'json', 'graph'],
                       default='text',
                       help='Output format')
    parser.add_argument('--show-all', action='store_true',
                       help='Show all variables and dependencies')
    parser.add_argument('--affected-lines', action='store_true',
                       help='Show only affected line numbers')
    
    # File options
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='Analyze files recursively')
    parser.add_argument('--include', '--glob', '-g',
                       help='Include files matching pattern')
    parser.add_argument('--exclude',
                       help='Exclude files matching pattern')
    
    # Other options
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview what would be analyzed')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.var and not args.show_all:
        parser.error("Either --var or --show-all must be specified")
    
    if not args.file and not args.scope:
        parser.error("Either --file or --scope must be specified")
    
    # Collect files to analyze
    files_to_analyze = []
    
    if args.file:
        for f in args.file:
            if os.path.exists(f):
                files_to_analyze.append(f)
            else:
                logger.warning(f"File not found: {f}")
    
    if args.scope:
        from pathlib import Path
        import fnmatch
        
        scope_path = Path(args.scope)
        if scope_path.is_dir():
            pattern = args.include or "*.py"
            
            if args.recursive:
                files = scope_path.rglob(pattern)
            else:
                files = scope_path.glob(pattern)
                
            for f in files:
                if args.exclude and fnmatch.fnmatch(str(f), args.exclude):
                    continue
                files_to_analyze.append(str(f))
    
    if not files_to_analyze:
        logger.error("No files found to analyze")
        return 1
    
    if args.dry_run:
        print(f"Would analyze {len(files_to_analyze)} files:")
        for f in files_to_analyze[:10]:
            print(f"  {f}")
        if len(files_to_analyze) > 10:
            print(f"  ... and {len(files_to_analyze) - 10} more")
        return 0
    
    # Create analyzer
    analyzer = None
    for filepath in files_to_analyze:
        file_type = get_file_type(filepath)
        
        if file_type == 'python':
            if not analyzer:
                analyzer = PythonDataFlowAnalyzer()
                analyzer.inter_procedural = args.inter_procedural
            analyzer.analyze_file(filepath)
        elif file_type == 'java':
            if not analyzer:
                analyzer = JavaDataFlowAnalyzer()
                analyzer.inter_procedural = args.inter_procedural
            analyzer.analyze_file(filepath)
    
    if not analyzer:
        logger.error("No supported files found")
        return 1
    
    # Perform inter-procedural analysis if requested
    analyzer.perform_inter_procedural_analysis()
    
    # Perform analysis
    if args.show_all:
        # Show all variables and their dependencies
        results = {
            "total_variables": len(analyzer.nodes),
            "total_functions": len(analyzer.functions),
            "variables": {}
        }
        
        for var_name in analyzer.nodes:
            if args.direction in ['forward', 'both']:
                results["variables"][var_name] = {
                    "forward": analyzer.track_forward(var_name, args.max_depth)
                }
            if args.direction in ['backward', 'both']:
                if var_name not in results["variables"]:
                    results["variables"][var_name] = {}
                results["variables"][var_name]["backward"] = analyzer.track_backward(var_name, args.max_depth)
    else:
        # Analyze specific variable
        results = {}
        
        if args.direction in ['forward', 'both']:
            results['forward'] = analyzer.track_forward(args.var, args.max_depth)
        
        if args.direction in ['backward', 'both']:
            results['backward'] = analyzer.track_backward(args.var, args.max_depth)
    
    # Output results
    if args.format == 'json':
        print(json.dumps(results, indent=2))
    elif args.format == 'graph':
        print(create_graphviz_output(analyzer, args.var))
    else:
        # Text format
        if args.show_all:
            print(f"Data Flow Analysis Summary")
            print(f"{'=' * 60}")
            print(f"Total variables analyzed: {results['total_variables']}")
            print(f"Total functions analyzed: {results['total_functions']}")
            print()
            
            for var_name, var_results in results['variables'].items():
                print(f"\nVariable: {var_name}")
                print(f"{'-' * 40}")
                
                if 'forward' in var_results:
                    fwd = var_results['forward']
                    if 'error' not in fwd:
                        print(f"  Affects {fwd['total_affected']} variables")
                        for affected in fwd['affects'][:5]:
                            print(f"    → {affected['name']} at {affected['location']}")
                        if len(fwd['affects']) > 5:
                            print(f"    ... and {len(fwd['affects']) - 5} more")
        else:
            # Single variable analysis
            if 'forward' in results:
                fwd = results['forward']
                if 'error' in fwd:
                    print(f"Error: {fwd['error']}")
                else:
                    print(f"Forward Data Flow Analysis for '{args.var}'")
                    print(f"{'=' * 60}")
                    print(f"Total affected variables: {fwd['total_affected']}")
                    print()
                    
                    if args.affected_lines:
                        # Just show line numbers
                        lines = set()
                        for item in fwd['affects']:
                            location = item['location']
                            if ':' in location:
                                line = location.split(':')[1]
                                lines.add(int(line))
                        print("Affected lines:", ', '.join(map(str, sorted(lines))))
                    else:
                        # Show full details
                        print("Data flow chain:")
                        for i, path in enumerate(fwd['flow_paths'][:10]):
                            print(f"  {i+1}. {path}")
                        
                        if len(fwd['flow_paths']) > 10:
                            print(f"  ... and {len(fwd['flow_paths']) - 10} more paths")
                        
                        print("\nAffected variables:")
                        for item in fwd['affects']:
                            print(f"  {item['name']} at {item['location']}")
                            print(f"    Code: {item['code']}")
                            if item.get('expression'):
                                print(f"    Expression: {item['expression']}")
            
            if 'backward' in results:
                back = results['backward']
                if 'error' in back:
                    print(f"Error: {back['error']}")
                else:
                    print(f"\nBackward Data Flow Analysis for '{args.var}'")
                    print(f"{'=' * 60}")
                    print(f"Total dependencies: {back['total_dependencies']}")
                    print()
                    
                    print("Dependency chain:")
                    for i, path in enumerate(back['dependency_paths'][:10]):
                        print(f"  {i+1}. {path}")
                    
                    if len(back['dependency_paths']) > 10:
                        print(f"  ... and {len(back['dependency_paths']) - 10} more paths")
                    
                    print("\nDepends on:")
                    for item in back['depends_on']:
                        print(f"  {item['name']} at {item['location']}")
                        print(f"    Code: {item['code']}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())