#!/usr/bin/env python3
"""
Sentinel Nanopore Reader — Four-Electrode Electrochemical Cell Simulation

Models and compares 2-electrode vs 4-electrode electrochemical cell dynamics:
1. Electrochemical Impedance Spectroscopy (EIS):
   - 2-Electrode Mode: Measures Z_cell = 2*Z_int(w) + 2*R_u + R_pore + 2*R_access
   - 4-Electrode Kelvin Mode: Measures Z_sensed = R_pore + 2*R_access + 2*R_u_eff(r_sense)
     where Z_int (electrode polarization) is completely eliminated by zero-current sense probes.
2. Geometric Uncompensated Resistance (R_u):
   - Remote channel layout (electrodes 15-25 mm off to side) vs.
   - Tight concentric annular rings (WS/RE at r=3.6-4.4 mm, WE/CE at r=5.6-7.2 mm).
3. Transient Step Response & DC Baseline Stability:
   - Simulates ionic current response to a voltage step (+V_bias applied at Working terminal,
     Counter tied to GNDA).
   - Demonstrates elimination of slow polarization relaxation (tau = R_ct * C_dl) in 4-electrode mode.
4. High-Frequency Bandwidth & Dwell Time Preservation:
   - Quantifies -3dB bandwidth cutoff: f_c = 1 / (2*pi*R_u*C_membrane).

Terminology (Gamry Standards):
- Working (WE): Positive terminal (+V_bias excitation into Cis chamber)
- Working Sense (WS / PS1): High-impedance potential probe at Cis aperture boundary
- Reference (RE / PS2): High-impedance potential probe at Trans aperture boundary
- Counter (CE): Negative return terminal connected to GNDA (Analog Ground)
- Counter Sense (CS): Senses potential directly at counter return
- Floating Ground (FloatGND / GNDA): Decoupled low-noise analog reference plane
"""

import math
import cmath
from typing import Dict, List, Tuple


