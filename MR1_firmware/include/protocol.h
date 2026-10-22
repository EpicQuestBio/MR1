/*
 * Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
 * Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
 * SPDX-License-Identifier: CC0-1.0
 */

/**
 * @file protocol.h
 * @brief High-Throughput Binary Streaming and Control Protocol Definitions
 */

#pragma once

#include <stdint.h>
#include "config.h"

#pragma pack(push, 1)

/**
 * @brief 4-byte Magic Word for Frame Synchronization: "SENT" (0x53454E54)
 */
#define STREAM_MAGIC_WORD 0x53454E54

/**
 * @brief Status Flag Bitmasks
 */
enum SystemStatusFlags : uint16_t {
    STATUS_STREAMING_ACTIVE = (1 << 0),
    STATUS_LEAK_DETECTED    = (1 << 1),
    STATUS_PUMP_CONNECTED   = (1 << 2),
    STATUS_PUMP_RUNNING     = (1 << 3),
    STATUS_PUMP_EMERGENCY   = (1 << 4),
    STATUS_DAC_PULSE_ACTIVE = (1 << 5),
    STATUS_DAC_WAVE_ACTIVE  = (1 << 6)
};

/**
 * @brief DAC Waveform Synthesis Types
 */
enum DacWaveformShape : uint8_t {
    WAVE_SHAPE_OFF      = 0,
    WAVE_SHAPE_SINE     = 1,
    WAVE_SHAPE_TRIANGLE = 2,
    WAVE_SHAPE_SQUARE   = 3,
    WAVE_SHAPE_RAMP     = 4,
    WAVE_SHAPE_CHIRP    = 5
};

/**
 * @brief Binary Telemetry Frame Header and Payload
 */
struct StreamFrame {
    uint32_t magic;                              // "SENT" sync word
    uint32_t frame_index;                        // Incremental sequence counter
    uint32_t timestamp_us;                       // Microsecond hardware timestamp
    uint16_t sample_count;                       // Number of samples in this frame (default 64)
    uint16_t status_flags;                       // System status flags bitmask
    int16_t  samples[SAMPLES_PER_FRAME];         // Differential raw ADC samples
    uint16_t crc16;                              // CRC-16-CCITT integrity checksum
};

/**
 * @brief Pump Command Packet Structure (over J22 UART)
 */
struct PumpPacket {
    uint8_t  sof;        // Start of frame (0xAA)
    uint8_t  cmd;        // Command ID (0x01: Run, 0x02: Stop, 0x03: SetSpeed, 0xFF: Emergency Stop)
    uint16_t param;      // Parameter (RPM / flow rate / direction)
    uint8_t  checksum;   // XOR checksum
};

#pragma pack(pop)

/**
 * @brief Compute CRC-16-CCITT for StreamFrame integrity check
 */
inline uint16_t calculate_crc16(const uint8_t* data, size_t length) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < length; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc = (crc << 1);
            }
        }
    }
    return crc;
}
