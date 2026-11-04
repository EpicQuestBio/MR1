#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
Test Signal Viewer Bundle Parity
================================
Validates that signal-viewer/standalone.html stays synchronized with index.html,
styles.css, src/signal.js, and src/app.js.
"""

import unittest
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import bundle_signal_viewer


class TestSignalViewerBundle(unittest.TestCase):
    def test_standalone_bundle_parity(self):
        bundle = bundle_signal_viewer.generate_bundle()
        self.assertTrue(os.path.exists(bundle_signal_viewer.STANDALONE_HTML_PATH))
        with open(bundle_signal_viewer.STANDALONE_HTML_PATH, "r", encoding="utf-8") as f:
            existing = f.read()
        self.assertEqual(
            existing.strip(),
            bundle.strip(),
            "standalone.html is out of sync! Run: python3 scripts/bundle_signal_viewer.py"
        )


if __name__ == "__main__":
    unittest.main()
