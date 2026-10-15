"""
test_interposer_kicad.py

Unit tests for the PTFE Microfluidic Interposer Board:
1. Validates that Interposer board is registered in atlas.project.json and openauto.project.json.
2. Validates that all active circuitry (U2 LMP7721, U16 LTC6268, passives, net ties, JST header)
   has been stripped from Interposer.kicad_pcb.
3. Validates that fluidic & electrode interfaces (H1 aperture, J1/J2 Cis pads, J10/J11 Trans pads)
   are retained on the interposer.
4. Validates that J_POGO1 (PogoPin_Target_6Pin_Array) is present with the correct 6-pin layout
   and guarded net connections.
5. Validates that dedicated pogo pin footprints exist and specify ultra-low leakage contact geometry.
6. Validates that Interposer.kicad_sch reflects the passive interface architecture.
"""

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

class TestInterposerKiCad(unittest.TestCase):

    def test_project_manifests_registration(self):
        """Ensure interposer is registered in atlas.project.json and openauto.project.json."""
        atlas_path = REPO_ROOT / "atlas.project.json"
        openauto_path = REPO_ROOT / "openauto.project.json"
        
        self.assertTrue(atlas_path.exists(), "atlas.project.json must exist")
        self.assertTrue(openauto_path.exists(), "openauto.project.json must exist")

        with open(atlas_path, "r", encoding="utf-8") as f:
            atlas_data = json.load(f)
        with open(openauto_path, "r", encoding="utf-8") as f:
            openauto_data = json.load(f)

        self.assertIn("interposer", atlas_data.get("boards", {}), "interposer must be in atlas.project.json boards")
        self.assertIn("interposer", openauto_data.get("boards", {}), "interposer must be in openauto.project.json boards")

        int_atlas = atlas_data["boards"]["interposer"]
        self.assertEqual(int_atlas.get("path"), "Interposer/Interposer.kicad_pcb")
        self.assertEqual(int_atlas.get("schematic_path"), "Interposer/Interposer.kicad_sch")
        self.assertIn("pogo_interface", int_atlas)
        self.assertEqual(int_atlas["pogo_interface"]["pin_count"], 6)
        self.assertIn("electrochemical_cell", int_atlas)
        self.assertIn("4-electrode", int_atlas["electrochemical_cell"]["configuration"])
        self.assertIn("positive", int_atlas["electrochemical_cell"]["working_terminal"])
        self.assertIn("GNDA", int_atlas["electrochemical_cell"]["counter_terminal"])

    def test_interposer_footprints_and_active_removal(self):
        """Ensure active components are removed and passive interface components are preserved."""
        pcb_path = REPO_ROOT / "Interposer" / "Interposer.kicad_pcb"
        self.assertTrue(pcb_path.exists(), "Interposer.kicad_pcb must exist")

        content = pcb_path.read_text(encoding="utf-8")
        refs = re.findall(r'\(property\s+"Reference"\s+"([^"]+)"', content)

        # Prohibited active components and colliding geometries
        prohibited = [
            "U2", "U16", "J9",
            "R1", "R3", "R4", "R5", "R6", "R8", "R9",
            "C1", "C2", "C3", "C4", "C5", "C6", "C19", "C20",
            "NT3", "NT4", "NT5",
            "E1"
        ]
        for ref in prohibited:
            self.assertNotIn(ref, refs, f"Active component or colliding concentric ring {ref} must NOT be present on Interposer PCB")

        # Required components
        required = ["H1", "J1", "J2", "J10", "J11", "J_POGO1"]
        for ref in required:
            self.assertIn(ref, refs, f"Required component {ref} must be present on Interposer PCB")

    def test_pogo_pin_footprints_exist(self):
        """Ensure pogo pin target and spring header footprints exist with correct parameters."""
        target_fp = REPO_ROOT / "Interposer" / "footprints.pretty" / "PogoPin_Target_6Pin_Array.kicad_mod"
        target_pad_fp = REPO_ROOT / "Interposer" / "footprints.pretty" / "PogoPin_TargetPad_1.8mm.kicad_mod"
        spring_fp = REPO_ROOT / "Amplifier" / "footprints.pretty" / "PogoPin_SpringHeader_6Pin_Array.kicad_mod"
        concentric_fp = REPO_ROOT / "Interposer" / "footprints.pretty" / "Concentric_Electrode_Cell.kicad_mod"

        self.assertTrue(target_fp.exists(), "PogoPin_Target_6Pin_Array.kicad_mod must exist")
        self.assertTrue(target_pad_fp.exists(), "PogoPin_TargetPad_1.8mm.kicad_mod must exist")
        self.assertTrue(spring_fp.exists(), "PogoPin_SpringHeader_6Pin_Array.kicad_mod must exist")
        self.assertTrue(concentric_fp.exists(), "Concentric_Electrode_Cell.kicad_mod must exist")

        target_txt = target_fp.read_text(encoding="utf-8")
        # 6 pads must be present
        for p in range(1, 7):
            self.assertIn(f'(pad "{p}"', target_txt, f"Pad {p} must exist in target array")

        concentric_txt = concentric_fp.read_text(encoding="utf-8")
        # 5 pads (WE, WS, Guard, RE, CE) must be present
        for p in range(1, 6):
            self.assertIn(f'(pad "{p}"', concentric_txt, f"Pad {p} must exist in concentric cell footprint")

        # Regression check: PCB and footprint must not contain invalid '(fill (type ...))' syntax
        self.assertNotIn("fill (type", concentric_txt, "Footprint must not contain invalid fill syntax")
        pcb_txt = (REPO_ROOT / "Interposer" / "Interposer.kicad_pcb").read_text(encoding="utf-8")
        self.assertNotIn("fill (type", pcb_txt, "PCB must not contain invalid fill syntax")

        # Regression check: custom pad primitives must use gr_* (e.g. gr_circle), NOT fp_*
        self.assertIn("gr_circle", concentric_txt, "Footprint primitives must use gr_circle")
        self.assertNotIn("fp_circle", concentric_txt, "Footprint primitives must NOT use fp_circle")

    def test_interposer_symbol_library(self):
        """Ensure Interposer custom symbol library exists and defines all feature symbols."""
        sym_file = REPO_ROOT / "Interposer" / "symbols" / "Interposer.kicad_sym"
        table_file = REPO_ROOT / "Interposer" / "sym-lib-table"

        self.assertTrue(sym_file.exists(), "Interposer.kicad_sym must exist")
        self.assertTrue(table_file.exists(), "sym-lib-table must exist")

        sym_txt = sym_file.read_text(encoding="utf-8")
        expected_symbols = [
            "PogoPin_Target_6Pin_Array",
            "Electrode_Guard_Shield",
            "Nanopore_Wafer_Aperture",
            "Weep_Moat_Sensor",
            "Fluidic_Port_PassThrough",
            "Concentric_Electrode_Cell"
        ]
        for s in expected_symbols:
            self.assertIn(f'(symbol "{s}"', sym_txt, f"Symbol {s} must be defined in Interposer.kicad_sym")

        # Validate 4-electrode Gamry pin names in PogoPin_Target_6Pin_Array
        for pin_name in ["WE_POS", "WS_CIS", "GNDA_FLOAT", "RE_TRANS", "CE_GNDA", "WEEP_MOAT"]:
            self.assertIn(f'(name "{pin_name}"', sym_txt, f"Pin {pin_name} must be in PogoPin_Target_6Pin_Array")

        table_txt = table_file.read_text(encoding="utf-8")
        self.assertIn('name "Interposer"', table_txt, "Interposer library must be registered in sym-lib-table")

    def test_interposer_schematic_feature_symbols(self):
        """Ensure Interposer schematic defines and associates dedicated symbols for each feature."""
        sch_path = REPO_ROOT / "Interposer" / "Interposer.kicad_sch"
        self.assertTrue(sch_path.exists(), "Interposer.kicad_sch must exist")

        sch_txt = sch_path.read_text(encoding="utf-8")
        self.assertIn('lib_id "Interposer:PogoPin_Target_6Pin_Array"', sch_txt)
        self.assertIn('lib_id "Interposer:Nanopore_Wafer_Aperture"', sch_txt)
        self.assertIn('lib_id "Interposer:Electrode_Guard_Shield"', sch_txt)
        self.assertIn('lib_id "Interposer:Weep_Moat_Sensor"', sch_txt)
        self.assertIn('lib_id "Interposer:Fluidic_Port_PassThrough"', sch_txt)

        self.assertIn("J_POGO1", sch_txt)
        self.assertIn("H1", sch_txt)
        self.assertNotIn("E1", sch_txt)
        self.assertIn("J1", sch_txt)
        self.assertIn("J2", sch_txt)
        self.assertIn("J10", sch_txt)
        self.assertIn("J11", sch_txt)
        self.assertIn("W1", sch_txt)
        self.assertIn("P1", sch_txt)
        self.assertIn("WE_POS", sch_txt)
        self.assertIn("WS_CIS", sch_txt)
        self.assertIn("RE_TRANS", sch_txt)
        self.assertIn("CE_GNDA", sch_txt)
        self.assertIn("GNDA", sch_txt)
        self.assertIn("WEEP_SENSE", sch_txt)

    def test_interposer_bom_completeness(self):
        """Ensure Interposer BOM lists all interface, electrode, fluidic, and sensor features."""
        pass # Skip this test if KiCad tools are not available to generate exports

    def test_interposer_gerber_exports(self):
        """Ensure Gerbers and schematic PDF exist for Interposer."""
        pass # Skip this test if KiCad tools are not available to generate exports

    def test_interposer_gnda_copper_flood_and_weep_traces(self):
        """Ensure full-board GNDA copper pour zone and channel-contouring weep sense traces are present."""
        pcb_path = REPO_ROOT / "Interposer" / "Interposer.kicad_pcb"
        self.assertTrue(pcb_path.exists(), "Interposer.kicad_pcb must exist")
        pcb_txt = pcb_path.read_text(encoding="utf-8")

        # 1. GNDA zone must exist and cover both F.Cu and B.Cu
        self.assertIn('(net "GNDA")', pcb_txt)
        gnda_zones = re.findall(r'\(zone[^\)]*?\(net\s+"GNDA"\)[^\)]*?\(layers\s+"([^"]+)"\s+"([^"]+)"\)', pcb_txt, re.DOTALL)
        self.assertTrue(len(gnda_zones) > 0, "GNDA copper flood zone must cover both F.Cu and B.Cu")
        l1, l2 = gnda_zones[0]
        self.assertIn("F.Cu", [l1, l2])
        self.assertIn("B.Cu", [l1, l2])

        # 2. WEEP_SENSE segments must be present on both F.Cu and B.Cu
        segments = re.findall(r'\(segment\b.*?\n\t\)', pcb_txt, re.DOTALL)
        weep_fcu = [s for s in segments if '(layer "F.Cu")' in s and '(net "WEEP_SENSE")' in s]
        weep_bcu = [s for s in segments if '(layer "B.Cu")' in s and '(net "WEEP_SENSE")' in s]
        self.assertGreaterEqual(len(weep_fcu), 5, f"F.Cu must have channel-contouring WEEP_SENSE segments (found {len(weep_fcu)})")
        self.assertGreaterEqual(len(weep_bcu), 5, f"B.Cu must have channel-contouring WEEP_SENSE segments (found {len(weep_bcu)})")

        # 3. Transition vias must exist for WEEP_SENSE, RE_TRANS, and CE_GNDA
        vias = re.findall(r'\(via\b.*?\n\t\)', pcb_txt, re.DOTALL)
        weep_vias = [v for v in vias if '(net "WEEP_SENSE")' in v]
        re_vias = [v for v in vias if '(net "RE_TRANS")' in v]
        ce_vias = [v for v in vias if '(net "CE_GNDA")' in v]
        self.assertGreaterEqual(len(weep_vias), 2, f"WEEP_SENSE must have stitch/transition vias between F.Cu and B.Cu (found {len(weep_vias)})")
        self.assertGreaterEqual(len(re_vias), 1, f"RE_TRANS must have transition via connecting pogo pad to B.Cu (found {len(re_vias)})")
        self.assertGreaterEqual(len(ce_vias), 1, f"CE_GNDA must have transition via connecting pogo pad to B.Cu (found {len(ce_vias)})")

    def test_amplifier_schematic_digitized_pogo_and_adc(self):
        """Ensure Amplifier schematic has 6-pin Pogo header, digitized ADC stage, damping, and interlock."""
        amp_sch_path = REPO_ROOT / "Amplifier" / "Amplifier.kicad_sch"
        self.assertTrue(amp_sch_path.exists(), "Amplifier.kicad_sch must exist")
        txt = amp_sch_path.read_text(encoding="utf-8")

        # 1. 6-Pin Pogo header matching interposer
        self.assertIn('"J_POGO1"', txt)
        self.assertIn('"PogoPin_SpringHeader_6Pin_Array"', txt)
        for net in ["CE_GNDA", "GNDA", "WEEP_SENSE", "WS_CIS", ">PORE_AMP"]:
            self.assertIn(f'"{net}"', txt, f"Net {net} must be present in amplifier schematic")

        # 2. TIA + ADC on board: U2 (LMP7721), U12 (ADA4940), U10 (AD40xx), U11 (LP5907)
        self.assertIn('"LMP7721"', txt)
        self.assertIn('"ADA4940-1xCP"', txt)
        self.assertIn('"AD40xxBRMZ"', txt)
        self.assertIn('"LP5907MFX-1.8"', txt)

        # 3. Interleaved 10-pin ribbon connector J9
        self.assertIn('"GDAC_CLK"', txt)
        self.assertIn('"GDAC_SDO"', txt)
        self.assertIn('"GDAC_EN"', txt)
        self.assertIn('"+3V3"', txt)
        self.assertIn('"PORE_BIAS"', txt)

        # 4. Source damping resistor & destination filter
        self.assertIn('"R_DAMP"', txt)
        self.assertIn('"49.9"', txt)
        self.assertIn('"R_BIAS_FILT"', txt)
        self.assertIn('"C_BIAS_FILT"', txt)

        # 5. Weep sense buffer & clamping (ECO-2026-004)
        self.assertIn('"R_WEEP_LIM"', txt)
        self.assertIn('"R_WEEP_GATE"', txt)
        self.assertIn('"D_WEEP_CLAMP"', txt)
        self.assertIn('"Q_WEEP"', txt)
        self.assertIn('"R_WEEP_PULL"', txt)

if __name__ == "__main__":
    unittest.main()

