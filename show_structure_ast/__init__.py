
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
show_structure_ast - Hierarchical code structure analysis package

This package provides tools for analyzing and displaying code structure
across multiple languages with advanced filtering capabilities.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-17
License: Mozilla Public License 2.0 (MPL-2.0)
"""

from .analyzer import StructureAnalyzer
from .models import CodeElement
from .filters import FilterContext
from .parsers import PythonParser, JavaParser, JavaScriptParser
from .preprocessor import ContentPreprocessor
from .utils import safe_analyzer_context

__version__ = "4.0.0"

__all__ = [
    "StructureAnalyzer",
    "CodeElement",
    "FilterContext",
    "PythonParser",
    "JavaParser",
    "JavaScriptParser",
    "ContentPreprocessor",
    "safe_analyzer_context",
]