#!/usr/bin/env python3
"""
Sentinel Nanopore Reader — Nanopore Electrokinetics & Translocation Physics

Models the nanoscale electrical field, ionic conductance, and macromolecule
translocation signatures through solid-state and biological nanopores:
1. Analytical access resistance (Hall / Kowallis) + lumen channel resistance:
     R_total = (4 * rho * L) / (pi * d^2) + rho / d
2. Open pore baseline current I_0(V_bias, [KCl], T, d_pore, L_pore).
3. Translocation current blockade depth Delta I_b and fractional blockade.
4. Electrophoretic capture radius and capture rate vs transmembrane potential.
"""

import math
from typing import Dict, List, Tuple


class NanoporeElectrokinetics:
    def __init__(
        self,
        kcl_molarity: float = 1.0,           # 1.0 M KCl
        temperature_c: float = 25.0,         # 25.0 C
        pore_diameter_nm: float = 4.0,       # 4.0 nm pore lumen
        membrane_thickness_nm: float = 20.0, # 20.0 nm SiNx membrane
    ):
        self.c_kcl = kcl_molarity
        self.temp_c = temperature_c
        self.d_p = pore_diameter_nm * 1e-9
        self.l_p = membrane_thickness_nm * 1e-9

        # Calculate electrolyte resistivity rho_elec [ohm*m]
        # At 25C: 1M KCl ~ 10.5 S/m, temp coefficient ~ +2.1%/C
        sigma_25 = 10.5 * (self.c_kcl / 1.0)
        sigma_t = sigma_25 * (1.0 + 0.021 * (self.temp_c - 25.0))
        self.sigma = max(sigma_t, 0.01)
        self.rho = 1.0 / self.sigma

    def calculate_pore_resistance(self) -> Dict[str, float]:
        """
        Calculates geometric and access resistances of the nanopore:
        R_lumen = (4 * rho * L) / (pi * d^2)
        R_access = rho / (2 * d) per side -> 2 * R_access = rho / d
        R_total = R_lumen + 2 * R_access
        """
        r_lumen = (4.0 * self.rho * self.l_p) / (math.pi * (self.d_p ** 2))
        r_access_each = self.rho / (2.0 * self.d_p)
        r_total = r_lumen + (2.0 * r_access_each)
        conductance_ns = (1.0 / r_total) * 1e9

        return {
            "r_lumen_mohm": r_lumen / 1e6,
            "r_access_total_mohm": (2.0 * r_access_each) / 1e6,
            "r_total_mohm": r_total / 1e6,
            "conductance_ns": conductance_ns,
            "access_resistance_fraction": (2.0 * r_access_each) / r_total,
        }

    def calculate_baseline_current(self, bias_voltage_mv: float = 180.0) -> Dict[str, float]:
        """Calculates open pore ionic baseline current I_0 at given bias voltage."""
        v_volts = bias_voltage_mv * 1e-3
        res = self.calculate_pore_resistance()
        r_total_ohms = res["r_total_mohm"] * 1e6

        i_base_amps = v_volts / r_total_ohms
        i_base_pa = i_base_amps * 1e12

        # Electric field inside pore lumen: E_pore = V_bias / (L + (pi/2)*d)
        eff_length = self.l_p + (math.pi / 2.0) * self.d_p
        e_field_v_m = abs(v_volts) / eff_length

        return {
            "bias_mv": bias_voltage_mv,
            "i_baseline_pa": i_base_pa,
            "i_baseline_na": i_base_pa / 1000.0,
            "e_field_v_m": e_field_v_m,
            "e_field_mv_nm": e_field_v_m * 1e-6, # MV/m -> mV/nm
        }

    def calculate_dna_blockade(
        self,
        bias_voltage_mv: float = 180.0,
        analyte_type: str = "dsDNA", # "dsDNA" (2.2nm) or "ssDNA" (1.2nm)
    ) -> Dict[str, float]:
        """
        Calculates translocation blockade depth and residual current:
        Delta_I / I_0 = (d_analyte / d_pore)^2 * (1 / (1 + d_pore / (2 * L_pore)))
        """
        d_analyte = 2.2e-9 if analyte_type == "dsDNA" else 1.2e-9

        base = self.calculate_baseline_current(bias_voltage_mv)
        i_0 = base["i_baseline_pa"]

        # Geometric exclusion ratio
        area_ratio = (d_analyte / self.d_p) ** 2
        access_factor = 1.0 / (1.0 + (self.d_p / (2.0 * self.l_p)))
        fractional_blockade = min(0.99, area_ratio * access_factor)

        delta_i_pa = i_0 * fractional_blockade
        i_residual_pa = i_0 - delta_i_pa

        return {
            "analyte": analyte_type,
            "analyte_diameter_nm": d_analyte * 1e9,
            "i_baseline_pa": i_0,
            "fractional_blockade": fractional_blockade,
            "blockade_depth_pa": delta_i_pa,
            "residual_current_pa": i_residual_pa,
        }

    def calculate_capture_radius_and_rate(
        self,
        bias_voltage_mv: float = 180.0,
        dna_concentration_nm: float = 10.0, # 10 nM DNA
    ) -> Dict[str, float]:
        """
        Calculates electrophoretic capture radius r_c and capture frequency:
        r_c = (mu_ep * V_bias) / (2 * pi * D)
        Rate J = 2 * pi * D * c_0 * r_c = mu_ep * c_0 * V_bias
        """
        v_volts = abs(bias_voltage_mv * 1e-3)
        mu_ep = 4.5e-8 # DNA electrophoretic mobility ~ 4.5e-8 m^2/(V*s)
        d_diff = 3.0e-12 # Diffusion coefficient for ~1kbp DNA (3 um^2/s)

        # Capture radius r_c
        r_capture_m = (mu_ep * v_volts) / (2.0 * math.pi * d_diff)
        r_capture_um = r_capture_m * 1e6

        # Concentration in molecules/m^3
        # 1 nM = 1e-9 mol/L = 1e-6 mol/m^3 * 6.022e23 = 6.022e17 molecules/m^3
        c_molecules_m3 = (dna_concentration_nm * 1e-6) * 6.02214076e23

        # Capture rate [events / second]
        capture_rate_hz = 2.0 * math.pi * d_diff * c_molecules_m3 * r_capture_m

        return {
            "bias_mv": bias_voltage_mv,
            "capture_radius_um": r_capture_um,
            "capture_rate_hz": capture_rate_hz,
            "mean_inter_event_time_ms": (1.0 / max(capture_rate_hz, 1e-6)) * 1000.0,
        }


