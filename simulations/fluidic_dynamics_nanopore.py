#!/usr/bin/env python3
"""
Sentinel Nanopore Reader — Fluidic Dynamics & Flowcell Simulation

Models the hydrodynamic resistance, Navier-Stokes channel flow, and structural
membrane stress across the microfluidic flowcell and solid-state nanopore:
1. Hagen-Poiseuille resistance network for microchannels, tubing, and Luer bulkheads.
2. Pressure drop vs flow rate characteristics for Cis and Trans chambers.
3. Nanopore hydrodynamic resistance (continuum Poiseuille + Sampson access loss).
4. Silicon nitride (SiNx) membrane deflection and burst pressure safety margins.
"""

import math
from typing import Dict, List, Tuple


class FluidicDynamicsNanopore:
    def __init__(
        self,
        buffer_viscosity_pa_s: float = 1.002e-3, # Water @ 20C (1.002 mPa*s)
        buffer_density_kg_m3: float = 1045.0,    # 1M KCl solution density
        wafer_window_um: float = 10.0,           # 10x10 um free-standing membrane window (standard low-capacitance SiNx)
        membrane_thickness_nm: float = 20.0,     # 20 nm SiNx membrane
        membrane_yield_strength_pa: float = 1.5e9, # 1.5 GPa tensile yield strength of LPCVD SiNx
    ):
        self.mu = buffer_viscosity_pa_s
        self.rho = buffer_density_kg_m3
        self.a_mem = wafer_window_um * 1e-6
        self.t_mem = membrane_thickness_nm * 1e-9
        self.sigma_yield = membrane_yield_strength_pa

    def circular_tube_resistance(self, length_m: float, diameter_m: float) -> float:
        """Hydrodynamic resistance of a circular pipe: R_hyd = 128*mu*L / (pi*D^4) [Pa*s/m^3]."""
        return (128.0 * self.mu * length_m) / (math.pi * (diameter_m ** 4))

    def rectangular_channel_resistance(self, length_m: float, width_m: float, height_m: float) -> float:
        """
        Hydrodynamic resistance of a rectangular microchannel (h < w):
        R_hyd = (12 * mu * L) / (w * h^3 * (1 - 0.63 * (h / w)))
        """
        w, h = max(width_m, height_m), min(width_m, height_m)
        factor = 1.0 - 0.63 * (h / w)
        return (12.0 * self.mu * length_m) / (w * (h ** 3) * factor)

    def nanopore_hydrodynamic_resistance(self, pore_diameter_nm: float, pore_length_nm: float) -> float:
        """
        Hydrodynamic resistance of a nanoscale pore combining Poiseuille channel
        resistance with Sampson acoustic/access pressure loss:
        R_pore = (128 * mu * L) / (pi * d^4) + (3 * mu) / d^3
        """
        d = pore_diameter_nm * 1e-9
        l = pore_length_nm * 1e-9
        r_channel = (128.0 * self.mu * l) / (math.pi * (d ** 4))
        r_sampson = (3.0 * self.mu) / (d ** 3)
        return r_channel + r_sampson

    def calculate_flowcell_pressure_drop(
        self,
        flow_rate_ul_min: float = 25.0,
        tubing_len_mm: float = 150.0,
        tubing_id_mm: float = 0.51, # 0.51 mm FEP microbore
        channel_len_mm: float = 30.0,
        channel_w_mm: float = 2.0,
        channel_h_mm: float = 0.5,
    ) -> Dict[str, float]:
        """Calculates pressure drop across the Cis/Trans feed lines at given flow rate."""
        # Flow rate in m^3/s: 1 uL/min = 1e-9 m^3 / 60 s = 1.6667e-11 m^3/s
        q_m3_s = (flow_rate_ul_min * 1e-9) / 60.0

        r_tube = self.circular_tube_resistance(tubing_len_mm * 1e-3, tubing_id_mm * 1e-3)
        r_channel = self.rectangular_channel_resistance(
            channel_len_mm * 1e-3, channel_w_mm * 1e-3, channel_h_mm * 1e-3
        )

        r_total = r_tube + r_channel
        delta_p_pa = q_m3_s * r_total
        delta_p_psi = delta_p_pa / 6894.76
        delta_p_mbar = delta_p_pa / 100.0

        # Calculate Reynolds number in feed tubing: Re = rho * v * D / mu
        v_tube = q_m3_s / (math.pi * ((tubing_id_mm * 1e-3 / 2.0) ** 2))
        reynolds = (self.rho * v_tube * (tubing_id_mm * 1e-3)) / self.mu

        return {
            "flow_rate_ul_min": flow_rate_ul_min,
            "r_hyd_total_pa_s_m3": r_total,
            "delta_p_pa": delta_p_pa,
            "delta_p_psi": delta_p_psi,
            "delta_p_mbar": delta_p_mbar,
            "flow_velocity_m_s": v_tube,
            "reynolds_number": reynolds,
            "is_laminar": reynolds < 2000.0,
        }

    def calculate_membrane_stress_and_burst(self, transmembrane_pressure_psi: float) -> Dict[str, float]:
        """
        Calculates maximum mechanical stress and deflection on the thin SiNx window
        under transmembrane pressure differential Delta P = P_cis - P_trans:
        sigma_max = 0.308 * Delta_P * (a / t)^2
        """
        delta_p_pa = transmembrane_pressure_psi * 6894.76
        ratio = self.a_mem / self.t_mem # Aspect ratio (e.g. 50 um / 20 nm = 2500)

        # Maximum stress at edge clamped boundaries
        sigma_max_pa = 0.308 * delta_p_pa * (ratio ** 2)

        # Central deflection w_max for thin plate:
        # w_max = 0.0138 * Delta_P * a^4 / (D_flex), where D_flex = E * t^3 / (12 * (1 - nu^2))
        e_sin = 250e9 # Young's modulus 250 GPa
        nu_sin = 0.23 # Poisson's ratio
        d_flex = (e_sin * (self.t_mem ** 3)) / (12.0 * (1.0 - (nu_sin ** 2)))
        w_max_m = (0.0138 * delta_p_pa * (self.a_mem ** 4)) / max(d_flex, 1e-30)

        # Burst pressure (pressure at which sigma_max reaches yield strength)
        p_burst_pa = self.sigma_yield / (0.308 * (ratio ** 2))
        p_burst_psi = p_burst_pa / 6894.76

        safety_factor = p_burst_pa / max(delta_p_pa, 1.0)

        return {
            "delta_p_psi": transmembrane_pressure_psi,
            "delta_p_pa": delta_p_pa,
            "sigma_max_mpa": sigma_max_pa / 1e6,
            "deflection_nm": w_max_m * 1e9,
            "burst_pressure_psi": p_burst_psi,
            "burst_pressure_mbar": p_burst_pa / 100.0,
            "safety_factor": safety_factor,
            "is_safe": safety_factor > 2.0,
        }


if __name__ == "__main__":
    sim = FluidicDynamicsNanopore()
    print("=== Flowcell Channel Hydrodynamics ===")
    flow = sim.calculate_flowcell_pressure_drop(flow_rate_ul_min=25.0)
    print(f"Flow Rate: {flow['flow_rate_ul_min']} uL/min")
    print(f"Total Pressure Drop: {flow['delta_p_psi']:.3f} psi ({flow['delta_p_mbar']:.2f} mbar)")
    print(f"Flow Velocity: {flow['flow_velocity_m_s'] * 1000:.1f} mm/s | Reynolds: {flow['reynolds_number']:.4f} (Laminar: {flow['is_laminar']})")

    print("\n=== Nanopore Membrane Mechanical Stress ===")
    mem = sim.calculate_membrane_stress_and_burst(transmembrane_pressure_psi=1.5)
    print(f"Delta P: {mem['delta_p_psi']} psi -> Peak Stress: {mem['sigma_max_mpa']:.1f} MPa")
    print(f"Burst Pressure: {mem['burst_pressure_psi']:.2f} psi ({mem['burst_pressure_mbar']:.1f} mbar)")
    print(f"Safety Factor: {mem['safety_factor']:.2f}x (Safe: {mem['is_safe']})")
