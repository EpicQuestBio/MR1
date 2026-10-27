# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
test_multi_stage_casting_molds.py

Unit tests for the multi-stage concentric 3D-guarded resin cast molds:
1. Validates Concentric_Guard_Mold_Plate_Top geometry and volume.
2. Validates Bottom_Fluidic_Electrode_Mold_Plate geometry and volume.
3. Validates MidLayer_PVA_Alignment_Frame geometry and volume.
4. Validates MultiStage_Interposer_Mold_Assembly composition.
5. Validates multi_stage_guard=True parameter on Nanopore_Wafer_Mold_Left / Right.
"""

import unittest
from build123d import *
from src.constants import *
from src.nanopore_wafer_mold import (
    Nanopore_Wafer_Mold_Left,
    Nanopore_Wafer_Mold_Right,
    Concentric_Guard_Mold_Plate_Top,
    Bottom_Fluidic_Electrode_Mold_Plate,
    MidLayer_PVA_Alignment_Frame,
    MultiStage_Interposer_Mold_Assembly,
)

class TestMultiStageCastingMolds(unittest.TestCase):

    def test_concentric_guard_mold_plate_top(self):
        """Verify the top concentric guard mold plate generates a valid BREP solid with expected cavities."""
        plate = Concentric_Guard_Mold_Plate_Top()
        self.assertIsNotNone(plate)
        self.assertTrue(plate.is_valid, "Concentric_Guard_Mold_Plate_Top must be a valid solid")
        self.assertGreater(plate.volume, 80000.0, "Top mold plate volume must match standard half-mold scale")
        bb = plate.bounding_box()
        self.assertAlmostEqual(bb.size.Y, MOLD_W, delta=0.5)
        self.assertAlmostEqual(bb.size.Z, MOLD_H, delta=0.5)

    def test_bottom_fluidic_electrode_mold_plate(self):
        """Verify the bottom fluidic / electrode mold plate generates a valid solid with crush-rib grooves."""
        plate = Bottom_Fluidic_Electrode_Mold_Plate()
        self.assertIsNotNone(plate)
        self.assertTrue(plate.is_valid, "Bottom_Fluidic_Electrode_Mold_Plate must be a valid solid")
        self.assertGreater(plate.volume, 80000.0, "Bottom mold plate volume must match standard half-mold scale")
        bb = plate.bounding_box()
        self.assertAlmostEqual(bb.size.Y, MOLD_W, delta=0.5)
        self.assertAlmostEqual(bb.size.Z, MOLD_H, delta=0.5)

    def test_midlayer_pva_alignment_frame(self):
        """Verify the mid-layer PVA channel core alignment frame generates valid geometry."""
        frame = MidLayer_PVA_Alignment_Frame()
        self.assertIsNotNone(frame)
        self.assertTrue(frame.is_valid, "MidLayer_PVA_Alignment_Frame must be a valid solid")
        self.assertGreater(frame.volume, 1000.0, "Frame volume must be positive")
        bb = frame.bounding_box()
        self.assertAlmostEqual(bb.size.Z, 0.8, delta=0.05, msg="Frame thickness must be 0.8mm")

    def test_multistage_interposer_mold_assembly(self):
        """Verify the complete 3-part multi-stage mold assembly instantiates all three components."""
        assembly = MultiStage_Interposer_Mold_Assembly(explode=10.0)
        self.assertEqual(len(assembly), 3, "Assembly must contain Top, Mid-Frame, and Bottom mold plates")
        for i, part in enumerate(assembly):
            self.assertTrue(part.is_valid, f"Assembly part {i} must be valid")

    def test_multi_stage_guard_parameter_parity(self):
        """Verify multi_stage_guard=True produces valid mold halves without breaking default signatures."""
        left_guard = Nanopore_Wafer_Mold_Left(is_nanopore=True, multi_stage_guard=True)
        right_guard = Nanopore_Wafer_Mold_Right(is_nanopore=True, multi_stage_guard=True)

        self.assertTrue(left_guard.is_valid)
        self.assertTrue(right_guard.is_valid)

        # Volume comparison: subtractive guard grooves reduce volume slightly
        left_std = Nanopore_Wafer_Mold_Left(is_nanopore=True, multi_stage_guard=False)
        right_std = Nanopore_Wafer_Mold_Right(is_nanopore=True, multi_stage_guard=False)

        self.assertLess(left_guard.volume, left_std.volume, "Guarded left mold has subtractive guard cavities")
        self.assertLess(right_guard.volume, right_std.volume, "Guarded right mold has subtractive crush-rib grooves")

if __name__ == "__main__":
    unittest.main()