if __name__ == "__main__":
    sim = NanoporeElectrokinetics(kcl_molarity=1.0, temperature_c=25.0, pore_diameter_nm=4.0, membrane_thickness_nm=20.0)
    print("=== Nanopore Electrical Properties ===")
    res = sim.calculate_pore_resistance()
    print(f"Lumen Resistance:  {res['r_lumen_mohm']:.2f} MOhm")
    print(f"Access Resistance: {res['r_access_total_mohm']:.2f} MOhm (Fraction: {res['access_resistance_fraction'] * 100:.1f}%)")
    print(f"Total Resistance:  {res['r_total_mohm']:.2f} MOhm | Conductance: {res['conductance_ns']:.2f} nS")

    print("\n=== Baseline Current & Field (V_bias = 180 mV) ===")
    base = sim.calculate_baseline_current(180.0)
    print(f"Baseline Current:  {base['i_baseline_pa']:.1f} pA ({base['i_baseline_na']:.3f} nA)")
    print(f"Lumen E-Field:     {base['e_field_v_m'] / 1e6:.2f} MV/m ({base['e_field_mv_nm']:.2f} mV/nm)")

    print("\n=== DNA Translocation Blockades ===")
    ds = sim.calculate_dna_blockade(180.0, "dsDNA")
    print(f"dsDNA Blockade:    Delta I = {ds['blockade_depth_pa']:.1f} pA ({(ds['fractional_blockade'] * 100):.1f}% reduction) -> Residual = {ds['residual_current_pa']:.1f} pA")
    ss = sim.calculate_dna_blockade(180.0, "ssDNA")
    print(f"ssDNA Blockade:    Delta I = {ss['blockade_depth_pa']:.1f} pA ({(ss['fractional_blockade'] * 100):.1f}% reduction) -> Residual = {ss['residual_current_pa']:.1f} pA")

    print("\n=== Electrophoretic Capture Dynamics ===")
    cap = sim.calculate_capture_radius_and_rate(180.0, 10.0)
    print(f"Capture Radius:    {cap['capture_radius_um']:.1f} um")
    print(f"Capture Frequency: {cap['capture_rate_hz']:.1f} events/s (Inter-event time: {cap['mean_inter_event_time_ms']:.1f} ms)")
