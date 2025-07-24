#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Replace exact text occurrences without recursive replacement."""

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

def replace_exact(content, old_text, new_text, count=-1):
    """Replace exact text occurrences without recursive replacement."""
    if old_text == new_text:
        return content
    
    # Find all positions first (before any replacements)
    positions = []
    start = 0
    while True:
        pos = content.find(old_text, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + len(old_text)
    
    # Apply count limit if specified
    if count > 0:
        positions = positions[:count]
    
    # If no positions found, return original
    if not positions:
        return content
    
    # Build the result by reconstructing the string with replacements
    # This avoids the recursive replacement issue entirely
    result = []
    last_end = 0
    
    for pos in positions:
        # Add the part before this match
        result.append(content[last_end:pos])
        # Add the replacement
        result.append(new_text)
        # Update position
        last_end = pos + len(old_text)
    
    # Add any remaining content after the last match
    result.append(content[last_end:])
    
    return ''.join(result)

# Test case
content = 'price priceinticks'
result = replace_exact(content, 'price', 'priceinticks')
print(f'Input: {repr(content)}')
print(f'Output: {repr(result)}')
print(f'Expected: {repr("priceinticks priceinticks")}')
print(f'Correct: {result == "priceinticks priceinticks"}')

# Debug positions
positions = []
start = 0
while True:
    pos = content.find('price', start)
    if pos == -1:
        break
    positions.append(pos)
    start = pos + len('price')
print(f'Positions found: {positions}')
