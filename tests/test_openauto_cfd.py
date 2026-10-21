#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
tests/test_openauto_cfd.py

Unit and integration tests for OpenAuto-CFD support:
1. Validates openauto.project.json manifest integrity, board registrations, and fluidics specifications.
2. Tests the OpenAuto-CFD KiCad Plugin & Co-Design Synchronizer across all boards.
3. Tests Edge.Cuts continuity and boundary assertions for KiCad / CFD geometry coupling.
4. Verifies 3D Visualizer assembly components and flexible routing splines.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "openauto.project.json"
PLUGIN_SCRIPT = REPO_ROOT / "plugins" / "openauto_cfd_plugin.py"


class TestOpenAutoCFD(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MANIFEST_PATH.exists(), "openauto.project.json must exist in repo root")
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def test_manifest_structure_and_boards(self):
        """Verify openauto.project.json contains all required architectural sections and boards."""
        required_sections = ["project_id", "boards", "mechanical", "fluidics", "cosimulation", "harnesses"]
        for sec in required_sections:
            self.assertIn(sec, self.manifest, f"Manifest must contain section '{sec}'")

        required_boards = ["amplifier", "mr1", "pump", "interposer"]
        boards = self.manifest.get("boards", {})
        for b in required_boards:
            self.assertIn(b, boards, f"Board '{b}' must be registered in openauto.project.json")
            board_meta = boards[b]
            pcb_file = REPO_ROOT / board_meta["path"]
            self.assertTrue(pcb_file.exists(), f"Board PCB file '{pcb_file}' must exist on disk")

    def test_fluidic_and_cosimulation_parameters(self):
        """Verify fluidic microchannel constraints and co-simulation physics bindings."""
        fluidics = self.manifest.get("fluidics", {})
        self.assertEqual(fluidics.get("channel_width_um"), 50)
        self.assertEqual(fluidics.get("channel_height_um"), 25)
        self.assertEqual(fluidics.get("pore_diameter_nm"), 4.0)
        self.assertEqual(fluidics.get("flow_rate_ul_min"), 10.0)
        self.assertIn("KCl", fluidics.get("buffer", ""))

        cosim = self.manifest.get("cosimulation", {})
        self.assertTrue(cosim.get("enabled", False), "Co-simulation must be enabled in openauto.project.json")
        self.assertIn("amplifier", cosim.get("circuits", []))
        self.assertIn("fluidic_transport", cosim.get("physics", []))
        self.assertIn("translocation_current", cosim.get("physics", []))

    def test_openauto_kicad_plugin_python_api(self):
        """Verify OpenAutoCFDSynchronizer validates all boards with zero errors."""
        from plugins.openauto_cfd_plugin import OpenAutoCFDSynchronizer

        sync = OpenAutoCFDSynchronizer(MANIFEST_PATH)
        report = sync.validate_all()
        self.assertTrue(report["all_valid"], f"All boards must pass OpenAuto-CFD validation: {report}")

        # Check Interposer specific parameters
        int_res = report["boards"]["interposer"]
        self.assertTrue(int_res["valid"])
        self.assertTrue(int_res["continuity"]["is_closed"])
        self.assertAlmostEqual(int_res["bounds"]["width"], 55.0, delta=0.5)
        self.assertAlmostEqual(int_res["bounds"]["height"], 51.96, delta=0.5)

        # Check Amplifier specific parameters
        amp_res = report["boards"]["amplifier"]
        self.assertTrue(amp_res["valid"])
        self.assertTrue(amp_res["continuity"]["is_closed"])
        self.assertAlmostEqual(amp_res["bounds"]["width"], 55.0, delta=0.5)

        # Check MR1 motherboard parameters
        mr1_res = report["boards"]["mr1"]
        self.assertTrue(mr1_res["valid"])
        self.assertTrue(mr1_res["continuity"]["is_closed"])
        self.assertAlmostEqual(mr1_res["bounds"]["width"], 80.0, delta=1.0)
        self.assertAlmostEqual(mr1_res["bounds"]["height"], 60.0, delta=1.0)

        # Check Pump controller board parameters
        pump_res = report["boards"]["pump"]
        self.assertTrue(pump_res["valid"])
        self.assertTrue(pump_res["continuity"]["is_closed"])
        self.assertAlmostEqual(pump_res["bounds"]["width"], 88.0, delta=1.0)
        self.assertAlmostEqual(pump_res["bounds"]["height"], 88.0, delta=1.0)

    def test_openauto_kicad_plugin_cli_execution(self):
        """Verify the OpenAuto KiCad plugin CLI executes cleanly with code 0."""
        self.assertTrue(PLUGIN_SCRIPT.exists(), f"Plugin script '{PLUGIN_SCRIPT}' must exist")
        cmd = [sys.executable, str(PLUGIN_SCRIPT), "--validate-all"]
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI command failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
        self.assertIn("[PASS] Board: amplifier", res.stdout)
        self.assertIn("[PASS] Board: interposer", res.stdout)
        self.assertIn("[PASS] Board: mr1", res.stdout)
        self.assertIn("[PASS] Board: pump", res.stdout)

    def test_visualizer_assembly_and_routing_api(self):
        """Verify that src/assembly.py provides all assembly and routing functions for the visualizer."""
        from src.assembly import (
            Reader_Module_Assembly,
            Pump_Module_Assembly,
            route_tubing,
            route_wiring,
            get_tubing_routes,
            get_wiring_routes,
        )

        tubing_routes = get_tubing_routes()
        self.assertEqual(len(tubing_routes), 5, "Visualizer must define all 5 fluid tubing lines")
        for line_name in ["TUBE_PUMP", "TUBE_FEED", "TUBE_TRANS_LINE", "TUBE_WASTE_1", "TUBE_WASTE_2"]:
            self.assertIn(line_name, tubing_routes)

        wiring_routes = get_wiring_routes()
        self.assertEqual(len(wiring_routes), 3, "Visualizer must define all 3 wiring harnesses")
        for wire_name in ["W_USB", "W_MOTOR", "W_POGO_ANALOG"]:
            self.assertIn(wire_name, wiring_routes)


if __name__ == "__main__":
    unittest.main()
