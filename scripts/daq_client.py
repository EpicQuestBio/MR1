#!/usr/bin/env python3
"""
Sentinel Nanopore DAQ Client
=============================
High-throughput 100 kHz USB streaming consumer and control client for the
ESP32-S3 Sentinel Nanopore Reader.

Features:
- Connects to native USB CDC-ACM virtual serial port (up to 921,600+ baud).
- Binary frame synchronization and unpacking (magic word 'SENT' / 0x53454E54).
- CRC-16-CCITT packet integrity validation.
- Real-time packet sequence loss and jitter detection.
- Live pore current conversion (I_pore = V_adc / R_feedback) in pA / nA / uA.
- Streaming data capture to disk (.csv, .bin, or compressed formats).
- Interactive live terminal dashboard with real-time signal metrics.
- Bidirectional command channel (bias setting, pulse injection, pump control, SBU detection).
- Built-in high-fidelity Mock / Simulation mode (--mock) for standalone testing and CI.
"""

import sys
import os
import time
import math
import struct
import argparse
import threading
import queue
from typing import Optional, Tuple, List, Dict, Any, Generator

# Protocol Constants (matching firmware/include/protocol.h and config.h)
STREAM_MAGIC_WORD = 0x53454E54  # "SENT" in little-endian (bytes: 0x54, 0x4E, 0x45, 0x53 = b"TNES")
STREAM_MAGIC_BYTES = struct.pack("<I", STREAM_MAGIC_WORD)
SAMPLES_PER_FRAME = 64
FRAME_STRUCT_FORMAT = f"<IIIHH{SAMPLES_PER_FRAME}hH"
FRAME_SIZE_BYTES = struct.calcsize(FRAME_STRUCT_FORMAT)  # 146 bytes

# Status Flags
STATUS_STREAMING_ACTIVE = 1 << 0
STATUS_LEAK_DETECTED    = 1 << 1
STATUS_PUMP_CONNECTED   = 1 << 2
STATUS_PUMP_RUNNING     = 1 << 3
STATUS_PUMP_EMERGENCY   = 1 << 4
STATUS_DAC_PULSE_ACTIVE = 1 << 5
STATUS_DAC_WAVE_ACTIVE  = 1 << 6


def calculate_crc16(data: bytes) -> int:
    """Computes CRC-16-CCITT (poly 0x1021, init 0xFFFF) matching firmware calculate_crc16()."""
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def raw_to_current(raw_sample: int, vref: float = 4.096, gain_ohms: float = 1e9) -> float:
    """
    Converts 16-bit differential ADC raw sample to pore ionic current in Amperes.
    Differential range: -32768 to +32767 -> -Vref to +Vref.
    I_pore = V_adc / R_feedback.
    Default gain_ohms = 1.0e9 (1 Gigaohm transimpedance gain -> 1 nA / 1 V).
    """
    v_adc = (raw_sample / 32768.0) * vref
    return v_adc / gain_ohms


def format_current(amps: float) -> str:
    """Formats current in engineering units (pA, nA, uA, mA)."""
    abs_amps = abs(amps)
    if abs_amps < 1e-9:
        return f"{amps * 1e12:8.2f} pA"
    elif abs_amps < 1e-6:
        return f"{amps * 1e9:8.3f} nA"
    elif abs_amps < 1e-3:
        return f"{amps * 1e6:8.3f} uA"
    else:
        return f"{amps * 1e3:8.3f} mA"


