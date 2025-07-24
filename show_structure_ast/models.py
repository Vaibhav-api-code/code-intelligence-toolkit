#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Data models for code structure analysis

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CodeElement:
    """Represents a code element (class, method, function, etc.)"""
    type: str  # 'class', 'method', 'function', 'field', 'import', 'variable'
    name: str
    line_start: int
    line_end: int
    visibility: Optional[str] = None  # public, private, protected
    parent: Optional[str] = None
    children: List['CodeElement'] = field(default_factory=list)
    signature: Optional[str] = None
    decorators: List[str] = field(default_factory=list)  # Python decorators
    annotations: List[str] = field(default_factory=list)  # Java annotations
    raw_text: Optional[str] = None  # For debugging
    
    @property
    def size(self) -> int:
        """Number of lines in this element"""
        return self.line_end - self.line_start + 1