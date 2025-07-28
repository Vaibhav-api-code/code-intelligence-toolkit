#!/usr/bin/env python3
"""
Core CodeIntelligence class - High-level interface for AI agents

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from .analysis.data_flow import DataFlowAnalyzer
from .analysis.impact import ImpactAssessor
from .analysis.ast_navigator import ASTNavigator
from .documentation.generator import DocumentationGenerator  
from .refactoring.safe_refactorer import SafeRefactorer
from .safety.git_safety import GitSafety
from .safety.file_safety import FileSafety
from .api.client import CodeIntelligenceAPI

@dataclass
class AnalysisResult:
    """Result of code analysis with AI reasoning"""
    success: bool
    data: Dict[str, Any]
    reasoning: Optional[Dict[str, Any]] = None
    files_generated: List[str] = None
    execution_time: float = 0.0
    
    def __post_init__(self):
        if self.files_generated is None:
            self.files_generated = []

@dataclass  
class RefactorResult:
    """Result of safe refactoring operation"""
    success: bool
    files_modified: int
    changes_made: int
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class CodeIntelligence:
    """
    High-level interface for AI agents to interact with the Code Intelligence Toolkit.
    
    This class provides a unified, safe interface for code analysis, documentation,
    and refactoring operations optimized for AI agent use cases.
    """
    
    def __init__(self, project_root: Union[str, Path], toolkit_path: Optional[Path] = None):
        """
        Initialize CodeIntelligence for a project.
        
        Args:
            project_root: Path to the project root directory
            toolkit_path: Path to the toolkit installation (auto-detected if None)
        """
        self.project_root = Path(project_root).resolve()
        self.toolkit_path = toolkit_path
        
        # Initialize components
        self.api = CodeIntelligenceAPI(toolkit_path)
        self.data_flow = DataFlowAnalyzer(self.project_root)
        self.impact_assessor = ImpactAssessor(self.project_root)
        self.ast_navigator = ASTNavigator(self.project_root)
        self.docs = DocumentationGenerator(self.project_root)
        self.refactorer = SafeRefactorer(self.project_root)
        self.git = GitSafety(self.project_root)
        self.file_manager = FileSafety(self.project_root)
        
        # State tracking
        self._operation_history = []
    
    def analyze_impact(self, file_path: str, variable: str, 
                      include_reasoning: bool = True) -> AnalysisResult:
        """
        Analyze the impact of changing a variable with AI reasoning.
        
        Args:
            file_path: Path to the source file
            variable: Variable name to analyze
            include_reasoning: Include AI reasoning in the result
            
        Returns:
            AnalysisResult with impact analysis and optional reasoning
        """
        # Use the unified API for consistent results
        response = self.api.execute({
            "tool": "data_flow_tracker_v2",
            "params": {
                "--var": variable,
                "--file": str(self.project_root / file_path),
                "--show-impact": True
            },
            "options": {
                "include_reasoning": include_reasoning,
                "working_dir": str(self.project_root)
            }
        })
        
        result = AnalysisResult(
            success=response["success"],
            data=response.get("result", {}),
            reasoning=response.get("reasoning"),
            files_generated=response.get("files_generated", []),
            execution_time=response.get("execution_time", 0.0)
        )
        
        self._track_operation("analyze_impact", {
            "file": file_path,
            "variable": variable,
            "success": result.success
        })
        
        return result
    
    def generate_documentation(self, file_path: str, style: str = "api-docs",
                             output_format: str = "markdown",
                             include_reasoning: bool = True) -> AnalysisResult:
        """
        Generate comprehensive documentation with AI insights.
        
        Args:
            file_path: Path to the source file
            style: Documentation style (api-docs, user-guide, technical, etc.)
            output_format: Output format (markdown, html, interactive, etc.)
            include_reasoning: Include AI reasoning about documentation quality
            
        Returns:
            AnalysisResult with generated documentation and reasoning
        """
        response = self.api.execute({
            "tool": "doc_generator_enhanced",
            "params": {
                "--file": str(self.project_root / file_path),
                "--style": style,
                "--format": output_format
            },
            "options": {
                "include_reasoning": include_reasoning,
                "working_dir": str(self.project_root)
            }
        })
        
        result = AnalysisResult(
            success=response["success"],
            data=response.get("result", {}),
            reasoning=response.get("reasoning"),
            files_generated=response.get("files_generated", []),
            execution_time=response.get("execution_time", 0.0)
        )
        
        self._track_operation("generate_documentation", {
            "file": file_path,
            "style": style,
            "format": output_format,
            "success": result.success
        })
        
        return result
    
    def refactor_safely(self, old_name: str, new_name: str, 
                       scope: str = "project", 
                       preview: bool = True) -> RefactorResult:
        """
        Perform safe, AST-aware refactoring with impact analysis.
        
        Args:
            old_name: Current name to replace
            new_name: New name to use
            scope: Refactoring scope (project, directory, file)
            preview: Show preview before applying changes
            
        Returns:
            RefactorResult with operation details
        """
        # First analyze impact
        impact_analysis = self.impact_assessor.assess_rename_impact(
            old_name, new_name, scope
        )
        
        if not impact_analysis.safe_to_proceed and not preview:
            return RefactorResult(
                success=False,
                files_modified=0,
                changes_made=0,
                errors=[f"Unsafe to proceed: {impact_analysis.risk_factors}"]
            )
        
        # Perform the refactoring
        result = self.refactorer.rename_symbol(old_name, new_name, scope, dry_run=preview)
        
        refactor_result = RefactorResult(
            success=result.success,
            files_modified=len(result.files_modified),
            changes_made=result.changes_made,
            errors=result.warnings
        )
        
        self._track_operation("refactor_safely", {
            "old_name": old_name,
            "new_name": new_name,
            "scope": scope,
            "success": refactor_result.success
        })
        
        return refactor_result
    
    def compare_semantically(self, file1: str, file2: str,
                           include_reasoning: bool = True) -> AnalysisResult:
        """
        Perform semantic comparison between two files with AI analysis.
        
        Args:
            file1: Path to first file
            file2: Path to second file  
            include_reasoning: Include AI reasoning about changes
            
        Returns:
            AnalysisResult with semantic diff and AI insights
        """
        response = self.api.execute({
            "tool": "semantic_diff_v3",
            "params": {
                "file1": str(self.project_root / file1),
                "file2": str(self.project_root / file2),
                "--format": "json"
            },
            "options": {
                "include_reasoning": include_reasoning,
                "working_dir": str(self.project_root)
            }
        })
        
        result = AnalysisResult(
            success=response["success"],
            data=response.get("result", {}),
            reasoning=response.get("reasoning"),
            execution_time=response.get("execution_time", 0.0)
        )
        
        self._track_operation("compare_semantically", {
            "file1": file1,
            "file2": file2,
            "success": result.success
        })
        
        return result
    
    def batch_analyze(self, operations: List[Dict[str, Any]]) -> List[AnalysisResult]:
        """
        Execute multiple analysis operations in batch for efficiency.
        
        Args:
            operations: List of operation dictionaries
            
        Returns:
            List of AnalysisResult objects
        """
        # Convert to API format
        api_requests = []
        for op in operations:
            api_requests.append({
                "tool": op["tool"],
                "params": op.get("params", {}),
                "options": {
                    "include_reasoning": op.get("include_reasoning", True),
                    "working_dir": str(self.project_root),
                    **op.get("options", {})
                }
            })
        
        # Execute batch
        responses = self.api.batch_execute(api_requests)
        
        # Convert to results
        results = []
        for response in responses:
            result = AnalysisResult(
                success=response["success"],
                data=response.get("result", {}),
                reasoning=response.get("reasoning"),
                files_generated=response.get("files_generated", []),
                execution_time=response.get("execution_time", 0.0)
            )
            results.append(result)
        
        self._track_operation("batch_analyze", {
            "operations_count": len(operations),
            "success_count": sum(1 for r in results if r.success)
        })
        
        return results
    
    def get_operation_history(self) -> List[Dict[str, Any]]:
        """Get history of operations performed"""
        return self._operation_history.copy()
    
    def clear_history(self):
        """Clear operation history"""
        self._operation_history.clear()
    
    def _track_operation(self, operation: str, details: Dict[str, Any]):
        """Track an operation in history"""
        from datetime import datetime
        
        self._operation_history.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details
        })
        
        # Keep only last 100 operations
        if len(self._operation_history) > 100:
            self._operation_history = self._operation_history[-100:]
    
    # Context manager support for safe transactions
    def __enter__(self):
        """Enter context manager for transaction-like operations"""
        self._transaction_start = len(self._operation_history)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, handle rollback on error"""
        if exc_type is not None:
            # Rollback operations performed in this transaction
            operations_in_transaction = self._operation_history[self._transaction_start:]
            if operations_in_transaction:
                print(f"Transaction failed, {len(operations_in_transaction)} operations may need manual rollback")
                for op in operations_in_transaction:
                    print(f"  - {op['operation']}: {op['details']}")
        return False  # Don't suppress exceptions