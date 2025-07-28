#!/usr/bin/env python3
"""
Code Intelligence Toolkit - Python SDK
AI-first code analysis and manipulation library

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

__version__ = "0.1.0"
__author__ = "Code Intelligence Team"
__email__ = "noreply@example.com"
__license__ = "Mozilla Public License 2.0 (MPL 2.0)"

# Core imports
from .analysis import DataFlowAnalyzer, ImpactAssessor, ASTNavigator
from .documentation import DocumentationGenerator
from .refactoring import SafeRefactorer
from .safety import GitSafety, FileSafety
from .api import CodeIntelligenceAPI

# High-level interface
from .core import CodeIntelligence

# Version information
try:
    from ._version import version as __version__
except ImportError:
    # Fallback version if setuptools_scm is not available
    pass

__all__ = [
    # Version info
    "__version__",
    "__author__", 
    "__email__",
    "__license__",
    
    # Core components
    "CodeIntelligence",
    "CodeIntelligenceAPI",
    
    # Analysis tools
    "DataFlowAnalyzer",
    "ImpactAssessor", 
    "ASTNavigator",
    
    # Documentation
    "DocumentationGenerator",
    
    # Refactoring
    "SafeRefactorer",
    
    # Safety tools
    "GitSafety",
    "FileSafety",
]

# Convenience functions
def analyze_impact(file_path: str, variable: str, **kwargs):
    """Quick impact analysis for a variable"""
    analyzer = DataFlowAnalyzer()
    return analyzer.analyze_impact(file_path, variable, **kwargs)

def generate_docs(file_path: str, **kwargs):
    """Quick documentation generation"""
    generator = DocumentationGenerator()
    return generator.generate(file_path, **kwargs)

def safe_refactor(old_name: str, new_name: str, scope: str = ".", **kwargs):
    """Quick safe refactoring"""
    refactorer = SafeRefactorer()
    return refactorer.rename(old_name, new_name, scope, **kwargs)

# Add convenience functions to __all__
__all__.extend([
    "analyze_impact",
    "generate_docs", 
    "safe_refactor",
])