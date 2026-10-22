/*
 * Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
 * Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
 * SPDX-License-Identifier: CC0-1.0
 */

/**
 * @file leak_detector.cpp
 * @brief Implementation of Weep Moat / Leak Detection Supervisor
 */

#include "leak_detector.h"
#include "dac_mcp4822.h"

LeakDetector Leak;

LeakDetector::LeakDetector()
    : _latched_leak(false)
    , _trip_start_time(0)
    , _debouncing(false)
    , _emergency_cb(nullptr) {
}

void LeakDetector::begin() {
    // GPIO 1 configured as input with pull-up.
    // Conductive liquid in weep moat grounds this pin.
    pinMode(PIN_LEAK_SENSE, INPUT_PULLUP);
    _latched_leak = false;
    _debouncing = false;
}

void LeakDetector::update() {
    // If already latched in emergency state, do nothing until reset
    if (_latched_leak) return;

    bool raw_trip = (digitalRead(PIN_LEAK_SENSE) == LOW);

    if (raw_trip) {
        if (!_debouncing) {
            _debouncing = true;
            _trip_start_time = millis();
        } else if (millis() - _trip_start_time >= LEAK_DEBOUNCE_MS) {
            trigger_emergency();
        }
    } else {
        _debouncing = false;
    }
}

void LeakDetector::trigger_emergency() {
    if (_latched_leak) return;

    _latched_leak = true;
    _debouncing = false;

    // 1. Immediately zero pore bias to prevent electrode damage/electrolysis
    Dac.emergency_zero();

    // 2. Invoke emergency cutoff callback (e.g. command pump module to stop)
    if (_emergency_cb) {
        _emergency_cb();
    }
}

void LeakDetector::reset() {
    _latched_leak = false;
    _debouncing = false;
}
