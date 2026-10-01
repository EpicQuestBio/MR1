#include "abp2_pressure.h"

ABP2Sensor::ABP2Sensor(TwoWire& wire, uint8_t i2c_addr, float p_min_psi, float p_max_psi)
    : wire_(wire), addr_(i2c_addr), p_min_(p_min_psi), p_max_(p_max_psi),
      pressure_psi_(0.0f), temperature_c_(25.0f), tare_offset_psi_(0.0f),
      last_status_(STATUS_COMM_ERROR) {}

bool ABP2Sensor::begin() {
    wire_.beginTransmission(addr_);
    uint8_t err = wire_.endTransmission();
    if (err == 0) {
        last_status_ = STATUS_OK;
        return true;
    }
    last_status_ = STATUS_COMM_ERROR;
    return false;
}

ABP2Sensor::Status ABP2Sensor::read() {
    // Honeywell ABP2 trigger measurement command: 0xAA 0x00 0x00
    wire_.beginTransmission(addr_);
    wire_.write(0xAA);
    wire_.write(0x00);
    wire_.write(0x00);
    if (wire_.endTransmission() != 0) {
        last_status_ = STATUS_COMM_ERROR;
        return last_status_;
    }

    // Wait ~5ms for 24-bit delta-sigma conversion
    delayMicroseconds(5500);

    // Read 7 bytes back: Status (1) + Pressure (3) + Temperature (3)
    uint8_t count = wire_.requestFrom(addr_, (uint8_t)7);
    if (count != 7) {
        last_status_ = STATUS_COMM_ERROR;
        return last_status_;
    }

    uint8_t status_byte = wire_.read();
    if (status_byte & 0x20) {
        last_status_ = STATUS_BUSY;
        return last_status_;
    }
    if (status_byte & 0x04) {
        last_status_ = STATUS_MEMORY_ERROR;
        return last_status_;
    }
    if (status_byte & 0x01) {
        last_status_ = STATUS_MATH_ERROR;
        return last_status_;
    }

    // Parse 24-bit raw pressure
    uint32_t raw_p = 0;
    raw_p |= ((uint32_t)wire_.read()) << 16;
    raw_p |= ((uint32_t)wire_.read()) << 8;
    raw_p |= ((uint32_t)wire_.read());

    // Parse 24-bit raw temperature
    uint32_t raw_t = 0;
    raw_t |= ((uint32_t)wire_.read()) << 16;
    raw_t |= ((uint32_t)wire_.read()) << 8;
    raw_t |= ((uint32_t)wire_.read());

    // Transfer function conversion
    if (raw_p >= OUTPUT_MIN && raw_p <= OUTPUT_MAX) {
        pressure_psi_ = (((float)(raw_p - OUTPUT_MIN) * (p_max_ - p_min_)) / 
                         (float)(OUTPUT_MAX - OUTPUT_MIN)) + p_min_;
    } else if (raw_p < OUTPUT_MIN) {
        pressure_psi_ = p_min_;
    } else {
        pressure_psi_ = p_max_;
    }

    temperature_c_ = (((float)raw_t * 200.0f) / 16777215.0f) - 50.0f;
    last_status_ = STATUS_OK;
    return last_status_;
}
