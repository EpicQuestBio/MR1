/**
 * @file usb_cdc_stream.h
 * @brief High-Throughput Native USB CDC Streaming & Host Command Parser
 */

#pragma once

#include <Arduino.h>
#include "protocol.h"
#include "config.h"

class UsbCdcStream {
public:
    UsbCdcStream();

    /**
     * @brief Initialize native USB CDC port
     */
    void begin();

    /**
     * @brief Process outbound binary stream frames (called from Core 1 acquisition task)
     */
    void process_streaming();

    /**
     * @brief Process incoming command line characters (called from Core 0)
     */
    void process_commands();

    void set_streaming(bool enable) { _streaming_enabled = enable; }
    bool is_streaming() const { return _streaming_enabled; }

    /**
     * @brief Send a JSON status reply to the host
     */
    void send_status_json();

private:
    void execute_command(const String& cmd);

    bool   _streaming_enabled;
    String _rx_buffer;
    uint32_t _streamed_frame_count;
};

extern UsbCdcStream UsbStream;
