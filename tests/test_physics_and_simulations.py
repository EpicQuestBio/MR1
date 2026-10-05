"""
Unit tests for Daemon Pore physical simulations:
- Guard ring and guard trace electrostatics & weep moat leak detection.
- Microfluidic channel fluid dynamics, hydrodynamic resistance, and SiNx membrane burst limits.
- Nanopore electrokinetics, ionic conductance, translocation blockades, and capture dynamics.
"""

import unittest
from simulations.guard_ring_electrostatics import GuardRingElectrostatics
from simulations.fluidic_dynamics_nanopore import FluidicDynamicsNanopore
from simulations.nanopore_electrokinetics import NanoporeElectrokinetics


class TestPhysicsAndSimulations(unittest.TestCase):
    def setUp(self):
        self.guard_sim = GuardRingElectrostatics()
        self.fluid_sim = FluidicDynamicsNanopore()
        self.pore_sim = NanoporeElectrokinetics(
            kcl_molarity=1.0, temperature_c=25.0, pore_diameter_nm=4.0, membrane_thickness_nm=20.0
        )

    def test_guard_ring_attenuation_and_leakage(self):
        """Verify driven guard ring provides > 20 dB of surface leakage suppression."""
        res = self.guard_sim.calculate_guard_attenuation(
            aggressor_voltage=3.3, core_voltage=0.0
        )
        self.assertGreater(res["i_unshielded_fa"], res["i_guarded_fa"])
        self.assertGreater(res["suppression_ratio"], 10.0) # > 10x suppression
        self.assertGreater(res["suppression_db"], 20.0)     # > 20 dB attenuation

    def test_weep_moat_saline_breach_detection(self):
        """Verify 1M KCl saline breach drops impedance from >10 Gohm to <1 kohm, tripping ESTOP."""
        moat = self.guard_sim.simulate_weep_moat_breach()
        self.assertGreater(moat["r_dry_gigaohms"], 10.0) # > 10 Giga-Ohms dry
        self.assertLess(moat["r_wet_ohms"], 1000.0)      # < 1 kOhm wet
        self.assertGreater(moat["v_sense_dry_volts"], 3.0) # Logic HIGH
        self.assertLess(moat["v_sense_wet_volts"], 0.8)    # Logic LOW
        self.assertTrue(moat["estop_tripped"])

    def test_weep_buffer_dry_quiescent_state(self):
        """Verify weep buffer N-FET is OFF dry, holding LP5907 EN at 3.3V with 1.8V VDD active."""
        dry = self.guard_sim.simulate_weep_buffer_circuit(v_fault=0.0)
        self.assertEqual(dry["v_gate_volts"], 0.0)
        self.assertFalse(dry["fet_conducting"])
        self.assertEqual(dry["v_en_pin_volts"], 3.3)
        self.assertEqual(dry["v_ldo_out_volts"], 1.8)
        self.assertFalse(dry["interlock_tripped"])
        self.assertTrue(dry["lp5907_safe"])

    def test_weep_buffer_positive_fault_interlock(self):
        """Verify +2.5V PORE_amp short turns N-FET ON, pulling LP5907 EN LOW and dropping 1.8V rail."""
        pos = self.guard_sim.simulate_weep_buffer_circuit(v_fault=2.5)
        self.assertGreater(pos["v_gate_volts"], 1.5) # Above 2N7002 V_th
        self.assertTrue(pos["fet_conducting"])
        self.assertLess(pos["v_en_pin_volts"], 0.4)  # Below LP5907 V_IL (0.4V)
        self.assertEqual(pos["v_ldo_out_volts"], 0.0)
        self.assertTrue(pos["interlock_tripped"])
        self.assertTrue(pos["lp5907_safe"])

    def test_weep_buffer_negative_excursion_clamping(self):
        """Verify -2.5V PORE_amp fault clamps gate to -0.3V, limits I_fault < 25 uA, and protects LP5907."""
        neg = self.guard_sim.simulate_weep_buffer_circuit(v_fault=-2.5)
        self.assertEqual(neg["v_gate_volts"], -0.3)
        self.assertLessEqual(neg["i_fault_ua"], 25.0) # 22 uA limited by 100k series R
        self.assertFalse(neg["fet_conducting"])
        self.assertEqual(neg["v_en_pin_volts"], 3.3)  # Isolated from -2.5V!
        self.assertTrue(neg["lp5907_safe"])
        self.assertTrue(neg["current_safe"])

    def test_fluidic_channel_resistance_and_reynolds(self):
        """Verify laminar creeping Stokes flow (Re < 5.0) and realistic pressure drop."""
        flow = self.fluid_sim.calculate_flowcell_pressure_drop(flow_rate_ul_min=25.0)
        self.assertTrue(flow["is_laminar"])
        self.assertLess(flow["reynolds_number"], 5.0)
        self.assertGreater(flow["delta_p_psi"], 0.0)
        self.assertLess(flow["delta_p_psi"], 1.0) # Should be low backpressure at 25 uL/min

    def test_sin_membrane_stress_and_burst_margin(self):
        """Verify SiNx membrane burst pressure and safety margins."""
        # 0.5 psi differential across membrane during continuous perfusion
        mem = self.fluid_sim.calculate_membrane_stress_and_burst(transmembrane_pressure_psi=0.5)
        self.assertTrue(mem["is_safe"])
        self.assertGreater(mem["safety_factor"], 2.0)
        self.assertGreater(mem["burst_pressure_psi"], 2.0)

    def test_nanopore_resistance_and_baseline_current(self):
        """Verify 4nm pore resistance in 1M KCl produces typical 5-15 nS conductance."""
        res = self.pore_sim.calculate_pore_resistance()
        self.assertGreater(res["conductance_ns"], 3.0)
        self.assertLess(res["conductance_ns"], 25.0)

        # Baseline at 180 mV
        base = self.pore_sim.calculate_baseline_current(180.0)
        self.assertGreater(base["i_baseline_pa"], 500.0)
        self.assertLess(base["i_baseline_pa"], 4000.0)
        # E-field inside pore lumen should exceed 1 MV/m
        self.assertGreater(base["e_field_v_m"], 1e6)

    def test_dna_translocation_blockade_depth(self):
        """Verify dsDNA creates deeper current blockade than ssDNA."""
        ds = self.pore_sim.calculate_dna_blockade(180.0, "dsDNA")
        ss = self.pore_sim.calculate_dna_blockade(180.0, "ssDNA")
        self.assertGreater(ds["blockade_depth_pa"], ss["blockade_depth_pa"])
        self.assertGreater(ds["fractional_blockade"], ss["fractional_blockade"])
        self.assertLess(ds["residual_current_pa"], ss["residual_current_pa"])

    def test_capture_radius_voltage_scaling(self):
        """Verify electrophoretic capture radius increases with applied voltage."""
        cap_100 = self.pore_sim.calculate_capture_radius_and_rate(100.0, 10.0)
        cap_200 = self.pore_sim.calculate_capture_radius_and_rate(200.0, 10.0)
        self.assertAlmostEqual(cap_200["capture_radius_um"], 2.0 * cap_100["capture_radius_um"], places=1)
        self.assertGreater(cap_200["capture_rate_hz"], cap_100["capture_rate_hz"])


if __name__ == "__main__":
    unittest.main()
