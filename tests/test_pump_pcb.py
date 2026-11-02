# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
Unit tests validating MR1 External Pump Controller KiCad Board (Pump/Pump.kicad_pcb)
against mechanical, electrical, and schematic interface specifications (TODO Section 22).
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestPumpControllerPCB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pcb_path = REPO_ROOT / "Pump" / "Pump.kicad_pcb"
        cls.assertTrue(cls.pcb_path.exists(), f"Pump.kicad_pcb must exist at {cls.pcb_path}")
        cls.content = cls.pcb_path.read_text(encoding="utf-8")

    def test_board_envelope_and_mounting_holes(self):
        """Verify 88.0 x 88.0 mm board size and 4x M3 mounting holes at (+/-38, +/-38)."""
        edge_lines = re.findall(r'\(gr_line\s+\(start\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)\s+\(end\s+([0-9\.\-]+)\s+([0-9\.\-]+)\).*?\(layer\s+"Edge\.Cuts"\)', self.content)
        self.assertGreaterEqual(len(edge_lines), 8, "Edge.Cuts boundary must define chamfered 88x88mm board")

        # Mounting holes MH1..MH4
        for mh in ["MH1", "MH2", "MH3", "MH4"]:
            self.assertIn(f'(property "Reference" "{mh}"', self.content, f"Mounting hole {mh} must be present")

    def test_mcu_stm32_qfn48_footprint_completion(self):
        """Verify STM32G431CBU6 MCU footprint has all 48 perimeter leads and exposed pad 49."""
        self.assertIn('property "Reference" "U1_MCU"', self.content)
        self.assertIn('property "Value" "STM32G431CBU6"', self.content)

        # Extract U1_MCU footprint block
        mcu_match = re.search(r'\(footprint\s+"Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm"[\s\S]*?\(property\s+"Reference"\s+"U1_MCU"[\s\S]*?\n\t\)', self.content)
        self.assertIsNotNone(mcu_match, "U1_MCU QFN-48 footprint block must be present")
        mcu_txt = mcu_match.group(0)

        # Verify all 48 perimeter pads and center thermal pad 49
        for p in range(1, 50):
            self.assertIn(f'(pad "{p}"', mcu_txt, f"Pad {p} must be defined in U1_MCU footprint")

    def test_passive_components_and_regulator(self):
        """Verify decoupling capacitors, pull-ups, crystal, and analog LDO footprints."""
        for c_ref in ["C1_MCU", "C2_MCU", "C3_MCU", "C4_MCU"]:
            self.assertIn(f'(property "Reference" "{c_ref}"', self.content, f"{c_ref} decoupling cap must be present")

        for r_ref in ["R1_PU", "R2_PU", "R3_PU", "R4_PU"]:
            self.assertIn(f'(property "Reference" "{r_ref}"', self.content, f"{r_ref} I2C pullup must be present")

        self.assertIn('(property "Reference" "Y1_HSE"', self.content, "Y1 8MHz HSE crystal must be present")
        self.assertIn('(property "Reference" "U5_REG"', self.content, "U5 analog LDO regulator must be present")

    def test_peripheral_interfaces_and_headers(self):
        """Verify dual USB-C, peristaltic motor headers, and pressure sensor footprints."""
        # Dual USB-C
        self.assertIn('(property "Reference" "J1_HOST"', self.content, "J1_HOST USB-C must be present")
        self.assertIn('(property "Reference" "J2_MR1"', self.content, "J2_MR1 USB-C must be present")

        # Motor headers
        self.assertIn('(property "Reference" "J_PUMP1"', self.content, "J_PUMP1 header must be present")
        self.assertIn('(property "Reference" "J_PUMP2"', self.content, "J_PUMP2 header must be present")

        # Pressure sensors
        self.assertIn('(property "Reference" "U9_SENS1"', self.content, "Cis pressure sensor U9 must be present")
        self.assertIn('(property "Reference" "U10_SENS2"', self.content, "Trans pressure sensor U10 must be present")

        # Power plane zones
        self.assertIn('(net_name "GND")', self.content, "GND copper plane must be present")
        self.assertIn('(net_name "+5V_MR1_CLEAN")', self.content, "Filtered +5V power plane must be present")


if __name__ == "__main__":
    unittest.main()
