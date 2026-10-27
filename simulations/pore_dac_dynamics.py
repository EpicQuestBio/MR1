# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
pore_dac_dynamics.py
====================
Mathematical and Physical Simulation Model for MCP4822 Pore Bias DAC:
1. Analog Output Slew Rate & Full-Power Bandwidth (0.55 V/us)
2. Small-Signal Settling Time & Precision Resolving Rate (4.5 us -> 222 kSPS)
3. 20 MHz SPI Bus Transfer Timings & Theoretical Max Update Rate (800 ns transfer -> 1.17 MSPS)
4. Waveform Synthesis Frequency Limits by Sample Density
5. Capacitive Loading Limits (< 100 pF)
"""

import math
from typing import Dict, Any, List, Tuple


class PoreDacDynamics:
    """
    Physical dynamics and timing simulation for MCP4822 pore bias DAC on MR1 Nanopore reader.
    """

    # MCP4822 Datasheet Specifications (DS20002249B)
    SLEW_RATE_V_US = 0.55          # Typ. 0.55 V/us (Page 4)
    SETTLING_TIME_US = 4.5         # Typ. 4.5 us for 1/4 to 3/4 step to 0.5 LSb (Page 4)
    MAX_SPI_CLOCK_HZ = 20_000_000  # Max SPI clock 20 MHz (Page 6)
    FRAME_BITS = 16                # 16-bit SPI command word (Page 21)
    T_CSH_MIN_NS = 15.0            # CS high time >= 15 ns (Page 7)
    T_CSSR_NS = 40.0               # Setup / idle margin (Page 6)
    T_LDAC_PULSE_MIN_NS = 100.0    # LDAC pulse width if pulsed (Page 7)
    MAX_LOAD_CAPACITANCE_PF = 100.0# Max recommended capacitive load without buffer (Page 4)

    # Reference Voltages
    VREF_1X_V = 2.048              # 1x gain internal reference (0 to 2.048V)
    VREF_2X_V = 4.096              # 2x gain internal reference (0 to 4.096V)

    def calculate_analog_bandwidth(self, gain_2x: bool = False) -> Dict[str, float]:
        """
        Calculates large-signal full-power bandwidth and small-signal settling rate.

        Formula: f_max,full-power = SlewRate / (2 * pi * V_peak)
        - 1x Gain (0 to 2.048V, V_p = 1.024V): ~85.5 kHz
        - 2x Gain (0 to 4.096V, V_p = 2.048V): ~42.7 kHz
        - Small-signal fully resolved step rate: 1 / 4.5 us = 222.2 kSPS
        """
        v_span = self.VREF_2X_V if gain_2x else self.VREF_1X_V
        v_peak = v_span / 2.0  # Peak AC amplitude around midscale

        # Slew rate in V/s: 0.55 V/us = 0.55e6 V/s
        sr_v_s = self.SLEW_RATE_V_US * 1e6
        f_max_full_power_hz = sr_v_s / (2.0 * math.pi * v_peak)

        # Small-signal resolving rate (1 / 4.5 us)
        small_signal_sps = 1.0 / (self.SETTLING_TIME_US * 1e-6)

        return {
            "gain_mode": 2.0 if gain_2x else 1.0,
            "v_span_v": v_span,
            "v_peak_v": v_peak,
            "slew_rate_v_us": self.SLEW_RATE_V_US,
            "f_max_full_power_hz": f_max_full_power_hz,
            "f_max_full_power_khz": f_max_full_power_hz / 1000.0,
            "settling_time_us": self.SETTLING_TIME_US,
            "small_signal_max_sps": small_signal_sps,
            "small_signal_max_ksps": small_signal_sps / 1000.0,
        }

    def calculate_spi_timings(self, spi_clock_hz: float = 20_000_000.0, ldac_tied_low: bool = True) -> Dict[str, float]:
        """
        Calculates digital interface timing and theoretical maximum write rate.

        Frame transfer time = 16 bits / F_CLK
        At 20 MHz: t_frame = 800 ns
        With LDAC tied low:
          t_cycle = t_frame + t_CSH + t_CSSR = 800 ns + 15 ns + 40 ns = 855 ns
          Max rate = 1 / 855 ns = 1.169 MSPS
        With LDAC pulsed separately:
          t_cycle = 855 ns + t_LDAC (100 ns) + margin = ~1.0 - 1.2 us (~800 - 1000 kSPS)
        """
        t_clock_ns = 1e9 / spi_clock_hz
        t_frame_ns = self.FRAME_BITS * t_clock_ns

        t_overhead_ns = self.T_CSH_MIN_NS + self.T_CSSR_NS
        if not ldac_tied_low:
            t_overhead_ns += self.T_LDAC_PULSE_MIN_NS

        t_cycle_ns = t_frame_ns + t_overhead_ns
        max_theoretical_sps = 1e9 / t_cycle_ns

        # Realistic continuous MCU DMA / hardware SPI burst rate (~1.0 to 1.25 us/frame)
        realistic_mcu_sps = min(max_theoretical_sps, 1_000_000.0)

        # Dual channel sequential update rate (alternating Channel A and Channel B)
        dual_channel_sps = realistic_mcu_sps / 2.0

        return {
            "spi_clock_mhz": spi_clock_hz / 1e6,
            "t_frame_ns": t_frame_ns,
            "t_overhead_ns": t_overhead_ns,
            "t_cycle_ns": t_cycle_ns,
            "max_theoretical_sps": max_theoretical_sps,
            "max_theoretical_msps": max_theoretical_sps / 1e6,
            "realistic_mcu_sps": realistic_mcu_sps,
            "realistic_mcu_ksps": realistic_mcu_sps / 1000.0,
            "dual_channel_sps": dual_channel_sps,
            "dual_channel_ksps": dual_channel_sps / 1000.0,
            "ldac_tied_low": float(ldac_tied_low),
        }

    def calculate_waveform_limits(self, dac_update_rate_sps: float = 800_000.0, gain_2x: bool = False) -> List[Dict[str, Any]]:
        """
        Calculates maximum practical waveform frequencies by sample density,
        comparing analog slew rate limitations vs SPI throughput limitations.
        """
        analog = self.calculate_analog_bandwidth(gain_2x=gain_2x)
        f_slew_max = analog["f_max_full_power_hz"]

        waveforms = [
            {
                "name": "Square Wave (Full-Scale)",
                "samples_per_cycle": 2,
                "analog_limit_khz": f_slew_max / 1000.0,
                "spi_limit_khz": (dac_update_rate_sps / 2.0) / 1000.0,
                "quality_description": "2 samples/cycle; high frequencies suffer slew distortion",
            },
            {
                "name": "Nyquist / Minimal Stepped Wave",
                "samples_per_cycle": 4,
                "analog_limit_khz": min(f_slew_max, 50_000.0) / 1000.0,
                "spi_limit_khz": (dac_update_rate_sps / 4.0) / 1000.0,
                "quality_description": "4-8 samples/cycle minimal stepped reconstruction",
            },
            {
                "name": "Fair Reconstruction Sine / Triangle",
                "samples_per_cycle": 16,
                "analog_limit_khz": min(f_slew_max, (dac_update_rate_sps / 16.0)) / 1000.0,
                "spi_limit_khz": (dac_update_rate_sps / 16.0) / 1000.0,
                "quality_description": "16 samples/cycle; low harmonic distortion",
            },
            {
                "name": "Low-Distortion Pure Sine Wave",
                "samples_per_cycle": 32,
                "analog_limit_khz": min(f_slew_max, (dac_update_rate_sps / 32.0)) / 1000.0,
                "spi_limit_khz": (dac_update_rate_sps / 32.0) / 1000.0,
                "quality_description": "32 samples/cycle; ultra-low THD for AC impedance sweeps",
            },
        ]
        return waveforms

    def evaluate_capacitive_load(self, c_load_pf: float) -> Dict[str, Any]:
        """
        Evaluates whether trace and flowcell capacitive loading is within MCP4822 stability margins (< 100 pF).
        """
        is_safe = c_load_pf <= self.MAX_LOAD_CAPACITANCE_PF
        margin_pf = self.MAX_LOAD_CAPACITANCE_PF - c_load_pf
        return {
            "c_load_pf": c_load_pf,
            "max_allowed_pf": self.MAX_LOAD_CAPACITANCE_PF,
            "is_safe": is_safe,
            "margin_pf": margin_pf,
            "recommendation": "OK" if is_safe else "Exceeds 100 pF; add series isolation resistor or buffer op-amp",
        }

    def calculate_slew_limited_bandwidth(self, gain_2x: bool = False) -> Dict[str, float]:
        """Alias returning slew-limited bandwidth metrics matching test suite."""
        res = self.calculate_analog_bandwidth(gain_2x=gain_2x)
        return {
            "gain_2x": gain_2x,
            "v_full_scale_v": res["v_span_v"],
            "v_peak_v": res["v_peak_v"],
            "f_max_full_power_hz": res["f_max_full_power_hz"],
            "f_max_full_power_khz": res["f_max_full_power_khz"],
        }

    def calculate_settling_rate(self) -> Dict[str, float]:
        """Calculates precision settling rate to 0.5 LSb (4.5 us)."""
        res = self.calculate_analog_bandwidth()
        return {
            "settling_time_us": self.SETTLING_TIME_US,
            "max_resolved_sps": res["small_signal_max_sps"],
        }

    def calculate_spi_throughput(self, spi_clock_hz: float = 20_000_000.0) -> Dict[str, float]:
        """Calculates SPI throughput metrics matching test suite."""
        res = self.calculate_spi_timings(spi_clock_hz=spi_clock_hz, ldac_tied_low=True)
        return {
            "frame_transfer_ns": res["t_frame_ns"],
            "min_cycle_time_ns": res["t_cycle_ns"],
            "max_theoretical_sps": res["max_theoretical_sps"],
            "realistic_dma_sps": res["realistic_mcu_sps"],
        }

    def generate_waveform_table(self, dac_update_rate_sps: float = 800_000.0) -> List[Dict[str, Any]]:
        """Generates waveform reconstruction density across test frequencies."""
        test_freqs = [100.0, 500.0, 1000.0, 5000.0, 10000.0, 20000.0, 40000.0, 85000.0]
        f_slew_max = self.calculate_analog_bandwidth(gain_2x=False)["f_max_full_power_hz"]
        table = []
        for f in test_freqs:
            samples_per_cycle = dac_update_rate_sps / f
            analog_ok = f <= f_slew_max
            table.append({
                "frequency_hz": f,
                "samples_per_cycle": samples_per_cycle,
                "analog_ok": analog_ok,
            })
        return table

    def calculate_composite_bipolar_driver(
        self,
        code_a: int = 2048,
        code_b: int = 0,
        gain_2x: bool = False,
    ) -> Dict[str, Any]:
        """
        Models the MR1 Ignition schematic (`MR1/Ignition.kicad_sch`) composite bipolar summing
        amplifier (`U3A`/`U3B` OPA2197 + `U13` ADR4520 + `U9` MCP4822):
        - `U3B` (OPA2197) inverts `U13` (+2.048V) via R13=10k, R22=10k -> -2.048V
        - `U3A` (OPA2197) sums:
          * Ch A (coarse) via R31 = 10 kOhm into R29 = 24 kOhm (Gain = -2.40 V/V)
          * Ch B (100:1 vernier fine trim) via R21 = 1 MOhm into R29 = 24 kOhm (Gain = -0.024 V/V)
          * Offset (-2.048V from U3B) via R35 = 20 kOhm into R29 = 24 kOhm (Gain = -1.20 V/V -> +2.4576V)
        - Feedback compensation: C43 = 1 nF in parallel with R29 = 24 kOhm (f_-3dB = 6.631 kHz)
        - Output isolation filter: R43 = 27 Ohm + C29 = 100 nF (f_-3dB = 58.95 kHz)
        """
        r13, r22 = 10_000.0, 10_000.0
        r31, r21, r35, r29 = 10_000.0, 1_000_000.0, 20_000.0, 24_000.0
        c43 = 1.0e-9
        r43, c29 = 27.0, 100.0e-9
        v_ref = 2.048

        v_fs = self.VREF_2X_V if gain_2x else self.VREF_1X_V
        v_a = (max(0, min(4095, int(code_a))) / 4096.0) * v_fs
        v_b = (max(0, min(4095, int(code_b))) / 4096.0) * v_fs

        v_u3b = -(r22 / r13) * v_ref  # -2.048 V
        gain_a = -(r29 / r31)          # -2.40 V/V
        gain_b = -(r29 / r21)          # -0.024 V/V
        gain_off = -(r29 / r35)        # -1.20 V/V

        v_pore = (gain_off * v_u3b) + (gain_a * v_a) + (gain_b * v_b)
        f_3db_u3a_hz = 1.0 / (2.0 * math.pi * r29 * c43)
        f_3db_rc_out_hz = 1.0 / (2.0 * math.pi * r43 * c29)

        step_coarse_mv = abs(gain_a) * (v_fs / 4096.0) * 1e3
        step_fine_uv = abs(gain_b) * (v_fs / 4096.0) * 1e6

        return {
            "code_a": code_a,
            "code_b": code_b,
            "v_dac_a_v": v_a,
            "v_dac_b_v": v_b,
            "v_u3b_neg_ref_v": v_u3b,
            "v_pore_out_v": v_pore,
            "gain_coarse_a": gain_a,
            "gain_fine_b": gain_b,
            "vernier_ratio": abs(gain_a / gain_b),
            "step_coarse_mv": step_coarse_mv,
            "step_fine_uv": step_fine_uv,
            "f_3db_u3a_feedback_hz": f_3db_u3a_hz,
            "f_3db_output_rc_hz": f_3db_rc_out_hz,
        }


if __name__ == "__main__":
    sim = PoreDacDynamics()
    print("=== MCP4822 Analog Output Limits ===")
    bw_1x = sim.calculate_analog_bandwidth(gain_2x=False)
    print(f"1x Gain: Full-Power BW = {bw_1x['f_max_full_power_khz']:.2f} kHz, Small-Signal Resolving Rate = {bw_1x['small_signal_max_ksps']:.1f} kSPS")
    bw_2x = sim.calculate_analog_bandwidth(gain_2x=True)
    print(f"2x Gain: Full-Power BW = {bw_2x['f_max_full_power_khz']:.2f} kHz, Small-Signal Resolving Rate = {bw_2x['small_signal_max_ksps']:.1f} kSPS")

    print("\n=== MCP4822 Digital SPI Limits (20 MHz) ===")
    spi = sim.calculate_spi_timings(spi_clock_hz=20_000_000, ldac_tied_low=True)
    print(f"Frame Time: {spi['t_frame_ns']:.1f} ns, Min Cycle: {spi['t_cycle_ns']:.1f} ns")
    print(f"Theoretical Max: {spi['max_theoretical_msps']:.3f} MSPS ({spi['realistic_mcu_ksps']:.0f} kSPS realistic DMA)")
    print(f"Dual-Channel Alternate: {spi['dual_channel_ksps']:.0f} kSPS/channel")

    print("\n=== Waveform Synthesis Table (@ 800 kSPS) ===")
    for w in sim.calculate_waveform_limits(dac_update_rate_sps=800_000, gain_2x=False):
        print(f"{w['name']:35} : Analog Limit = {w['analog_limit_khz']:6.1f} kHz | SPI Limit = {w['spi_limit_khz']:6.1f} kHz")
