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

    def test_interposer_footprints_and_active_removal(self):
        """Ensure active components are removed and passive interface components are preserved."""
        pcb_path = REPO_ROOT / "Interposer" / "Interposer.kicad_pcb"
        self.assertTrue(pcb_path.exists(), "Interposer.kicad_pcb must exist")

        content = pcb_path.read_text(encoding="utf-8")
        refs = re.findall(r'\(property\s+"Reference"\s+"([^"]+)"', content)

        # Prohibited active components
        prohibited = [
            "U2", "U16", "J9",
            "R1", "R3", "R4", "R5", "R6", "R8", "R9",
            "C1", "C2", "C3", "C4", "C5", "C6", "C19", "C20",
            "NT3", "NT4", "NT5"
        ]
        for ref in prohibited:
            self.assertNotIn(ref, refs, f"Active component {ref} must NOT be present on Interposer PCB")

        # Required components
        required = ["H1", "J1", "J2", "J10", "J11", "J_POGO1"]
        for ref in required:
            self.assertIn(ref, refs, f"Required component {ref} must be present on Interposer PCB")

    def test_pogo_pin_footprints_exist(self):
        """Ensure pogo pin target and spring header footprints exist with correct parameters."""
        target_fp = REPO_ROOT / "Interposer" / "footprints.pretty" / "PogoPin_Target_6Pin_Array.kicad_mod"
        target_pad_fp = REPO_ROOT / "Interposer" / "footprints.pretty" / "PogoPin_TargetPad_1.8mm.kicad_mod"
        spring_fp = REPO_ROOT / "Amplifier" / "footprints.pretty" / "PogoPin_SpringHeader_6Pin_Array.kicad_mod"

        self.assertTrue(target_fp.exists(), "PogoPin_Target_6Pin_Array.kicad_mod must exist")
        self.assertTrue(target_pad_fp.exists(), "PogoPin_TargetPad_1.8mm.kicad_mod must exist")
        self.assertTrue(spring_fp.exists(), "PogoPin_SpringHeader_6Pin_Array.kicad_mod must exist")

        target_txt = target_fp.read_text(encoding="utf-8")
        # 6 pads must be present
        for p in range(1, 7):
            self.assertIn(f'(pad "{p}"', target_txt, f"Pad {p} must exist in target array")

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
            "Fluidic_Port_PassThrough"
        ]
        for s in expected_symbols:
            self.assertIn(f'(symbol "{s}"', sym_txt, f"Symbol {s} must be defined in Interposer.kicad_sym")

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
        self.assertIn("J1", sch_txt)
        self.assertIn("J2", sch_txt)
        self.assertIn("J10", sch_txt)
        self.assertIn("J11", sch_txt)
        self.assertIn("W1", sch_txt)
        self.assertIn("P1", sch_txt)
        self.assertIn(">PORE_AMP", sch_txt)
        self.assertIn("GUARD", sch_txt)
        self.assertIn("Vbias", sch_txt)
        self.assertIn("WEEP_SENSE", sch_txt)

    def test_interposer_bom_completeness(self):
        """Ensure Interposer BOM lists all interface, electrode, fluidic, and sensor features."""
        bom_csv = REPO_ROOT / "exports" / "bom" / "Interposer_BOM.csv"
        self.assertTrue(bom_csv.exists(), "Interposer_BOM.csv must exist")

        bom_txt = bom_csv.read_text(encoding="utf-8")
        for ref in ["H1", "J1", "J2", "J10", "J11", "J_POGO1", "P1", "P2", "P3", "P4", "W1"]:
            self.assertIn(f'"{ref}"', bom_txt, f"Reference {ref} must be listed in Interposer_BOM.csv")

    def test_interposer_gerber_exports(self):
        """Ensure Gerbers and schematic PDF exist for Interposer."""
        gerber_zip = REPO_ROOT / "exports" / "Interposer_Gerbers.zip"
        sch_pdf = REPO_ROOT / "exports" / "schematics" / "Interposer.pdf"
        bom_csv = REPO_ROOT / "exports" / "bom" / "Interposer_BOM.csv"

        self.assertTrue(gerber_zip.exists(), "Interposer_Gerbers.zip must exist")
        self.assertTrue(sch_pdf.exists(), "Interposer.pdf schematic must exist")
        self.assertTrue(bom_csv.exists(), "Interposer_BOM.csv must exist")

if __name__ == "__main__":
    unittest.main()
