#!/usr/bin/env python3
"""
Code Intelligence Toolkit - Unified JSON API Prototype
Proof of concept for structured AI agent integration
"""

import json
import subprocess
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

class CodeIntelligenceAPI:
    """
    Unified API for all Code Intelligence Toolkit operations.
    Provides structured, programmatic access optimized for AI agents.
    """
    
    def __init__(self, toolkit_path: Optional[Path] = None):
        self.toolkit_path = toolkit_path or Path(__file__).parent
        self.wrapper = self.toolkit_path / "run_any_python_tool.sh"
        
        # Validate toolkit installation
        if not self.wrapper.exists():
            raise RuntimeError(f"Toolkit wrapper not found at {self.wrapper}")
    
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
                "non_interactive": true,
                "working_dir": "/path/to/project"
            }
        }
        
        Response format:
        {
            "success": true,
            "tool": "data_flow_tracker_v2",
            "result": {...},
            "files_generated": ["impact_report.html"],
            "execution_time": 1.23,
            "warnings": [],
            "reasoning": {...}  # If reasoning requested
        }
        """
        tool = request.get("tool")
        if not tool:
            return {
                "success": False,
                "error": "No tool specified in request"
            }
        
        params = request.get("params", {})
        options = request.get("options", {})
        
        # Build command
        cmd = [str(self.wrapper), f"{tool}.py"]
        
        # Add parameters
        for key, value in params.items():
            if key.startswith("--"):
                cmd.append(key)
                if value is not True and value is not False:
                    cmd.append(str(value))
            else:
                # Positional arguments
                cmd.append(str(value))
        
        # Ensure JSON output for parseable results
        if "--json" not in params and tool in self._json_capable_tools():
            cmd.extend(["--json"])
        
        # Add reasoning output if requested
        if options.get("include_reasoning") and tool in self._reasoning_capable_tools():
            cmd.extend(["--output-reasoning-json"])
        
        # Set environment for non-interactive mode
        env = os.environ.copy()
        if options.get("non_interactive", True):
            env["CODE_INTEL_NONINTERACTIVE"] = "1"
            env["SAFEGIT_ASSUME_YES"] = "1"
            env["SAFE_FILE_MANAGER_ASSUME_YES"] = "1"
        
        # Set working directory
        cwd = options.get("working_dir", self.toolkit_path)
        
        # Execute with timeout
        timeout = options.get("timeout", 60)
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=cwd
            )
            execution_time = time.time() - start_time
            
            # Parse result
            if result.returncode == 0:
                response = {
                    "success": True,
                    "tool": tool,
                    "execution_time": execution_time,
                    "warnings": self._extract_warnings(result.stderr)
                }
                
                # Try to parse JSON output
                try:
                    tool_output = json.loads(result.stdout)
                    response["result"] = tool_output
                    
                    # Extract files generated
                    response["files_generated"] = self._detect_generated_files(tool_output)
                    
                    # Extract reasoning if present
                    if "ai_reasoning" in tool_output:
                        response["reasoning"] = tool_output["ai_reasoning"]
                        
                except json.JSONDecodeError:
                    # Fallback for non-JSON output
                    response["result"] = {
                        "raw_output": result.stdout,
                        "output_type": "text"
                    }
                
                return response
            else:
                return {
                    "success": False,
                    "tool": tool,
                    "error": result.stderr or result.stdout,
                    "execution_time": execution_time,
                    "command": " ".join(cmd)  # For debugging
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "tool": tool,
                "error": f"Tool execution timed out after {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def batch_execute(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple requests, with dependency analysis."""
        results = []
        for request in requests:
            # Add previous results to context if needed
            if request.get("options", {}).get("use_previous_results"):
                request["options"]["previous_results"] = results
            
            result = self.execute(request)
            results.append(result)
            
            # Stop on failure if requested
            if not result["success"] and request.get("options", {}).get("stop_on_failure"):
                break
        
        return results
    
    def _json_capable_tools(self) -> set:
        """Tools that support JSON output."""
        return {
            "data_flow_tracker_v2",
            "find_text_v7",
            "doc_generator",
            "doc_generator_enhanced",
            "cross_file_analysis_ast",
            "method_analyzer_ast",
            "git_commit_analyzer",
            "semantic_diff_v3"
        }
    
    def _reasoning_capable_tools(self) -> set:
        """Tools that can provide AI reasoning output."""
        return {
            "data_flow_tracker_v2",
            "doc_generator_enhanced",
            "semantic_diff_v3"
        }
    
    def _detect_generated_files(self, output: Dict) -> List[str]:
        """Detect files generated by the tool."""
        files = []
        
        # Check common output patterns
        if "output_file" in output:
            files.append(output["output_file"])
        if "generated_files" in output:
            files.extend(output["generated_files"])
        if "html_report" in output:
            files.append(output["html_report"])
            
        return files
    
    def _extract_warnings(self, stderr: str) -> List[str]:
        """Extract meaningful warnings from stderr."""
        warnings = []
        if stderr:
            for line in stderr.split('\n'):
                if any(marker in line.lower() for marker in ['warning:', 'warn:', 'caution:']):
                    warnings.append(line.strip())
        return warnings


