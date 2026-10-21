/*
 * Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
 * Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
 * SPDX-License-Identifier: CC0-1.0
 */

/**
 * @file dac_mcp4822.h
 * @brief MCP4822 Dual 12-Bit SPI DAC Driver with High-Throughput Waveform Synthesis
 */

#pragma once

#include <Arduino.h>
#include <SPI.h>
#include "pinout.h"
#include "config.h"
#include "protocol.h"

class DacMCP4822 {
public:
    DacMCP4822();

    /**
     * @brief Initialize 20 MHz SPI bus and tie LDAC low for instantaneous CS-rising update
     */
    void begin();

    /**
     * @brief Set pore bias potential in millivolts
     * @param mv Target bias voltage in millivolts (-1587 to +1587 in 2x mode, -793.5 to +793.5 in 1x mode)
     * @return Applied voltage in millivolts
     */
    float set_voltage_mv(float mv);

    /**
     * @brief Set raw 12-bit code (0 - 4095) to specified DAC channel
     * @param channel 0 for Channel A (Bias), 1 for Channel B (Aux/Offset)
     * @param code 12-bit value
     * @param gain_2x If true, output range is 0-4.096V (gain=2x), else 0-2.048V (gain=1x)
     */
    void set_raw(uint8_t channel, uint16_t code, bool gain_2x = true);

    /**
     * @brief Ultra-fast raw 16-bit packet transfer (< 850 ns at 20 MHz SPI)
     * Assumes LDAC is permanently tied low and SPISettings are active.
     */
    inline void set_raw_fast(uint16_t packet) {
        digitalWrite(PIN_DAC_CS, LOW);
        _spi->transfer16(packet);
        digitalWrite(PIN_DAC_CS, HIGH);
    }

    /**
     * @brief Configure Gain Mode (1x vs 2x)
     * 1x mode doubles large-signal full-power bandwidth to 85.5 kHz against 0.55 V/us slew rate limit.
     */
    void set_gain_mode(bool gain_2x);
    bool is_gain_2x() const { return _gain_2x; }

    /**
     * @brief Configure update rate in SPS (up to 1,000,000 SPS)
     */
    void set_update_rate_sps(uint32_t sps);
    uint32_t get_update_rate_sps() const { return _update_rate_sps; }

    /**
     * @brief Configure arbitrary/periodic waveform synthesis
     * @param shape Waveform shape (SINE, TRIANGLE, SQUARE, RAMP, CHIRP)
     * @param freq_hz Frequency in Hz (up to 85.5 kHz full-power, or 200 kHz Nyquist)
     * @param amp_mv Amplitude in millivolts
     * @param offset_mv Offset in millivolts
     */
    void configure_waveform(DacWaveformShape shape, float freq_hz, float amp_mv, float offset_mv = 0.0f);

    /**
     * @brief Start or stop high-throughput waveform synthesis
     */
    void start_waveform();
    void stop_waveform();
    bool is_waveform_active() const { return _wave_active; }

    DacWaveformShape get_waveform_shape() const { return _wave_shape; }
    float get_waveform_freq_hz() const { return _wave_freq_hz; }
    float get_waveform_amp_mv() const { return _wave_amp_mv; }
    float get_waveform_offset_mv() const { return _wave_offset_mv; }

    /**
     * @brief Service waveform generation step (called from real-time loop)
     */
    void service_waveform();

    /**
     * @brief Inject a temporary high-voltage pulse for pore wetting / unclogging
     * @param pulse_mv Pulse amplitude in millivolts
     * @param duration_ms Duration in milliseconds
     */
    void inject_pulse(float pulse_mv, uint32_t duration_ms);

    /**
     * @brief Service pulse timer. Call periodically from Core 0 loop.
     */
    void update();

    /**
     * @brief Immediately zero the pore bias (e.g. on emergency stop or leak)
     */
    void emergency_zero();

    /**
     * @brief Check if a voltage pulse is currently active
     */
    bool is_pulse_active() const { return _pulse_active; }

    /**
     * @brief Get current pore bias setting in millivolts
     */
    float get_current_bias_mv() const { return _current_bias_mv; }

private:
    void rebuild_lut();

    float            _current_bias_mv;
    float            _pre_pulse_bias_mv;
    bool             _pulse_active;
    uint32_t         _pulse_end_time;
    bool             _gain_2x;
    uint32_t         _update_rate_sps;

    // Waveform generator state
    bool             _wave_active;
    DacWaveformShape _wave_shape;
    float            _wave_freq_hz;
    float            _wave_amp_mv;
    float            _wave_offset_mv;
    uint32_t         _wave_lut_index;
    uint32_t         _wave_step_accumulator;
    uint32_t         _wave_step_phase_increment;
    uint16_t         _lut[DAC_WAVE_LUT_SIZE];
    uint32_t         _last_service_time_us;

    SPIClass*        _spi;
    SPISettings      _spi_settings;
};

extern DacMCP4822 Dac;
