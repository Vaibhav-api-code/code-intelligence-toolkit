#!/usr/bin/env python3
"""
Git Safety - Safe git operations with automatic backups

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from ..api import CodeIntelligenceAPI


class GitSafety:
    """Safe git operations with automatic protection"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.api = CodeIntelligenceAPI()
    
    def safe_reset(self, target: str, hard: bool = False) -> Dict[str, Any]:
        """Safely reset with automatic backup"""
        params = {"reset": True, target: True}
        if hard:
            params["--hard"] = True
        
        return self.api.execute({
            "tool": "safegit",
            "params": params,
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def safe_clean(self, force: bool = False, directories: bool = False) -> Dict[str, Any]:
        """Safely clean working directory with backup"""
        params = {"clean": True}
        if force:
            params["-f"] = True
        if directories:
            params["-d"] = True
        
        return self.api.execute({
            "tool": "safegit",
            "params": params,
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def safe_push(self, branch: str = "HEAD", force: bool = False) -> Dict[str, Any]:
        """Safely push with protection against force push disasters"""
        params = {"push": True, "origin": True, branch: True}
        if force:
            params["--force-with-lease"] = True  # SafeGIT converts --force to this
        
        return self.api.execute({
            "tool": "safegit",
            "params": params,
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def status(self) -> Dict[str, Any]:
        """Get git status safely"""
        return self.api.execute({
            "tool": "safegit",
            "params": {"status": True},
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def add_files(self, files: List[str], all_files: bool = False) -> Dict[str, Any]:
        """Add files to staging area"""
        params = {"add": True}
        
        if all_files:
            params["."] = True
        else:
            for file in files:
                params[file] = True
        
        return self.api.execute({
            "tool": "safegit",
            "params": params,
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def commit(self, message: str, all_modified: bool = False) -> Dict[str, Any]:
        """Commit changes with safety checks"""
        params = {"commit": True, "-m": message}
        
        if all_modified:
            params["-a"] = True
        
        return self.api.execute({
            "tool": "safegit",
            "params": params,
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def show_undo_history(self) -> Dict[str, Any]:
        """Show available undo operations"""
        return self.api.execute({
            "tool": "safegit",
            "params": {"undo-history": True},
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def undo_last_operation(self) -> Dict[str, Any]:
        """Undo the last dangerous git operation"""
        return self.api.execute({
            "tool": "safegit",
            "params": {"undo": True},
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def check_branch_safety(self, operation: str) -> Dict[str, Any]:
        """Check if an operation is safe on the current branch"""
        return self.api.execute({
            "tool": "safegit",
            "params": {"--dry-run": True, operation: True},
            "options": {
                "working_dir": str(self.project_root)
            }
        })