class FourElectrodeCellSimulation:
    """
    Four-Electrode Electrochemical Cell Simulator.

    Terminology (Gamry Standards):
    - Working (WE): Positive terminal (+V_bias excitation into Cis chamber)
    - Working Sense (WS / PS1): High-impedance potential probe at Cis aperture boundary
    - Reference (RE / PS2): High-impedance potential probe at Trans aperture boundary
    - Counter (CE): Negative return terminal connected to GNDA (Analog Ground)
    - Counter Sense (CS): Senses potential directly at counter return
    - Floating Ground (FloatGND / GNDA): Decoupled low-noise analog reference plane
    """
    def __init__(
        self,
        # Electrolyte parameters (1M KCl at 25 deg C)
        electrolyte_conductivity_s_m: float = 10.5,  # S/m (~10.5 S/m for 1M KCl)
        # Nanopore parameters (solid-state nanopore)
        pore_diameter_nm: float = 4.0,
        membrane_thickness_nm: float = 10.0,
        membrane_capacitance_pf: float = 80.0,  # 80 pF flowcell/silicon nitride membrane
        # Electrode interfacial parameters (Ag/AgCl ENIG / sintered ribbon)
        r_ct_ohm: float = 150.0,        # Charge transfer resistance per electrode
        c_dl_uf: float = 2.0,           # Double layer capacitance (2 uF)
        warburg_sigma: float = 25.0,    # Warburg coefficient (ohm*s^-0.5)
        # 2-Electrode remote channel geometry
        remote_channel_length_mm: float = 18.0,
        remote_channel_width_mm: float = 1.0,
        remote_channel_height_mm: float = 0.5,
        # 4-Electrode concentric geometry
        concentric_h1_aperture_radius_mm: float = 3.1,  # 6.2mm diamond inscribed radius
        sense_ring_inner_r_mm: float = 3.6,
        sense_ring_outer_r_mm: float = 4.4,
        drive_ring_inner_r_mm: float = 5.6,
        drive_ring_outer_r_mm: float = 7.2,
        chamber_depth_mm: float = 0.8,
        # Instrument sense buffer input impedance (electrometer op-amp)
        sense_buffer_input_r_ohm: float = 1e13,  # 10 Teraohms
    ):
        self.sigma = electrolyte_conductivity_s_m
        self.d_pore = pore_diameter_nm * 1e-9
        self.l_pore = membrane_thickness_nm * 1e-9
        self.c_m = membrane_capacitance_pf * 1e-12
        
        self.r_ct = r_ct_ohm
        self.c_dl = c_dl_uf * 1e-6
        self.warburg_sigma = warburg_sigma
        
        self.l_remote = remote_channel_length_mm * 1e-3
        self.w_remote = remote_channel_width_mm * 1e-3
        self.h_remote = remote_channel_height_mm * 1e-3
        
        self.r_h1 = concentric_h1_aperture_radius_mm * 1e-3
        self.r_ws_in = sense_ring_inner_r_mm * 1e-3
        self.r_ws_out = sense_ring_outer_r_mm * 1e-3
        self.r_we_in = drive_ring_inner_r_mm * 1e-3
        self.r_we_out = drive_ring_outer_r_mm * 1e-3
        self.chamber_h = chamber_depth_mm * 1e-3
        
        self.r_buffer = sense_buffer_input_r_ohm

        # Compute intrinsic resistances
        self.r_pore = self.calculate_pore_resistance()
        self.r_access = self.calculate_access_resistance()
        self.ru_remote = self.calculate_remote_uncompensated_resistance()
        self.ru_concentric_sense = self.calculate_concentric_sense_uncompensated_resistance()
        self.ru_concentric_drive = self.calculate_concentric_drive_uncompensated_resistance()

    def calculate_pore_resistance(self) -> float:
        """
        Calculates pore lumen resistance:
        R_pore = (4 * l_pore) / (pi * d_pore^2 * sigma)
        """
        area = (math.pi / 4.0) * (self.d_pore ** 2)
        return self.l_pore / (self.sigma * area)

    def calculate_access_resistance(self) -> float:
        """
        Calculates access resistance per side (Hall's access resistance):
        R_access = 1 / (2 * sigma * d_pore)
        """
        return 1.0 / (2.0 * self.sigma * self.d_pore)

    def calculate_remote_uncompensated_resistance(self) -> float:
        """
        Calculates uncompensated solution resistance of remote channel (per side):
        R_u = L / (sigma * W * H)
        """
        area = self.w_remote * self.h_remote
        return self.l_remote / (self.sigma * area)

    def calculate_concentric_sense_uncompensated_resistance(self) -> float:
        """
        Calculates uncompensated resistance between aperture boundary (r_h1)
        and concentric sense ring mean radius r_sense:
        R = ln(r_sense / r_h1) / (2 * pi * sigma * chamber_h)
        """
        r_sense_mean = (self.r_ws_in + self.r_ws_out) / 2.0
        if r_sense_mean <= self.r_h1:
            return 10.0
        return math.log(r_sense_mean / self.r_h1) / (2.0 * math.pi * self.sigma * self.chamber_h)

    def calculate_concentric_drive_uncompensated_resistance(self) -> float:
        """
        Calculates bulk solution resistance between aperture boundary and
        outer drive ring (WE / CE):
        R = ln(r_drive / r_h1) / (2 * pi * sigma * chamber_h)
        """
        r_drive_mean = (self.r_we_in + self.r_we_out) / 2.0
        return math.log(r_drive_mean / self.r_h1) / (2.0 * math.pi * self.sigma * self.chamber_h)

    def electrode_impedance(self, freq_hz: float) -> complex:
        """
        Electrode interfacial impedance (Randles circuit model):
        Z_int(w) = (R_ct + Z_w) || (1 / (j*w*C_dl))
        where Z_w = sigma_w * (1 - j) / sqrt(w)
        """
        w = 2.0 * math.pi * max(freq_hz, 1e-3)
        zw = complex(self.warburg_sigma / math.sqrt(w), -self.warburg_sigma / math.sqrt(w))
        z_faradaic = self.r_ct + zw
        y_faradaic = 1.0 / z_faradaic
        y_dl = complex(0.0, w * self.c_dl)
        return 1.0 / (y_faradaic + y_dl)

    def membrane_pore_impedance(self, freq_hz: float) -> complex:
        """
        Nanopore and membrane impedance:
        R_pore_total = R_pore + 2*R_access
        Z_mp(w) = R_pore_total || (1 / (j*w*C_m))
        """
        w = 2.0 * math.pi * max(freq_hz, 1e-3)
        r_tot = self.r_pore + 2.0 * self.r_access
        y_pore = 1.0 / r_tot
        y_cm = complex(0.0, w * self.c_m)
        return 1.0 / (y_pore + y_cm)

    def impedance_two_electrode(self, freq_hz: float) -> complex:
        """
        Full 2-electrode measured cell impedance:
        Z_2elec(w) = 2 * Z_int(w) + 2 * R_u_remote + Z_mp(w)
        """
        z_int = self.electrode_impedance(freq_hz)
        z_mp = self.membrane_pore_impedance(freq_hz)
        return 2.0 * z_int + 2.0 * self.ru_remote + z_mp

    def impedance_four_electrode(self, freq_hz: float) -> complex:
        """
        4-electrode Kelvin measured impedance across WS and RE:
        V_sense = I_cell * (Z_mp(w) + 2 * R_u_concentric_sense)
        Because WS and RE connect to electrometer buffers (R_in = 1e13 ohm),
        sense electrode interfacial polarization current is negligible (~femtoamperes):
        Z_4elec(w) = Z_mp(w) + 2 * R_u_concentric_sense
        """
        z_mp = self.membrane_pore_impedance(freq_hz)
        # Attenuation of sense contact error by buffer input impedance:
        z_int_sense = self.electrode_impedance(freq_hz)
        # Voltage divider error factor: R_buffer / (R_buffer + Z_int_sense) ~= 1.0
        sense_error_factor = self.r_buffer / (self.r_buffer + abs(z_int_sense))
        return (z_mp + 2.0 * self.ru_concentric_sense) * sense_error_factor

    def run_eis_frequency_sweep(
        self,
        f_min: float = 1.0,
        f_max: float = 1e7,
        num_points: int = 50,
    ) -> List[Dict[str, float]]:
        """
        Simulates AC Electrochemical Impedance Spectroscopy (EIS) sweep from 1 Hz to 10 MHz.
        Returns tabular Bode and Nyquist coordinates for both 2-electrode and 4-electrode models.
        """
        results = []
        log_min = math.log10(f_min)
        log_max = math.log10(f_max)
        step = (log_max - log_min) / (num_points - 1)

        for i in range(num_points):
            f = 10.0 ** (log_min + i * step)
            z2 = self.impedance_two_electrode(f)
            z4 = self.impedance_four_electrode(f)

            results.append({
                "freq_hz": f,
                # 2-Electrode Mode
                "z2_mag": abs(z2),
                "z2_phase_deg": math.degrees(cmath.phase(z2)),
                "z2_real": z2.real,
                "z2_imag": z2.imag,
                # 4-Electrode Mode
                "z4_mag": abs(z4),
                "z4_phase_deg": math.degrees(cmath.phase(z4)),
                "z4_real": z4.real,
                "z4_imag": z4.imag,
            })

        return results

    def calculate_cutoff_bandwidths(self) -> Tuple[float, float]:
        """
        Calculates the low-pass -3dB bandwidth cutoff caused by uncompensated solution resistance
        interacting with membrane capacitance:
        f_c = 1 / (2 * pi * R_u * C_m)
        Returns: (fc_two_electrode_hz, fc_four_electrode_hz)
        """
        fc_2e = 1.0 / (2.0 * math.pi * (2.0 * self.ru_remote) * self.c_m)
        fc_4e = 1.0 / (2.0 * math.pi * (2.0 * self.ru_concentric_sense) * self.c_m)
        return fc_2e, fc_4e

    def simulate_voltage_step_transient(
        self,
        v_step_mv: float = 100.0,
        duration_us: float = 200.0,
        num_steps: int = 200,
    ) -> List[Dict[str, float]]:
        """
        Simulates transient current response to a +100 mV step applied between WE and CE.
        Compares:
        1. 2-Electrode current: suffers from slow polarization baseline drift due to C_dl charging.
        2. 4-Electrode sensed potential: instantly tracks true transmembrane potential.
        """
        v_app = v_step_mv * 1e-3
        dt = (duration_us * 1e-6) / num_steps
        
        # Nanopore steady state resistance
        r_pore_tot = self.r_pore + 2.0 * self.r_access
        
        # 2-Electrode time constants:
        # Fast membrane charging: tau_fast = (2*R_u_remote) * C_m
        tau_fast_2e = (2.0 * self.ru_remote) * self.c_m
        # Slow double-layer polarization: tau_slow = (R_ct + R_pore_tot) * C_dl
        # Note: In series with high-resistance pore, tau_slow is dominated by R_pore * C_dl / 2
        tau_slow_2e = (r_pore_tot + 2.0 * self.ru_remote + 2.0 * self.r_ct) * (self.c_dl / 2.0)
        
        # 4-Electrode tight concentric:
        # Fast membrane charging: tau_fast = (2*R_u_concentric) * C_m
        tau_fast_4e = (2.0 * self.ru_concentric_sense) * self.c_m

        i_ss = v_app / (r_pore_tot + 2.0 * self.ru_concentric_sense)
        
        results = []
        for step in range(num_steps):
            t = step * dt
            # 2-Electrode current:
            # Displays initial displacement spike followed by slow decay due to double-layer charging
            # I_2e(t) = I_ss * (1 - 0.2 * exp(-t / 0.05)) (showing polarization droop)
            drift_factor = 1.0 - 0.05 * math.exp(-t / max(tau_slow_2e * 1e-4, 1e-4))
            spike_2e = (v_app / (2.0 * self.ru_remote)) * math.exp(-t / max(tau_fast_2e, 1e-9))
            i_2e = i_ss * drift_factor + spike_2e * 0.01  # scale spike
            
            # Sensed potential in 2-Electrode mode: has electrode polarization drop:
            v_polarization = 2.0 * (self.r_ct * (1.0 - math.exp(-t / 1e-4))) * i_ss
            v_sense_2e = v_app - v_polarization - (2.0 * self.ru_remote * i_ss)

            # 4-Electrode Kelvin sensed potential: zero current through WS/RE, pure pore voltage
            # Fast settling determined purely by tau_fast_4e
            v_sense_4e = (v_app * (r_pore_tot / (r_pore_tot + 2.0 * self.ru_concentric_drive))) * (1.0 - math.exp(-t / max(tau_fast_4e, 1e-9)))

            results.append({
                "time_us": t * 1e6,
                "current_2e_na": i_2e * 1e9,
                "v_sense_2e_mv": v_sense_2e * 1e3,
                "v_sense_4e_mv": v_sense_4e * 1e3,
            })

        return results


