/**
 * @file dac_mcp4822.cpp
 * @brief Implementation of High-Throughput MCP4822 Dual 12-Bit SPI DAC Driver
 */

#include "dac_mcp4822.h"
#include <math.h>

DacMCP4822 Dac;

DacMCP4822::DacMCP4822() 
    : _current_bias_mv(0.0f)
    , _pre_pulse_bias_mv(0.0f)
    , _pulse_active(false)
    , _pulse_end_time(0)
    , _gain_2x(true)
    , _update_rate_sps(DAC_DEFAULT_UPDATE_RATE_SPS)
    , _wave_active(false)
    , _wave_shape(WAVE_SHAPE_OFF)
    , _wave_freq_hz(1000.0f)
    , _wave_amp_mv(100.0f)
    , _wave_offset_mv(0.0f)
    , _wave_lut_index(0)
    , _wave_step_accumulator(0)
    , _wave_step_phase_increment(0)
    , _last_service_time_us(0)
    , _spi(nullptr)
    , _spi_settings(DAC_SPI_CLOCK_HZ, MSBFIRST, SPI_MODE0) {
    memset(_lut, 0, sizeof(_lut));
}

void DacMCP4822::begin() {
    pinMode(PIN_DAC_CS, OUTPUT);
    pinMode(PIN_DAC_LDAC, OUTPUT);
    digitalWrite(PIN_DAC_CS, HIGH);

    // Tie LDAC permanently LOW: register latches immediately on rising edge of CS
    // eliminating separate latch pulse delay (t_LD >= 100ns) and blocking microsecond delays
    digitalWrite(PIN_DAC_LDAC, LOW);

    // Initialize custom SPI instance for DAC on Ignition sheet pins at 20 MHz
    _spi = new SPIClass(HSPI);
    _spi->begin(PIN_DAC_SCK, -1, PIN_DAC_SDI, PIN_DAC_CS);

    // Pre-activate SPI transaction settings for zero-overhead continuous burst writes
    _spi->beginTransaction(_spi_settings);

    // Initialize to midscale (0.0 mV pore bias)
    set_voltage_mv(0.0f);
}

void DacMCP4822::set_gain_mode(bool gain_2x) {
    _gain_2x = gain_2x;
    if (_wave_active) {
        rebuild_lut();
    }
    set_voltage_mv(_current_bias_mv);
}

void DacMCP4822::set_update_rate_sps(uint32_t sps) {
    if (sps < 1000) sps = 1000;
    if (sps > DAC_MAX_UPDATE_RATE_SPS) sps = DAC_MAX_UPDATE_RATE_SPS;
    _update_rate_sps = sps;
    if (_wave_active) {
        // Recompute phase increment: (freq / sps) * 2^32
        _wave_step_phase_increment = (uint32_t)(((double)_wave_freq_hz / (double)_update_rate_sps) * 4294967296.0);
    }
}

float DacMCP4822::set_voltage_mv(float mv) {
    float min_mv = _gain_2x ? BIAS_MIN_MV : BIAS_MIN_1X_MV;
    float max_mv = _gain_2x ? BIAS_MAX_MV : BIAS_MAX_1X_MV;

    if (mv < min_mv) mv = min_mv;
    if (mv > max_mv) mv = max_mv;

    _current_bias_mv = mv;

    // Linear mapping:
    // min_mv -> Code 0
    // 0.0 mV -> Code 2048
    // max_mv -> Code 4095
    float norm = (mv - min_mv) / (max_mv - min_mv);
    int code = (int)(norm * 4095.0f + 0.5f);
    if (code < 0) code = 0;
    if (code > 4095) code = 4095;

    // Write to Channel A (0)
    set_raw(0, (uint16_t)code, _gain_2x);
    return _current_bias_mv;
}

void DacMCP4822::set_raw(uint8_t channel, uint16_t code, bool gain_2x) {
    if (!_spi) return;

    code &= 0x0FFF; // 12-bit mask

    // Bit 15: 0=A, 1=B
    // Bit 14: 0
    // Bit 13: 0=2x gain (0-4.096V), 1=1x gain (0-2.048V)
    // Bit 12: 1=active, 0=shutdown
    // Bits 11-0: data
    uint16_t packet = code;
    if (channel != 0) packet |= (1 << 15);
    if (!gain_2x)     packet |= (1 << 13);
    packet |= (1 << 12); // Active output

    // Ultra-fast write (< 850 ns transfer at 20 MHz SPI)
    set_raw_fast(packet);
}

