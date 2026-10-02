"""
test_four_electrode_cell.py

Unit tests for Sentinel Nanopore Reader 4-Electrode Electrochemical Cell:
1. Validates physical calculation of pore lumen and access resistance.
2. Validates uncompensated solution resistance (R_u) reduction in tight concentric geometry.
3. Validates AC EIS impedance calculation and elimination of interfacial polarization (Z_int).
4. Validates high-frequency bandwidth cutoff enhancement (f_c = 1 / (2*pi*R_u*C_m)).
5. Validates transient step response settling and stability.
6. Validates adherence to standardized Gamry terminology (WE, WS, RE, CE, CS, FloatGND).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import unittest
from simulations.four_electrode_cell_simulation import FourElectrodeCellSimulation


class TestFourElectrodeCell(unittest.TestCase):

    def setUp(self):
        self.sim = FourElectrodeCellSimulation()

    def test_pore_and_access_resistance(self):
        """Verify solid-state nanopore lumen and Hall access resistance values."""
        # For d=4nm, l=10nm in 1M KCl (sigma=10.5 S/m):
        # R_pore = 10e-9 / (10.5 * pi/4 * 16e-18) ~= 75.8 Mohm
        self.assertGreater(self.sim.r_pore, 50e6)
        self.assertLess(self.sim.r_pore, 100e6)

        # 2 * R_access = 1 / (sigma * d_pore) = 1 / (10.5 * 4e-9) ~= 23.8 Mohm
        self.assertGreater(self.sim.r_access * 2.0, 15e6)
        self.assertLess(self.sim.r_access * 2.0, 30e6)

    def test_uncompensated_resistance_reduction(self):
        """Verify tight concentric rings reduce uncompensated resistance by > 90%."""
        ru_remote = self.sim.ru_remote
        ru_concentric = self.sim.ru_concentric_sense

        self.assertGreater(ru_remote, 1000.0, "Remote channel R_u must be > 1 kOhm")
        self.assertLess(ru_concentric, 100.0, "Concentric sense R_u must be < 100 Ohm")

        reduction_ratio = (ru_remote - ru_concentric) / ru_remote
        self.assertGreater(reduction_ratio, 0.90, "Concentric layout must reduce R_u by at least 90%")

    def test_electrode_polarization_elimination(self):
        """Verify 4-electrode Kelvin sensing eliminates electrode polarization impedance."""
        z_int_100hz = self.sim.electrode_impedance(100.0)
        # At 100 Hz, interfacial impedance is non-zero
        self.assertGreater(abs(z_int_100hz), 50.0)

        # In 2-electrode mode at 100 Hz, impedance includes 2*Z_int:
        z_2e = self.sim.impedance_two_electrode(100.0)
        # In 4-electrode mode, Z_int is rejected by high-Z buffer:
        z_4e = self.sim.impedance_four_electrode(100.0)

        # Real difference at low frequency between 2e and 4e must exceed 2*R_u + 2*Re(Z_int)
        self.assertGreater(z_2e.real - z_4e.real, 2.0 * self.sim.ru_remote)

    def test_eis_frequency_sweep(self):
        """Verify AC EIS frequency sweep produces correct tabular spectra."""
        sweep = self.sim.run_eis_frequency_sweep(f_min=1.0, f_max=1e6, num_points=20)
        self.assertEqual(len(sweep), 20)

        # Frequency must monotonically increase
        freqs = [pt["freq_hz"] for pt in sweep]
        self.assertEqual(freqs, sorted(freqs))

        # Check fields
        for pt in sweep:
            self.assertIn("z2_mag", pt)
            self.assertIn("z4_mag", pt)
            self.assertIn("z2_phase_deg", pt)
            self.assertIn("z4_phase_deg", pt)
            self.assertGreater(pt["z2_mag"], 0.0)
            self.assertGreater(pt["z4_mag"], 0.0)

    def test_bandwidth_cutoff_enhancement(self):
        """Verify -3dB bandwidth cutoff improves by > 10x with concentric sensing."""
        fc_2e, fc_4e = self.sim.calculate_cutoff_bandwidths()
        
        self.assertGreater(fc_2e, 1e4, "2-electrode cutoff must be in kHz range")
        self.assertGreater(fc_4e, fc_2e * 10.0, "4-electrode cutoff must be > 10x higher than 2-electrode")

    def test_transient_step_response(self):
        """Verify step response simulation demonstrates baseline stability."""
        transient = self.sim.simulate_voltage_step_transient(v_step_mv=100.0, duration_us=100.0, num_steps=50)
        self.assertEqual(len(transient), 50)

        # Check that 4-electrode sensed potential reaches > 95 mV without droop
        final_pt = transient[-1]
        self.assertGreater(final_pt["v_sense_4e_mv"], 95.0)

    def test_gamry_terminology_and_conventions(self):
        """Verify standardized terminology (WE, WS, RE, CE, CS, FloatGND) is present in docstrings."""
        doc = self.sim.__doc__ or ""
        self.assertIn("Working (WE)", doc)
        self.assertIn("Working Sense (WS", doc)
        self.assertIn("Reference (RE", doc)
        self.assertIn("Counter (CE)", doc)
        self.assertIn("Counter Sense (CS)", doc)
        self.assertIn("Floating Ground (FloatGND", doc)


if __name__ == "__main__":
    unittest.main()
