#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Utility functions for the show_structure_ast package

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import sys
import logging
import traceback
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def safe_analyzer_context():
    """Context manager for safe analyzer execution"""
    try:
        yield
    except KeyboardInterrupt:
        logger.info("\nOperation interrupted by user")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)