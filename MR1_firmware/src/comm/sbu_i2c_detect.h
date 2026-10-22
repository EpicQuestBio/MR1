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
 * @file sbu_i2c_detect.h
 * @brief USB-C Sideband Use (SBU) Auto-Orientation & I2C Polarity Detection
 * 
 * Automatically identifies clock (SCL) and data (SDA) lines on SBU1/SBU2
 * pins regardless of whether the USB-C cable is inserted normally or flipped 180 degrees.
 */

#pragma once

#include <Arduino.h>
#include <Wire.h>
#include <vector>
#include "pinout.h"
#include "config.h"

enum SbuOrientation : uint8_t {
    SBU_ORIENT_UNKNOWN      = 0,
    SBU_ORIENT_NORMAL       = 1, // SBU1 = SCL, SBU2 = SDA
    SBU_ORIENT_INVERTED     = 2, // SBU1 = SDA, SBU2 = SCL (Flipped 180 deg)
    SBU_ORIENT_DISCONNECTED = 3  // No responsive I2C peripheral detected
};

class SbuI2cDetector {
public:
    SbuI2cDetector();

    /**
     * @brief Configures SBU GPIO pins and prepares detection engine.
     */
    void begin();

    /**
     * @brief Probes SBU lines by attempting I2C communication on test addresses.
     * Automatically assigns ESP32-S3 internal GPIO matrix SCL and SDA routing.
     * @param probe_addr Primary I2C peripheral address to test (default 0x38).
     * @return SbuOrientation Detected cable orientation.
     */
    SbuOrientation detect_orientation(uint8_t probe_addr = I2C_TARGET_PUMP_ADDR);

    /**
     * @brief Gets current orientation state.
     */
    SbuOrientation get_orientation() const { return _orientation; }

    /**
     * @brief Gets string description ("NORMAL", "INVERTED", "DISCONNECTED", "UNKNOWN").
     */
    const char* get_orientation_str() const;

    /**
     * @brief Gets active SCL GPIO pin assignment.
     */
    int get_scl_pin() const { return _scl_pin; }

    /**
     * @brief Gets active SDA GPIO pin assignment.
     */
    int get_sda_pin() const { return _sda_pin; }

    /**
     * @brief True if an I2C device is active and communicating over SBU.
     */
    bool is_connected() const {
        return (_orientation == SBU_ORIENT_NORMAL || _orientation == SBU_ORIENT_INVERTED);
    }

    /**
     * @brief Scans active I2C bus (0x01 to 0x7F) and returns responding addresses.
     */
    std::vector<uint8_t> scan_bus();

    /**
     * @brief Resets detector and releases I2C peripheral.
     */
    void reset();

private:
    bool probe_configuration(int sda_pin, int scl_pin, uint8_t probe_addr);

    SbuOrientation _orientation;
    int _scl_pin;
    int _sda_pin;
    bool _initialized;
};

extern SbuI2cDetector SbuDetector;
