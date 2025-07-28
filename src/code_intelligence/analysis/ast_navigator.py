#!/usr/bin/env python3
"""
AST Navigator - Code navigation and symbol resolution

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ..api import CodeIntelligenceAPI


class ASTNavigator:
    """AST-based code navigation and symbol resolution"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.api = CodeIntelligenceAPI()
    
    def find_definition(self, symbol: str, file_path: str) -> Dict[str, Any]:
        """Find the definition of a symbol"""
        return self.api.execute({
            "tool": "navigate_ast_v2",
            "params": {
                str(self.project_root / file_path): True,
                "--to": symbol
            },
            "options": {"working_dir": str(self.project_root)}
        })
    
    def show_structure(self, file_path: str) -> Dict[str, Any]:
        """Show AST structure of a file"""
        return self.api.execute({
            "tool": "show_structure_ast",
            "params": {
                str(self.project_root / file_path): True
            },
            "options": {"working_dir": str(self.project_root)}
        })