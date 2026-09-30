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
