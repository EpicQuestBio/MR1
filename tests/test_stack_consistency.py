# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0
"""
tests/test_stack_consistency.py
===============================
Formal consistency test verifying that:
  1. Amplifier.kicad_pcb pin placements match src/stack_spec.py
  2. All 12 pogo pins are placed on F.Cu (component side)
  3. CAD pogo-pin solid array matches spec pin coordinates
  4. build123d CAD interposer fluid ports match spec.FLUID_HOLES
  5. The pogo gap budget and discrete spacer combinations satisfy stroke constraints
"""

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src import stack_spec as spec
from scripts.generate_footprint import cross_check_cad, extract_pin_placements_from_pcb
from src.spacers import Pogo_Pin_Array_Solid


class TestStackConsistency(unittest.TestCase):
    def test_stack_spec_validity(self):
        problems = spec.validate()
        self.assertEqual(problems, [], f"stack_spec validation failed: {problems}")

    def test_cad_matches_spec(self):
        mismatches = cross_check_cad()
        self.assertEqual(mismatches, [], f"CAD geometry disagrees with stack_spec: {mismatches}")

    def test_amplifier_pcb_pins_match_spec(self):
        pcb_path = REPO_ROOT / "Amplifier" / "Amplifier.kicad_pcb"
        self.assertTrue(pcb_path.exists(), "Amplifier.kicad_pcb must exist")

        placements = extract_pin_placements_from_pcb(pcb_path)
        self.assertEqual(len(placements), 12, "Must find exactly 12 pogo pin footprints on Amplifier PCB")

        # All pins must be on F.Cu
        for ref, info in placements.items():
            self.assertEqual(info["layer"], "F.Cu", f"{ref} must be placed on F.Cu (component side)")

        # Verify relative pin-to-pin vectors match spec
        p1 = placements["P1"]
        p1_spec = spec.pin(1)
        kicad_p1_x, kicad_p1_y = spec.kicad_xy(p1_spec.x, p1_spec.y)

        # Inferred board origin (X0, Y0)
        x0 = p1["x"] - kicad_p1_x
        y0 = p1["y"] - kicad_p1_y

        for p_spec in spec.PINS:
            ref = p_spec.ref
            self.assertIn(ref, placements, f"{ref} missing from PCB placements")
            actual = placements[ref]
            expected_kx, expected_ky = spec.kicad_xy(p_spec.x, p_spec.y)
            expected_x = x0 + expected_kx
            expected_y = y0 + expected_ky
            self.assertAlmostEqual(actual["x"], expected_x, places=2,
                                   msg=f"{ref} X coord mismatch: actual={actual['x']}, expected={expected_x}")
            self.assertAlmostEqual(actual["y"], expected_y, places=2,
                                   msg=f"{ref} Y coord mismatch: actual={actual['y']}, expected={expected_y}")

    def test_cad_pogo_pin_array_matches_spec(self):
        pa = Pogo_Pin_Array_Solid(compressed=True)
        self.assertEqual(len(pa.children), 12)
        centers = [(child.bounding_box().center().X, child.bounding_box().center().Y)
                   for child in pa.children]
        for p in spec.PINS:
            self.assertTrue(
                any(abs(p.x - cx) < 0.01 and abs(p.y - cy) < 0.01 for cx, cy in centers),
                f"P{p.number} ({p.x}, {p.y}) not found in array centers: {centers}"
            )


if __name__ == "__main__":
    unittest.main()
