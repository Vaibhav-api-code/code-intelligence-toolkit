#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Verify Replacement

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

# The content is "price priceinticks"
# Finding all occurrences of "price":
# Position 0: "price" (standalone)
# Position 6: "price" (within "priceinticks")

# So replacing both with "priceinticks" gives:
# Position 0: "price" -> "priceinticks"
# Position 6: "price" (in "priceinticks") -> "priceinticks"

# Result: "priceinticks priceinticksinticks"

# This is CORRECT behavior\! The test expectation is wrong.
# If you want to avoid this, you should use --whole-word flag\!

print("Testing whole-word replacement:")
import subprocess
import tempfile

content = 'price priceinticks'
with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
    f.write(content)
    filepath = f.name

result = subprocess.run(['python3', 'replace_text.py', filepath, 'price', 'priceinticks', '--whole-word'], 
                      capture_output=True, text=True, input='y\n')

with open(filepath, 'r') as f:
    final_content = f.read()

print(f'Original: {repr(content)}')
print(f'Final: {repr(final_content)}')
print(f'This should be: "priceinticks priceinticks"')

import os
os.unlink(filepath)
