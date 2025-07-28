#!/usr/bin/env python3
"""
Impact Assessor - Comprehensive impact analysis

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from pathlib import Path
from typing import Dict, Any, Optional, NamedTuple
from ..api import CodeIntelligenceAPI


class ImpactAssessment(NamedTuple):
    """Result of impact assessment"""
    safe_to_proceed: bool
    risk_level: str
    risk_factors: list
    affected_files: list
    recommendations: list


class ImpactAssessor:
    """Comprehensive impact analysis for code changes"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.api = CodeIntelligenceAPI()
    
    def assess_rename_impact(self, old_name: str, new_name: str, 
                           scope: str = "project") -> ImpactAssessment:
        """Assess impact of renaming a symbol"""
        # First find all occurrences
        find_result = self.api.execute({
            "tool": "find_text_v7",
            "params": {
                old_name: True,
                "--scope": scope if scope != "project" else str(self.project_root)
            },
            "options": {"working_dir": str(self.project_root)}
        })
        
        if not find_result["success"]:
            return ImpactAssessment(
                safe_to_proceed=False,
                risk_level="unknown",
                risk_factors=["Analysis failed"],
                affected_files=[],
                recommendations=["Retry analysis"]
            )
        
        # Simplified assessment
        raw_output = find_result["result"]["raw_output"]
        occurrence_count = raw_output.count(old_name) if isinstance(raw_output, str) else 0
        
        if occurrence_count == 0:
            risk_level = "none"
            safe_to_proceed = True
        elif occurrence_count < 5:
            risk_level = "low"
            safe_to_proceed = True
        elif occurrence_count < 20:
            risk_level = "medium"
            safe_to_proceed = True
        else:
            risk_level = "high"
            safe_to_proceed = False
        
        return ImpactAssessment(
            safe_to_proceed=safe_to_proceed,
            risk_level=risk_level,
            risk_factors=[f"{occurrence_count} occurrences found"],
            affected_files=[],
            recommendations=["Run comprehensive tests after refactoring"]
        )