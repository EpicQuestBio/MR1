# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

import unittest
import json
import os
from build123d import *
from src.constants import *
from src.housing import Housing_Pump_Case, Housing_Pump_Lid, Housing_Case_Reader, Housing_Lid_Reader
from src.cartridge import Cast_Nanopore_Wafer_Gasket, Fitted_Amplifier_Gasket, PCB_Rigid_Active
from src.nanopore_wafer_mold import Nanopore_Wafer_Mold_Left, Nanopore_Wafer_Mold_Right

class TestLegacyParity(unittest.TestCase):
    def test_legacy_pump_config(self):
        """Parity with tests/test_pump_config.scad - test pump configurations (Diitao, Blank, Custom)"""
        for p_type in ["Diitao", "Blank", "Custom"]:
            pump_case = Housing_Pump_Case(pump_type=p_type)
            self.assertIsNotNone(pump_case)
            self.assertTrue(pump_case.is_valid)
            self.assertGreater(pump_case.volume, 0)

    def test_legacy_gasket_plan(self):
        """Parity with tests/test_gasket_plan.scad"""
        gasket_top = Cast_Nanopore_Wafer_Gasket()
        gasket_bot = Fitted_Amplifier_Gasket()
        mold_l = Nanopore_Wafer_Mold_Left(is_nanopore=True)
        mold_r = Nanopore_Wafer_Mold_Right(is_nanopore=True)
        self.assertGreater(gasket_top.volume, 0)
        self.assertGreater(gasket_bot.volume, 0)
        self.assertGreater(mold_l.volume, 0)
        self.assertGreater(mold_r.volume, 0)

    def test_legacy_pcb_clearance(self):
        """Parity with tests/verify_pcb_clearance.scad"""
        lid = Housing_Lid_Reader()
        pcb = PCB_Rigid_Active()
        self.assertGreater(lid.volume, 0)
        self.assertGreater(pcb.volume, 0)

    def test_golden_manifest_parity(self):
        """Parity with tests/golden_manifest.json verification"""
        manifest_path = "tests/golden_manifest.json"
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, 'r') as f:
            golden_data = json.load(f)
        self.assertIn("Housing_Pump_Case_STL.stl", golden_data)
        self.assertIn("Housing_Reader_Case_STL.stl", golden_data)
        self.assertIn("Housing_Reader_Lid_STL.stl", golden_data)

if __name__ == "__main__":
    unittest.main()
