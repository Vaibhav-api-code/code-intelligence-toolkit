#!/usr/bin/env python3
"""
File Safety - Safe file operations with atomic writes and backups

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from ..api import CodeIntelligenceAPI


class FileSafety:
    """Safe file operations with automatic backups and recovery"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.api = CodeIntelligenceAPI()
    
    def safe_move(self, source: str, destination: str, 
                  overwrite: bool = False) -> Dict[str, Any]:
        """Safely move files with backup"""
        params = {"move": True, source: True, destination: True}
        if overwrite:
            params["--overwrite"] = True
        
        return self.api.execute({
            "tool": "safe_file_manager",
            "params": params,
            "options": {
                "working_dir": str(self.project_root),
                "non_interactive": True
            }
        })
    
    def safe_copy(self, source: str, destination: str,
                  overwrite: bool = False) -> Dict[str, Any]:
        """Safely copy files with verification"""
        params = {"copy": True, source: True, destination: True}
        if overwrite:
            params["--overwrite"] = True
        
        return self.api.execute({
            "tool": "safe_file_manager",
            "params": params,
            "options": {
                "working_dir": str(self.project_root),
                "non_interactive": True
            }
        })
    
    def safe_delete(self, files: Union[str, List[str]]) -> Dict[str, Any]:
        """Safely delete files (moves to trash)"""
        if isinstance(files, str):
            files = [files]
        
        params = {"trash": True}
        for file in files:
            params[file] = True
        
        return self.api.execute({
            "tool": "safe_file_manager",
            "params": params,
            "options": {
                "working_dir": str(self.project_root),
                "non_interactive": True
            }
        })
    
    def create_file(self, file_path: str, content: str = "",
                   from_stdin: bool = False) -> Dict[str, Any]:
        """Safely create a new file"""
        params = {"create": True, file_path: True}
        
        if from_stdin:
            params["--from-stdin"] = True
        elif content:
            params["--content"] = content
        
        return self.api.execute({
            "tool": "safe_file_manager",
            "params": params,
            "options": {
                "working_dir": str(self.project_root),
                "non_interactive": True
            }
        })
    
    def create_directory(self, dir_path: str, parents: bool = True) -> Dict[str, Any]:
        """Safely create directory"""
        params = {"mkdir": True, dir_path: True}
        if parents:
            params["-p"] = True
        
        return self.api.execute({
            "tool": "safe_file_manager",
            "params": params,
            "options": {
                "working_dir": str(self.project_root),
                "non_interactive": True
            }
        })
    
    def list_directory(self, dir_path: str = ".", detailed: bool = False) -> Dict[str, Any]:
        """List directory contents safely"""
        params = {"list": True, dir_path: True}
        if detailed:
            params["--detailed"] = True
        
        return self.api.execute({
            "tool": "safe_file_manager",
            "params": params,
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def change_permissions(self, file_path: str, mode: str) -> Dict[str, Any]:
        """Change file permissions safely"""
        return self.api.execute({
            "tool": "safe_file_manager",
            "params": {"chmod": True, mode: True, file_path: True},
            "options": {
                "working_dir": str(self.project_root),
                "non_interactive": True
            }
        })
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed file information"""
        return self.api.execute({
            "tool": "safe_file_manager",
            "params": {"info": True, file_path: True},
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def show_operation_history(self) -> Dict[str, Any]:
        """Show file operation history for undo"""
        return self.api.execute({
            "tool": "safe_file_manager",
            "params": {"history": True},
            "options": {
                "working_dir": str(self.project_root)
            }
        })
    
    def undo_operation(self, operation_id: Optional[str] = None,
                      interactive: bool = False) -> Dict[str, Any]:
        """Undo a file operation"""
        params = {"undo": True}
        if operation_id:
            params["--id"] = operation_id
        if interactive:
            params["--interactive"] = True
        
        return self.api.execute({
            "tool": "safe_file_manager",
            "params": params,
            "options": {
                "working_dir": str(self.project_root),
                "non_interactive": not interactive
            }
        })