def run_summary():
    sim = FourElectrodeCellSimulation()
    fc_2e, fc_4e = sim.calculate_cutoff_bandwidths()
    
    print("=" * 70)
    print("SENTINEL NANOPORE READER — 4-ELECTRODE ELECTROCHEMICAL CELL SIMULATION")
    print("=" * 70)
    print(f"Electrolyte: 1M KCl (sigma = {sim.sigma:.1f} S/m)")
    print(f"Pore Lumen Resistance (R_pore):      {sim.r_pore / 1e6:.2f} M-ohm")
    print(f"Pore Access Resistance (2*R_access): {2.0 * sim.r_access / 1e6:.2f} M-ohm")
    print("-" * 70)
    print("UNCOMPENSATED SOLUTION RESISTANCE (R_u):")
    print(f"  2-Electrode Remote Channel (18mm):    2 * {sim.ru_remote:.1f} = {2 * sim.ru_remote:.1f} ohm")
    print(f"  4-Electrode Tight Concentric (3.6mm): 2 * {sim.ru_concentric_sense:.1f} = {2 * sim.ru_concentric_sense:.1f} ohm")
    ru_reduction = (1.0 - sim.ru_concentric_sense / sim.ru_remote) * 100.0
    print(f"  -> Solution Resistance Reduction:     {ru_reduction:.1f}%")
    print("-" * 70)
    print("HIGH-FREQUENCY BANDWIDTH CUTOFF (f_c with C_m = 80 pF):")
    print(f"  2-Electrode Mode (-3dB cutoff):       {fc_2e / 1e3:.1f} kHz")
    print(f"  4-Electrode Mode (-3dB cutoff):       {fc_4e / 1e6:.2f} MHz")
    bandwidth_boost = fc_4e / fc_2e
    print(f"  -> Bandwidth Improvement Factor:      {bandwidth_boost:.1f}x")
    print("-" * 70)
    print("ELECTRODE INTERFACE POLARIZATION (Z_int at 100 Hz):")
    z_int_100 = sim.electrode_impedance(100.0)
    print(f"  Polarization Impedance per electrode: {abs(z_int_100):.1f} ohm (Phase: {math.degrees(cmath.phase(z_int_100)):.1f} deg)")
    print(f"  In 2-Electrode Mode: Appears in series with pore -> Baseline tilt & drift.")
    print(f"  In 4-Electrode Mode: Eliminated by WS/RE high-Z electrometer buffers (R_in = 10 TOhm).")
    print("=" * 70)


if __name__ == "__main__":
    run_summary()
