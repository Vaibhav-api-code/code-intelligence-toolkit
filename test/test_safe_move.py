#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test Safe Move

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import json
import threading
import tempfile
import unittest
import importlib
from pathlib import Path

class SafeMoveAtomicTests(unittest.TestCase):
    def setUp(self):
        # Isolate SAFEMOVE env to a tmp dir
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base_path = Path(self.tmp.name)
        self.history = self.base_path / "history.log"
        self.trash = self.base_path / "trash"
        os.environ["SAFE_MOVE_HISTORY"] = str(self.history)
        os.environ["SAFE_MOVE_TRASH"] = str(self.trash)

        # Reload module after patching env
        import safe_move as _sm
        import importlib
        importlib.reload(_sm)
        self.sm = _sm
        self.mover = self.sm.SafeMover(dry_run=False, verbose=False, 
                                        undo_log=self.history, 
                                        trash_dir=self.trash)

        # IO sandbox
        self.src_dir = self.base_path / "src"
        self.dst_dir = self.base_path / "dst"
        self.src_dir.mkdir()
        self.dst_dir.mkdir()

    def _make_file(self, directory: Path, name: str, content: str = "x"):
        p = directory / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_single_atomic_move(self):
        src = self._make_file(self.src_dir, "a.txt", "abc")
        dest = self.dst_dir / "a.txt"
        self.assertTrue(self.mover.safe_move(src, dest))
        self.assertFalse(src.exists())
        self.assertEqual(dest.read_text(), "abc")
        # valid undo JSON
        with self.history.open() as fh:
            entry = json.loads(fh.readline())
            self.assertEqual(entry["op_type"], "move")
            self.assertEqual(entry["source"], str(src))
            self.assertEqual(entry["dest"], str(dest))

    def test_thread_safe_history_and_atomicity(self):
        # spawn several concurrent moves
        def worker(idx: int):
            s = self._make_file(self.src_dir, f"f{idx}.dat", str(idx))
            d = self.dst_dir / f"f{idx}.dat"
            self.mover.safe_move(s, d)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(25)]
        for t in threads: t.start()
        for t in threads: t.join()

        for i in range(25):
            dest = self.dst_dir / f"f{i}.dat"
            self.assertTrue(dest.exists(), f"dest {dest} missing")
            self.assertEqual(dest.read_text(), str(i))

        # history lines == moves executed (25 from this test only, each test has its own history)
        self.assertEqual(len(self.history.read_text().splitlines()), 25)