# Convenience functions for common AI operations
class AICodeAssistant:
    """High-level interface for common AI coding operations."""
    
    def __init__(self, api: Optional[CodeIntelligenceAPI] = None):
        self.api = api or CodeIntelligenceAPI()
    
    def analyze_before_change(self, file: str, variable: str) -> Dict[str, Any]:
        """Comprehensive analysis before making changes."""
        # Get impact analysis
        impact_result = self.api.execute({
            "tool": "data_flow_tracker_v2",
            "params": {
                "--var": variable,
                "--file": file,
                "--show-impact": True,
                "--show-calculation-path": True
            },
            "options": {
                "include_reasoning": True
            }
        })
        
        # Get documentation context
        doc_result = self.api.execute({
            "tool": "doc_generator_enhanced",
            "params": {
                "--file": file,
                "--style": "technical",
                "--depth": "deep"
            }
        })
        
        # Combine results
        return {
            "variable": variable,
            "file": file,
            "impact_analysis": impact_result.get("result", {}),
            "documentation": doc_result.get("result", {}),
            "reasoning": impact_result.get("reasoning", {}),
            "safe_to_proceed": self._evaluate_safety(impact_result)
        }
    
    def _evaluate_safety(self, impact_result: Dict) -> bool:
        """Evaluate if it's safe to proceed with changes."""
        if not impact_result.get("success"):
            return False
            
        result = impact_result.get("result", {})
        
        # Check risk factors
        if result.get("risk_level") == "high":
            return False
        if result.get("affects_external_api"):
            return False
        if result.get("affects_security"):
            return False
            
        return True
    
    def safe_refactor(self, old_name: str, new_name: str, 
                     scope: str = "src/") -> Dict[str, Any]:
        """Perform safe refactoring with comprehensive checks."""
        # First, find all occurrences
        find_result = self.api.execute({
            "tool": "find_text_v7",
            "params": {
                old_name,
                "--scope": scope,
                "--json": True
            }
        })
        
        if not find_result.get("success"):
            return find_result
        
        # Analyze impact for each file
        files = find_result.get("result", {}).get("files", [])
        impact_reports = []
        
        for file in files:
            impact = self.analyze_before_change(file, old_name)
            impact_reports.append(impact)
            
            if not impact["safe_to_proceed"]:
                return {
                    "success": False,
                    "error": f"Unsafe to refactor in {file}",
                    "impact_report": impact
                }
        
        # Perform refactoring
        refactor_results = []
        for file in files:
            result = self.api.execute({
                "tool": "replace_text_ast_v2",
                "params": {
                    "--file": file,
                    old_name,
                    new_name,
                    "--yes": True
                }
            })
            refactor_results.append(result)
        
        return {
            "success": True,
            "files_modified": len(files),
            "impact_reports": impact_reports,
            "refactor_results": refactor_results
        }
    
    def generate_comprehensive_docs(self, file: str) -> Dict[str, Any]:
        """Generate all documentation styles for a file."""
        styles = ["api-docs", "user-guide", "technical", "architecture", "tutorial"]
        results = {}
        
        batch_requests = [
            {
                "tool": "doc_generator_enhanced",
                "params": {
                    "--file": file,
                    "--style": style,
                    "--format": "json"
                }
            }
            for style in styles
        ]
        
        batch_results = self.api.batch_execute(batch_requests)
        
        for style, result in zip(styles, batch_results):
            if result.get("success"):
                results[style] = result.get("result", {})
        
        return {
            "file": file,
            "documentation": results,
            "styles_generated": list(results.keys())
        }


def main():
    """Example usage and testing."""
    # Initialize API
    api = CodeIntelligenceAPI()
    assistant = AICodeAssistant(api)
    
    # Example 1: Direct API usage
    print("Example 1: Direct API usage")
    result = api.execute({
        "tool": "find_text_v7",
        "params": {
            "TODO",
            "--scope": ".",
            "--json": True
        }
    })
    print(json.dumps(result, indent=2))
    print("\n" + "="*60 + "\n")
    
    # Example 2: AI Assistant analyzing before changes
    print("Example 2: Analyzing before changes")
    analysis = assistant.analyze_before_change("example.py", "config")
    print(f"Safe to proceed: {analysis['safe_to_proceed']}")
    print("\n" + "="*60 + "\n")
    
    # Example 3: Batch operations
    print("Example 3: Batch operations")
    requests = [
        {
            "tool": "safegit",
            "params": {"status": True}
        },
        {
            "tool": "find_text_v7",
            "params": {
                "FIXME",
                "--json": True
            }
        }
    ]
    batch_results = api.batch_execute(requests)
    print(f"Executed {len(batch_results)} operations")


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        main()
    else:
        # Run as a service
        print("Code Intelligence API ready for requests...")
        print("Send JSON requests to stdin, get JSON responses on stdout")
        
        while True:
            try:
                line = input()
                request = json.loads(line)
                
                api = CodeIntelligenceAPI()
                response = api.execute(request)
                
                print(json.dumps(response))
                sys.stdout.flush()
                
            except EOFError:
                break
            except Exception as e:
                error_response = {
                    "success": False,
                    "error": str(e)
                }
                print(json.dumps(error_response))
                sys.stdout.flush()