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
 * @file opendaq_stream.h
 * @brief OpenDAQ Native Streaming Protocol over WebSockets
 */

#pragma once

#include <Arduino.h>
#include <WebSocketsServer.h>
#include "hal/adc_ad40xx.h"

class OpenDAQStream {
public:
    OpenDAQStream();

    /**
     * @brief Initialize the OpenDAQ WebSocket server on port 7414
     */
    void begin();

    /**
     * @brief Service the WebSocket server and handle packet streaming
     */
    void update();

    /**
     * @brief Control whether OpenDAQ streaming is active
     */
    void set_active(bool active) { _active = active; }
    bool is_active() const { return _active; }

private:
    void on_websocket_event(uint8_t num, WStype_t type, uint8_t * payload, size_t length);
    void handle_binary_packet(uint8_t num, uint8_t * payload, size_t length);

    WebSocketsServer _server;
    bool _active;

    // Simple state: 0 = disconnected/unsubscribed, 1 = subscribed
    // WebSocketsServer supports up to WEBSOCKETS_SERVER_CLIENT_MAX (usually 5)
    bool _client_subscribed[WEBSOCKETS_SERVER_CLIENT_MAX];

    uint32_t _last_stream_time;
};

extern OpenDAQStream DAQStream;
