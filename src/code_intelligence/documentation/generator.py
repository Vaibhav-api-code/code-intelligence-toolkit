#!/usr/bin/env python3
"""
Documentation Generator - Automated documentation generation

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from ..api import CodeIntelligenceAPI


class DocumentationGenerator:
    """Automated documentation generation with AI reasoning"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.api = CodeIntelligenceAPI()
    
    def generate_docs(self, target_path: str, **kwargs) -> Dict[str, Any]:
        """Generate documentation for a file or directory"""
        return self.api.execute({
            "tool": "doc_generator_enhanced",
            "params": {
                str(self.project_root / target_path): True,
                "--format": "markdown"
            },
            "options": {
                "include_reasoning": kwargs.get("include_reasoning", True),
                "working_dir": str(self.project_root)
            }
        })
    
    def analyze_documentation_quality(self, target_path: str) -> Dict[str, Any]:
        """Analyze existing documentation quality"""
        result = self.generate_docs(target_path, include_reasoning=True)
        
        if not result["success"]:
            return {
                "quality_score": 0.0,
                "completeness": "unknown",
                "recommendations": ["Analysis failed"]
            }
        
        reasoning = result.get("reasoning", {})
        return {
            "quality_score": reasoning.get("quality_score", 0.5),
            "completeness": reasoning.get("completeness", "partial"),
            "recommendations": reasoning.get("recommendations", [])
        }
    
    def generate_api_docs(self, files: List[str]) -> Dict[str, Any]:
        """Generate API documentation for multiple files"""
        results = []
        
        for file_path in files:
            result = self.generate_docs(file_path)
            results.append({
                "file": file_path,
                "success": result["success"],
                "documentation": result.get("result", {})
            })
        
        return {
            "files_processed": len(files),
            "successful": sum(1 for r in results if r["success"]),
            "results": results
        }