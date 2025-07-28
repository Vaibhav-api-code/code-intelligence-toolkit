#!/usr/bin/env python3
"""
Data Flow Analyzer - SDK wrapper for data_flow_tracker_v2.py

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ..api import CodeIntelligenceAPI


class DataFlowAnalyzer:
    """SDK wrapper for data_flow_tracker_v2.py tool"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.api = CodeIntelligenceAPI()
    
    def analyze_impact(self, file_path: str, variable: str, **kwargs) -> Dict[str, Any]:
        """Analyze the impact of changing a variable"""
        return self.api.execute({
            "tool": "data_flow_tracker_v2",
            "params": {
                "--var": variable,
                "--file": str(self.project_root / file_path),
                "--show-impact": True,
                "--format": "json"
            },
            "options": {
                "include_reasoning": kwargs.get("include_reasoning", True),
                "working_dir": str(self.project_root)
            }
        })
    
    def track_variable(self, file_path: str, variable: str, 
                      direction: str = "forward", **kwargs) -> Dict[str, Any]:
        """Track variable data flow"""
        return self.api.execute({
            "tool": "data_flow_tracker_v2",
            "params": {
                "--var": variable,
                "--file": str(self.project_root / file_path),
                "--direction": direction,
                "--format": "json"
            },
            "options": {
                "include_reasoning": kwargs.get("include_reasoning", False),
                "working_dir": str(self.project_root)
            }
        })