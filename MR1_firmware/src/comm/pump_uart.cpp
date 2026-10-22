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
 * @file pump_uart.cpp
 * @brief Implementation of External Peristaltic Pump UART Driver
 */

#include "pump_uart.h"

PumpController Pump;

PumpController::PumpController()
    : _serial(nullptr)
    , _connected(false)
    , _running(false)
    , _emergency(false)
    , _speed_rpm(0)
    , _last_heartbeat_sent(0)
    , _last_packet_received(0)
    , _rx_state(0)
    , _rx_cmd(0)
    , _rx_param(0)
    , _rx_checksum(0) {
}

void PumpController::begin() {
    _serial = &Serial1;
    // J22: TX on GPIO17, RX on GPIO47
    _serial->begin(PUMP_BAUD_RATE, SERIAL_8N1, PIN_PUMP_RX, PIN_PUMP_TX);
}

void PumpController::send_packet(uint8_t cmd, uint16_t param) {
    if (!_serial) return;

    PumpPacket pkt;
    pkt.sof = 0xAA;
    pkt.cmd = cmd;
    pkt.param = param;
    pkt.checksum = (uint8_t)(pkt.sof ^ pkt.cmd ^ (param & 0xFF) ^ ((param >> 8) & 0xFF));

    _serial->write((const uint8_t*)&pkt, sizeof(pkt));
}

void PumpController::start(uint16_t speed_rpm, bool reverse) {
    _emergency = false;
    _running = true;
    _speed_rpm = speed_rpm;
    uint8_t cmd = reverse ? 0x04 : 0x01; // 0x01: Run Fwd, 0x04: Run Rev
    send_packet(cmd, speed_rpm);
}

void PumpController::stop() {
    _running = false;
    _speed_rpm = 0;
    send_packet(0x02, 0); // 0x02: Normal Stop
}

void PumpController::emergency_stop() {
    _emergency = true;
    _running = false;
    _speed_rpm = 0;
    // Transmit emergency stop frame 3 times for robustness
    for (int i = 0; i < 3; i++) {
        send_packet(0xFF, 0xDEAD); // 0xFF: Emergency Stop
        delayMicroseconds(500);
    }
}

void PumpController::set_speed(uint16_t speed_rpm) {
    if (_emergency) return;
    _speed_rpm = speed_rpm;
    send_packet(0x03, speed_rpm);
}

void PumpController::update() {
    if (!_serial) return;

    // Read incoming bytes from pump
    while (_serial->available()) {
        process_incoming_byte(_serial->read());
    }

    // Heartbeat check
    uint32_t now = millis();
    if (now - _last_heartbeat_sent >= PUMP_HEARTBEAT_INTERVAL_MS) {
        _last_heartbeat_sent = now;
        send_packet(0x00, 0); // 0x00: Ping/Heartbeat
    }

    // Check connection timeout
    if (_connected && (now - _last_packet_received > PUMP_TIMEOUT_MS)) {
        _connected = false;
        _running = false;
    }
}

void PumpController::process_incoming_byte(uint8_t b) {
    switch (_rx_state) {
        case 0: // SOF
            if (b == 0xAA) {
                _rx_state = 1;
            }
            break;
        case 1: // CMD
            _rx_cmd = b;
            _rx_state = 2;
            break;
        case 2: // PARAM LSB
            _rx_param = b;
            _rx_state = 3;
            break;
        case 3: // PARAM MSB
            _rx_param |= ((uint16_t)b << 8);
            _rx_state = 4;
            break;
        case 4: // Checksum
            _rx_checksum = b;
            uint8_t calc_cs = (uint8_t)(0xAA ^ _rx_cmd ^ (_rx_param & 0xFF) ^ ((_rx_param >> 8) & 0xFF));
            if (calc_cs == _rx_checksum) {
                _connected = true;
                _last_packet_received = millis();

                if (_rx_cmd == 0x81) { // Status reply
                    _running = (_rx_param > 0);
                    _speed_rpm = _rx_param;
                } else if (_rx_cmd == 0x8F) { // Emergency acknowledgement
                    _emergency = true;
                    _running = false;
                }
            }
            _rx_state = 0;
            break;
    }
}
