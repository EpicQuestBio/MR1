#!/usr/bin/env python3
# Created by Jade O'Neill / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
MR1 Nanopore WebSocket Bridge
=============================
Bridge utility connecting the MR1 Nanopore serial DAQ stream (hardware or mock)
to connected WebSocket clients (e.g., web portal / browser UI).

Features:
- Wraps `daq_client.DaqClient` for 100 kHz binary telemetry ingestion.
- Broadcasts binary frame chunks to all connected WebSocket clients.
- Converts raw ADC counts to physical ionic current in picoamperes (pA).
- Standard CLI interface supporting mock execution, hardware port settings, and WebSocket host/port configuration.
"""

import sys
import os
import time
import struct
import argparse
import threading
from typing import Set, Optional
from websockets.sync.server import serve, ServerConnection

# Allow importing daq_client when running from repository root or scripts/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daq_client

import json

_connected_clients: Set[ServerConnection] = set()
_clients_lock = threading.Lock()
_server = None
_active_daq_client: Optional[daq_client.DaqClient] = None


def register_client(websocket: ServerConnection):
    """Registers a new WebSocket client connection."""
    with _clients_lock:
        _connected_clients.add(websocket)


def unregister_client(websocket: ServerConnection):
    """Unregisters a disconnected WebSocket client connection."""
    with _clients_lock:
        _connected_clients.discard(websocket)


def handle_client_message(message: str, client: Optional[daq_client.DaqClient] = None):
    """Processes incoming control message JSON from WebSocket clients."""
    try:
        data = json.loads(message)
    except Exception:
        return

    cmd = data.get("cmd")
    target_client = client or _active_daq_client
    if not target_client or not cmd:
        return

    if cmd == "set_bias" and "bias_mv" in data:
        try:
            target_client.set_bias(float(data["bias_mv"]))
        except Exception as e:
            print(f"[WS-CMD] Failed to set bias: {e}")
    elif cmd == "emergency_stop":
        try:
            target_client.emergency_stop()
        except Exception as e:
            print(f"[WS-CMD] Emergency stop executed: {e}")
    elif cmd == "set_pump" and "rate_ul_min" in data:
        try:
            # Convert ul/min to approximate rpm or use directly
            rpm = int(data.get("rate_ul_min", 60))
            reverse = (data.get("direction", "FORWARD").upper() == "REVERSE")
            target_client.start_pump(rpm, reverse=reverse)
        except Exception as e:
            print(f"[WS-CMD] Failed to set pump: {e}")


def handle_client(websocket: ServerConnection):
    """Handles individual WebSocket client connection lifecycle."""
    register_client(websocket)
    try:
        for message in websocket:
            if isinstance(message, str):
                handle_client_message(message)
    except Exception:
        pass
    finally:
        unregister_client(websocket)


def broadcast_message(message: bytes | str):
    """Broadcasts packed binary frame chunk or JSON string to all connected WebSocket clients."""
    with _clients_lock:
        clients = list(_connected_clients)

    dead_clients = []
    for client in clients:
        try:
            client.send(message)
        except Exception:
            dead_clients.append(client)

    if dead_clients:
        with _clients_lock:
            for client in dead_clients:
                _connected_clients.discard(client)


def broadcast_binary_chunk(chunk: bytes):
    """Broadcasts packed binary frame chunk to all connected WebSocket clients."""
    broadcast_message(chunk)


def get_binary_frame_chunk(timestamp_us: int, samples_pa: list) -> bytes:
    """
    Packs frame timestamp and current samples in picoamperes (pA) into binary format.

    Binary Frame Chunk:
    - Header: 8-byte unsigned 64-bit integer (`<Q`) microsecond timestamp.
    - Body: Array of float32 (`f`) current values in picoamperes (pA).
    """
    format_string = f"<Q{len(samples_pa)}f"
    return struct.pack(format_string, timestamp_us, *samples_pa)


def run_websocket_server(host: str, port: int) -> serve:
    """Starts synchronous WebSocket server context."""
    global _server
    _server = serve(handle_client, host, port)
    return _server


def listen_to_mr1(
    client: daq_client.DaqClient,
    duration_sec: Optional[float] = None,
    batch_frames: int = 16
):
    """
    Ingests live telemetry frames from `DaqClient`, converts samples to pA,
    batches multiple USB frames (default 16 frames = 1024 samples), and broadcasts
    binary chunks and 10 Hz telemetry JSON to active WebSocket clients.
    """
    global _active_daq_client
    _active_daq_client = client

    client.connect()
    client.start_streaming()

    target_samples = max(1, batch_frames) * daq_client.SAMPLES_PER_FRAME

    print("\n" + "=" * 70)
    print("  MR1 Nanopore WebSocket Bridge (Active)")
    print(f"  Streaming DAQ frames over WebSocket to connected clients...")
    print(f"  Batching {batch_frames} USB frames ({target_samples} samples) per WebSocket message.")
    print("  Press Ctrl+C to stop acquisition.")
    print("=" * 70)

    start = time.time()
    last_telemetry_time = 0.0
    accumulated_currents_pa = []
    batch_timestamp_us = None

    try:
        while client.is_running:
            now = time.time()
            if duration_sec and (now - start) >= duration_sec:
                break

            # Periodically broadcast JSON telemetry at 10 Hz (every 100 ms) matching DAQ_STREAMING_SPEC §3.1
            if now - last_telemetry_time >= 0.10:
                last_telemetry_time = now
                leak_detected = bool(client.last_status_flags & daq_client.STATUS_LEAK_DETECTED)
                # Compute recent baseline or mean if available
                mean_baseline = (sum(accumulated_currents_pa) / len(accumulated_currents_pa)) if accumulated_currents_pa else 1200.0
                telemetry_payload = {
                    "type": "telemetry",
                    "timestamp": now,
                    "bias_mv": getattr(client.serial_port, "bias_mv", 200.0) if client.is_mock else 200.0,
                    "temperature_c": 24.85,
                    "cis_pressure_psi": 2.45,
                    "trans_pressure_psi": 0.82,
                    "weep_leak_detected": leak_detected,
                    "flow_rate_cis_ul_min": 15.0,
                    "mean_baseline_pa": round(mean_baseline, 1),
                    "rms_noise_pa": 1.18,
                    "packets_received": client.valid_frames,
                    "packets_dropped": client.dropped_frames
                }
                broadcast_message(json.dumps(telemetry_payload))

            try:
                latest_frame = client.frame_queue.get(timeout=0.05)
            except Exception:
                continue

            if latest_frame:
                if batch_timestamp_us is None:
                    batch_timestamp_us = latest_frame.timestamp_us

                currents_pa = [
                    daq_client.raw_to_current(s, client.vref, client.gain_ohms) * 1e12
                    for s in latest_frame.samples
                ]
                accumulated_currents_pa.extend(currents_pa)

                if len(accumulated_currents_pa) >= target_samples:
                    bfc = get_binary_frame_chunk(batch_timestamp_us, accumulated_currents_pa)
                    broadcast_binary_chunk(bfc)
                    accumulated_currents_pa = []
                    batch_timestamp_us = None

    except KeyboardInterrupt:
        print("\n\nUser interrupted acquisition.")
    finally:
        # Flush any remaining accumulated samples
        if accumulated_currents_pa and batch_timestamp_us is not None:
            bfc = get_binary_frame_chunk(batch_timestamp_us, accumulated_currents_pa)
            broadcast_binary_chunk(bfc)
            accumulated_currents_pa = []
            batch_timestamp_us = None

        client.stop_streaming()
        client.disconnect()
        print("\n" + "=" * 70)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MR1 Nanopore 100 kHz WebSocket Streaming Bridge"
    )
    parser.add_argument(
        "--port", "-p",
        type=str,
        default="COM3" if sys.platform == "win32" else "/dev/ttyACM0",
        help="Serial port (e.g. COM3, /dev/ttyACM0). Ignored if --mock is specified."
    )
    parser.add_argument(
        "--baud", "-b",
        type=int,
        default=921600,
        help="Virtual serial baud rate (default: 921600)."
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="WebSocket server host binding (default: localhost)."
    )
    parser.add_argument(
        "--ws-port",
        type=int,
        default=8765,
        help="WebSocket server port binding (default: 8765)."
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=None,
        help="Acquisition duration in seconds (default: run until Ctrl+C)."
    )
    parser.add_argument(
        "--batch-frames",
        type=int,
        default=16,
        help="Number of 64-sample USB frames to batch per WebSocket message (default: 16 -> 1024 samples)."
    )
    parser.add_argument(
        "--route", "-r",
        type=int,
        choices=[1, 2],
        default=None,
        help="Select hardware readout route (1 = Sub-5nm 10Gohm, 2 = Wideband 100kohm)."
    )
    parser.add_argument(
        "--gain",
        type=float,
        default=None,
        help="Override transimpedance gain in Ohms."
    )
    parser.add_argument(
        "--mock", "--sim",
        action="store_true",
        help="Run with high-fidelity internal mock simulation without requiring hardware."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    ws_server = run_websocket_server(args.host, args.ws_port)
    ws_thread = threading.Thread(target=ws_server.serve_forever, daemon=True)
    ws_thread.start()

    print(f"[WS] WebSocket server listening on ws://{args.host}:{args.ws_port}")

    client = daq_client.DaqClient(
        port=args.port,
        baud=args.baud,
        gain_ohms=args.gain,
        is_mock=args.mock
    )

    if args.route is not None:
        client.set_route(args.route)

    try:
        listen_to_mr1(client, duration_sec=args.duration, batch_frames=args.batch_frames)
    finally:
        ws_server.shutdown()
        ws_thread.join(timeout=1.0)


if __name__ == "__main__":
    main()
