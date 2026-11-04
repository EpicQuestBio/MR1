#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
Unit and Integration Tests for MR1 WebSocket Bridge
===================================================
Verifies:
- Binary frame chunk packing (`get_binary_frame_chunk`).
- Client registration, unregistration, and broadcast error handling.
- Mock DaqClient integration and WebSocket streaming server execution.
"""

import unittest
import struct
import time
import threading
import sys
import os
from websockets.sync.client import connect

# Add scripts directory to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import websocket_bridge
import daq_client


class TestWebSocketBridgeUnit(unittest.TestCase):
    """Unit tests for binary packing and client management functions."""

    def test_get_binary_frame_chunk(self):
        timestamp_us = 1234567890123
        samples_pa = [1200.5, -345.2, 0.0, 50.1]

        chunk = websocket_bridge.get_binary_frame_chunk(timestamp_us, samples_pa)
        expected_len = 8 + 4 * len(samples_pa)
        self.assertEqual(len(chunk), expected_len)

        unpacked = struct.unpack(f"<Q{len(samples_pa)}f", chunk)
        self.assertEqual(unpacked[0], timestamp_us)
        for original, parsed in zip(samples_pa, unpacked[1:]):
            self.assertAlmostEqual(original, parsed, places=4)

    def test_client_registration(self):
        class MockClient:
            pass

        mock_ws = MockClient()
        websocket_bridge.register_client(mock_ws)
        self.assertIn(mock_ws, websocket_bridge._connected_clients)

        websocket_bridge.unregister_client(mock_ws)
        self.assertNotIn(mock_ws, websocket_bridge._connected_clients)


class TestWebSocketBridgeIntegration(unittest.TestCase):
    """Integration test checking live WebSocket server with mock DaqClient."""

    def test_mock_websocket_streaming(self):
        host = "127.0.0.1"
        ws_port = 8785

        # Start WebSocket server
        server = websocket_bridge.run_websocket_server(host, ws_port)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        # Connect WebSocket client
        ws_url = f"ws://{host}:{ws_port}"
        received_chunks = []

        def client_reader(ws):
            try:
                for _ in range(5):
                    data = ws.recv(timeout=1.0)
                    if isinstance(data, bytes):
                        received_chunks.append(data)
            except Exception:
                pass

        try:
            with connect(ws_url) as ws:
                reader_thread = threading.Thread(target=client_reader, args=(ws,), daemon=True)
                reader_thread.start()

                # Run mock listen_to_mr1 for 0.5s
                mock_client = daq_client.DaqClient(port="MOCK", is_mock=True)
                websocket_bridge.listen_to_mr1(mock_client, duration_sec=0.5)

                reader_thread.join(timeout=1.0)

            self.assertGreater(len(received_chunks), 0)

            # Verify structure of first received binary frame chunk (default batching = 16 frames = 1024 samples)
            first_chunk = received_chunks[0]
            self.assertEqual(len(first_chunk), 8 + 1024 * 4)  # 8 bytes timestamp + 1024 * float32
            timestamp_us, *samples = struct.unpack("<Q1024f", first_chunk)
            self.assertGreaterEqual(timestamp_us, 0)
            self.assertEqual(len(samples), 1024)

        finally:
            server.shutdown()
            server_thread.join(timeout=1.0)

    def test_mock_websocket_custom_batching(self):
        host = "127.0.0.1"
        ws_port = 8786

        # Start WebSocket server
        server = websocket_bridge.run_websocket_server(host, ws_port)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        ws_url = f"ws://{host}:{ws_port}"
        received_chunks = []

        def client_reader(ws):
            try:
                for _ in range(5):
                    data = ws.recv(timeout=1.0)
                    if isinstance(data, bytes):
                        received_chunks.append(data)
            except Exception:
                pass

        try:
            with connect(ws_url) as ws:
                reader_thread = threading.Thread(target=client_reader, args=(ws,), daemon=True)
                reader_thread.start()

                # Run mock listen_to_mr1 for 0.5s with batch_frames=4 (256 samples)
                mock_client = daq_client.DaqClient(port="MOCK", is_mock=True)
                websocket_bridge.listen_to_mr1(mock_client, duration_sec=0.5, batch_frames=4)

                reader_thread.join(timeout=1.0)

            self.assertGreater(len(received_chunks), 0)

            first_chunk = received_chunks[0]
            self.assertEqual(len(first_chunk), 8 + 256 * 4)  # 8 bytes timestamp + 256 * float32
            timestamp_us, *samples = struct.unpack("<Q256f", first_chunk)
            self.assertGreaterEqual(timestamp_us, 0)
            self.assertEqual(len(samples), 256)

        finally:
            server.shutdown()
            server_thread.join(timeout=1.0)

    def test_mock_websocket_bidirectional_commands_and_telemetry(self):
        host = "127.0.0.1"
        ws_port = 8787

        # Start WebSocket server
        server = websocket_bridge.run_websocket_server(host, ws_port)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        ws_url = f"ws://{host}:{ws_port}"
        telemetry_messages = []

        try:
            mock_client = daq_client.DaqClient(port="MOCK", is_mock=True)
            daq_thread = threading.Thread(
                target=websocket_bridge.listen_to_mr1,
                args=(mock_client,),
                kwargs={"duration_sec": 1.0, "batch_frames": 4},
                daemon=True
            )
            daq_thread.start()
            time.sleep(0.15)

            with connect(ws_url) as ws:
                # 1. Send set_bias command
                import json
                ws.send(json.dumps({"cmd": "set_bias", "bias_mv": 320.0}))
                time.sleep(0.1)
                self.assertEqual(mock_client.serial_port.bias_mv, 320.0)

                # 2. Send emergency_stop command
                ws.send(json.dumps({"cmd": "emergency_stop"}))
                time.sleep(0.1)
                self.assertEqual(mock_client.serial_port.bias_mv, 0.0)

                # 3. Receive telemetry JSON
                for _ in range(15):
                    try:
                        msg = ws.recv(timeout=0.5)
                        if isinstance(msg, str):
                            data = json.loads(msg)
                            if data.get("type") == "telemetry":
                                telemetry_messages.append(data)
                                break
                    except Exception:
                        pass

            self.assertGreater(len(telemetry_messages), 0)
            self.assertIn("temperature_c", telemetry_messages[0])
            self.assertIn("cis_pressure_psi", telemetry_messages[0])
            self.assertIn("trans_pressure_psi", telemetry_messages[0])
            self.assertIn("weep_leak_detected", telemetry_messages[0])

            daq_thread.join(timeout=2.0)
        finally:
            server.shutdown()
            server_thread.join(timeout=1.0)


if __name__ == "__main__":
    unittest.main()
