#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0
"""
test_run_python_script.py
=========================
Validates the `scripts/run_python.sh` virtual environment wrapper script:
- Correct execution and exit code forwarding.
- Argument passing (CLI flags, strings, evaluation flags).
- Working directory flexibility (from repo root and inside scripts/).
- Module resolution with PYTHONPATH configured to repository root (importing build123d and src).
"""

import os
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_python.sh"


class TestRunPythonScript(unittest.TestCase):
    def test_script_exists_and_executable(self):
        self.assertTrue(SCRIPT_PATH.is_file(), "scripts/run_python.sh must exist")
        self.assertTrue(os.access(SCRIPT_PATH, os.X_OK), "scripts/run_python.sh must be executable")
        # Ensure root directory does not contain duplicate run_python.sh
        root_script = REPO_ROOT / "run_python.sh"
        self.assertFalse(root_script.exists(), "run_python.sh should only exist in scripts/")

    def test_executes_simple_python_command(self):
        res = subprocess.run(
            [str(SCRIPT_PATH), "-c", "import sys; print('PYTHON_OK', sys.version_info.major)"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("PYTHON_OK 3", res.stdout)

    def test_imports_build123d_and_src_modules(self):
        res = subprocess.run(
            [
                str(SCRIPT_PATH),
                "-c",
                "import build123d; import src.constants; print('IMPORTS_SUCCESS')",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("IMPORTS_SUCCESS", res.stdout)

    def test_run_from_scripts_directory(self):
        # Reproduces the user's exact scenario from `scripts/`:
        # loki@loki-omega:~/Projects/MR1/scripts$ ./run_python.sh generate_footprint.py --help
        res = subprocess.run(
            ["./run_python.sh", "generate_footprint.py", "--help"],
            cwd=REPO_ROOT / "scripts",
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("generate_footprint.py", res.stdout)
        self.assertIn("--pins", res.stdout)

    def test_exit_code_forwarding(self):
        res = subprocess.run(
            [str(SCRIPT_PATH), "-c", "import sys; sys.exit(42)"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 42)


if __name__ == "__main__":
    unittest.main()
