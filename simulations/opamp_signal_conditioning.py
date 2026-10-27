# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
opamp_signal_conditioning.py
============================
End-to-End Hardware Op-Amp Signal Conditioning Simulation for MR1 and Amplifier Boards:

1. MR1 Excitation Chain (`MR1/Ignition.kicad_sch` & `MR1/Power.kicad_sch`):
   - `U13` (`ADR4520`): +2.048V ultra-low-noise precision voltage reference
   - `U3B` (`OPA2197`): Unity-gain inverting reference buffer (`R13=10k`, `R22=10k`) -> -2.048V
   - `U3A` (`OPA2197`): Composite bipolar summing amplifier (`R31=10k` coarse DAC_A,
     `R21=1M` 100:1 vernier fine DAC_B, `R35=20k` bipolar offset, `R29=24k || C43=1nF` feedback)
   - Output RC isolation filter (`R43=27 Ohm`, `C29=100nF`) driving `/Ignition/>PORE`
   - Analog rails (`U4` `LT3045` +2.49V, `U2` `LT3094` -2.49V)

2. Amplifier Route 1 Femtoampere Chain (`Amplifier/Amplifier.kicad_sch`):
   - `U2` (`LMP7721`): Stage 1 TIA (`R1=1 GOhm || C1=2 pF`, `fc1 = 79.58 Hz`),
     passive guard `/GUARD` tied to `/Vbias` via `NT3`
   - `U16` (`LTC6268`): Stage 2 differential reference-cancelling post-gain & low-pass filter
     (`R8=100`, `R5=1k` on `+IN`; `R4=100` to `/Vbias`, `R3=1k || C9=100nF` feedback on `-IN`,
     `fc2 = 1.592 kHz`), yielding exact `/Vbias` cancellation and -10.0 GOhm effective transimpedance

3. Amplifier Route 2 Wideband Micropore Chain (`Amplifier/Amplifier.kicad_sch`):
   - `U5A` (`OPA2192IDR`): Wideband TIA (`R10=100 kOhm || C3=15 pF`, `fc = 106.10 kHz`, `R32=49.9 Ohm`)
   - `U5B` (`OPA2192IDR`): Unity-gain active guard buffer driving `/GUARD_WIDE`

4. Route Multiplexer, Fully Differential ADC Driver, and Anti-Aliasing Filter:
   - `U17` (`ADG1219BRMZ`): Low-capacitance SPDT route switch (`Ron=150 Ohm`, `I_leak=1 pA`)
   - `U6` (`ADA4940-1`): Fully differential ADC driver (`R43=R44=R45=R46=499 Ohm`)
   - Differential RC anti-aliasing filter (`R27=27 Ohm`, `R41=27 Ohm`, `C41=1nF`, `fc = 2.947 MHz`)
   - `U13` (`AD4000`): 16-bit 2 MSPS SAR ADC quantization model
