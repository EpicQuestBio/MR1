# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
Unit tests for MR1 Pump Controller firmware logic, packet framing,
flow rate calibration, and overpressure safety cutoff equations.
"""

import unittest
import struct


def calculate_pump_checksum(sof: int, cmd: int, param: int) -> int:
    """Calculates XOR checksum matching SbuLink / pump_uart."""
    param_lsb = param & 0xFF
    param_msb = (param >> 8) & 0xFF
    return sof ^ cmd ^ param_lsb ^ param_msb


def raw_to_pressure_psi(raw_p: int, p_min: float, p_max: float) -> float:
    """Honeywell ABP2 24-bit transfer function A."""
    output_min = 1677722
    output_max = 15099494
    if raw_p < output_min:
        return p_min
    if raw_p > output_max:
        return p_max
    return ((raw_p - output_min) * (p_max - p_min) / (output_max - output_min)) + p_min


def calculate_flow_duty(ul_per_min: float, ul_per_rev: float, max_rpm: float) -> float:
    """Calculates motor PWM duty percentage."""
    if ul_per_min <= 0.0:
        return 0.0
    rpm = ul_per_min / ul_per_rev
    duty = (rpm / max_rpm) * 100.0
    if 0.0 < duty < 15.0:
        duty = 15.0
    return min(100.0, duty)


class TestPumpFirmware(unittest.TestCase):
    def test_sbu_packet_framing_and_checksum(self):
        sof = 0xAA
        cmd = 0x01  # CMD_RUN_FWD
        param = 150  # 150 uL/min
        expected_cs = sof ^ cmd ^ (150 & 0xFF) ^ 0
        self.assertEqual(calculate_pump_checksum(sof, cmd, param), expected_cs)

    def test_pressure_transducer_conversion(self):
        # 0 psi at 10% (1,677,722)
        p0 = raw_to_pressure_psi(1677722, 0.0, 15.0)
        self.assertAlmostEqual(p0, 0.0, places=2)

        # 15 psi at 90% (15,099,494)
        p15 = raw_to_pressure_psi(15099494, 0.0, 15.0)
        self.assertAlmostEqual(p15, 15.0, places=2)

        # Midscale 7.5 psi at 50% ((1677722 + 15099494)/2 = 8,388,608)
        p_mid = raw_to_pressure_psi(8388608, 0.0, 15.0)
        self.assertAlmostEqual(p_mid, 7.5, places=2)

    def test_flow_rate_duty_calculation(self):
        ul_per_rev = 45.0
        max_rpm = 180.0
        # 45 uL/min -> 1 RPM -> (1/180)*100 = 0.55% -> clamped to starting threshold 15.0%
        self.assertEqual(calculate_flow_duty(45.0, ul_per_rev, max_rpm), 15.0)

        # 90 uL/min -> 2 RPM -> clamped to 15.0%
        self.assertEqual(calculate_flow_duty(90.0, ul_per_rev, max_rpm), 15.0)

        # 4500 uL/min -> 100 RPM -> (100/180)*100 = 55.55%
        duty = calculate_flow_duty(4500.0, ul_per_rev, max_rpm)
        self.assertAlmostEqual(duty, 55.555, places=2)

    def test_overpressure_detection(self):
        MAX_CIS = 10.0
        MAX_TRANS = 4.0

        def check_overpressure(p_cis: float, p_trans: float) -> bool:
            return p_cis > MAX_CIS or p_trans > MAX_TRANS

        self.assertFalse(check_overpressure(2.5, 1.2))
        self.assertTrue(check_overpressure(10.5, 1.2))  # Cis trip
        self.assertTrue(check_overpressure(3.0, 4.5))   # Trans trip


if __name__ == "__main__":
    unittest.main()
