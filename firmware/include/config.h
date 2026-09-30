/**
 * @file config.h
 * @brief Global Firmware Configuration Constants
 */

#pragma once

#include <stdint.h>

// =============================================================================
// Sampling & Acquisition Constants
// =============================================================================
#define DEFAULT_SAMPLE_RATE_HZ     100000   // 100 kHz continuous throughput
#define MAX_SAMPLE_RATE_HZ         100000
#define MIN_SAMPLE_RATE_HZ           1000
#define ADC_TIMER_PERIOD_US            10   // 10 microseconds @ 100 kHz

#define SAMPLES_PER_FRAME              64   // Binary packet payload size
#define RING_BUFFER_FRAME_COUNT        32   // Ring buffer capacity (2048 samples)

// =============================================================================
// Bias & Voltage Range Constants
// =============================================================================
#define DAC_VREF_MV               4096.0f   // MCP4822 internal 2x reference (4.096V)
#define BIAS_MIN_MV              -1587.0f   // Minimum controllable pore bias
#define BIAS_MAX_MV               1587.0f   // Maximum controllable pore bias
#define BIAS_CAL_SLOPE              1.00f   // Calibration correction factor
#define BIAS_CAL_OFFSET_MV          0.00f

// Pulse Injection Defaults
#define DEFAULT_PULSE_VOLTAGE_MV   800.0f
#define DEFAULT_PULSE_DURATION_MS   250

// =============================================================================
// Pump Communication
// =============================================================================
#define PUMP_BAUD_RATE             115200
#define PUMP_HEARTBEAT_INTERVAL_MS   1000
#define PUMP_TIMEOUT_MS              3000

// =============================================================================
// Wi-Fi & Web Portal
// =============================================================================
#define WIFI_AP_SSID               "Sentinel-Nanopore"
#define WIFI_AP_PASS               "nanopore123"
#define WEB_PORTAL_PORT                80
#define WEBSOCKET_DECIMATION_FACTOR   100   // Downsample 100 kHz -> 1 kHz for UI

// =============================================================================
// Safety Thresholds
// =============================================================================
#define LEAK_DEBOUNCE_MS               10   // Minimum trip duration to trigger cutoff

// =============================================================================
// USB-C SBU & I2C Auto-Polarity Configuration
// =============================================================================
#define I2C_SBU_FREQUENCY_HZ       100000   // Standard-mode 100 kHz I2C
#define I2C_TARGET_PUMP_ADDR         0x38   // Default pump controller / GPIO expander
#define I2C_TARGET_MOTOR_ADDR        0x60   // Alternate stepper / DC motor driver
#define I2C_TARGET_SENSOR_ADDR       0x48   // Pressure / temperature sensor
#define SBU_PROBE_TIMEOUT_MS           50   // I2C probe timeout
