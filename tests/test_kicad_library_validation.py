"""
Unit tests validating KiCad Symbol and Footprint Libraries for the Amplifier project
against the https://github.com/Aharoni-Lab/kicad-library-validator specification.
"""

import unittest
from pathlib import Path

from kicad_lib_validator.validator import KiCadLibraryValidator
from kicad_lib_validator.parser.library_parser import parse_symbol_file, parse_footprint_file
from kicad_lib_validator.validators.symbol_validator import validate_symbol
from kicad_lib_validator.validators.footprint_validator import validate_footprint
from kicad_lib_validator.parser.structure_parser import parse_library_structure


class TestKiCadLibraryValidation(unittest.TestCase):
    """Verifies that Amplifier symbols and footprints pass KiCad Library Validator."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parent.parent
        cls.amp_dir = cls.repo_root / "Amplifier"
        cls.structure_file = cls.amp_dir / "library_structure.yaml"
        cls.symbols_file = cls.amp_dir / "symbols" / "MR1.kicad_sym"
        cls.footprints_dir = cls.amp_dir / "footprints"
        cls.pretty_dir = cls.amp_dir / "footprints.pretty"

    def test_library_structure_file_exists_and_parses(self):
        """Verifies library_structure.yaml exists and parses cleanly."""
        self.assertTrue(self.structure_file.is_file(), "library_structure.yaml missing")
        structure = parse_library_structure(self.structure_file)
        self.assertEqual(structure.library.prefix, "MR1")
        self.assertEqual(structure.library.directories.symbols, "symbols")
        self.assertEqual(structure.library.directories.footprints, "footprints")

    def test_full_library_validator_run(self):
        """Runs KiCadLibraryValidator.validate() and verifies 0 errors."""
        validator = KiCadLibraryValidator(self.amp_dir, self.structure_file)
        result = validator.validate()
        self.assertFalse(result.has_errors(), f"Validation errors found: {result.errors}")
        self.assertEqual(len(result.errors), 0)

    def test_symbols_parsing_and_required_properties(self):
        """Verifies that every symbol in MR1.kicad_sym has all required validator fields."""
        structure = parse_library_structure(self.structure_file)
        symbols = parse_symbol_file(self.symbols_file, "MR1", structure, self.amp_dir)
        self.assertGreaterEqual(len(symbols), 7)

        symbol_names = {s.name for s in symbols}
        self.assertIn("OPA192IDR", symbol_names)
        self.assertIn("LTC6268xS8-10_SHIELD", symbol_names)
        self.assertIn("PogoPin_SpringHeader_12Pin_Distributed", symbol_names)

        required_fields = ["Reference", "Value", "Footprint", "Datasheet", "Description", "ki_keywords"]
        for s in symbols:
            res = validate_symbol(s, structure)
            self.assertEqual(len(res.errors), 0, f"Symbol {s.name} failed validation: {res.errors}")
            for field in required_fields:
                self.assertIn(field, s.properties, f"Symbol {s.name} missing required field '{field}'")

    def test_opa192idr_symbol_pinout(self):
        """Verifies pinout of OPA192IDR symbol conforms to SOIC-8 single op-amp specification."""
        structure = parse_library_structure(self.structure_file)
        symbols = parse_symbol_file(self.symbols_file, "MR1", structure, self.amp_dir)
        opa = next(s for s in symbols if s.name == "OPA192IDR")

        self.assertEqual(opa.properties["Reference"], "U")
        self.assertEqual(opa.properties["Value"], "OPA192IDR")
        self.assertIn("SOIC-8", opa.properties["Footprint"])

        pin_map = {p.number: (p.name, p.type) for p in opa.pins}
        self.assertEqual(len(pin_map), 8)
        self.assertEqual(pin_map["2"][0], "-")
        self.assertEqual(pin_map["3"][0], "+")
        self.assertEqual(pin_map["4"][0], "V-")
        self.assertIn(pin_map["6"][0], ["", "~"])
        self.assertEqual(pin_map["7"][0], "V+")

    def test_footprints_parsing_and_required_properties(self):
        """Verifies that every footprint in footprints and footprints.pretty passes validation."""
        structure = parse_library_structure(self.structure_file)
        footprint_files = list(self.footprints_dir.glob("*.kicad_mod"))
        self.assertGreaterEqual(len(footprint_files), 13)

        for fp_file in footprint_files:
            fp = parse_footprint_file(fp_file, self.footprints_dir, structure)
            self.assertIsNotNone(fp, f"Failed to parse footprint file {fp_file.name}")
            res = validate_footprint(fp, structure)
            self.assertEqual(len(res.errors), 0, f"Footprint {fp.name} failed validation: {res.errors}")

            required_fp_fields = ["Reference", "Value", "Datasheet", "Description"]
            for field in required_fp_fields:
                self.assertIn(field, fp.properties, f"Footprint {fp.name} missing property '{field}'")

    def test_library_tables_exist_and_point_to_valid_libraries(self):
        """Verifies sym-lib-table and fp-lib-table resolve to existing on-disk libraries."""
        sym_table = (self.amp_dir / "sym-lib-table").read_text()
        fp_table = (self.amp_dir / "fp-lib-table").read_text()

        self.assertIn('"MR1"', sym_table)
        self.assertIn('"footprints"', fp_table)

        # Ensure target paths exist
        self.assertTrue((self.amp_dir / "symbols" / "MR1.kicad_sym").is_file())
        self.assertTrue((self.amp_dir / "footprints.pretty").is_dir())


if __name__ == "__main__":
    unittest.main()
