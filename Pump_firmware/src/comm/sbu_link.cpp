/*
 * Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
 * Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
 * SPDX-License-Identifier: CC0-1.0
 */

#include "sbu_link.h"

SbuLink::SbuLink(HardwareSerial& serial, uint32_t baud)
    : serial_(serial), baud_(baud), cmd_handler_(nullptr),
      connected_(false), last_rx_ms_(0),
      rx_state_(0), rx_cmd_(0), rx_param_(0), rx_checksum_(0) {}

void SbuLink::begin() {
    serial_.begin(baud_);
    connected_ = false;
    last_rx_ms_ = millis();
}

void SbuLink::sendPacket(uint8_t cmd, uint16_t param) {
    Packet pkt;
    pkt.sof = 0xAA;
    pkt.cmd = cmd;
    pkt.param = param;
    pkt.checksum = (uint8_t)(pkt.sof ^ pkt.cmd ^ (param & 0xFF) ^ ((param >> 8) & 0xFF));

    serial_.write((const uint8_t*)&pkt, sizeof(pkt));
}

void SbuLink::sendPressureTelemetry(float cis_psi, float trans_psi) {
    // Pack 0..10 psi as centi-psi (0..1000)
    uint16_t cis_cp = (uint16_t)(constrain(cis_psi, 0.0f, 650.0f) * 100.0f);
    sendPacket(CMD_REPORT_PRESS, cis_cp);
}

void SbuLink::update() {
    while (serial_.available() > 0) {
        processByte((uint8_t)serial_.read());
    }

    // Timeout check
    if (millis() - last_rx_ms_ > 1500) {
        connected_ = false;
    }
}

void SbuLink::processByte(uint8_t b) {
    switch (rx_state_) {
        case 0: // Waiting for SOF (0xAA)
            if (b == 0xAA) {
                rx_state_ = 1;
            }
            break;

        case 1: // CMD byte
            rx_cmd_ = b;
            rx_state_ = 2;
            break;

        case 2: // PARAM LSB
            rx_param_ = b;
            rx_state_ = 3;
            break;

        case 3: // PARAM MSB
            rx_param_ |= ((uint16_t)b << 8);
            rx_state_ = 4;
            break;

        case 4: { // CHECKSUM byte
            rx_checksum_ = b;
            uint8_t expected = (uint8_t)(0xAA ^ rx_cmd_ ^ (rx_param_ & 0xFF) ^ ((rx_param_ >> 8) & 0xFF));
            if (rx_checksum_ == expected) {
                connected_ = true;
                last_rx_ms_ = millis();
                if (cmd_handler_) {
                    cmd_handler_(rx_cmd_, rx_param_);
                }
            }
            rx_state_ = 0;
            break;
        }

        default:
            rx_state_ = 0;
            break;
    }
}
