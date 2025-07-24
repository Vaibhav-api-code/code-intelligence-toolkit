#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Content preprocessing for code analysis

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import re
import logging
from typing import Tuple, Dict, List

logger = logging.getLogger(__name__)


class ContentPreprocessor:
    """Pre-processes code content to handle string literals and comments"""
    
    @staticmethod
    def should_preprocess(content: str, language: str) -> bool:
        """Determine if preprocessing is needed based on content characteristics"""
        # For small files, preprocessing overhead isn't worth it
        if len(content) < 50000:  # ~1000 lines
            return False
        
        # Check for complex string patterns that might confuse regex
        complex_patterns = [
            r'"\\s*{',  # String containing brace
            r'{\\s*"',  # Brace followed by string
            r'/\*.*\*/',  # Multi-line comments
            r'"[^"]*\\\\[^"]*"',  # Escaped quotes in strings
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, content[:5000]):  # Check first part only
                return True
        
        return False
    
    @staticmethod
    def strip_strings_and_comments_simple(content: str, language: str) -> str:
        """Simplified preprocessing - just remove obvious comments"""
        try:
            if language == 'java':
                # Remove single-line comments
                content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
                # Remove multi-line comments (simple cases)
                content = re.sub(r'/\*[^*]*\*/', '', content, flags=re.DOTALL)
        except Exception as e:
            logger.debug(f"Preprocessing error: {e}")
            # Return original content if preprocessing fails
            return content
        return content