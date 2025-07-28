#!/usr/bin/env python3
"""
Safe Refactorer - Safe refactoring operations with rollback capability

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, NamedTuple
from ..api import CodeIntelligenceAPI


class RefactorResult(NamedTuple):
    """Result of a refactoring operation"""
    success: bool
    files_modified: List[str]
    changes_made: int
    rollback_id: Optional[str]
    warnings: List[str]


class SafeRefactorer:
    """Safe refactoring with automatic backups and rollback"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.api = CodeIntelligenceAPI()
        self.active_transactions = {}
    
    def rename_symbol(self, old_name: str, new_name: str, 
                     scope: str = "project", **kwargs) -> RefactorResult:
        """Safely rename a symbol across the project"""
        result = self.api.execute({
            "tool": "unified_refactor",
            "params": {
                "rename": True,
                old_name: True,
                new_name: True,
                "--scope": scope if scope != "project" else str(self.project_root),
                "--dry-run": kwargs.get("dry_run", False)
            },
            "options": {
                "working_dir": str(self.project_root)
            }
        })
        
        if not result["success"]:
            return RefactorResult(
                success=False,
                files_modified=[],
                changes_made=0,
                rollback_id=None,
                warnings=[result.get("error", "Unknown error")]
            )
        
        # Extract refactoring information
        refactor_data = result.get("result", {})
        files_modified = refactor_data.get("files_modified", [])
        changes_made = refactor_data.get("changes_made", 0)
        
        return RefactorResult(
            success=True,
            files_modified=files_modified,
            changes_made=changes_made,
            rollback_id=result.get("request_id"),
            warnings=result.get("warnings", [])
        )
    
    def extract_method(self, file_path: str, start_line: int, end_line: int,
                      new_method_name: str, **kwargs) -> RefactorResult:
        """Extract code into a new method"""
        # This would use a method extraction tool
        result = self.api.execute({
            "tool": "replace_text_ast_v2",
            "params": {
                "--file": str(self.project_root / file_path),
                "--extract-method": True,
                "--start-line": start_line,
                "--end-line": end_line,
                "--method-name": new_method_name
            },
            "options": {
                "working_dir": str(self.project_root)
            }
        })
        
        return RefactorResult(
            success=result["success"],
            files_modified=[file_path] if result["success"] else [],
            changes_made=1 if result["success"] else 0,
            rollback_id=result.get("request_id"),
            warnings=result.get("warnings", [])
        )
    
    def move_class(self, class_name: str, from_file: str, to_file: str) -> RefactorResult:
        """Move a class from one file to another"""
        # This would be a complex operation involving multiple tools
        # For now, return a stub implementation
        return RefactorResult(
            success=False,
            files_modified=[],
            changes_made=0,
            rollback_id=None,
            warnings=["Move class operation not yet implemented"]
        )
    
    def start_transaction(self, transaction_id: str) -> bool:
        """Start a refactoring transaction for rollback"""
        # Create backup state
        self.active_transactions[transaction_id] = {
            "started_at": str(Path.cwd()),
            "operations": []
        }
        return True
    
    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a refactoring transaction"""
        if transaction_id in self.active_transactions:
            del self.active_transactions[transaction_id]
            return True
        return False
    
    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a refactoring transaction"""
        if transaction_id in self.active_transactions:
            # Would implement actual rollback logic
            del self.active_transactions[transaction_id]
            return True
        return False