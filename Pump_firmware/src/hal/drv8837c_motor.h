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

/**
 * TI DRV8837C Low-Voltage H-Bridge Motor Driver
 * Provides PWM speed regulation, direction control, and hardware emergency braking.
 */
class DRV8837CMotor {
public:
    enum Direction {
        DIR_FORWARD = 1,
        DIR_REVERSE = 0
    };

    enum Mode {
        MODE_STOPPED = 0,
        MODE_CONTINUOUS = 1,
        MODE_DISPENSE_VOLUME = 2,
        MODE_FLUSH = 3,
        MODE_ESTOP = 4
    };

    DRV8837CMotor(uint8_t pwm_pin, uint8_t dir_pin, float ul_per_rev);

    void begin();
    void setDirection(Direction dir);
    void setPwmDuty(float duty_pct); // 0.0 to 100.0%
    void setFlowRate(float ul_per_min, Direction dir = DIR_FORWARD);
    void dispenseVolume(float target_ul, float rate_ul_min);
    void flush(Direction dir = DIR_FORWARD);
    void stop();
    void emergencyStop();

    void update(uint32_t dt_ms);

    Mode getMode() const { return current_mode_; }
    float getTargetRate() const { return target_rate_ul_min_; }
    float getDispensedVolumeUl() const { return dispensed_ul_; }
    bool isRunning() const { return current_mode_ != MODE_STOPPED && current_mode_ != MODE_ESTOP; }

private:
    uint8_t pwm_pin_;
    uint8_t dir_pin_;
    float ul_per_rev_;
    Direction current_dir_;
    Mode current_mode_;
    float target_rate_ul_min_;
    float target_volume_ul_;
    float dispensed_ul_;
    float current_duty_;

    static constexpr float MAX_RPM = 180.0f;
    static constexpr uint32_t PWM_MAX_COUNT = 4095; // 12-bit
};
