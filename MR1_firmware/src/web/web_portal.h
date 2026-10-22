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
 * @file web_portal.h
 * @brief Embedded Web Portal & Oscilloscope Telemetry Server
 */

#pragma once

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include "config.h"

class WebPortal {
public:
    WebPortal();

    /**
     * @brief Initialize Wi-Fi SoftAP and start embedded HTTP server
     */
    void begin();

    /**
     * @brief Process incoming HTTP requests and broadcast telemetry. Call from Core 0 loop.
     */
    void update();

    /**
     * @brief Control whether Wi-Fi portal is active or throttled during high-speed USB streaming
     */
    void set_active(bool active) { _active = active; }
    bool is_active() const { return _active; }

private:
    void handle_root();
    void handle_bias();
    void handle_pulse();
    void handle_pump();
    void handle_leak_reset();
    void handle_status();

    WebServer _server;
    bool      _active;
    uint32_t  _last_broadcast_time;
};

extern WebPortal Portal;
