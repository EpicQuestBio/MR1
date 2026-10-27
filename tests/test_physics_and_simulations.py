# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
Unit tests for MR1 physical simulations:
- Guard ring and guard trace electrostatics & weep moat leak detection.
- Microfluidic channel fluid dynamics, hydrodynamic resistance, and SiNx membrane burst limits.
- Nanopore electrokinetics, ionic conductance, translocation blockades, and capture dynamics.
"""

import unittest
from simulations.guard_ring_electrostatics import GuardRingElectrostatics
from simulations.fluidic_dynamics_nanopore import FluidicDynamicsNanopore
from simulations.nanopore_electrokinetics import NanoporeElectrokinetics
from simulations.pore_dac_dynamics import PoreDacDynamics
from simulations.opamp_signal_conditioning import OpAmpSignalConditioningSimulation


class TestPhysicsAndSimulations(unittest.TestCase):
    def setUp(self):
        self.guard_sim = GuardRingElectrostatics()
        self.fluid_sim = FluidicDynamicsNanopore()
        self.pore_sim = NanoporeElectrokinetics(
            kcl_molarity=1.0, temperature_c=25.0, pore_diameter_nm=4.0, membrane_thickness_nm=20.0
        )
        self.dac_sim = PoreDacDynamics()
        self.opamp_sim = OpAmpSignalConditioningSimulation()

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


    def test_wide_pore_200nm_dual_path_performance(self):
        """Verify 200 nm pore operates unsaturated on Path 2 (Wideband 100k TIA) while saturating Path 1."""
        wide_pore_sim = NanoporeElectrokinetics(pore_diameter_nm=200.0, membrane_thickness_nm=40.0)

        # 1. 200 nm pore resistance in 1M KCl (500 kohm - 1 Mohm)
        res_200 = wide_pore_sim.calculate_pore_resistance()
        self.assertGreaterEqual(res_200["r_total_mohm"] * 1e6, 300e3)
        self.assertLessEqual(res_200["r_total_mohm"] * 1e6, 1.5e6)

        # 2. At 100 mV bias, open pore current is ~200 nA
        perf_100mv = wide_pore_sim.calculate_dual_path_performance(bias_voltage_mv=100.0)
        self.assertGreaterEqual(perf_100mv["i_pore_na"], 100.0)
        self.assertLessEqual(perf_100mv["i_pore_na"], 500.0)

        # Path 1 saturates on 200 nm pore
        self.assertTrue(perf_100mv["sat_path1"])

        # Path 2 operates unsaturated with > 90% headroom
        self.assertFalse(perf_100mv["sat_path2"])
        self.assertGreater(perf_100mv["headroom_path2"], 0.90)

        # Path 2 output voltage at 200 nA is 20 mV
        self.assertAlmostEqual(perf_100mv["v_stage2_path2_v"], perf_100mv["i_pore_na"] * 1e-9 * 100e3, delta=0.005)

        # Path 2 bandwidth (-3dB) at Rf=100k, Cf=15pF is ~106 kHz
        self.assertAlmostEqual(perf_100mv["f_3db_path2_hz"], 106103.0, delta=1000.0)

        # 3. At 1.0V bias, open pore current is ~1-2 uA
        perf_1v = wide_pore_sim.calculate_dual_path_performance(bias_voltage_mv=1000.0)
        self.assertGreaterEqual(perf_1v["i_pore_na"], 1000.0)
        self.assertFalse(perf_1v["sat_path2"])

    def test_gain_matching_and_saturation(self):
        """Verify 4nm pore operates unsaturated under 1 Gohm feedback while large pores saturate."""
        # 4 nm pore at 180 mV in 1M KCl
        gain_4nm = self.pore_sim.calculate_gain_matching_and_saturation(180.0, r_feedback_ohms=1e9, v_full_scale_v=2.048)
        self.assertFalse(gain_4nm["is_saturated"])
        self.assertGreater(gain_4nm["headroom_fraction"], 0.0)

        # 20 nm pore at 180 mV in 1M KCl exceeds 2 nA
        large_pore_sim = NanoporeElectrokinetics(pore_diameter_nm=20.0, membrane_thickness_nm=20.0)
        gain_20nm = large_pore_sim.calculate_gain_matching_and_saturation(180.0, r_feedback_ohms=1e9, v_full_scale_v=2.048)
        self.assertTrue(gain_20nm["is_saturated"])

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

    def test_dac_analog_bandwidth_slew_rate_limits(self):
        """Verify MCP4822 slew rate limit of 0.55 V/us yields 85.5 kHz in 1x mode and 42.7 kHz in 2x mode."""
        bw_1x = self.dac_sim.calculate_slew_limited_bandwidth(gain_2x=False)
        self.assertAlmostEqual(bw_1x["f_max_full_power_khz"], 85.48, places=1)
        self.assertEqual(bw_1x["v_full_scale_v"], 2.048)

        bw_2x = self.dac_sim.calculate_slew_limited_bandwidth(gain_2x=True)
        self.assertAlmostEqual(bw_2x["f_max_full_power_khz"], 42.74, places=1)
        self.assertEqual(bw_2x["v_full_scale_v"], 4.096)

        settle = self.dac_sim.calculate_settling_rate()
        self.assertAlmostEqual(settle["max_resolved_sps"], 222222.2, places=0)

    def test_dac_spi_throughput_and_hardware_limit(self):
        """Verify 20 MHz SPI 16-bit frame transfer takes 800 ns, yielding 1.17 MSPS raw throughput."""
        spi = self.dac_sim.calculate_spi_throughput()
        self.assertAlmostEqual(spi["frame_transfer_ns"], 800.0, places=1)
        self.assertAlmostEqual(spi["min_cycle_time_ns"], 855.0, places=1)
        self.assertGreater(spi["max_theoretical_sps"], 1.1e6)
        self.assertGreaterEqual(spi["realistic_dma_sps"], 8.0e5)

    def test_dac_waveform_reconstruction_density(self):
        """Verify waveform table generation across standard frequencies."""
        table = self.dac_sim.generate_waveform_table()
        self.assertEqual(len(table), 8)
        # 1 kHz sine should have 800 samples/cycle at 800 kSPS
        row_1k = next(r for r in table if r["frequency_hz"] == 1000.0)
        self.assertGreaterEqual(row_1k["samples_per_cycle"], 800.0)
        self.assertTrue(row_1k["analog_ok"])

    def test_micropore_10um_nacl_simulation(self):
        """Verify 10 micron pore simulation in 1M NaCl under Path 2 wideband TIA."""
        from simulations.micropore_configuration_table import simulate_pore_configuration

        cfg_10um = simulate_pore_configuration(
            pore_diameter_um=10.0,
            membrane_length_um=10.0,
            electrolyte_key="1.0M NaCl",
            bias_mv=20.0,
        )
        # 1. Total resistance should be ~25-30 kOhm
        self.assertGreaterEqual(cfg_10um["r_total_ohms"], 20e3)
        self.assertLessEqual(cfg_10um["r_total_ohms"], 35e3)

        # 2. Path 1 (1 Gohm) saturates
        self.assertTrue(cfg_10um["sat_path1"])

        # 3. Path 2 (100 kohm) operates unsaturated with > 90% headroom at 20 mV
        self.assertFalse(cfg_10um["sat_path2"])
        self.assertGreater(cfg_10um["headroom_path2_pct"], 90.0)
        self.assertAlmostEqual(cfg_10um["v_out_path2_v"], 0.075, delta=0.01)

        # 4. 4-Electrode concentric sensing eliminates uncompensated solution drop (< 0.1% error)
        self.assertLess(cfg_10um["voltage_error_4e_pct"], 0.1)
        self.assertGreater(cfg_10um["voltage_error_2e_pct"], 20.0)

        # 5. Coulter particle blockade (2 um particle in 10 um pore gives ~3.4 nA pulse at 20 mV)
        self.assertGreater(cfg_10um["coulter_delta_i_na"], 2.0)

    def test_micropore_100um_nacl_simulation(self):
        """Verify 100 micron pore simulation in 1M NaCl: Path 2 saturation limits and 4-electrode requirement."""
        from simulations.micropore_configuration_table import simulate_pore_configuration

        # At low bias (10 mV), Path 2 operates unsaturated
        cfg_100um_low = simulate_pore_configuration(
            pore_diameter_um=100.0,
            membrane_length_um=10.0,
            electrolyte_key="1.0M NaCl",
            bias_mv=10.0,
        )
        self.assertFalse(cfg_100um_low["sat_path2"])
        self.assertLess(cfg_100um_low["v_out_path2_v"], 1.0)

        # At higher bias (50 mV), Path 2 (100k) saturates, but 10k feedback operates cleanly
        cfg_100um_high = simulate_pore_configuration(
            pore_diameter_um=100.0,
            membrane_length_um=10.0,
            electrolyte_key="1.0M NaCl",
            bias_mv=50.0,
        )
        self.assertTrue(cfg_100um_high["sat_path2"])
        self.assertFalse(cfg_100um_high["sat_10k"])
        self.assertLess(cfg_100um_high["v_out_10k_v"], 1.0)

        # 2-Electrode mode loses > 80% of voltage in remote solution channels
        self.assertGreater(cfg_100um_high["voltage_error_2e_pct"], 80.0)
        # 4-Electrode concentric keeps voltage error under 1.0%
        self.assertLess(cfg_100um_high["voltage_error_4e_pct"], 1.0)

    def test_micropore_matrix_generation(self):
        """Verify complete matrix generator and markdown table formatting."""
        from simulations.micropore_configuration_table import (
            generate_configuration_matrix,
            format_markdown_table,
        )

        matrix = generate_configuration_matrix()
        self.assertGreater(len(matrix), 50)
        md = format_markdown_table(matrix[:5])
        self.assertIn("10 $\\mu\\text{m}$", md)
        self.assertIn("Path 2", md)

    def test_mr1_composite_bipolar_dac_summing_amplifier(self):
        """Verify MR1 U3A/U3B OPA2197 composite bipolar summing amplifier range, midscale 0V, and 100:1 vernier."""
        # Midscale coarse (code_a=2048 -> 1.024V) and zero fine (code_b=0) produces 0.000V at >PORE
        mid = self.opamp_sim.calculate_excitation_voltage(code_a=2048, code_b=0)
        self.assertAlmostEqual(mid["v_u3b_ref_neg_v"], -2.048, places=4)
        self.assertAlmostEqual(mid["v_pore_out_v"], 0.0, places=5)
        self.assertAlmostEqual(mid["step_coarse_mv"], 1.20, places=3)
        self.assertAlmostEqual(mid["step_fine_uv"], 12.0, places=2)
        self.assertAlmostEqual(mid["vernier_ratio"], 100.0, places=2)
        self.assertGreater(mid["effective_resolution_bits"], 18.5)

        # Zero DAC codes (code_a=0, code_b=0) produce +2.4576V (within +2.49V LT3045 rail)
        pos_max = self.opamp_sim.calculate_excitation_voltage(code_a=0, code_b=0)
        self.assertAlmostEqual(pos_max["v_pore_out_v"], 2.4576, places=4)
        self.assertFalse(pos_max["is_rail_saturated"])

        # Fine vernier step of 100 LSBs on Ch B shifts output by exactly -1.20 mV (1 coarse LSB)
        vernier_100 = self.opamp_sim.calculate_excitation_voltage(code_a=2048, code_b=100)
        self.assertAlmostEqual(vernier_100["v_pore_out_v"], -0.0012, places=6)

        # Verify PoreDacDynamics helper matches
        dac_comp = self.dac_sim.calculate_composite_bipolar_driver(code_a=2048, code_b=0)
        self.assertAlmostEqual(dac_comp["v_pore_out_v"], 0.0, places=5)
        self.assertAlmostEqual(dac_comp["f_3db_u3a_feedback_hz"], 6631.46, delta=5.0)
        self.assertAlmostEqual(dac_comp["f_3db_output_rc_hz"], 58946.3, delta=50.0)

    def test_amplifier_route1_reference_cancellation_and_poles(self):
        """Verify Amplifier Route 1 (U2 LMP7721 + U16 LTC6268) 10.0x stage-2 gain and exact Vbias cancellation."""
        # Test at +180 mV bias and -500 mV bias with 100 pA pore current:
        # Output at Route1_OUT must be -1.000V regardless of Vbias common-mode voltage!
        r1_pos_bias = self.opamp_sim.calculate_route1_dc_transfer(i_pore_a=100e-12, v_bias_v=0.180)
        r1_neg_bias = self.opamp_sim.calculate_route1_dc_transfer(i_pore_a=100e-12, v_bias_v=-0.500)
        self.assertAlmostEqual(r1_pos_bias["stage2_effective_gain_v_v"], 10.0, places=5)
        self.assertAlmostEqual(r1_pos_bias["common_mode_vbias_leakage_v_v"], 0.0, places=9)
        self.assertAlmostEqual(r1_pos_bias["v_route1_out_v"], -1.000, places=5)
        self.assertAlmostEqual(r1_neg_bias["v_route1_out_v"], -1.000, places=5)
        self.assertAlmostEqual(r1_pos_bias["total_transimpedance_gohm"], -10.0, places=4)

        # Verify cascaded poles: fc1 = 79.58 Hz (R1=1G || C1=2pF), fc2 = 1591.55 Hz (R3=1k || C9=100nF)
        ac_fc1 = self.opamp_sim.route1_frequency_response(freq_hz=79.5775)
        self.assertAlmostEqual(ac_fc1["f_3db_stage1_hz"], 79.5775, places=2)
        self.assertAlmostEqual(ac_fc1["f_3db_stage2_hz"], 1591.55, places=1)
        self.assertAlmostEqual(ac_fc1["relative_db"], -3.01, delta=0.05)

        # Verify femtoampere noise model (1 GOhm thermal floor ~4.07 fA/rtHz)
        noise = self.opamp_sim.calculate_route1_noise_psd(freq_hz=10.0, c_in_pf=15.0)
        self.assertAlmostEqual(noise["i_thermal_r1_fa_rthz"], 4.07, delta=0.1)
        self.assertLess(noise["i_rms_pa"], 0.5)  # Sub-500 fA RMS integrated over 79.6 Hz BW

    def test_amplifier_route2_active_guard_and_full_adc_chain(self):
        """Verify Route 2 U5B active guard impedance suppression and full U17 -> U6 -> AD4000 chain."""
        guard_cmp = self.opamp_sim.compare_passive_vs_active_guard(freq_hz=10_000.0, r_vbias_source_ohm=200.0)
        self.assertLess(guard_cmp["z_guard_active_ohm"], 0.1)
        self.assertGreater(guard_cmp["active_suppression_improvement_db"], 60.0)

        # Full chain on Route 1 at 100 pA -> Route1_OUT = -1.0V -> U17 (ADG1219) -> U6 (ADA4940-1) -> AD4000
        chain_r1 = self.opamp_sim.simulate_full_readout_chain(i_pore_a=100e-12, route_sel=0, v_bias_v=0.180)
        self.assertAlmostEqual(chain_r1["v_mux_in_v"], -1.0, places=4)
        self.assertAlmostEqual(chain_r1["f_3db_antialiasing_hz"], 2_947_314.0, delta=1000.0)
        self.assertAlmostEqual(chain_r1["mux_ron_attenuation_factor"], 499.0 / (499.0 + 150.0), places=4)
        self.assertGreater(chain_r1["adc_signed_code_16bit"], 10000)

        # Full chain on Route 2 at 5 uA -> Route2_OUT = -0.5V (at Vbias=0V)
        chain_r2 = self.opamp_sim.simulate_full_readout_chain(i_pore_a=5e-6, route_sel=1, v_bias_v=0.0)
        self.assertAlmostEqual(chain_r2["v_mux_in_v"], -0.5, places=4)
        self.assertAlmostEqual(chain_r2["mux_ron_attenuation_factor"], 499.0 / (499.0 + 150.0 + 49.9), places=4)

    def test_broad_range_5nm_to_200um_ionic_and_non_ionic_balancing(self):
        """Verify V_PORE and dual TIA routes (Route 1 & Route 2) balance across 5 nm to 200 um in ionic & non-ionic liquids."""
        # 1. Verify DAC solver achieves sub-6uV quantization error across bipolar range
        for v_req in [1.80, 0.180, 0.01259, 0.00396, 0.0, -0.500]:
            solved = self.opamp_sim.solve_dac_codes_for_vpore(v_req)
            self.assertLessEqual(abs(solved["quantization_error_uv"]), 6.5)

        # 2. Extreme high-conductance corner: 200 um pore in 3.0M NaCl (20 S/m, R_pore ~ 330 Ohm)
        # Must select Route 2 (-100 kOhm) and use fine vernier V_PORE (~3.96 mV) to avoid saturation
        hi_cond_200um = self.opamp_sim.balance_vpore_and_dual_tia(
            pore_diameter_nm=200_000.0,
            membrane_thickness_nm=50_000.0,
            liquid_conductivity_s_m=20.0,
            surface_charge_c_m2=-0.02,
        )
        self.assertEqual(hi_cond_200um["selected_route"], 1)
        self.assertFalse(hi_cond_200um["is_saturated"])
        self.assertTrue(hi_cond_200um["is_resolvable"])
        self.assertAlmostEqual(hi_cond_200um["v_tia_mux_out_v"], -1.20, delta=0.02)
        self.assertGreater(hi_cond_200um["snr_db"], 90.0)

        # 3. Sub-5nm corner in 1.0M KCl: 5 nm pore (10.5 S/m, R_pore ~ 106 MOhm)
        # Must select Route 1 (-10 GOhm) and scale V_PORE (~12.6 mV) so Stage 2 U16 does not saturate
        nano_5nm_kcl = self.opamp_sim.balance_vpore_and_dual_tia(
            pore_diameter_nm=5.0,
            membrane_thickness_nm=20.0,
            liquid_conductivity_s_m=10.5,
            surface_charge_c_m2=-0.02,
        )
        self.assertEqual(nano_5nm_kcl["selected_route"], 0)
        self.assertFalse(nano_5nm_kcl["is_saturated"])
        self.assertTrue(nano_5nm_kcl["is_resolvable"])
        self.assertAlmostEqual(nano_5nm_kcl["v_tia_mux_out_v"], -1.20, delta=0.02)
        self.assertGreater(nano_5nm_kcl["snr_db"], 65.0)

        # 4. Non-ionic / polar organic & DI water corners across 5 nm to 200 um:
        # Notice that in low-conductivity / non-ionic liquids, even a 200 um micropore (R ~ 65 MOhm - 1 GOhm)
        # switches to Route 1 (-10 GOhm femtoampere TIA) to maintain >70 dB SNR!
        matrix = self.opamp_sim.evaluate_broad_range_sensing_matrix()
        self.assertEqual(len(matrix), 42)
        for row in matrix:
            self.assertFalse(row["is_saturated"], f"Saturated on {row['liquid_name']} {row['pore_diameter_nm']} nm")
            self.assertTrue(row["is_resolvable"], f"Unresolvable on {row['liquid_name']} {row['pore_diameter_nm']} nm")
            self.assertGreaterEqual(row["snr_db"], 60.0)


if __name__ == "__main__":
    unittest.main()