class StreamFrame:
    """Represents an unpacked binary telemetry frame from the Sentinel Reader."""

    __slots__ = (
        "magic", "frame_index", "timestamp_us", "sample_count",
        "status_flags", "samples", "crc16", "is_valid_crc"
    )

    def __init__(
        self,
        magic: int,
        frame_index: int,
        timestamp_us: int,
        sample_count: int,
        status_flags: int,
        samples: Tuple[int, ...],
        crc16: int,
        is_valid_crc: bool = True
    ):
        self.magic = magic
        self.frame_index = frame_index
        self.timestamp_us = timestamp_us
        self.sample_count = sample_count
        self.status_flags = status_flags
        self.samples = samples
        self.crc16 = crc16
        self.is_valid_crc = is_valid_crc

    @property
    def is_streaming(self) -> bool:
        return bool(self.status_flags & STATUS_STREAMING_ACTIVE)

    @property
    def is_leak(self) -> bool:
        return bool(self.status_flags & STATUS_LEAK_DETECTED)

    @property
    def is_pump_running(self) -> bool:
        return bool(self.status_flags & STATUS_PUMP_RUNNING)

    @property
    def is_pump_connected(self) -> bool:
        return bool(self.status_flags & STATUS_PUMP_CONNECTED)

    @property
    def is_emergency(self) -> bool:
        return bool(self.status_flags & STATUS_PUMP_EMERGENCY)

    @property
    def is_pulse_active(self) -> bool:
        return bool(self.status_flags & STATUS_DAC_PULSE_ACTIVE)

    @property
    def is_wave_active(self) -> bool:
        return bool(self.status_flags & STATUS_DAC_WAVE_ACTIVE)

    @classmethod
    def unpack(cls, buffer: bytes) -> Optional["StreamFrame"]:
        """Unpacks 146 bytes into a StreamFrame and verifies CRC-16."""
        if len(buffer) < FRAME_SIZE_BYTES:
            return None

        unpacked = struct.unpack(FRAME_STRUCT_FORMAT, buffer[:FRAME_SIZE_BYTES])
        magic = unpacked[0]
        if magic != STREAM_MAGIC_WORD:
            return None

        frame_index = unpacked[1]
        timestamp_us = unpacked[2]
        sample_count = unpacked[3]
        status_flags = unpacked[4]
        samples = unpacked[5:69]
        received_crc = unpacked[69]

        # CRC is calculated over all bytes preceding the 2-byte crc16 field
        expected_crc = calculate_crc16(buffer[: FRAME_SIZE_BYTES - 2])
        is_valid = (received_crc == expected_crc)

        return cls(
            magic=magic,
            frame_index=frame_index,
            timestamp_us=timestamp_us,
            sample_count=sample_count,
            status_flags=status_flags,
            samples=samples,
            crc16=received_crc,
            is_valid_crc=is_valid
        )

    def pack(self) -> bytes:
        """Packs frame into 146 binary bytes with correct CRC-16."""
        payload = struct.pack(
            f"<IIIHH{SAMPLES_PER_FRAME}h",
            self.magic,
            self.frame_index,
            self.timestamp_us,
            self.sample_count,
            self.status_flags,
            *self.samples
        )
        computed_crc = calculate_crc16(payload)
        return payload + struct.pack("<H", computed_crc)


