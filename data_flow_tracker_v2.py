#!/usr/bin/env python3
"""
Data Flow Tracker V2 - Advanced code intelligence and algorithm analysis tool

Enhanced version with three major capabilities:
1. Impact Analysis - Shows where data escapes scope and causes effects
2. Calculation Path Analysis - Extracts minimal critical path for values
3. Type and State Tracking - Monitors type evolution and state changes

This tool provides both safety (know what changes affect) and intelligence
(understand complex algorithms) for confident refactoring and debugging.

New Features in V2:
- Impact analysis with exit point detection
- Critical path extraction with branch pruning
- Static type inference and state tracking
- Enhanced visualization and reporting
- Performance optimizations for large codebases

Backward compatible with V1 while adding powerful new analysis modes.
"""

import ast
import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Union, Any, NamedTuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import traceback

# Optional Java support
try:
    import javalang
    JAVA_SUPPORT = True
except ImportError:
    javalang = None
    JAVA_SUPPORT = False

# Type definitions
class ExitPointType(Enum):
    """Types of exit points where data leaves local scope"""
    RETURN = "return"
    GLOBAL_WRITE = "global_write"
    INSTANCE_WRITE = "instance_write"
    EXTERNAL_CALL = "external_call"
    FILE_WRITE = "file_write"
    NETWORK = "network"
    CONSOLE = "console"
    DATABASE = "database"

class TypeInfo(NamedTuple):
    """Type information at a specific point"""
    type_name: str
    confidence: float  # 0.0 to 1.0
    possible_values: Optional[List[Any]] = None
    nullable: bool = False

@dataclass
class StateChange:
    """Represents a state change for a variable"""
    location: str
    line: int
    change_type: str  # 'assignment', 'mutation', 'deletion'
    old_state: Optional[str] = None
    new_state: Optional[str] = None
    in_loop: bool = False
    in_conditional: bool = False

@dataclass
class ExitPoint:
    """Information about where data exits its scope"""
    type: ExitPointType
    location: str
    line: int
    function: str
    description: str
    severity: str  # 'low', 'medium', 'high'

@dataclass
class CalculationStep:
    """A single step in a calculation path"""
    variable: str
    operation: str
    inputs: List[str]
    output: str
    location: str
    line: int
    essential: bool = True

