# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
Unit tests for torque cap topology optimization bridge and problem setup.
Validates:
1. Topology optimization problem setup generates valid CAD solids for root support, design space, and pawl tip load.
2. Problem parameters (E-modulus, force vector, volume fraction) match PETG ratchet flexure requirements.
3. Density solver execution or analytical parabolic taper fallback returns optimal living hinge parameters.
4. Export function creates valid thresholded geometry file (STL/STEP).
"""

import os
import unittest
from simulations.torque_cap_topology_optimization import TorqueCapLivingHingeTOProblem


class TestTopologyOptimization(unittest.TestCase):
    def test_cad_domains_generation(self):
        """Verify build123d solids for root fixed boundary, design space, and load tip are valid non-empty shapes."""
        prob = TorqueCapLivingHingeTOProblem()
        domains = prob.create_cad_domains()

        self.assertIn("root_fixed", domains)
        self.assertIn("design_space", domains)
        self.assertIn("load_pawl_tip", domains)

        for name, solid in domains.items():
            self.assertIsNotNone(solid)
            self.assertGreater(solid.volume, 0.0)

    def test_problem_setup_dictionary(self):
        """Verify problem setup parameters strictly match physical specifications."""
        prob = TorqueCapLivingHingeTOProblem(applied_load_n=5.0)
        setup = prob.setup_problem_dict()

        self.assertEqual(setup["load_vector_n"], (0.0, 5.0, 0.0))
        self.assertAlmostEqual(setup["young_modulus_gpa"], 2.1) # PETG E-modulus
        self.assertAlmostEqual(setup["target_volume_fraction"], 0.45)
        self.assertEqual(setup["grid_resolution"], (32, 16, 8))

    def test_solver_density_results(self):
        """Verify density solver returns optimal root fillet radius and recommended living hinge thickness."""
        prob = TorqueCapLivingHingeTOProblem()
        res = prob.solve_or_simulate_density()

        self.assertIn("density_profile_type", res)
        self.assertAlmostEqual(res["optimal_root_fillet_mm"], 2.5)
        self.assertAlmostEqual(res["recommended_living_hinge_thickness_mm"], 1.8)
        self.assertGreater(res["optimal_hinge_taper_ratio"], 0.0)

    def test_thresholded_geometry_export(self):
        """Verify exporting thresholded geometry generates a non-empty file on disk."""
        prob = TorqueCapLivingHingeTOProblem()
        output_path = "exports/test_torque_cap_opt_export.stl"
        if os.path.exists(output_path):
            os.remove(output_path)

        res_path = prob.export_thresholded_geometry(output_path)
        self.assertTrue(os.path.exists(res_path))
        self.assertGreater(os.path.getsize(res_path), 0)

        if os.path.exists(output_path):
            os.remove(output_path)


if __name__ == "__main__":
    unittest.main()
