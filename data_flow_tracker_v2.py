#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Data Flow Tracker V2 - Advanced code intelligence and algorithm analysis tool

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-26
Updated: 2025-07-27
License: Mozilla Public License 2.0 (MPL-2.0)

Enhanced version with five major capabilities:
1. Impact Analysis - Shows where data escapes scope and causes effects
2. Calculation Path Analysis - Extracts minimal critical path for values
3. Type and State Tracking - Monitors type evolution and state changes
4. Natural Language Explanations - Intuitive explanations of complex analysis
5. Interactive HTML Visualization - Self-contained reports with vis.js network graphs

This tool provides both safety (know what changes affect) and intelligence
(understand complex algorithms) for confident refactoring and debugging.

New Features in V2:
- Impact analysis with exit point detection and risk assessment
- Critical path extraction with branch pruning
- Static type inference and state tracking
- Natural language explanations with --explain flag
- Interactive HTML reports with --output-html flag
- Self-contained visualizations using vis.js (no external dependencies)
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
import re

# Optional Java support
try:
    import javalang
    JAVA_SUPPORT = True
except ImportError:
    javalang = None
    JAVA_SUPPORT = False

# Optional Jinja2 template support
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_SUPPORT = True
except ImportError:
    Environment = None
    FileSystemLoader = None
    select_autoescape = None
    JINJA2_SUPPORT = False

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
        # Function/method calls and inter-procedural data
        self.function_calls: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # var -> list(call info)
        self.function_returns = defaultdict(list)
        self.parameter_mappings: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # func -> list of mappings
        self.function_params: Dict[str, List[str]] = {}  # func -> parameter names
        
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
    
    def generate_explanation(self, result: Dict[str, Any], analysis_type: str, var_name: str) -> str:
        """Generate natural language explanations of analysis results"""
        if analysis_type == "impact":
            return self._explain_impact_analysis(result, var_name)
        elif analysis_type == "calculation_path":
            return self._explain_calculation_path(result, var_name)
        elif analysis_type == "state_tracking":
            return self._explain_state_tracking(result, var_name)
        else:
            return self._explain_standard_analysis(result, var_name)
    
    def generate_html_report(self, result: Dict[str, Any], analysis_type: str, var_name: str) -> str:
        """Generate interactive HTML visualization report"""
        explanation = self.generate_explanation(result, analysis_type, var_name)
        
        if analysis_type == "impact":
            return self._generate_impact_html(result, var_name, explanation)
        elif analysis_type == "calculation_path":
            return self._generate_calculation_path_html(result, var_name, explanation)
        elif analysis_type == "state_tracking":
            return self._generate_state_tracking_html(result, var_name, explanation)
        else:
            return self._generate_standard_html(result, var_name, explanation)
    
    def _build_function_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Build a mapping of function names to return values and dependencies."""
        mappings: Dict[str, Dict[str, Any]] = {}
        
        # Look through all exit points to find what functions return
        for var, exit_points in self.exit_points.items():
            for exit_point in exit_points:
                if exit_point.type == ExitPointType.RETURN:
                    func_name = exit_point.function
                    if func_name not in mappings:
                        mappings[func_name] = {
                            "returns": [],
                            "dependencies": [],
                            "location": exit_point.location,
                            "line": exit_point.line
                        }
                    if var not in mappings[func_name]["returns"]:
                        mappings[func_name]["returns"].append(var)
        
        # Look through function calls to get dependencies observed at call sites
        for var, calls in self.function_calls.items():
            for call_info in calls:
                func_name = call_info.get("function", "")
                if func_name in mappings:
                    if var not in mappings[func_name]["dependencies"]:
                        mappings[func_name]["dependencies"].append(var)

        # Incorporate explicit parameter mappings captured at call sites
        for func_name, mapping_list in self.parameter_mappings.items():
            if func_name not in mappings:
                mappings[func_name] = {
                    "returns": [],
                    "dependencies": [],
                    "location": "unknown",
                    "line": 0
                }
            for m in mapping_list:
                for args in m.get("mapping", {}).values():
                    for v in args:
                        if v not in mappings[func_name]["dependencies"]:
                            mappings[func_name]["dependencies"].append(v)
        
        return mappings
    
    def _extract_calculation_path(self, target_var: str) -> List[Dict[str, Any]]:
        """Extract the minimal calculation path for a variable with deep function call tracing"""
        path = []
        visited = set()
        function_mappings = self._build_function_mappings()
        
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
                    
                    # Trace inputs - enhanced to follow function calls
                    for input_var in step["inputs"]:
                        # If input_var is a function name, trace what that function returns
                        if input_var in function_mappings:
                            # Add a step for the function call itself
                            func_step = {
                                "variable": input_var,
                                "operation": "function_call",
                                "inputs": function_mappings[input_var].get("dependencies", []),
                                "output": input_var,
                                "location": function_mappings[input_var].get("location", "unknown"),
                                "line": function_mappings[input_var].get("line", 0),
                                "essential": True,
                                "depth": depth + 1
                            }
                            path.append(func_step)
                            
                            # Trace what the function returns
                            for returned_var in function_mappings[input_var].get("returns", []):
                                trace_calculation(returned_var, depth + 2)
                            
                            # Trace function parameters
                            for param_var in function_mappings[input_var].get("dependencies", []):
                                trace_calculation(param_var, depth + 2)
                        else:
                            # Regular variable dependency
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
        """Determine if a calculation step is essential for the target value
        
        A calculation is considered essential if:
        1. It directly produces the target variable
        2. It modifies a variable that eventually affects the target
        3. It's part of a control flow that determines the target's value
        """
        # Direct assignment to target is always essential
        if step.get('variable') == target:
            return True
        
        # Check if this step's output affects the target
        outputs = step.get('outputs', [])
        if target in outputs:
            return True
        
        # Check operation type
        operation = step.get('operation', 'assignment')
        
        # Control flow operations are usually essential
        if operation in ['condition', 'loop', 'branch']:
            # Check if the condition uses variables that affect target
            inputs = step.get('inputs', [])
            if any(self._variable_affects_target(var, target) for var in inputs):
                return True
        
        # Function calls that might have side effects
        if operation == 'function_call':
            func_name = step.get('function', '')
            # Essential if it's a known state-modifying function
            if any(pattern in func_name.lower() for pattern in ['set', 'update', 'modify', 'write', 'save']):
                return True
        
        # Intermediate calculations - check if they contribute to target
        if operation in ['assignment', 'calculation']:
            # This step is essential if its output is used by another essential step
            step_var = step.get('variable')
            if step_var and self._variable_affects_target(step_var, target):
                return True
        
        # Default: consider non-essential for pruning
        return False
    
    def _variable_affects_target(self, var: str, target: str, visited: Optional[Set[str]] = None, depth: int = 0) -> bool:
        """Check if a variable eventually affects the target variable"""
        # Initialize visited set on first call
        if visited is None:
            visited = set()
        
        # Prevent infinite recursion with depth limit
        if depth > 100:
            return False
        
        # Prevent cycles
        if var in visited:
            return False
        
        # Quick check: if var is the target itself
        if var == target:
            return True
        
        # Mark as visited
        visited.add(var)
        
        # Check in our tracked dependencies
        if var in self.dependencies:
            for dep_var in self.dependencies[var]:
                if dep_var == target or self._variable_affects_target(dep_var, target, visited, depth + 1):
                    return True
        
        return False
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            "HIGH": "Comprehensive testing required - consider breaking into smaller changes",
            "MEDIUM": "Standard testing with focus on affected areas",
            "LOW": "Normal testing procedures sufficient"
        }
        return recommendations.get(risk_level, "Assess based on specific changes")
    
    def _explain_impact_analysis(self, result: Dict[str, Any], var_name: str) -> str:
        """Generate natural language explanation for impact analysis"""
        returns = result.get("returns", [])
        side_effects = result.get("side_effects", [])
        state_changes = result.get("state_changes", [])
        
        total_effects = len(returns) + len(side_effects) + len(state_changes)
        functions_affected = len(set(ep.get("function", "unknown") for ep in returns + side_effects + state_changes))
        
        risk_level = result.get("risk_assessment", {}).get("risk_level", "LOW")
        
        if total_effects == 0:
            return f"✅ **Perfect Safety**: Changing '{var_name}' has no external effects. This variable stays within its local scope and is completely safe to modify without any risk of breaking other parts of the code."
        
        explanation = f"📊 **Impact Analysis for '{var_name}'**:\n\n"
        
        if risk_level == "HIGH":
            explanation += f"🚨 **High Risk Change**: Modifying '{var_name}' affects {total_effects} different places across {functions_affected} functions. "
        elif risk_level == "MEDIUM":
            explanation += f"⚠️ **Medium Risk Change**: Modifying '{var_name}' affects {total_effects} places in your code. "
        else:
            explanation += f"✅ **Low Risk Change**: Modifying '{var_name}' has minimal impact with {total_effects} effects. "
        
        if returns:
            explanation += f"It affects {len(returns)} return values, "
        if side_effects:
            explanation += f"causes {len(side_effects)} external side effects (like file writes or console output), "
        if state_changes:
            explanation += f"and modifies {len(state_changes)} global or class variables. "
        
        explanation = explanation.rstrip(", ") + ".\n\n"
        
        if risk_level == "HIGH":
            explanation += "💡 **Recommendation**: Break this change into smaller steps and test each affected function thoroughly."
        elif risk_level == "MEDIUM":
            explanation += "💡 **Recommendation**: Focus testing on the affected areas and verify all return values and side effects."
        else:
            explanation += "💡 **Recommendation**: Standard testing procedures should be sufficient for this change."
        
        return explanation
    
    def _explain_calculation_path(self, result: List[Dict[str, Any]], var_name: str) -> str:
        """Generate natural language explanation for calculation path analysis"""
        if not result:
            return f"❓ **No Calculation Path**: Variable '{var_name}' appears to be assigned directly or not found in the code."
        
        explanation = f"🔍 **How '{var_name}' is Calculated**:\n\n"
        
        if len(result) == 1:
            explanation += f"This is a simple assignment with {len(result[0].get('inputs', []))} input variables."
        else:
            explanation += f"This value is calculated through {len(result)} steps, showing the complete algorithm flow."
        
        explanation += f"\n\n**The Critical Path**:\n"
        
        for i, step in enumerate(result, 1):
            inputs = step.get("inputs", [])
            operation = step.get("operation", "assignment")
            
            if operation == "declaration":
                explanation += f"{i}. **Variable Created**: '{step['variable']}' is first declared"
            elif operation == "assignment":
                if inputs:
                    explanation += f"{i}. **Calculation Step**: '{step['variable']}' is computed from {', '.join(inputs)}"
                else:
                    explanation += f"{i}. **Direct Assignment**: '{step['variable']}' is assigned a direct value"
            else:
                explanation += f"{i}. **{operation.title()}**: '{step['variable']}' undergoes {operation}"
            
            if inputs:
                explanation += f" (depends on: {', '.join(inputs)})"
            explanation += "\n"
        
        explanation += f"\n💡 **Understanding**: To debug issues with '{var_name}', trace through these {len(result)} steps. "
        explanation += "Each step shows exactly where the value comes from and what influences it."
        
        return explanation
    
    def _explain_state_tracking(self, result: Dict[str, Any], var_name: str) -> str:
        """Generate natural language explanation for state tracking analysis"""
        type_evolution = result.get("type_evolution", [])
        state_changes = result.get("state_changes", [])
        warnings = result.get("warnings", [])
        
        explanation = f"🔄 **State Evolution Analysis for '{var_name}'**:\n\n"
        
        if not type_evolution and not state_changes:
            explanation += f"No type or state changes detected for '{var_name}'. This variable maintains consistent behavior throughout the code."
            return explanation
        
        # Type evolution summary
        if type_evolution:
            types_seen = [te.get("type", "unknown") for te in type_evolution]
            unique_types = list(dict.fromkeys(types_seen))  # Preserve order, remove duplicates
            
            if len(unique_types) == 1:
                explanation += f"**Type Consistency**: '{var_name}' maintains the type '{unique_types[0]}' throughout its lifecycle. ✅\n\n"
            else:
                explanation += f"**Type Changes Detected**: '{var_name}' changes types: {' → '.join(unique_types)}. "
                explanation += "This could indicate potential bugs or intentional polymorphic behavior.\n\n"
        
        # State changes summary
        if state_changes:
            change_types = [sc.get("change_type", "unknown") for sc in state_changes]
            loop_changes = sum(1 for sc in state_changes if sc.get("context", {}).get("in_loop", False))
            conditional_changes = sum(1 for sc in state_changes if sc.get("context", {}).get("in_conditional", False))
            
            explanation += f"**State Modifications**: '{var_name}' is modified {len(state_changes)} times"
            if loop_changes > 0:
                explanation += f", including {loop_changes} changes inside loops"
            if conditional_changes > 0:
                explanation += f", and {conditional_changes} conditional modifications"
            explanation += ".\n\n"
        
        # Warnings summary
        if warnings:
            explanation += f"⚠️ **Potential Issues Detected**:\n"
            for warning in warnings:
                explanation += f"• {warning}\n"
            explanation += "\n"
        
        explanation += "💡 **Analysis Summary**: "
        if warnings:
            explanation += "Review the warnings above to prevent potential runtime errors. "
        if len(unique_types if type_evolution else []) > 1:
            explanation += "Consider type annotations or validation to handle type changes safely. "
        if state_changes:
            explanation += f"Track the {len(state_changes)} state modifications to understand variable behavior."
        else:
            explanation += "Variable behavior is stable and predictable."
        
        return explanation
    
    def _explain_standard_analysis(self, result: Dict[str, Any], var_name: str) -> str:
        """Generate natural language explanation for standard forward/backward analysis"""
        if "affects" in result:
            # Forward analysis
            affects = result.get("affects", [])
            if not affects:
                return f"🔍 **Forward Analysis**: Variable '{var_name}' doesn't affect any other variables. It's a terminal value in your code flow."
            
            explanation = f"🔍 **Forward Analysis for '{var_name}'**:\n\n"
            explanation += f"This variable influences {len(affects)} other variables in your codebase. "
            
            if len(affects) <= 3:
                explanation += f"Specifically, it affects: {', '.join([a.get('variable', a.get('name', 'unknown')) for a in affects])}"
            else:
                explanation += f"The main affected variables are: {', '.join([a.get('variable', a.get('name', 'unknown')) for a in affects[:3]])}, and {len(affects) - 3} others"
            
            explanation += f".\n\n💡 **Impact**: Changes to '{var_name}' will propagate through this dependency chain. Test all affected variables when modifying this one."
            
        elif "depends_on" in result:
            # Backward analysis
            depends_on = result.get("depends_on", [])
            if not depends_on:
                return f"🔍 **Backward Analysis**: Variable '{var_name}' has no dependencies. It's either a constant, user input, or source value."
            
            explanation = f"🔍 **Backward Analysis for '{var_name}'**:\n\n"
            explanation += f"This variable depends on {len(depends_on)} other variables. "
            
            if len(depends_on) <= 3:
                explanation += f"It's calculated from: {', '.join([d.get('variable', d.get('name', 'unknown')) for d in depends_on])}"
            else:
                explanation += f"Key dependencies include: {', '.join([d.get('variable', d.get('name', 'unknown')) for d in depends_on[:3]])}, and {len(depends_on) - 3} others"
            
            explanation += f".\n\n💡 **Debugging**: To troubleshoot issues with '{var_name}', check these dependencies first. Any problems likely originate from these source variables."
        
        else:
            explanation = f"🔍 **Analysis Results**: Completed analysis for variable '{var_name}'. See detailed results above for specific dependency information."
        
        return explanation
    
    def _generate_impact_html(self, result: Dict[str, Any], var_name: str, explanation: str) -> str:
        """Generate interactive HTML for impact analysis"""
        returns = result.get("returns", [])
        side_effects = result.get("side_effects", [])
        state_changes = result.get("state_changes", [])
        risk_level = result.get("risk_assessment", {}).get("risk_level", "LOW")
        
        # Create node data for visualization
        nodes = [{"id": var_name, "label": var_name, "group": "source", "level": 0}]
        edges = []
        
        # Add affected nodes
        for i, ret in enumerate(returns):
            node_id = f"return_{i}"
            nodes.append({
                "id": node_id,
                "label": f"Return: {ret.get('function', 'unknown')}",
                "group": "return",
                "level": 1,
                "details": f"Function: {ret.get('function', 'unknown')}\nLocation: {ret.get('location', 'unknown')}"
            })
            edges.append({"from": var_name, "to": node_id, "arrows": "to", "color": {"color": "#2B7CE9"}})
        
        for i, effect in enumerate(side_effects):
            node_id = f"effect_{i}"
            effect_type = effect.get("type", "unknown")
            color = {"file_write": "#FF6B6B", "console": "#4ECDC4", "network": "#45B7D1", "database": "#96CEB4"}.get(effect_type, "#FFA07A")
            nodes.append({
                "id": node_id,
                "label": f"Side Effect: {effect.get('type', 'unknown')}",
                "group": "side_effect",
                "level": 1,
                "details": f"Type: {effect_type}\nLocation: {effect.get('location', 'unknown')}"
            })
            edges.append({"from": var_name, "to": node_id, "arrows": "to", "color": {"color": color}})
        
        for i, change in enumerate(state_changes):
            node_id = f"state_{i}"
            nodes.append({
                "id": node_id,
                "label": f"State Change: {change.get('effect', 'unknown')}",
                "group": "state_change",
                "level": 1,
                "details": f"Location: {change.get('location', 'unknown')}"
            })
            edges.append({"from": var_name, "to": node_id, "arrows": "to", "color": {"color": "#F39C12"}})
        
        return self._create_html_template("Impact Analysis", var_name, explanation, nodes, edges, risk_level)
    
    def _generate_calculation_path_html(self, result: List[Dict[str, Any]], var_name: str, explanation: str) -> str:
        """Generate interactive HTML for calculation path analysis"""
        nodes = []
        edges = []
        
        if not result:
            nodes.append({"id": var_name, "label": var_name, "group": "target", "level": 0})
            return self._create_html_template("Calculation Path", var_name, explanation, nodes, edges, "NONE")
        
        # Create a path visualization
        for i, step in enumerate(result):
            node_id = f"step_{i}"
            inputs = step.get("inputs", [])
            
            nodes.append({
                "id": node_id,
                "label": f"{step.get('variable', 'unknown')}",
                "group": "calculation",
                "level": i,
                "details": f"Operation: {step.get('operation', 'unknown')}\nLocation: {step.get('location', 'unknown')}\nInputs: {', '.join(inputs) if inputs else 'none'}"
            })
            
            # Add input nodes and edges
            for input_var in inputs:
                input_id = f"input_{input_var}_{i}"
                if not any(n["id"] == input_id for n in nodes):
                    nodes.append({
                        "id": input_id,
                        "label": input_var,
                        "group": "input",
                        "level": i - 0.5
                    })
                edges.append({"from": input_id, "to": node_id, "arrows": "to", "color": {"color": "#27AE60"}})
            
            # Connect calculation steps
            if i > 0:
                edges.append({"from": f"step_{i-1}", "to": node_id, "arrows": "to", "color": {"color": "#E74C3C"}, "width": 3})
        
        return self._create_html_template("Calculation Path", var_name, explanation, nodes, edges, "INFO")
    
    def _generate_state_tracking_html(self, result: Dict[str, Any], var_name: str, explanation: str) -> str:
        """Generate interactive HTML for state tracking analysis"""
        type_evolution = result.get("type_evolution", [])
        state_changes = result.get("state_changes", [])
        
        nodes = [{"id": var_name, "label": f"{var_name} (start)", "group": "source", "level": 0}]
        edges = []
        
        # Add type evolution nodes
        for i, type_info in enumerate(type_evolution):
            node_id = f"type_{i}"
            type_name = type_info.get("type", "unknown")
            confidence = type_info.get("confidence", 0.0)
            
            nodes.append({
                "id": node_id,
                "label": f"{type_name} ({confidence:.1f})",
                "group": "type",
                "level": i + 1,
                "details": f"Type: {type_name}\nConfidence: {confidence:.2f}\nLocation: {type_info.get('location', 'unknown')}"
            })
            
            if i == 0:
                edges.append({"from": var_name, "to": node_id, "arrows": "to", "color": {"color": "#9B59B6"}})
            else:
                edges.append({"from": f"type_{i-1}", "to": node_id, "arrows": "to", "color": {"color": "#9B59B6"}})
        
        # Add state change nodes
        for i, change in enumerate(state_changes):
            node_id = f"change_{i}"
            change_type = change.get("change_type", "unknown")
            
            nodes.append({
                "id": node_id,
                "label": f"{change_type}",
                "group": "state_change",
                "level": len(type_evolution) + i + 1,
                "details": f"Change: {change_type}\nLocation: {change.get('location', 'unknown')}\nContext: Loop={change.get('context', {}).get('in_loop', False)}, Conditional={change.get('context', {}).get('in_conditional', False)}"
            })
            
            # Connect to appropriate previous node
            if type_evolution:
                edges.append({"from": f"type_{len(type_evolution)-1}", "to": node_id, "arrows": "to", "color": {"color": "#E67E22"}})
            else:
                edges.append({"from": var_name, "to": node_id, "arrows": "to", "color": {"color": "#E67E22"}})
        
        warnings = result.get("warnings", [])
        risk_level = "HIGH" if len(warnings) > 2 else "MEDIUM" if warnings else "LOW"
        
        return self._create_html_template("State Tracking", var_name, explanation, nodes, edges, risk_level)
    
    def _generate_standard_html(self, result: Dict[str, Any], var_name: str, explanation: str) -> str:
        """Generate interactive HTML for standard dependency analysis"""
        nodes = [{"id": var_name, "label": var_name, "group": "source", "level": 0}]
        edges = []
        
        if "affects" in result:
            # Forward analysis
            affects = result.get("affects", [])
            for i, affected in enumerate(affects):
                node_id = f"affects_{i}"
                nodes.append({
                    "id": node_id,
                    "label": affected.get("variable", affected.get("name", "unknown")),
                    "group": "affected",
                    "level": 1,
                    "details": f"Variable: {affected.get('variable', affected.get('name', 'unknown'))}\nLocation: {affected.get('location', 'unknown')}"
                })
                edges.append({"from": var_name, "to": node_id, "arrows": "to", "color": {"color": "#3498DB"}})
        
        elif "depends_on" in result:
            # Backward analysis  
            depends_on = result.get("depends_on", [])
            for i, dependency in enumerate(depends_on):
                node_id = f"depends_{i}"
                nodes.append({
                    "id": node_id,
                    "label": dependency.get("variable", dependency.get("name", "unknown")),
                    "group": "dependency",
                    "level": -1,
                    "details": f"Variable: {dependency.get('variable', dependency.get('name', 'unknown'))}\nLocation: {dependency.get('location', 'unknown')}"
                })
                edges.append({"from": node_id, "to": var_name, "arrows": "to", "color": {"color": "#E74C3C"}})
        
        return self._create_html_template("Dependency Analysis", var_name, explanation, nodes, edges, "INFO")
    
    def _get_template_environment(self) -> Optional[Environment]:
        """Get Jinja2 environment if available"""
        if not JINJA2_SUPPORT:
            return None
        
        # Find template directory relative to this script
        script_dir = Path(__file__).parent
        template_dir = script_dir / "templates"
        
        if not template_dir.exists():
            return None
            
        return Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def _create_html_template(self, title: str, var_name: str, explanation: str, nodes: List[Dict], edges: List[Dict], risk_level: str) -> str:
        """Create the base HTML template with vis.js visualization"""
        
        # Risk level colors and messages
        risk_colors = {
            "HIGH": "#E74C3C",
            "MEDIUM": "#F39C12", 
            "LOW": "#27AE60",
            "INFO": "#3498DB",
            "NONE": "#95A5A6"
        }
        
        risk_messages = {
            "HIGH": "🚨 High Risk - Comprehensive testing required",
            "MEDIUM": "⚠️ Medium Risk - Standard testing recommended", 
            "LOW": "✅ Low Risk - Normal testing sufficient",
            "INFO": "ℹ️ Information - Analysis complete",
            "NONE": "➖ No Data - Limited analysis available"
        }
        
        # Try to use Jinja2 template if available
        env = self._get_template_environment()
        if env:
            try:
                template = env.get_template('data_flow/visualization.html')
                return template.render(
                    title=title,
                    var_name=var_name,
                    explanation=explanation,
                    nodes=nodes,
                    edges=edges,
                    risk_level=risk_level,
                    risk_color=risk_colors.get(risk_level, '#3498DB'),
                    risk_message=risk_messages.get(risk_level, ''),
                    metadata={
                        'analysis_type': title,
                        'total_nodes': len(nodes),
                        'total_edges': len(edges)
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to use Jinja2 template: {e}", file=sys.stderr)
                # Fall through to built-in template
        
        # Fallback to built-in template (keeping existing code for compatibility)
        # Risk level colors and messages are already defined above
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {var_name}</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: {risk_colors.get(risk_level, '#3498DB')};
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        
        .header .subtitle {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .risk-indicator {{
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 25px;
            display: inline-block;
            margin-top: 15px;
            font-weight: 500;
        }}
        
        .content {{
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 0;
            min-height: 600px;
        }}
        
        .explanation {{
            padding: 30px;
            background: #f8f9fa;
            border-right: 1px solid #e9ecef;
            overflow-y: auto;
        }}
        
        .explanation h2 {{
            color: #2c3e50;
            margin-top: 0;
            border-bottom: 2px solid {risk_colors.get(risk_level, '#3498DB')};
            padding-bottom: 10px;
        }}
        
        .explanation p {{
            line-height: 1.6;
            color: #34495e;
        }}
        
        .visualization {{
            position: relative;
        }}
        
        #network {{
            width: 100%;
            height: 600px;
            background: #fafafa;
        }}
        
        .controls {{
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
        }}
        
        .control-btn {{
            background: white;
            border: 1px solid #ddd;
            padding: 8px 12px;
            margin: 2px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .control-btn:hover {{
            background: #f0f0f0;
        }}
        
        .node-details {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            right: 10px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 15px;
            display: none;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .content {{
                grid-template-columns: 1fr;
            }}
            
            .explanation {{
                border-right: none;
                border-bottom: 1px solid #e9ecef;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">Variable: <code>{var_name}</code></div>
            <div class="risk-indicator">{risk_messages.get(risk_level, 'Analysis Complete')}</div>
        </div>
        
        <div class="content">
            <div class="explanation">
                <h2>📝 Analysis Summary</h2>
                <div style="white-space: pre-line;">{explanation}</div>
            </div>
            
            <div class="visualization">
                <div class="controls">
                    <button class="control-btn" onclick="network.fit()">📍 Center</button>
                    <button class="control-btn" onclick="togglePhysics()">⚡ Physics</button>
                    <button class="control-btn" onclick="exportImage()">📸 Export</button>
                </div>
                <div id="network"></div>
                <div id="nodeDetails" class="node-details">
                    <h4>Node Details</h4>
                    <div id="detailsContent">Click a node to see details</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            Generated by Data Flow Tracker V2 | Interactive visualization powered by vis.js
        </div>
    </div>

    <script>
        // Network data
        const nodes = new vis.DataSet({json.dumps(nodes, indent=8)});
        const edges = new vis.DataSet({json.dumps(edges, indent=8)});
        
        // Network options
        const options = {{
            nodes: {{
                shape: 'box',
                margin: 10,
                font: {{ size: 14, face: 'Arial', color: '#2c3e50' }},
                borderWidth: 2,
                shadow: true,
                borderWidthSelected: 3
            }},
            edges: {{
                width: 2,
                shadow: true,
                smooth: {{ type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.4 }}
            }},
            groups: {{
                source: {{ color: {{ background: '#3498DB', border: '#2980B9' }}, font: {{ color: 'white' }} }},
                return: {{ color: {{ background: '#2ECC71', border: '#27AE60' }} }},
                side_effect: {{ color: {{ background: '#E74C3C', border: '#C0392B' }}, font: {{ color: 'white' }} }},
                state_change: {{ color: {{ background: '#F39C12', border: '#E67E22' }} }},
                calculation: {{ color: {{ background: '#9B59B6', border: '#8E44AD' }}, font: {{ color: 'white' }} }},
                input: {{ color: {{ background: '#95A5A6', border: '#7F8C8D' }} }},
                type: {{ color: {{ background: '#1ABC9C', border: '#16A085' }} }},
                affected: {{ color: {{ background: '#E67E22', border: '#D35400' }} }},
                dependency: {{ color: {{ background: '#34495E', border: '#2C3E50' }}, font: {{ color: 'white' }} }}
            }},
            layout: {{
                hierarchical: {{
                    direction: 'LR',
                    sortMethod: 'directed',
                    levelSeparation: 150,
                    nodeSpacing: 100
                }}
            }},
            physics: {{
                enabled: true,
                hierarchicalRepulsion: {{
                    centralGravity: 0.0,
                    springLength: 100,
                    springConstant: 0.01,
                    nodeDistance: 120,
                    damping: 0.09
                }}
            }},
            interaction: {{
                dragNodes: true,
                dragView: true,
                zoomView: true
            }}
        }};
        
        // Initialize network
        const container = document.getElementById('network');
        const data = {{ nodes: nodes, edges: edges }};
        const network = new vis.Network(container, data, options);
        
        // Event handlers
        network.on('click', function(params) {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);
                showNodeDetails(node);
            }} else {{
                hideNodeDetails();
            }}
        }});
        
        let physicsEnabled = true;
        
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            network.setOptions({{ physics: {{ enabled: physicsEnabled }} }});
        }}
        
        function showNodeDetails(node) {{
            const details = document.getElementById('nodeDetails');
            const content = document.getElementById('detailsContent');
            
            let html = `<strong>${{node.label}}</strong><br>`;
            if (node.details) {{
                html += node.details.replace(/\\n/g, '<br>');
            }} else {{
                html += `Group: ${{node.group}}<br>Level: ${{node.level}}`;
            }}
            
            content.innerHTML = html;
            details.style.display = 'block';
        }}
        
        function hideNodeDetails() {{
            document.getElementById('nodeDetails').style.display = 'none';
        }}
        
        function exportImage() {{
            const canvas = document.querySelector('#network canvas');
            const link = document.createElement('a');
            link.download = '{title.lower().replace(" ", "_")}_{var_name}.png';
            link.href = canvas.toDataURL();
            link.click();
        }}
        
        // Initialize
        network.once('stabilizationIterationsDone', function() {{
            network.fit();
        }});
    </script>
</body>
</html>"""
    
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
    
    def generate_ai_reasoning(self, result: Dict[str, Any], analysis_type: str, variable: str) -> Dict[str, Any]:
        """Generate structured reasoning output for AI consumption"""
        from datetime import datetime
        
        reasoning = {
            "reasoning_version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "analysis_type": analysis_type,
            "target_variable": variable,
            "logical_steps": [],
            "risk_assessment": {
                "level": "unknown",
                "factors": [],
                "overall_confidence": 0.0
            },
            "recommendations": [],
            "context_requirements": {
                "needs_human_review": False,
                "needs_additional_analysis": [],
                "safe_for_automation": True
            }
        }
        
        # Analyze based on analysis type
        if analysis_type == "impact":
            reasoning["logical_steps"] = self._generate_impact_reasoning_steps(result)
            reasoning["risk_assessment"] = self._assess_impact_risk(result)
            reasoning["recommendations"] = self._generate_impact_recommendations(result)
        elif analysis_type == "calculation":
            reasoning["logical_steps"] = self._generate_calculation_reasoning_steps(result)
            reasoning["risk_assessment"] = self._assess_calculation_risk(result)
            reasoning["recommendations"] = self._generate_calculation_recommendations(result)
        else:  # standard tracking
            reasoning["logical_steps"] = self._generate_tracking_reasoning_steps(result)
            reasoning["risk_assessment"] = self._assess_tracking_risk(result)
            reasoning["recommendations"] = self._generate_tracking_recommendations(result)
        
        # Update context requirements based on risk
        risk_level = reasoning["risk_assessment"]["level"]
        if risk_level == "high":
            reasoning["context_requirements"]["needs_human_review"] = True
            reasoning["context_requirements"]["safe_for_automation"] = False
        elif risk_level == "medium":
            reasoning["context_requirements"]["needs_additional_analysis"] = ["security_scan", "test_coverage"]
        
        return reasoning
    
    def _generate_impact_reasoning_steps(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate reasoning steps for impact analysis"""
        steps = []
        step_num = 1
        
        # Step 1: Variable identification
        steps.append({
            "step": step_num,
            "action": "identified_variable_scope",
            "targets": list(result.get("definitions", {}).keys()),
            "confidence": 0.95,
            "reasoning": f"Located {len(result.get('definitions', {}))} definitions of the target variable"
        })
        step_num += 1
        
        # Step 2: Direct dependencies
        if "direct_uses" in result or "uses" in result:
            uses = result.get("direct_uses", result.get("uses", []))
            steps.append({
                "step": step_num,
                "action": "traced_direct_dependencies",
                "targets": [use.get("location", "unknown") for use in uses[:5]],  # First 5
                "confidence": 0.90,
                "reasoning": f"Found {len(uses)} direct uses of the variable"
            })
            step_num += 1
        
        # Step 3: Impact analysis
        impact_categories = ["returns", "side_effects", "state_changes", "external_calls"]
        impacts_found = []
        for category in impact_categories:
            if category in result and result[category]:
                impacts_found.append(category)
        
        if impacts_found:
            steps.append({
                "step": step_num,
                "action": "analyzed_impact_categories",
                "targets": impacts_found,
                "confidence": 0.88,
                "reasoning": f"Variable impacts {len(impacts_found)} different system aspects"
            })
            step_num += 1
        
        # Step 4: Exit point analysis
        if "returns" in result and result["returns"]:
            steps.append({
                "step": step_num,
                "action": "identified_exit_points",
                "targets": [ret.get("function", "unknown") for ret in result["returns"]],
                "confidence": 0.92,
                "reasoning": f"Variable affects {len(result['returns'])} function return values"
            })
            step_num += 1
        
        return steps
    
    def _assess_impact_risk(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk level based on impact analysis"""
        risk_factors = []
        total_severity = 0.0
        
        # Check for external API calls
        if result.get("external_calls"):
            risk_factors.append({
                "factor": "external_api_calls",
                "severity": 0.8,
                "description": f"{len(result['external_calls'])} external API calls affected"
            })
            total_severity += 0.8
        
        # Check for side effects
        if result.get("side_effects"):
            high_severity_count = sum(1 for se in result["side_effects"] if se.get("severity") == "high")
            if high_severity_count > 0:
                risk_factors.append({
                    "factor": "high_severity_side_effects",
                    "severity": 0.9,
                    "description": f"{high_severity_count} high-severity side effects detected"
                })
                total_severity += 0.9
        
        # Check for state changes
        if result.get("state_changes"):
            risk_factors.append({
                "factor": "state_mutations",
                "severity": 0.6,
                "description": f"{len(result['state_changes'])} state changes identified"
            })
            total_severity += 0.6
        
        # Check for multiple return impacts
        if result.get("returns") and len(result["returns"]) > 3:
            risk_factors.append({
                "factor": "widespread_return_impact",
                "severity": 0.7,
                "description": f"Affects {len(result['returns'])} function return values"
            })
            total_severity += 0.7
        
        # Determine overall risk level
        avg_severity = total_severity / len(risk_factors) if risk_factors else 0
        if avg_severity >= 0.7:
            risk_level = "high"
        elif avg_severity >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Calculate confidence based on analysis completeness
        confidence = min(0.95, 0.6 + (len(risk_factors) * 0.1))
        
        return {
            "level": risk_level,
            "factors": risk_factors,
            "overall_confidence": confidence
        }
    
    def _generate_impact_recommendations(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on impact analysis"""
        recommendations = []
        
        # Check for missing tests
        if result.get("external_calls") or result.get("side_effects"):
            recommendations.append({
                "action": "add_integration_tests",
                "priority": "high",
                "reasoning": "Variable affects external systems - integration tests needed"
            })
        
        # Check for state mutations
        if result.get("state_changes"):
            recommendations.append({
                "action": "add_state_validation",
                "priority": "medium",
                "reasoning": "Multiple state changes detected - add validation checks"
            })
        
        # Check for widespread impact
        total_impacts = sum(len(result.get(cat, [])) for cat in ["returns", "side_effects", "state_changes", "external_calls"])
        if total_impacts > 10:
            recommendations.append({
                "action": "consider_refactoring",
                "priority": "medium",
                "reasoning": f"Variable has {total_impacts} impact points - consider breaking down functionality"
            })
        
        # Security recommendations
        if any("password" in str(item).lower() or "token" in str(item).lower() or "key" in str(item).lower() 
               for item in result.get("external_calls", [])):
            recommendations.append({
                "action": "security_review",
                "priority": "high",
                "reasoning": "Potential security-sensitive data flow detected"
            })
        
        return recommendations
    
    def _generate_calculation_reasoning_steps(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate reasoning steps for calculation path analysis"""
        steps = []
        
        if "critical_path" in result:
            path = result["critical_path"]
            steps.append({
                "step": 1,
                "action": "extracted_critical_path",
                "targets": [step.get("location", "unknown") for step in path[:3]],
                "confidence": 0.85,
                "reasoning": f"Identified {len(path)}-step critical calculation path"
            })
            
            # Analyze path complexity
            has_loops = any("loop" in str(step).lower() for step in path)
            has_conditions = any("condition" in str(step).lower() for step in path)
            
            if has_loops or has_conditions:
                steps.append({
                    "step": 2,
                    "action": "identified_control_flow",
                    "targets": ["loops" if has_loops else None, "conditions" if has_conditions else None],
                    "confidence": 0.80,
                    "reasoning": "Critical path includes complex control flow"
                })
        
        return steps
    
    def _assess_calculation_risk(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for calculation paths"""
        risk_factors = []
        
        if "critical_path" in result:
            path_length = len(result["critical_path"])
            if path_length > 10:
                risk_factors.append({
                    "factor": "complex_calculation",
                    "severity": 0.6,
                    "description": f"Long calculation path with {path_length} steps"
                })
        
        # Default to medium risk for calculations
        return {
            "level": "medium" if risk_factors else "low",
            "factors": risk_factors,
            "overall_confidence": 0.75
        }
    
    def _generate_calculation_recommendations(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for calculation paths"""
        recommendations = []
        
        if "critical_path" in result and len(result["critical_path"]) > 10:
            recommendations.append({
                "action": "add_intermediate_validation",
                "priority": "medium",
                "reasoning": "Long calculation path - add validation at intermediate steps"
            })
        
        return recommendations
    
    def _generate_tracking_reasoning_steps(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate reasoning steps for standard tracking"""
        return [{
            "step": 1,
            "action": "tracked_data_flow",
            "targets": list(result.keys()),
            "confidence": 0.90,
            "reasoning": "Standard data flow tracking completed"
        }]
    
    def _assess_tracking_risk(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for standard tracking"""
        return {
            "level": "low",
            "factors": [],
            "overall_confidence": 0.85
        }
    
    def _generate_tracking_recommendations(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for standard tracking"""
        return []
    
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
        """Handle function definitions with return tracking and param capture."""
        old_function = self.current_function
        self.current_function = node.name

        # Record parameter names for inter-procedural mapping
        try:
            params = [arg.arg for arg in getattr(node, "args", {}).args]
        except Exception:
            params = []
        self.analyzer.function_params[node.name] = params

        # Process function body
        self.generic_visit(node)

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
        """Enhanced call tracking with external effect detection and dependency recording"""
        # Get function name
        func_name = self._get_call_name(node.func)
        
        if func_name:
            # Extract arguments
            arg_vars = []
            for arg in node.args:
                arg_vars.extend(self._extract_dependencies(arg))
            
            # Record function call dependencies for calculation path analysis
            for var in arg_vars:
                call_info = {
                    "function": func_name,
                    "location": self.analyzer.filename,
                    "line": node.lineno,
                    "arguments": list(arg_vars),
                    "in_function": self.current_function or "module"
                }
                self.analyzer.function_calls[var].append(call_info)

            # Also record parameter->argument mapping when function parameters are known
            if func_name in self.analyzer.function_params:
                formals = self.analyzer.function_params[func_name]
                mapping: Dict[str, List[str]] = {}
                # Positional
                for i, formal in enumerate(formals):
                    if i < len(node.args):
                        mapping[formal] = sorted(self._extract_dependencies(node.args[i]))
                # Keywords
                for kw in getattr(node, "keywords", []) or []:
                    if kw.arg:
                        mapping[kw.arg] = sorted(self._extract_dependencies(kw.value))
                self.analyzer.parameter_mappings[func_name].append({
                    "location": self.analyzer.filename,
                    "line": node.lineno,
                    "in_function": self.current_function or "module",
                    "mapping": mapping
                })
            
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
                        severity="high" if effect_type in (ExitPointType.FILE_WRITE,
                                                           ExitPointType.DATABASE,
                                                           ExitPointType.NETWORK) else "medium"
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
                    # Track full attribute to avoid losing specificity
                    deps.add(f"{node.value.id}.{node.attr}")
                    deps.add(node.value.id)  # also track base for broader impact
            else:
                deps |= self._extract_dependencies(node.value)
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
    """Java analyzer reaching feature parity with Python analyzer.
    Two-pass:
      1) Collect method/constructor parameter lists into function_params
      2) Analyze statements for assignments, calls, returns, control flow, and exit points
    """
    
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
            
        # Pass 1: collect parameter lists
        for path, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                self.current_class = node.name
                for m in node.methods or []:
                    self._record_method_params(m, node.name)
                for c in node.constructors or []:
                    self._record_constructor_params(c, node.name)
                self.current_class = None

        # Pass 2: full analysis
        for path, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                self._analyze_class(node)
    
    def _record_method_params(self, method, class_name: str):
        formals = [p.name for p in (method.parameters or [])]
        simple = method.name
        qualified = f"{class_name}.{method.name}"
        self.analyzer.function_params[simple] = formals
        self.analyzer.function_params[qualified] = formals

    def _record_constructor_params(self, ctor, class_name: str):
        formals = [p.name for p in (ctor.parameters or [])]
        qualified = f"{class_name}.<init>"
        self.analyzer.function_params[qualified] = formals

    def _analyze_class(self, node):
        """Analyze class with full analysis including declarations, assignments, calls, returns"""
        try:
            import javalang
        except ImportError:
            return
            
        self.current_class = node.name
        self.current_scope.append(node.name)
        
        # Process fields
        for field in node.fields or []:
            for declarator in field.declarators:
                var_name = f"{self.current_class}.{declarator.name}"
                location = f"{self.analyzer.filename}:{self._get_line_number(node)}"
                self.analyzer.definitions[var_name] = location
        
        # Process methods
        for method in node.methods or []:
            self._analyze_method(method)
            
        # Process constructors  
        for constructor in node.constructors or []:
            self._analyze_constructor(constructor)
        
        self.current_scope.pop()
        self.current_class = None

    def _analyze_method(self, method):
        """Analyze method with comprehensive data flow tracking"""
        self._analyze_callable(method.name, method.body, add_to_scope=True)

    def _analyze_constructor(self, constructor):
        """Analyze constructor with comprehensive data flow tracking"""
        self._analyze_callable("<init>", constructor.body, add_to_scope=True)
    
    def _analyze_callable(self, callable_name, body, add_to_scope=True):
        """Common logic for analyzing callable bodies (methods/constructors)"""
        old_method = self.current_method
        self.current_method = callable_name
        
        if add_to_scope:
            self.current_scope.append(callable_name)
        
        # Analyze body
        if body:
            for stmt in body:
                self._analyze_java_statement(stmt)
        
        if add_to_scope:
            self.current_scope.pop()
            
        self.current_method = old_method
    
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
        """Analyze Java class with V2 features (fields + methods + constructors)."""
        old_class = self.current_class
        self.current_class = class_node.name
        self.current_scope.append(class_node.name)
        
        # Record fields as definitions (class scope)
        for field in getattr(class_node, "fields", []) or []:
            for declarator in getattr(field, "declarators", []) or []:
                var_name = f"{self.current_class}.{declarator.name}"
                location = f"{self.analyzer.filename}:{self._get_line_number(class_node)}"
                self.analyzer.definitions[var_name] = location
        
        # Analyze methods
        for method in getattr(class_node, "methods", []) or []:
            self._analyze_method(method)
        
        # Analyze constructors
        for constructor in getattr(class_node, "constructors", []) or []:
            self._analyze_constructor(constructor)
        
        self.current_scope.pop()
        self.current_class = old_class
    
    def _analyze_method(self, method):
        """Analyze Java method with comprehensive V2 features"""
        self._analyze_callable_body(method, method.name, method.parameters, method.body, include_scope=True)
    
    def _analyze_constructor(self, constructor):
        """Analyze Java constructor"""
        self._analyze_callable_body(constructor, "<init>", constructor.parameters, constructor.body, include_scope=False)
    
    def _analyze_callable_body(self, node, callable_name, parameters, body, include_scope=True):
        """Common logic for analyzing methods and constructors"""
        old_method = self.current_method
        self.current_method = callable_name
        
        # Add to scope if it's a method (not constructor)
        if include_scope:
            self.current_scope.append(callable_name)
        
        # Analyze parameters
        for param in parameters or []:
            var_name = param.name
            location = f"{self.analyzer.filename}:{self._get_line_number(param)}"
            self.analyzer.definitions[var_name] = location
            
            # V2: Add type information for parameters (only for methods, not constructors in current impl)
            if include_scope and param.type:
                type_info = self._infer_java_type(param.type)
                type_key = f"{var_name}_{self._get_line_number(param)}"
                self.analyzer.type_info[type_key] = type_info
        
        # Analyze body
        if body:
            for stmt in body:
                self._analyze_statement(stmt)
        
        # Clean up scope if it was added
        if include_scope:
            self.current_scope.pop()
        
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
                    severity="high" if effect_type in (ExitPointType.FILE_WRITE,
                                                      ExitPointType.DATABASE,
                                                      ExitPointType.NETWORK) else "medium"
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
    
    parser.add_argument("--var", required=False, help="Variable name to track")
    parser.add_argument("--file", required=True, help="Source file to analyze")
    parser.add_argument("--direction", choices=["forward", "backward"], 
                       help="Tracking direction (default: forward)")
    parser.add_argument("--max-depth", type=int, default=-1,
                       help="Maximum tracking depth (-1 for unlimited)")
    parser.add_argument("--format", choices=["text", "json", "graph"], default="text",
                       help="Output format")
    parser.add_argument("--output-reasoning-json", action="store_true",
                       help="Output AI reasoning in JSON format (for AI agents)")
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
    parser.add_argument("--explain", action="store_true",
                       help="Provide natural language explanations of analysis results")
    parser.add_argument("--output-html", action="store_true",
                       help="Generate interactive HTML visualization report")
    parser.add_argument("--html-out", help="Write HTML report to this path; if a directory, files are written inside")
    parser.add_argument("--var-all", action="store_true", help="Generate reports for all variables (batch mode)")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not getattr(args, 'var', None) and not getattr(args, 'var_all', False):
        parser.error("--var is required unless --var-all is specified.")
    if getattr(args, 'html_out', None):
        # Ensure HTML is emitted when explicit output path is provided
        args.output_html = True
    
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
    
    # Batch mode: generate per-variable reports
    if args.var_all and args.output_html:
        # Batch per-variable HTML
        all_vars = set(analyzer.definitions.keys()) | set(analyzer.dependencies.keys()) | set(analyzer.assignments.keys())
        out = args.html_out or os.getcwd()
        out_dir = out if not out.lower().endswith(".html") else os.path.dirname(out) or os.getcwd()
        os.makedirs(out_dir, exist_ok=True)
        def _san(s): return re.sub(r"[^A-Za-z0-9_.-]+", "_", s or "var")
        base = os.path.basename(args.file).replace('.', '_')
        cnt = 0
        for v in sorted(all_vars):
            if args.show_impact:
                res, a_type = analyzer.show_impact(v), "impact"
            elif args.show_calculation_path:
                res, a_type = analyzer.show_calculation_path(v), "calculation_path"
            elif args.track_state:
                res, a_type = analyzer.track_state(v), "state_tracking"
            else:
                res = analyzer.track_backward(v, args.max_depth) if args.direction == "backward" else analyzer.track_forward(v, args.max_depth)
                a_type = "standard"
            html = analyzer.generate_html_report(res, a_type, v)
            with open(os.path.join(out_dir, f"data_flow_{a_type}_{_san(v)}_{base}.html"), "w", encoding="utf-8") as f:
                f.write(html)
            cnt += 1
        print(f"📦 Batch HTML reports generated for {cnt} variables in: {out_dir}")
        return
    
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
    
    # Determine analysis type for explanations and HTML
    if args.show_impact:
        analysis_type = "impact"
    elif args.show_calculation_path:
        analysis_type = "calculation_path"
    elif args.track_state:
        analysis_type = "state_tracking"
    else:
        analysis_type = "standard"
    
    # Handle special output modes
    if args.output_html:
        # Generate interactive HTML report
        html_output = analyzer.generate_html_report(result, analysis_type, args.var)
        
        # Save to file
        safe_var = re.sub(r'[^A-Za-z0-9_.-]+', '_', args.var or 'var')
        base_file = os.path.basename(args.file).replace('.', '_')
        default_name = f"data_flow_{analysis_type}_{safe_var}_{base_file}.html"
        if args.html_out:
            out = args.html_out
            # If endswith .html, use exactly; else treat as directory
            if out.lower().endswith('.html'):
                out_path = out
            else:
                os.makedirs(out, exist_ok=True)
                out_path = os.path.join(out, default_name)
        else:
            out_path = default_name
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        print(f"📊 Interactive HTML report generated: {out_path}")
        print(f"🌐 Open in browser to explore the visualization")
        
        # Also show explanation if requested
        if args.explain:
            print("\n" + "="*60)
            print(analyzer.generate_explanation(result, analysis_type, args.var))
    
    elif args.explain:
        # Show explanation first, then formatted results
        explanation = analyzer.generate_explanation(result, analysis_type, args.var)
        print(explanation)
        print("\n" + "="*60)
        print("📋 DETAILED ANALYSIS RESULTS:")
        print("="*60)
        output = analyzer.format_output(result, args.format)
        print(output)
    
    elif args.output_reasoning_json:
        # Generate AI reasoning output
        reasoning = analyzer.generate_ai_reasoning(result, analysis_type, args.var)
        
        # If format is JSON, include reasoning in the result
        if args.format == "json":
            result["ai_reasoning"] = reasoning
            print(json.dumps(result, indent=2))
        else:
            # Output just the reasoning
            print(json.dumps(reasoning, indent=2))
    
    else:
        # Standard output
        output = analyzer.format_output(result, args.format)
        print(output)


if __name__ == "__main__":
    main()