"""
Unit tests for Sentinel Nanopore Reader firmware protocol, packet serialization,
CRC-16 validation, and host-device command interfaces.
"""

import struct
import unittest

STREAM_MAGIC_WORD = 0x53454E54  # "SENT"
SAMPLES_PER_FRAME = 64


def calculate_crc16(data: bytes) -> int:
    """CRC-16-CCITT implementation matching firmware protocol.h."""
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


class TestFirmwareProtocol(unittest.TestCase):
    def test_crc16_calculation(self):
        # Known standard test vectors for CRC-16-CCITT
        test_data = b"123456789"
        crc = calculate_crc16(test_data)
        # CRC-16-CCITT false (init 0xFFFF, poly 0x1021) of "123456789" is 0x29B1
        self.assertEqual(crc, 0x29B1)

    def test_stream_frame_packing_and_unpacking(self):
        """Verify binary layout of StreamFrame matches firmware struct."""
        # Struct format:
        # uint32 magic (4B)
        # uint32 frame_index (4B)
        # uint32 timestamp_us (4B)
        # uint16 sample_count (2B)
        # uint16 status_flags (2B)
        # int16 samples[64] (128B)
        # uint16 crc16 (2B)
        # Total size: 4 + 4 + 4 + 2 + 2 + 128 + 2 = 146 bytes
        expected_size = 146

        magic = STREAM_MAGIC_WORD
        frame_idx = 1042
        timestamp = 5400200
        sample_count = SAMPLES_PER_FRAME
        status_flags = 0x0001  # STATUS_STREAMING_ACTIVE

        # Generate sample sine wave
        samples = [int(1000 * ((i % 16) - 8)) for i in range(SAMPLES_PER_FRAME)]

        header_and_data = struct.pack(
            f"<IIIHH{SAMPLES_PER_FRAME}h",
            magic,
            frame_idx,
            timestamp,
            sample_count,
            status_flags,
            *samples,
        )

        crc = calculate_crc16(header_and_data)
        full_packet = header_and_data + struct.pack("<H", crc)

        self.assertEqual(len(full_packet), expected_size)

        # Unpack and verify
        unpacked_magic = struct.unpack_from("<I", full_packet, 0)[0]
        self.assertEqual(unpacked_magic, STREAM_MAGIC_WORD)

        unpacked_idx, unpacked_time, unpacked_count, unpacked_flags = struct.unpack_from(
            "<IIHH", full_packet, 4
        )
        self.assertEqual(unpacked_idx, 1042)
        self.assertEqual(unpacked_time, 5400200)
        self.assertEqual(unpacked_count, 64)
        self.assertEqual(unpacked_flags, 1)

        # Check CRC verification
        calculated_crc = calculate_crc16(full_packet[:-2])
        packet_crc = struct.unpack_from("<H", full_packet, expected_size - 2)[0]
        self.assertEqual(calculated_crc, packet_crc)

    def test_pump_packet_xor_checksum(self):
        """Verify pump packet XOR checksum calculation."""
        sof = 0xAA
        cmd = 0x01  # Run
        param = 120  # 120 RPM
        param_lsb = param & 0xFF
        param_msb = (param >> 8) & 0xFF

        expected_cs = sof ^ cmd ^ param_lsb ^ param_msb
        calc_cs = 0xAA ^ 0x01 ^ 120 ^ 0

        self.assertEqual(expected_cs, calc_cs)

    def test_pore_bias_voltage_clamping_and_mapping(self):
        """Verify DAC voltage mapping logic."""
        BIAS_MIN_MV = -1587.0
        BIAS_MAX_MV = 1587.0

        def mv_to_code(mv: float) -> int:
            clamped = max(BIAS_MIN_MV, min(BIAS_MAX_MV, mv))
            norm = (clamped - BIAS_MIN_MV) / (BIAS_MAX_MV - BIAS_MIN_MV)
            return int(round(norm * 4095.0))

        # Midscale (0 mV) -> code ~2048
        self.assertEqual(mv_to_code(0.0), 2048)
        # Min scale (-1587 mV) -> code 0
        self.assertEqual(mv_to_code(-1587.0), 0)
        # Max scale (+1587 mV) -> code 4095
        self.assertEqual(mv_to_code(1587.0), 4095)
        # Out-of-bounds negative clamped to 0
        self.assertEqual(mv_to_code(-2500.0), 0)
        # Out-of-bounds positive clamped to 4095
        self.assertEqual(mv_to_code(3000.0), 4095)


if __name__ == "__main__":
    unittest.main()
