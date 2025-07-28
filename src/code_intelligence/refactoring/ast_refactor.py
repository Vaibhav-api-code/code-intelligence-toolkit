#!/usr/bin/env python3
"""
AST Refactorer - AST-based refactoring operations

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from ..api import CodeIntelligenceAPI


class ASTRefactorer:
    """AST-based refactoring with semantic understanding"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.api = CodeIntelligenceAPI()
    
    def rename_variable(self, file_path: str, old_name: str, new_name: str,
                       line_context: Optional[int] = None) -> Dict[str, Any]:
        """Rename a variable using AST-based analysis"""
        params = {
            "--file": str(self.project_root / file_path),
            old_name: True,
            new_name: True
        }
        
        if line_context:
            params["--line"] = line_context
        
        return self.api.execute({
            "tool": "replace_text_ast_v2",
            "params": params,
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def rename_function(self, file_path: str, old_name: str, new_name: str) -> Dict[str, Any]:
        """Rename a function and all its references"""
        return self.api.execute({
            "tool": "unified_refactor",
            "params": {
                "rename": True,
                old_name: True,
                new_name: True,
                "--file": str(self.project_root / file_path),
                "--backend": "python_ast"
            },
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def find_references(self, symbol: str, scope: str = "project") -> Dict[str, Any]:
        """Find all references to a symbol"""
        return self.api.execute({
            "tool": "unified_refactor",
            "params": {
                "find": True,
                symbol: True,
                "--scope": scope if scope != "project" else str(self.project_root)
            },
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def extract_variable(self, file_path: str, expression: str, 
                        variable_name: str, line: int) -> Dict[str, Any]:
        """Extract an expression into a variable"""
        return self.api.execute({
            "tool": "replace_text_ast_v2",
            "params": {
                "--file": str(self.project_root / file_path),
                "--line": line,
                expression: True,
                f"{variable_name} = {expression}": True
            },
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def inline_variable(self, file_path: str, variable_name: str) -> Dict[str, Any]:
        """Inline a variable by replacing all references with its value"""
        # First find the variable definition
        find_result = self.api.execute({
            "tool": "find_text_v7",
            "params": {
                f"{variable_name} =": True,
                "--file": str(self.project_root / file_path),
                "--ast-context": True
            },
            "options": {
                "working_dir": str(self.project_root)
            }
        })
        
        if not find_result["success"]:
            return find_result
        
        # This would require more complex logic to extract the value
        # and replace all references - stub implementation for now
        return {
            "success": False,
            "error": "Inline variable operation not yet fully implemented",
            "tool": "ast_refactor"
        }
    
    def reorganize_imports(self, file_path: str) -> Dict[str, Any]:
        """Reorganize and optimize imports in a file"""
        return self.api.execute({
            "tool": "replace_text_ast_v2",
            "params": {
                "--file": str(self.project_root / file_path),
                "--organize-imports": True
            },
            "options": {
                "working_dir": str(self.project_root)
            }
        })