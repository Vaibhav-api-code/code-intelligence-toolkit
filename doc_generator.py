#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Automated Documentation Generator - Transform code analysis into intelligent documentation

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-27
Updated: 2025-07-27
License: Mozilla Public License 2.0 (MPL-2.0)

This tool leverages the data flow analysis and intelligence layer to automatically generate
comprehensive, accurate documentation for functions, classes, and modules.

Key Features:
- Multiple documentation styles (API docs, user guides, technical references)
- Intelligent analysis using data flow tracking and impact analysis
- Natural language explanations of complex code behavior
- Support for Python and Java with AST-based parsing
- Multiple output formats (Markdown, HTML, docstrings, RST)
- Depth levels from surface overview to deep technical analysis

Language Support:
- Python: Full AST-based analysis with complete feature support
- Java: AST-based parsing with javalang library for accurate target finding
  Note: Java analysis inherits some limitations from the underlying analyzer,
  including basic type inference and limited state tracking compared to Python

Dependencies:
- Required: data_flow_tracker_v2.py (included in toolkit)
- Required for Java: javalang>=0.13.0 (in requirements-core.txt)
- Optional: markdown>=3.3.0 for enhanced HTML conversion (in requirements-optional.txt)
  Falls back to built-in converter if not installed
- Optional: jinja2>=3.0.0 for clean HTML template separation (in requirements-optional.txt)
  Falls back to built-in templates if not installed

