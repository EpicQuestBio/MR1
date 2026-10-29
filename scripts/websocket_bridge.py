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

_connected_clients: Set[ServerConnection] = set()
_clients_lock = threading.Lock()
_server = None


def register_client(websocket: ServerConnection):
    """Registers a new WebSocket client connection."""
    with _clients_lock:
        _connected_clients.add(websocket)


def unregister_client(websocket: ServerConnection):
    """Unregisters a disconnected WebSocket client connection."""
    with _clients_lock:
        _connected_clients.discard(websocket)


def handle_client(websocket: ServerConnection):
    """Handles individual WebSocket client connection lifecycle."""
    register_client(websocket)
    try:
        for message in websocket:
            # Handle incoming control messages from WebSocket clients if needed
            pass
    except Exception:
        pass
    finally:
        unregister_client(websocket)


def broadcast_binary_chunk(chunk: bytes):
    """Broadcasts packed binary frame chunk to all connected WebSocket clients."""
    with _clients_lock:
        clients = list(_connected_clients)

    dead_clients = []
    for client in clients:
        try:
            client.send(chunk)
        except Exception:
            dead_clients.append(client)

    if dead_clients:
        with _clients_lock:
            for client in dead_clients:
                _connected_clients.discard(client)


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
    duration_sec: Optional[float] = None
):
    """
    Ingests live telemetry frames from `DaqClient`, converts samples to pA,
    and broadcasts binary chunks to active WebSocket clients.
    """
    client.connect()
    client.start_streaming()

    print("\n" + "=" * 70)
    print("  MR1 Nanopore WebSocket Bridge (Active)")
    print(f"  Streaming DAQ frames over WebSocket to connected clients...")
    print("  Press Ctrl+C to stop acquisition.")
    print("=" * 70)

    start = time.time()
    try:
        while client.is_running:
            if duration_sec and (time.time() - start) >= duration_sec:
                break

            try:
                latest_frame = client.frame_queue.get(timeout=0.1)
            except Exception:
                continue

            if latest_frame:
                currents_pa = [
                    daq_client.raw_to_current(s, client.vref, client.gain_ohms) * 1e12
                    for s in latest_frame.samples
                ]
                bfc = get_binary_frame_chunk(latest_frame.timestamp_us, currents_pa)
                broadcast_binary_chunk(bfc)

    except KeyboardInterrupt:
        print("\n\nUser interrupted acquisition.")
    finally:
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
        listen_to_mr1(client, duration_sec=args.duration)
    finally:
        ws_server.shutdown()
        ws_thread.join(timeout=1.0)


if __name__ == "__main__":
    main()
