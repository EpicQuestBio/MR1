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
#include <Arduino.h>
#include <Wire.h>

/**
 * Honeywell TruStability ABP2 Series Digital Pressure Transducer Driver
 * Supports 24-bit SPI/I2C digital readouts with temperature compensation.
 */
class ABP2Sensor {
public:
    enum Status {
        STATUS_OK = 0,
        STATUS_BUSY = 1,
        STATUS_MEMORY_ERROR = 2,
        STATUS_MATH_ERROR = 3,
        STATUS_COMM_ERROR = 4
    };

    ABP2Sensor(TwoWire& wire, uint8_t i2c_addr, float p_min_psi, float p_max_psi);

    bool begin();
    Status read();

    float getPressurePsi() const { return pressure_psi_ - tare_offset_psi_; }
    float getPressureMbar() const { return getPressurePsi() * 68.9476f; }
    float getRawPressurePsi() const { return pressure_psi_; }
    float getTemperatureC() const { return temperature_c_; }
    Status getStatus() const { return last_status_; }

    void tare() { tare_offset_psi_ = pressure_psi_; }
    void resetTare() { tare_offset_psi_ = 0.0f; }

private:
    TwoWire& wire_;
    uint8_t addr_;
    float p_min_;
    float p_max_;
    float pressure_psi_;
    float temperature_c_;
    float tare_offset_psi_;
    Status last_status_;

    static constexpr uint32_t OUTPUT_MIN = 1677722;   // 10% of 2^24
    static constexpr uint32_t OUTPUT_MAX = 15099494;  // 90% of 2^24
};
