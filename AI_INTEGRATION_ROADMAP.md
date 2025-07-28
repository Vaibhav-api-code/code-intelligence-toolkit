<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

AI Integration Roadmap

Author: Code Intelligence Team
Created: 2025-07-28
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# AI Integration Roadmap - Code Intelligence Toolkit

## Executive Summary

Transform the Code Intelligence Toolkit from a powerful CLI tool collection into the definitive platform for AI-driven development by adding programmatic interfaces, structured reasoning output, and a proper Python SDK.

## Phase 1: Unified JSON API (2-3 weeks)

### 1.1 Create `api.py` - Universal JSON Endpoint

```python
# code-intelligence-toolkit/api.py
"""
Unified JSON API for all Code Intelligence Toolkit operations.
Provides structured, programmatic access for AI agents.
"""

import json
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path

class CodeIntelligenceAPI:
    def __init__(self, toolkit_path: Optional[Path] = None):
        self.toolkit_path = toolkit_path or Path(__file__).parent
        self.wrapper = self.toolkit_path / "run_any_python_tool.sh"
    
    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute any toolkit command via JSON request.
        
        Request format:
        {
            "tool": "data_flow_tracker_v2",
            "params": {
                "--var": "user_input",
                "--file": "app.py",
                "--show-impact": true,
                "--json": true
            },
            "options": {
                "timeout": 30,
                "non_interactive": true
            }
        }
        
        Response format:
        {
            "success": true,
            "tool": "data_flow_tracker_v2",
            "result": {...},  # Tool-specific JSON output
            "files_generated": ["impact_report.html"],
            "execution_time": 1.23,
            "warnings": []
        }
        """
        tool = request["tool"]
        params = request.get("params", {})
        options = request.get("options", {})
        
        # Build command
        cmd = [str(self.wrapper), f"{tool}.py"]
        
        # Add parameters
        for key, value in params.items():
            if key.startswith("--"):
                cmd.append(key)
                if value is not True:  # Boolean flags don't need values
                    cmd.append(str(value))
            else:
                cmd.append(str(value))
        
        # Ensure JSON output for parseable results
        if "--json" not in params:
            cmd.extend(["--json"])
        
        # Set environment for non-interactive mode
        env = os.environ.copy()
        if options.get("non_interactive", True):
            env["CODE_INTEL_NONINTERACTIVE"] = "1"
            env["SAFEGIT_ASSUME_YES"] = "1"
        
        # Execute with timeout
        timeout = options.get("timeout", 60)
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            execution_time = time.time() - start_time
            
            # Parse result
            if result.returncode == 0:
                try:
                    tool_output = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Fallback for non-JSON output
                    tool_output = {"raw_output": result.stdout}
                
                return {
                    "success": True,
                    "tool": tool,
                    "result": tool_output,
                    "files_generated": self._detect_generated_files(tool_output),
                    "execution_time": execution_time,
                    "warnings": self._extract_warnings(result.stderr)
                }
            else:
                return {
                    "success": False,
                    "tool": tool,
                    "error": result.stderr or result.stdout,
                    "execution_time": execution_time
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "tool": tool,
                "error": f"Tool execution timed out after {timeout} seconds"
            }
```

### 1.2 Usage Examples for AI Agents

```python
# AI agent using the unified API
api = CodeIntelligenceAPI()

# Analyze code impact
response = api.execute({
    "tool": "data_flow_tracker_v2",
    "params": {
        "--var": "database_connection",
        "--file": "app.py",
        "--show-impact": True
    }
})

if response["success"]:
    impact = response["result"]["impact_analysis"]
    if impact["risk_level"] == "high":
        # Get more context before proceeding
        doc_response = api.execute({
            "tool": "doc_generator_enhanced",
            "params": {
                "--class": "DatabaseManager",
                "--file": "app.py",
                "--style": "technical"
            }
        })
```

## Phase 2: AI Reasoning Output Format (1-2 weeks)

### 2.1 Structured Reasoning Schema

```python
# Add to each analysis tool
def generate_reasoning_output(self, analysis_results: Dict) -> Dict:
    """
    Generate structured reasoning output for AI consumption.
    """
    return {
        "reasoning_version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "analysis_type": self.__class__.__name__,
        "logical_steps": [
            {
                "step": 1,
                "action": "identified_variable_dependencies",
                "targets": ["config", "database", "logger"],
                "confidence": 0.95,
                "reasoning": "Static analysis found 3 direct dependencies"
            },
            {
                "step": 2,
                "action": "traced_impact_chain",
                "affected_functions": ["save_user", "update_profile", "delete_account"],
                "confidence": 0.88,
                "reasoning": "Data flow analysis shows 3 functions use this variable"
            }
        ],
        "risk_assessment": {
            "level": "high",
            "factors": [
                {
                    "factor": "external_api_calls",
                    "severity": 0.8,
                    "description": "Variable affects external API interactions"
                },
                {
                    "factor": "data_persistence",
                    "severity": 0.9,
                    "description": "Changes affect database writes"
                }
            ],
            "overall_confidence": 0.85
        },
        "recommendations": [
            {
                "action": "add_validation",
                "priority": "high",
                "reasoning": "Input validation missing on user-supplied data"
            },
            {
                "action": "add_tests",
                "priority": "medium",
                "reasoning": "No test coverage for error paths"
            }
        ],
        "context_requirements": {
            "needs_human_review": False,
            "needs_additional_analysis": ["security_scan", "performance_profile"],
            "safe_for_automation": True
        }
    }
```

