#pragma once
#include <Arduino.h>

/**
 * Pump Controller SBU / UART Link Handler
 * Communicates with MR1 Reader using the standard packet framing protocol.
 */
class SbuLink {
public:
    struct Packet {
        uint8_t  sof;
        uint8_t  cmd;
        uint16_t param;
        uint8_t  checksum;
    } __attribute__((packed));

    enum Command : uint8_t {
        CMD_RUN_FWD       = 0x01,
        CMD_STOP          = 0x02,
        CMD_ESTOP         = 0x03,
        CMD_RUN_REV       = 0x04,
        CMD_SET_SPEED     = 0x05,
        CMD_HEARTBEAT     = 0x06,
        CMD_TELEMETRY     = 0x10,
        CMD_REPORT_PRESS  = 0x11
    };

    typedef void (*CommandHandler)(uint8_t cmd, uint16_t param);

    SbuLink(HardwareSerial& serial, uint32_t baud = 115200);

    void begin();
    void setCommandHandler(CommandHandler handler) { cmd_handler_ = handler; }
    void update();

    void sendPacket(uint8_t cmd, uint16_t param);
    void sendPressureTelemetry(float cis_psi, float trans_psi);

    bool isConnected() const { return connected_; }
    uint32_t getLastPacketTimeMs() const { return last_rx_ms_; }

private:
    HardwareSerial& serial_;
    uint32_t baud_;
    CommandHandler cmd_handler_;
    bool connected_;
    uint32_t last_rx_ms_;

    // Parser state machine
    uint8_t rx_state_;
    uint8_t rx_cmd_;
    uint16_t rx_param_;
    uint8_t rx_checksum_;

    void processByte(uint8_t b);
};
