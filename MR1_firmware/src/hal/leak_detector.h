/*
 * Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
 * Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
 * SPDX-License-Identifier: CC0-1.0
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
