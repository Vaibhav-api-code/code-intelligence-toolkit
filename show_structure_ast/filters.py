#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filtering logic for code elements

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import argparse
import logging
from typing import Optional, List, Pattern

logger = logging.getLogger(__name__)


class FilterContext:
    """Context for early filtering during traversal"""
    def __init__(self, options: argparse.Namespace):
        self.options = options
        self.name_pattern = None
        if options.filter_name:
            try:
                self.name_pattern = re.compile(options.filter_name)
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{options.filter_name}': {e}")
        
        self.filter_visibility = set(options.filter_visibility) if options.filter_visibility else None
        self.filter_decorator = options.filter_decorator
        self.filter_annotation = getattr(options, 'filter_annotation', None)  # Java annotations
        self.max_depth = options.max_depth
        self.include_imports = options.include_imports
        self.include_fields = options.include_fields
        self.include_variables = options.include_variables
    
    def should_process_element(self, elem_type: str, name: str, visibility: Optional[str] = None,
                             decorators: Optional[List[str]] = None, depth: int = 0,
                             annotations: Optional[List[str]] = None) -> bool:
        """Check if element should be processed based on filters"""
        # Early termination for max depth
        if self.max_depth is not None and depth > self.max_depth:
            return False
        
        # Type filters
        if elem_type == 'import' and not self.include_imports:
            return False
        if elem_type == 'field' and not self.include_fields:
            return False
        if elem_type == 'variable' and not self.include_variables:
            return False
        
        # Name filter
        if self.name_pattern and not self.name_pattern.search(name):
            return False
        
        # Visibility filter
        if self.filter_visibility and visibility and visibility not in self.filter_visibility:
            return False
        
        # Note: Decorator and annotation filters are handled in post-processing
        # to preserve parent-child relationships. Early filtering only applies
        # to type, name, and visibility filters.
        
        return True
    
    def should_traverse_children(self, depth: int) -> bool:
        """Check if we should traverse children based on depth"""
        return self.max_depth is None or depth < self.max_depth