Built on the intelligence layer of data_flow_tracker_v2.py for maximum accuracy.
"""

import argparse
import ast
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import importlib.util
import traceback

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

# Import our existing data flow analysis capabilities
# We'll dynamically import to avoid circular dependencies
def import_data_flow_analyzer():
    """Dynamically import the data flow analyzer"""
    script_dir = Path(__file__).parent
    spec = importlib.util.spec_from_file_location(
        "data_flow_tracker_v2", 
        script_dir / "data_flow_tracker_v2.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DataFlowAnalyzerV2

class DocumentationStyle(Enum):
    """Different documentation styles for different audiences"""
    API_DOCS = "api-docs"           # Technical API documentation
    USER_GUIDE = "user-guide"       # User-friendly guides
    TECHNICAL = "technical"         # Deep technical analysis
    QUICK_REF = "quick-ref"        # Quick reference format
    TUTORIAL = "tutorial"          # Tutorial-style with examples
    
class DepthLevel(Enum):
    """Analysis depth levels"""
    SURFACE = "surface"            # Basic signature and purpose
    MEDIUM = "medium"              # Include dependencies and flow
    DEEP = "deep"                  # Complete analysis with all details

class OutputFormat(Enum):
    """Output format options"""
    MARKDOWN = "markdown"          # Markdown format
    HTML = "html"                  # HTML format
    DOCSTRING = "docstring"        # Python docstring format
    RST = "rst"                    # reStructuredText format

@dataclass
class DocumentationTarget:
    """Represents a code element to document"""
    name: str
    type: str  # 'function', 'class', 'module'
    file_path: str
    line_number: Optional[int] = None
    source_code: Optional[str] = None

class DocumentationGenerator:
    """Main documentation generator using data flow analysis"""
    
    def __init__(self, file_path: str, style: DocumentationStyle, 
                 depth: DepthLevel, output_format: OutputFormat, 
                 verbose: bool = False, analyzer_class: Optional[Any] = None):
        self.file_path = file_path
        self.style = style
        self.depth = depth
        self.output_format = output_format
        self.verbose = verbose
        self.analyzer_class = analyzer_class  # Store the injected class
        self.source_code = ""
        self.language = self._detect_language()
        
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
        elif ext == '.java':
            return 'java'
        else:
            print(f"Warning: Unknown file type {ext}, assuming Python", file=sys.stderr)
            return 'python'
    
    def _get_analyzer(self) -> Any:
        """Get data flow analyzer instance"""
        if self.analyzer_class is None:
            self.analyzer_class = import_data_flow_analyzer()
        
        analyzer = self.analyzer_class(self.source_code, self.file_path, self.language)
        analyzer.analyze()
        return analyzer
    
    def _get_template_environment(self) -> Optional[Any]:
        """Get Jinja2 environment if available"""
        if not _JINJA2_SUPPORT:
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
    
    def generate_function_docs(self, function_name: str) -> str:
        """Generate documentation for a specific function"""
        target = self._find_function(function_name)
        if not target:
            raise ValueError(f"Function '{function_name}' not found in {self.file_path}")
        
        return self._generate_documentation(target)
    
    def generate_class_docs(self, class_name: str) -> str:
        """Generate documentation for a specific class"""
        target = self._find_class(class_name)
        if not target:
            raise ValueError(f"Class '{class_name}' not found in {self.file_path}")
        
        return self._generate_documentation(target)
    
    def generate_module_docs(self) -> str:
        """Generate documentation for the entire module"""
        target = DocumentationTarget(
            name=Path(self.file_path).stem,
            type="module",
            file_path=self.file_path,
            source_code=self.source_code
        )
        
        return self._generate_documentation(target)
    
    def _find_function(self, function_name: str) -> Optional[DocumentationTarget]:
        """Find a function/method in the source code using AST (Python) or javalang (Java)."""
        try:
            if self.language == 'python':
                tree = ast.parse(self.source_code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == function_name:
                        return DocumentationTarget(
                            name=function_name,
                            type="function",
                            file_path=self.file_path,
                            line_number=node.lineno,
                            source_code=ast.unparse(node) if hasattr(ast, 'unparse') else None
                        )
            elif self.language == 'java':
                # First, try to find the method using the javalang parser if available
                if _JAVA_SUPPORT:
                    cls_node, m_node = self._find_java_method_node(self.source_code, None, function_name)
                    if m_node is not None:
                        lineno = getattr(m_node, 'position', None).line if getattr(m_node, 'position', None) else 1
                        return DocumentationTarget(
                            name=function_name,
                            type="function",
                            file_path=self.file_path,
                            line_number=lineno
                        )
                
                # Fallback to text-based approach if javalang not available or fails
                lines = self.source_code.split('\n')
                for i, line in enumerate(lines):
                    # Look for Java method patterns (public/private/protected optional)
                    import re
                    # Enhanced pattern to match more Java method signatures
                    # Handles: modifiers, generics, arrays, and various return types
                    method_pattern = rf'(?:(?:public|private|protected|static|final|abstract|synchronized|native|strictfp)\s+)*(?:(?:<[\w\s,?]+>\s+)?(?:\w+(?:\[\])?(?:\s*<[\w\s,?]+>)?)\s+)?{re.escape(function_name)}\s*\('
                    if re.search(method_pattern, line):
                        return DocumentationTarget(
                            name=function_name,
                            type="function", 
                            file_path=self.file_path,
                            line_number=i + 1
                        )
        except Exception as e:
            print(f"Error finding function {function_name}: {e}", file=sys.stderr)
        
        return None
    
    def _find_class(self, class_name: str) -> Optional[DocumentationTarget]:
        """Find a class/constructor target in the source code using AST or javalang."""
        try:
            if self.language == 'python':
                tree = ast.parse(self.source_code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        return DocumentationTarget(
                            name=class_name,
                            type="class",
                            file_path=self.file_path,
                            line_number=node.lineno,
                            source_code=ast.unparse(node) if hasattr(ast, 'unparse') else None
                        )
            elif self.language == 'java':
                if _JAVA_SUPPORT:
                    cls_node = self._find_java_class_node(self.source_code, class_name)
                    if cls_node is not None:
                        lineno = getattr(cls_node, 'position', None).line if getattr(cls_node, 'position', None) else 1
                        return DocumentationTarget(
                            name=class_name,
                            type="class",
                            file_path=self.file_path,
                            line_number=lineno
                        )
                # Fallback: text search
                for i, line in enumerate(self.source_code.split('\n')):
                    if f'class {class_name}' in line:
                        return DocumentationTarget(
                            name=class_name,
                            type="class",
                            file_path=self.file_path,
                            line_number=i + 1
                        )
        except Exception as e:
            print(f"Error finding class {class_name}: {e}", file=sys.stderr)
        
        return None
    
    def _generate_documentation(self, target: DocumentationTarget) -> str:
        """Generate documentation for a target using data flow analysis"""
        
        # Get data flow analysis
        analyzer = self._get_analyzer()
        
        # Gather relevant information based on depth level
        analysis_data = self._gather_analysis_data(target, analyzer)
        
        # Generate documentation based on style
        if self.style == DocumentationStyle.API_DOCS:
            return self._generate_api_docs(target, analysis_data)
        elif self.style == DocumentationStyle.USER_GUIDE:
            return self._generate_user_guide(target, analysis_data)
        elif self.style == DocumentationStyle.TECHNICAL:
            return self._generate_technical_docs(target, analysis_data)
        elif self.style == DocumentationStyle.QUICK_REF:
            return self._generate_quick_reference(target, analysis_data)
        elif self.style == DocumentationStyle.TUTORIAL:
            return self._generate_tutorial(target, analysis_data)
        else:
            return self._generate_api_docs(target, analysis_data)  # Default
    
    def _gather_analysis_data(self, target: DocumentationTarget, analyzer: Any) -> Dict[str, Any]:
        """Gather analysis data based on depth level
        
        Note: For Java code, the analysis may have limitations compared to Python:
        - Type inference is based on declared types only
        - State tracking is limited to field assignments
        - Generic types and lambdas are not fully analyzed
        """
        data = {
            'target': target,
            'dependencies': {},
            'affects': {},
            'impact_analysis': {},
            'calculation_paths': {},
            'complexity_info': {},
            'variables': []
        }
        
        if self.depth == DepthLevel.SURFACE:
            # Basic information only
            data['variables'] = list(analyzer.definitions.keys())[:5]  # Limit to 5
            
        elif self.depth == DepthLevel.MEDIUM:
            # Include dependencies and basic impact
            data['variables'] = list(analyzer.definitions.keys())[:10]
            
            # Sample a few key variables for analysis
            key_vars = self._get_key_variables(analyzer, target)[:3]
            for var in key_vars:
                try:
                    data['dependencies'][var] = analyzer.track_backward(var, max_depth=2)
                    data['affects'][var] = analyzer.track_forward(var, max_depth=2)
                except Exception as e:
                    print(f"[docgen] MEDIUM analysis failed for var '{var}': {e}", file=sys.stderr)
                    # continue collecting others
                    continue
                    
        elif self.depth == DepthLevel.DEEP:
            # Full analysis with impact and complexity
            data['variables'] = list(analyzer.definitions.keys())
            
            for var in data['variables']:
                try:
                    data['dependencies'][var] = analyzer.track_backward(var, max_depth=5)
                    data['affects'][var] = analyzer.track_forward(var, max_depth=5)
                    data['impact_analysis'][var] = analyzer.show_impact(var)
                except Exception as e:
                    print(f"[docgen] DEEP analysis failed for var '{var}': {e}", file=sys.stderr)
                    continue
        
        return data
    
    def _get_key_variables(self, analyzer: Any, target: DocumentationTarget) -> List[str]:
        """Get key variables relevant to the target"""
        all_vars = list(analyzer.definitions.keys())
        
        # Filter based on target type and name
        if target.type == 'function':
            # Look for variables that might be parameters or return values
            relevant_vars = [var for var in all_vars if target.name.lower() in var.lower() or 
                           var in ['result', 'return', 'output', 'value']]
        elif target.type == 'class':
            # Look for instance variables and key methods
            relevant_vars = [var for var in all_vars
                             if 'self' in var or 'this' in var
                             or target.name.lower() in var.lower()
                             or var.startswith(f"{target.name}.")]
        else:
            # For modules, get the most connected variables
            relevant_vars = all_vars
        
        # If we don't have enough relevant vars, add some general ones
        if len(relevant_vars) < 3:
            relevant_vars.extend([var for var in all_vars if var not in relevant_vars][:5])
        
        return relevant_vars[:10]  # Limit to 10 variables max
    
    def _dispatch_format_generation(self, style_name: str, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Dispatches to the correct format generator and handles errors."""
        
        # Map of (style, format) to the generation method
        format_map = {
            # API docs formats
            ("api_docs", "markdown"): self._generate_api_docs_markdown,
            ("api_docs", "html"): self._generate_api_docs_html,
            ("api_docs", "docstring"): self._generate_api_docs_docstring,
            ("api_docs", "rst"): self._generate_api_docs_rst,
            
            # User guide formats
            ("user_guide", "markdown"): self._generate_user_guide_markdown,
            ("user_guide", "html"): self._generate_user_guide_html,
            ("user_guide", "docstring"): self._generate_user_guide_docstring,
            ("user_guide", "rst"): self._generate_user_guide_rst,
            
            # Technical docs formats
            ("technical_docs", "markdown"): self._generate_technical_docs_markdown,
            ("technical_docs", "html"): self._generate_technical_docs_html,
            ("technical_docs", "docstring"): self._generate_technical_docs_docstring,
            ("technical_docs", "rst"): self._generate_technical_docs_rst,
            
            # Quick reference formats
            ("quick_reference", "markdown"): self._generate_quick_reference_markdown,
            ("quick_reference", "html"): self._generate_quick_reference_html,
            ("quick_reference", "docstring"): self._generate_quick_reference_docstring,
            ("quick_reference", "rst"): self._generate_quick_reference_rst,
            
            # Tutorial formats
            ("tutorial", "markdown"): self._generate_tutorial_markdown,
            ("tutorial", "html"): self._generate_tutorial_html,
            ("tutorial", "docstring"): self._generate_tutorial_docstring,
            ("tutorial", "rst"): self._generate_tutorial_rst,
        }
        
        # Get the specific method to call
        method_to_call = format_map.get((style_name, self.output_format.value))

        # Default to markdown if the specific format isn't found
        if not method_to_call:
            method_to_call = format_map.get((style_name, "markdown"))

        try:
            if method_to_call:
                return method_to_call(target, data)
            else:
                raise NotImplementedError(f"No generator found for style '{style_name}'")
        except Exception as e:
            print(f"Warning: Error generating {self.output_format.value} for {style_name}: {e}", file=sys.stderr)
            print("Falling back to default generator...", file=sys.stderr)
            # Attempt a final fallback to the most basic markdown generator
            return self._generate_api_docs_markdown(target, data)
    
    def _generate_api_docs(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate API-style documentation"""
        return self._dispatch_format_generation("api_docs", target, data)
    
    def _generate_api_docs_markdown(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate API documentation in Markdown format"""
        
        docs = []
        
        # Header
        if target.type == 'function':
            docs.append(f"# Function: `{target.name}()`\n")
        elif target.type == 'class':
            docs.append(f"# Class: `{target.name}`\n")
        else:
            docs.append(f"# Module: `{target.name}`\n")
        
        # Location
        docs.append(f"**Location**: `{target.file_path}`")
        if target.line_number:
            docs.append(f" (Line {target.line_number})")
        docs.append("\n\n")
        
        # Purpose (inferred from analysis)
        docs.append("## Purpose\n")
        purpose = self._infer_purpose(target, data)
        docs.append(f"{purpose}\n\n")
        
        # Parameters (for functions)
        if target.type == 'function' and self.depth != DepthLevel.SURFACE:
            docs.append("## Parameters\n")
            params = self._extract_parameters(target, data)
            if params:
                for param_name, param_info in params.items():
                    docs.append(f"- **`{param_name}`**: {param_info}\n")
            else:
                docs.append("*No parameters detected or analysis incomplete.*\n")
            docs.append("\n")
        
        # Variables and Dependencies
        if data['variables'] and self.depth != DepthLevel.SURFACE:
            docs.append("## Key Variables\n")
            for var in data['variables'][:5]:  # Limit display
                docs.append(f"- `{var}`")
                if var in data['dependencies'] and data['dependencies'][var].get('depends_on'):
                    deps = [d.get('variable', d.get('name', 'unknown')) for d in data['dependencies'][var]['depends_on'][:3]]
                    docs.append(f" (depends on: {', '.join(deps)})")
                docs.append("\n")
            docs.append("\n")
        
        # Impact Analysis (for deep analysis)
        if self.depth == DepthLevel.DEEP and data['impact_analysis']:
            docs.append("## Impact Analysis\n")
            for var, impact in data['impact_analysis'].items():
                returns = impact.get('returns', [])
                side_effects = impact.get('side_effects', [])
                if returns or side_effects:
                    docs.append(f"### Variable: `{var}`\n")
                    if returns:
                        docs.append(f"- **Returns**: {len(returns)} functions affected\n")
                    if side_effects:
                        docs.append(f"- **Side Effects**: {len(side_effects)} external effects\n")
                    docs.append("\n")
        
        # Usage Example
        docs.append("## Usage Example\n")
        example = self._generate_usage_example(target, data)
        docs.append(f"```{self.language}\n{example}\n```\n\n")
        
        # Additional Information for Deep Analysis
        if self.depth == DepthLevel.DEEP:
            docs.append("## Additional Information\n")
            notes = self._generate_deep_analysis_notes(target, data)
            docs.append(f"{notes}\n\n")
        
        # Footer
        docs.append("---\n")
        docs.append("*Generated by Code Intelligence Toolkit - Automated Documentation Generator*\n")
        
        return ''.join(docs)
    
    def _generate_user_guide(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate user-friendly guide documentation"""
        return self._dispatch_format_generation("user_guide", target, data)
    
    def _generate_user_guide_markdown(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate user-friendly guide documentation in Markdown format"""
        
        docs = []
        
        # Friendly header
        docs.append(f"# How to Use: {target.name}\n\n")
        
        # What it does
        docs.append("## What This Does\n")
        purpose = self._infer_purpose(target, data, user_friendly=True)
        docs.append(f"{purpose}\n\n")
        
        # When to use it
        docs.append("## When to Use This\n")
        use_cases = self._infer_use_cases(target, data)
        docs.append(f"{use_cases}\n\n")
        
        # How to use it
        docs.append("## How to Use It\n")
        
        # Simple example
        docs.append("### Basic Usage\n")
        example = self._generate_usage_example(target, data, simple=True)
        docs.append(f"```{self.language}\n{example}\n```\n\n")
        
        # What happens
        if self.depth != DepthLevel.SURFACE:
            docs.append("### What Happens Inside\n")
            explanation = self._generate_user_explanation(target, data)
            docs.append(f"{explanation}\n\n")
        
        # Common pitfalls
        docs.append("## Things to Watch Out For\n")
        warnings = self._generate_warnings(target, data)
        docs.append(f"{warnings}\n\n")
        
        return ''.join(docs)
    
    def _generate_technical_docs(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate deep technical documentation"""
        return self._dispatch_format_generation("technical_docs", target, data)
    
    def _generate_technical_docs_markdown(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate deep technical documentation in Markdown format"""
        
        docs = []
        
        # Technical header
        docs.append(f"# Technical Analysis: {target.name}\n\n")
        
        # Architecture overview
        docs.append("## Architecture Overview\n")
        arch_analysis = self._analyze_architecture(target, data)
        docs.append(f"{arch_analysis}\n\n")
        
        # Data flow analysis
        if data['dependencies'] or data['affects']:
            docs.append("## Data Flow Analysis\n")
            
            # Dependencies
            if data['dependencies']:
                docs.append("### Dependencies (What This Depends On)\n")
                for var, deps in data['dependencies'].items():
                    if deps.get('depends_on'):
                        docs.append(f"**{var}**:\n")
                        for dep in deps['depends_on'][:5]:
                            docs.append(f"- {dep.get('variable', dep.get('name', 'unknown'))} ({dep.get('location', 'unknown')})\n")
                        docs.append("\n")
            
            # Affects
            if data['affects']:
                docs.append("### Effects (What This Affects)\n")
                for var, effects in data['affects'].items():
                    if effects.get('affects'):
                        docs.append(f"**{var}**:\n")
                        for effect in effects['affects'][:5]:
                            docs.append(f"- {effect.get('variable', effect.get('name', 'unknown'))} ({effect.get('location', 'unknown')})\n")
                        docs.append("\n")
        
        # Impact analysis
        if data['impact_analysis']:
            docs.append("## Impact Analysis\n")
            for var, impact in data['impact_analysis'].items():
                docs.append(f"### {var}\n")
                
                returns = impact.get('returns', [])
                side_effects = impact.get('side_effects', [])
                risk = impact.get('risk_assessment', {})
                
                if risk:
                    docs.append(f"**Risk Level**: {risk.get('risk_level', 'Unknown')}\n\n")
                
                if returns:
                    docs.append("**Return Dependencies**:\n")
                    for ret in returns:
                        docs.append(f"- {ret.get('function', 'unknown')} at {ret.get('location', 'unknown')}\n")
                    docs.append("\n")
                
                if side_effects:
                    docs.append("**Side Effects**:\n")
                    for effect in side_effects:
                        docs.append(f"- {effect.get('type', 'unknown')}: {effect.get('effect', 'unknown')}\n")
                    docs.append("\n")
        
        # Calculation Paths (if available)
        if data.get('calculation_paths'):
            docs.append("## Calculation Paths\n")
            docs.append("*Shows the essential steps to compute each variable*\n\n")
            
            # Filter out debug/logging variables from display
            important_paths = {}
            for var, path_data in data['calculation_paths'].items():
                if not self._is_debug_or_logging({'variable': var}):
                    important_paths[var] = path_data
            
            # If we filtered out everything, show at least the main variables
            if not important_paths and data.get('calculation_paths'):
                # Show paths for return values or main computation variables
                for var, path_data in data['calculation_paths'].items():
                    if 'result' in var.lower() or 'return' in var.lower() or var in data.get('affects', {}):
                        important_paths[var] = path_data
            
            for var, path_data in important_paths.items():
                if path_data and isinstance(path_data, list):
                    docs.append(f"### Path to `{var}`\n")
                    
                    # Filter to show only essential steps
                    essential_steps = self._filter_essential_steps(path_data, var)
                    
                    if essential_steps:
                        for i, step in enumerate(essential_steps, 1):
                            step_var = step.get('variable', 'unknown')
                            operation = step.get('operation', 'assignment')
                            inputs = step.get('inputs', [])
                            location = step.get('location', 'unknown')
                            
                            # Extract just the line number from location
                            if ':' in location:
                                location = location.split(':')[-1]
                            
                            if inputs:
                                docs.append(f"{i}. `{step_var}` ← {', '.join(inputs)} (line {location})\n")
                            else:
                                docs.append(f"{i}. `{step_var}` ← {operation} (line {location})\n")
                        docs.append("\n")
                    else:
                        docs.append("*Direct assignment or trivial calculation*\n\n")
        
        # Complexity metrics
        docs.append("## Complexity Analysis\n")
        complexity = self._analyze_complexity(target, data)
        docs.append(f"{complexity}\n\n")
        
        return ''.join(docs)
    
    def _generate_quick_reference(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate quick reference documentation"""
        return self._dispatch_format_generation("quick_reference", target, data)
    
    def _generate_quick_reference_markdown(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate quick reference documentation in Markdown format"""
        
        docs = []
        
        # Quick header
        docs.append(f"# {target.name} - Quick Reference\n\n")
        
        # One-liner
        purpose = self._infer_purpose(target, data, concise=True)
        docs.append(f"**Purpose**: {purpose}\n\n")
        
        # Signature
        if target.type == 'function':
            signature = self._extract_signature(target)
            docs.append(f"**Signature**: `{signature}`\n\n")
        
        # Key points
        docs.append("**Key Points**:\n")
        key_points = self._extract_key_points(target, data)
        for point in key_points:
            docs.append(f"- {point}\n")
        docs.append("\n")
        
        # Quick example
        docs.append("**Example**:\n")
        example = self._generate_usage_example(target, data, minimal=True)
        docs.append(f"```{self.language}\n{example}\n```\n\n")
        
        return ''.join(docs)
    
    def _generate_tutorial(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate tutorial-style documentation"""
        return self._dispatch_format_generation("tutorial", target, data)
    
    def _generate_tutorial_markdown(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate tutorial-style documentation in Markdown format"""
        
        docs = []
        
        # Tutorial header
        docs.append(f"# Tutorial: Working with {target.name}\n\n")
        
        # Learning objectives
        docs.append("## What You'll Learn\n")
        objectives = self._generate_learning_objectives(target, data)
        docs.append(f"{objectives}\n\n")
        
        # Step-by-step guide
        docs.append("## Step-by-Step Guide\n")
        
        steps = self._generate_tutorial_steps(target, data)
        for i, step in enumerate(steps, 1):
            docs.append(f"### Step {i}: {step['title']}\n")
            docs.append(f"{step['description']}\n\n")
            if step.get('code'):
                docs.append(f"```{self.language}\n{step['code']}\n```\n\n")
        
        # Practice exercises
        docs.append("## Practice Exercises\n")
        exercises = self._generate_exercises(target, data)
        docs.append(f"{exercises}\n\n")
        
        return ''.join(docs)
    
    # Helper methods for content generation
    
    def _infer_purpose(self, target: DocumentationTarget, data: Dict[str, Any], 
                      user_friendly: bool = False, concise: bool = False) -> str:
        """Infer the purpose of the code element"""
        
        if target.type == 'function':
            if concise:
                return f"Executes {target.name} operation"
            elif user_friendly:
                return f"The `{target.name}` function performs a specific operation in your code. It processes inputs and produces outputs based on the logic defined within it."
            else:
                return f"The `{target.name}` function implements core business logic with data processing and transformation capabilities."
        
        elif target.type == 'class':
            if concise:
                return f"Represents {target.name} entity"
            elif user_friendly:
                return f"The `{target.name}` class is a blueprint that defines the structure and behavior for objects of this type."
            else:
                return f"The `{target.name}` class encapsulates data and methods to provide a cohesive interface for related functionality."
        
        else:  # module
            if concise:
                return f"Module containing {len(data.get('variables', []))} components"
            elif user_friendly:
                return f"This module contains various functions and classes that work together to provide functionality for your application."
            else:
                return f"Module providing integrated functionality through {len(data.get('variables', []))} defined components with interdependent relationships."
    
    def _extract_parameters(self, target: DocumentationTarget, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract parameter names robustly for Python; attempt with javalang for Java."""
        params: Dict[str, str] = {}
        try:
            if target.type != 'function':
                return params
            # Python robust path
            if self.language == 'python' and target.source_code:
                try:
                    tree = ast.parse(target.source_code)
                    fn_node = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)), None)
                    if fn_node:
                        # Positional-only (3.8+), args, vararg, kwonly, kwarg
                        def add_param(name: str) -> None:
                            if name and name != 'self':
                                params[name] = f"Parameter used in {target.name} processing"
                        for a in getattr(fn_node.args, "posonlyargs", []):
                            add_param(a.arg)
                        for a in fn_node.args.args:
                            add_param(a.arg)
                        if fn_node.args.vararg:
                            add_param(fn_node.args.vararg.arg)
                        for a in fn_node.args.kwonlyargs:
                            add_param(a.arg)
                        if fn_node.args.kwarg:
                            add_param(fn_node.args.kwarg.arg)
                        return params
                except Exception as e:
                    print(f"[docgen] Python parameter extraction failed: {e}", file=sys.stderr)
            # Java path
            if self.language == 'java' and _JAVA_SUPPORT:
                cls_node, m_node = self._find_java_method_node(self.source_code, None, target.name)
                if m_node:
                    for p in getattr(m_node, "parameters", []) or []:
                        try:
                            pname = getattr(p, "name", None)
                            if pname:
                                params[pname] = f"Parameter used in {target.name} processing"
                        except Exception:
                            pass
        except Exception as e:
            print(f"[docgen] _extract_parameters failed: {e}", file=sys.stderr)
        return params
    
    def _generate_usage_example(self, target: DocumentationTarget, data: Dict[str, Any], 
                               simple: bool = False, minimal: bool = False) -> str:
        """Generate usage example"""
        
        if target.type == 'function':
            if minimal:
                return f"{target.name}()"
            elif simple:
                return f"result = {target.name}(input_data)\nprint(result)"
            else:
                return f"""# Example usage of {target.name}
input_data = "sample input"
result = {target.name}(input_data)
print(f"Result: {{result}}")"""
        
        elif target.type == 'class':
            if minimal:
                return f"{target.name}()"
            elif simple:
                return f"obj = {target.name}()\nobj.method()"
            else:
                return f"""# Example usage of {target.name}
obj = {target.name}()
obj.configure(parameters)
result = obj.process()
print(result)"""
        
        else:  # module
            return f"""# Import and use {target.name}
import {target.name}
{target.name}.main_function()"""
    
    def _extract_signature(self, target: DocumentationTarget) -> str:
        """Extract function signature robustly for Python; best-effort for Java."""
        if target.type != 'function':
            return target.name
        # Python robust signature
        if self.language == 'python' and target.source_code:
            try:
                tree = ast.parse(target.source_code)
                fn_node = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)), None)
                if fn_node:
                    parts: List[str] = []
                    # Helper to format arg with annotation/default info (simplified)
                    def fmt_arg(a: ast.arg) -> str:
                        name = a.arg
                        ann = None
                        if getattr(a, 'annotation', None):
                            try:
                                ann = ast.unparse(a.annotation) if hasattr(ast, 'unparse') else None
                            except Exception:
                                ann = None
                        return f"{name}: {ann}" if ann else name
                    # positional-only (Py3.8+)
                    posonly = [fmt_arg(a) for a in getattr(fn_node.args, "posonlyargs", [])]
                    if posonly:
                        parts.extend(posonly + ['/'])
                    # normal args
                    parts.extend(fmt_arg(a) for a in fn_node.args.args)
                    # vararg
                    if fn_node.args.vararg:
                        parts.append("*" + fn_node.args.vararg.arg)
                    # kw-only separator
                    if fn_node.args.kwonlyargs and not fn_node.args.vararg:
                        parts.append("*")
                    # kwonly
                    parts.extend(fmt_arg(a) for a in fn_node.args.kwonlyargs)
                    # kwarg
                    if fn_node.args.kwarg:
                        parts.append("**" + fn_node.args.kwarg.arg)
                    return f"{target.name}(" + ", ".join(parts) + ")"
            except Exception as e:
                print(f"[docgen] Python signature extraction failed: {e}", file=sys.stderr)
        # Java best-effort
        if self.language == 'java':
            if _JAVA_SUPPORT:
                try:
                    cls_node, m_node = self._find_java_method_node(self.source_code, None, target.name)
                    if m_node:
                        pnames: List[str] = []
                        for p in getattr(m_node, "parameters", []) or []:
                            nm = getattr(p, "name", "")
                            pnames.append(nm if nm else "param")
                        return f"{target.name}(" + ", ".join(pnames) + ")"
                except Exception as e:
                    print(f"[docgen] Java signature extraction failed: {e}", file=sys.stderr)
            return f"{target.name}(...)"
        # Fallback
        return f"{target.name}(...)"
    
    def _extract_key_points(self, target: DocumentationTarget, data: Dict[str, Any]) -> List[str]:
        """Extract key points about the code element"""
        points = []
        
        # Variable count
        var_count = len(data.get('variables', []))
        if var_count > 0:
            points.append(f"Works with {var_count} variables")
        
        # Dependencies
        dep_count = len(data.get('dependencies', {}))
        if dep_count > 0:
            points.append(f"Has {dep_count} dependencies")
        
        # Impact
        impact_count = len(data.get('impact_analysis', {}))
        if impact_count > 0:
            points.append(f"Affects {impact_count} components")
        
        # Default points if no analysis data
        if not points:
            points.append(f"Implements {target.name} functionality")
            if target.type == 'function':
                points.append("Accepts parameters and returns values")
            elif target.type == 'class':
                points.append("Provides object-oriented interface")
        
        return points
    
    def _infer_use_cases(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Infer when to use this code element"""
        if target.type == 'function':
            return f"Use `{target.name}` when you need to perform the specific operation it implements. It's designed to handle the processing logic and return appropriate results."
        elif target.type == 'class':
            return f"Use `{target.name}` when you need to create objects that encapsulate related data and behavior. It's useful for organizing code and maintaining state."
        else:
            return f"Import and use this module when you need access to its functionality in your application."
    
    def _generate_user_explanation(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate user-friendly explanation of what happens"""
        explanation = f"When you use `{target.name}`, it processes your input through several steps:\n\n"
        
        if data.get('variables'):
            explanation += f"1. It works with {len(data['variables'])} internal variables\n"
        
        if data.get('dependencies'):
            explanation += f"2. It depends on {len(data['dependencies'])} other components\n"
        
        if data.get('affects'):
            explanation += f"3. It affects {len(data['affects'])} other parts of your code\n"
        
        explanation += f"4. It returns the processed result to you"
        
        return explanation
    
    def _generate_warnings(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate warnings and common pitfalls"""
        warnings = []
        
        # Check for high impact
        if data.get('impact_analysis'):
            for var, impact in data['impact_analysis'].items():
                risk_level = impact.get('risk_assessment', {}).get('risk_level', 'LOW')
                if risk_level == 'HIGH':
                    warnings.append(f"⚠️ Modifying variables related to `{var}` can have high impact")
        
        # Default warnings
        if not warnings:
            if target.type == 'function':
                warnings.append("✓ Ensure you provide the correct parameter types")
                warnings.append("✓ Check the return value for expected format")
            elif target.type == 'class':
                warnings.append("✓ Initialize the object properly before using its methods")
                warnings.append("✓ Be aware of state changes when calling methods")
            else:
                warnings.append("✓ Import the module correctly")
                warnings.append("✓ Check for any required dependencies")
        
        return '\n'.join(warnings)
    
    def _extract_additional_info(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Extract additional information for documentation"""
        info = []
        
        # Add testing suggestions
        info.append("**Testing Suggestions:**")
        info.append("- Unit tests for normal input cases")
        info.append("- Edge case testing (empty inputs, boundary values)")
        info.append("- Error handling validation")
        info.append("")
        
        # Add any warnings
        warnings = self._generate_warnings(target, data)
        if warnings:
            info.append("**Important Notes:**")
            info.append(warnings)
        
        return '\n'.join(info)
    
    def _analyze_architecture(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Analyze architectural aspects"""
        analysis = f"The `{target.name}` {target.type} follows these architectural patterns:\n\n"
        
        var_count = len(data.get('variables', []))
        dep_count = len(data.get('dependencies', {}))
        effect_count = len(data.get('affects', {}))
        
        if dep_count > effect_count:
            analysis += "- **Consumer Pattern**: Primarily consumes data from other components\n"
        elif effect_count > dep_count:
            analysis += "- **Producer Pattern**: Primarily produces data for other components\n"
        else:
            analysis += "- **Transformer Pattern**: Balanced input/output data flow\n"
        
        if var_count > 10:
            analysis += "- **Complex Processing**: High variable count indicates sophisticated logic\n"
        elif var_count > 5:
            analysis += "- **Moderate Complexity**: Standard processing with multiple variables\n"
        else:
            analysis += "- **Simple Processing**: Lightweight logic with minimal state\n"
        
        return analysis
    
    def _analyze_complexity(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Analyze complexity metrics"""
        complexity = "Complexity Analysis:\n\n"
        
        var_count = len(data.get('variables', []))
        dep_count = len(data.get('dependencies', {}))
        
        complexity += f"- **Variable Count**: {var_count}\n"
        complexity += f"- **Dependency Count**: {dep_count}\n"
        
        if var_count > 15:
            complexity += "- **Complexity Level**: High - Consider refactoring\n"
        elif var_count > 8:
            complexity += "- **Complexity Level**: Medium - Monitor for growth\n"
        else:
            complexity += "- **Complexity Level**: Low - Well-contained logic\n"
        
        return complexity
    
    def _generate_learning_objectives(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate learning objectives for tutorial"""
        objectives = f"By the end of this tutorial, you'll understand:\n\n"
        objectives += f"- How to use `{target.name}` effectively\n"
        objectives += f"- What inputs it expects and outputs it provides\n"
        objectives += f"- How it fits into your larger application\n"
        
        if self.depth != DepthLevel.SURFACE:
            objectives += f"- Its dependencies and relationships with other code\n"
            objectives += f"- Best practices for integration and usage\n"
        
        return objectives
    
    def _generate_tutorial_steps(self, target: DocumentationTarget, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate tutorial steps"""
        steps = []
        
        if target.type == 'function':
            steps.append({
                'title': 'Import and Set Up',
                'description': f'First, make sure you have access to the `{target.name}` function.',
                'code': f'from {Path(target.file_path).stem} import {target.name}'
            })
            
            steps.append({
                'title': 'Prepare Your Data',
                'description': 'Prepare the input data in the correct format.',
                'code': 'input_data = "your_data_here"'
            })
            
            steps.append({
                'title': 'Call the Function',
                'description': f'Call `{target.name}` with your prepared data.',
                'code': f'result = {target.name}(input_data)'
            })
            
            steps.append({
                'title': 'Use the Result',
                'description': 'Process the returned result as needed.',
                'code': 'print(f"Result: {result}")'
            })
        
        elif target.type == 'class':
            steps.append({
                'title': 'Import the Class',
                'description': f'Import the `{target.name}` class.',
                'code': f'from {Path(target.file_path).stem} import {target.name}'
            })
            
            steps.append({
                'title': 'Create an Instance',
                'description': 'Create an instance of the class.',
                'code': f'obj = {target.name}()'
            })
            
            steps.append({
                'title': 'Configure the Object',
                'description': 'Set up any necessary configuration.',
                'code': 'obj.configure(your_settings)'
            })
            
            steps.append({
                'title': 'Use the Object',
                'description': 'Call methods to perform operations.',
                'code': 'result = obj.main_method()'
            })
        
        return steps
    
    def _generate_exercises(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate practice exercises"""
        exercises = "Try these exercises to practice:\n\n"
        
        if target.type == 'function':
            exercises += f"1. Call `{target.name}` with different types of input data\n"
            exercises += f"2. Handle the return value in different ways\n"
            exercises += f"3. Integrate `{target.name}` into a larger workflow\n"
        elif target.type == 'class':
            exercises += f"1. Create multiple instances of `{target.name}`\n"
            exercises += f"2. Try different configuration options\n"
            exercises += f"3. Build a small application using this class\n"
        
        return exercises
    
    # Additional format generators
    
    def _generate_api_docs_html(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate API documentation in HTML format with interactive visualizations"""
        
        # Try to use Jinja2 template if available
        env = self._get_template_environment()
        if env:
            try:
                template = env.get_template('doc_generator/api_docs.html')
                
                # Prepare visualization data
                visualization_data = None
                if 'variables' in data and data['variables']:
                    nodes = []
                    edges = []
                    # Create simple visualization of variable dependencies
                    for i, var in enumerate(data['variables'][:10]):
                        nodes.append({
                            "id": var,
                            "label": var,
                            "color": "#E74C3C" if var == target.name else "#3498DB"
                        })
                    visualization_data = {"nodes": nodes, "edges": edges}
                
                return template.render(
                    target={
                        'name': target.name,
                        'type': target.type,
                        'file_path': target.file_path,
                        'line_number': target.line_number
                    },
                    signature=self._extract_signature(target),
                    purpose=self._infer_purpose(target, data),
                    parameters=self._extract_parameters(target, data),
                    variables=data.get('variables', []),
                    key_points=self._extract_key_points(target, data),
                    usage_example=self._generate_usage_example(target, data),
                    analysis_data=data,
                    visualization_data=visualization_data,
                    include_visualization=bool(visualization_data),
                    additional_info=self._markdown_to_html(self._extract_additional_info(target, data))
                )
            except Exception as e:
                print(f"Warning: Failed to use Jinja2 template: {e}", file=sys.stderr)
                # Fall through to built-in template
        
        # Fallback to built-in template generation
        markdown_content = self._generate_api_docs_markdown(target, data)
        
        # Generate interactive visualization if we have data flow information
        interactive_section = self._generate_interactive_visualization(target, data)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{target.name} - Interactive API Documentation</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
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
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .content {{
            padding: 30px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }}
        .docs-section {{
            padding-right: 20px;
        }}
        .visualization-section {{
            border-left: 2px solid #eee;
            padding-left: 20px;
        }}
        code {{ 
            background-color: #f8f9fa; 
            padding: 2px 6px; 
            border-radius: 4px;
            color: #e83e8c;
        }}
        pre {{ 
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 8px;
            overflow-x: auto;
            border-left: 4px solid #007bff;
        }}
        h1, h2, h3 {{ 
            color: #333;
            margin-top: 30px;
        }}
        h1 {{ margin-top: 0; font-size: 2.5em; }}
        h2 {{ color: #007bff; }}
        .visualization-container {{
            height: 400px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .controls {{
            margin-bottom: 15px;
            text-align: center;
        }}
        .btn {{
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            margin: 0 5px;
            cursor: pointer;
            transition: background 0.3s;
        }}
        .btn:hover {{
            background: #0056b3;
        }}
        .explanation {{
            background: #e7f3ff;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        @media (max-width: 768px) {{
            .content {{
                grid-template-columns: 1fr;
            }}
            .visualization-section {{
                border-left: none;
                border-top: 2px solid #eee;
                padding-left: 0;
                padding-top: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 {target.name}</h1>
            <p>Interactive API Documentation with Data Flow Analysis</p>
        </div>
        <div class="content">
            <div class="docs-section">
                {self._markdown_to_html(markdown_content)}
            </div>
            <div class="visualization-section">
                <h2>🌐 Interactive Dependency Graph</h2>
                <p>Explore how this {target.type} interacts with other components:</p>
                {interactive_section}
            </div>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _generate_interactive_visualization(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate interactive vis.js visualization integrated with documentation"""
        try:
            # Import the data flow tracker for analysis
            import importlib.util
            import os
            
            # Get the path to data_flow_tracker_v2.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            tracker_path = os.path.join(current_dir, "data_flow_tracker_v2.py")
            
            if not os.path.exists(tracker_path):
                return self._generate_fallback_visualization(target, data)
            
            # Import the tracker module
            spec = importlib.util.spec_from_file_location("data_flow_tracker_v2", tracker_path)
            tracker_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tracker_module)
            
            # Create tracker instance
            with open(self.file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Determine language from file extension
            language = "python" if self.file_path.endswith('.py') else "java"
            
            tracker = tracker_module.DataFlowAnalyzerV2(source_code, self.file_path, language)
            
            # Analyze the code first
            tracker.analyze()
            
            # Analyze the target (function/class/module)
            if target.type == 'function':
                # Perform impact analysis for the function
                result = tracker.show_impact(target.name)
                if result:
                    explanation = tracker.generate_explanation(result, "impact", target.name)
                    return self._embed_data_flow_html(result, target.name, explanation, "impact")
            
            # If no specific analysis available, generate basic visualization
            return self._generate_basic_visualization(target, data)
            
        except Exception as e:
            print(f"⚠️  Could not generate interactive visualization: {e}")
            return self._generate_fallback_visualization(target, data)
    
    def _embed_data_flow_html(self, result: dict, var_name: str, explanation: str, analysis_type: str) -> str:
        """Embed data flow analysis HTML directly into documentation"""
        
        # Extract visualization data based on analysis type
        if analysis_type == "impact":
            nodes, edges = self._extract_impact_visualization_data(result, var_name)
        else:
            nodes, edges = self._extract_basic_visualization_data(result, var_name)
        
        # Generate JavaScript for the visualization
        nodes_js = str(nodes).replace("'", '"').replace("True", "true").replace("False", "false")
        edges_js = str(edges).replace("'", '"').replace("True", "true").replace("False", "false")
        
        html = f"""
        <div class="explanation">
            <h3>🧠 Analysis Explanation</h3>
            <p>{explanation}</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="togglePhysics()">Toggle Physics</button>
            <button class="btn" onclick="centerView()">Center View</button>
            <button class="btn" onclick="exportPNG()">Export PNG</button>
        </div>
        
        <div id="visualization" class="visualization-container"></div>
        
        <script>
            // Data for the network
            var nodes = new vis.DataSet({nodes_js});
            var edges = new vis.DataSet({edges_js});
            var data = {{ nodes: nodes, edges: edges }};
            
            // Configuration options
            var options = {{
                nodes: {{
                    shape: 'box',
                    margin: 10,
                    font: {{ size: 14, color: '#343a40' }},
                    borderWidth: 2,
                    shadow: true
                }},
                edges: {{
                    arrows: {{ to: {{ enabled: true, scaleFactor: 1.2 }} }},
                    color: {{ inherit: 'from' }},
                    width: 2,
                    shadow: true,
                    smooth: {{ type: 'continuous' }}
                }},
                groups: {{
                    source: {{ color: {{ background: '#4facfe', border: '#007bff' }} }},
                    return: {{ color: {{ background: '#28a745', border: '#1e7e34' }} }},
                    effect: {{ color: {{ background: '#dc3545', border: '#c82333' }} }},
                    state: {{ color: {{ background: '#ffc107', border: '#e0a800' }} }},
                    dependency: {{ color: {{ background: '#17a2b8', border: '#138496' }} }}
                }},
                physics: {{
                    enabled: true,
                    stabilization: {{ iterations: 100 }},
                    barnesHut: {{ gravitationalConstant: -2000, springConstant: 0.001, springLength: 200 }}
                }},
                interaction: {{
                    hover: true,
                    selectConnectedEdges: false
                }},
                layout: {{
                    hierarchical: {{
                        enabled: true,
                        direction: 'LR',
                        sortMethod: 'directed',
                        shakeTowards: 'roots'
                    }}
                }}
            }};
            
            // Create the network
            var container = document.getElementById('visualization');
            var network = new vis.Network(container, data, options);
            
            // Event listeners
            network.on('click', function(params) {{
                if (params.nodes.length > 0) {{
                    var nodeId = params.nodes[0];
                    var node = nodes.get(nodeId);
                    if (node.details) {{
                        alert('Details:\\n' + node.details);
                    }}
                }}
            }});
            
            // Control functions
            function togglePhysics() {{
                var enabled = network.physics.physicsEnabled;
                network.setOptions({{ physics: {{ enabled: !enabled }} }});
            }}
            
            function centerView() {{
                network.fit();
            }}
            
            function exportPNG() {{
                // Note: This is a simplified version. Full implementation would use canvas export
                alert('PNG export would be implemented here. Use browser screenshot for now.');
            }}
            
            // Initial fit
            network.once('stabilizationIterationsDone', function() {{
                network.fit();
            }});
        </script>
        """
        
        return html
    
    def _extract_impact_visualization_data(self, result: dict, var_name: str) -> tuple:
        """Extract visualization data for impact analysis"""
        nodes = [{"id": var_name, "label": var_name, "group": "source"}]
        edges = []
        
        # Add return dependencies
        for i, ret in enumerate(result.get("returns", [])):
            node_id = f"return_{i}"
            nodes.append({
                "id": node_id,
                "label": f"Return: {ret.get('function', 'unknown')}",
                "group": "return",
                "details": f"Function: {ret.get('function', 'unknown')}\\nLocation: {ret.get('location', 'unknown')}"
            })
            edges.append({"from": var_name, "to": node_id, "color": "#28a745"})
        
        # Add side effects
        for i, effect in enumerate(result.get("side_effects", [])):
            node_id = f"effect_{i}"
            nodes.append({
                "id": node_id,
                "label": f"Side Effect: {effect.get('effect', 'unknown')}",
                "group": "effect",
                "details": f"Type: {effect.get('type', 'unknown')}\\nEffect: {effect.get('effect', 'unknown')}"
            })
            edges.append({"from": var_name, "to": node_id, "color": "#dc3545"})
        
        # Add state changes
        for i, state in enumerate(result.get("state_changes", [])):
            node_id = f"state_{i}"
            nodes.append({
                "id": node_id,
                "label": f"State: {state.get('variable', 'unknown')}",
                "group": "state",
                "details": f"Variable: {state.get('variable', 'unknown')}\\nLocation: {state.get('location', 'unknown')}"
            })
            edges.append({"from": var_name, "to": node_id, "color": "#ffc107"})
        
        return nodes, edges
    
    def _extract_basic_visualization_data(self, result: dict, var_name: str) -> tuple:
        """Extract basic visualization data"""
        nodes = [{"id": var_name, "label": var_name, "group": "source"}]
        edges = []
        
        # Add some basic dependencies from the data
        dependencies = result.get("dependencies", [])
        for i, dep in enumerate(dependencies[:5]):  # Limit to 5 for clarity
            node_id = f"dep_{i}"
            nodes.append({
                "id": node_id,
                "label": str(dep),
                "group": "dependency"
            })
            edges.append({"from": node_id, "to": var_name, "color": "#17a2b8"})
        
        return nodes, edges
    
    def _generate_basic_visualization(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate basic visualization when no data flow analysis is available"""
        # Create a simple dependency graph from available data
        dependencies = data.get("dependencies", [])
        affects = data.get("affects", [])
        
        nodes = [{"id": target.name, "label": target.name, "group": "source"}]
        edges = []
        
        # Add dependencies
        for i, dep in enumerate(dependencies[:3]):
            node_id = f"dep_{i}"
            nodes.append({"id": node_id, "label": str(dep), "group": "dependency"})
            edges.append({"from": node_id, "to": target.name, "color": "#17a2b8"})
        
        # Add affected items
        for i, affect in enumerate(affects[:3]):
            node_id = f"affect_{i}"
            nodes.append({"id": node_id, "label": str(affect), "group": "effect"})
            edges.append({"from": target.name, "to": node_id, "color": "#28a745"})
        
        return self._embed_data_flow_html({"dependencies": dependencies, "affects": affects}, target.name, 
                                        f"This shows the basic dependencies and effects for {target.name}.", "basic")
    
    def _generate_fallback_visualization(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate fallback visualization when data flow tracker is not available"""
        return f"""
        <div class="explanation">
            <h3>📊 Component Overview</h3>
            <p>This {target.type} is part of your codebase structure. Interactive visualization requires data flow analysis.</p>
        </div>
        
        <div style="padding: 40px; text-align: center; background: #f8f9fa; border-radius: 8px; border: 2px dashed #dee2e6;">
            <h4>🔍 Enhanced Visualization Available</h4>
            <p>Run with data flow analysis to see interactive dependency graphs:</p>
            <code>./run_any_python_tool.sh data_flow_tracker_v2.py --var {target.name} --show-impact --output-html --file {os.path.basename(self.file_path)}</code>
        </div>
        """
    
    def _generate_api_docs_docstring(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate API documentation in Python docstring format"""
        
        lines = []
        
        # Brief description
        purpose = self._infer_purpose(target, data, concise=True)
        lines.append(f'"""{purpose}')
        lines.append('')
        
        # Parameters
        if target.type == 'function':
            params = self._extract_parameters(target, data)
            if params:
                lines.append('Args:')
                for param_name, param_desc in params.items():
                    lines.append(f'    {param_name}: {param_desc}')
                lines.append('')
            
            lines.append('Returns:')
            lines.append('    The processed result')
            lines.append('')
        
        # Example
        lines.append('Example:')
        example = self._generate_usage_example(target, data, simple=True)
        for line in example.split('\n'):
            lines.append(f'    {line}')
        
        lines.append('"""')
        
        return '\n'.join(lines)
    
    def _generate_api_docs_rst(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate API documentation in reStructuredText format"""
        
        lines = []
        
        # Title with proper RST formatting
        title = f"Function: ``{target.name}()``" if target.type == 'function' else f"Class: ``{target.name}``"
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")
        
        # Location
        location = f"**Location**: ``{self.file_path}``"
        if hasattr(target, 'line_number'):
            location += f" (Line {target.line_number})"
        lines.append(location)
        lines.append("")
        
        # Purpose
        lines.append("Purpose")
        lines.append("-------")
        purpose = self._infer_purpose(target, data)
        lines.append(purpose)
        lines.append("")
        
        # Parameters (for functions)
        if target.type == 'function':
            params = self._extract_parameters(target, data)
            if params:
                lines.append("Parameters")
                lines.append("----------")
                for param_name, param_desc in params.items():
                    lines.append(f"* **{param_name}**: {param_desc}")
                lines.append("")
        
        # Key Variables
        variables = data.get('variables', [])
        if variables and len(variables) > 0:
            lines.append("Key Variables")
            lines.append("-------------")
            for var in variables[:5]:  # Limit to first 5
                var_deps = data.get('dependencies', {}).get(var, [])
                if var_deps and isinstance(var_deps, (list, tuple)):
                    dep_str = ", ".join([str(d) for d in var_deps[:3]])
                    lines.append(f"* ``{var}`` (depends on: {dep_str})")
                else:
                    lines.append(f"* ``{var}``")
            lines.append("")
        
        # Usage Example
        lines.append("Usage Example")
        lines.append("-------------")
        lines.append("")
        lines.append(".. code-block:: python")
        lines.append("")
        example = self._generate_usage_example(target, data, simple=True)
        for line in example.split('\n'):
            lines.append(f"   {line}")
        lines.append("")
        
        # Footer
        lines.append(".. note::")
        lines.append("   Generated by Code Intelligence Toolkit - Automated Documentation Generator")
        
        return '\n'.join(lines)
    
    # HTML format methods for all styles
    def _generate_user_guide_html(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate user-friendly guide documentation in HTML format"""
        markdown_content = self._generate_user_guide_markdown(target, data)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>User Guide: {target.name}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px;
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(90deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .content {{
            padding: 30px;
        }}
        h1, h2, h3 {{ color: #2d3436; }}
        code {{ background: #f8f9fa; padding: 2px 6px; border-radius: 4px; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 8px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 User Guide</h1>
            <p>Learn how to use {target.name} effectively</p>
        </div>
        <div class="content">
            {self._markdown_to_html(markdown_content)}
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _generate_technical_docs_html(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate technical documentation in HTML format"""
        markdown_content = self._generate_technical_docs_markdown(target, data)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Technical Analysis: {target.name}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ 
            font-family: 'JetBrains Mono', 'Consolas', monospace; 
            margin: 0; 
            padding: 20px;
            background: linear-gradient(135deg, #2d3436 0%, #636e72 100%);
            min-height: 100vh;
            color: #ddd;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #2d3436;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            overflow: hidden;
            border: 1px solid #636e72;
        }}
        .header {{
            background: linear-gradient(90deg, #fd79a8 0%, #e84393 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .content {{
            padding: 30px;
        }}
        h1, h2, h3 {{ color: #fd79a8; }}
        code {{ background: #636e72; padding: 2px 6px; border-radius: 4px; color: #00b894; }}
        pre {{ background: #636e72; padding: 15px; border-radius: 8px; overflow-x: auto; border-left: 4px solid #fd79a8; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 Technical Analysis</h1>
            <p>Deep dive into {target.name} implementation</p>
        </div>
        <div class="content">
            {self._markdown_to_html(markdown_content)}
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _generate_quick_reference_html(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate quick reference documentation in HTML format"""
        markdown_content = self._generate_quick_reference_markdown(target, data)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Quick Reference: {target.name}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px;
            background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 700px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(90deg, #00b894 0%, #00a085 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .content {{
            padding: 20px;
        }}
        h1, h2, h3 {{ color: #2d3436; }}
        code {{ background: #f8f9fa; padding: 2px 6px; border-radius: 4px; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 8px; overflow-x: auto; }}
        .purpose {{ font-size: 1.2em; color: #00b894; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ Quick Reference</h1>
            <p>Fast lookup for {target.name}</p>
        </div>
        <div class="content">
            {self._markdown_to_html(markdown_content)}
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _generate_tutorial_html(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate tutorial documentation in HTML format"""
        markdown_content = self._generate_tutorial_markdown(target, data)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Tutorial: {target.name}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px;
            background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(90deg, #a29bfe 0%, #6c5ce7 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .content {{
            padding: 30px;
        }}
        h1, h2, h3 {{ color: #2d3436; }}
        h3 {{ color: #6c5ce7; }}
        code {{ background: #f8f9fa; padding: 2px 6px; border-radius: 4px; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 8px; overflow-x: auto; border-left: 4px solid #a29bfe; }}
        .step {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Tutorial</h1>
            <p>Step-by-step guide to mastering {target.name}</p>
        </div>
        <div class="content">
            {self._markdown_to_html(markdown_content)}
        </div>
    </div>
</body>
</html>"""
        return html
    
    # RST format methods for all styles
    def _generate_user_guide_rst(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate user-friendly guide documentation in reStructuredText format"""
        
        lines = []
        
        # Title
        title = f"How to Use: {target.name}"
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")
        
        # What it does
        lines.append("What This Does")
        lines.append("-" * 14)
        purpose = self._infer_purpose(target, data, user_friendly=True)
        lines.append(purpose)
        lines.append("")
        
        # When to use it
        lines.append("When to Use This")
        lines.append("-" * 16)
        use_cases = self._infer_use_cases(target, data)
        lines.append(use_cases)
        lines.append("")
        
        # How to use it
        lines.append("How to Use It")
        lines.append("-" * 13)
        lines.append("")
        
        # Basic usage
        lines.append("Basic Usage")
        lines.append("~~~~~~~~~~~")
        lines.append("")
        lines.append(f".. code-block:: {self.language}")
        lines.append("")
        example = self._generate_usage_example(target, data, simple=True)
        for line in example.split('\n'):
            lines.append(f"   {line}")
        lines.append("")
        
        # What happens inside
        if self.depth != DepthLevel.SURFACE:
            lines.append("What Happens Inside")
            lines.append("~~~~~~~~~~~~~~~~~~~")
            explanation = self._generate_user_explanation(target, data)
            lines.append(explanation)
            lines.append("")
        
        # Things to watch out for
        lines.append("Things to Watch Out For")
        lines.append("~~~~~~~~~~~~~~~~~~~~~~~")
        warnings = self._generate_warnings(target, data)
        lines.append(warnings)
        lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_technical_docs_rst(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate technical documentation in reStructuredText format"""
        
        lines = []
        
        # Title
        title = f"Technical Analysis: {target.name}"
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")
        
        # Architecture overview
        lines.append("Architecture Overview")
        lines.append("-" * 21)
        arch_analysis = self._analyze_architecture(target, data)
        lines.append(arch_analysis)
        lines.append("")
        
        # Data flow analysis
        if data['dependencies'] or data['affects']:
            lines.append("Data Flow Analysis")
            lines.append("-" * 18)
            lines.append("")
            
            # Dependencies
            if data['dependencies']:
                lines.append("Dependencies (What This Depends On)")
                lines.append("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                for var, deps in data['dependencies'].items():
                    if deps.get('depends_on'):
                        lines.append(f"**{var}**:")
                        lines.append("")
                        for dep in deps['depends_on'][:5]:
                            lines.append(f"* {dep.get('variable', dep.get('name', 'unknown'))} ({dep.get('location', 'unknown')})")
                        lines.append("")
            
            # Effects
            if data['affects']:
                lines.append("Effects (What This Affects)")
                lines.append("~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                for var, effects in data['affects'].items():
                    if effects.get('affects'):
                        lines.append(f"**{var}**:")
                        lines.append("")
                        for effect in effects['affects'][:5]:
                            lines.append(f"* {effect.get('variable', effect.get('name', 'unknown'))} ({effect.get('location', 'unknown')})")
                        lines.append("")
        
        # Impact analysis
        if data['impact_analysis']:
            lines.append("Impact Analysis")
            lines.append("-" * 15)
            lines.append("")
            for var, impact in data['impact_analysis'].items():
                lines.append(var)
                lines.append("~" * len(var))
                lines.append("")
                
                returns = impact.get('returns', [])
                side_effects = impact.get('side_effects', [])
                risk = impact.get('risk_assessment', {})
                
                if risk:
                    lines.append(f"**Risk Level**: {risk.get('risk_level', 'Unknown')}")
                    lines.append("")
                
                if returns:
                    lines.append("**Return Dependencies**:")
                    lines.append("")
                    for ret in returns:
                        lines.append(f"* {ret.get('function', 'unknown')} at {ret.get('location', 'unknown')}")
                    lines.append("")
                
                if side_effects:
                    lines.append("**Side Effects**:")
                    lines.append("")
                    for effect in side_effects:
                        lines.append(f"* {effect.get('type', 'unknown')}: {effect.get('effect', 'unknown')}")
                    lines.append("")
        
        # Complexity analysis
        lines.append("Complexity Analysis")
        lines.append("-" * 19)
        complexity = self._analyze_complexity(target, data)
        lines.append(complexity)
        lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_quick_reference_rst(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate quick reference documentation in reStructuredText format"""
        
        lines = []
        
        # Title
        title = f"{target.name} - Quick Reference"
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")
        
        # Purpose
        purpose = self._infer_purpose(target, data, concise=True)
        lines.append(f"**Purpose**: {purpose}")
        lines.append("")
        
        # Signature
        if target.type == 'function':
            signature = self._extract_signature(target)
            lines.append(f"**Signature**: ``{signature}``")
            lines.append("")
        
        # Key points
        lines.append("**Key Points**:")
        lines.append("")
        key_points = self._extract_key_points(target, data)
        for point in key_points:
            lines.append(f"* {point}")
        lines.append("")
        
        # Example
        lines.append("**Example**:")
        lines.append("")
        lines.append(f".. code-block:: {self.language}")
        lines.append("")
        example = self._generate_usage_example(target, data, minimal=True)
        for line in example.split('\n'):
            lines.append(f"   {line}")
        lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_tutorial_rst(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate tutorial documentation in reStructuredText format"""
        
        lines = []
        
        # Title
        title = f"Tutorial: Working with {target.name}"
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")
        
        # Learning objectives
        lines.append("What You'll Learn")
        lines.append("-" * 17)
        objectives = self._generate_learning_objectives(target, data)
        lines.append(objectives)
        lines.append("")
        
        # Step-by-step guide
        lines.append("Step-by-Step Guide")
        lines.append("-" * 18)
        lines.append("")
        
        steps = self._generate_tutorial_steps(target, data)
        for i, step in enumerate(steps, 1):
            step_title = f"Step {i}: {step['title']}"
            lines.append(step_title)
            lines.append("~" * len(step_title))
            lines.append(step['description'])
            lines.append("")
            if step.get('code'):
                lines.append(f".. code-block:: {self.language}")
                lines.append("")
                for line in step['code'].split('\n'):
                    lines.append(f"   {line}")
                lines.append("")
        
        # Practice exercises
        lines.append("Practice Exercises")
        lines.append("-" * 18)
        exercises = self._generate_exercises(target, data)
        lines.append(exercises)
        lines.append("")
        
        return '\n'.join(lines)
    
    # Docstring format methods for all styles
    def _generate_user_guide_docstring(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate user-friendly guide in Python docstring format"""
        
        lines = []
        lines.append('"""')
        lines.append(f'How to Use: {target.name}')
        lines.append('')
        
        # What it does
        purpose = self._infer_purpose(target, data, user_friendly=True)
        lines.append('What This Does:')
        lines.append(f'    {purpose}')
        lines.append('')
        
        # When to use it
        use_cases = self._infer_use_cases(target, data)
        lines.append('When to Use This:')
        lines.append(f'    {use_cases}')
        lines.append('')
        
        # Basic usage
        lines.append('Basic Usage:')
        example = self._generate_usage_example(target, data, simple=True)
        for line in example.split('\n'):
            lines.append(f'    {line}')
        lines.append('')
        
        # What happens inside
        if self.depth != DepthLevel.SURFACE:
            explanation = self._generate_user_explanation(target, data)
            lines.append('What Happens Inside:')
            lines.append(f'    {explanation}')
            lines.append('')
        
        # Things to watch out for
        warnings = self._generate_warnings(target, data)
        lines.append('Things to Watch Out For:')
        lines.append(f'    {warnings}')
        lines.append('')
        
        lines.append('"""')
        return '\n'.join(lines)
    
    def _generate_technical_docs_docstring(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate technical documentation in Python docstring format"""
        
        lines = []
        lines.append('"""')
        lines.append(f'Technical Analysis: {target.name}')
        lines.append('')
        
        # Architecture overview
        arch_analysis = self._analyze_architecture(target, data)
        lines.append('Architecture Overview:')
        lines.append(f'    {arch_analysis}')
        lines.append('')
        
        # Data flow analysis
        if data['dependencies'] or data['affects']:
            lines.append('Data Flow Analysis:')
            
            # Dependencies
            if data['dependencies']:
                lines.append('    Dependencies:')
                for var, deps in data['dependencies'].items():
                    if deps.get('depends_on'):
                        lines.append(f'        {var}:')
                        for dep in deps['depends_on'][:3]:
                            lines.append(f'            - {dep.get("variable", dep.get("name", "unknown"))} ({dep.get("location", "unknown")})')
            
            # Effects
            if data['affects']:
                lines.append('    Effects:')
                for var, effects in data['affects'].items():
                    if effects.get('affects'):
                        lines.append(f'        {var}:')
                        for effect in effects['affects'][:3]:
                            lines.append(f'            - {effect.get("variable", effect.get("name", "unknown"))} ({effect.get("location", "unknown")})')
            lines.append('')
        
        # Impact analysis
        if data['impact_analysis']:
            lines.append('Impact Analysis:')
            for var, impact in data['impact_analysis'].items():
                lines.append(f'    {var}:')
                
                returns = impact.get('returns', [])
                side_effects = impact.get('side_effects', [])
                risk = impact.get('risk_assessment', {})
                
                if risk:
                    lines.append(f'        Risk Level: {risk.get("risk_level", "Unknown")}')
                
                if returns:
                    lines.append('        Return Dependencies:')
                    for ret in returns[:2]:
                        lines.append(f'            - {ret.get("function", "unknown")} at {ret.get("location", "unknown")}')
                
                if side_effects:
                    lines.append('        Side Effects:')
                    for effect in side_effects[:2]:
                        lines.append(f'            - {effect.get("type", "unknown")}: {effect.get("effect", "unknown")}')
            lines.append('')
        
        # Complexity analysis
        complexity = self._analyze_complexity(target, data)
        lines.append('Complexity Analysis:')
        lines.append(f'    {complexity}')
        lines.append('')
        
        lines.append('"""')
        return '\n'.join(lines)
    
    def _generate_quick_reference_docstring(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate quick reference in Python docstring format"""
        
        lines = []
        lines.append('"""')
        lines.append(f'{target.name} - Quick Reference')
        lines.append('')
        
        # Purpose
        purpose = self._infer_purpose(target, data, concise=True)
        lines.append(f'Purpose: {purpose}')
        lines.append('')
        
        # Signature
        if target.type == 'function':
            signature = self._extract_signature(target)
            lines.append(f'Signature: {signature}')
            lines.append('')
        
        # Key points
        key_points = self._extract_key_points(target, data)
        lines.append('Key Points:')
        for point in key_points:
            lines.append(f'    - {point}')
        lines.append('')
        
        # Example
        lines.append('Example:')
        example = self._generate_usage_example(target, data, minimal=True)
        for line in example.split('\n'):
            lines.append(f'    {line}')
        lines.append('')
        
        lines.append('"""')
        return '\n'.join(lines)
    
    def _generate_tutorial_docstring(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate tutorial in Python docstring format"""
        
        lines = []
        lines.append('"""')
        lines.append(f'Tutorial: Working with {target.name}')
        lines.append('')
        
        # Learning objectives
        objectives = self._generate_learning_objectives(target, data)
        lines.append("What You'll Learn:")
        lines.append(f'    {objectives}')
        lines.append('')
        
        # Step-by-step guide
        lines.append('Step-by-Step Guide:')
        
        steps = self._generate_tutorial_steps(target, data)
        for i, step in enumerate(steps, 1):
            lines.append(f'    Step {i}: {step["title"]}')
            lines.append(f'        {step["description"]}')
            if step.get('code'):
                lines.append('        Example:')
                for line in step['code'].split('\n'):
                    lines.append(f'            {line}')
            lines.append('')
        
        # Practice exercises
        exercises = self._generate_exercises(target, data)
        lines.append('Practice Exercises:')
        lines.append(f'    {exercises}')
        lines.append('')
        
        lines.append('"""')
        return '\n'.join(lines)
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """
        Convert Markdown to HTML.
        Prefer standard libraries; fall back to a simple converter if unavailable.
        """
        # Try Python-Markdown first
        try:
            import markdown  # type: ignore
            return markdown.markdown(
                markdown_text,
                extensions=["fenced_code", "tables", "toc", "codehilite"]
            )
        except Exception:
            pass
        # Try mistune
        try:
            import mistune  # type: ignore
            return mistune.create_markdown(escape=True, plugins=["strikethrough", "table", "url"])(
                markdown_text
            )
        except Exception:
            pass
        # Fallback to existing basic converter
        return self._markdown_to_html_fallback(markdown_text)
    
    def _markdown_to_html_fallback(self, markdown: str) -> str:
        """Simple, limited converter retained as a fallback."""
        import re
        lines = markdown.split('\n')
        html_lines: List[str] = []
        in_code_block = False
        in_list = False
        code_lang = ""
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if line.startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_lang = line[3:].strip()
                    html_lines.append(f'<pre><code class="language-{code_lang}">')
                else:
                    in_code_block = False
                    html_lines.append('</code></pre>')
                i += 1
                continue
            if in_code_block:
                escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_lines.append(escaped)
                i += 1
                continue
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                content = line[level:].strip()
                html_lines.append(f'<h{level}>{content}</h{level}>')
                i += 1
                continue
            if line.strip().startswith(('-', '*')):
                if not in_list:
                    in_list = True
                    html_lines.append('<ul>')
                content = line.lstrip('-*').strip()
                html_lines.append(f'<li>{self._process_inline_markdown(content)}</li>')
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if not (next_line.startswith('-') or next_line.startswith('*')):
                        html_lines.append('</ul>')
                        in_list = False
                else:
                    html_lines.append('</ul>')
                    in_list = False
            else:
                if line.strip().startswith('>'):
                    html_lines.append(f'<blockquote>{self._process_inline_markdown(line[1:].strip())}</blockquote>')
                elif line.strip() == '':
                    html_lines.append('')
                else:
                    processed_line = self._process_inline_markdown(line)
                    html_lines.append(f'<p>{processed_line}</p>')
            
            i += 1
        if in_list:
            html_lines.append('</ul>')
        return '\n'.join(html_lines)
    
    def _process_inline_markdown(self, text: str) -> str:
        """Process inline markdown formatting"""
        import re
        
        # Inline code (process first to avoid conflicts)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # Bold text
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        
        return text

    def _filter_essential_steps(self, steps: List[Dict[str, Any]], target_var: str) -> List[Dict[str, Any]]:
        """Filter calculation steps to show only essential ones
        
        Implements path pruning to remove:
        - Debug/logging variables
        - Metadata that doesn't affect calculations
        - Intermediate values that don't contribute to the target
        """
        if not steps:
            return []
        
        essential = []
        
        # Track which variables are needed for the target
        needed_vars = {target_var}
        
        # Work backwards through steps to find what's essential
        for step in reversed(steps):
            step_var = step.get('variable')
            inputs = step.get('inputs', [])
            operation = step.get('operation', 'assignment')
            
            # This step is essential if:
            # 1. It produces a needed variable
            # 2. It's a control flow operation that affects needed variables
            # 3. It has side effects that matter
            
            if step_var in needed_vars:
                essential.append(step)
                # Add its inputs to needed vars
                needed_vars.update(inputs)
            elif operation in ['condition', 'loop', 'branch']:
                # Control flow that uses needed variables
                if any(inp in needed_vars for inp in inputs):
                    essential.append(step)
            elif self._is_debug_or_logging(step):
                # Skip debug/logging unless they affect needed vars
                continue
            elif operation == 'function_call':
                # Include function calls that might have side effects
                func_name = step.get('function', '')
                if any(pattern in func_name.lower() for pattern in ['set', 'update', 'modify', 'write']):
                    essential.append(step)
        
        # Return in forward order
        return list(reversed(essential))
    
    def _is_debug_or_logging(self, step: Dict[str, Any]) -> bool:
        """Check if a step is likely debug or logging related"""
        var_name = step.get('variable', '').lower()
        operation = step.get('operation', '')
        
        # Common debug/logging patterns
        debug_patterns = ['debug', 'log', 'trace', 'verbose', 'timestamp', 'metadata', 'info_level']
        
        if any(pattern in var_name for pattern in debug_patterns):
            return True
        
        # Check if it's a print/log operation
        if operation == 'function_call':
            func_name = step.get('function', '').lower()
            if any(pattern in func_name for pattern in ['print', 'log', 'debug', 'trace']):
                return True
        
        return False
    
    def _generate_deep_analysis_notes(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate additional analysis notes for deep documentation level"""
        notes = []
        
        # Code complexity analysis
        if 'complexity' in data:
            complexity = data['complexity']
            notes.append("**Complexity Analysis:**")
            notes.append(f"- Cyclomatic complexity: {complexity.get('cyclomatic', 'N/A')}")
            notes.append(f"- Cognitive complexity: {complexity.get('cognitive', 'N/A')}")
            notes.append(f"- Lines of code: {complexity.get('lines_of_code', 'N/A')}")
        
        # Performance considerations
        if data.get('performance_hints'):
            notes.append("\n**Performance Considerations:**")
            for hint in data['performance_hints'][:3]:  # Limit to top 3
                notes.append(f"- {hint}")
        
        # Security considerations
        if data.get('security_issues'):
            notes.append("\n**Security Considerations:**")
            for issue in data['security_issues'][:3]:  # Limit to top 3
                notes.append(f"- {issue}")
        
        # Testing suggestions
        if target.type == 'function':
            notes.append("\n**Testing Suggestions:**")
            notes.append("- Unit tests for normal input cases")
            notes.append("- Edge case testing (empty inputs, boundary values)")
            notes.append("- Error handling validation")
            if data.get('external_dependencies'):
                notes.append("- Mock external dependencies for isolated testing")
        
        # Code quality metrics
        if 'quality_metrics' in data:
            metrics = data['quality_metrics']
            notes.append("\n**Code Quality Metrics:**")
            notes.append(f"- Maintainability index: {metrics.get('maintainability', 'N/A')}")
            notes.append(f"- Technical debt ratio: {metrics.get('technical_debt', 'N/A')}")
        
        # Refactoring opportunities
        if data.get('refactor_suggestions'):
            notes.append("\n**Refactoring Opportunities:**")
            for suggestion in data['refactor_suggestions'][:3]:  # Limit to top 3
                notes.append(f"- {suggestion}")
        
        # Design patterns detected
        if data.get('design_patterns'):
            notes.append("\n**Design Patterns:**")
            for pattern in data['design_patterns']:
                notes.append(f"- {pattern}")
        
        # Related code analysis
        if data.get('related_code'):
            notes.append("\n**Related Code Analysis:**")
            notes.append(f"- Similar functions found: {len(data['related_code'])}")
            if data['related_code']:
                notes.append(f"- Most similar: {data['related_code'][0].get('variable', data['related_code'][0].get('name', 'N/A'))}")
        
        # Anti-patterns detected
        if data.get('anti_patterns'):
            notes.append("\n**Anti-patterns Detected:**")
            for pattern in data['anti_patterns']:
                notes.append(f"- ⚠️ {pattern}")
        
        # If no additional analysis available, provide basic notes
        if not notes:
            notes.append("**Additional Analysis:**")
            notes.append(f"- Code structure follows {target.type} conventions")
            notes.append(f"- Located in {target.file_path}")
            if target.line_number:
                notes.append(f"- Implementation starts at line {target.line_number}")
            notes.append(f"- Consider adding comprehensive tests for this {target.type}")
        
        return '\n'.join(notes)

    # -------------------- Java helpers --------------------
    def _java_parse_tree(self, source_text: str):
        if not _JAVA_SUPPORT:
            return None
        try:
            return javalang.parse.parse(source_text)
        except Exception as e:
            print(f"[docgen] Java parse failed: {e}", file=sys.stderr)
            return None

    def _find_java_class_node(self, source_text: str, class_name: str):
        tree = self._java_parse_tree(source_text)
        if not tree:
            return None
        try:
            for _, node in tree.filter(javalang.tree.ClassDeclaration):
                if node.name == class_name:
                    return node
        except Exception:
            pass
        return None

    def _find_java_method_node(self, source_text: str, class_name: Optional[str], method_name: str):
        """
        Return (class_node, method_node) for Java. If class_name is None, search all classes.
        """
        tree = self._java_parse_tree(source_text)
        if not tree:
            return (None, None)
        try:
            for _, cls in tree.filter(javalang.tree.ClassDeclaration):
                if class_name and cls.name != class_name:
                    continue
                # methods
                for m in getattr(cls, "methods", []) or []:
                    if getattr(m, "name", None) == method_name:
                        return (cls, m)
                # ctors
                for c in getattr(cls, "constructors", []) or []:
                    if getattr(c, "name", None) == method_name:
                        return (cls, c)
        except Exception:
            pass
        return (None, None)

    # ---------------------------------------------------------------------
    # AST-based Java lookup (legacy methods for compatibility)
    # ---------------------------------------------------------------------
    def _find_java_class(self, source_text: str, class_name: str):
        """Return (class_node) for the named Java class, or None if not found."""
        return self._find_java_class_node(source_text, class_name)

    def _find_java_method(self, source_text: str, class_name: str | None, method_name: str):
        """Return (class_node, method_node) for the Java method/ctor, or (None, None)."""
        return self._find_java_method_node(source_text, class_name, method_name)

    # ---------------------------------------------------------------------
    # Dispatchers: use Python AST or Java AST; fall back to text search
    # ---------------------------------------------------------------------
    def _find_class_ast(self, source_text: str, name: str, language: str):
        """Return a language-appropriate representation of the class node, or None."""
        lang = (language or "").lower()
        if lang == "java":
            node = self._find_java_class(source_text, name)
            if node is not None:
                return node
            # Fallback: simple text search (best-effort)
            return None
        # Python path would use Python AST logic
        return None

    def _find_function_ast(self, source_text: str, name: str, language: str, class_name: str | None = None):
        """Return a language-appropriate function/method node or None."""
        lang = (language or "").lower()
        if lang == "java":
            _, node = self._find_java_method(source_text, class_name, name)
            if node is not None:
                return node
            # Fallback: None (caller can degrade gracefully)
            return None
        # Python path would use Python AST logic
        return None


def main():
    """Main entry point for the documentation generator"""
    
    parser = argparse.ArgumentParser(
        description="Automated Documentation Generator - Transform code analysis into intelligent documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate API documentation for a function
  doc_generator.py --function calculatePrice --file pricing.py --style api-docs
  
  # Generate user guide for a class
  doc_generator.py --class UserManager --file auth.py --style user-guide --depth deep
  
  # Generate technical documentation for a module
  doc_generator.py --module --file database.py --style technical --output html
  
  # Generate quick reference
  doc_generator.py --function process_data --file data.py --style quick-ref --format docstring
  
  # Generate tutorial
  doc_generator.py --class APIClient --file client.py --style tutorial --depth medium

Styles:
  api-docs    - Technical API documentation
  user-guide  - User-friendly guides  
  technical   - Deep technical analysis
  quick-ref   - Quick reference format
  tutorial    - Tutorial-style with examples
  
Depth Levels:
  surface     - Basic signature and purpose
  medium      - Include dependencies and flow
  deep        - Complete analysis with all details
  
Output Formats:
  markdown    - Markdown format (default)
  html        - HTML format
  docstring   - Python docstring format
  rst         - reStructuredText format
        """
    )
    
    # Target specification (mutually exclusive)
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--function", help="Function name to document")
    target_group.add_argument("--class", dest="class_name", help="Class name to document")
    target_group.add_argument("--module", action="store_true", help="Document the entire module")
    
    # Required arguments
    parser.add_argument("--file", required=True, help="Source file to analyze")
    
    # Style and format options
    parser.add_argument("--style", choices=[s.value for s in DocumentationStyle], 
                       default=DocumentationStyle.API_DOCS.value,
                       help="Documentation style (default: api-docs)")
    parser.add_argument("--depth", choices=[d.value for d in DepthLevel],
                       default=DepthLevel.MEDIUM.value,
                       help="Analysis depth level (default: medium)")
    parser.add_argument("--format", choices=[f.value for f in OutputFormat],
                       default=OutputFormat.MARKDOWN.value,
                       help="Output format (default: markdown)")
    
    # Output options
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    parser.add_argument("--verbose", action="store_true", help="Show detailed error information")
    
    args = parser.parse_args()
    
    try:
        # Create documentation generator
        generator = DocumentationGenerator(
            file_path=args.file,
            style=DocumentationStyle(args.style),
            depth=DepthLevel(args.depth),
            output_format=OutputFormat(args.format),
            verbose=args.verbose
        )
        
        # Generate documentation based on target type
        if args.function:
            if not args.quiet:
                print(f"🔍 Generating documentation for function '{args.function}'...", file=sys.stderr)
            docs = generator.generate_function_docs(args.function)
        elif args.class_name:
            if not args.quiet:
                print(f"🔍 Generating documentation for class '{args.class_name}'...", file=sys.stderr)
            docs = generator.generate_class_docs(args.class_name)
        elif args.module:
            if not args.quiet:
                print(f"🔍 Generating documentation for module...", file=sys.stderr)
            docs = generator.generate_module_docs()
        
        # Output results
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(docs)
            if not args.quiet:
                print(f"📝 Documentation written to {args.output}", file=sys.stderr)
        else:
            print(docs)
            
        if not args.quiet:
            print("✅ Documentation generation completed!", file=sys.stderr)
            
    except Exception as e:
        print(f"❌ Error generating documentation: {e}", file=sys.stderr)
        if not args.quiet:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()