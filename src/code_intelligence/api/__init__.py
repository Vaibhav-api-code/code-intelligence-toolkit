#!/usr/bin/env python3
"""
API Module - Unified interface to toolkit operations

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from .client import CodeIntelligenceAPI

__all__ = [
    "CodeIntelligenceAPI",
]