#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test Refactor Rename

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import tempfile
import unittest
from pathlib import Path

import refactor_rename as rr

class RefactorRenameTests(unittest.TestCase):

    def test_rename_file_atomic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                src = Path("old_name.py")
                src.write_text("print('hello')")
                renamer = rr.CodeRefactorRenamer(dry_run=False, verbose=False)
                dest = Path("new_name.py")
                renamer.rename_file(src, dest)
                self.assertTrue(dest.exists())
                self.assertFalse(src.exists())
                self.assertEqual(dest.read_text(), "print('hello')")
            finally:
                os.chdir(cwd)