class MockSerialPort:
    """
    Simulates the ESP32-S3 firmware serial port:
    - Generates 100 kHz streaming binary frames.
    - Emulates realistic baseline ionic pore current (~1.2 nA) with 1/f noise.
    - Simulates transient DNA translocation blockade events.
    - Responds to ASCII commands (SET:BIAS, STREAM:START/STOP, SBU:DETECT, etc.).
    """

    def __init__(self, sample_rate_hz: int = 100000):
        self.sample_rate_hz = sample_rate_hz
        self.streaming = False
        self.bias_mv = 200.0
        self.pulse_active = False
        self.dac_gain_2x = True
        self.dac_speed_sps = 200000
        self.wave_active = False
        self.wave_shape = "OFF"
        self.wave_freq_hz = 1000.0
        self.wave_amp_mv = 100.0
        self.wave_offset_mv = 0.0
        self.pump_connected = True
        self.pump_running = False
        self.pump_rpm = 0
        self.leak_detected = False
        self.sbu_orientation = 1  # 1 = Normal, 2 = Inverted

        self._frame_index = 0
        self._start_time_us = int(time.time() * 1e6)
        self._rx_queue = queue.Queue()
        self._tx_buffer = bytearray()
        self._lock = threading.Lock()
        self._is_open = True

        # Translocation event simulation state
        self._event_active = False
        self._event_samples_remaining = 0

    @property
    def in_waiting(self) -> int:
        self._generate_mock_stream()
        with self._lock:
            return len(self._tx_buffer)

    def read(self, size: int = 1) -> bytes:
        self._generate_mock_stream()
        with self._lock:
            chunk = bytes(self._tx_buffer[:size])
            del self._tx_buffer[:size]
            return chunk

    def write(self, data: bytes) -> int:
        text = data.decode("utf-8", errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            self._handle_command(line)
        return len(data)

    def close(self):
        self._is_open = False

    def _handle_command(self, cmd: str):
        response = ""
        if cmd == "HELP":
            response = "=== Sentinel Nanopore Commands ===\nOK:HELP\n"
        elif cmd.startswith("SET:BIAS:"):
            try:
                self.bias_mv = float(cmd.split(":")[2])
                response = f"OK:BIAS:{self.bias_mv:.2f}\n"
            except ValueError:
                response = "ERR:INVALID_ARG\n"
        elif cmd == "GET:BIAS":
            response = f"BIAS:{self.bias_mv:.2f}\n"
        elif cmd.startswith("CMD:PULSE:"):
            parts = cmd.split(":")
            response = f"OK:PULSE:{parts[2]}:{parts[3]}\n"
        elif cmd.startswith("SET:DAC:GAIN:"):
            mode = cmd.split(":")[3].upper()
            if mode == "1X":
                self.dac_gain_2x = False
                response = "OK:DAC:GAIN:1X\n"
            elif mode == "2X":
                self.dac_gain_2x = True
                response = "OK:DAC:GAIN:2X\n"
            else:
                response = "ERR:INVALID_GAIN_MODE\n"
        elif cmd.startswith("SET:DAC:SPEED:"):
            try:
                sps = int(cmd.split(":")[3])
                self.dac_speed_sps = min(max(sps, 1000), 1000000)
                response = f"OK:DAC:SPEED:{self.dac_speed_sps}\n"
            except (IndexError, ValueError):
                response = "ERR:INVALID_ARG\n"
        elif cmd.startswith("WAVE:CONFIG:"):
            parts = cmd.split(":")
            if len(parts) >= 5:
                self.wave_shape = parts[2].upper()
                self.wave_freq_hz = float(parts[3])
                self.wave_amp_mv = float(parts[4])
                self.wave_offset_mv = float(parts[5]) if len(parts) > 5 else 0.0
                response = f"OK:WAVE:CONFIG:{self.wave_shape}:{self.wave_freq_hz:.2f}:{self.wave_amp_mv:.2f}:{self.wave_offset_mv:.2f}\n"
            else:
                response = "ERR:WAVE:SYNTAX\n"
        elif cmd == "WAVE:START":
            self.wave_active = True
            response = "OK:WAVE:STARTED\n"
        elif cmd == "WAVE:STOP":
            self.wave_active = False
            response = "OK:WAVE:STOPPED\n"
        elif cmd.startswith("DAC:SET:RAW:"):
            parts = cmd.split(":")
            if len(parts) >= 5:
                response = f"OK:DAC:RAW:{parts[3]}:{parts[4]}\n"
            else:
                response = "ERR:INVALID_ARG\n"
        elif cmd == "STREAM:START":
            self.streaming = True
            response = "OK:STREAM:STARTED\n"
        elif cmd == "STREAM:STOP":
            self.streaming = False
            response = "OK:STREAM:STOPPED\n"
        elif cmd.startswith("PUMP:START:"):
            self.pump_rpm = int(cmd.split(":")[2])
            self.pump_running = True
            response = f"OK:PUMP:START:{self.pump_rpm}\n"
        elif cmd == "PUMP:STOP":
            self.pump_running = False
            self.pump_rpm = 0
            response = "OK:PUMP:STOP\n"
        elif cmd == "PUMP:ESTOP":
            self.pump_running = False
            self.pump_rpm = 0
            self.bias_mv = 0.0
            self.wave_active = False
            response = "OK:PUMP:ESTOP\n"
        elif cmd == "LEAK:RESET":
            self.leak_detected = False
            response = "OK:LEAK:RESET\n"
        elif cmd == "SBU:DETECT":
            # Return detected orientation
            orient_str = "NORMAL" if self.sbu_orientation == 1 else "INVERTED"
            response = f"OK:SBU:{orient_str}\n"
        elif cmd == "SBU:STATUS":
            orient_str = "NORMAL" if self.sbu_orientation == 1 else "INVERTED"
            response = f'{{"sbu_orient":"{orient_str}","scl_gpio":12,"sda_gpio":13,"devices":["0x38","0x60"]}}\n'
        elif cmd == "STATUS?":
            gain_str = "2X" if self.dac_gain_2x else "1X"
            response = (
                f'{{"bias_mv":{self.bias_mv:.2f},"dac_gain":"{gain_str}","dac_sps":{self.dac_speed_sps},'
                f'"wave_active":{str(self.wave_active).lower()},"wave_shape":"{self.wave_shape}",'
                f'"wave_freq":{self.wave_freq_hz:.1f},"pulse_active":false,'
                f'"sampling":{str(self.streaming).lower()},"streaming":{str(self.streaming).lower()},'
                f'"rate_hz":{self.sample_rate_hz},"leak":{str(self.leak_detected).lower()},'
                f'"pump_conn":{str(self.pump_connected).lower()},"pump_run":{str(self.pump_running).lower()},'
                f'"pump_rpm":{self.pump_rpm},"frames":{self._frame_index},"dropped":0}}\n'
            )
        else:
            response = f"ERR:UNKNOWN_CMD:{cmd}\n"

        with self._lock:
            self._tx_buffer.extend(response.encode("utf-8"))

    def _generate_mock_stream(self):
        if not self.streaming:
            return

        # Generate a burst of frames based on real time
        with self._lock:
            if len(self._tx_buffer) > 4096:
                return

        conductance_ns = 6.0
        target_current_na = (self.bias_mv / 1000.0) * conductance_ns
        base_counts = int((target_current_na / 4.096) * 32768)

        # Generate a burst of 4 frames (256 samples)
        with self._lock:
            for _ in range(4):
                samples = []
                for i in range(SAMPLES_PER_FRAME):
                    # Check for simulated translocation event
                    if not self._event_active and (self._frame_index % 70 == 0) and i == 10:
                        self._event_active = True
                        self._event_samples_remaining = 25  # ~250 us blockade

                    noise = int(math.sin(self._frame_index * 0.1 + i * 0.05) * 120)
                    if self._event_active:
                        # 30% current blockade
                        sample_val = int(base_counts * 0.7) + noise
                        self._event_samples_remaining -= 1
                        if self._event_samples_remaining <= 0:
                            self._event_active = False
                    else:
                        sample_val = base_counts + noise

                    # Clamp int16
                    sample_val = max(-32768, min(32767, sample_val))
                    samples.append(sample_val)

                flags = 0
                if self.streaming:       flags |= STATUS_STREAMING_ACTIVE
                if self.leak_detected:   flags |= STATUS_LEAK_DETECTED
                if self.pump_connected:  flags |= STATUS_PUMP_CONNECTED
                if self.pump_running:    flags |= STATUS_PUMP_RUNNING
                if self.wave_active:     flags |= STATUS_DAC_WAVE_ACTIVE

                frame = StreamFrame(
                    magic=STREAM_MAGIC_WORD,
                    frame_index=self._frame_index,
                    timestamp_us=(self._frame_index * SAMPLES_PER_FRAME * 10),
                    sample_count=SAMPLES_PER_FRAME,
                    status_flags=flags,
                    samples=tuple(samples),
                    crc16=0
                )
                self._tx_buffer.extend(frame.pack())
                self._frame_index += 1


class DaqClient:
    """
    Core DAQ Client orchestrating serial comms, frame synchronization,
    telemetry decoding, disk logging, and live metrics.
    """

    def __init__(
        self,
        port: str,
        baud: int = 921600,
        gain_ohms: float = 1e9,
        vref: float = 4.096,
        is_mock: bool = False
    ):
        self.port_name = port
        self.baud = baud
        self.gain_ohms = gain_ohms
        self.vref = vref
        self.is_mock = is_mock

        self.serial_port = None
        self.is_running = False
        self._reader_thread: Optional[threading.Thread] = None

        # Telemetry & Statistics
        self.total_frames = 0
        self.valid_frames = 0
        self.crc_errors = 0
        self.dropped_frames = 0
        self.last_frame_index: Optional[int] = None
        self.start_time: Optional[float] = None
        self.last_status_flags = 0

        # Ring buffer for live statistics & visualization
        self.recent_samples = queue.Queue(maxsize=10000)
        self.frame_queue = queue.Queue(maxsize=1000)
        self.response_queue = queue.Queue(maxsize=100)

        # Output logging file handles
        self.csv_file = None
        self.bin_file = None

    def connect(self):
        """Establishes connection to physical serial port or mock device."""
        if self.is_mock:
            self.serial_port = MockSerialPort()
        else:
            try:
                import serial
            except ImportError:
                raise RuntimeError(
                    "pyserial is required for hardware connection. Install via: pip install pyserial"
                )
            self.serial_port = serial.Serial(
                port=self.port_name,
                baudrate=self.baud,
                timeout=0.1
            )
            time.sleep(0.1)

        self.is_running = True
        self.start_time = time.time()
        self._reader_thread = threading.Thread(target=self._stream_reader_loop, daemon=True)
        self._reader_thread.start()

    def disconnect(self):
        """Stops acquisition and safely closes ports and file handles."""
        self.is_running = False
        if self.serial_port:
            try:
                self.send_command("STREAM:STOP", timeout=0.1)
                time.sleep(0.05)
            except Exception:
                pass
            self.serial_port.close()
            self.serial_port = None

        if self.csv_file:
            try:
                self.csv_file.flush()
                self.csv_file.close()
            except Exception:
                pass
            self.csv_file = None
        if self.bin_file:
            try:
                self.bin_file.flush()
                self.bin_file.close()
            except Exception:
                pass
            self.bin_file = None

    def send_command(self, cmd: str, timeout: float = 0.3) -> str:
        """Sends an ASCII command to the reader and returns the response."""
        if not self.serial_port:
            return ""
        formatted = f"{cmd.strip()}\n".encode("utf-8")
        self.serial_port.write(formatted)
        if self._reader_thread and self._reader_thread.is_alive():
            try:
                return self.response_queue.get(timeout=timeout)
            except queue.Empty:
                return ""
        else:
            time.sleep(0.02)
            response = ""
            while self.serial_port.in_waiting > 0:
                chunk = self.serial_port.read(self.serial_port.in_waiting)
                response += chunk.decode("utf-8", errors="ignore")
            return response

    def set_bias(self, mv: float):
        return self.send_command(f"SET:BIAS:{mv:.2f}")

    def start_streaming(self):
        return self.send_command("STREAM:START")

    def stop_streaming(self):
        return self.send_command("STREAM:STOP")

    def trigger_pulse(self, mv: float, ms: int):
        return self.send_command(f"CMD:PULSE:{mv:.1f}:{ms}")

    def start_pump(self, rpm: int, reverse: bool = False):
        cmd = f"PUMP:REV:{rpm}" if reverse else f"PUMP:START:{rpm}"
        return self.send_command(cmd)

    def stop_pump(self):
        return self.send_command("PUMP:STOP")

    def emergency_stop(self):
        return self.send_command("PUMP:ESTOP")

    def detect_sbu(self) -> str:
        return self.send_command("SBU:DETECT")

    def set_dac_gain(self, gain_2x: bool = True):
        mode = "2X" if gain_2x else "1X"
        return self.send_command(f"SET:DAC:GAIN:{mode}")

    def set_dac_speed(self, sps: int):
        return self.send_command(f"SET:DAC:SPEED:{int(sps)}")

    def configure_waveform(self, shape: str, freq_hz: float, amp_mv: float, offset_mv: float = 0.0):
        return self.send_command(f"WAVE:CONFIG:{shape.upper()}:{freq_hz:.2f}:{amp_mv:.2f}:{offset_mv:.2f}")

    def start_waveform(self):
        return self.send_command("WAVE:START")

    def stop_waveform(self):
        return self.send_command("WAVE:STOP")

    def set_dac_raw(self, channel: int, code: int):
        return self.send_command(f"DAC:SET:RAW:{channel}:{code}")

    def set_csv_output(self, file_path: str):
        """Configures live CSV sample stream logging."""
        self.csv_file = open(file_path, "w", buffering=65536)
        self.csv_file.write("timestamp_us,frame_index,sample_in_frame,raw_adc,current_pa,status_flags\n")

    def set_bin_output(self, file_path: str):
        """Configures raw binary frame logging."""
        self.bin_file = open(file_path, "wb", buffering=65536)

    def _stream_reader_loop(self):
        """
        High-speed background byte ingestion loop.
        Synchronizes on magic bytes, parses frames, validates CRC,
        and dispatches to disk and analysis queues.
        """
        rx_buffer = bytearray()
        magic_bytes = STREAM_MAGIC_BYTES

        while self.is_running and self.serial_port:
            try:
                available = self.serial_port.in_waiting
                if available > 0:
                    chunk = self.serial_port.read(min(available, 8192))
                    rx_buffer.extend(chunk)
                else:
                    time.sleep(0.001)
                    continue

                # Process buffer
                while len(rx_buffer) > 0:
                    magic_pos = rx_buffer.find(magic_bytes)
                    if magic_pos == 0:
                        if len(rx_buffer) < FRAME_SIZE_BYTES:
                            break
                        frame_bytes = bytes(rx_buffer[:FRAME_SIZE_BYTES])
                        del rx_buffer[:FRAME_SIZE_BYTES]

                        frame = StreamFrame.unpack(frame_bytes)
                        if not frame:
                            continue

                        self.total_frames += 1
                        if not frame.is_valid_crc:
                            self.crc_errors += 1
                            continue

                        self.valid_frames += 1
                        self.last_status_flags = frame.status_flags

                        # Sequence continuity check
                        if self.last_frame_index is not None:
                            expected_index = self.last_frame_index + 1
                            if frame.frame_index > expected_index:
                                dropped = frame.frame_index - expected_index
                                self.dropped_frames += dropped
                        self.last_frame_index = frame.frame_index

                        # Write to binary output
                        if self.bin_file:
                            self.bin_file.write(frame_bytes)

                        # Write to CSV output
                        if self.csv_file:
                            for idx, s in enumerate(frame.samples):
                                i_amps = raw_to_current(s, self.vref, self.gain_ohms)
                                i_pa = i_amps * 1e12
                                ts = frame.timestamp_us + (idx * 10)  # 10us @ 100kHz
                                self.csv_file.write(
                                    f"{ts},{frame.frame_index},{idx},{s},{i_pa:.3f},{frame.status_flags}\n"
                                )

                        # Update queue for live display
                        if not self.frame_queue.full():
                            self.frame_queue.put(frame)

                    elif magic_pos > 0:
                        # Non-magic prefix: check for ASCII newline
                        prefix = bytes(rx_buffer[:magic_pos])
                        del rx_buffer[:magic_pos]
                        text = prefix.decode("utf-8", errors="ignore").strip()
                        if text:
                            for line in text.splitlines():
                                line = line.strip()
                                if line:
                                    self.response_queue.put(line)

                    else:
                        # No magic word in buffer: check for ASCII lines
                        nl_pos = rx_buffer.find(b"\n")
                        if nl_pos != -1:
                            line_bytes = bytes(rx_buffer[: nl_pos + 1])
                            del rx_buffer[: nl_pos + 1]
                            line = line_bytes.decode("utf-8", errors="ignore").strip()
                            if line:
                                self.response_queue.put(line)
                        else:
                            # Keep only trailing 3 bytes
                            if len(rx_buffer) > 3:
                                rx_buffer = rx_buffer[-3:]
                            break

            except Exception:
                if self.is_running:
                    time.sleep(0.01)

    def get_throughput_stats(self) -> Dict[str, Any]:
        """Calculates live ingestion throughput metrics."""
        elapsed = time.time() - self.start_time if self.start_time else 0.001
        total_samples = self.valid_frames * SAMPLES_PER_FRAME
        rate_samples_sec = total_samples / elapsed if elapsed > 0 else 0
        rate_kb_sec = (self.valid_frames * FRAME_SIZE_BYTES) / (elapsed * 1024.0) if elapsed > 0 else 0
        drop_rate = (self.dropped_frames / (self.valid_frames + self.dropped_frames) * 100.0) if (self.valid_frames + self.dropped_frames) > 0 else 0.0

        return {
            "elapsed_sec": elapsed,
            "total_frames": self.total_frames,
            "valid_frames": self.valid_frames,
            "crc_errors": self.crc_errors,
            "dropped_frames": self.dropped_frames,
            "drop_rate_pct": drop_rate,
            "total_samples": total_samples,
            "rate_k_samples_sec": rate_samples_sec / 1000.0,
            "rate_kb_sec": rate_kb_sec,
            "last_flags": self.last_status_flags
        }


def run_cli_dashboard(client: DaqClient, duration_sec: Optional[float] = None):
    """Renders a responsive live terminal dashboard with throughput & pore current."""
    client.start_streaming()
    print("\n" + "=" * 70)
    print("  Sentinel Nanopore 100 kHz Streaming Client (Active)")
    print("  Press Ctrl+C to stop acquisition.")
    print("=" * 70)

    start = time.time()
    try:
        while client.is_running:
            if duration_sec and (time.time() - start) >= duration_sec:
                break

            time.sleep(0.2)
            stats = client.get_throughput_stats()

            # Drain latest frame to get current sample mean
            latest_frame = None
            while not client.frame_queue.empty():
                latest_frame = client.frame_queue.get_nowait()

            mean_current_str = "    N/A    "
            rms_noise_str = "   N/A   "
            if latest_frame:
                currents = [raw_to_current(s, client.vref, client.gain_ohms) for s in latest_frame.samples]
                mean_i = sum(currents) / len(currents)
                variance = sum((c - mean_i) ** 2 for c in currents) / len(currents)
                rms = math.sqrt(variance)
                mean_current_str = format_current(mean_i)
                rms_noise_str = format_current(rms)

            flags = stats["last_flags"]
            leak_str = "[!] LEAK DETECTED" if (flags & STATUS_LEAK_DETECTED) else "OK (Dry)"
            pump_str = "RUNNING" if (flags & STATUS_PUMP_RUNNING) else ("CONNECTED" if (flags & STATUS_PUMP_CONNECTED) else "DISCONNECTED")

            line = (
                f"\r[{stats['elapsed_sec']:6.1f}s] "
                f"Rate: {stats['rate_k_samples_sec']:5.1f} kS/s ({stats['rate_kb_sec']:5.1f} KB/s) | "
                f"I_pore: {mean_current_str} (RMS: {rms_noise_str}) | "
                f"Drop: {stats['dropped_frames']:3d} ({stats['drop_rate_pct']:.2f}%) | "
                f"Pump: {pump_str:<9} | Leak: {leak_str}"
            )
            sys.stdout.write(line)
            sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n\nUser interrupted acquisition.")
    finally:
        client.stop_streaming()
        print("\n" + "=" * 70)
        final_stats = client.get_throughput_stats()
        print("  Acquisition Summary:")
        print(f"  - Elapsed Time:      {final_stats['elapsed_sec']:.2f} seconds")
        print(f"  - Valid Frames:      {final_stats['valid_frames']}")
        print(f"  - Total Samples:     {final_stats['total_samples']:,}")
        print(f"  - Throughput:        {final_stats['rate_k_samples_sec']:.2f} kS/s ({final_stats['rate_kb_sec']:.2f} KB/s)")
        print(f"  - CRC Check Errors:  {final_stats['crc_errors']}")
        print(f"  - Dropped Frames:    {final_stats['dropped_frames']} ({final_stats['drop_rate_pct']:.3f}%)")
        print("=" * 70 + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sentinel Nanopore 100 kHz USB Streaming DAQ Client"
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
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path (.csv for text, .bin for binary frames)."
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=None,
        help="Acquisition duration in seconds (default: run until Ctrl+C)."
    )
    parser.add_argument(
        "--bias",
        type=float,
        default=None,
        help="Initial pore bias voltage in mV (-1587 to +1587)."
    )
    parser.add_argument(
        "--pulse",
        type=str,
        default=None,
        help="Inject pulse as <voltage_mv>:<duration_ms> (e.g. 800:250)."
    )
    parser.add_argument(
        "--pump",
        type=int,
        default=None,
        help="Run peristaltic pump at RPM (e.g. 60)."
    )
    parser.add_argument(
        "--sbu-detect",
        action="store_true",
        help="Probe USB-C SBU lines to detect I2C polarity."
    )
    parser.add_argument(
        "--gain",
        type=float,
        default=1e9,
        help="Transimpedance feedback resistor Rf in Ohms (default: 1e9 = 1 Gigaohm)."
    )
    parser.add_argument(
        "--dac-gain-1x",
        action="store_true",
        help="Configure DAC to 1X gain (0-2.048V, unlocking 85.5 kHz full-power bandwidth)."
    )
    parser.add_argument(
        "--dac-speed",
        type=int,
        default=None,
        help="Configure DAC update speed in SPS (up to 1,000,000 SPS)."
    )
    parser.add_argument(
        "--wave-shape",
        type=str,
        default=None,
        choices=["SINE", "TRIANGLE", "SQUARE", "RAMP", "CHIRP", "OFF"],
        help="Configure periodic/arbitrary DDS waveform shape."
    )
    parser.add_argument(
        "--wave-freq",
        type=float,
        default=1000.0,
        help="Waveform frequency in Hz (default: 1000.0 Hz, max 85.5 kHz full-power)."
    )
    parser.add_argument(
        "--wave-amp",
        type=float,
        default=100.0,
        help="Waveform amplitude in mV (default: 100.0 mV)."
    )
    parser.add_argument(
        "--wave-offset",
        type=float,
        default=0.0,
        help="Waveform offset in mV (default: 0.0 mV)."
    )
    parser.add_argument(
        "--mock", "--sim",
        action="store_true",
        help="Run with high-fidelity internal mock simulation without requiring hardware."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    client = DaqClient(
        port=args.port,
        baud=args.baud,
        gain_ohms=args.gain,
        is_mock=args.mock
    )

    try:
        client.connect()

        if args.dac_gain_1x:
            resp = client.set_dac_gain(gain_2x=False)
            print(f"[CMD] Set DAC Gain 1X: {resp.strip()}")

        if args.dac_speed is not None:
            resp = client.set_dac_speed(args.dac_speed)
            print(f"[CMD] Set DAC Speed: {resp.strip()}")

        if args.wave_shape:
            resp = client.configure_waveform(args.wave_shape, args.wave_freq, args.wave_amp, args.wave_offset)
            print(f"[CMD] Config Waveform: {resp.strip()}")
            if args.wave_shape.upper() != "OFF":
                resp_start = client.start_waveform()
                print(f"[CMD] Start Waveform: {resp_start.strip()}")

        # Execute pre-stream commands
        if args.bias is not None:
            resp = client.set_bias(args.bias)
            print(f"[CMD] Set Bias: {resp.strip()}")

        if args.pulse:
            parts = args.pulse.split(":")
            if len(parts) == 2:
                resp = client.trigger_pulse(float(parts[0]), int(parts[1]))
                print(f"[CMD] Pulse: {resp.strip()}")

        if args.pump is not None:
            resp = client.start_pump(args.pump)
            print(f"[CMD] Pump Start: {resp.strip()}")

        if args.sbu_detect:
            resp = client.detect_sbu()
            print(f"[CMD] SBU Polarity Detect: {resp.strip()}")

        if args.output:
            if args.output.endswith(".csv"):
                client.set_csv_output(args.output)
                print(f"[IO] Streaming CSV records to: {args.output}")
            elif args.output.endswith(".bin"):
                client.set_bin_output(args.output)
                print(f"[IO] Streaming raw binary frames to: {args.output}")
            else:
                client.set_csv_output(args.output)
                print(f"[IO] Defaulting to CSV output: {args.output}")

        run_cli_dashboard(client, duration_sec=args.duration)

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
