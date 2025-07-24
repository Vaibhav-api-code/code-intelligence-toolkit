#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test Organize Files

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import tempfile
import unittest
from pathlib import Path
from organize_files import FileOrganizer

class OrganizeFilesTests(unittest.TestCase):

    def test_move_file_via_safe_mover(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            dst_dir = Path(tmpdir) / "dst"
            src_dir.mkdir()
            dst_dir.mkdir()
            file_path = src_dir / "item.txt"
            file_path.write_text("payload")

            organizer = FileOrganizer(dry_run=False, verbose=False)
            moved = organizer.safe_move_file(file_path, dst_dir)

            self.assertTrue(moved)
            self.assertFalse(file_path.exists())
            self.assertTrue((dst_dir / "item.txt").exists())