"""

import cmath
import math
import sys
from pathlib import Path
from typing import Dict, Any, List

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class OpAmpSignalConditioningSimulation:
    """
    Exact schematic-matched simulation of the multi-stage operational amplifier
    signal conditioning chains on the MR1 and Amplifier boards.
    """

    # Physical constants
    K_BOLTZMANN = 1.380649e-23
    Q_ELECTRON = 1.602176634e-19

    # --- MR1 Excitation Chain Component Values (MR1/Ignition.kicad_sch) ---
    V_REF_ADR4520 = 2.048       # U13 ADR4520 reference voltage (V)
    R13_INV_IN = 10_000.0       # U3B inverting input resistor (Ohm)
    R22_INV_FB = 10_000.0       # U3B inverting feedback resistor (Ohm)
    R42_INV_OUT = 27.0          # U3B output isolation resistor (Ohm)

    R31_DAC_A = 10_000.0        # U3A coarse DAC Ch A summing resistor (Ohm)
    R21_DAC_B = 1_000_000.0     # U3A fine vernier DAC Ch B summing resistor (Ohm)
    R35_OFFSET = 20_000.0       # U3A bipolar offset summing resistor from U3B (Ohm)
    R29_SUM_FB = 24_000.0       # U3A feedback resistor (Ohm)
    C43_SUM_FB = 1.0e-9         # U3A feedback compensation capacitor (F)
    R43_PORE_OUT = 27.0         # U3A output series isolation resistor (Ohm)
    C29_PORE_OUT = 100.0e-9     # U3A output shunt filter capacitor to GNDA (F)
    OPA2197_GBW_HZ = 10.0e6     # U3 (OPA2197) Gain-Bandwidth Product (Hz)

    # Analog Supply Rails (MR1/Power.kicad_sch: U4 LT3045 / U2 LT3094 with R_set = 24.9k)
    VDDA_RAIL_V = 2.49          # +100 uA * 24.9 kOhm = +2.49V
    VSSA_RAIL_V = -2.49         # -100 uA * 24.9 kOhm = -2.49V

    # --- Amplifier Route 1 Component Values (Amplifier/Amplifier.kicad_sch) ---
    R1_TIA1_FB = 1.0e9          # U2 (LMP7721) feedback resistor (1 GOhm)
    C1_TIA1_FB = 2.0e-12        # U2 feedback capacitor (2 pF)
    LMP7721_GBW_HZ = 17.0e6     # U2 (LMP7721) Gain-Bandwidth Product (Hz)
    LMP7721_EN_V_RTHZ = 6.5e-9  # U2 input voltage noise density at 1 kHz (V/rtHz)
    LMP7721_IB_A = 3.0e-15      # U2 typical input bias current at 25C (3 fA)

    R8_POST_DIV_TOP = 100.0     # U16 (LTC6268) +IN series resistor from U2 out (Ohm)
    R5_POST_DIV_BOT = 1_000.0   # U16 +IN shunt resistor to GNDA (Ohm)
    R4_POST_BIAS_IN = 100.0     # U16 -IN resistor to /Vbias (Ohm)
    R3_POST_FB = 1_000.0        # U16 feedback resistor (Ohm)
    C9_POST_FB = 100.0e-9       # U16 feedback capacitor (100 nF)
    LTC6268_GBW_HZ = 500.0e6    # U16 (LTC6268) Gain-Bandwidth Product (Hz)

    # --- Amplifier Route 2 Component Values (Amplifier/Amplifier.kicad_sch) ---
    R10_TIA2_FB = 100_000.0     # U5A (OPA2192) feedback resistor (100 kOhm)
    C3_TIA2_FB = 15.0e-12       # U5A feedback capacitor (15 pF)
    R32_TIA2_OUT = 49.9         # U5A series output isolation resistor (Ohm)
    OPA2192_GBW_HZ = 10.0e6     # U5 (OPA2192) Gain-Bandwidth Product (Hz)
    OPA2192_ROUT_OL_OHM = 30.0  # U5 open-loop output resistance (Ohm)
    OPA2192_AOL_DC = 3.162e6    # U5 DC open-loop gain (130 dB)

    # --- Multiplexer, Differential ADC Driver, and Anti-Aliasing Filter ---
    ADG1219_RON_OHM = 150.0     # U17 (ADG1219BRMZ) typical on-resistance (Ohm)
    ADG1219_ILEAK_A = 1.0e-12   # U17 typical off/on leakage current (1 pA)
    ADG1219_CD_F = 2.6e-12      # U17 drain capacitance (2.6 pF)

    R45_FDA_IN_P = 499.0        # U6 (ADA4940-1) input resistor from Signal_Return (Ohm)
    R43_FDA_IN_N = 499.0        # U6 input resistor from GNDA (Ohm)
    R46_FDA_FB_1 = 499.0        # U6 feedback resistor 1 (Ohm)
    R44_FDA_FB_2 = 499.0        # U6 feedback resistor 2 (Ohm)
    R27_AA_FILT_P = 27.0        # U6 +OUT series filter resistor to AD4000 IN+ (Ohm)
    R41_AA_FILT_N = 27.0        # U6 -OUT series filter resistor to AD4000 IN- (Ohm)
    C41_AA_DIFF = 1.0e-9        # Differential anti-aliasing capacitor across IN+/IN- (F)
    AD4000_BITS = 16            # U13 (AD4000) resolution (bits)
    AD4000_VREF_V = 2.048       # Standard reference span for ADC differential calculation (V)

    def __init__(self, temperature_c: float = 25.0):
        self.temperature_c = temperature_c
        self.temperature_k = temperature_c + 273.15

    # =========================================================================
    # 1. MR1 Excitation Chain (U13 ADR4520 + U3B/U3A OPA2197 + U9 MCP4822)
    # =========================================================================

    def calculate_excitation_voltage(
        self,
        code_a: int = 2048,
        code_b: int = 0,
        gain_2x_a: bool = False,
        gain_2x_b: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculates the exact DC output of the MR1 composite bipolar excitation chain
        (U13 ADR4520 + U9 MCP4822 + U3B OPA2197 Inverter + U3A OPA2197 Summing Amplifier):
            V_U3B = -(R22 / R13) * V_REF = -2.048 V
            V_PORE = -(R29 / R31)*V_A - (R29 / R21)*V_B - (R29 / R35)*V_U3B
                   = +2.4576 V - 2.40 * V_A - 0.024 * V_B
        """
        code_a_clamped = max(0, min(4095, int(code_a)))
        code_b_clamped = max(0, min(4095, int(code_b)))

        v_fs_a = 4.096 if gain_2x_a else 2.048
        v_fs_b = 4.096 if gain_2x_b else 2.048

        v_dac_a = (code_a_clamped / 4096.0) * v_fs_a
        v_dac_b = (code_b_clamped / 4096.0) * v_fs_b

        # U3B Reference Inverter
        gain_u3b = -self.R22_INV_FB / self.R13_INV_IN
        v_u3b_out = gain_u3b * self.V_REF_ADR4520  # -2.048 V

        # U3A Summing Gains
        gain_coarse_a = -self.R29_SUM_FB / self.R31_DAC_A   # -2.40 V/V
        gain_fine_b = -self.R29_SUM_FB / self.R21_DAC_B     # -0.024 V/V
        gain_offset = -self.R29_SUM_FB / self.R35_OFFSET    # -1.20 V/V

        v_offset_contribution = gain_offset * v_u3b_out     # +2.4576 V
        v_pore_ideal = (
            v_offset_contribution
            + (gain_coarse_a * v_dac_a)
            + (gain_fine_b * v_dac_b)
        )

        # Rail clamping check against LT3045 (+2.49V) / LT3094 (-2.49V)
        v_pore_clamped = max(self.VSSA_RAIL_V, min(self.VDDA_RAIL_V, v_pore_ideal))
        is_rail_saturated = abs(v_pore_ideal - v_pore_clamped) > 1e-6

        # Step sizes and effective composite resolution
        lsb_dac_a_v = v_fs_a / 4096.0
        lsb_dac_b_v = v_fs_b / 4096.0
        step_coarse_mv = abs(gain_coarse_a * lsb_dac_a_v) * 1e3      # 1.20 mV/LSB (1x)
        step_fine_uv = abs(gain_fine_b * lsb_dac_b_v) * 1e6          # 12.0 uV/LSB (1x)
        vernier_ratio = abs(gain_coarse_a / gain_fine_b)             # 100.0

        total_span_v = abs(gain_coarse_a * v_fs_a) + abs(gain_fine_b * v_fs_b)
        effective_steps = total_span_v / (abs(gain_fine_b) * lsb_dac_b_v)
        effective_bits = math.log2(effective_steps)

        return {
            "code_a": code_a_clamped,
            "code_b": code_b_clamped,
            "v_dac_a_v": v_dac_a,
            "v_dac_b_v": v_dac_b,
            "v_u3b_ref_neg_v": v_u3b_out,
            "gain_coarse_a_v_v": gain_coarse_a,
            "gain_fine_b_v_v": gain_fine_b,
            "gain_offset_v_v": gain_offset,
            "v_offset_contribution_v": v_offset_contribution,
            "v_pore_ideal_v": v_pore_ideal,
            "v_pore_out_v": v_pore_clamped,
            "is_rail_saturated": is_rail_saturated,
            "step_coarse_mv": step_coarse_mv,
            "step_fine_uv": step_fine_uv,
            "vernier_ratio": vernier_ratio,
            "effective_resolution_bits": effective_bits,
        }

    def excitation_frequency_response(self, freq_hz: float) -> Dict[str, float]:
        """
        Calculates the AC frequency response of the MR1 >PORE excitation chain from DAC_A
        to the flowcell electrode (`U3A` feedback pole R29||C43 + `OPA2197` GBW + output R43/C29 filter).
        """
        s = 2.0j * math.pi * max(freq_hz, 0.0)

        # U3A feedback impedance Z_fb(s) = R29 / (1 + s * R29 * C43)
        z_fb = self.R29_SUM_FB / (1.0 + s * self.R29_SUM_FB * self.C43_SUM_FB)
        h_u3a_ideal = -z_fb / self.R31_DAC_A

        # Finite GBW of U3A (OPA2197, 10 MHz) with noise gain NG ~ 1 + R29/R31 + R29/R35 = 4.6
        noise_gain_dc = 1.0 + (self.R29_SUM_FB / self.R31_DAC_A) + (self.R29_SUM_FB / self.R35_OFFSET)
        f_opamp_pole = self.OPA2197_GBW_HZ / noise_gain_dc
        h_opamp = 1.0 / (1.0 + (s / (2.0 * math.pi * f_opamp_pole)))

        # Output passive isolation filter R43 (27 Ohm) + C29 (100 nF)
        h_rc_out = 1.0 / (1.0 + s * self.R43_PORE_OUT * self.C29_PORE_OUT)

        h_total = h_u3a_ideal * h_opamp * h_rc_out
        mag = abs(h_total)
        mag_dc = self.R29_SUM_FB / self.R31_DAC_A  # 2.40 V/V
        gain_db = 20.0 * math.log10(max(mag, 1e-18))
        rel_db = 20.0 * math.log10(max(mag / mag_dc, 1e-18))
        phase_deg = math.degrees(cmath.phase(h_total))

        f_3db_fb_hz = 1.0 / (2.0 * math.pi * self.R29_SUM_FB * self.C43_SUM_FB)
        f_3db_rc_hz = 1.0 / (2.0 * math.pi * self.R43_PORE_OUT * self.C29_PORE_OUT)

        return {
            "frequency_hz": freq_hz,
            "gain_v_v": mag,
            "gain_db": gain_db,
            "relative_db": rel_db,
            "phase_deg": phase_deg,
            "f_3db_feedback_hz": f_3db_fb_hz,
            "f_3db_output_rc_hz": f_3db_rc_hz,
        }

    # =========================================================================
    # 2. Amplifier Route 1 Chain (U2 LMP7721 TIA + U16 LTC6268 Post-Gain)
    # =========================================================================

    def calculate_route1_dc_transfer(
        self,
        i_pore_a: float,
        v_bias_v: float = 0.0,
        r8_ohm: float = None,
        r5_ohm: float = None,
        r4_ohm: float = None,
        r3_ohm: float = None,
    ) -> Dict[str, float]:
        """
        Calculates the exact DC transfer across Route 1 (`U2` LMP7721 + `U16` LTC6268):
          Stage 1 (U2):
            V_U2 = V_bias - I_pore * R1
          Stage 2 (U16):
            V_+ = V_U2 * (R5 / (R8 + R5))
            V_Route1_OUT = (1 + R3 / R4) * V_+ - (R3 / R4) * V_bias
        When R8=100, R5=1000, R4=100, R3=1000:
            V_+ = (10 / 11) * V_U2
            V_Route1_OUT = 11 * (10 / 11) * (V_bias - I_pore * R1) - 10 * V_bias
                         = -10.0 * I_pore * R1
        """
        r8 = self.R8_POST_DIV_TOP if r8_ohm is None else r8_ohm
        r5 = self.R5_POST_DIV_BOT if r5_ohm is None else r5_ohm
        r4 = self.R4_POST_BIAS_IN if r4_ohm is None else r4_ohm
        r3 = self.R3_POST_FB if r3_ohm is None else r3_ohm

        # Stage 1: U2 LMP7721
        v_u2_out = v_bias_v - (i_pore_a * self.R1_TIA1_FB)

        # Stage 2: U16 LTC6268 non-inverting divider and differential reference subtraction
        div_ratio_plus = r5 / (r8 + r5)               # 1000 / 1100 = 10/11
        non_inv_gain = 1.0 + (r3 / r4)                # 1 + 1000/100 = 11.0
        inv_bias_gain = r3 / r4                       # 1000/100 = 10.0

        effective_stage2_signal_gain = non_inv_gain * div_ratio_plus  # 11 * (10/11) = 10.0
        common_mode_vbias_gain = effective_stage2_signal_gain - inv_bias_gain  # 10.0 - 10.0 = 0.0

        v_u16_plus = v_u2_out * div_ratio_plus
        v_route1_out = (non_inv_gain * v_u16_plus) - (inv_bias_gain * v_bias_v)
        effective_transimpedance_ohm = -self.R1_TIA1_FB * effective_stage2_signal_gain

        return {
            "i_pore_a": i_pore_a,
            "i_pore_pa": i_pore_a * 1e12,
            "v_bias_v": v_bias_v,
            "v_u2_tia_out_v": v_u2_out,
            "v_u16_plus_in_v": v_u16_plus,
            "v_route1_out_v": v_route1_out,
            "stage1_transimpedance_ohm": -self.R1_TIA1_FB,
            "stage2_non_inv_gain": non_inv_gain,
            "stage2_input_divider": div_ratio_plus,
            "stage2_effective_gain_v_v": effective_stage2_signal_gain,
            "common_mode_vbias_leakage_v_v": common_mode_vbias_gain,
            "total_transimpedance_ohm": effective_transimpedance_ohm,
            "total_transimpedance_gohm": effective_transimpedance_ohm / 1e9,
        }

    def route1_frequency_response(self, freq_hz: float) -> Dict[str, float]:
        """
        Calculates the cascaded AC transimpedance response of Route 1 (`U2` LMP7721 + `U16` LTC6268):
          - Stage 1 pole: R1 (1 GOhm) || C1 (2 pF) -> fc1 = 79.58 Hz
          - Stage 2 pole: R3 (1 kOhm) || C9 (100 nF) -> fc2 = 1591.55 Hz
        """
        s = 2.0j * math.pi * max(freq_hz, 0.0)

        # Stage 1: Z_f1(s) = -R1 / (1 + s * R1 * C1)
        z_f1 = -self.R1_TIA1_FB / (1.0 + s * self.R1_TIA1_FB * self.C1_TIA1_FB)

        # Stage 2: Z_3(s) = R3 / (1 + s * R3 * C9)
        # Signal path from U2 out to U16 out: H2(s) = (R5 / (R8 + R5)) * (1 + Z_3(s) / R4)
        z_3 = self.R3_POST_FB / (1.0 + s * self.R3_POST_FB * self.C9_POST_FB)
        div_plus = self.R5_POST_DIV_BOT / (self.R8_POST_DIV_TOP + self.R5_POST_DIV_BOT)
        h_stage2 = div_plus * (1.0 + (z_3 / self.R4_POST_BIAS_IN))

        z_total = z_f1 * h_stage2
        mag_ohm = abs(z_total)
        dc_ohm = self.R1_TIA1_FB * 10.0  # 10 GOhm
        rel_db = 20.0 * math.log10(max(mag_ohm / dc_ohm, 1e-18))

        fc1_hz = 1.0 / (2.0 * math.pi * self.R1_TIA1_FB * self.C1_TIA1_FB)
        fc2_hz = 1.0 / (2.0 * math.pi * self.R3_POST_FB * self.C9_POST_FB)

        return {
            "frequency_hz": freq_hz,
            "transimpedance_mag_ohm": mag_ohm,
            "transimpedance_mag_gohm": mag_ohm / 1e9,
            "stage1_mag_gohm": abs(z_f1) / 1e9,
            "stage2_gain_mag": abs(h_stage2),
            "relative_db": rel_db,
            "phase_deg": math.degrees(cmath.phase(z_total)),
            "f_3db_stage1_hz": fc1_hz,
            "f_3db_stage2_hz": fc2_hz,
        }

    def calculate_route1_noise_psd(
        self,
        freq_hz: float = 100.0,
        c_in_pf: float = 15.0,
        bw_brickwall_hz: float = 79.58,
    ) -> Dict[str, float]:
        """
        Calculates the input-referred current noise spectral density and integrated RMS current noise
        of the Route 1 `U2` (`LMP7721`) femtoampere TIA front-end:
          i_n^2(f) = 2*q*I_b + 4*k_B*T/R1 + e_n^2 * (1/R1^2 + (2*pi*f*(C_in + C1))^2)
        """
        c_tot_f = (c_in_pf * 1e-12) + self.C1_TIA1_FB

        # 1. Shot noise from 3 fA input bias current: 2 * q * I_b
        i_shot_sq = 2.0 * self.Q_ELECTRON * self.LMP7721_IB_A
        # 2. Johnson-Nyquist thermal noise of 1 GOhm feedback resistor: 4 * k_B * T / R1
        i_thermal_sq = (4.0 * self.K_BOLTZMANN * self.temperature_k) / self.R1_TIA1_FB
        # 3. Voltage noise (e_n * |Y_in + Y_f|) -> e_n^2 * (1/R1^2 + (2*pi*f*C_tot)^2)
        omega = 2.0 * math.pi * max(freq_hz, 0.0)
        i_en_sq = (self.LMP7721_EN_V_RTHZ ** 2) * (
            (1.0 / (self.R1_TIA1_FB ** 2)) + ((omega * c_tot_f) ** 2)
        )

        i_total_sq = i_shot_sq + i_thermal_sq + i_en_sq
        i_total_fa_rthz = math.sqrt(i_total_sq) * 1e15

        # Integrated RMS noise over brickwall bandwidth [0, B]:
        # int_0^B [i_white^2 + (2*pi*C_tot*e_n)^2 * f^2] df = i_white^2 * B + (2*pi*C_tot*e_n)^2 * B^3 / 3
        b_hz = max(bw_brickwall_hz, 1.0)
        i_white_sq = i_shot_sq + i_thermal_sq + ((self.LMP7721_EN_V_RTHZ / self.R1_TIA1_FB) ** 2)
        c_noise_coeff_sq = (2.0 * math.pi * c_tot_f * self.LMP7721_EN_V_RTHZ) ** 2
        i_rms_a = math.sqrt((i_white_sq * b_hz) + (c_noise_coeff_sq * (b_hz ** 3) / 3.0))

        return {
            "frequency_hz": freq_hz,
            "c_in_pf": c_in_pf,
            "i_shot_fa_rthz": math.sqrt(i_shot_sq) * 1e15,
            "i_thermal_r1_fa_rthz": math.sqrt(i_thermal_sq) * 1e15,
            "i_en_capacitive_fa_rthz": math.sqrt(i_en_sq) * 1e15,
            "i_total_fa_rthz": i_total_fa_rthz,
            "integrated_bw_hz": b_hz,
            "i_rms_fa": i_rms_a * 1e15,
            "i_rms_pa": i_rms_a * 1e12,
        }

    # =========================================================================
    # 3. Amplifier Route 2 Chain (U5A Wideband TIA + U5B Active Guard Buffer)
    # =========================================================================

    def route2_frequency_response(self, freq_hz: float) -> Dict[str, float]:
        """
        Calculates the AC transimpedance response of Route 2 (`U5A` OPA2192):
          R10 = 100 kOhm || C3 = 15 pF -> f_-3dB = 106.103 kHz
        """
        s = 2.0j * math.pi * max(freq_hz, 0.0)
        z_f2 = -self.R10_TIA2_FB / (1.0 + s * self.R10_TIA2_FB * self.C3_TIA2_FB)

        # Finite GBW of OPA2192 (10 MHz)
        f_opamp = self.OPA2192_GBW_HZ
        h_opamp = 1.0 / (1.0 + (s / (2.0 * math.pi * f_opamp)))

        z_total = z_f2 * h_opamp
        mag_ohm = abs(z_total)
        rel_db = 20.0 * math.log10(max(mag_ohm / self.R10_TIA2_FB, 1e-18))
        fc_hz = 1.0 / (2.0 * math.pi * self.R10_TIA2_FB * self.C3_TIA2_FB)

        return {
            "frequency_hz": freq_hz,
            "transimpedance_mag_ohm": mag_ohm,
            "transimpedance_mag_kohm": mag_ohm / 1e3,
            "relative_db": rel_db,
            "phase_deg": math.degrees(cmath.phase(z_total)),
            "f_3db_hz": fc_hz,
            "f_3db_khz": fc_hz / 1e3,
        }

    def compare_passive_vs_active_guard(
        self,
        freq_hz: float = 10_000.0,
        r_vbias_source_ohm: float = 200.0,
        c_aggressor_to_guard_pf: float = 5.0,
        v_aggressor_ac_v: float = 1.0,
    ) -> Dict[str, float]:
        """
        Compares Route 1 Passive Guard (`NT3` tying `/GUARD` to `/Vbias`) vs
        Route 2 Active Guard (`U5B` OPA2192 unity-gain buffer driving `/GUARD_WIDE`):
        - Passive guard impedance equals the `/Vbias` source impedance `r_vbias_source_ohm`,
          producing zero active op-amp voltage noise injection at DC/low-f (ideal for Route 1 < 80 Hz).
        - Active guard (`U5B` OPA2192) reduces output impedance by (1 + A_OL(f)), suppressing
          high-frequency capacitive displacement crosstalk on `/GUARD_WIDE` across 1-100 kHz.
        """
        omega = 2.0 * math.pi * max(freq_hz, 1e-3)
        c_agg_f = c_aggressor_to_guard_pf * 1e-12

        # Dominant pole of OPA2192 open-loop response: f_dom = GBW / A_OL_DC
        f_dom = self.OPA2192_GBW_HZ / self.OPA2192_AOL_DC
        a_ol = self.OPA2192_AOL_DC / (1.0 + 1.0j * (freq_hz / f_dom))

        # Closed-loop output impedance of U5B unity-gain follower
        z_out_active = self.OPA2192_ROUT_OL_OHM / (1.0 + a_ol)
        z_out_active_mag = abs(z_out_active)
        z_out_passive_mag = r_vbias_source_ohm

        # Induced AC voltage ripple on guard ring from capacitive aggressor C_agg
        z_c_agg = 1.0 / (1.0j * omega * c_agg_f)
        v_ripple_passive = abs(v_aggressor_ac_v * (z_out_passive_mag / (z_out_passive_mag + z_c_agg)))
        v_ripple_active = abs(v_aggressor_ac_v * (z_out_active / (z_out_active + z_c_agg)))

        suppression_improvement_db = 20.0 * math.log10(
            max(v_ripple_passive / max(v_ripple_active, 1e-18), 1e-18)
        )

        return {
            "frequency_hz": freq_hz,
            "z_guard_passive_ohm": z_out_passive_mag,
            "z_guard_active_ohm": z_out_active_mag,
            "v_ripple_passive_v": v_ripple_passive,
            "v_ripple_active_v": v_ripple_active,
            "active_suppression_improvement_db": suppression_improvement_db,
        }

    # =========================================================================
    # 4. Full End-to-End Readout Chain (U17 ADG1219 + U6 ADA4940-1 + U13 AD4000)
    # =========================================================================

    def simulate_full_readout_chain(
        self,
        i_pore_a: float,
        route_sel: int = 0,
        v_bias_v: float = 0.0,
        freq_hz: float = 0.0,
        v_ocm_v: float = 1.024,
    ) -> Dict[str, Any]:
        """
        Simulates the complete signal chain from pore current `i_pore_a` through:
          - Route 1 (`route_sel=0`: `U2` LMP7721 + `U16` LTC6268) OR
            Route 2 (`route_sel=1`: `U5A` OPA2192 + `R32` 49.9 Ohm)
          - `U17` (`ADG1219BRMZ` SPDT mux, `Ron = 150 Ohm`)
          - `U6` (`ADA4940-1` fully differential ADC driver, `R43=R44=R45=R46=499 Ohm`)
          - Anti-aliasing filter (`R27=27 Ohm`, `R41=27 Ohm`, `C41=1 nF`, `fc = 2.947 MHz`)
          - `U13` (`AD4000` 16-bit SAR ADC)
        """
        if route_sel == 0:
            r1_dc = self.calculate_route1_dc_transfer(i_pore_a=i_pore_a, v_bias_v=v_bias_v)
            r1_ac = self.route1_frequency_response(freq_hz=freq_hz)
            v_mux_in = r1_dc["v_route1_out_v"] * (
                r1_ac["transimpedance_mag_ohm"] / abs(r1_dc["total_transimpedance_ohm"])
            )
            r_source_series = 0.0  # U16 output drives U17 SA directly
        else:
            r2_ac = self.route2_frequency_response(freq_hz=freq_hz)
            v_dc_r2 = v_bias_v - (i_pore_a * self.R10_TIA2_FB)
            ac_scale = r2_ac["transimpedance_mag_ohm"] / self.R10_TIA2_FB
            v_mux_in = v_bias_v - (i_pore_a * self.R10_TIA2_FB * ac_scale)
            r_source_series = self.R32_TIA2_OUT  # R32 = 49.9 Ohm in series with Route2_OUT

        # U17 ADG1219BRMZ Multiplexer + U6 ADA4940-1 Fully Differential Driver
        # Ideal gain when driven by zero-impedance source: G_diff = -R46 / R45 = -1.0
        gain_fda_ideal = -self.R46_FDA_FB_1 / self.R45_FDA_IN_P

        # Actual effective input resistance on +IN branch includes U17 Ron (150 Ohm) + R_source_series
        r_in_p_eff = self.R45_FDA_IN_P + self.ADG1219_RON_OHM + r_source_series
        # For a single-ended-to-differential FDA with feedback R46=R44 and reference branch R43:
        gain_fda_actual = -self.R46_FDA_FB_1 / r_in_p_eff
        mux_attenuation_factor = abs(gain_fda_actual / gain_fda_ideal)

        # Anti-aliasing filter (R27 = 27 Ohm, R41 = 27 Ohm, C41 = 1 nF differential)
        r_aa_total = self.R27_AA_FILT_P + self.R41_AA_FILT_N
        f_3db_aa_hz = 1.0 / (2.0 * math.pi * r_aa_total * self.C41_AA_DIFF)
        s = 2.0j * math.pi * max(freq_hz, 0.0)
        h_aa_mag = abs(1.0 / (1.0 + s * r_aa_total * self.C41_AA_DIFF))

        v_diff_ideal = v_mux_in * gain_fda_ideal * h_aa_mag
        v_diff_actual = v_mux_in * gain_fda_actual * h_aa_mag

        v_adc_in_p = v_ocm_v + (0.5 * v_diff_actual)
        v_adc_in_n = v_ocm_v - (0.5 * v_diff_actual)

        # 16-bit two's complement quantization across [-VREF, +VREF] differential span
        full_scale_diff = self.AD4000_VREF_V
        normalized = max(-1.0, min(0.999969, v_diff_actual / full_scale_diff))
        adc_signed_code = int(round(normalized * 32768.0))
        adc_signed_code = max(-32768, min(32767, adc_signed_code))

        return {
            "route_sel": route_sel,
            "route_name": "Route 1 (Sub-5nm LMP7721 + LTC6268)" if route_sel == 0 else "Route 2 (Wideband OPA2192)",
            "i_pore_a": i_pore_a,
            "v_bias_v": v_bias_v,
            "frequency_hz": freq_hz,
            "v_mux_in_v": v_mux_in,
            "r_in_fda_effective_ohm": r_in_p_eff,
            "gain_fda_ideal_v_v": gain_fda_ideal,
            "gain_fda_actual_v_v": gain_fda_actual,
            "mux_ron_attenuation_factor": mux_attenuation_factor,
            "f_3db_antialiasing_hz": f_3db_aa_hz,
            "antialiasing_mag": h_aa_mag,
            "v_diff_adc_ideal_v": v_diff_ideal,
            "v_diff_adc_actual_v": v_diff_actual,
            "v_adc_in_p_v": v_adc_in_p,
            "v_adc_in_n_v": v_adc_in_n,
            "adc_signed_code_16bit": adc_signed_code,
        }

    # =========================================================================
    # 5. V_PORE & Dual-Route TIA Balancing Across 5 nm - 200 um & All Liquids
    # =========================================================================

    def solve_dac_codes_for_vpore(self, target_vpore_v: float) -> Dict[str, Any]:
        """
        Solves for the exact 12-bit coarse (code_a) and 100:1 vernier fine (code_b)
        MCP4822 register codes to synthesize `target_vpore_v` on `/Ignition/>PORE`:
            V_PORE(code_a, code_b) = +2.4576 V - 0.0012 * code_a - 0.000012 * code_b
        """
        v_clamped = max(self.VSSA_RAIL_V, min(2.4576, target_vpore_v))
        delta_v = max(0.0, 2.4576 - v_clamped)

        # Coarse step = 1.20 mV, Fine step = 12.0 uV
        code_a = min(4095, int(math.floor(delta_v / 0.0012 + 1e-9)))
        residual_v = max(0.0, delta_v - (code_a * 0.0012))
        code_b = min(4095, int(round(residual_v / 0.000012)))

        # Re-evaluate via exact circuit model
        exc = self.calculate_excitation_voltage(code_a=code_a, code_b=code_b)
        quantization_error_uv = (exc["v_pore_out_v"] - v_clamped) * 1e6

        return {
            "target_vpore_v": target_vpore_v,
            "achievable_vpore_v": exc["v_pore_out_v"],
            "quantization_error_uv": quantization_error_uv,
            "code_a": exc["code_a"],
            "code_b": exc["code_b"],
            "v_dac_a_v": exc["v_dac_a_v"],
            "v_dac_b_v": exc["v_dac_b_v"],
        }

    def balance_vpore_and_dual_tia(
        self,
        pore_diameter_nm: float,
        membrane_thickness_nm: float,
        liquid_conductivity_s_m: float,
        surface_charge_c_m2: float = 0.0,
        target_output_v: float = 1.20,
    ) -> Dict[str, Any]:
        """
        Evaluates whether V_PORE and the dual TIA ranges (Route 1: -10 GOhm vs Route 2: -100 kOhm)
        can be balanced to achieve linear, unsaturated, high-SNR sensing for any pore diameter
        (5 nm to 200 um) and liquid conductivity (20 S/m hypertonic ionic down to 5.5e-6 S/m DI/non-ionic).
        """
        from simulations.nanopore_electrokinetics import NanoporeElectrokinetics

        ek = NanoporeElectrokinetics(
            pore_diameter_nm=pore_diameter_nm,
            membrane_thickness_nm=membrane_thickness_nm,
            electrolyte_conductivity_s_m=liquid_conductivity_s_m,
            surface_charge_c_m2=surface_charge_c_m2,
        )
        res = ek.calculate_pore_resistance()
        r_pore_ohm = res["r_total_mohm"] * 1e6

        # Route 1 (-10.0 GOhm effective transimpedance, linear full-scale I_max = 204.8 pA)
        zt_route1_ohm = self.R1_TIA1_FB * 10.0  # 10.0 GOhm
        i_max_route1_a = 2.048 / zt_route1_ohm  # 204.8 pA
        i_target_route1_a = target_output_v / zt_route1_ohm  # 120.0 pA for 1.20 V output

        # Route 2 (-100.0 kOhm transimpedance, linear full-scale I_max = 20.48 uA)
        zt_route2_ohm = self.R10_TIA2_FB         # 100.0 kOhm
        i_max_route2_a = 2.048 / zt_route2_ohm  # 20.48 uA
        i_target_route2_a = target_output_v / zt_route2_ohm  # 12.0 uA for 1.20 V output

        # Ideal V_PORE required on Route 1 vs Route 2 to hit target_output_v (1.20V)
        vpore_ideal_r1 = i_target_route1_a * r_pore_ohm
        vpore_ideal_r2 = i_target_route2_a * r_pore_ohm

        # Select optimal route:
        # Use Route 1 when required V_PORE for Route 1 is >= 1.20 mV (100 fine vernier steps),
        # otherwise switch to Route 2 for higher-conductance pores.
        if vpore_ideal_r1 >= 0.0012:
            route_sel = 0
            v_target = min(2.4576, max(0.0012, vpore_ideal_r1))
        else:
            route_sel = 1
            v_target = min(2.4576, max(0.00012, vpore_ideal_r2))

        dac_cfg = self.solve_dac_codes_for_vpore(v_target)
        v_pore_actual = dac_cfg["achievable_vpore_v"]
        i_pore_actual_a = v_pore_actual / r_pore_ohm

        # Run full readout chain simulation at selected route and actual V_PORE
        readout = self.simulate_full_readout_chain(
            i_pore_a=i_pore_actual_a,
            route_sel=route_sel,
            v_bias_v=0.0,
            freq_hz=0.0,
        )

        # Noise floor & SNR calculation
        if route_sel == 0:
            noise_rms_a = self.calculate_route1_noise_psd(freq_hz=50.0)["i_rms_pa"] * 1e-12  # ~36.2 fA_rms
            is_saturated = (abs(i_pore_actual_a) * self.R1_TIA1_FB > 2.048) or (abs(readout["v_mux_in_v"]) > 2.048)
        else:
            # Route 2 100 kOhm thermal + OPA2192 noise over 106.1 kHz bandwidth (~35 pA_rms)
            i_th_r10_sq = (4.0 * self.K_BOLTZMANN * self.temperature_k) / self.R10_TIA2_FB
            noise_rms_a = math.sqrt(i_th_r10_sq * 106_103.0)  # ~132 pA_rms over full 106 kHz BW
            is_saturated = abs(readout["v_mux_in_v"]) > 2.048

        snr_linear = abs(i_pore_actual_a) / max(noise_rms_a, 1e-21)
        snr_db = 20.0 * math.log10(max(snr_linear, 1e-9))
        headroom_pct = max(0.0, (1.0 - (abs(readout["v_mux_in_v"]) / 2.048)) * 100.0)

        return {
            "pore_diameter_nm": pore_diameter_nm,
            "membrane_thickness_nm": membrane_thickness_nm,
            "liquid_conductivity_s_m": liquid_conductivity_s_m,
            "surface_charge_c_m2": surface_charge_c_m2,
            "r_pore_ohm": r_pore_ohm,
            "selected_route": route_sel,
            "route_label": "Route 1 (-10 GOhm)" if route_sel == 0 else "Route 2 (-100 kOhm)",
            "v_pore_v": v_pore_actual,
            "v_pore_mv": v_pore_actual * 1e3,
            "dac_code_a": dac_cfg["code_a"],
            "dac_code_b": dac_cfg["code_b"],
            "i_pore_a": i_pore_actual_a,
            "v_tia_mux_out_v": readout["v_mux_in_v"],
            "v_adc_diff_v": readout["v_diff_adc_actual_v"],
            "adc_code_16bit": readout["adc_signed_code_16bit"],
            "noise_rms_a": noise_rms_a,
            "snr_db": snr_db,
            "headroom_pct": headroom_pct,
            "is_saturated": is_saturated,
            "is_resolvable": (not is_saturated) and (snr_db >= 6.0),
        }

    def evaluate_broad_range_sensing_matrix(self) -> List[Dict[str, Any]]:
        """
        Generates and validates the complete 5 nm to 200 um sensing matrix across:
        - Very conductive ionic liquids (3.0M NaCl, 1.0M KCl, 0.154M NaCl)
        - Dilute low-ionic liquids (1.0mM KCl)
        - Non-ionic / polar organic / ultrapure DI liquids (1e-4 S/m and 5.5e-6 S/m)
        """
        liquids = [
            ("3.0M NaCl (Hypertonic Ionic)", 20.0, -0.02),
            ("1.0M KCl (Standard Ionic)", 10.5, -0.02),
            ("0.154M NaCl (Physiological PBS)", 1.54, -0.02),
            ("1.0mM KCl (Dilute Low-Ionic)", 0.015, -0.015),
            ("Polar Organic / Non-Ionic (1e-4 S/m)", 1.0e-4, -0.002),
            ("DI Water / Non-Ionic (5.5e-6 S/m)", 5.5e-6, -0.015),
        ]
        pores = [
            (5.0, 20.0),          # 5 nm nanopore, L = 20 nm
            (20.0, 20.0),         # 20 nm nanopore, L = 20 nm
            (200.0, 40.0),        # 200 nm nanopore, L = 40 nm
            (1_000.0, 1_000.0),   # 1 um micropore, L = 1 um
            (10_000.0, 10_000.0), # 10 um micropore, L = 10 um
            (100_000.0, 50_000.0),# 100 um micropore, L = 50 um
            (200_000.0, 50_000.0),# 200 um micropore, L = 50 um
        ]
        matrix = []
        for liq_name, sigma, surf_q in liquids:
            for d_nm, l_nm in pores:
                row = self.balance_vpore_and_dual_tia(
                    pore_diameter_nm=d_nm,
                    membrane_thickness_nm=l_nm,
                    liquid_conductivity_s_m=sigma,
                    surface_charge_c_m2=surf_q,
                )
                row["liquid_name"] = liq_name
                matrix.append(row)
        return matrix


