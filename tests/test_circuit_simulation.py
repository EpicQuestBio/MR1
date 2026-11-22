# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
test_circuit_simulation.py
===========================
Unit and physics verification tests for the Cartridge Amplifier board circuit simulation:
- Analytical DC gains and common-mode Vbias cancellation
- Small-signal AC transfer functions, pole locations, and active guard impedance
- Dynamical transient response to single-molecule DNA translocation events
- Noise power spectral density, Johnson thermal floor, and cumulative RMS noise
- Fluidic weep-sense safety interlock triggering and negative voltage clamp
- Standalone SPICE netlist generation and validation
"""

import math
import os
import sys
import unittest
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from simulations.amplifier_circuit_simulation import (
    AmplifierCircuitSimulation,
    CircuitParameters,
)


class TestAmplifierCircuitSimulation(unittest.TestCase):
    def setUp(self):
        self.sim = AmplifierCircuitSimulation()

    def test_route1_dc_transimpedance_and_vbias_rejection(self):
        """Verify Route 1 provides 10.0 GΩ transimpedance with exact Vbias cancellation."""
        gain = self.sim.route1_dc_transimpedance()
        # Stage 1: -1 GΩ, Stage 2: -10 V/V => Total: +10 GΩ (or -10 GΩ depending on sign convention)
        self.assertAlmostEqual(abs(gain), 10.0e9, delta=1.0e6)

        # Test common-mode Vbias rejection across various excitation voltages
        for v_bias in [-0.500, -0.180, 0.0, 0.180, 0.500, 1.000]:
            v_cm_out = self.sim.route1_vbias_rejection(v_bias)
            self.assertAlmostEqual(v_cm_out, 0.0, places=9, msg=f"Vbias leakage detected at Vbias={v_bias}V")

    def test_route1_poles_and_bandwidth(self):
        """Verify Route 1 Stage 1 and Stage 2 pole locations match design target."""
        fp1, fp2 = self.sim.route1_poles()
        # fp1 = 1 / (2*pi * 1GΩ * 2pF) = 79.577 Hz
        self.assertAlmostEqual(fp1, 79.577, places=2)
        # fp2 = 1 / (2*pi * 1kΩ * 100nF) = 1591.55 Hz
        self.assertAlmostEqual(fp2, 1591.55, places=1)

    def test_route2_transimpedance_and_active_guard(self):
        """Verify Route 2 wideband TIA and active guard driver performance."""
        gain2 = self.sim.route2_dc_transimpedance()
        self.assertAlmostEqual(gain2, -100.0e3, delta=10.0)

        fp_r2 = self.sim.route2_pole()
        # fp = 1 / (2*pi * 100kΩ * 15pF) = 106.103 kHz
        self.assertAlmostEqual(fp_r2, 106103.3, delta=50.0)

        # Active guard impedance should be < 0.05 Ω at 10 kHz
        z_guard = self.sim.active_guard_impedance(freq_hz=10.0e3)
        self.assertLess(abs(z_guard), 0.06)

    def test_anti_aliasing_filter_cutoff(self):
        """Verify differential anti-aliasing filter cutoff is approximately 2.95 MHz."""
        fc_aa = self.sim.anti_aliasing_filter_cutoff()
        # fc = 1 / (2*pi * 54Ω * 1nF) = 2.947 MHz
        self.assertAlmostEqual(fc_aa / 1e6, 2.947, places=2)

    def test_transient_dna_translocation_blockade(self):
        """Verify Route 1 time-domain transient response to single-molecule translocation."""
        res = self.sim.simulate_transient_dna_translocation(
            t_stop=0.030,
            dt=5.0e-6,
            i_baseline=100e-12,
            i_blockade=25e-12,
            t_event_start=0.010,
            t_dwell=0.010,
        )
        t = res["time"]
        v_diff = res["v_diff_v"]
        adc_codes = res["adc_codes"]

        # Baseline differential voltage: 100 pA * 10 GΩ = 1.0 V
        idx_base = int(0.008 / 5.0e-6)
        self.assertAlmostEqual(v_diff[idx_base], 1.0, delta=0.01)

        # Blockade level: (100 pA - 25 pA) * 10 GΩ = 0.75 V
        # Wait until near end of dwell time (t = 0.019s)
        idx_blockade = int(0.019 / 5.0e-6)
        self.assertAlmostEqual(v_diff[idx_blockade], 0.75, delta=0.02)

        # Check LSB resolution (16-bit, 2.048V Vref => ~62.5 µV)
        self.assertAlmostEqual(res["lsb_uv"], 62.5, delta=0.1)

    def test_transient_micropore_pulse(self):
        """Verify Route 2 fast response to microsecond micropore pulses."""
        res = self.sim.simulate_transient_micropore_pulse(
            t_stop=0.0005,
            dt=1.0e-7,
            i_baseline=10.0e-6,
            i_pulse=2.5e-6,
            t_pulse_start=0.0001,
            t_dwell=0.0001,
        )
        v_r2 = res["v_route2_v"]
        # Baseline: -10 µA * 100 kΩ = -1.0 V
        idx_base = int(0.00008 / 1.0e-7)
        self.assertAlmostEqual(v_r2[idx_base], -1.0, delta=0.01)
        # Blockade: -7.5 µA * 100 kΩ = -0.75 V
        idx_pulse = int(0.00018 / 1.0e-7)
        self.assertAlmostEqual(v_r2[idx_pulse], -0.75, delta=0.01)

    def test_noise_spectral_density_and_rms_integration(self):
        """Verify Johnson thermal noise floor and integrated RMS noise."""
        noise = self.sim.compute_noise_analysis(f_min=0.1, f_max=10.0e3, num_points=200)
        # Thermal floor: sqrt(4 * kB * T / 1GΩ) ≈ 4.058 fA/√Hz
        thermal_floor = noise["thermal_floor_fa"][0]
        self.assertAlmostEqual(thermal_floor, 4.058, places=2)

        # Integrated RMS noise over 80 Hz should be under 50 fA_rms
        rms_at_fp1 = noise["rms_at_fp1_fa"]
        self.assertLess(rms_at_fp1, 50.0)
        self.assertGreater(rms_at_fp1, 20.0)

    def test_weep_sense_interlock_and_clamping(self):
        """Verify fluidic weep moat safety interlock trigger and negative clamp."""
        weep = self.sim.compute_weep_sense_sweep(num_points=100)
        r_leak = weep["r_leak"]
        is_interlocked = weep["is_interlocked"]

        # When dry (R_leak = 10 MΩ), normal operation (interlock NOT asserted)
        idx_dry = np.argmin(np.abs(r_leak - 10.0e6))
        self.assertFalse(is_interlocked[idx_dry])
        self.assertAlmostEqual(weep["v_drain"][idx_dry], 3.3, delta=0.1)

        # When wet / breached (R_leak = 10 kΩ), interlock MUST be asserted
        idx_wet = np.argmin(np.abs(r_leak - 10.0e3))
        self.assertTrue(is_interlocked[idx_wet])
        self.assertAlmostEqual(weep["v_drain"][idx_wet], 0.05, delta=0.05)

        # Negative excursion clamping: Gate voltage clamped to Schottky forward drop (-0.35V)
        self.assertGreaterEqual(weep["v_gate_neg_clamped"], -0.40)
        self.assertLess(weep["v_gate_neg_unclamped"], -2.0)

    def test_spice_netlist_generation(self):
        """Verify standalone SPICE netlist contains macromodels and valid syntax."""
        tmp_cir = REPO_ROOT / "exports" / "simulations" / "test_amp.cir"
        netlist = self.sim.generate_spice_netlist(tmp_cir)
        self.assertTrue(tmp_cir.exists())
        self.assertIn(".subckt LMP7721_MODEL", netlist)
        self.assertIn(".subckt LTC6268_MODEL", netlist)
        self.assertIn(".subckt OPA2192_MODEL", netlist)
        self.assertIn(".subckt ADA4940_MODEL", netlist)
        self.assertIn(".subckt MAX4564_MODEL", netlist)
        self.assertIn(".tran", netlist)
        self.assertIn(".ac", netlist)
        self.assertIn(".noise", netlist)
        # Clean up temp file
        if tmp_cir.exists():
            tmp_cir.unlink()


if __name__ == "__main__":
    unittest.main()