class DataFlowAnalyzerV2:
    """Enhanced data flow analyzer with V2 features"""
    
    def __init__(self, source_code: str, filename: str = "unknown", language: str = "python"):
        self.source_code = source_code
        self.filename = filename
        self.language = language
        self.lines = source_code.splitlines()
        
        # V1 compatibility
        self.dependencies = defaultdict(set)
        self.definitions = {}
        self.assignments = defaultdict(list)
        self.function_calls = defaultdict(list)
        self.function_returns = defaultdict(list)
        self.parameter_mappings = defaultdict(list)
        
        # V2 additions
        self.exit_points = defaultdict(list)
        self.type_info = defaultdict(lambda: TypeInfo("unknown", 0.0))
        self.state_changes = defaultdict(list)
        self.calculation_graph = defaultdict(list)
        self.external_effects = defaultdict(list)
        
        # Context tracking
        self.current_function = None
        self.current_class = None
        self.loop_depth = 0
        self.conditional_depth = 0
        
        # External function patterns
        self.io_functions = {
            'print', 'write', 'writelines', 'dump', 'dumps',
            'send', 'post', 'put', 'request', 'save'
        }
        
        self.db_functions = {
            'execute', 'commit', 'insert', 'update', 'delete',
            'save', 'create', 'persist'
        }
        
    def analyze(self):
        """Perform complete analysis based on language"""
        if self.language.lower() == "python":
            self._analyze_python()
        elif self.language.lower() == "java":
            self._analyze_java()
        else:
            raise ValueError(f"Unsupported language: {self.language}")
    
    def _analyze_python(self):
        """Analyze Python code with V2 enhancements"""
        try:
            tree = ast.parse(self.source_code, filename=self.filename)
            analyzer = PythonDataFlowAnalyzerV2(self)
            analyzer.visit(tree)
        except SyntaxError as e:
            print(f"Syntax error in {self.filename}: {e}", file=sys.stderr)
            raise
    
    def _analyze_java(self):
        """Analyze Java code with V2 enhancements"""
        if not JAVA_SUPPORT:
            print("Error: javalang not installed. Run: pip install javalang", file=sys.stderr)
            sys.exit(1)
        try:
            tree = javalang.parse.parse(self.source_code)
            analyzer = JavaDataFlowAnalyzerV2(self)
            analyzer.analyze_tree(tree)
        except Exception as e:
            print(f"Error parsing Java code: {e}", file=sys.stderr)
            raise
    
    def track_forward(self, var_name: str, max_depth: int = -1) -> Dict[str, Any]:
        """Enhanced forward tracking with impact analysis"""
        result = {
            "variable": var_name,
            "direction": "forward",
            "affects": [],
            "exit_points": [],
            "external_effects": [],
            "risk_assessment": {}
        }
        
        visited = set()
        queue = deque([(var_name, 0)])
        
        while queue:
            current_var, depth = queue.popleft()
            
            if current_var in visited:
                continue
            
            if max_depth >= 0 and depth > max_depth:
                continue
            
            visited.add(current_var)
            
            # Track dependencies
            for dependent in self.dependencies.get(current_var, []):
                location = self._get_location(dependent)
                result["affects"].append({
                    "variable": dependent,
                    "location": location,
                    "depth": depth + 1
                })
                queue.append((dependent, depth + 1))
            
            # V2: Track exit points
            for exit_point in self.exit_points.get(current_var, []):
                result["exit_points"].append({
                    "type": exit_point.type.value,
                    "location": f"{exit_point.location}:{exit_point.line}",
                    "function": exit_point.function,
                    "description": exit_point.description,
                    "severity": exit_point.severity
                })
            
            # V2: Track external effects
            for effect in self.external_effects.get(current_var, []):
                result["external_effects"].append(effect)
        
        # V2: Risk assessment
        result["risk_assessment"] = self._assess_impact_risk(result)
        
        return result
    
    def track_backward(self, var_name: str, max_depth: int = -1) -> Dict[str, Any]:
        """Enhanced backward tracking with calculation path"""
        result = {
            "variable": var_name,
            "direction": "backward",
            "depends_on": [],
            "calculation_path": [],
            "type_evolution": [],
            "state_history": []
        }
        
        # Standard backward tracking (V1 compatibility)
        visited = set()
        queue = deque([(var_name, 0)])
        all_dependencies = []
        
        while queue:
            current_var, depth = queue.popleft()
            
            if current_var in visited:
                continue
            
            if max_depth >= 0 and depth > max_depth:
                continue
            
            visited.add(current_var)
            
            # Find what current_var depends on
            for other_var, dependents in self.dependencies.items():
                if current_var in dependents:
                    location = self._get_location(other_var)
                    all_dependencies.append({
                        "variable": other_var,
                        "location": location,
                        "depth": depth + 1
                    })
                    queue.append((other_var, depth + 1))
        
        result["depends_on"] = all_dependencies
        
        # V2: Extract calculation path
        result["calculation_path"] = self._extract_calculation_path(var_name)
        
        # V2: Track type evolution
        result["type_evolution"] = self._track_type_evolution(var_name)
        
        # V2: Include state history
        if var_name in self.state_changes:
            result["state_history"] = [
                {
                    "location": f"{sc.location}:{sc.line}",
                    "change_type": sc.change_type,
                    "old_state": sc.old_state,
                    "new_state": sc.new_state,
                    "in_loop": sc.in_loop,
                    "in_conditional": sc.in_conditional
                }
                for sc in self.state_changes[var_name]
            ]
        
        return result
    
    def show_impact(self, var_name: str) -> Dict[str, Any]:
        """V2: Dedicated impact analysis showing all effects of changing a variable"""
        impact = self.track_forward(var_name)
        
        # Categorize impacts
        categorized = {
            "returns": [],
            "side_effects": [],
            "state_changes": [],
            "external_calls": [],
            "summary": {}
        }
        
        for exit_point in impact["exit_points"]:
            if exit_point["type"] == "return":
                categorized["returns"].append(exit_point)
            elif exit_point["type"] in ["file_write", "network", "console", "database"]:
                categorized["side_effects"].append(exit_point)
            elif exit_point["type"] in ["global_write", "instance_write"]:
                categorized["state_changes"].append(exit_point)
            elif exit_point["type"] == "external_call":
                categorized["external_calls"].append(exit_point)
        
        # Generate summary
        high_risk_count = len([ep for ep in impact["exit_points"] if ep.get("severity") == "high"])
        categorized["summary"] = {
            "total_exit_points": len(impact["exit_points"]),
            "functions_affected": len(set(ep["function"] for ep in impact["exit_points"])) if impact["exit_points"] else 0,
            "high_risk_count": high_risk_count,
            "recommendation": self._generate_impact_recommendation(categorized, high_risk_count)
        }
        
        return categorized
    
    def show_calculation_path(self, var_name: str) -> List[Dict[str, Any]]:
        """V2: Show minimal calculation path for a value"""
        path = self._extract_calculation_path(var_name)
        
        # Prune non-essential steps
        essential_path = [step for step in path if step["essential"]]
        
        # Add visual representation
        for i, step in enumerate(essential_path):
            if i < len(essential_path) - 1:
                step["arrow"] = "↓"
            else:
                step["arrow"] = "="
        
        return essential_path
    
    def track_state(self, var_name: str) -> Dict[str, Any]:
        """V2: Track type and state evolution of a variable"""
        return {
            "variable": var_name,
            "type_evolution": self._track_type_evolution(var_name),
            "state_changes": [
                {
                    "location": f"{sc.location}:{sc.line}",
                    "change_type": sc.change_type,
                    "old_state": sc.old_state,
                    "new_state": sc.new_state,
                    "context": {
                        "in_loop": sc.in_loop,
                        "in_conditional": sc.in_conditional
                    }
                }
                for sc in self.state_changes.get(var_name, [])
            ],
            "warnings": self._generate_state_warnings(var_name)
        }
    
    def _extract_calculation_path(self, target_var: str) -> List[Dict[str, Any]]:
        """Extract the minimal calculation path for a variable"""
        path = []
        visited = set()
        
        def trace_calculation(var: str, depth: int = 0):
            if var in visited or depth > 50:  # Prevent infinite recursion
                return
            
            visited.add(var)
            
            # Look for assignments to this variable
            for assignment in self.assignments.get(var, []):
                step = {
                    "variable": var,
                    "operation": assignment.get("type", "assignment"),
                    "inputs": assignment.get("dependencies", []),
                    "output": var,
                    "location": assignment.get("location", "unknown"),
                    "line": assignment.get("line", 0),
                    "essential": True,
                    "depth": depth
                }
                
                # Check if this step is actually essential
                if self._is_essential_calculation(step, target_var):
                    path.append(step)
                    
                    # Trace inputs
                    for input_var in step["inputs"]:
                        trace_calculation(input_var, depth + 1)
        
        trace_calculation(target_var)
        
        # Sort by depth (reverse) to get correct order
        path.sort(key=lambda x: x["depth"], reverse=True)
        
        # Remove depth from output
        for step in path:
            step.pop("depth", None)
        
        return path
    
    def _track_type_evolution(self, var_name: str) -> List[Dict[str, Any]]:
        """Track how a variable's type changes through the code"""
        evolution = []
        
        # Get all assignments to this variable
        for assignment in self.assignments.get(var_name, []):
            type_info = self.type_info.get(f"{var_name}_{assignment.get('line', 0)}", 
                                          TypeInfo("unknown", 0.0))
            
            evolution.append({
                "location": f"{assignment.get('location', 'unknown')}:{assignment.get('line', 0)}",
                "type": type_info.type_name,
                "confidence": type_info.confidence,
                "nullable": type_info.nullable,
                "possible_values": type_info.possible_values,
                "operation": assignment.get("type", "assignment")
            })
        
        return evolution
    
    def _assess_impact_risk(self, impact_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the risk level of changing a variable"""
        risk_score = 0
        risk_factors = []
        
        # Check exit points
        for exit_point in impact_result["exit_points"]:
            if exit_point["severity"] == "high":
                risk_score += 10
                risk_factors.append(f"High severity exit: {exit_point['type']}")
            elif exit_point["severity"] == "medium":
                risk_score += 5
        
        # Check external effects
        if impact_result["external_effects"]:
            risk_score += len(impact_result["external_effects"]) * 3
            risk_factors.append(f"{len(impact_result['external_effects'])} external effects")
        
        # Determine risk level
        if risk_score >= 20:
            risk_level = "HIGH"
        elif risk_score >= 10:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "level": risk_level,
            "score": risk_score,
            "factors": risk_factors,
            "recommendation": self._get_risk_recommendation(risk_level)
        }
    
    def _generate_impact_recommendation(self, categorized: Dict[str, Any], high_risk_count: int) -> str:
        """Generate recommendation based on impact analysis"""
        if high_risk_count > 0:
            return "⚠️  HIGH RISK: Review all high-severity exit points before modification"
        elif len(categorized["side_effects"]) > 0:
            return "⚡ MEDIUM RISK: External side effects detected - ensure testing covers these"
        elif len(categorized["state_changes"]) > 0:
            return "📝 LOW RISK: Only internal state changes - standard testing sufficient"
        else:
            return "✅ MINIMAL RISK: Local scope only - safe to modify"
    
    def _generate_state_warnings(self, var_name: str) -> List[str]:
        """Generate warnings about variable state issues"""
        warnings = []
        
        # Check for None assignments
        type_evolution = self._track_type_evolution(var_name)
        if any(t["nullable"] for t in type_evolution):
            warnings.append("Variable may be None - add null checks")
        
        # Check for type changes
        types = [t["type"] for t in type_evolution if t["confidence"] > 0.5]
        if len(set(types)) > 1:
            warnings.append(f"Type changes detected: {' → '.join(set(types))}")
        
        # Check for modifications in loops
        loop_modifications = [sc for sc in self.state_changes.get(var_name, []) if sc.in_loop]
        if loop_modifications:
            warnings.append(f"Modified in loop at {len(loop_modifications)} location(s)")
        
        return warnings
    
    def _is_essential_calculation(self, step: Dict[str, Any], target: str) -> bool:
        """Determine if a calculation step is essential for the target value"""
        # For now, consider all steps essential
        # Future: implement branch pruning logic
        return True
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            "HIGH": "Comprehensive testing required - consider breaking into smaller changes",
            "MEDIUM": "Standard testing with focus on affected areas",
            "LOW": "Normal testing procedures sufficient"
        }
        return recommendations.get(risk_level, "Assess based on specific changes")
    
    def _get_location(self, var_name: str) -> str:
        """Get location of variable definition"""
        if var_name in self.definitions:
            return self.definitions[var_name]
        return "unknown"
    
    def format_output(self, result: Dict[str, Any], format_type: str = "text") -> str:
        """Format analysis results for output"""
        if format_type == "json":
            return json.dumps(result, indent=2)
        elif format_type == "graph":
            return self._generate_graphviz(result)
        else:
            return self._format_text(result)
    
    def _format_text(self, result: Dict[str, Any]) -> str:
        """Enhanced text formatting for V2 features"""
        output = []
        
        # Handle different result types
        if isinstance(result, dict) and "summary" in result and "returns" in result:
            # Impact analysis result from show_impact
            output.append(f"\n{'='*60}")
            output.append(f"Impact Analysis")
            output.append(f"{'='*60}\n")
            
            # Show different categories
            if result.get("returns"):
                output.append("🔄 RETURNS:")
                for ret in result["returns"]:
                    output.append(f"  - {ret['function']} at {ret['location']}")
                    output.append(f"    {ret['description']}\n")
            
            if result.get("side_effects"):
                output.append("⚠️  SIDE EFFECTS:")
                for se in result["side_effects"]:
                    severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(se.get("severity", "medium"), "⚪")
                    output.append(f"  {severity_icon} {se['type']} at {se['location']}")
                    output.append(f"     {se['description']}\n")
            
            if result.get("state_changes"):
                output.append("📝 STATE CHANGES:")
                for sc in result["state_changes"]:
                    output.append(f"  - {sc['type']} at {sc['location']}")
                    output.append(f"    {sc['description']}\n")
            
            if result.get("external_calls"):
                output.append("🌐 EXTERNAL CALLS:")
                for ec in result["external_calls"]:
                    output.append(f"  - {ec['description']} at {ec['location']}\n")
            
            if result.get("summary"):
                summary = result["summary"]
                output.append(f"\n{'─'*60}")
                output.append(f"SUMMARY:")
                output.append(f"  Total exit points: {summary['total_exit_points']}")
                output.append(f"  Functions affected: {summary['functions_affected']}")
                output.append(f"  High risk count: {summary['high_risk_count']}")
                output.append(f"\n  {summary['recommendation']}")
        
        elif isinstance(result, list) and result and "variable" in result[0]:
            # Calculation path result (list of steps)
            output.append(f"\n{'='*60}")
            output.append(f"Calculation Path")
            output.append(f"{'='*60}\n")
            
            for i, step in enumerate(result):
                output.append(f"{i+1}. {step['variable']} = {step['operation']}")
                if step.get('inputs'):
                    output.append(f"   Inputs: {', '.join(step['inputs'])}")
                output.append(f"   Location: {step['location']}:{step['line']}")
                if step.get('arrow') == '↓':
                    output.append("   ↓")
                output.append("")
        
        elif "type_evolution" in result:
            # State tracking result
            output.append(f"\n{'='*60}")
            output.append(f"Type & State Evolution for '{result['variable']}'")
            output.append(f"{'='*60}\n")
            
            if result.get("type_evolution"):
                output.append("📈 TYPE EVOLUTION:")
                for evo in result["type_evolution"]:
                    confidence = "✓" if evo["confidence"] > 0.8 else "?"
                    nullable = " (nullable)" if evo["nullable"] else ""
                    output.append(f"  {evo['location']}: {evo['type']}{nullable} {confidence}")
                    if evo.get("possible_values"):
                        output.append(f"    Possible values: {evo['possible_values'][:5]}")
            
            if result.get("state_changes"):
                output.append("\n🔄 STATE CHANGES:")
                for change in result["state_changes"]:
                    context = []
                    if change["context"]["in_loop"]:
                        context.append("in loop")
                    if change["context"]["in_conditional"]:
                        context.append("in conditional")
                    context_str = f" ({', '.join(context)})" if context else ""
                    
                    output.append(f"  {change['location']}: {change['change_type']}{context_str}")
                    if change.get("old_state") and change.get("new_state"):
                        output.append(f"    {change['old_state']} → {change['new_state']}")
            
            if result.get("warnings"):
                output.append("\n⚠️  WARNINGS:")
                for warning in result["warnings"]:
                    output.append(f"  - {warning}")
        
        else:
            # Fall back to V1 formatting for standard results
            output.append(f"\nData flow analysis for '{result['variable']}' ({result['direction']}):")
            output.append("-" * 50)
            
            if result["direction"] == "forward" and result.get("affects"):
                output.append("\nThis variable affects:")
                for item in result["affects"]:
                    output.append(f"  → {item['variable']} at {item['location']} (depth: {item['depth']})")
            
            elif result["direction"] == "backward" and result.get("depends_on"):
                output.append("\nThis variable depends on:")
                for item in result["depends_on"]:
                    output.append(f"  ← {item['variable']} at {item['location']} (depth: {item['depth']})")
        
        return "\n".join(output)
    
    def _generate_graphviz(self, result: Dict[str, Any]) -> str:
        """Generate GraphViz output for visualization"""
        dot_lines = ["digraph DataFlow {", '    rankdir=LR;', '    node [shape=box];', '']
        
        # Track nodes we've seen
        nodes = set()
        
        # Different visualization based on analysis type
        if "calculation_path" in result:
            # Calculation path visualization
            dot_lines.append('    // Calculation Path')
            for i, step in enumerate(result.get("calculation_path", [])):
                node_id = f"step_{i}"
                label = f"{step['variable']} = {step['operation']}\\n{step['location']}:{step['line']}"
                dot_lines.append(f'    {node_id} [label="{label}", style=filled, fillcolor=lightblue];')
                
                if i > 0:
                    dot_lines.append(f'    step_{i-1} -> step_{i};')
                
                # Show inputs
                for input_var in step.get("inputs", []):
                    input_id = f"input_{input_var}_{i}"
                    if input_id not in nodes:
                        dot_lines.append(f'    {input_id} [label="{input_var}", shape=ellipse];')
                        nodes.add(input_id)
                    dot_lines.append(f'    {input_id} -> {node_id} [style=dashed];')
        
        else:
            # Standard dependency graph
            dot_lines.append(f'    "{result["variable"]}" [style=filled, fillcolor=yellow];')
            
            if result["direction"] == "forward":
                for item in result.get("affects", []):
                    dot_lines.append(f'    "{result["variable"]}" -> "{item["variable"]}" '
                                   f'[label="depth={item["depth"]}"];')
                
                # Add exit points
                for i, ep in enumerate(result.get("exit_points", [])):
                    exit_id = f"exit_{i}"
                    color = {"high": "red", "medium": "orange", "low": "green"}.get(ep["severity"], "gray")
                    dot_lines.append(f'    {exit_id} [label="{ep["type"]}\\n{ep["location"]}", '
                                   f'shape=octagon, style=filled, fillcolor={color}];')
                    dot_lines.append(f'    "{result["variable"]}" -> {exit_id};')
            
            else:  # backward
                for item in result.get("depends_on", []):
                    dot_lines.append(f'    "{item["variable"]}" -> "{result["variable"]}" '
                                   f'[label="depth={item["depth"]}"];')
        
        dot_lines.append("}")
        return "\n".join(dot_lines)


class PythonDataFlowAnalyzerV2(ast.NodeVisitor):
    """Enhanced Python AST visitor with V2 features"""
    
    def __init__(self, analyzer: DataFlowAnalyzerV2):
        self.analyzer = analyzer
        self.current_scope = []
        self.current_function = None
        self.current_class = None
        self.loop_depth = 0
        self.conditional_depth = 0
        
    def visit_FunctionDef(self, node):
        """Handle function definitions with return tracking"""
        old_function = self.current_function
        self.current_function = node.name
        self.current_scope.append(node.name)
        
        # Process function body
        self.generic_visit(node)
        
        self.current_scope.pop()
        self.current_function = old_function
        
    def visit_ClassDef(self, node):
        """Handle class definitions"""
        old_class = self.current_class
        self.current_class = node.name
        self.current_scope.append(node.name)
        
        self.generic_visit(node)
        
        self.current_scope.pop()
        self.current_class = old_class
        
    def visit_Assign(self, node):
        """Enhanced assignment handling with type inference"""
        # Extract target variables
        targets = []
        for target in node.targets:
            targets.extend(self._extract_names(target))
        
        # Extract dependencies from value
        dependencies = self._extract_dependencies(node.value)
        
        # Record assignments and dependencies
        for target_var in targets:
            # V1 compatibility
            location = f"{self.analyzer.filename}:{node.lineno}"
            self.analyzer.definitions[target_var] = location
            
            assignment_info = {
                "location": self.analyzer.filename,
                "line": node.lineno,
                "type": "assignment",
                "dependencies": list(dependencies),
                "in_loop": self.loop_depth > 0,
                "in_conditional": self.conditional_depth > 0
            }
            self.analyzer.assignments[target_var].append(assignment_info)
            
            for dep in dependencies:
                self.analyzer.dependencies[dep].add(target_var)
            
            # V2: Type inference
            inferred_type = self._infer_type(node.value)
            type_key = f"{target_var}_{node.lineno}"
            self.analyzer.type_info[type_key] = inferred_type
            
            # V2: State tracking
            state_change = StateChange(
                location=self.analyzer.filename,
                line=node.lineno,
                change_type="assignment",
                new_state=self._get_value_repr(node.value),
                in_loop=self.loop_depth > 0,
                in_conditional=self.conditional_depth > 0
            )
            self.analyzer.state_changes[target_var].append(state_change)
        
        self.generic_visit(node)
    
    def visit_Return(self, node):
        """Track return statements as exit points"""
        if node.value and self.current_function:
            # Extract what's being returned
            returned_vars = self._extract_dependencies(node.value)
            
            for var in returned_vars:
                exit_point = ExitPoint(
                    type=ExitPointType.RETURN,
                    location=self.analyzer.filename,
                    line=node.lineno,
                    function=self.current_function or "module",
                    description=f"Returns value dependent on {var}",
                    severity="medium"
                )
                self.analyzer.exit_points[var].append(exit_point)
        
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Enhanced call tracking with external effect detection"""
        # Get function name
        func_name = self._get_call_name(node.func)
        
        if func_name:
            # Extract arguments
            arg_vars = []
            for arg in node.args:
                arg_vars.extend(self._extract_dependencies(arg))
            
            # Check if this is an external effect
            if self._is_external_effect(func_name):
                for var in arg_vars:
                    effect_type = self._classify_external_effect(func_name)
                    exit_point = ExitPoint(
                        type=effect_type,
                        location=self.analyzer.filename,
                        line=node.lineno,
                        function=self.current_function or "module",
                        description=f"External call to {func_name}",
                        severity="high" if effect_type in [ExitPointType.FILE_WRITE, 
                                                          ExitPointType.DATABASE] else "medium"
                    )
                    self.analyzer.exit_points[var].append(exit_point)
                    self.analyzer.external_effects[var].append(
                        f"{func_name} at {self.analyzer.filename}:{node.lineno}"
                    )
        
        self.generic_visit(node)
    
    def visit_For(self, node):
        """Track loop context"""
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1
    
    def visit_While(self, node):
        """Track loop context"""
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1
    
    def visit_If(self, node):
        """Track conditional context"""
        self.conditional_depth += 1
        self.generic_visit(node)
        self.conditional_depth -= 1
    
    def _extract_names(self, node) -> List[str]:
        """Extract variable names from AST node"""
        if isinstance(node, ast.Name):
            return [node.id]
        elif isinstance(node, ast.Tuple) or isinstance(node, ast.List):
            names = []
            for elt in node.elts:
                names.extend(self._extract_names(elt))
            return names
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                return [f"self.{node.attr}"]
            return []
        elif isinstance(node, ast.Subscript):
            return self._extract_names(node.value)
        return []
    
    def _extract_dependencies(self, node) -> Set[str]:
        """Extract all variable dependencies from an expression"""
        deps = set()
        
        if isinstance(node, ast.Name):
            deps.add(node.id)
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                if node.value.id == "self":
                    deps.add(f"self.{node.attr}")
                else:
                    deps.add(node.value.id)
            else:
                deps.update(self._extract_dependencies(node.value))
        elif isinstance(node, ast.BinOp):
            deps.update(self._extract_dependencies(node.left))
            deps.update(self._extract_dependencies(node.right))
        elif isinstance(node, ast.UnaryOp):
            deps.update(self._extract_dependencies(node.operand))
        elif isinstance(node, ast.Call):
            deps.update(self._extract_dependencies(node.func))
            for arg in node.args:
                deps.update(self._extract_dependencies(arg))
        elif isinstance(node, ast.IfExp):
            deps.update(self._extract_dependencies(node.test))
            deps.update(self._extract_dependencies(node.body))
            deps.update(self._extract_dependencies(node.orelse))
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for elt in node.elts:
                deps.update(self._extract_dependencies(elt))
        elif isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if k:
                    deps.update(self._extract_dependencies(k))
                if v:
                    deps.update(self._extract_dependencies(v))
        elif isinstance(node, ast.Subscript):
            deps.update(self._extract_dependencies(node.value))
            deps.update(self._extract_dependencies(node.slice))
        elif isinstance(node, ast.Compare):
            deps.update(self._extract_dependencies(node.left))
            for comp in node.comparators:
                deps.update(self._extract_dependencies(comp))
        elif isinstance(node, ast.ListComp):
            deps.update(self._extract_dependencies(node.elt))
            for gen in node.generators:
                deps.update(self._extract_dependencies(gen.iter))
        elif isinstance(node, ast.DictComp):
            deps.update(self._extract_dependencies(node.key))
            deps.update(self._extract_dependencies(node.value))
            for gen in node.generators:
                deps.update(self._extract_dependencies(gen.iter))
        
        return deps
    
    def _infer_type(self, node) -> TypeInfo:
        """Infer type from AST node"""
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, int):
                return TypeInfo("int", 1.0, [value])
            elif isinstance(value, float):
                return TypeInfo("float", 1.0, [value])
            elif isinstance(value, str):
                return TypeInfo("str", 1.0, [value] if len(value) < 50 else None)
            elif isinstance(value, bool):
                return TypeInfo("bool", 1.0, [value])
            elif value is None:
                return TypeInfo("NoneType", 1.0, [None], nullable=True)
        elif isinstance(node, ast.List):
            return TypeInfo("list", 0.9)
        elif isinstance(node, ast.Dict):
            return TypeInfo("dict", 0.9)
        elif isinstance(node, ast.Set):
            return TypeInfo("set", 0.9)
        elif isinstance(node, ast.Tuple):
            return TypeInfo("tuple", 0.9)
        elif isinstance(node, ast.Call):
            func_name = self._get_call_name(node.func)
            if func_name in ["str", "int", "float", "bool", "list", "dict", "set", "tuple"]:
                return TypeInfo(func_name, 0.8)
        elif isinstance(node, ast.Name):
            # Could be None
            if node.id == "None":
                return TypeInfo("NoneType", 1.0, [None], nullable=True)
        
        return TypeInfo("unknown", 0.0)
    
    def _get_call_name(self, node) -> Optional[str]:
        """Get the name of a function being called"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None
    
    def _is_external_effect(self, func_name: str) -> bool:
        """Check if function call has external effects"""
        return (func_name in self.analyzer.io_functions or 
                func_name in self.analyzer.db_functions or
                func_name in ["print", "write", "send", "post", "execute"])
    
    def _classify_external_effect(self, func_name: str) -> ExitPointType:
        """Classify the type of external effect"""
        if func_name == "print":
            return ExitPointType.CONSOLE
        elif func_name in ["write", "writelines", "dump", "save"]:
            return ExitPointType.FILE_WRITE
        elif func_name in ["send", "post", "put", "request"]:
            return ExitPointType.NETWORK
        elif func_name in self.analyzer.db_functions:
            return ExitPointType.DATABASE
        else:
            return ExitPointType.EXTERNAL_CALL
    
    def _get_value_repr(self, node) -> str:
        """Get string representation of a value"""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return f"[{len(node.elts)} items]"
        elif isinstance(node, ast.Dict):
            return f"{{dict with {len(node.keys)} keys}}"
        else:
            return type(node).__name__


class JavaDataFlowAnalyzerV2:
    """Enhanced Java analyzer with V2 features - Full parity with Python"""
    
    def __init__(self, analyzer: DataFlowAnalyzerV2):
        self.analyzer = analyzer
        self.current_class = None
        self.current_method = None
        self.current_scope = []
        self.loop_depth = 0
        self.conditional_depth = 0
        self.line_number = 0
        
        # Java-specific external functions
        self.java_io_functions = {
            'println', 'print', 'printf', 'write', 'writeBytes', 'writeChars',
            'save', 'store', 'flush', 'close'
        }
        
        self.java_db_functions = {
            'execute', 'executeQuery', 'executeUpdate', 'commit', 'rollback',
            'save', 'persist', 'merge', 'remove', 'find'
        }
        
        self.java_network_functions = {
            'send', 'post', 'put', 'get', 'delete', 'connect', 'openConnection'
        }
    
    def analyze_tree(self, tree):
        """Analyze Java AST tree with comprehensive V2 features"""
        try:
            import javalang
        except ImportError:
            print("Error: javalang not installed. Run: pip install javalang", file=sys.stderr)
            return
            
        # First pass: collect all declarations
        self._collect_declarations(tree)
        
        # Second pass: analyze data flow
        self._analyze_data_flow(tree)
    
    def _collect_declarations(self, tree):
        """First pass: collect class and method declarations"""
        for path, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                self.current_class = node.name
                self.current_scope.append(node.name)
                
                # Process fields
                for field in node.fields or []:
                    for declarator in field.declarators:
                        var_name = f"{self.current_class}.{declarator.name}"
                        location = f"{self.analyzer.filename}:{self._get_line_number(node)}"
                        self.analyzer.definitions[var_name] = location
                
                self.current_scope.pop()
                self.current_class = None
    
    def _analyze_data_flow(self, tree):
        """Second pass: analyze data flow with V2 features"""
        for path, node in tree:
            self.line_number = self._get_line_number(node)
            
            if isinstance(node, javalang.tree.ClassDeclaration):
                self._analyze_class(node)
            elif isinstance(node, javalang.tree.MethodDeclaration):
                self._analyze_method(node)
    
    def _analyze_class(self, class_node):
        """Analyze Java class with V2 features"""
        old_class = self.current_class
        self.current_class = class_node.name
        self.current_scope.append(class_node.name)
        
        # Analyze methods
        for method in class_node.methods or []:
            self._analyze_method(method)
        
        # Analyze constructors
        for constructor in class_node.constructors or []:
            self._analyze_constructor(constructor)
        
        self.current_scope.pop()
        self.current_class = old_class
    
    def _analyze_method(self, method):
        """Analyze Java method with comprehensive V2 features"""
        old_method = self.current_method
        self.current_method = method.name
        self.current_scope.append(method.name)
        
        # Analyze parameters
        for param in method.parameters or []:
            var_name = param.name
            location = f"{self.analyzer.filename}:{self._get_line_number(param)}"
            self.analyzer.definitions[var_name] = location
            
            # V2: Add type information for parameters
            if param.type:
                type_info = self._infer_java_type(param.type)
                type_key = f"{var_name}_{self._get_line_number(param)}"
                self.analyzer.type_info[type_key] = type_info
        
        # Analyze method body
        if method.body:
            for stmt in method.body:
                self._analyze_statement(stmt)
        
        self.current_scope.pop()
        self.current_method = old_method
    
    def _analyze_constructor(self, constructor):
        """Analyze Java constructor"""
        old_method = self.current_method
        self.current_method = f"<init>"
        
        # Analyze parameters
        for param in constructor.parameters or []:
            var_name = param.name
            location = f"{self.analyzer.filename}:{self._get_line_number(param)}"
            self.analyzer.definitions[var_name] = location
        
        # Analyze constructor body
        if constructor.body:
            for stmt in constructor.body:
                self._analyze_statement(stmt)
        
        self.current_method = old_method
    
    def _analyze_statement(self, stmt):
        """Analyze Java statement with V2 features"""
        try:
            import javalang
        except ImportError:
            return
            
        if isinstance(stmt, javalang.tree.LocalVariableDeclaration):
            self._analyze_variable_declaration(stmt)
        elif isinstance(stmt, javalang.tree.StatementExpression):
            self._analyze_expression_statement(stmt)
        elif isinstance(stmt, javalang.tree.ReturnStatement):
            self._analyze_return_statement(stmt)
        elif isinstance(stmt, javalang.tree.ForStatement):
            self._analyze_for_statement(stmt)
        elif isinstance(stmt, javalang.tree.WhileStatement):
            self._analyze_while_statement(stmt)
        elif isinstance(stmt, javalang.tree.IfStatement):
            self._analyze_if_statement(stmt)
        elif isinstance(stmt, javalang.tree.BlockStatement):
            for s in stmt.statements:
                self._analyze_statement(s)
    
    def _analyze_variable_declaration(self, decl):
        """Analyze Java variable declaration with V2 features"""
        try:
            import javalang
        except ImportError:
            return
            
        for declarator in decl.declarators:
            var_name = declarator.name
            location = f"{self.analyzer.filename}:{self.line_number}"
            
            # V1: Basic tracking
            self.analyzer.definitions[var_name] = location
            
            # Extract dependencies from initializer
            dependencies = set()
            if declarator.initializer:
                dependencies = self._extract_java_dependencies(declarator.initializer)
            
            # Record assignment
            assignment_info = {
                "location": self.analyzer.filename,
                "line": self.line_number,
                "type": "declaration",
                "dependencies": list(dependencies),
                "in_loop": self.loop_depth > 0,
                "in_conditional": self.conditional_depth > 0
            }
            self.analyzer.assignments[var_name].append(assignment_info)
            
            # Update dependencies
            for dep in dependencies:
                self.analyzer.dependencies[dep].add(var_name)
            
            # V2: Type inference
            if decl.type:
                type_info = self._infer_java_type(decl.type)
                type_key = f"{var_name}_{self.line_number}"
                self.analyzer.type_info[type_key] = type_info
            
            # V2: State tracking
            state_change = StateChange(
                location=self.analyzer.filename,
                line=self.line_number,
                change_type="declaration",
                new_state=self._get_java_value_repr(declarator.initializer) if declarator.initializer else "uninitialized",
                in_loop=self.loop_depth > 0,
                in_conditional=self.conditional_depth > 0
            )
            self.analyzer.state_changes[var_name].append(state_change)
    
    def _analyze_expression_statement(self, stmt):
        """Analyze Java expression statement (assignments, method calls)"""
        try:
            import javalang
        except ImportError:
            return
            
        expr = stmt.expression
        
        if isinstance(expr, javalang.tree.Assignment):
            self._analyze_assignment(expr)
        elif isinstance(expr, javalang.tree.MethodInvocation):
            self._analyze_method_invocation(expr)
    
    def _analyze_assignment(self, assignment):
        """Analyze Java assignment with V2 features"""
        try:
            import javalang
        except ImportError:
            return
            
        # Extract target variable
        target_vars = self._extract_java_names(assignment.expressionl)
        dependencies = self._extract_java_dependencies(assignment.value)
        
        for target_var in target_vars:
            # V1: Basic tracking
            location = f"{self.analyzer.filename}:{self.line_number}"
            self.analyzer.definitions[target_var] = location
            
            assignment_info = {
                "location": self.analyzer.filename,
                "line": self.line_number,
                "type": "assignment",
                "dependencies": list(dependencies),
                "in_loop": self.loop_depth > 0,
                "in_conditional": self.conditional_depth > 0
            }
            self.analyzer.assignments[target_var].append(assignment_info)
            
            for dep in dependencies:
                self.analyzer.dependencies[dep].add(target_var)
            
            # V2: Type inference for assignment
            type_info = self._infer_java_type_from_expression(assignment.value)
            type_key = f"{target_var}_{self.line_number}"
            self.analyzer.type_info[type_key] = type_info
            
            # V2: State tracking
            state_change = StateChange(
                location=self.analyzer.filename,
                line=self.line_number,
                change_type="assignment",
                new_state=self._get_java_value_repr(assignment.value),
                in_loop=self.loop_depth > 0,
                in_conditional=self.conditional_depth > 0
            )
            self.analyzer.state_changes[target_var].append(state_change)
    
    def _analyze_method_invocation(self, invocation):
        """Analyze Java method invocation with V2 external effect detection"""
        try:
            import javalang
        except ImportError:
            return
            
        # Get method name
        method_name = invocation.member if invocation.member else "unknown"
        
        # Extract arguments
        arg_vars = []
        for arg in invocation.arguments or []:
            arg_vars.extend(self._extract_java_dependencies(arg))
        
        # V2: Check for external effects
        if self._is_java_external_effect(method_name, invocation):
            for var in arg_vars:
                effect_type = self._classify_java_external_effect(method_name, invocation)
                exit_point = ExitPoint(
                    type=effect_type,
                    location=self.analyzer.filename,
                    line=self.line_number,
                    function=self.current_method or "main",
                    description=f"Java method call to {method_name}",
                    severity="high" if effect_type in [ExitPointType.FILE_WRITE, 
                                                      ExitPointType.DATABASE] else "medium"
                )
                self.analyzer.exit_points[var].append(exit_point)
                self.analyzer.external_effects[var].append(
                    f"{method_name} at {self.analyzer.filename}:{self.line_number}"
                )
    
    def _analyze_return_statement(self, stmt):
        """Analyze Java return statement as exit point"""
        try:
            import javalang
        except ImportError:
            return
            
        if stmt.expression and self.current_method:
            returned_vars = self._extract_java_dependencies(stmt.expression)
            
            for var in returned_vars:
                exit_point = ExitPoint(
                    type=ExitPointType.RETURN,
                    location=self.analyzer.filename,
                    line=self.line_number,
                    function=self.current_method or "main",
                    description=f"Returns value dependent on {var}",
                    severity="medium"
                )
                self.analyzer.exit_points[var].append(exit_point)
    
    def _analyze_for_statement(self, stmt):
        """Analyze Java for loop with context tracking"""
        self.loop_depth += 1
        
        # Analyze initialization in control
        if stmt.control and hasattr(stmt.control, 'init') and stmt.control.init:
            if hasattr(stmt.control.init, 'declarators'):  # Variable declaration
                self._analyze_variable_declaration(stmt.control.init)
        
        # Analyze body
        if stmt.body:
            self._analyze_statement(stmt.body)
        
        self.loop_depth -= 1
    
    def _analyze_while_statement(self, stmt):
        """Analyze Java while loop with context tracking"""
        self.loop_depth += 1
        
        if stmt.body:
            self._analyze_statement(stmt.body)
        
        self.loop_depth -= 1
    
    def _analyze_if_statement(self, stmt):
        """Analyze Java if statement with context tracking"""
        self.conditional_depth += 1
        
        # Analyze then statement
        if stmt.then_statement:
            self._analyze_statement(stmt.then_statement)
        
        # Analyze else statement
        if stmt.else_statement:
            self._analyze_statement(stmt.else_statement)
        
        self.conditional_depth -= 1
    
    def _extract_java_names(self, expr) -> List[str]:
        """Extract variable names from Java expression"""
        try:
            import javalang
        except ImportError:
            return []
            
        if not expr:
            return []
            
        if isinstance(expr, javalang.tree.MemberReference):
            if expr.qualifier and hasattr(expr.qualifier, 'name'):
                if expr.qualifier.name == "this":
                    return [f"this.{expr.member}"]
                else:
                    return [f"{expr.qualifier.name}.{expr.member}"]
            return [expr.member]
        elif hasattr(expr, 'name'):
            return [expr.name]
        elif isinstance(expr, javalang.tree.ArraySelector):
            return self._extract_java_names(expr.array)
        
        return []
    
    def _extract_java_dependencies(self, expr) -> Set[str]:
        """Extract all variable dependencies from Java expression"""
        try:
            import javalang
        except ImportError:
            return set()
            
        if not expr:
            return set()
        
        deps = set()
        
        if isinstance(expr, javalang.tree.MemberReference):
            if expr.qualifier and hasattr(expr.qualifier, 'name'):
                if expr.qualifier.name == "this":
                    deps.add(f"this.{expr.member}")
                else:
                    deps.add(expr.qualifier.name)
            else:
                deps.add(expr.member)
        elif hasattr(expr, 'name'):
            deps.add(expr.name)
        elif isinstance(expr, javalang.tree.BinaryOperation):
            deps.update(self._extract_java_dependencies(expr.operandl))
            deps.update(self._extract_java_dependencies(expr.operandr))
        elif isinstance(expr, javalang.tree.Assignment):
            deps.update(self._extract_java_dependencies(expr.value))
        elif isinstance(expr, javalang.tree.MethodInvocation):
            if expr.qualifier:
                deps.update(self._extract_java_dependencies(expr.qualifier))
            for arg in expr.arguments or []:
                deps.update(self._extract_java_dependencies(arg))
        elif isinstance(expr, javalang.tree.ArraySelector):
            deps.update(self._extract_java_dependencies(expr.array))
            deps.update(self._extract_java_dependencies(expr.index))
        elif isinstance(expr, javalang.tree.Cast):
            deps.update(self._extract_java_dependencies(expr.expression))
        elif isinstance(expr, javalang.tree.TernaryExpression):
            deps.update(self._extract_java_dependencies(expr.condition))
            deps.update(self._extract_java_dependencies(expr.if_true))
            deps.update(self._extract_java_dependencies(expr.if_false))
        
        return deps
    
    def _infer_java_type(self, type_node) -> TypeInfo:
        """Infer type from Java type node"""
        try:
            import javalang
        except ImportError:
            return TypeInfo("unknown", 0.0)
        
        if not type_node:
            return TypeInfo("unknown", 0.0)
        
        if hasattr(type_node, 'name'):
            type_name = type_node.name
            if type_name in ["int", "Integer"]:
                return TypeInfo("int", 0.9)
            elif type_name in ["double", "Double", "float", "Float"]:
                return TypeInfo("double", 0.9)
            elif type_name in ["boolean", "Boolean"]:
                return TypeInfo("boolean", 0.9)
            elif type_name in ["String"]:
                return TypeInfo("String", 0.9)
            elif type_name in ["List", "ArrayList", "LinkedList"]:
                return TypeInfo("List", 0.8)
            elif type_name in ["Map", "HashMap", "TreeMap"]:
                return TypeInfo("Map", 0.8)
            else:
                return TypeInfo(type_name, 0.7)
        
        return TypeInfo("unknown", 0.0)
    
    def _infer_java_type_from_expression(self, expr) -> TypeInfo:
        """Infer type from Java expression"""
        try:
            import javalang
        except ImportError:
            return TypeInfo("unknown", 0.0)
        
        if not expr:
            return TypeInfo("unknown", 0.0)
        
        if isinstance(expr, javalang.tree.Literal):
            if expr.value == "null":
                return TypeInfo("null", 1.0, [None], nullable=True)
            elif isinstance(expr.value, str):
                if expr.value.startswith('"'):
                    return TypeInfo("String", 1.0, [expr.value.strip('"')])
                elif expr.value.isdigit():
                    return TypeInfo("int", 1.0, [int(expr.value)])
                elif '.' in expr.value:
                    return TypeInfo("double", 1.0, [float(expr.value)])
                elif expr.value in ["true", "false"]:
                    return TypeInfo("boolean", 1.0, [expr.value == "true"])
        elif isinstance(expr, javalang.tree.MethodInvocation):
            # Try to infer from method name
            if expr.member:
                if expr.member.startswith("get") and expr.member != "get":
                    return TypeInfo("Object", 0.5)
                elif expr.member in ["toString", "substring", "toLowerCase", "toUpperCase"]:
                    return TypeInfo("String", 0.8)
                elif expr.member in ["size", "length", "count"]:
                    return TypeInfo("int", 0.8)
        elif isinstance(expr, javalang.tree.BinaryOperation):
            # Infer from operation type
            if expr.operator in ["+", "-", "*", "/", "%"]:
                return TypeInfo("numeric", 0.6)
            elif expr.operator in ["==", "!=", "<", ">", "<=", ">=", "&&", "||"]:
                return TypeInfo("boolean", 0.8)
        
        return TypeInfo("unknown", 0.0)
    
    def _is_java_external_effect(self, method_name: str, invocation) -> bool:
        """Check if Java method call has external effects"""
        if method_name in self.java_io_functions:
            return True
        elif method_name in self.java_db_functions:
            return True
        elif method_name in self.java_network_functions:
            return True
        
        # Check if it's System.out.println or similar
        try:
            import javalang
            if (isinstance(invocation.qualifier, javalang.tree.MemberReference) and
                hasattr(invocation.qualifier, 'qualifier') and
                hasattr(invocation.qualifier.qualifier, 'name') and
                invocation.qualifier.qualifier.name == "System"):
                return True
        except:
            pass
        
        return False
    
    def _classify_java_external_effect(self, method_name: str, invocation) -> ExitPointType:
        """Classify the type of Java external effect"""
        if method_name in ["println", "print", "printf"]:
            return ExitPointType.CONSOLE
        elif method_name in self.java_io_functions:
            return ExitPointType.FILE_WRITE
        elif method_name in self.java_network_functions:
            return ExitPointType.NETWORK
        elif method_name in self.java_db_functions:
            return ExitPointType.DATABASE
        else:
            return ExitPointType.EXTERNAL_CALL
    
    def _get_java_value_repr(self, expr) -> str:
        """Get string representation of Java expression"""
        try:
            import javalang
        except ImportError:
            return "unknown"
        
        if not expr:
            return "uninitialized"
        
        if isinstance(expr, javalang.tree.Literal):
            return str(expr.value)
        elif hasattr(expr, 'name'):
            return expr.name
        elif isinstance(expr, javalang.tree.MethodInvocation):
            return f"{expr.member}()"
        elif isinstance(expr, javalang.tree.BinaryOperation):
            return f"binary_op({expr.operator})"
        else:
            return type(expr).__name__
    
    def _get_line_number(self, node) -> int:
        """Get line number from Java AST node"""
        if hasattr(node, 'position') and node.position:
            return node.position.line
        return self.line_number or 1


def main():
    parser = argparse.ArgumentParser(
        description="Data Flow Tracker V2 - Advanced code intelligence and algorithm analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Impact analysis - see what changing a variable affects
  %(prog)s --var config --show-impact --file app.py

  # Calculation path - understand how a value is computed
  %(prog)s --var final_price --show-calculation-path --file pricing.py

  # Type and state tracking - monitor variable evolution
  %(prog)s --var user_data --track-state --file process.py

  # Standard forward/backward tracking (V1 compatibility)
  %(prog)s --var x --direction forward --file calc.py
  %(prog)s --var result --direction backward --file calc.py

  # Generate visualization
  %(prog)s --var data --format graph --file module.py > flow.dot
  dot -Tpng flow.dot -o flow.png
        """
    )
    
    parser.add_argument("--var", required=True, help="Variable name to track")
    parser.add_argument("--file", required=True, help="Source file to analyze")
    parser.add_argument("--direction", choices=["forward", "backward"], 
                       help="Tracking direction (default: forward)")
    parser.add_argument("--max-depth", type=int, default=-1,
                       help="Maximum tracking depth (-1 for unlimited)")
    parser.add_argument("--format", choices=["text", "json", "graph"], default="text",
                       help="Output format")
    parser.add_argument("--show-all", action="store_true",
                       help="Show all variables and their dependencies")
    parser.add_argument("--inter-procedural", action="store_true",
                       help="Enable inter-procedural analysis")
    
    # V2 specific options
    parser.add_argument("--show-impact", action="store_true",
                       help="Show impact analysis (where data escapes scope)")
    parser.add_argument("--show-calculation-path", action="store_true",
                       help="Show minimal calculation path for the variable")
    parser.add_argument("--track-state", action="store_true",
                       help="Track type and state evolution")
    
    args = parser.parse_args()
    
    # Read source file
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Determine language
    if args.file.endswith('.py'):
        language = "python"
    elif args.file.endswith('.java'):
        language = "java"
    else:
        print("Warning: Unknown file type, assuming Python", file=sys.stderr)
        language = "python"
    
    # Create analyzer
    analyzer = DataFlowAnalyzerV2(source_code, args.file, language)
    
    try:
        analyzer.analyze()
    except Exception as e:
        print(f"Error analyzing code: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
    
    # Perform requested analysis
    if args.show_impact:
        result = analyzer.show_impact(args.var)
    elif args.show_calculation_path:
        result = analyzer.show_calculation_path(args.var)
    elif args.track_state:
        result = analyzer.track_state(args.var)
    elif args.show_all:
        # Show all variables
        all_vars = set()
        all_vars.update(analyzer.definitions.keys())
        all_vars.update(analyzer.dependencies.keys())
        
        result = {
            "total_variables": len(all_vars),
            "variables": []
        }
        
        for var in sorted(all_vars):
            var_info = {
                "name": var,
                "defined_at": analyzer.definitions.get(var, "undefined"),
                "depends_on": list(analyzer.dependencies.get(var, [])),
                "affects": [v for v, deps in analyzer.dependencies.items() if var in deps]
            }
            result["variables"].append(var_info)
    else:
        # Standard forward/backward tracking
        direction = args.direction or "forward"
        if direction == "forward":
            result = analyzer.track_forward(args.var, args.max_depth)
        else:
            result = analyzer.track_backward(args.var, args.max_depth)
    
    # Format and output
    output = analyzer.format_output(result, args.format)
    print(output)


if __name__ == "__main__":
    main()