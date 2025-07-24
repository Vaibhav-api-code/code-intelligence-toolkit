#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test Preflight Checks

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

from preflight_checks import PreflightChecker

def test_preflight_checks():
    # Test check_file_readable
    success, message = PreflightChecker.check_file_readable(__file__)
    print(f"Check file readable: {success}, {message}")
    assert success == True

    # Test check_directory_accessible
    success, message = PreflightChecker.check_directory_accessible(".")
    print(f"Check directory accessible: {success}, {message}")
    assert success == True

    # Test validate_method_name
    success, message = PreflightChecker.validate_method_name("myMethod")
    print(f"Validate method name: {success}, {message}")
    assert success == True

    success, message = PreflightChecker.validate_method_name("invalid-method")
    print(f"Validate invalid method name: {success}, {message}")
    assert success == False

test_preflight_checks()
