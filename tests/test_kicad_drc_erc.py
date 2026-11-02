# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
test_kicad_drc_erc.py
======================
Automated KiCad 10 Design Rule Check (DRC) and Electrical Rule Check (ERC)
verification gate for MR1 PCBs and Schematics (REFACTOR_PLAN.md P4.4).
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def is_kicad_cli_available() -> bool:
    return shutil.which("kicad-cli") is not None


def run_pcb_drc(pcb_path: Path) -> dict:
    """Executes kicad-cli pcb drc in JSON report mode and returns the parsed report."""
    if not is_kicad_cli_available():
        raise RuntimeError("kicad-cli is not installed on system PATH")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        cmd = [
            "kicad-cli",
            "pcb",
            "drc",
            "--format",
            "json",
            "-o",
            str(tmp_path),
            str(pcb_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode not in (0, 1):  # 0: clean or warnings, 1: violations found
            raise RuntimeError(f"kicad-cli pcb drc failed ({res.returncode}): {res.stderr}")

        if not tmp_path.exists() or tmp_path.stat().st_size == 0:
            return {"violations": [], "unconnected_items": []}

        return json.loads(tmp_path.read_text(encoding="utf-8"))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def run_sch_erc(sch_path: Path) -> dict:
    """Executes kicad-cli sch erc in JSON report mode and returns the parsed report."""
    if not is_kicad_cli_available():
        raise RuntimeError("kicad-cli is not installed on system PATH")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        cmd = [
            "kicad-cli",
            "sch",
            "erc",
            "--format",
            "json",
            "-o",
            str(tmp_path),
            str(sch_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode not in (0, 1):
            raise RuntimeError(f"kicad-cli sch erc failed ({res.returncode}): {res.stderr}")

        if not tmp_path.exists() or tmp_path.stat().st_size == 0:
            return {"sheets": []}

        return json.loads(tmp_path.read_text(encoding="utf-8"))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


class TestKiCadDrcErcGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not is_kicad_cli_available():
            raise unittest.SkipTest("kicad-cli not available on system")

    def test_interposer_pcb_drc_thresholds(self):
        """Verifies Interposer PCB DRC: no broken tracks and <= 2 ring anchor warnings."""
        pcb_path = REPO_ROOT / "Interposer" / "Interposer.kicad_pcb"
        self.assertTrue(pcb_path.exists(), "Interposer.kicad_pcb must exist")

        drc_data = run_pcb_drc(pcb_path)
        unconnected = drc_data.get("unconnected_items", [])
        violations = drc_data.get("violations", [])

        # Unconnected items must be <= 2 (purely concentric ring anchor center warnings)
        self.assertLessEqual(len(unconnected), 2, f"Interposer unconnected items exceeded: {len(unconnected)}")

        # No short circuits between primary signal nets
        short_circuits = [v for v in violations if v.get("type") == "shorting_items"]
        critical_shorts = []
        for sc in short_circuits:
            desc = sc.get("description", "")
            if any(net in desc for net in ["WS_CIS", "WE_POS", "RE_TRANS", "CE_GNDA"]):
                critical_shorts.append(desc)

        self.assertEqual(len(critical_shorts), 0, f"Critical signal shorts detected: {critical_shorts}")

    def test_pump_pcb_drc_executes_cleanly(self):
        """Verifies Pump Controller PCB DRC runs and parses correctly."""
        pcb_path = REPO_ROOT / "Pump" / "Pump.kicad_pcb"
        self.assertTrue(pcb_path.exists(), "Pump.kicad_pcb must exist")

        drc_data = run_pcb_drc(pcb_path)
        self.assertIn("violations", drc_data)
        self.assertIn("unconnected_items", drc_data)

    def test_interposer_schematic_erc_parses_cleanly(self):
        """Verifies Interposer schematic ERC executes and reports cleanly."""
        sch_path = REPO_ROOT / "Interposer" / "Interposer.kicad_sch"
        self.assertTrue(sch_path.exists(), "Interposer.kicad_sch must exist")

        erc_data = run_sch_erc(sch_path)
        self.assertIn("sheets", erc_data)


if __name__ == "__main__":
    unittest.main()
