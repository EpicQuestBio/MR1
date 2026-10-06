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
// Bias & Voltage Range Constants (MCP4822 High-Throughput DAC)
// =============================================================================
#define DAC_SPI_CLOCK_HZ          20000000  // 20 MHz rated maximum SPI clock
#define DAC_MAX_UPDATE_RATE_SPS   1000000   // 1.0 MSPS theoretical single-channel burst limit
#define DAC_DEFAULT_UPDATE_RATE_SPS 200000  // 200 kSPS small-signal settling rate (4.5us resolving)
#define DAC_MAX_FULL_POWER_FREQ_HZ   85480  // 85.5 kHz full-power bandwidth at 1x gain (0.55 V/us slew)
#define DAC_WAVE_LUT_SIZE             256   // Precomputed 256-sample DDS waveform lookup table

#define DAC_VREF_1X_MV            2048.0f   // MCP4822 internal 1x reference (0 to 2.048V, doubles BW)
#define DAC_VREF_2X_MV            4096.0f   // MCP4822 internal 2x reference (0 to 4.096V)
#define DAC_VREF_MV               4096.0f   // Default reference
#define BIAS_MIN_MV              -1587.0f   // Minimum controllable pore bias (2x mode)
#define BIAS_MAX_MV               1587.0f   // Maximum controllable pore bias (2x mode)
#define BIAS_MIN_1X_MV            -793.5f   // Minimum controllable pore bias (1x mode)
#define BIAS_MAX_1X_MV             793.5f   // Maximum controllable pore bias (1x mode)
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
