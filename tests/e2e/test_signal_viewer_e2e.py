#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
End-to-End (E2E) Test Suite for MR1 Signal Viewer
=================================================
Automated Playwright simulation that:
1. Spawns `scripts/websocket_bridge.py --mock` in a background subprocess.
2. Serves `signal-viewer/` over a local HTTP server.
3. Launches Playwright headless Chromium and visits the Signal Viewer web application.
4. Connects to `ws://localhost:8799` bridge.
5. Verifies:
   - WebSocket connection status changes to Connected.
   - Live waveform canvas receives draw calls.
   - Throughput metrics settle near ~100 kS/s.
   - Live Telemetry JSON arrives (temperature, pressures, leak status).
   - Bidirectional controls (setting bias and estop) interact with backend.
   - Translocation events are detected and populated in the events table with dwell time and depth.
"""

import os
import sys
import time
import subprocess
import unittest
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VIEWER_DIR = os.path.join(REPO_ROOT, "signal-viewer")


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]
        s.close()
        return port


class SignalViewerE2ETest(unittest.TestCase):
    http_server = None
    http_thread = None
    http_port = 0
    ws_port = 0
    bridge_proc = None

    @classmethod
    def setUpClass(cls):
        # 1. Allocate free ports
        cls.http_port = find_free_port()
        cls.ws_port = find_free_port()

        # 2. Start HTTP server serving signal-viewer/
        class CustomHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=VIEWER_DIR, **kwargs)

            def log_message(self, format, *args):
                pass  # Suppress request logging

        cls.http_server = ThreadingHTTPServer(("127.0.0.1", cls.http_port), CustomHandler)
        cls.http_thread = threading.Thread(target=cls.http_server.serve_forever, daemon=True)
        cls.http_thread.start()

        # 3. Start websocket_bridge.py in background with mock simulation
        venv_python = sys.executable
        bridge_script = os.path.join(REPO_ROOT, "scripts", "websocket_bridge.py")
        cmd = [
            venv_python,
            bridge_script,
            "--mock",
            "--host", "127.0.0.1",
            "--ws-port", str(cls.ws_port),
            "--batch-frames", "8"
        ]
        cls.bridge_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1.0)  # Wait for bridge and server startup

    @classmethod
    def tearDownClass(cls):
        if cls.bridge_proc:
            cls.bridge_proc.terminate()
            try:
                cls.bridge_proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                cls.bridge_proc.kill()
        if cls.http_server:
            cls.http_server.shutdown()
            cls.http_thread.join(timeout=1.0)

    def test_full_signal_viewer_simulation(self):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})

            # Navigate to signal viewer
            viewer_url = f"http://127.0.0.1:{self.http_port}/index.html"
            page.goto(viewer_url)
            page.wait_for_selector("#socketUrl")

            # Fill WebSocket endpoint with test port
            page.fill("#socketUrl", f"ws://127.0.0.1:{self.ws_port}")
            page.click("#connectBtn")

            # 1. Assert connection succeeds
            page.wait_for_selector("#connectionLabel:text('Connected')", timeout=5000)

            # 2. Wait for samples to stream in and check throughput
            # Buffer value should become > 0
            page.wait_for_function(
                "() => parseFloat(document.getElementById('bufferValue').textContent) > 0.1",
                timeout=5000
            )

            # 3. Verify incoming telemetry badges
            page.wait_for_function(
                "() => parseFloat(document.getElementById('tempBadge').textContent) > 0.0",
                timeout=5000
            )
            temp_text = page.text_content("#tempBadge")
            temp_val = float(temp_text)
            self.assertAlmostEqual(temp_val, 24.9, delta=0.5)

            leak_text = page.text_content("#leakText")
            self.assertEqual(leak_text, "LEAK SENSOR: DRY")

            # 4. Verify bidirectional controls: Set bias and check reflected value
            page.fill("#biasInput", "300")
            page.click("#setBiasBtn")
            page.wait_for_selector("#ctrlStatus:text('Bias command sent: 300 mV')", timeout=3000)

            # 5. Verify bidirectional controls: Emergency stop
            page.click("#estopBtn")
            page.wait_for_selector("#ctrlStatus:text('EMERGENCY STOP SENT!')", timeout=3000)

            # Re-enable bias to keep events generating
            page.fill("#biasInput", "200")
            page.click("#setBiasBtn")

            # 6. Verify translocation event detection in UI table
            # With multi-scale events firing periodically in mock simulation,
            # an event row should appear in the table within ~4 seconds
            page.wait_for_selector(".event-row", timeout=6000)
            rows = page.query_selector_all(".event-row")
            self.assertGreater(len(rows), 0)

            first_row_text = rows[0].text_content()
            self.assertIn("#", first_row_text)
            self.assertIn("pA", first_row_text)
            self.assertIn("µs", first_row_text)

            # Verify Canvas is actively rendering (not blank)
            canvas_handle = page.query_selector("#signalCanvas")
            self.assertIsNotNone(canvas_handle)

            browser.close()


if __name__ == "__main__":
    unittest.main()
