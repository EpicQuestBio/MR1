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
 * @file pump_uart.h
 * @brief Bidirectional UART Driver & Protocol for External Peristaltic Pump Module (J22)
 */

#pragma once

#include <Arduino.h>
#include "pinout.h"
#include "config.h"
#include "protocol.h"

class PumpController {
public:
    PumpController();

    /**
     * @brief Initialize Hardware UART on J22 connector pins
     */
    void begin();

    /**
     * @brief Periodic update for heartbeat and incoming telemetry parsing
     */
    void update();

    /**
     * @brief Command pump to run at specified RPM or flow rate
     * @param speed_rpm Speed setting (e.g. 10 - 300 RPM)
     * @param reverse Reverse direction if true
     */
    void start(uint16_t speed_rpm, bool reverse = false);

    /**
     * @brief Command pump to stop normally
     */
    void stop();

    /**
     * @brief Send high-priority emergency shutdown frame immediately
     */
    void emergency_stop();

    /**
     * @brief Set pump speed while running
     */
    void set_speed(uint16_t speed_rpm);

    bool is_connected() const { return _connected; }
    bool is_running() const { return _running; }
    bool is_emergency() const { return _emergency; }
    uint16_t get_speed() const { return _speed_rpm; }

private:
    void send_packet(uint8_t cmd, uint16_t param);
    void process_incoming_byte(uint8_t b);

    HardwareSerial* _serial;
    bool     _connected;
    bool     _running;
    bool     _emergency;
    uint16_t _speed_rpm;
    uint32_t _last_heartbeat_sent;
    uint32_t _last_packet_received;

    // Parser state
    uint8_t  _rx_state;
    uint8_t  _rx_cmd;
    uint16_t _rx_param;
    uint8_t  _rx_checksum;
};

extern PumpController Pump;
