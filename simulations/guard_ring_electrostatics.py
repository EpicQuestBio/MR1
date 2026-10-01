#!/usr/bin/env python3
"""
Sentinel Nanopore Reader — Guard Ring & Guard Trace Electrostatic Simulation

Models the physics of ultra-low leakage transimpedance amplifier (TIA) guarding
on Rogers RO4350B / PTFE substrate:
1. 2D Finite-Difference Laplace Equation Solver:
     d^2V/dx^2 + d^2V/dy^2 = 0
2. Surface and bulk leakage current calculation into the picoampere/femtoampere pore trace.
3. Guard efficiency / leakage attenuation factor comparison:
     - Unshielded configuration (supply rail -> pore node)
     - Driven guard ring configuration (supply rail -> driven guard -> pore node)
4. Weep moat / saline breach conductivity transition model (dry vs. 1M KCl).
"""

import math
from typing import Dict, Tuple, List


class GuardRingElectrostatics:
    def __init__(
        self,
        grid_width_mm: float = 10.0,
        grid_height_mm: float = 10.0,
        grid_step_mm: float = 0.1,
        substrate_rho_surface_dry: float = 1e14,  # ohms/square (Rogers RO4350B / PTFE)
        substrate_rho_surface_wet: float = 1e8,   # ohms/square (flux / moisture residue)
        electrolyte_conductivity_s_m: float = 10.5, # 1M KCl (~10.5 S/m)
    ):
        self.w = grid_width_mm
        self.h = grid_height_mm
        self.dx = grid_step_mm
        self.nx = int(round(self.w / self.dx)) + 1
        self.ny = int(round(self.h / self.dx)) + 1
        self.rho_surface_dry = substrate_rho_surface_dry
        self.rho_surface_wet = substrate_rho_surface_wet
        self.electrolyte_sigma = electrolyte_conductivity_s_m

    def solve_laplace_2d(
        self,
        core_pos: Tuple[float, float],
        core_radius: float,
        core_voltage: float,
        aggressor_pos: Tuple[float, float],
        aggressor_radius: float,
        aggressor_voltage: float,
        guard_enabled: bool = True,
        guard_radius_inner: float = 1.0,
        guard_radius_outer: float = 1.4,
        guard_voltage: float = 0.0,
        max_iter: int = 1500,
        tol: float = 1e-5,
    ) -> Tuple[List[List[float]], float]:
        """
        Solves Laplace's equation with Dirichlet boundary conditions on a 2D mesh.
        Returns: (potential_field, total_leakage_current_amperes)
        """
        nx, ny = self.nx, self.ny
        dx = self.dx

        # Initialize potential grid V and fixed boundary mask
        V = [[0.0 for _ in range(ny)] for _ in range(nx)]
        fixed = [[False for _ in range(ny)] for _ in range(nx)]

        cx, cy = core_pos
        ax, ay = aggressor_pos

        for i in range(nx):
            x = i * dx
            for j in range(ny):
                y = j * dx

                # Distance to core TIA pore node
                d_core = math.hypot(x - cx, y - cy)
                if d_core <= core_radius:
                    V[i][j] = core_voltage
                    fixed[i][j] = True
                    continue

                # Distance to driven guard ring collar
                if guard_enabled and (guard_radius_inner <= d_core <= guard_radius_outer):
                    V[i][j] = guard_voltage
                    fixed[i][j] = True
                    continue

                # Distance to aggressor supply rail
                d_agg = math.hypot(x - ax, y - ay)
                if d_agg <= aggressor_radius:
                    V[i][j] = aggressor_voltage
                    fixed[i][j] = True
                    continue

                # Far boundaries set to 0V (grounded chassis)
                if i == 0 or i == nx - 1 or j == 0 or j == ny - 1:
                    V[i][j] = 0.0
                    fixed[i][j] = True

        # Gauss-Seidel with Successive Over-Relaxation (SOR)
        omega = 1.75
        for it in range(max_iter):
            max_diff = 0.0
            for i in range(1, nx - 1):
                for j in range(1, ny - 1):
                    if fixed[i][j]:
                        continue
                    v_new = 0.25 * (V[i + 1][j] + V[i - 1][j] + V[i][j + 1] + V[i][j - 1])
                    diff = v_new - V[i][j]
                    V[i][j] += omega * diff
                    if abs(diff) > max_diff:
                        max_diff = abs(diff)

            if max_diff < tol:
                break

        # Calculate inward surface leakage current around the core node boundary
        # I_leak = integral (sigma_s * E_n) dl
        # E_n = -dV/dn
        leakage_current = 0.0
        boundary_pts = 0
        rho_s = self.rho_surface_dry

        for i in range(1, nx - 1):
            x = i * dx
            for j in range(1, ny - 1):
                y = j * dx
                d_core = math.hypot(x - cx, y - cy)
                # Just outside the core conductor
                if core_radius < d_core <= core_radius + dx:
                    # Estimate radial electric field Er = -(V(r) - V_core) / dr
                    grad_v = (V[i][j] - core_voltage) / dx
                    # Inward surface current segment: dI = (grad_v / rho_s) * segment_length
                    leakage_current += (grad_v / rho_s) * (2.0 * math.pi * core_radius / 16.0)
                    boundary_pts += 1

        return V, abs(leakage_current)

    def calculate_guard_attenuation(
        self,
        aggressor_voltage: float = 3.3,
        core_voltage: float = 0.0,
        core_radius: float = 0.4,
        guard_radius_inner: float = 0.8,
        guard_radius_outer: float = 1.3,
    ) -> Dict[str, float]:
        """
        Computes leakage current with and without driven guard ring to establish
        leakage suppression ratio.
        """
        core_pos = (5.0, 5.0)
        aggressor_pos = (5.0, 8.5) # 3.5 mm separation
        aggressor_radius = 0.5

        # 1. Unshielded
        _, i_unshielded = self.solve_laplace_2d(
            core_pos=core_pos,
            core_radius=core_radius,
            core_voltage=core_voltage,
            aggressor_pos=aggressor_pos,
            aggressor_radius=aggressor_radius,
            aggressor_voltage=aggressor_voltage,
            guard_enabled=False,
        )

        # 2. Guarded with driven guard (V_guard = core_voltage = 0V)
        _, i_guarded = self.solve_laplace_2d(
            core_pos=core_pos,
            core_radius=core_radius,
            core_voltage=core_voltage,
            aggressor_pos=aggressor_pos,
            aggressor_radius=aggressor_radius,
            aggressor_voltage=aggressor_voltage,
            guard_enabled=True,
            guard_radius_inner=guard_radius_inner,
            guard_radius_outer=guard_radius_outer,
            guard_voltage=core_voltage,
        )

        # Guard attenuation factor
        suppression_factor = (i_unshielded / max(i_guarded, 1e-20))
        suppression_db = 20.0 * math.log10(max(suppression_factor, 1.0))

        return {
            "i_unshielded_fa": i_unshielded * 1e15,
            "i_guarded_fa": i_guarded * 1e15,
            "suppression_ratio": suppression_factor,
            "suppression_db": suppression_db,
        }

    def simulate_weep_moat_breach(
        self,
        moat_gap_mm: float = 0.5,
        moat_perimeter_mm: float = 120.0,
        droplet_contact_width_mm: float = 2.0,
    ) -> Dict[str, float]:
        """
        Simulates impedance change across the dual-conductor weep moat
        when breached by 1M KCl buffer droplet (10.5 S/m).
        """
        # Dry state resistance across gap
        r_dry_ohms = self.rho_surface_dry * (moat_gap_mm / moat_perimeter_mm)

        # Wet state resistance through 1M KCl electrolyte film (assume film thickness 50 um)
        film_thickness_m = 50e-6
        gap_m = moat_gap_mm * 1e-3
        width_m = droplet_contact_width_mm * 1e-3
        # R = L / (sigma * A) = gap / (sigma * width * thickness)
        r_wet_ohms = gap_m / (self.electrolyte_sigma * width_m * film_thickness_m)

        # Detection signal current with 3.3V pull-up
        v_pullup = 3.3
        r_pullup = 10000.0 # 10k
        v_sense_dry = v_pullup * (r_dry_ohms / (r_dry_ohms + r_pullup))
        v_sense_wet = v_pullup * (r_wet_ohms / (r_wet_ohms + r_pullup))

        return {
            "r_dry_gigaohms": r_dry_ohms / 1e9,
            "r_wet_ohms": r_wet_ohms,
            "v_sense_dry_volts": v_sense_dry,
            "v_sense_wet_volts": v_sense_wet,
            "estop_tripped": v_sense_wet < 0.8, # TTL logic LOW (< 0.8V)
        }


if __name__ == "__main__":
    sim = GuardRingElectrostatics()
    print("=== Running Guard Ring Electrostatic Simulation ===")
    res = sim.calculate_guard_attenuation()
    print(f"Unshielded Core Leakage: {res['i_unshielded_fa']:.2f} fA")
    print(f"Guarded Core Leakage:    {res['i_guarded_fa']:.4f} fA")
    print(f"Guard Suppression Ratio: {res['suppression_ratio']:.1f}x ({res['suppression_db']:.1f} dB)")

    print("\n=== Simulating Weep Moat Electrolyte Breach ===")
    moat = sim.simulate_weep_moat_breach()
    print(f"Dry Moat Resistance:     {moat['r_dry_gigaohms']:.1f} Giga-Ohms (V_sense = {moat['v_sense_dry_volts']:.3f} V)")
    print(f"Wet Moat Resistance:     {moat['r_wet_ohms']:.2f} Ohms (V_sense = {moat['v_sense_wet_volts']:.4f} V)")
    print(f"Emergency Trip Triggered: {moat['estop_tripped']}")