void DacMCP4822::rebuild_lut() {
    float min_mv = _gain_2x ? BIAS_MIN_MV : BIAS_MIN_1X_MV;
    float max_mv = _gain_2x ? BIAS_MAX_MV : BIAS_MAX_1X_MV;

    for (int i = 0; i < DAC_WAVE_LUT_SIZE; i++) {
        float phase = (2.0f * M_PI * i) / (float)DAC_WAVE_LUT_SIZE;
        float v_inst = _wave_offset_mv;

        switch (_wave_shape) {
            case WAVE_SHAPE_SINE:
                v_inst += _wave_amp_mv * sinf(phase);
                break;
            case WAVE_SHAPE_TRIANGLE: {
                float norm_phase = (float)i / (float)DAC_WAVE_LUT_SIZE;
                if (norm_phase < 0.25f) {
                    v_inst += _wave_amp_mv * (norm_phase * 4.0f);
                } else if (norm_phase < 0.75f) {
                    v_inst += _wave_amp_mv * (1.0f - (norm_phase - 0.25f) * 4.0f);
                } else {
                    v_inst += _wave_amp_mv * (-1.0f + (norm_phase - 0.75f) * 4.0f);
                }
                break;
            }
            case WAVE_SHAPE_SQUARE:
                v_inst += (i < DAC_WAVE_LUT_SIZE / 2) ? _wave_amp_mv : -_wave_amp_mv;
                break;
            case WAVE_SHAPE_RAMP:
                v_inst += _wave_amp_mv * (-1.0f + 2.0f * ((float)i / (float)DAC_WAVE_LUT_SIZE));
                break;
            default:
                v_inst = _current_bias_mv;
                break;
        }

        // Clamp to allowable voltage span
        if (v_inst < min_mv) v_inst = min_mv;
        if (v_inst > max_mv) v_inst = max_mv;

        float norm = (v_inst - min_mv) / (max_mv - min_mv);
        int code = (int)(norm * 4095.0f + 0.5f);
        if (code < 0) code = 0;
        if (code > 4095) code = 4095;

        uint16_t packet = (uint16_t)code & 0x0FFF;
        if (!_gain_2x) packet |= (1 << 13);
        packet |= (1 << 12); // Active
        _lut[i] = packet;
    }
}

void DacMCP4822::configure_waveform(DacWaveformShape shape, float freq_hz, float amp_mv, float offset_mv) {
    _wave_shape = shape;
    _wave_freq_hz = freq_hz;
    _wave_amp_mv = amp_mv;
    _wave_offset_mv = offset_mv;

    // Automatic gain optimization: if amplitude + offset fits within 1x mode, use 1x to double slew bandwidth
    if (fabsf(offset_mv) + fabsf(amp_mv) <= fabsf(BIAS_MAX_1X_MV)) {
        _gain_2x = false;
    }

    _wave_step_phase_increment = (uint32_t)(((double)_wave_freq_hz / (double)_update_rate_sps) * 4294967296.0);
    rebuild_lut();
}

void DacMCP4822::start_waveform() {
    if (_wave_shape == WAVE_SHAPE_OFF) {
        _wave_shape = WAVE_SHAPE_SINE;
        configure_waveform(_wave_shape, _wave_freq_hz, _wave_amp_mv, _wave_offset_mv);
    }
    _wave_step_accumulator = 0;
    _wave_active = true;
}

void DacMCP4822::stop_waveform() {
    _wave_active = false;
    set_voltage_mv(_current_bias_mv);
}

void DacMCP4822::service_waveform() {
    if (!_wave_active || !_spi) return;

    // Output current sample from LUT
    uint8_t index = (uint8_t)(_wave_step_accumulator >> 24); // 8 MSBs for 256-entry table
    set_raw_fast(_lut[index]);

    // Advance phase
    _wave_step_accumulator += _wave_step_phase_increment;
}

void DacMCP4822::inject_pulse(float pulse_mv, uint32_t duration_ms) {
    if (!_pulse_active) {
        _pre_pulse_bias_mv = _current_bias_mv;
    }
    _pulse_active = true;
    _pulse_end_time = millis() + duration_ms;
    set_voltage_mv(pulse_mv);
}

void DacMCP4822::update() {
    if (_pulse_active && (long)(millis() - _pulse_end_time) >= 0) {
        _pulse_active = false;
        set_voltage_mv(_pre_pulse_bias_mv);
    }

    if (_wave_active) {
        service_waveform();
    }
}

void DacMCP4822::emergency_zero() {
    _pulse_active = false;
    _wave_active = false;
    set_voltage_mv(0.0f);
}