### 2.2 Integration with Existing Tools

```python
# Enhanced data_flow_tracker_v2.py
class DataFlowAnalyzerV2:
    def analyze(self, file_path: str, variable: str, 
                output_reasoning: bool = False) -> Dict:
        # Existing analysis...
        results = self._perform_analysis(file_path, variable)
        
        if output_reasoning:
            results["ai_reasoning"] = self.generate_reasoning_output(results)
        
        return results
```

## Phase 3: Python SDK (3-4 weeks)

### 3.1 Package Structure

```
code-intelligence-toolkit/
├── setup.py
├── pyproject.toml
├── src/
│   └── code_intelligence/
│       ├── __init__.py
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── data_flow.py
│       │   ├── ast_navigation.py
│       │   └── impact_assessment.py
│       ├── documentation/
│       │   ├── __init__.py
│       │   ├── generator.py
│       │   └── styles.py
│       ├── refactoring/
│       │   ├── __init__.py
│       │   ├── ast_refactor.py
│       │   └── safe_replacer.py
│       ├── safety/
│       │   ├── __init__.py
│       │   ├── git_safety.py
│       │   └── file_safety.py
│       └── api/
│           ├── __init__.py
│           └── client.py
```

### 3.2 SDK Interface Design

```python
# src/code_intelligence/__init__.py
"""
Code Intelligence Toolkit - Python SDK
AI-first code analysis and manipulation library
"""

from .analysis import DataFlowAnalyzer, ImpactAssessor, ASTNavigator
from .documentation import DocumentationGenerator
from .refactoring import SafeRefactorer
from .safety import SafeGit, SafeFileManager

class CodeIntelligence:
    """High-level interface for AI agents."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.data_flow = DataFlowAnalyzer(project_root)
        self.docs = DocumentationGenerator(project_root)
        self.refactor = SafeRefactorer(project_root)
        self.git = SafeGit(project_root)
    
    def analyze_impact(self, file: str, variable: str) -> ImpactReport:
        """Analyze the impact of changing a variable."""
        return self.data_flow.analyze_impact(file, variable)
    
    def generate_documentation(self, file: str, **options) -> Documentation:
        """Generate comprehensive documentation."""
        return self.docs.generate(file, **options)
    
    def refactor_safely(self, old_name: str, new_name: str, 
                       scope: str = "project") -> RefactorResult:
        """Perform safe, AST-aware refactoring."""
        return self.refactor.rename(old_name, new_name, scope)
```

### 3.3 AI-Optimized Usage

```python
# AI agent using the SDK
from code_intelligence import CodeIntelligence

# Initialize for a project
ci = CodeIntelligence(project_root="/path/to/project")

# Analyze before making changes
impact = ci.analyze_impact("core/auth.py", "session_timeout")

# AI evaluates the risk
if impact.risk_level == "high" and impact.affects_security:
    # Get detailed reasoning
    reasoning = impact.get_reasoning()
    
    # Generate documentation for affected code
    for affected_file in impact.affected_files:
        docs = ci.generate_documentation(
            affected_file,
            style="technical",
            include_impact_analysis=True
        )
    
    # If AI decides to proceed, use safe refactoring
    result = ci.refactor_safely(
        "session_timeout",
        "auth_session_timeout",
        scope=impact.suggested_scope
    )
    
    # Commit with enhanced message
    ci.git.commit(
        message=f"refactor: rename session_timeout for clarity\n\n{reasoning.summary}",
        include_impact_report=True
    )
```

## Phase 4: Advanced AI Features (Future)

### 4.1 Conversation Memory

```python
class AIConversationContext:
    """Maintain context across multiple AI operations."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.operations = []
        self.file_states = {}
        self.risk_accumulator = RiskAccumulator()
    
    def track_operation(self, operation: Dict):
        """Track all operations for rollback and reasoning."""
        self.operations.append({
            "timestamp": datetime.now(),
            "operation": operation,
            "state_snapshot": self._capture_state()
        })
```

### 4.2 Intelligent Batching

```python
class BatchOperationOptimizer:
    """Optimize multiple operations for efficiency."""
    
    def plan_operations(self, requested_ops: List[Dict]) -> ExecutionPlan:
        """
        Analyze requested operations and create optimal execution plan.
        - Detect conflicts
        - Parallelize where possible
        - Minimize file I/O
        - Predict total execution time
        """
        # Implementation
```

## Implementation Timeline

1. **Week 1-2**: Implement unified JSON API
2. **Week 3**: Add AI reasoning output to core tools
3. **Week 4-6**: Build Python SDK structure
4. **Week 7**: Create comprehensive test suite
5. **Week 8**: Documentation and examples
6. **Week 9+**: Advanced features and optimization

## Success Metrics

- **Performance**: SDK 10x faster than shell wrapper approach
- **Adoption**: 100+ AI projects using the SDK within 3 months
- **Safety**: Zero data loss incidents reported
- **Developer Experience**: 90%+ satisfaction in surveys

## Marketing Strategy

1. **Launch Blog Post**: "Introducing the AI-First Code Intelligence SDK"
2. **Integration Guides**: For OpenAI, Anthropic, Google AI platforms
3. **Example AI Agents**: Full-featured examples on GitHub
4. **Partnership**: With major AI coding assistant providers

This roadmap transforms the Code Intelligence Toolkit from a powerful CLI tool into the essential infrastructure for safe, intelligent AI-driven development.