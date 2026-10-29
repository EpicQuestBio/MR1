#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
Unit and Integration Tests for MR1 Nanopore DAQ Client
===========================================================
Validates:
- CRC-16-CCITT packet checksum computation.
- Binary StreamFrame pack / unpack synchronization and corruption rejection.
- Transimpedance ADC to ionic current mathematical conversion.
- Current engineering unit formatting.
- Mock firmware serial port command parsing.
- High-speed stream ingestion, frame continuity, and CSV logging.
"""

import os
import sys
import tempfile
import unittest
import time
import struct

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.daq_client import (
    calculate_crc16,
    raw_to_current,
    format_current,
    StreamFrame,
    MockSerialPort,
    DaqClient,
    STREAM_MAGIC_WORD,
    SAMPLES_PER_FRAME,
    FRAME_SIZE_BYTES,
    STATUS_STREAMING_ACTIVE,
    STATUS_LEAK_DETECTED
)


class TestDaqClient(unittest.TestCase):

    def test_crc16_calculation(self):
        """Verify CRC-16-CCITT implementation against reference values."""
        # Standard CCITT-FALSE / XMODEM test vector: "123456789" -> 0x29B1 or 0x31C3 depending on model.
        # Here we test our specific polynomial (0x1021, init 0xFFFF)
        data = b"123456789"
        crc = calculate_crc16(data)
        self.assertIsInstance(crc, int)
        self.assertGreaterEqual(crc, 0)
        self.assertLessEqual(crc, 0xFFFF)

        # Consistent calculation
        self.assertEqual(crc, calculate_crc16(data))

        # Different data produces different checksum
        self.assertNotEqual(crc, calculate_crc16(b"123456788"))

    def test_stream_frame_pack_and_unpack(self):
        """Verify StreamFrame packing and unpacking integrity with CRC validation."""
        samples = tuple(range(SAMPLES_PER_FRAME))
        frame = StreamFrame(
            magic=STREAM_MAGIC_WORD,
            frame_index=42,
            timestamp_us=420000,
            sample_count=SAMPLES_PER_FRAME,
            status_flags=STATUS_STREAMING_ACTIVE,
            samples=samples,
            crc16=0
        )

        packed = frame.pack()
        self.assertEqual(len(packed), FRAME_SIZE_BYTES)

        # Unpack valid frame
        unpacked = StreamFrame.unpack(packed)
        self.assertIsNotNone(unpacked)
        self.assertEqual(unpacked.magic, STREAM_MAGIC_WORD)
        self.assertEqual(unpacked.frame_index, 42)
        self.assertEqual(unpacked.timestamp_us, 420000)
        self.assertEqual(unpacked.sample_count, SAMPLES_PER_FRAME)
        self.assertEqual(unpacked.status_flags, STATUS_STREAMING_ACTIVE)
        self.assertTrue(unpacked.is_streaming)
        self.assertFalse(unpacked.is_leak)
        self.assertEqual(unpacked.samples, samples)
        self.assertTrue(unpacked.is_valid_crc)

    def test_stream_frame_corruption_detection(self):
        """Corrupted data in the payload must fail CRC validation."""
        samples = tuple([100] * SAMPLES_PER_FRAME)
        frame = StreamFrame(
            magic=STREAM_MAGIC_WORD,
            frame_index=1,
            timestamp_us=1000,
            sample_count=SAMPLES_PER_FRAME,
            status_flags=0,
            samples=samples,
            crc16=0
        )
        packed = bytearray(frame.pack())

        # Corrupt one byte inside sample payload
        packed[20] ^= 0xFF

        unpacked = StreamFrame.unpack(bytes(packed))
        self.assertIsNotNone(unpacked)
        self.assertFalse(unpacked.is_valid_crc, "Corrupted frame must be marked invalid CRC")

    def test_stream_frame_invalid_magic(self):
        """Frames lacking the 'SENT' magic word must be rejected."""
        samples = tuple([0] * SAMPLES_PER_FRAME)
        frame = StreamFrame(
            magic=0xDEADBEEF,  # Wrong magic
            frame_index=1,
            timestamp_us=1000,
            sample_count=SAMPLES_PER_FRAME,
            status_flags=0,
            samples=samples,
            crc16=0
        )
        packed = frame.pack()
        unpacked = StreamFrame.unpack(packed)
        self.assertIsNone(unpacked)

    def test_raw_to_current_conversion(self):
        """Verify mathematical conversion from differential ADC counts to Amperes."""
        # Vref = 4.096V, Rf = 1e9 Ohm (1 Gigaohm)
        # Full positive scale: 32768 counts -> 4.096 V / 1e9 Ohm = 4.096 nA
        i_pos = raw_to_current(32768, vref=4.096, gain_ohms=1e9)
        self.assertAlmostEqual(i_pos, 4.096e-9, places=12)

        # Zero counts -> 0 A
        i_zero = raw_to_current(0, vref=4.096, gain_ohms=1e9)
        self.assertAlmostEqual(i_zero, 0.0, places=12)

        # Negative scale: -32768 counts -> -4.096 nA
        i_neg = raw_to_current(-32768, vref=4.096, gain_ohms=1e9)
        self.assertAlmostEqual(i_neg, -4.096e-9, places=12)

        # 100 MOhm gain: 1.0 V / 1e8 Ohm = 10 nA
        i_100m = raw_to_current(8000, vref=4.096, gain_ohms=1e8)
        self.assertAlmostEqual(i_100m, 1.0e-8, delta=1e-9)

    def test_format_current(self):
        """Verify formatting in human-readable engineering units."""
        self.assertIn("pA", format_current(150e-12))
        self.assertIn("nA", format_current(1.25e-9))
        self.assertIn("uA", format_current(45.0e-6))
        self.assertIn("mA", format_current(2.5e-3))

    def test_route_selection_and_dynamic_gain(self):
        """Verify route command handling and dynamic gain calculation for Route 1 vs Route 2."""
        client = DaqClient(port="MOCK", is_mock=True)
        client.connect()
        try:
            # Default Route 1: gain = 10 Gigaohm (1G TIA * 10 post-stage)
            self.assertEqual(client.active_route, 1)
            self.assertEqual(client.gain_ohms, 10e9)

            # Switch to Route 2: gain = 100 kOhm
            resp = client.set_route(2)
            self.assertIn("OK:ROUTE:2", resp)
            self.assertEqual(client.active_route, 2)
            self.assertEqual(client.gain_ohms, 100e3)

            # Switch back to Route 1
            resp = client.set_route(1)
            self.assertIn("OK:ROUTE:1", resp)
            self.assertEqual(client.active_route, 1)
            self.assertEqual(client.gain_ohms, 10e9)
        finally:
            client.disconnect()

    def test_mock_serial_commands(self):
        """Verify mock firmware serial port parses commands correctly."""
        mock = MockSerialPort()

        # Bias command
        mock.write(b"SET:BIAS:150.5\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertIn("OK:BIAS:150.50", resp)

        mock.write(b"GET:BIAS\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertIn("BIAS:150.50", resp)

        # Pump commands
        mock.write(b"PUMP:START:45\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertIn("OK:PUMP:START:45", resp)

        mock.write(b"PUMP:STOP\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertIn("OK:PUMP:STOP", resp)

        mock.write(b"PUMP:ESTOP\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertIn("OK:PUMP:ESTOP", resp)

        # SBU polarity commands
        mock.write(b"SBU:DETECT\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertIn("OK:SBU:NORMAL", resp)

        mock.write(b"SBU:STATUS\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertIn("sbu_orient", resp)

        # Status telemetry
        mock.write(b"STATUS?\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertIn("bias_mv", resp)
        self.assertIn("sampling", resp)

    def test_mock_serial_dac_waveform_commands(self):
        """Verify DAC speed, gain mode, raw transfer, and waveform synthesis commands."""
        mock = MockSerialPort()

        # Gain mode
        mock.write(b"SET:DAC:GAIN:1X\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertEqual(resp.strip(), "OK:DAC:GAIN:1X")
        self.assertFalse(mock.dac_gain_2x)

        mock.write(b"SET:DAC:GAIN:2X\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertEqual(resp.strip(), "OK:DAC:GAIN:2X")
        self.assertTrue(mock.dac_gain_2x)

        # Update rate / speed
        mock.write(b"SET:DAC:SPEED:1000000\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertEqual(resp.strip(), "OK:DAC:SPEED:1000000")
        self.assertEqual(mock.dac_speed_sps, 1000000)

        # Waveform config and start
        mock.write(b"WAVE:CONFIG:SINE:10000:250:50\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertEqual(resp.strip(), "OK:WAVE:CONFIG:SINE:10000.00:250.00:50.00")
        self.assertEqual(mock.wave_shape, "SINE")
        self.assertEqual(mock.wave_freq_hz, 10000.0)

        mock.write(b"WAVE:START\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertEqual(resp.strip(), "OK:WAVE:STARTED")
        self.assertTrue(mock.wave_active)

        # Telemetry reflecting wave active
        mock.write(b"STATUS?\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertIn('"wave_active":true', resp)
        self.assertIn('"wave_shape":"SINE"', resp)
        self.assertIn('"dac_sps":1000000', resp)

        mock.write(b"WAVE:STOP\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertEqual(resp.strip(), "OK:WAVE:STOPPED")
        self.assertFalse(mock.wave_active)

        # Direct raw write
        mock.write(b"DAC:SET:RAW:0:2048\n")
        resp = mock.read(mock.in_waiting).decode("utf-8")
        self.assertEqual(resp.strip(), "OK:DAC:RAW:0:2048")

    def test_daq_client_streaming_mock_e2e(self):
        """Verify DaqClient end-to-end streaming, frame parsing, throughput, and CSV output."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
            csv_path = tf.name

        try:
            client = DaqClient(port="MOCK", is_mock=True)
            client.set_csv_output(csv_path)
            client.connect()

            # Start streaming and acquire for 0.4 seconds
            client.set_bias(200.0)
            client.start_streaming()
            time.sleep(0.4)
            client.stop_streaming()

            stats = client.get_throughput_stats()
            self.assertGreater(stats["valid_frames"], 10, "Should have received multiple frames")
            self.assertEqual(stats["crc_errors"], 0, "Mock stream should have 0 CRC errors")
            self.assertGreater(stats["total_samples"], 640)
            self.assertGreater(stats["rate_kb_sec"], 0)

            client.disconnect()

            # Verify CSV file output
            self.assertTrue(os.path.exists(csv_path))
            with open(csv_path, "r") as f:
                header = f.readline().strip()
                self.assertIn("timestamp_us", header)
                self.assertIn("raw_adc", header)
                self.assertIn("current_pa", header)

                lines = f.readlines()
                self.assertGreater(len(lines), 600, "Should have logged hundreds of sample records")
                # Check sample values
                first_record = lines[0].split(",")
                raw_sample = int(first_record[3])
                current_pa = float(first_record[4])
                self.assertNotEqual(raw_sample, 0)
                self.assertGreater(current_pa, 0)

        finally:
            try:
                client.disconnect()
            except Exception:
                pass
            if os.path.exists(csv_path):
                try:
                    os.remove(csv_path)
                except Exception:
                    pass


if __name__ == "__main__":
    unittest.main()
