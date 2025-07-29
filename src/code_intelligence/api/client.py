#!/usr/bin/env python3
"""
API Client - Unified interface to Code Intelligence Toolkit operations

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

import json
import subprocess
import os
import sys
import time
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import tempfile

# Configure logging
logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry of all available tools and their capabilities."""
    
    # Tools that support JSON output
    JSON_CAPABLE = {
        "data_flow_tracker_v2", "find_text_v7", "doc_generator", 
        "doc_generator_enhanced", "cross_file_analysis_ast", 
        "method_analyzer_ast", "git_commit_analyzer", "semantic_diff_v3",
        "navigate_ast_v2", "show_structure_ast", "replace_text_v9",
        "replace_text_ast_v2", "unified_refactor", "smart_ls",
        "find_files", "recent_files", "dir_stats", "tree_view"
    }
    
    # Tools that can provide AI reasoning output
    REASONING_CAPABLE = {
        "data_flow_tracker_v2", "doc_generator_enhanced", 
        "semantic_diff_v3", "impact_analyzer"
    }
    
    # Tools that require file path validation
    FILE_REQUIRED = {
        "data_flow_tracker_v2", "navigate_ast_v2", "method_analyzer_ast",
        "doc_generator", "doc_generator_enhanced", "replace_text_v9",
        "replace_text_ast_v2", "show_structure_ast"
    }
    
    # Tools that support batch operations efficiently
    BATCH_CAPABLE = {
        "find_text_v7", "replace_text_v9", "safegit", 
        "safe_file_manager", "git_commit_analyzer"
    }
    
    @classmethod
    def validate_tool(cls, tool: str) -> bool:
        """Check if tool exists in the toolkit."""
        # In production, this would check against actual available tools
        # For now, we'll accept any tool name that follows naming conventions
        return bool(tool and isinstance(tool, str) and len(tool) > 0)