if __name__ == "__main__":
    sim = OpAmpSignalConditioningSimulation()
    print("=== 1. MR1 Composite Bipolar Excitation Chain (U3A/U3B OPA2197 + U9 MCP4822) ===")
    for code_a, code_b, label in [(0, 0, "Max Positive"), (2048, 0, "Zero Bias Midscale"), (4095, 0, "Max Negative"), (2048, 100, "Fine Vernier -1.2mV")]:
        exc = sim.calculate_excitation_voltage(code_a=code_a, code_b=code_b)
        print(
            f"  {label:22s} (A={code_a:4d}, B={code_b:4d}): V_PORE = {exc['v_pore_out_v']:+.6f} V "
            f"(Coarse={exc['step_coarse_mv']:.2f} mV/LSB, Fine={exc['step_fine_uv']:.1f} uV/LSB, "
            f"Eff. Res={exc['effective_resolution_bits']:.2f} bits)"
        )

    print("\n=== 2. Amplifier Route 1 (U2 LMP7721 + U16 LTC6268) DC & Noise ===")
    r1 = sim.calculate_route1_dc_transfer(i_pore_a=100e-12, v_bias_v=0.180)
    noise = sim.calculate_route1_noise_psd(freq_hz=100.0)
    print(
        f"  I_pore = 100 pA @ V_bias = +180 mV -> U2_OUT = {r1['v_u2_tia_out_v']:+.4f} V, "
        f"Route1_OUT = {r1['v_route1_out_v']:+.4f} V (Vbias leakage = {r1['common_mode_vbias_leakage_v_v']:.1e} V/V)"
    )
    print(
        f"  Input Noise @ 100 Hz = {noise['i_total_fa_rthz']:.2f} fA/rtHz, "
        f"Integrated RMS (79.6 Hz BW) = {noise['i_rms_fa']:.1f} fA_rms"
    )

    print("\n=== 3. Amplifier Route 2 Active vs Passive Guard @ 10 kHz ===")
    grd = sim.compare_passive_vs_active_guard(freq_hz=10_000.0)
    print(
        f"  Z_guard (Passive NT3) = {grd['z_guard_passive_ohm']:.1f} Ohm vs "
        f"Z_guard (Active U5B OPA2192) = {grd['z_guard_active_ohm']:.4f} Ohm "
        f"(+{grd['active_suppression_improvement_db']:.1f} dB crosstalk suppression)"
    )

    print("\n=== 4. Broad-Range V_PORE & Dual-TIA Balancing (5 nm to 200 um, Ionic to Non-Ionic) ===")
    matrix = sim.evaluate_broad_range_sensing_matrix()
    resolvable_count = sum(1 for r in matrix if r["is_resolvable"])
    print(f"  Validated {resolvable_count}/{len(matrix)} pore-liquid configurations unsaturated with SNR >= 6 dB:")
    for r in matrix:
        d_nm = r["pore_diameter_nm"]
        p_str = f"{d_nm/1000:.0f} um" if d_nm >= 1000 else f"{d_nm:.0f} nm"
        print(
            f"  [{r['liquid_name']:35s} | {p_str:6s}] {r['route_label']:18s} | "
            f"V_PORE = {r['v_pore_mv']:8.2f} mV (A={r['dac_code_a']:4d}, B={r['dac_code_b']:4d}) | "
            f"V_mux = {r['v_tia_mux_out_v']:+6.3f} V | SNR = {r['snr_db']:5.1f} dB"
        )
