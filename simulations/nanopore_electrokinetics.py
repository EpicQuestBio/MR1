#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
MR1 Nanopore Reader — Nanopore Electrokinetics & Translocation Physics

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
        kcl_molarity: float = 1.0,           # 1.0 M KCl (or default salt concentration)
        temperature_c: float = 25.0,         # 25.0 C
        pore_diameter_nm: float = 4.0,       # 4.0 nm pore lumen
        membrane_thickness_nm: float = 20.0, # 20.0 nm SiNx membrane
        salt_type: str = "KCl",              # "KCl" or "NaCl"
        salt_molarity: float = None,         # Explicit salt molarity (overrides kcl_molarity)
        electrolyte_conductivity_s_m: float = None, # Explicit conductivity override (S/m)
        surface_charge_c_m2: float = 0.0,    # Optional pore wall surface charge density (C/m^2)
    ):
        self.salt_type = salt_type.upper()
        self.c_salt = salt_molarity if salt_molarity is not None else kcl_molarity
        self.c_kcl = self.c_salt  # Backwards compatibility alias
        self.temp_c = temperature_c
        self.d_p = pore_diameter_nm * 1e-9
        self.l_p = membrane_thickness_nm * 1e-9
        self.surface_charge_c_m2 = surface_charge_c_m2

        # Calculate electrolyte resistivity rho_elec [ohm*m]
        # At 25C: 1M KCl ~ 10.5 S/m, 1M NaCl ~ 8.5 S/m, temp coefficient ~ +2.1%/C
        if electrolyte_conductivity_s_m is not None:
            sigma_25 = electrolyte_conductivity_s_m
        elif self.salt_type == "NACL":
            # 1.0 M NaCl = 8.5 S/m, 0.154 M (physiological saline) = 1.54 S/m, 3.0 M = 20.0 S/m
            if abs(self.c_salt - 0.154) < 0.01:
                sigma_25 = 1.54
            elif abs(self.c_salt - 3.0) < 0.01:
                sigma_25 = 20.0
            else:
                sigma_25 = 8.5 * (self.c_salt / 1.0)
        else:
            # Default KCl
            sigma_25 = 10.5 * (self.c_salt / 1.0)

        sigma_t = sigma_25 * (1.0 + 0.021 * (self.temp_c - 25.0))
        self.sigma = max(sigma_t, 1e-9)  # Support down to non-ionic / ultrapure liquids
        self.rho = 1.0 / self.sigma

    def calculate_pore_resistance(self) -> Dict[str, float]:
        """
        Calculates geometric and access resistances of the nanopore:
        R_lumen = (4 * L) / (pi * sigma_lumen * d^2)
          where sigma_lumen = sigma_bulk + (4 * |Sigma_wall| * mu_counter) / d
        R_access = rho_bulk / (2 * d) per side -> 2 * R_access = rho_bulk / d
        R_total = R_lumen + 2 * R_access
        """
        mu_counter = 7.62e-8  # K+/Na+ counter-ion mobility (m^2 / (V*s))
        sigma_surf = (4.0 * abs(self.surface_charge_c_m2) * mu_counter) / self.d_p
        sigma_lumen = self.sigma + sigma_surf
        sigma_access = self.sigma + (0.5 * sigma_surf)  # Dukhin surface conduction at pore mouth
        r_lumen = (4.0 * self.l_p) / (math.pi * sigma_lumen * (self.d_p ** 2))
        r_access_each = 1.0 / (2.0 * sigma_access * self.d_p)
        r_total = r_lumen + (2.0 * r_access_each)
        conductance_ns = (1.0 / r_total) * 1e9

        return {
            "r_lumen_mohm": r_lumen / 1e6,
            "r_access_total_mohm": (2.0 * r_access_each) / 1e6,
            "r_total_mohm": r_total / 1e6,
            "conductance_ns": conductance_ns,
            "access_resistance_fraction": (2.0 * r_access_each) / r_total,
            "sigma_bulk_s_m": self.sigma,
            "sigma_surface_s_m": sigma_surf,
            "sigma_lumen_s_m": sigma_lumen,
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

    def calculate_coulter_blockade(
        self,
        particle_diameter_um: float = 2.0,
        bias_voltage_mv: float = 20.0,
    ) -> Dict[str, float]:
        """
        Calculates Coulter counter particle translocation blockade for micro-scale apertures
        using the DeBlois & Bean / Gregg & Steidley access-corrected relation:
        Delta_R / R = (d_particle^3 / (D_pore^2 * L_eff)) * F(d/D)
        where L_eff = L_pore + 0.8 * D_pore
        """
        d_particle = particle_diameter_um * 1e-6
        d_pore = self.d_p
        l_pore = self.l_p
        l_eff = l_pore + 0.8 * d_pore

        ratio = d_particle / d_pore
        if ratio >= 1.0:
            fractional_dr = 1.0
        else:
            # Correction factor F(d/D) ~ 1 + 0.8*(d/D)^2
            corr = 1.0 + 0.8 * (ratio ** 2)
            fractional_dr = min(0.99, ((d_particle ** 3) / ((d_pore ** 2) * l_eff)) * corr)

        base = self.calculate_baseline_current(bias_voltage_mv)
        i_0_pa = base["i_baseline_pa"]
        fractional_di = fractional_dr / (1.0 + fractional_dr)
        delta_i_pa = i_0_pa * fractional_di
        i_residual_pa = i_0_pa - delta_i_pa

        return {
            "particle_diameter_um": particle_diameter_um,
            "pore_diameter_um": self.d_p * 1e6,
            "bias_mv": bias_voltage_mv,
            "fractional_resistance_change": fractional_dr,
            "fractional_current_blockade": fractional_di,
            "delta_i_pa": delta_i_pa,
            "delta_i_na": delta_i_pa / 1000.0,
            "delta_i_ua": delta_i_pa / 1e6,
            "i_residual_pa": i_residual_pa,
            "i_baseline_ua": i_0_pa / 1e6,
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

    def calculate_gain_matching_and_saturation(
        self,
        bias_voltage_mv: float = 180.0,
        r_feedback_ohms: float = 1e9,
        v_full_scale_v: float = 2.048,
        stage2_gain: float = 10.0,
    ) -> Dict[str, float]:
        """
        Calculates TIA headroom and saturation status for current pore diameter:
        - Stage 1 (U2 LMP7721, 1 Gohm feedback) gives +-2.048 nA dynamic range at +-2.048V full scale.
        - Stage 2 (U16 LTC6268, 10.0x net post-gain) gives +-0.2048 nA (+-204.8 pA) full-chain range.
        """
        res = self.calculate_pore_resistance()
        r_pore_ohms = res["r_total_mohm"] * 1e6
        base = self.calculate_baseline_current(bias_voltage_mv)
        i_base_na = base["i_baseline_na"]
        i_max_na = (v_full_scale_v / r_feedback_ohms) * 1e9
        i_max_stage2_na = i_max_na / max(stage2_gain, 1.0)
        is_saturated = abs(i_base_na) > i_max_na
        is_saturated_stage2 = abs(i_base_na) > i_max_stage2_na
        max_vpore_stage2_mv = (i_max_stage2_na * 1e-9) * r_pore_ohms * 1e3

        return {
            "bias_mv": bias_voltage_mv,
            "r_feedback_ohms": r_feedback_ohms,
            "v_full_scale_v": v_full_scale_v,
            "i_baseline_na": i_base_na,
            "i_max_measurable_na": i_max_na,
            "i_max_stage2_na": i_max_stage2_na,
            "is_saturated": is_saturated,
            "is_saturated_stage2": is_saturated_stage2,
            "max_vpore_stage2_mv": max_vpore_stage2_mv,
            "headroom_fraction": max(0.0, 1.0 - (abs(i_base_na) / i_max_na)),
            "headroom_stage2_fraction": max(0.0, 1.0 - (abs(i_base_na) / i_max_stage2_na)),
        }
    def calculate_dual_path_performance(
        self,
        bias_voltage_mv: float = 100.0,
        r_f1_ohms: float = 1e9,
        c_f1_farads: float = 2e-12,
        r_f2_ohms: float = 100e3,
        c_f2_farads: float = 15e-12,
        stage2_gain_path1: float = 10.0,
        stage2_gain_path2: float = 1.0,
        v_full_scale_v: float = 2.048,
        r_post1_ohms: float = 1000.0,
        c_post1_farads: float = 100e-9,
    ) -> Dict[str, float]:
        """
        Calculates dual-path performance (Path 1 Sub-5nm LMP7721 + LTC6268 vs Path 2 200nm OPA2192 Wideband).
        Note: U16 (LTC6268) on Amplifier has R8=100, R5=1000 (+IN divider 10/11) and R4=100, R3=1000
        (non-inverting gain 11.0), yielding an exact net stage-2 signal gain of 10.0 V/V and zero Vbias offset.
        """
        import math
        res = self.calculate_pore_resistance()
        base = self.calculate_baseline_current(bias_voltage_mv)
        i_pore_a = base["i_baseline_na"] * 1e-9

        # Path 1 (LMP7721 Stage 1 + LTC6268 Stage 2)
        v_tia_path1 = abs(i_pore_a) * r_f1_ohms
        v_stage2_path1 = v_tia_path1 * stage2_gain_path1
        sat_path1 = (v_tia_path1 > v_full_scale_v) or (v_stage2_path1 > v_full_scale_v)
        f_3db_path1_tia_hz = 1.0 / (2.0 * math.pi * r_f1_ohms * c_f1_farads)
        f_3db_path1_post_hz = 1.0 / (2.0 * math.pi * r_post1_ohms * c_post1_farads)

        # Path 2 (OPA2192 Wideband)
        v_tia_path2 = abs(i_pore_a) * r_f2_ohms
        v_stage2_path2 = v_tia_path2 * stage2_gain_path2
        sat_path2 = v_stage2_path2 > v_full_scale_v
        headroom_path2 = max(0.0, 1.0 - (v_stage2_path2 / v_full_scale_v))
        f_3db_path2_hz = 1.0 / (2.0 * math.pi * r_f2_ohms * c_f2_farads)

        return {
            "pore_diameter_nm": self.d_p,
            "bias_mv": bias_voltage_mv,
            "r_pore_ohms": res["r_total_mohm"] * 1e6,
            "i_pore_na": base["i_baseline_na"],
            "v_tia_path1_v": v_tia_path1,
            "v_stage2_path1_v": v_stage2_path1,
            "stage2_gain_path1": stage2_gain_path1,
            "sat_path1": sat_path1,
            "f_3db_path1_tia_hz": f_3db_path1_tia_hz,
            "f_3db_path1_post_hz": f_3db_path1_post_hz,
            "v_tia_path2_v": v_tia_path2,
            "v_stage2_path2_v": v_stage2_path2,
            "sat_path2": sat_path2,
            "headroom_path2": headroom_path2,
            "f_3db_path2_hz": f_3db_path2_hz,
        }


if __name__ == "__main__":
    sim = NanoporeElectrokinetics(kcl_molarity=1.0, temperature_c=25.0, pore_diameter_nm=4.0, membrane_thickness_nm=20.0)
    print("=== Nanopore Electrical Properties ===")
    res = sim.calculate_pore_resistance()
    print(f"Lumen Resistance:  {res['r_lumen_mohm']:.2f} MOhm")
    print(f"Access Resistance: {res['r_access_total_mohm']:.2f} MOhm")
    print(f"Total Resistance:  {res['r_total_mohm']:.2f} MOhm | Conductance: {res['conductance_ns']:.2f} nS")

    print("=== Dual-Path Wide-Pore Performance (200 nm Pore) ===")
    sim_200 = NanoporeElectrokinetics(pore_diameter_nm=200.0, membrane_thickness_nm=40.0)
    perf = sim_200.calculate_dual_path_performance(bias_voltage_mv=100.0)
    print(f"200 nm Open Pore Current: {perf['i_pore_na']:.1f} nA")
    print(f"Path 1 Saturation: {perf['sat_path1']} | Path 2 Saturation: {perf['sat_path2']}")
    print(f"Path 2 -3dB Bandwidth: {perf['f_3db_path2_hz']/1000.0:.1f} kHz")
