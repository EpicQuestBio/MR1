/**
 * @file dac_mcp4822.h
 * @brief MCP4822 Dual 12-Bit SPI DAC Driver with Pore Bias Scaling
 */

#pragma once

#include <Arduino.h>
#include <SPI.h>
#include "pinout.h"
#include "config.h"

class DacMCP4822 {
public:
    DacMCP4822();

    /**
     * @brief Initialize SPI bus and GPIO control lines
     */
    void begin();

    /**
     * @brief Set pore bias potential in millivolts (-1587.0mV to +1587.0mV)
     * @param mv Target bias voltage in millivolts
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
    float    _current_bias_mv;
    float    _pre_pulse_bias_mv;
    bool     _pulse_active;
    uint32_t _pulse_end_time;
    SPIClass* _spi;
};

extern DacMCP4822 Dac;
