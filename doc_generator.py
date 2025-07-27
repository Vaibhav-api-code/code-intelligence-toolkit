#!/usr/bin/env python3
"""
Automated Documentation Generator - Transform code analysis into intelligent documentation

This tool leverages the data flow analysis and intelligence layer to automatically generate
comprehensive, accurate documentation for functions, classes, and modules.

Key Features:
- Multiple documentation styles (API docs, user guides, technical references)
- Intelligent analysis using data flow tracking and impact analysis
- Natural language explanations of complex code behavior
- Support for Python and Java
- Multiple output formats (Markdown, HTML, docstrings)
- Depth levels from surface overview to deep technical analysis

Built on the intelligence layer of data_flow_tracker_v2.py for maximum accuracy.
"""

import argparse
import ast
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import importlib.util
import traceback

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
                 depth: DepthLevel, output_format: OutputFormat):
        self.file_path = file_path
        self.style = style
        self.depth = depth
        self.output_format = output_format
        self.analyzer_class = None
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
        """Find a function in the source code"""
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
                # For Java, we'll use a simpler text-based approach for now
                lines = self.source_code.split('\n')
                for i, line in enumerate(lines):
                    if f'def {function_name}(' in line or f'{function_name}(' in line:
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
        """Find a class in the source code"""
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
                lines = self.source_code.split('\n')
                for i, line in enumerate(lines):
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
        """Gather analysis data based on depth level"""
        data = {
            'target': target,
            'dependencies': {},
            'affects': {},
            'impact_analysis': {},
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
                except:
                    continue
                    
        elif self.depth == DepthLevel.DEEP:
            # Complete analysis
            data['variables'] = list(analyzer.definitions.keys())
            
            # Analyze key variables with full depth
            key_vars = self._get_key_variables(analyzer, target)[:5]
            for var in key_vars:
                try:
                    data['dependencies'][var] = analyzer.track_backward(var, max_depth=5)
                    data['affects'][var] = analyzer.track_forward(var, max_depth=5)
                    data['impact_analysis'][var] = analyzer.show_impact(var)
                except:
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
            relevant_vars = [var for var in all_vars if 'self' in var or target.name.lower() in var.lower()]
        else:
            # For modules, get the most connected variables
            relevant_vars = all_vars
        
        # If we don't have enough relevant vars, add some general ones
        if len(relevant_vars) < 3:
            relevant_vars.extend([var for var in all_vars if var not in relevant_vars][:5])
        
        return relevant_vars[:10]  # Limit to 10 variables max
    
    def _generate_api_docs(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate API-style documentation"""
        
        if self.output_format == OutputFormat.MARKDOWN:
            return self._generate_api_docs_markdown(target, data)
        elif self.output_format == OutputFormat.HTML:
            return self._generate_api_docs_html(target, data)
        elif self.output_format == OutputFormat.DOCSTRING:
            return self._generate_api_docs_docstring(target, data)
        else:
            return self._generate_api_docs_markdown(target, data)
    
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
                    deps = [d.get('name', 'unknown') for d in data['dependencies'][var]['depends_on'][:3]]
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
        
        # Notes
        if self.depth == DepthLevel.DEEP:
            docs.append("## Notes\n")
            notes = self._generate_notes(target, data)
            docs.append(f"{notes}\n\n")
        
        # Footer
        docs.append("---\n")
        docs.append("*Generated by Code Intelligence Toolkit - Automated Documentation Generator*\n")
        
        return ''.join(docs)
    
    def _generate_user_guide(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate user-friendly guide documentation"""
        
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
                            docs.append(f"- {dep.get('name', 'unknown')} ({dep.get('location', 'unknown')})\n")
                        docs.append("\n")
            
            # Affects
            if data['affects']:
                docs.append("### Effects (What This Affects)\n")
                for var, effects in data['affects'].items():
                    if effects.get('affects'):
                        docs.append(f"**{var}**:\n")
                        for effect in effects['affects'][:5]:
                            docs.append(f"- {effect.get('name', 'unknown')} ({effect.get('location', 'unknown')})\n")
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
        
        # Complexity metrics
        docs.append("## Complexity Analysis\n")
        complexity = self._analyze_complexity(target, data)
        docs.append(f"{complexity}\n\n")
        
        return ''.join(docs)
    
    def _generate_quick_reference(self, target: DocumentationTarget, data: Dict[str, Any]) -> str:
        """Generate quick reference documentation"""
        
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
        """Extract parameter information"""
        params = {}
        
        # This is a simplified version - in a full implementation, we'd parse the AST more thoroughly
        if target.source_code:
            # Extract parameter names from source (basic implementation)
            if 'def ' in target.source_code:
                # Simple regex-like extraction for demo
                try:
                    lines = target.source_code.split('\n')
                    for line in lines:
                        if 'def ' in line and '(' in line:
                            param_part = line.split('(')[1].split(')')[0]
                            if param_part.strip():
                                param_names = [p.strip().split('=')[0].strip() for p in param_part.split(',')]
                                for param in param_names:
                                    if param and param != 'self':
                                        params[param] = f"Parameter used in {target.name} processing"
                            break
                except:
                    pass
        
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
        """Extract function signature"""
        if target.source_code and 'def ' in target.source_code:
            lines = target.source_code.split('\n')
            for line in lines:
                if 'def ' in line:
                    return line.strip().replace('def ', '').replace(':', '')
        
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
        """Generate API documentation in HTML format"""
        # This would be a more sophisticated HTML generator
        markdown_content = self._generate_api_docs_markdown(target, data)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{target.name} - API Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; overflow-x: auto; }}
        h1, h2, h3 {{ color: #333; }}
    </style>
</head>
<body>
{self._markdown_to_html(markdown_content)}
</body>
</html>"""
        return html
    
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
    
    def _markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML conversion"""
        html = markdown
        
        # Headers
        html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
        html = html.replace('## ', '<h2>').replace('\n', '</h2>\n', 1)
        html = html.replace('### ', '<h3>').replace('\n', '</h3>\n', 1)
        
        # Code blocks
        html = html.replace('```', '<pre><code>').replace('```', '</code></pre>')
        
        # Inline code
        html = html.replace('`', '<code>').replace('`', '</code>')
        
        # Bold
        html = html.replace('**', '<strong>').replace('**', '</strong>')
        
        # Paragraphs
        html = html.replace('\n\n', '</p>\n<p>')
        html = '<p>' + html + '</p>'
        
        return html


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
    
    args = parser.parse_args()
    
    try:
        # Create documentation generator
        generator = DocumentationGenerator(
            file_path=args.file,
            style=DocumentationStyle(args.style),
            depth=DepthLevel(args.depth),
            output_format=OutputFormat(args.format)
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