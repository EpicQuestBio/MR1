/*
 * Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
 * Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
 * SPDX-License-Identifier: CC0-1.0
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
