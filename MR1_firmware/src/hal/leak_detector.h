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
 * @file leak_detector.h
 * @brief Weep Moat / Leak Detection and Emergency Shutdown Supervisor
 */

#pragma once

#include <Arduino.h>
#include "pinout.h"
#include "config.h"

typedef void (*LeakCallback_t)();

class LeakDetector {
public:
    LeakDetector();

    /**
     * @brief Initialize sensing GPIO with pull-up and interrupt
     */
    void begin();

    /**
     * @brief Service routine to check debounce and status. Call from Core 0.
     */
    void update();

    /**
     * @brief Register a callback to execute immediately when a leak is detected
     */
    void set_emergency_callback(LeakCallback_t cb) { _emergency_cb = cb; }

    /**
     * @brief Check if leak sensor has tripped and latched
     */
    bool is_leak_detected() const { return _latched_leak; }

    /**
     * @brief Clear latched error state after physical leak inspection
     */
    void reset();

    /**
     * @brief Manually simulate or test emergency trip
     */
    void trigger_emergency();

private:
    bool           _latched_leak;
    uint32_t       _trip_start_time;
    bool           _debouncing;
    LeakCallback_t _emergency_cb;
};

extern LeakDetector Leak;
