/*
 * Copyright (C) 2026 Lawrence R. Kincheloe III / Molecular Reality Corp
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#pragma once
#include <stdint.h>

/**
 * MR1 Pump Controller - System Configuration & Safety Limits
 */

// Firmware Identification
#define PUMP_FW_VERSION_MAJOR   1
#define PUMP_FW_VERSION_MINOR   0
#define PUMP_FW_VERSION_PATCH   0

// I2C Device Addresses
#define I2C_ADDR_ABP2_CIS       0x28    // Honeywell ABP2 Cis Feedline (0..15 psi)
#define I2C_ADDR_ABP2_TRANS     0x38    // Honeywell ABP2 Trans Recirculation (0..5 psi)
#define I2C_ADDR_STUSB4500      0x28    // STUSB4500 USB-PD controller (alternate or bus shared)

// Fluidic Safety Thresholds
#define MAX_PRESSURE_CIS_PSI    10.0f   // Safety trip limit on Cis chamber (psi)
#define MAX_PRESSURE_TRANS_PSI  4.0f    // Safety trip limit on Trans chamber (psi)
#define PRESSURE_BURST_MBAR     750.0f  // Absolute maximum allowable pressure head

// Peristaltic Pump Flow Rate Calibrations (Ditao 1/8" ID silicone tubing)
#define UL_PER_REVOLUTION       45.0f   // Nominal displacement per motor shaft rev (uL)
#define MOTOR_PWM_FREQUENCY_HZ  20000   // 20 kHz ultrasonic PWM (silent operation)
#define MOTOR_PWM_RESOLUTION    12      // 12-bit PWM resolution (0..4095)
#define MAX_FLOW_RATE_UL_MIN    150.0f  // Maximum allowable flow rate
#define MIN_FLOW_RATE_UL_MIN    0.5f    // Minimum steady flow rate

// Hardware Watchdog & Sampling Timing
#define PRESSURE_SAMPLE_RATE_HZ 100     // 100 Hz pressure loop
#define TELEMETRY_BROADCAST_HZ  20      // 20 Hz SBU telemetry rate
#define WATCHDOG_TIMEOUT_MS     500     // Comms loss timeout
