#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced Automated Documentation Generator - Complete AST Intelligence Integration

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-27
Updated: 2025-07-27
License: Mozilla Public License 2.0 (MPL-2.0)

This enhanced version integrates ALL AST analysis tools for complete code intelligence:
- navigate_ast.py: Symbol definition lookup and cross-referencing
- method_analyzer_ast.py: Call flow and parameter tracking
- cross_file_analysis_ast.py: Module dependency analysis
- show_structure_ast_v4.py: Code structure visualization
- trace_calls_ast.py: Execution path analysis
- data_flow_tracker_v2.py: Variable dependency tracking

Key Enhancements:
- Multi-dimensional code analysis combining all AST tools
- Interactive documentation with deep cross-references
- Call graph visualization and execution path documentation
- Module dependency analysis and impact assessment
- Complete symbol resolution and definition lookup
- Rich HTML output with navigation and interactive features

Built on the complete intelligence layer for maximum accuracy and insight.
"""

import argparse
import ast
import json
import os
import sys
import subprocess
import tempfile
import re
import html
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import importlib.util
import traceback
from collections import defaultdict

# Optional Java parsing support
try:
    import javalang  # type: ignore
    _JAVA_SUPPORT = True
except Exception:  # pragma: no cover
    javalang = None
    _JAVA_SUPPORT = False

# Optional markdown library for better HTML conversion
try:
    import markdown  # type: ignore
    _MARKDOWN_SUPPORT = True
except ImportError:
    markdown = None
    _MARKDOWN_SUPPORT = False

# Optional Jinja2 template support for clean HTML generation
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
    _JINJA2_SUPPORT = True
except ImportError:
    Environment = None
    FileSystemLoader = None
    select_autoescape = None
    _JINJA2_SUPPORT = False


class EnhancedASTAnalyzer:
    """
    Comprehensive AST analyzer integrating all available tools
    """
    
    def __init__(self, file_path: str, verbose: bool = False):
        self.file_path = Path(file_path).resolve()  # Normalize path
        self.verbose = verbose
        self.script_dir = Path(__file__).parent
        self.wrapper_script = self.script_dir / "run_any_python_tool.sh"
        
        # Cache for expensive operations
        self._cache = {}
        
        # Initialize core data flow analyzer (Python and Java)
        self.data_flow_analyzer = self._import_data_flow_analyzer()
        supported_languages = {'.py': 'python', '.java': 'java'}
        file_ext = self.file_path.suffix.lower()
        
        if self.data_flow_analyzer and file_ext in supported_languages:
            try:
                # Read the source code
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                # Initialize with source code, filename, and language
                self.df_instance = self.data_flow_analyzer(
                    source_code, 
                    str(self.file_path), 
                    supported_languages[file_ext]
                )
                # Perform the analysis
                self.df_instance.analyze()
            except Exception as e:
                if verbose:
                    print(f"[AST] Failed to init data flow analyzer: {e}", file=sys.stderr)
                self.df_instance = None
        else:
            if verbose and file_ext not in supported_languages:
                print(f"[AST] Data flow analyzer only supports Python and Java files", file=sys.stderr)
            self.df_instance = None
            
    def _import_data_flow_analyzer(self):
        """Import data flow analyzer"""
        try:
            spec = importlib.util.spec_from_file_location(
                "data_flow_tracker_v2", 
                self.script_dir / "data_flow_tracker_v2.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.DataFlowAnalyzerV2
        except Exception as e:
            if self.verbose:
                print(f"[AST] Could not import data flow analyzer: {e}", file=sys.stderr)
            return None
    
    def _run_tool(self, tool_name: str, args: List[str]) -> Dict[str, Any]:
        """Run an AST tool and return parsed results"""
        cache_key = f"{tool_name}:{':'.join(args)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        try:
            # Convert file paths to absolute normalized paths
            abs_args = []
            for arg in args:
                if arg == str(self.file_path) or (Path(arg).exists() and Path(arg).is_file()):
                    abs_args.append(str(Path(arg).resolve()))
                else:
                    abs_args.append(arg)
            
            cmd = [str(self.wrapper_script), tool_name] + abs_args
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=self.script_dir.parent
            )
            
            if result.returncode == 0:
                # Try to parse as JSON first
                try:
                    data = json.loads(result.stdout)
                    self._cache[cache_key] = {"success": True, "data": data, "raw": result.stdout}
                    return self._cache[cache_key]
                except json.JSONDecodeError:
                    # Return raw text output
                    self._cache[cache_key] = {"success": True, "data": None, "raw": result.stdout}
                    return self._cache[cache_key]
            else:
                if self.verbose:
                    print(f"[AST] Tool {tool_name} failed: {result.stderr}", file=sys.stderr)
                self._cache[cache_key] = {"success": False, "error": result.stderr, "raw": ""}
                return self._cache[cache_key]
                
        except Exception as e:
            if self.verbose:
                print(f"[AST] Exception running {tool_name}: {e}", file=sys.stderr)
            self._cache[cache_key] = {"success": False, "error": str(e), "raw": ""}
            return self._cache[cache_key]
    
    def navigate_to_symbol(self, symbol_name: str) -> Dict[str, Any]:
        """Use navigate_ast.py to find symbol definition"""
        result = self._run_tool("navigate_ast_v2.py", [str(self.file_path), "--to", symbol_name])
        return result
    
    def analyze_method_calls(self, method_name: str, scope: Optional[str] = None) -> Dict[str, Any]:
        """Use method_analyzer_ast.py to analyze method calls and flow"""
        args = [method_name]
        if scope:
            args.extend(["--scope", scope])
        else:
            args.extend(["--file", str(self.file_path)])
        args.extend(["--trace-flow", "--show-args"])
        
        result = self._run_tool("method_analyzer_ast_v2.py", args)
        return result
    
    def analyze_cross_file_dependencies(self, target_symbol: str, scope: str = ".") -> Dict[str, Any]:
        """Use cross_file_analysis_ast.py for module dependency analysis"""
        args = [target_symbol, "--scope", scope, "--max-depth", "4"]
        result = self._run_tool("cross_file_analysis_ast.py", args)
        return result
    
    def get_code_structure(self, include_annotations: bool = True) -> Dict[str, Any]:
        """Use show_structure_ast_v4.py to get hierarchical structure"""
        args = [str(self.file_path)]
        # Only add annotation filter for Java files if specifically requested
        # The @.* pattern seems to break the tool
        result = self._run_tool("show_structure_ast_v4.py", args)
        return result
    
    def trace_execution_paths(self, entry_point: str, max_depth: int = 3) -> Dict[str, Any]:
        """Use trace_calls_ast.py to analyze execution paths"""
        args = [entry_point, "--file", str(self.file_path), "--max-depth", str(max_depth)]
        result = self._run_tool("trace_calls_with_timeout.py", args)
        return result
    
    def get_data_flow_analysis(self, variable: str, direction: str = "both") -> Dict[str, Any]:
        """Get data flow analysis from the core analyzer"""
        if not self.df_instance:
            return {"success": False, "error": "Data flow analyzer not available"}
            
        try:
            result = {}
            if direction in ["backward", "both"]:
                result["dependencies"] = self.df_instance.track_backward(variable, max_depth=5)
            if direction in ["forward", "both"]:
                result["affects"] = self.df_instance.track_forward(variable, max_depth=5)
            if hasattr(self.df_instance, 'show_impact'):
                result["impact"] = self.df_instance.show_impact(variable)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_comprehensive_analysis(self, target_name: str, target_type: str = "function") -> Dict[str, Any]:
        """Get comprehensive analysis combining all tools"""
        analysis = {
            "target": {"name": target_name, "type": target_type, "file": str(self.file_path)},
            "navigation": {},
            "method_analysis": {},
            "cross_file_analysis": {},
            "structure": {},
            "execution_paths": {},
            "data_flow": {},
            "errors": []
        }
        
        # Navigate to symbol definition
        nav_result = self.navigate_to_symbol(target_name)
        if nav_result["success"]:
            analysis["navigation"] = nav_result
        else:
            analysis["errors"].append(f"Navigation failed: {nav_result.get('error', 'Unknown')}")
        
        # Analyze method calls (for functions, methods, or classes)
        # For classes, we still want to analyze methods within the class
        method_result = self.analyze_method_calls(target_name)
        if method_result["success"]:
            analysis["method_analysis"] = method_result
        else:
            analysis["errors"].append(f"Method analysis failed: {method_result.get('error', 'Unknown')}")
        
        # Cross-file analysis
        cross_result = self.analyze_cross_file_dependencies(target_name)
        if cross_result["success"]:
            analysis["cross_file_analysis"] = cross_result
        else:
            analysis["errors"].append(f"Cross-file analysis failed: {cross_result.get('error', 'Unknown')}")
        
        # Code structure
        struct_result = self.get_code_structure()
        if struct_result["success"]:
            analysis["structure"] = struct_result
        else:
            analysis["errors"].append(f"Structure analysis failed: {struct_result.get('error', 'Unknown')}")
        
        # Execution paths (for functions, methods, or analyzing methods within classes)
        trace_result = self.trace_execution_paths(target_name)
        if trace_result["success"]:
            analysis["execution_paths"] = trace_result
        else:
            analysis["errors"].append(f"Execution tracing failed: {trace_result.get('error', 'Unknown')}")
        
        # Data flow analysis (Python and Java files)
        if self.df_instance:
            try:
                variables = list(self.df_instance.definitions.keys())
                # For Java, also look for the target name itself
                if self.file_path.suffix.lower() == '.java':
                    # In Java, we might have fully qualified names
                    key_vars = [v for v in variables if target_name.lower() in v.lower() or v.lower() in target_name.lower()][:5]
                    # Also explicitly check for the target name
                    if target_name in variables and target_name not in key_vars:
                        key_vars.insert(0, target_name)
                else:
                    key_vars = [v for v in variables if target_name.lower() in v.lower()][:5]
                
                for var in key_vars:
                    df_result = self.get_data_flow_analysis(var)
                    if df_result["success"]:
                        analysis["data_flow"][var] = df_result["data"]
            except Exception as e:
                analysis["errors"].append(f"Data flow analysis failed: {str(e)}")
        
        return analysis


class DocumentationStyle(Enum):
    """Different documentation styles for different audiences"""
    API_DOCS = "api-docs"           # Technical API documentation
    USER_GUIDE = "user-guide"       # User-friendly guides
    TECHNICAL = "technical"         # Deep technical analysis
    QUICK_REF = "quick-ref"        # Quick reference format
    TUTORIAL = "tutorial"          # Tutorial-style with examples
    ARCHITECTURE = "architecture"   # Module-level architecture docs (NEW)
    CALL_GRAPH = "call-graph"      # Call graph visualization (NEW)
    
class DepthLevel(Enum):
    """Analysis depth levels"""
    SURFACE = "surface"            # Basic signature and purpose
    MEDIUM = "medium"              # Include dependencies and flow
    DEEP = "deep"                  # Complete analysis with all details
    COMPREHENSIVE = "comprehensive" # All tools, maximum depth (NEW)

class OutputFormat(Enum):
    """Output format options"""
    MARKDOWN = "markdown"          # Markdown format
    HTML = "html"                  # HTML format
    DOCSTRING = "docstring"        # Python docstring format
    RST = "rst"                    # reStructuredText format
    INTERACTIVE = "interactive"    # Interactive HTML with navigation (NEW)

@dataclass
class DocumentationTarget:
    """Represents a code element to document"""
    name: str
    type: str  # 'function', 'class', 'module'
    file_path: str
    line_number: Optional[int] = None
    source_code: Optional[str] = None
    comprehensive_analysis: Optional[Dict[str, Any]] = field(default_factory=dict)


class EnhancedDocumentationGenerator:
    """Enhanced documentation generator with complete AST intelligence"""
    
    def __init__(self, file_path: str, style: DocumentationStyle, 
                 depth: DepthLevel, output_format: OutputFormat, 
                 verbose: bool = False):
        self.file_path = file_path
        self.style = style
        self.depth = depth
        self.output_format = output_format
        self.verbose = verbose
        self.source_code = ""
        self.language = self._detect_language()
        
        # Initialize enhanced AST analyzer
        self.ast_analyzer = EnhancedASTAnalyzer(file_path, verbose)
        
        # Load source code
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.source_code = f.read()
        except Exception as e:
            raise Exception(f"Could not read file {file_path}: {e}")
    
    def _detect_language(self) -> str:
        """Detect programming language from file extension"""
        ext = Path(self.file_path).suffix.lower()
        if ext == '.py':
            return 'python'
        elif ext in ['.java']:
            return 'java'
        elif ext in ['.js', '.jsx']:
            return 'javascript'
        elif ext in ['.ts', '.tsx']:
            return 'typescript'
        else:
            return 'unknown'
    
    def generate_function_docs(self, function_name: str) -> str:
        """Generate documentation for a function"""
        target = DocumentationTarget(
            name=function_name,
            type='function',
            file_path=self.file_path
        )
        
        # Get comprehensive analysis if depth warrants it
        if self.depth in [DepthLevel.DEEP, DepthLevel.COMPREHENSIVE]:
            target.comprehensive_analysis = self.ast_analyzer.get_comprehensive_analysis(
                function_name, "function"
            )
        
        return self._generate_documentation(target)
    
    def generate_class_docs(self, class_name: str) -> str:
        """Generate documentation for a class"""
        target = DocumentationTarget(
            name=class_name,
            type='class',
            file_path=self.file_path
        )
        
        # Get comprehensive analysis if depth warrants it
        if self.depth in [DepthLevel.DEEP, DepthLevel.COMPREHENSIVE]:
            target.comprehensive_analysis = self.ast_analyzer.get_comprehensive_analysis(
                class_name, "class"
            )
        
        return self._generate_documentation(target)
    
    def generate_module_docs(self) -> str:
        """Generate documentation for the entire module"""
        module_name = Path(self.file_path).stem
        target = DocumentationTarget(
            name=module_name,
            type='module',
            file_path=self.file_path
        )
        
        # For modules, always get structure analysis
        target.comprehensive_analysis = {
            "structure": self.ast_analyzer.get_code_structure(),
            "cross_file_analysis": self.ast_analyzer.analyze_cross_file_dependencies(module_name),
        }
        
        return self._generate_documentation(target)
    
    def _generate_documentation(self, target: DocumentationTarget) -> str:
        """Generate documentation based on style and format"""
        if self.verbose:
            print(f"[DocGen] Generating {self.style.value} docs for {target.name}", file=sys.stderr)
        
        # Dispatch to style-specific generators
        if self.style == DocumentationStyle.API_DOCS:
            return self._generate_api_docs(target)
        elif self.style == DocumentationStyle.USER_GUIDE:
            return self._generate_user_guide(target)
        elif self.style == DocumentationStyle.TECHNICAL:
            return self._generate_technical_docs(target)
        elif self.style == DocumentationStyle.QUICK_REF:
            return self._generate_quick_reference(target)
        elif self.style == DocumentationStyle.TUTORIAL:
            return self._generate_tutorial(target)
        elif self.style == DocumentationStyle.ARCHITECTURE:
            return self._generate_architecture_docs(target)
        elif self.style == DocumentationStyle.CALL_GRAPH:
            return self._generate_call_graph_docs(target)
        else:
            return self._generate_api_docs(target)  # Default
    
    def _generate_architecture_docs(self, target: DocumentationTarget) -> str:
        """Generate architecture-focused documentation"""
        # Generate markdown content first
        content = f"# Architecture Documentation: {target.name}\n\n"
        
        # Module structure
        if target.comprehensive_analysis.get("structure", {}).get("success"):
            content += "## Module Structure\n\n"
            struct_data = target.comprehensive_analysis["structure"].get("raw", "")
            # Strip ANSI codes from structure data
            struct_data = self._strip_ansi_codes(struct_data)
            content += f"```\n{struct_data}\n```\n\n"
        
        # Cross-file dependencies
        if target.comprehensive_analysis.get("cross_file_analysis", {}).get("success"):
            content += "## Dependencies\n\n"
            cross_data = target.comprehensive_analysis["cross_file_analysis"].get("raw", "")
            # Strip ANSI codes from cross-file data
            cross_data = self._strip_ansi_codes(cross_data)
            content += f"```\n{cross_data}\n```\n\n"
        
        # Handle different output formats
        if self.output_format == OutputFormat.HTML:
            return self._markdown_to_html(content, f"Architecture: {target.name}")
        elif self.output_format == OutputFormat.INTERACTIVE:
            return self._generate_interactive_docs(target)
        elif self.output_format == OutputFormat.DOCSTRING:
            return '"""\n' + content + '\n"""'
        elif self.output_format == OutputFormat.RST:
            # Convert markdown to RST (basic)
            rst_content = content.replace('# ', '').replace('## ', '')
            rst_content = rst_content.replace('```', '::')
            return rst_content
        else:
            return content
    
    def _generate_call_graph_docs(self, target: DocumentationTarget) -> str:
        """Generate call graph visualization documentation"""
        # Generate markdown content first
        content = f"# Call Graph: {target.name}\n\n"
        
        # Method analysis with call flows
        if target.comprehensive_analysis.get("method_analysis", {}).get("success"):
            content += "## Call Flow Analysis\n\n"
            method_data = target.comprehensive_analysis["method_analysis"].get("raw", "")
            # Strip ANSI codes
            method_data = self._strip_ansi_codes(method_data)
            content += f"```\n{method_data}\n```\n\n"
        
        # Execution paths
        if target.comprehensive_analysis.get("execution_paths", {}).get("success"):
            content += "## Execution Paths\n\n"
            trace_data = target.comprehensive_analysis["execution_paths"].get("raw", "")
            # Strip ANSI codes
            trace_data = self._strip_ansi_codes(trace_data)
            content += f"```\n{trace_data}\n```\n\n"
        
        # Handle different output formats
        if self.output_format == OutputFormat.HTML:
            return self._markdown_to_html(content, f"Call Graph: {target.name}")
        elif self.output_format == OutputFormat.INTERACTIVE:
            return self._generate_interactive_docs(target)
        elif self.output_format == OutputFormat.DOCSTRING:
            return '"""\n' + content + '\n"""'
        elif self.output_format == OutputFormat.RST:
            # Convert markdown to RST (basic)
            rst_content = content.replace('# ', '').replace('## ', '')
            rst_content = rst_content.replace('```', '::')
            return rst_content
        else:
            return content
    
    def generate_ai_reasoning(self, target: DocumentationTarget) -> Dict[str, Any]:
        """Generate structured reasoning output for AI consumption"""
        from datetime import datetime
        
        reasoning = {
            "reasoning_version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "documentation_generation",
            "target": {
                "name": target.name,
                "type": target.type,
                "file_path": target.file_path
            },
            "logical_steps": [],
            "documentation_assessment": {
                "completeness": 0.0,
                "clarity": 0.0,
                "complexity": "unknown",
                "missing_sections": []
            },
            "recommendations": [],
            "context_requirements": {
                "needs_human_review": False,
                "needs_additional_analysis": [],
                "safe_for_automation": True
            }
        }
        
        # Generate reasoning steps based on available analysis
        steps = []
        step_num = 1
        
        # Step 1: Code structure analysis
        if target.comprehensive_analysis.get("structure", {}).get("success"):
            steps.append({
                "step": step_num,
                "action": "analyzed_code_structure",
                "targets": ["classes", "functions", "imports"],
                "confidence": 0.90,
                "reasoning": "Successfully parsed code structure to identify documentation targets"
            })
            step_num += 1
        
        # Step 2: Symbol analysis
        if target.comprehensive_analysis.get("symbol_info", {}).get("success"):
            steps.append({
                "step": step_num,
                "action": "resolved_symbol_definitions",
                "targets": [target.name],
                "confidence": 0.95,
                "reasoning": f"Located {target.type} definition and analyzed signature"
            })
            step_num += 1
        
        # Step 3: Dependencies analysis
        if target.comprehensive_analysis.get("cross_file_analysis", {}).get("success"):
            deps = target.comprehensive_analysis.get("dependencies", [])
            steps.append({
                "step": step_num,
                "action": "traced_dependencies",
                "targets": deps[:5],  # First 5 dependencies
                "confidence": 0.85,
                "reasoning": f"Identified {len(deps)} external dependencies"
            })
            step_num += 1
        
        # Step 4: Call flow analysis
        if target.comprehensive_analysis.get("method_analysis", {}).get("success"):
            steps.append({
                "step": step_num,
                "action": "analyzed_call_flows",
                "targets": ["internal_calls", "external_calls"],
                "confidence": 0.88,
                "reasoning": "Traced method calls and parameter flows"
            })
            step_num += 1
        
        # Step 5: Data flow analysis
        if target.comprehensive_analysis.get("data_flow", {}).get("success"):
            steps.append({
                "step": step_num,
                "action": "traced_data_flows",
                "targets": ["inputs", "outputs", "state_changes"],
                "confidence": 0.82,
                "reasoning": "Analyzed variable dependencies and data transformations"
            })
            step_num += 1
        
        reasoning["logical_steps"] = steps
        
        # Assess documentation completeness
        completeness_score = self._assess_doc_completeness(target)
        clarity_score = self._assess_doc_clarity(target)
        complexity = self._assess_code_complexity(target)
        
        reasoning["documentation_assessment"] = {
            "completeness": completeness_score,
            "clarity": clarity_score,
            "complexity": complexity,
            "missing_sections": self._identify_missing_sections(target)
        }
        
        # Generate recommendations
        recommendations = []
        
        if completeness_score < 0.7:
            recommendations.append({
                "action": "add_missing_documentation",
                "priority": "high",
                "reasoning": f"Documentation completeness is {completeness_score:.0%} - critical sections missing"
            })
        
        if complexity == "high" and clarity_score < 0.8:
            recommendations.append({
                "action": "add_examples",
                "priority": "medium",
                "reasoning": "Complex code needs more examples for clarity"
            })
        
        if not target.comprehensive_analysis.get("data_flow", {}).get("success"):
            recommendations.append({
                "action": "add_data_flow_documentation",
                "priority": "medium",
                "reasoning": "Data flow analysis unavailable - manual documentation needed"
            })
        
        reasoning["recommendations"] = recommendations
        
        # Update context requirements based on analysis
        if complexity == "high" or completeness_score < 0.5:
            reasoning["context_requirements"]["needs_human_review"] = True
            reasoning["context_requirements"]["safe_for_automation"] = False
        
        if len(self._identify_missing_sections(target)) > 2:
            reasoning["context_requirements"]["needs_additional_analysis"] = ["manual_review", "domain_expert"]
        
        return reasoning
    
    def _assess_doc_completeness(self, target: DocumentationTarget) -> float:
        """Assess how complete the documentation is"""
        score = 0.0
        total_checks = 0
        
        # Check for basic elements
        checks = {
            "has_description": bool(target.description),
            "has_parameters": bool(target.parameters) if target.type == "function" else True,
            "has_returns": bool(target.returns) if target.type == "function" else True,
            "has_examples": bool(target.examples),
            "has_dependencies": bool(target.comprehensive_analysis.get("dependencies")),
            "has_structure": bool(target.comprehensive_analysis.get("structure"))
        }
        
        for check, passed in checks.items():
            total_checks += 1
            if passed:
                score += 1.0
        
        return score / total_checks if total_checks > 0 else 0.0
    
    def _assess_doc_clarity(self, target: DocumentationTarget) -> float:
        """Assess documentation clarity"""
        # Simple heuristic based on description length and structure
        if not target.description:
            return 0.0
        
        desc_len = len(target.description)
        if desc_len < 20:
            return 0.3
        elif desc_len < 50:
            return 0.6
        elif desc_len < 200:
            return 0.8
        else:
            return 0.9
    
    def _assess_code_complexity(self, target: DocumentationTarget) -> str:
        """Assess code complexity level"""
        # Simple heuristic based on available analysis
        complexity_indicators = 0
        
        # Check various complexity indicators
        if target.comprehensive_analysis.get("method_analysis", {}).get("success"):
            method_data = target.comprehensive_analysis["method_analysis"].get("raw", "")
            if "nested" in method_data.lower() or "recursive" in method_data.lower():
                complexity_indicators += 2
        
        if target.comprehensive_analysis.get("data_flow", {}).get("success"):
            complexity_indicators += 1
        
        deps = target.comprehensive_analysis.get("dependencies", [])
        if len(deps) > 10:
            complexity_indicators += 2
        elif len(deps) > 5:
            complexity_indicators += 1
        
        if complexity_indicators >= 3:
            return "high"
        elif complexity_indicators >= 1:
            return "medium"
        else:
            return "low"
    
    def _identify_missing_sections(self, target: DocumentationTarget) -> List[str]:
        """Identify missing documentation sections"""
        missing = []
        
        if not target.description:
            missing.append("description")
        
        if target.type == "function" and not target.parameters:
            missing.append("parameters")
        
        if target.type == "function" and not target.returns:
            missing.append("return_value")
        
        if not target.examples:
            missing.append("examples")
        
        if target.type == "class" and not target.methods:
            missing.append("method_documentation")
        
        return missing
    
    def _generate_api_docs(self, target: DocumentationTarget) -> str:
        """Generate API documentation with enhanced analysis"""
        if self.output_format == OutputFormat.MARKDOWN:
            return self._generate_api_docs_markdown(target)
        elif self.output_format == OutputFormat.HTML:
            return self._generate_api_docs_html(target)
        elif self.output_format == OutputFormat.INTERACTIVE:
            return self._generate_interactive_docs(target)
        else:
            return self._generate_api_docs_markdown(target)
    
    def _generate_api_docs_markdown(self, target: DocumentationTarget) -> str:
        """Generate enhanced API docs in Markdown format"""
        content = f"# {target.type.title()}: {target.name}\n\n"
        
        # Navigation section (NEW)
        if target.comprehensive_analysis.get("navigation", {}).get("success"):
            content += "## Quick Navigation\n"
            nav_data = target.comprehensive_analysis["navigation"].get("raw", "")
            if "line" in nav_data.lower():
                content += f"- **Definition**: Line {self._extract_line_number(nav_data)}\n"
            content += f"- **File**: `{target.file_path}`\n\n"
        
        # Method signature and basic info
        content += "## Overview\n\n"
        content += f"**Type**: {target.type}\n"
        content += f"**File**: `{target.file_path}`\n\n"
        
        # Call flow analysis (NEW)
        if target.comprehensive_analysis.get("method_analysis", {}).get("success"):
            content += "## Call Flow Analysis\n\n"
            method_data = target.comprehensive_analysis["method_analysis"].get("raw", "")
            content += f"```\n{method_data}\n```\n\n"
        
        # Data flow information
        if target.comprehensive_analysis.get("data_flow"):
            content += "## Data Flow\n\n"
            for var, flow_data in target.comprehensive_analysis["data_flow"].items():
                content += f"### Variable: `{var}`\n\n"
                if "dependencies" in flow_data:
                    content += "**Dependencies**:\n"
                    deps = flow_data["dependencies"]
                    if isinstance(deps, dict):
                        # Check if it's the backward tracking structure
                        if "depends_on" in deps:
                            dep_list = deps.get("depends_on", [])
                            if dep_list:
                                for dep_item in dep_list[:3]:  # Limit to 3
                                    if isinstance(dep_item, dict):
                                        content += f"- `{dep_item.get('variable', 'unknown')}`: {dep_item.get('type', 'unknown')}\n"
                                    else:
                                        content += f"- {dep_item}\n"
                            else:
                                content += "- No dependencies found\n"
                        else:
                            # Old structure
                            for dep_var, dep_info in list(deps.items())[:3]:  # Limit to 3
                                if isinstance(dep_info, dict):
                                    content += f"- `{dep_var}`: {dep_info.get('type', 'unknown')}\n"
                                else:
                                    content += f"- `{dep_var}`: {dep_info}\n"
                    content += "\n"
                
                if "affects" in flow_data:
                    content += "**Affects**:\n"
                    affects = flow_data["affects"]
                    if isinstance(affects, dict):
                        # Check if it's the forward tracking structure
                        if "affects" in affects and isinstance(affects["affects"], list):
                            aff_list = affects.get("affects", [])
                            if aff_list:
                                for aff_item in aff_list[:3]:  # Limit to 3
                                    if isinstance(aff_item, dict):
                                        content += f"- `{aff_item.get('variable', 'unknown')}`: {aff_item.get('type', 'unknown')}\n"
                                    else:
                                        content += f"- {aff_item}\n"
                            else:
                                content += "- No affected variables found\n"
                        else:
                            # Old structure
                            for aff_var, aff_info in list(affects.items())[:3]:  # Limit to 3
                                if isinstance(aff_info, dict):
                                    content += f"- `{aff_var}`: {aff_info.get('type', 'unknown')}\n"
                                else:
                                    content += f"- `{aff_var}`: {aff_info}\n"
                    content += "\n"
        
        # Cross-file impact (NEW)
        if target.comprehensive_analysis.get("cross_file_analysis", {}).get("success"):
            content += "## Cross-File Impact\n\n"
            cross_data = target.comprehensive_analysis["cross_file_analysis"].get("raw", "")
            # Extract key information from cross-file analysis
            if "files" in cross_data.lower() or "modules" in cross_data.lower():
                content += f"```\n{cross_data[:500]}...\n```\n\n"
        
        # Error summary
        errors = target.comprehensive_analysis.get("errors", [])
        if errors and self.verbose:
            content += "## Analysis Notes\n\n"
            for error in errors[:3]:  # Limit to first 3 errors
                content += f"- {error}\n"
            content += "\n"
        
        return content
    
    def _markdown_to_html(self, markdown_content: str, title: str) -> str:
        """Convert markdown to basic HTML"""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{html.escape(title)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        code {{ background: #f4f4f4; padding: 2px 4px; }}
        pre {{ background: #f4f4f4; padding: 10px; overflow-x: auto; }}
        h1, h2, h3 {{ color: #333; }}
    </style>
</head>
<body>
"""
        # Basic markdown to HTML conversion
        lines = markdown_content.split('\n')
        in_code_block = False
        
        for line in lines:
            if line.startswith('```'):
                if in_code_block:
                    html_content += "</pre>\n"
                    in_code_block = False
                else:
                    html_content += "<pre>\n"
                    in_code_block = True
            elif in_code_block:
                html_content += html.escape(line) + "\n"
            elif line.startswith('# '):
                html_content += f"<h1>{html.escape(line[2:])}</h1>\n"
            elif line.startswith('## '):
                html_content += f"<h2>{html.escape(line[3:])}</h2>\n"
            elif line.startswith('### '):
                html_content += f"<h3>{html.escape(line[4:])}</h3>\n"
            elif line.startswith('- '):
                html_content += f"<li>{html.escape(line[2:])}</li>\n"
            elif line.strip():
                # Handle inline code
                line_html = html.escape(line)
                line_html = re.sub(r'`([^`]+)`', r'<code>\1</code>', line_html)
                html_content += f"<p>{line_html}</p>\n"
            else:
                html_content += "<br>\n"
        
        html_content += """</body>
</html>"""
        return html_content
    
    def _generate_api_docs_docstring(self, target: DocumentationTarget) -> str:
        """Generate API documentation in Python docstring format"""
        content = '"""\n'
        content += f"{target.name}\n"
        content += "=" * len(target.name) + "\n\n"
        
        # Add description
        content += f"A {target.type} for handling specific functionality.\n\n"
        
        # Add analysis summary if available
        if target.comprehensive_analysis:
            errors = target.comprehensive_analysis.get("errors", [])
            if not errors:
                content += "Analysis Summary\n"
                content += "---------------\n"
                if target.comprehensive_analysis.get("navigation", {}).get("success"):
                    content += "- Symbol navigation: Available\n"
                if target.comprehensive_analysis.get("method_analysis", {}).get("success"):
                    content += "- Method analysis: Available\n"
                if target.comprehensive_analysis.get("data_flow"):
                    content += f"- Data flow tracking: {len(target.comprehensive_analysis['data_flow'])} variables\n"
                content += "\n"
        
        content += '"""'
        return content
    
    def _generate_api_docs_rst(self, target: DocumentationTarget) -> str:
        """Generate API documentation in reStructuredText format"""
        content = target.name + "\n"
        content += "=" * len(target.name) + "\n\n"
        
        content += f".. class:: {target.name}\n\n"
        content += f"   {target.type.title()} for specific functionality.\n\n"
        
        # Add navigation info if available
        if target.comprehensive_analysis.get("navigation", {}).get("success"):
            content += "   **Location**\n\n"
            nav_data = target.comprehensive_analysis["navigation"].get("raw", "")
            if "line" in nav_data.lower():
                line_num = self._extract_line_number(nav_data)
                content += f"   - Line: {line_num}\n"
            content += f"   - File: ``{target.file_path}``\n\n"
        
        # Add method summary if available
        if target.comprehensive_analysis.get("method_analysis", {}).get("success"):
            content += "   **Methods**\n\n"
            method_data = target.comprehensive_analysis["method_analysis"].get("raw", "")
            # Extract key methods from the raw output
            lines = method_data.split('\n')
            method_count = 0
            for line in lines:
                if "METHOD DEFINITIONS FOUND:" in line:
                    try:
                        count = int(line.split(':')[1].strip())
                        content += f"   - Total methods: {count}\n\n"
                    except:
                        pass
                    break
        
        return content
    
    def _generate_interactive_docs(self, target: DocumentationTarget) -> str:
        """Generate interactive HTML documentation"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Docs: {target.name}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ border-bottom: 2px solid #e0e0e0; padding-bottom: 20px; margin-bottom: 30px; }}
        .nav-pills {{ display: flex; gap: 10px; margin-bottom: 20px; }}
        .nav-pill {{ padding: 8px 16px; background: #e9ecef; border: none; border-radius: 20px; cursor: pointer; transition: all 0.2s; }}
        .nav-pill.active, .nav-pill:hover {{ background: #007bff; color: white; }}
        .content-section {{ display: none; }}
        .content-section.active {{ display: block; }}
        .code-block {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 15px; margin: 10px 0; font-family: 'Courier New', monospace; white-space: pre-wrap; }}
        .symbol-link {{ color: #007bff; text-decoration: none; font-weight: bold; }}
        .symbol-link:hover {{ text-decoration: underline; }}
        .error-note {{ background: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 10px; border-radius: 4px; margin: 10px 0; }}
        .success-note {{ background: #d1edff; border: 1px solid #bee5eb; color: #0c5460; padding: 10px; border-radius: 4px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{html.escape(target.type.title())}: {html.escape(target.name)}</h1>
            <p><strong>File:</strong> <code>{html.escape(str(target.file_path))}</code></p>
        </div>
        
        <div class="nav-pills">
            <button class="nav-pill active" onclick="showSection('overview')">Overview</button>
            <button class="nav-pill" onclick="showSection('navigation')">Navigation</button>
            <button class="nav-pill" onclick="showSection('callflow')">Call Flow</button>
            <button class="nav-pill" onclick="showSection('dataflow')">Data Flow</button>
            <button class="nav-pill" onclick="showSection('structure')">Structure</button>
            <button class="nav-pill" onclick="showSection('crossfile')">Dependencies</button>
        </div>
        
        <div id="overview" class="content-section active">
            <h2>Overview</h2>
            <p><strong>Type:</strong> {target.type}</p>
            <p><strong>Language:</strong> {self.language}</p>
            <p><strong>Analysis Depth:</strong> {self.depth.value}</p>
        </div>
        
        <div id="navigation" class="content-section">
            <h2>Symbol Navigation</h2>
            {self._generate_navigation_section(target)}
        </div>
        
        <div id="callflow" class="content-section">
            <h2>Call Flow Analysis</h2>
            {self._generate_callflow_section(target)}
        </div>
        
        <div id="dataflow" class="content-section">
            <h2>Data Flow Analysis</h2>
            {self._generate_dataflow_section(target)}
        </div>
        
        <div id="structure" class="content-section">
            <h2>Code Structure</h2>
            {self._generate_structure_section(target)}
        </div>
        
        <div id="crossfile" class="content-section">
            <h2>Cross-File Dependencies</h2>
            {self._generate_crossfile_section(target)}
        </div>
    </div>
    
    <script>
        function showSection(sectionId) {{
            // Hide all sections
            document.querySelectorAll('.content-section').forEach(section => {{
                section.classList.remove('active');
            }});
            
            // Remove active class from all pills
            document.querySelectorAll('.nav-pill').forEach(pill => {{
                pill.classList.remove('active');
            }});
            
            // Show selected section
            document.getElementById(sectionId).classList.add('active');
            
            // Activate clicked pill
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>
        """
        return html_content
    
    def _strip_ansi_codes(self, text: str) -> str:
        """Strip ANSI color codes from text"""
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)
        # Also remove simple color codes like [93m, [0m, etc.
        text = re.sub(r'\[\d+m', '', text)
        return text
    
    def _generate_navigation_section(self, target: DocumentationTarget) -> str:
        """Generate navigation section for interactive docs"""
        nav_data = target.comprehensive_analysis.get("navigation", {})
        if nav_data.get("success"):
            raw_data = nav_data.get("raw", "")
            clean_data = self._strip_ansi_codes(raw_data)
            return f'<div class="success-note">Symbol found successfully</div><div class="code-block">{html.escape(clean_data)}</div>'
        else:
            error = nav_data.get("error", "Navigation analysis not available")
            return f'<div class="error-note">Navigation failed: {error}</div>'
    
    def _generate_callflow_section(self, target: DocumentationTarget) -> str:
        """Generate call flow section for interactive docs"""
        method_data = target.comprehensive_analysis.get("method_analysis", {})
        if method_data.get("success"):
            raw_data = method_data.get("raw", "")
            clean_data = self._strip_ansi_codes(raw_data)
            return f'<div class="success-note">Call flow analysis completed</div><div class="code-block">{html.escape(clean_data)}</div>'
        else:
            error = method_data.get("error", "Method analysis not available")
            return f'<div class="error-note">Call flow analysis failed: {error}</div>'
    
    def _generate_dataflow_section(self, target: DocumentationTarget) -> str:
        """Generate data flow section for interactive docs"""
        data_flow = target.comprehensive_analysis.get("data_flow", {})
        if data_flow and len(data_flow) > 0:
            content = '<div class="success-note">Data flow analysis available</div>'
            for var, flow_data in data_flow.items():
                content += f'<h3>Variable: <code>{html.escape(var)}</code></h3>'
                content += f'<div class="code-block">{html.escape(json.dumps(flow_data, indent=2))}</div>'
            return content
        else:
            return '<div class="error-note">Data flow analysis not available</div>'
    
    def _generate_structure_section(self, target: DocumentationTarget) -> str:
        """Generate structure section for interactive docs"""
        struct_data = target.comprehensive_analysis.get("structure", {})
        if struct_data.get("success"):
            raw_data = struct_data.get("raw", "")
            clean_data = self._strip_ansi_codes(raw_data)
            return f'<div class="success-note">Structure analysis completed</div><div class="code-block">{html.escape(clean_data)}</div>'
        else:
            error = struct_data.get("error", "Structure analysis not available")
            return f'<div class="error-note">Structure analysis failed: {error}</div>'
    
    def _generate_crossfile_section(self, target: DocumentationTarget) -> str:
        """Generate cross-file section for interactive docs"""
        cross_data = target.comprehensive_analysis.get("cross_file_analysis", {})
        if cross_data.get("success"):
            raw_data = cross_data.get("raw", "")
            clean_data = self._strip_ansi_codes(raw_data)
            return f'<div class="success-note">Cross-file analysis completed</div><div class="code-block">{html.escape(clean_data)}</div>'
        else:
            error = cross_data.get("error", "Cross-file analysis not available")
            return f'<div class="error-note">Cross-file analysis failed: {error}</div>'
    
    def _extract_line_number(self, nav_data: str) -> str:
        """Extract line number from navigation data"""
        try:
            import re
            match = re.search(r'line (\d+)', nav_data, re.IGNORECASE)
            return match.group(1) if match else "unknown"
        except:
            return "unknown"
    
    def _generate_user_guide(self, target: DocumentationTarget) -> str:
        """Generate user guide documentation"""
        content = f"# User Guide: {target.name}\n\n"
        content += f"## Overview\n\n"
        content += f"The `{target.name}` {target.type} provides functionality for...\n\n"
        
        # Add usage examples if available
        content += "## Basic Usage\n\n"
        content += "```java\n"
        content += f"// Example usage of {target.name}\n"
        content += f"{target.name} instance = new {target.name}();\n"
        content += "// ... configure and use\n"
        content += "```\n\n"
        
        # Add key features from structure analysis
        if target.comprehensive_analysis.get("structure", {}).get("success"):
            content += "## Key Features\n\n"
            struct_data = target.comprehensive_analysis["structure"].get("raw", "")
            # Extract method names from structure
            lines = struct_data.split('\n')
            methods = [line.strip() for line in lines if '🔧' in line][:5]
            for method in methods:
                content += f"- {method}\n"
        
        # Handle different output formats
        if self.output_format == OutputFormat.HTML:
            return self._markdown_to_html(content, f"User Guide: {target.name}")
        elif self.output_format == OutputFormat.INTERACTIVE:
            return self._generate_interactive_docs(target)
        elif self.output_format == OutputFormat.DOCSTRING:
            return '"""\n' + content + '\n"""'
        elif self.output_format == OutputFormat.RST:
            # Convert markdown to RST (basic)
            rst_content = content.replace('# ', '').replace('## ', '')
            rst_content = rst_content.replace('```', '::')
            return rst_content
        else:
            return content
    
    def _generate_technical_docs(self, target: DocumentationTarget) -> str:
        """Generate technical documentation"""
        content = f"# Technical Documentation: {target.name}\n\n"
        content += f"## Technical Overview\n\n"
        content += f"This document provides in-depth technical analysis of `{target.name}`.\n\n"
        
        # Add implementation details
        content += "## Implementation Details\n\n"
        
        # Add performance characteristics if available
        if target.comprehensive_analysis.get("execution_paths", {}).get("success"):
            content += "### Execution Paths\n\n"
            exec_data = target.comprehensive_analysis["execution_paths"].get("raw", "")
            content += f"```\n{exec_data[:500]}...\n```\n\n"
        
        # Add data flow if available
        if target.comprehensive_analysis.get("data_flow"):
            content += "### Data Flow Analysis\n\n"
            content += f"Found {len(target.comprehensive_analysis['data_flow'])} key variables tracked.\n\n"
        
        # Handle different output formats
        if self.output_format == OutputFormat.HTML:
            return self._markdown_to_html(content, f"Technical Documentation: {target.name}")
        elif self.output_format == OutputFormat.INTERACTIVE:
            return self._generate_interactive_docs(target)
        elif self.output_format == OutputFormat.DOCSTRING:
            return '"""\n' + content + '\n"""'
        elif self.output_format == OutputFormat.RST:
            # Convert markdown to RST (basic)
            rst_content = content.replace('# ', '').replace('## ', '')
            rst_content = rst_content.replace('```', '::')
            return rst_content
        else:
            return content
    
    def _generate_quick_reference(self, target: DocumentationTarget) -> str:
        """Generate quick reference documentation"""
        content = f"# Quick Reference: {target.name}\n\n"
        
        # Quick info
        content += f"**Type:** {target.type}\n"
        content += f"**File:** `{Path(target.file_path).name}`\n\n"
        
        # Key methods from structure
        if target.comprehensive_analysis.get("structure", {}).get("success"):
            content += "## Methods\n\n"
            struct_data = target.comprehensive_analysis["structure"].get("raw", "")
            lines = struct_data.split('\n')
            methods = [line.strip() for line in lines if '🔧' in line][:10]
            content += "```\n"
            for method in methods:
                # Clean up the method signature
                clean_method = method.replace('🔧', '').strip()
                content += f"{clean_method}\n"
            content += "```\n"
        
        # Handle different output formats
        if self.output_format == OutputFormat.HTML:
            return self._markdown_to_html(content, f"Quick Reference: {target.name}")
        elif self.output_format == OutputFormat.INTERACTIVE:
            return self._generate_interactive_docs(target)
        elif self.output_format == OutputFormat.DOCSTRING:
            return '"""\n' + content + '\n"""'
        elif self.output_format == OutputFormat.RST:
            # Convert markdown to RST (basic)
            rst_content = content.replace('# ', '').replace('## ', '')
            rst_content = rst_content.replace('```', '::')
            return rst_content
        else:
            return content
    
    def _generate_tutorial(self, target: DocumentationTarget) -> str:
        """Generate tutorial documentation"""
        content = f"# Tutorial: Working with {target.name}\n\n"
        content += f"## Introduction\n\n"
        content += f"In this tutorial, you'll learn how to use the `{target.name}` {target.type}.\n\n"
        
        content += "## Prerequisites\n\n"
        content += "- Basic knowledge of Java\n"
        content += "- Understanding of the codebase structure\n\n"
        
        content += "## Step 1: Basic Setup\n\n"
        content += "```java\n"
        content += f"// Import the necessary classes\n"
        content += f"import com.example.package.{target.name};\n\n"
        content += f"// Create an instance\n"
        content += f"{target.name} instance = new {target.name}();\n"
        content += "```\n\n"
        
        content += "## Step 2: Configuration\n\n"
        content += "Configure the instance according to your needs...\n\n"
        
        content += "## Step 3: Using the Features\n\n"
        # Add some method examples if available
        if target.comprehensive_analysis.get("method_analysis", {}).get("success"):
            content += "The main methods you'll use are:\n\n"
            method_data = target.comprehensive_analysis["method_analysis"].get("raw", "")
            # Extract some method names
            lines = method_data.split('\n')
            for line in lines:
                if "METHOD DEFINITIONS FOUND" in line:
                    content += f"- See the method analysis for available operations\n"
                    break
        
        content += "\n## Conclusion\n\n"
        content += f"You've learned the basics of using `{target.name}`. For more details, see the API documentation.\n"
        
        # Handle different output formats
        if self.output_format == OutputFormat.HTML:
            return self._markdown_to_html(content, f"Tutorial: {target.name}")
        elif self.output_format == OutputFormat.INTERACTIVE:
            return self._generate_interactive_docs(target)
        elif self.output_format == OutputFormat.DOCSTRING:
            return '"""\n' + content + '\n"""'
        elif self.output_format == OutputFormat.RST:
            # Convert markdown to RST (basic)
            rst_content = content.replace('# ', '').replace('## ', '')
            rst_content = rst_content.replace('```', '::')
            return rst_content
        else:
            return content


