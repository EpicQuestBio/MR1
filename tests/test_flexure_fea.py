"""
Unit tests for CAD flexure structural mechanics and G-code toolpath-informed FEA simulations.
Validates that:
1. CAD 3D model flexure mechanics accurately computes stress concentration and fatigue life.
2. G-code parser detects hollow shells, voids, and sharp notch delamination risks.
3. Optimized living-hinge toolpaths pass all structural and fatigue criteria.
"""

import unittest
from simulations.flexure_living_hinge_fea import FlexureLivingHingeFEA
from simulations.gcode_toolpath_fea import GCodeToolpathFEA


class TestFlexureFEA(unittest.TestCase):
    def test_cad_flexure_mechanics_comparison(self):
        """Verify CAD flexure model identifies high stress concentration in unfilleted arms."""
        fea = FlexureLivingHingeFEA()
        comp = fea.compare_unfilleted_vs_living_hinge()

        orig = comp["original_design"]
        opt = comp["optimized_living_hinge"]

        # Original unfilleted arm has high stress concentration (Kt > 2.5)
        self.assertGreater(orig["k_t_stress_concentration"], 2.5)
        # Original arm exceeds yield strength or has low fatigue life
        self.assertTrue(orig["will_snap_prematurely"])

        # Optimized living hinge has low stress concentration (Kt < 1.7)
        self.assertLess(opt["k_t_stress_concentration"], 1.7)
        # Optimized arm has high fatigue life (> 2,000 cycles, vs 1 cycle for unfilleted)
        self.assertGreater(opt["predicted_fatigue_cycles"], 2000.0)
        self.assertFalse(opt["will_snap_prematurely"])

    def test_gcode_flawed_cross_section_detection(self):
        """Verify G-code parser detects hollow cores, voids, and delamination risks."""
        sim = GCodeToolpathFEA(material="PLA")
        gcode_flawed = sim.generate_synthetic_ratchet_slice(design_type="flawed")
        sim.parse_gcode_text(gcode_flawed)

        res = sim.analyze_flexure_cross_section()
        self.assertTrue(res["has_internal_void"])
        self.assertGreater(res["max_internal_gap_mm"], 0.15)
        self.assertTrue(res["sharp_root_notch"])
        self.assertIn("FAIL", res["diagnosis"])

    def test_gcode_optimized_living_hinge_validation(self):
        """Verify optimized 4-pass solid living hinge passes toolpath FEA."""
        sim = GCodeToolpathFEA(material="PETG")
        gcode_opt = sim.generate_synthetic_ratchet_slice(design_type="optimized")
        sim.parse_gcode_text(gcode_opt)

        res = sim.analyze_flexure_cross_section()
        self.assertFalse(res["has_internal_void"])
        self.assertAlmostEqual(res["fill_ratio"], 1.0, delta=0.05)
        self.assertFalse(res["sharp_root_notch"])
        self.assertEqual(res["diagnosis"], "PASS_SOLID_DURABLE_LIVING_HINGE")

    def test_material_fatigue_properties(self):
        """Verify PETG and Nylon show superior living-hinge compliance over brittle PLA."""
        fea_pla = FlexureLivingHingeFEA(material_name="PLA").calculate_flexure_mechanics()
        fea_petg = FlexureLivingHingeFEA(material_name="PETG").calculate_flexure_mechanics()

        # PETG has lower modulus (lower peak bending stress) and higher fatigue endurance
        self.assertLess(fea_petg["peak_stress_mpa"], fea_pla["peak_stress_mpa"])
        self.assertGreater(fea_petg["predicted_fatigue_cycles"], fea_pla["predicted_fatigue_cycles"])


if __name__ == "__main__":
    unittest.main()
