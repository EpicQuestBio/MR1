# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0
"""Tests for src/spacers.py (pogo pin CAD models, PP shim, Delrin block, and printed spacer)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import stack_spec as spec
from src.spacers import (
    Delrin_Block,
    PP_Shim,
    Pogo_Pin_Array_Solid,
    Pogo_Pin_Solid,
    Printed_Spacer,
)


class TestSpacersCAD(unittest.TestCase):
    def test_pogo_pin_dimensions(self):
        compressed = Pogo_Pin_Solid(compressed=True)
        uncompressed = Pogo_Pin_Solid(compressed=False)
        self.assertTrue(compressed.is_valid)
        self.assertTrue(uncompressed.is_valid)
        self.assertAlmostEqual(compressed.bounding_box().size.Z, spec.POGO.working_height, places=3)
        self.assertAlmostEqual(uncompressed.bounding_box().size.Z, spec.POGO.free_length, places=3)
        self.assertGreater(uncompressed.volume, compressed.volume)

    def test_pogo_pin_array_count_and_positions(self):
        pa = Pogo_Pin_Array_Solid()
        self.assertEqual(len(pa.children), 12)
        centers = [(child.bounding_box().center().X, child.bounding_box().center().Y)
                   for child in pa.children]
        for p in spec.PINS:
            self.assertTrue(
                any(abs(p.x - cx) < 0.01 and abs(p.y - cy) < 0.01 for cx, cy in centers),
                f"P{p.number} ({p.x}, {p.y}) not found in array centers: {centers}"
            )

    def test_pp_shim(self):
        shim = PP_Shim()
        self.assertTrue(shim.is_valid)
        self.assertAlmostEqual(shim.bounding_box().size.Z, spec.PP_SHIM, places=3)

    def test_delrin_block(self):
        d1 = Delrin_Block(thickness=spec.DELRIN_THIN)
        d2 = Delrin_Block(thickness=spec.DELRIN_THICK)
        self.assertTrue(d1.is_valid)
        self.assertTrue(d2.is_valid)
        self.assertAlmostEqual(d1.bounding_box().size.Z, spec.DELRIN_THIN, places=3)
        self.assertAlmostEqual(d2.bounding_box().size.Z, spec.DELRIN_THICK, places=3)

    def test_printed_spacer_height_validation(self):
        with self.assertRaises(ValueError):
            Printed_Spacer(height=2.0)  # below PRINTED_MIN (3.0mm)

        sp = Printed_Spacer(height=3.6)
        self.assertTrue(sp.is_valid)
        self.assertAlmostEqual(sp.bounding_box().size.Z, 3.6, places=3)


if __name__ == "__main__":
    unittest.main()
