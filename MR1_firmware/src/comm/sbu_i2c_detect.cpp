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

/**
 * @file sbu_i2c_detect.cpp
 * @brief Implementation of USB-C SBU Auto-Orientation & I2C Polarity Detection
 */

#include "sbu_i2c_detect.h"

SbuI2cDetector SbuDetector;

SbuI2cDetector::SbuI2cDetector()
    : _orientation(SBU_ORIENT_UNKNOWN)
    , _scl_pin(-1)
    , _sda_pin(-1)
    , _initialized(false) {
}

void SbuI2cDetector::begin() {
    // Configure SBU pins with internal weak pull-ups for line stabilization
    pinMode(PIN_USB_SBU1, INPUT_PULLUP);
    pinMode(PIN_USB_SBU2, INPUT_PULLUP);

#ifdef PIN_SBU_MUX_SEL
    pinMode(PIN_SBU_MUX_SEL, OUTPUT);
    digitalWrite(PIN_SBU_MUX_SEL, LOW);
#endif

    _initialized = true;
    _orientation = SBU_ORIENT_UNKNOWN;
}

bool SbuI2cDetector::probe_configuration(int sda_pin, int scl_pin, uint8_t probe_addr) {
    Wire.end();
    delay(5);

    // Initialize Wire on probed GPIO assignments
    Wire.begin(sda_pin, scl_pin, (uint32_t)I2C_SBU_FREQUENCY_HZ);
    Wire.setTimeOut(SBU_PROBE_TIMEOUT_MS);

    // Test primary address
    Wire.beginTransmission(probe_addr);
    uint8_t err = Wire.endTransmission();
    if (err == 0) {
        return true;
    }

    // Try alternate targets if primary didn't answer
    uint8_t alternate_targets[] = {I2C_TARGET_MOTOR_ADDR, I2C_TARGET_SENSOR_ADDR};
    for (uint8_t alt_addr : alternate_targets) {
        Wire.beginTransmission(alt_addr);
        if (Wire.endTransmission() == 0) {
            return true;
        }
    }

    return false;
}

SbuOrientation SbuI2cDetector::detect_orientation(uint8_t probe_addr) {
    if (!_initialized) {
        begin();
    }

    // --- Test Orientation 1 (Normal): SBU1 = SCL, SBU2 = SDA ---
    if (probe_configuration(PIN_USB_SBU2, PIN_USB_SBU1, probe_addr)) {
        _orientation = SBU_ORIENT_NORMAL;
        _sda_pin = PIN_USB_SBU2;
        _scl_pin = PIN_USB_SBU1;
#ifdef PIN_SBU_MUX_SEL
        digitalWrite(PIN_SBU_MUX_SEL, LOW);
#endif
        return _orientation;
    }

    // --- Test Orientation 2 (Inverted / 180 deg flipped): SBU1 = SDA, SBU2 = SCL ---
    if (probe_configuration(PIN_USB_SBU1, PIN_USB_SBU2, probe_addr)) {
        _orientation = SBU_ORIENT_INVERTED;
        _sda_pin = PIN_USB_SBU1;
        _scl_pin = PIN_USB_SBU2;
#ifdef PIN_SBU_MUX_SEL
        digitalWrite(PIN_SBU_MUX_SEL, HIGH);
#endif
        return _orientation;
    }

    // Both orientations failed to communicate
    Wire.end();
    _orientation = SBU_ORIENT_DISCONNECTED;
    _scl_pin = -1;
    _sda_pin = -1;
    return _orientation;
}

const char* SbuI2cDetector::get_orientation_str() const {
    switch (_orientation) {
        case SBU_ORIENT_NORMAL:       return "NORMAL";
        case SBU_ORIENT_INVERTED:     return "INVERTED";
        case SBU_ORIENT_DISCONNECTED: return "DISCONNECTED";
        default:                      return "UNKNOWN";
    }
}

std::vector<uint8_t> SbuI2cDetector::scan_bus() {
    std::vector<uint8_t> found;
    if (!is_connected()) {
        return found;
    }

    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            found.push_back(addr);
        }
    }
    return found;
}

void SbuI2cDetector::reset() {
    Wire.end();
    _orientation = SBU_ORIENT_UNKNOWN;
    _scl_pin = -1;
    _sda_pin = -1;
}