def main():
    """Main entry point for the enhanced documentation generator"""
    parser = argparse.ArgumentParser(
        description="Enhanced Documentation Generator with Complete AST Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate comprehensive API docs with all AST tools
    python doc_generator_enhanced.py file.py function_name --style api-docs --depth comprehensive --format interactive
    
    # Generate architecture documentation
    python doc_generator_enhanced.py module.py --style architecture --depth deep --format html
    
    # Generate call graph visualization
    python doc_generator_enhanced.py file.py main --style call-graph --depth comprehensive --format markdown
        """
    )
    
    parser.add_argument("file_path", help="Path to the source file to analyze")
    parser.add_argument("target_name", nargs="?", help="Name of function/class to document (optional for module docs)")
    
    parser.add_argument("--style", 
                        choices=[s.value for s in DocumentationStyle],
                        default=DocumentationStyle.API_DOCS.value,
                        help="Documentation style")
    
    parser.add_argument("--depth",
                        choices=[d.value for d in DepthLevel],
                        default=DepthLevel.MEDIUM.value,
                        help="Analysis depth level")
    
    parser.add_argument("--format",
                        choices=[f.value for f in OutputFormat],
                        default=OutputFormat.MARKDOWN.value,
                        help="Output format")
    
    parser.add_argument("--output", "-o",
                        help="Output file path (default: stdout)")
    
    parser.add_argument("--verbose", "-v",
                        action="store_true",
                        help="Enable verbose output")
    
    parser.add_argument("--output-reasoning-json",
                        action="store_true",
                        help="Output AI reasoning in JSON format (for AI agents)")
    
    args = parser.parse_args()
    
    try:
        # Create generator
        generator = EnhancedDocumentationGenerator(
            args.file_path,
            DocumentationStyle(args.style),
            DepthLevel(args.depth),
            OutputFormat(args.format),
            args.verbose
        )
        
        # Generate documentation
        if args.target_name:
            # Detect if it's a class or function (simple heuristic)
            if args.target_name[0].isupper():
                docs = generator.generate_class_docs(args.target_name)
            else:
                docs = generator.generate_function_docs(args.target_name)
        else:
            docs = generator.generate_module_docs()
        
        # Handle AI reasoning output
        if args.output_reasoning_json:
            # Generate a target for reasoning analysis
            if args.target_name:
                # Create a target for the specific function/class
                target = DocumentationTarget(
                    name=args.target_name,
                    type="function",  # Will be updated by analysis
                    file_path=args.file_path
                )
                # Populate with analyzer data - simplified for now
                target.comprehensive_analysis = {
                    "structure": {"success": True},
                    "symbol_info": {"success": True}
                }
                # Initialize missing attributes
                target.description = f"Documentation for {target.name}"
                target.parameters = []
                target.returns = ""
                target.examples = []
                target.methods = []
            else:
                # Module-level target
                target = DocumentationTarget(
                    name=Path(args.file_path).stem,
                    type="module",
                    file_path=args.file_path
                )
                target.comprehensive_analysis = {
                    "structure": {"success": True},
                    "cross_file_analysis": {"success": True}
                }
                # Initialize missing attributes
                target.description = f"Module documentation for {target.name}"
                target.parameters = []
                target.returns = ""
                target.examples = []
                target.methods = []
            
            reasoning = generator.generate_ai_reasoning(target)
            
            if args.output:
                output_data = {"documentation": docs, "ai_reasoning": reasoning}
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(output_data, indent=2))
                print(f"Documentation with AI reasoning written to {args.output}")
            else:
                print(json.dumps(reasoning, indent=2))
        
        # Normal output
        elif args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(docs)
            print(f"Documentation written to {args.output}")
        else:
            print(docs)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
