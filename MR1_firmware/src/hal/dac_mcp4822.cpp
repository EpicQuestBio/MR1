/**
 * @file dac_mcp4822.cpp
 * @brief Implementation of MCP4822 Dual 12-Bit SPI DAC Driver
 */

#include "dac_mcp4822.h"

DacMCP4822 Dac;

DacMCP4822::DacMCP4822() 
    : _current_bias_mv(0.0f)
    , _pre_pulse_bias_mv(0.0f)
    , _pulse_active(false)
    , _pulse_end_time(0)
    , _spi(nullptr) {
}

void DacMCP4822::begin() {
    pinMode(PIN_DAC_CS, OUTPUT);
    pinMode(PIN_DAC_LDAC, OUTPUT);
    digitalWrite(PIN_DAC_CS, HIGH);
    digitalWrite(PIN_DAC_LDAC, HIGH);

    // Initialize custom SPI instance for DAC on Ignition sheet pins
    _spi = new SPIClass(HSPI);
    _spi->begin(PIN_DAC_SCK, -1, PIN_DAC_SDI, PIN_DAC_CS);

    // Initialize to midscale (0.0 mV pore bias)
    set_voltage_mv(0.0f);
}

float DacMCP4822::set_voltage_mv(float mv) {
    if (mv < BIAS_MIN_MV) mv = BIAS_MIN_MV;
    if (mv > BIAS_MAX_MV) mv = BIAS_MAX_MV;

    _current_bias_mv = mv;

    // Linear mapping:
    // -1587.0 mV -> Code 0
    //     0.0 mV -> Code 2048
    // +1587.0 mV -> Code 4095
    float norm = (mv - BIAS_MIN_MV) / (BIAS_MAX_MV - BIAS_MIN_MV);
    int code = (int)(norm * 4095.0f + 0.5f);
    if (code < 0) code = 0;
    if (code > 4095) code = 4095;

    // Write to Channel A (0) with 2x gain
    set_raw(0, (uint16_t)code, true);
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
    if (!gain_2x)    packet |= (1 << 13);
    packet |= (1 << 12); // Active output

    _spi->beginTransaction(SPISettings(20000000, MSBFIRST, SPI_MODE0));
    digitalWrite(PIN_DAC_CS, LOW);
    _spi->transfer16(packet);
    digitalWrite(PIN_DAC_CS, HIGH);
    _spi->endTransaction();

    // Pulse LDAC to latch DAC output register synchronously
    digitalWrite(PIN_DAC_LDAC, LOW);
    delayMicroseconds(1);
    digitalWrite(PIN_DAC_LDAC, HIGH);
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
}

void DacMCP4822::emergency_zero() {
    _pulse_active = false;
    set_voltage_mv(0.0f);
}
