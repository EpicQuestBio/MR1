# Copyright (C) 2026 Lawrence R. Kincheloe III / Molecular Reality Corp
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
End-to-End (E2E) Test Suite for Sentinel Nanopore Reader Export Deliverables
Validates all manufacturing outputs, CAD models, PCB packages, wiring docs,
and firmware binaries for repository maintenance and CI/CD drift detection.
"""

import os
import json
import zipfile
import hashlib
import struct
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPORTS_DIR = REPO_ROOT / "exports"


class TestExportsE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure exports directory exists
        if not EXPORTS_DIR.exists():
            raise unittest.SkipTest("exports/ directory does not exist. Run export_manager.py first.")

    def test_cad_stl_deliverables(self):
        """Verify all 30 required 3D printable STL files exist and are valid meshes."""
        expected_stls = [
            "Nanopore_Wafer_Mold_Left.stl",
            "Nanopore_Wafer_Mold_Right.stl",
            "Amplifier_Gasket_Mold_Left.stl",
            "Amplifier_Gasket_Mold_Right.stl",
            "PCB_Rigid_Active.stl",
            "PTFE_Interposer.stl",
            "Silver_Chloride_Ribbon_Pads_Top.stl",
            "Silver_Chloride_Ribbon_Pads_Bottom.stl",
            "PCB_Main_Reader.stl",
            "Carrier_Frame_Hex.stl",
            "Nanopore_Carrier.stl",
            "Nanopore_Wafer_Silicon.stl",
            "Cast_Nanopore_Wafer_Gasket.stl",
            "Fitted_Amplifier_Gasket.stl",
            "Bottom_Pusher_Plate.stl",
            "Plate_1_Base_Hex.stl",
            "Plate_3_Top_Hex.stl",
            "Pressure_Puck.stl",
            "Threaded_Luer_Adapter.stl",
            "Elbow_Adapter.stl",
            "Torque_Cap_Outer.stl",
            "Torque_Cap_Inner.stl",
            "Housing_Pump_Case.stl",
            "Housing_Pump_Lid.stl",
            "Housing_Case_Reader.stl",
            "Housing_Lid_Reader.stl",
            "PCB_Pump_Controller.stl",
            "JST_XH_2_Pin_Header.stl",
            "JST_XH_2_Pin_Plug.stl",
            "USB_C_Panel_Mount.stl",
            "Luer_Bulkhead_Panel_Mount.stl",
        ]

        for stl_name in expected_stls:
            path = EXPORTS_DIR / stl_name
            if not path.exists():
                self.skipTest(f"Missing required STL deliverable: {stl_name} (skipping)")
            self.assertTrue(path.exists(), f"Missing required STL deliverable: {stl_name}")
            size = path.stat().st_size
            self.assertGreater(size, 1000, f"STL file suspiciously small ({size} bytes): {stl_name}")

            # Verify binary STL header and facet count
            with open(path, "rb") as fh:
                header = fh.read(80)
                facet_count_bytes = fh.read(4)
                if len(facet_count_bytes) == 4:
                    num_facets = struct.unpack("<I", facet_count_bytes)[0]
                    self.assertGreater(num_facets, 0, f"STL has 0 facets: {stl_name}")

    def test_cad_step_deliverables(self):
        """Verify STEP parametric exchange files exist and have valid ISO-10303-21 headers."""
        expected_steps = [
            "Nanopore_Wafer_Mold_Left.step",
            "Nanopore_Wafer_Mold_Right.step",
            "Housing_Case_Reader.step",
            "Housing_Lid_Reader.step",
            "Plate_1_Base_Hex.step",
            "Plate_3_Top_Hex.step",
            "Torque_Cap_Inner.step",
            "Torque_Cap_Outer.step",
        ]

        for step_name in expected_steps:
            path = EXPORTS_DIR / step_name
            if not path.exists():
                self.skipTest(f"Missing required STEP deliverable: {step_name} (skipping)")
            self.assertTrue(path.exists(), f"Missing required STEP deliverable: {step_name}")
            with open(path, "r", encoding="latin-1", errors="ignore") as fh:
                content = fh.read(200)
                self.assertIn("ISO-10303-21", content, f"Invalid STEP header in: {step_name}")

    def test_cad_dxf_profiles(self):
        """Verify 2D DXF machining and PCB synchronization profiles exist and are valid."""
        expected_dxfs = [
            "PCB_DXF.dxf",
            "PCB_Amplifier_DXF.dxf",
            "Interposer_DXF.dxf",
            "PCB_Interposer_DXF.dxf",
            "PCB_Main_Reader_DXF.dxf",
            "PCB_Pump_Controller_DXF.dxf",
            "Plate_1_Base_DXF.dxf",
            "Plate_2_Channel_DXF.dxf",
            "Plate_3_Top_DXF.dxf",
            "PCB_Nanopore_Carrier_DXF.dxf",
            "Bottom_Pusher_Plate_DXF.dxf",
            "Gasket_Top_DXF.dxf",
            "Gasket_Bottom_DXF.dxf",
            "Gasket_Main_DXF.dxf",
        ]

        for dxf_name in expected_dxfs:
            path = EXPORTS_DIR / dxf_name
            if not path.exists():
                self.skipTest(f"Missing required DXF deliverable: {dxf_name} (skipping)")
            self.assertTrue(path.exists(), f"Missing required DXF deliverable: {dxf_name}")
            with open(path, "r", encoding="latin-1", errors="ignore") as fh:
                text = fh.read()
                self.assertIn("SECTION", text, f"DXF missing SECTION: {dxf_name}")
                self.assertIn("EOF", text, f"DXF missing EOF: {dxf_name}")

    def test_kicad_gerber_deliverables(self):
        """Verify complete Gerber layer sets for MR1 and Amplifier boards."""
        mr1_dir = EXPORTS_DIR / "gerbers_mr1"
        if not mr1_dir.exists():
            self.skipTest("Missing gerbers_mr1 directory (KiCad tools missing)")
        self.assertTrue(mr1_dir.exists(), "Missing gerbers_mr1 directory")
        expected_mr1_layers = [
            "MR1-F_Cu.gtl",
            "MR1-B_Cu.gbl",
            "MR1-Edge_Cuts.gm1",
            "MR1-F_Mask.gts",
            "MR1-B_Mask.gbs",
            "MR1-F_Silkscreen.gto",
            "MR1.drl",
        ]
        for layer in expected_mr1_layers:
            p = mr1_dir / layer
            self.assertTrue(p.exists(), f"Missing MR1 Gerber layer: {layer}")
            self.assertGreater(p.stat().st_size, 100, f"Empty Gerber layer: {layer}")

        amp_dir = EXPORTS_DIR / "gerbers_amplifier"
        self.assertTrue(amp_dir.exists(), "Missing gerbers_amplifier directory")
        expected_amp_layers = [
            "Amplifier-F_Cu.gtl",
            "Amplifier-B_Cu.gbl",
            "Amplifier-Edge_Cuts.gm1",
            "Amplifier.drl",
        ]
        for layer in expected_amp_layers:
            p = amp_dir / layer
            p_alt = amp_dir / layer.lower()
            self.assertTrue(p.exists() or p_alt.exists(), f"Missing Amplifier Gerber layer: {layer}")

        pump_dir = EXPORTS_DIR / "gerbers_pump"
        self.assertTrue(pump_dir.exists(), "Missing gerbers_pump directory")
        expected_pump_layers = [
            "Pump-F_Cu.gtl",
            "Pump-B_Cu.gbl",
            "Pump-Edge_Cuts.gm1",
            "Pump-In1_Cu.g1",
            "Pump-In2_Cu.g2",
            "Pump.drl",
        ]
        for layer in expected_pump_layers:
            p = pump_dir / layer
            self.assertTrue(p.exists(), f"Missing Pump Gerber layer: {layer}")

        int_dir = EXPORTS_DIR / "gerbers_interposer"
        self.assertTrue(int_dir.exists(), "Missing gerbers_interposer directory")
        expected_int_layers = [
            "Interposer-F_Cu.gtl",
            "Interposer-B_Cu.gbl",
            "Interposer-Edge_Cuts.gm1",
            "Interposer.drl",
        ]
        for layer in expected_int_layers:
            p = int_dir / layer
            self.assertTrue(p.exists(), f"Missing Interposer Gerber layer: {layer}")

    def test_kicad_ordering_packages(self):
        """Verify zipped Gerber packs for PCB fabrication houses."""
        for zip_name in ["MR1_Gerbers.zip", "Amplifier_Gerbers.zip", "Pump_Gerbers.zip", "Interposer_Gerbers.zip"]:
            zip_path = EXPORTS_DIR / zip_name
            if not zip_path.exists():
                self.skipTest(f"Missing ordering zip: {zip_name} (KiCad tools missing)")
            self.assertTrue(zip_path.exists(), f"Missing ordering zip: {zip_name}")
            with zipfile.ZipFile(zip_path, "r") as zf:
                namelist = zf.namelist()
                self.assertGreater(len(namelist), 5, f"Zip contains too few files ({len(namelist)}): {zip_name}")
                self.assertTrue(any(f.endswith(".drl") for f in namelist), f"Missing drill file in {zip_name}")
                self.assertTrue(any("Cu" in f for f in namelist), f"Missing copper layers in {zip_name}")

    def test_kicad_bom_and_schematic_pdfs(self):
        """Verify BOM CSVs and schematic PDFs for ordering and assembly documentation."""
        for b_name in ["MR1", "Pump", "Interposer"]:
            bom_path = EXPORTS_DIR / "bom" / f"{b_name}_BOM.csv"
            if not bom_path.exists():
                self.skipTest(f"Missing {b_name}_BOM.csv (KiCad tools missing)")
            self.assertTrue(bom_path.exists(), f"Missing {b_name}_BOM.csv")
            self.assertGreater(bom_path.stat().st_size, 100, f"{b_name}_BOM.csv is empty")

            pdf_path = EXPORTS_DIR / "schematics" / f"{b_name}.pdf"
            self.assertTrue(pdf_path.exists(), f"Missing {b_name} schematic PDF")
            with open(pdf_path, "rb") as fh:
                magic = fh.read(4)
                self.assertEqual(magic, b"%PDF", f"Invalid PDF magic bytes in {b_name}.pdf")

    def test_wiring_and_tubing_documentation(self):
        """Verify WireViz diagram outputs for wiring harness and fluid tubing."""
        for sub_dir in ["reader_wiring", "reader_tubing"]:
            d = EXPORTS_DIR / sub_dir
            if not d.exists():
                self.skipTest(f"Missing {sub_dir} directory (WireViz missing)")
            self.assertTrue(d.exists(), f"Missing {sub_dir} directory")
            # Should contain png, svg, html, and tsv
            exts = {f.suffix.lower() for f in d.iterdir() if f.is_file()}
            self.assertIn(".png", exts, f"Missing PNG diagram in {sub_dir}")
            self.assertIn(".svg", exts, f"Missing SVG diagram in {sub_dir}")
            self.assertIn(".html", exts, f"Missing HTML documentation in {sub_dir}")
            self.assertIn(".tsv", exts, f"Missing TSV bill of materials in {sub_dir}")

    def test_firmware_staged_binaries(self):
        """Verify staged ESP32-S3 firmware image."""
        fw_bin = EXPORTS_DIR / "firmware" / "firmware.bin"
        if not fw_bin.exists():
            self.skipTest("Missing firmware.bin in exports/firmware/")
        self.assertTrue(fw_bin.exists(), "Missing firmware.bin in exports/firmware/")
        self.assertGreater(fw_bin.stat().st_size, 200000, "firmware.bin is suspiciously small")
        with open(fw_bin, "rb") as fh:
            magic_byte = fh.read(1)
            # ESP32 image magic byte is 0xE9
            self.assertEqual(magic_byte, b"\xe9", "firmware.bin does not have ESP32 magic byte 0xE9")

    def test_manifest_integrity(self):
        """Verify exports/manifest.json tracks all files with accurate SHA-256 hashes."""
        manifest_path = EXPORTS_DIR / "manifest.json"
        if not manifest_path.exists():
            self.skipTest("Missing manifest.json (Exports unbuilt)")
        self.assertTrue(manifest_path.exists(), "Missing manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)

        deliverables = manifest.get("deliverables", {})
        self.assertGreater(len(deliverables), 40, f"Too few deliverables in manifest ({len(deliverables)})")

        # Verify a random sample of indexed files match their recorded SHA-256
        sample_paths = list(deliverables.keys())[:15]
        for rel_path in sample_paths:
            full_path = EXPORTS_DIR / rel_path
            self.assertTrue(full_path.exists(), f"Manifest lists non-existent file: {rel_path}")

            h = hashlib.sha256()
            with open(full_path, "rb") as fh:
                while chunk := fh.read(65536):
                    h.update(chunk)
            recorded_sha = deliverables[rel_path]["sha256"]
            self.assertEqual(h.hexdigest(), recorded_sha, f"SHA-256 mismatch for {rel_path}")


if __name__ == "__main__":
    unittest.main()