class CodeIntelligenceAPI:
    """
    Unified API for all Code Intelligence Toolkit operations.
    Provides structured, programmatic access optimized for AI agents.
    """
    
    def __init__(self, toolkit_path: Optional[Path] = None, cache_enabled: bool = True):
        self.toolkit_path = toolkit_path or self._find_toolkit_path()
        self.wrapper = self.toolkit_path / "run_any_python_tool.sh"
        self.cache_enabled = cache_enabled
        self.cache_dir = self.toolkit_path / ".api_cache"
        
        # Validate toolkit installation
        if not self.wrapper.exists():
            raise RuntimeError(f"Toolkit wrapper not found at {self.wrapper}")
        
        # Initialize cache if enabled
        if self.cache_enabled:
            self.cache_dir.mkdir(exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "total_execution_time": 0
        }
    
    def _find_toolkit_path(self) -> Path:
        """Auto-detect toolkit path"""
        # Try common locations
        possible_paths = [
            Path(__file__).parent.parent.parent.parent,  # SDK installation
            Path.cwd(),  # Current directory
            Path.home() / "code-intelligence-toolkit",  # Home directory
            Path("/opt/code-intelligence-toolkit"),  # System installation
        ]
        
        for path in possible_paths:
            if (path / "run_any_python_tool.sh").exists():
                return path
        
        raise RuntimeError("Could not find Code Intelligence Toolkit installation")
    
    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute any toolkit command via JSON request.
        
        Request format:
        {
            "tool": "data_flow_tracker_v2",
            "params": {
                "--var": "user_input",
                "--file": "app.py",
                "--show-impact": true
            },
            "options": {
                "timeout": 30,
                "non_interactive": true,
                "working_dir": "/path/to/project",
                "cache": true,
                "include_reasoning": true
            }
        }
        """
        self.stats["total_requests"] += 1
        start_time = time.time()
        
        try:
            # Validate request
            validation_error = self._validate_request(request)
            if validation_error:
                self.stats["failed_requests"] += 1
                return {
                    "success": False,
                    "error": validation_error,
                    "request_id": self._generate_request_id(request)
                }
            
            tool = request["tool"]
            params = request.get("params", {})
            options = request.get("options", {})
            
            # Check cache if enabled
            if options.get("cache", True) and self.cache_enabled:
                cache_key = self._generate_cache_key(request)
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    self.stats["cache_hits"] += 1
                    cached_result["from_cache"] = True
                    return cached_result
            
            # Build command
            cmd = self._build_command(tool, params, options)
            
            # Set environment
            env = self._prepare_environment(options)
            
            # Set working directory
            cwd = Path(options.get("working_dir", self.toolkit_path))
            
            # Execute command
            timeout = options.get("timeout", 60)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=cwd
            )
            
            execution_time = time.time() - start_time
            self.stats["total_execution_time"] += execution_time
            
            # Process result
            response = self._process_result(
                result, tool, execution_time, request
            )
            
            # Cache if successful and caching enabled
            if response["success"] and options.get("cache", True) and self.cache_enabled:
                self._cache_result(cache_key, response)
            
            # Update stats
            if response["success"]:
                self.stats["successful_requests"] += 1
            else:
                self.stats["failed_requests"] += 1
            
            return response
            
        except subprocess.TimeoutExpired:
            self.stats["failed_requests"] += 1
            return {
                "success": False,
                "tool": request.get("tool"),
                "error": f"Tool execution timed out after {timeout} seconds",
                "request_id": self._generate_request_id(request)
            }
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.exception("Unexpected error in API execution")
            return {
                "success": False,
                "tool": request.get("tool"),
                "error": f"Unexpected error: {str(e)}",
                "request_id": self._generate_request_id(request)
            }
    
    def batch_execute(self, requests: List[Dict[str, Any]], 
                     parallel: bool = False) -> List[Dict[str, Any]]:
        """
        Execute multiple requests with optional parallelization.
        
        Args:
            requests: List of request dictionaries
            parallel: Execute requests in parallel (not implemented in this version)
        """
        results = []
        context = {"previous_results": []}
        
        for i, request in enumerate(requests):
            # Add context from previous results if requested
            if request.get("options", {}).get("use_previous_results"):
                request["options"]["context"] = context
            
            # Execute request
            result = self.execute(request)
            result["batch_index"] = i
            results.append(result)
            
            # Update context
            context["previous_results"].append({
                "index": i,
                "tool": request.get("tool"),
                "success": result.get("success"),
                "summary": self._summarize_result(result)
            })
            
            # Stop on failure if requested
            if not result["success"] and request.get("options", {}).get("stop_on_failure"):
                # Add skipped markers for remaining requests
                for j in range(i + 1, len(requests)):
                    results.append({
                        "success": False,
                        "error": "Skipped due to previous failure",
                        "batch_index": j,
                        "tool": requests[j].get("tool")
                    })
                break
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        stats = self.stats.copy()
        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_requests"]
            if self.cache_enabled:
                stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_requests"]
        return stats
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear the API cache."""
        if not self.cache_enabled:
            return {"cleared": False, "reason": "Cache not enabled"}
        
        try:
            file_count = len(list(self.cache_dir.glob("*.json")))
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            return {"cleared": True, "files_removed": file_count}
        except Exception as e:
            return {"cleared": False, "error": str(e)}
    
    # Private methods for implementation details...
    # (Include all the private methods from the original api.py)
    
    def _validate_request(self, request: Dict[str, Any]) -> Optional[str]:
        """Validate request structure and content."""
        if not isinstance(request, dict):
            return "Request must be a dictionary"
        
        tool = request.get("tool")
        if not tool:
            return "No tool specified in request"
        
        if not ToolRegistry.validate_tool(tool):
            return f"Unknown tool: {tool}"
        
        params = request.get("params", {})
        if not isinstance(params, dict):
            return "params must be a dictionary"
        
        # Validate file paths if required
        if tool in ToolRegistry.FILE_REQUIRED:
            file_param = params.get("--file") or params.get("file")
            if not file_param:
                # Check for positional file argument
                for key, value in params.items():
                    if not key.startswith("--") and Path(str(value)).suffix:
                        file_param = value
                        break
            
            if file_param and not Path(file_param).exists():
                return f"File not found: {file_param}"
        
        return None
    
    def _build_command(self, tool: str, params: Dict[str, Any], 
                      options: Dict[str, Any]) -> List[str]:
        """Build command line from request parameters."""
        cmd = [str(self.wrapper), f"{tool}.py"]
        
        # Process parameters
        for key, value in params.items():
            if key.startswith("--"):
                cmd.append(key)
                if value is not True and value is not False:
                    cmd.append(str(value))
            elif value is True:
                # Positional boolean flag
                cmd.append(key)
            else:
                # Positional argument
                cmd.append(str(value))
        
        # Ensure JSON output for capable tools
        if "--json" not in params and tool in ToolRegistry.JSON_CAPABLE:
            cmd.extend(["--json"])
        
        # Add reasoning output if requested
        if options.get("include_reasoning") and tool in ToolRegistry.REASONING_CAPABLE:
            if "--output-reasoning-json" not in params:
                cmd.extend(["--output-reasoning-json"])
        
        return cmd
    
    def _prepare_environment(self, options: Dict[str, Any]) -> Dict[str, str]:
        """Prepare environment variables for tool execution."""
        env = os.environ.copy()
        
        # Non-interactive mode settings
        if options.get("non_interactive", True):
            env["CODE_INTEL_NONINTERACTIVE"] = "1"
            env["SAFEGIT_NONINTERACTIVE"] = "1"
            env["SAFEGIT_ASSUME_YES"] = "1"
            env["SAFE_FILE_MANAGER_ASSUME_YES"] = "1"
            env["SFM_ASSUME_YES"] = "1"
            env["REPLACE_TEXT_ASSUME_YES"] = "1"
        
        # Custom environment variables
        custom_env = options.get("env", {})
        env.update(custom_env)
        
        return env
    
    def _process_result(self, result: subprocess.CompletedProcess, 
                       tool: str, execution_time: float, 
                       request: Dict[str, Any]) -> Dict[str, Any]:
        """Process subprocess result into API response."""
        response = {
            "success": result.returncode == 0,
            "tool": tool,
            "execution_time": execution_time,
            "request_id": self._generate_request_id(request),
            "warnings": self._extract_warnings(result.stderr)
        }
        
        if result.returncode == 0:
            # Try to parse JSON output
            if tool in ToolRegistry.JSON_CAPABLE:
                try:
                    tool_output = json.loads(result.stdout)
                    response["result"] = tool_output
                    
                    # Extract special fields
                    if "files_generated" in tool_output:
                        response["files_generated"] = tool_output["files_generated"]
                    
                    if "ai_reasoning" in tool_output:
                        response["reasoning"] = tool_output["ai_reasoning"]
                        
                except json.JSONDecodeError:
                    # Fallback for non-JSON output
                    response["result"] = {
                        "raw_output": result.stdout,
                        "output_type": "text"
                    }
            else:
                response["result"] = {
                    "raw_output": result.stdout,
                    "output_type": "text"
                }
            
            # Detect generated files from output patterns
            if "files_generated" not in response:
                response["files_generated"] = self._detect_generated_files(
                    response.get("result", {})
                )
        else:
            response["error"] = result.stderr or result.stdout or "Unknown error"
            response["command"] = " ".join(self._build_command(
                tool, request.get("params", {}), request.get("options", {})
            ))
        
        return response
    
    def _extract_warnings(self, stderr: str) -> List[str]:
        """Extract meaningful warnings from stderr."""
        warnings = []
        if stderr:
            warning_patterns = ['warning:', 'warn:', 'caution:', 'deprecated:']
            for line in stderr.split('\\n'):
                line_lower = line.lower()
                if any(pattern in line_lower for pattern in warning_patterns):
                    warnings.append(line.strip())
        return warnings
    
    def _detect_generated_files(self, output: Union[Dict, str]) -> List[str]:
        """Detect files generated by the tool from output."""
        files = []
        
        if isinstance(output, dict):
            # Check common output patterns
            for key in ["output_file", "output_files", "generated_files", 
                       "html_report", "report_path", "file_created"]:
                if key in output:
                    value = output[key]
                    if isinstance(value, str):
                        files.append(value)
                    elif isinstance(value, list):
                        files.extend(value)
        
        return files
    
    def _generate_request_id(self, request: Dict[str, Any]) -> str:
        """Generate unique request ID for tracking."""
        content = json.dumps(request, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _generate_cache_key(self, request: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        # Include tool, params, and working directory in cache key
        cache_data = {
            "tool": request.get("tool"),
            "params": request.get("params", {}),
            "working_dir": str(request.get("options", {}).get("working_dir", ""))
        }
        content = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result if available."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                # Check cache age (default 1 hour)
                age = time.time() - cache_file.stat().st_mtime
                if age < 3600:  # 1 hour
                    with open(cache_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache successful result."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            # Don't cache results with warnings or large outputs
            if result.get("warnings") or len(json.dumps(result)) > 1_000_000:
                return
            
            with open(cache_file, 'w') as f:
                json.dump(result, f)
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
    
    def _summarize_result(self, result: Dict[str, Any]) -> str:
        """Create summary of result for context."""
        if not result.get("success"):
            return f"Failed: {result.get('error', 'Unknown error')}"
        
        tool_result = result.get("result", {})
        if isinstance(tool_result, dict):
            if "summary" in tool_result:
                return tool_result["summary"]
            elif "matches" in tool_result:
                return f"Found {len(tool_result['matches'])} matches"
            elif "files_analyzed" in tool_result:
                return f"Analyzed {tool_result['files_analyzed']} files"
        
        return "Completed successfully"