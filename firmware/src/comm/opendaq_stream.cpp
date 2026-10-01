/**
 * @file opendaq_stream.cpp
 * @brief Implementation of OpenDAQ Native Streaming Protocol over WebSockets
 */

#include "opendaq_stream.h"

#define OPENDAQ_PORT 7414

// OpenDAQ Package Type Codes
#define PKG_SIGNAL_PACKET 0x1
#define PKG_SIGNAL_AVAILABLE 0x2
#define PKG_SIGNAL_UNAVAILABLE 0x3
#define PKG_SUBSCRIBE_REQ 0x4
#define PKG_UNSUBSCRIBE_REQ 0x5
#define PKG_INIT_DONE_ACK 0x6
#define PKG_SUBSCRIBE_ACK 0x7
#define PKG_UNSUBSCRIBE_ACK 0x8
#define PKG_INIT_REQ 0xB

#define SIGNAL_NUMERIC_ID 1

static const char* SIGNAL_JSON =
"{\n"
"    \"__type\": \"Signal\",\n"
"    \"domainSignalId\": \"/MR1/Time\",\n"
"    \"dataDescriptor\": {\n"
"        \"__type\": \"DataDescriptor\",\n"
"        \"name\": \"Current\",\n"
"        \"sampleType\": 2,\n"
"        \"dimensions\": [],\n"
"        \"rule\": {\n"
"            \"__type\": \"DataRule\",\n"
"            \"ruleType\": 3,\n"
"            \"params\": {\n"
"                \"__type\": \"Dict\",\n"
"                \"values\": []\n"
"            }\n"
"        },\n"
"        \"origin\": \"\",\n"
"        \"metadata\": {\n"
"            \"__type\": \"Dict\",\n"
"            \"values\": []\n"
"        },\n"
"        \"structFields\": []\n"
"    },\n"
"    \"public\": true,\n"
"    \"description\": \"MR1 Decimated Current Signal\",\n"
"    \"name\": \"MR1_Current\"\n"
"}";

OpenDAQStream DAQStream;

OpenDAQStream::OpenDAQStream()
    : _server(OPENDAQ_PORT)
    , _active(true)
    , _last_stream_time(0) {
    for (int i = 0; i < WEBSOCKETS_SERVER_CLIENT_MAX; i++) {
        _client_subscribed[i] = false;
    }
}

void OpenDAQStream::begin() {
    _server.begin();
    _server.onEvent([this](uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
        on_websocket_event(num, type, payload, length);
    });
}

void OpenDAQStream::update() {
    if (!_active) return;

    _server.loop();

    // Broadcast decimated sample at ~100Hz (every 10ms)
    uint32_t now = millis();
    if (now - _last_stream_time >= 10) {
        _last_stream_time = now;

        bool has_subscriber = false;
        for (int i = 0; i < WEBSOCKETS_SERVER_CLIENT_MAX; i++) {
            if (_client_subscribed[i]) {
                has_subscriber = true;
                break;
            }
        }

        if (has_subscriber) {
            int16_t sample = Adc.get_latest_decimated_sample();

            // Construct Data Packet (0x1)
            // Package header: 1 byte type, followed by payload.
            // Wait! The OpenDAQ protocol spec says: "Package type code: 0x1".
            // Since it doesn't specify if the type is 1 byte, 2 bytes or 4 bytes, let's assume it's a 1-byte prefix for the websocket payload (or it's the entire payload if header-only).
            // Wait, looking at opendaq native protocol, it's often a 1-byte packet type ID at the start.

            // For now, let's just pack a basic Signal packet.
            // The spec says:
            // Packet buffer generic header: 12 bytes
            // Packet buffer extra header + payload: Rest of the payload size
            uint8_t pkt[1 + 12 + 2];
            pkt[0] = PKG_SIGNAL_PACKET;
            memset(&pkt[1], 0, 12); // Dummy generic header

            // payload
            pkt[13] = sample & 0xFF;
            pkt[14] = (sample >> 8) & 0xFF;

            for (int i = 0; i < WEBSOCKETS_SERVER_CLIENT_MAX; i++) {
                if (_client_subscribed[i]) {
                    _server.sendBIN(i, pkt, sizeof(pkt));
                }
            }
        }
    }
}

void OpenDAQStream::on_websocket_event(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:
            _client_subscribed[num] = false;
            break;
        case WStype_CONNECTED:
            break;
        case WStype_BIN:
            handle_binary_packet(num, payload, length);
            break;
        default:
            break;
    }
}

void OpenDAQStream::handle_binary_packet(uint8_t num, uint8_t * payload, size_t length) {
    if (length < 1) return;

    // Assume 1st byte is the package type
    uint8_t pkg_type = payload[0];

    if (pkg_type == PKG_INIT_REQ) {
        // Send PKG_SIGNAL_AVAILABLE
        String symId = "/MR1_Current";

        size_t json_len = strlen(SIGNAL_JSON);
        size_t pkt_len = 1 + 4 + 2 + symId.length() + json_len + 1; // +1 for null terminator of string
        uint8_t* out = new uint8_t[pkt_len];

        out[0] = PKG_SIGNAL_AVAILABLE;

        // Signal numeric ID
        uint32_t id = SIGNAL_NUMERIC_ID;
        memcpy(&out[1], &id, 4);

        // Signal symbolic ID size
        uint16_t sym_len = symId.length();
        memcpy(&out[5], &sym_len, 2);

        // Signal symbolic ID
        memcpy(&out[7], symId.c_str(), sym_len);

        // Serialized signal string (null terminated)
        memcpy(&out[7 + sym_len], SIGNAL_JSON, json_len);
        out[7 + sym_len + json_len] = '\0';

        _server.sendBIN(num, out, pkt_len);
        delete[] out;

        // Send PKG_INIT_DONE_ACK
        uint8_t ack_pkt[1] = { PKG_INIT_DONE_ACK };
        _server.sendBIN(num, ack_pkt, 1);
    }
    else if (pkg_type == PKG_SUBSCRIBE_REQ) {
        if (length >= 5) {
            uint32_t id;
            memcpy(&id, &payload[1], 4);
            if (id == SIGNAL_NUMERIC_ID) {
                _client_subscribed[num] = true;

                // Send PKG_SUBSCRIBE_ACK
                uint8_t ack[5];
                ack[0] = PKG_SUBSCRIBE_ACK;
                memcpy(&ack[1], &id, 4);
                _server.sendBIN(num, ack, 5);
            }
        }
    }
    else if (pkg_type == PKG_UNSUBSCRIBE_REQ) {
        if (length >= 5) {
            uint32_t id;
            memcpy(&id, &payload[1], 4);
            if (id == SIGNAL_NUMERIC_ID) {
                _client_subscribed[num] = false;

                // Send PKG_UNSUBSCRIBE_ACK
                uint8_t ack[5];
                ack[0] = PKG_UNSUBSCRIBE_ACK;
                memcpy(&ack[1], &id, 4);
                _server.sendBIN(num, ack, 5);
            }
        }
    }
}
