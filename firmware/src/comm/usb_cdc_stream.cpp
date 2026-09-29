/**
 * @file usb_cdc_stream.cpp
 * @brief Implementation of Native USB CDC Streamer and Host Command Parser
 */

#include "usb_cdc_stream.h"
#include "hal/adc_ad40xx.h"
#include "hal/dac_mcp4822.h"
#include "hal/leak_detector.h"
#include "comm/pump_uart.h"

UsbCdcStream UsbStream;

UsbCdcStream::UsbCdcStream()
    : _streaming_enabled(false)
    , _streamed_frame_count(0) {
    _rx_buffer.reserve(128);
}

void UsbCdcStream::begin() {
    Serial.begin(921600);
    // Allow USB enumeration
    delay(100);
}

void UsbCdcStream::process_streaming() {
    if (!_streaming_enabled) {
        vTaskDelay(pdMS_TO_TICKS(1));
        return;
    }

    StreamFrame frame;
    // Drain completed frames from ADC ring buffer and write to USB CDC
    while (Adc.get_next_frame(&frame)) {
        // Update current status flags
        frame.status_flags = 0;
        if (_streaming_enabled)       frame.status_flags |= STATUS_STREAMING_ACTIVE;
        if (Leak.is_leak_detected())  frame.status_flags |= STATUS_LEAK_DETECTED;
        if (Pump.is_connected())      frame.status_flags |= STATUS_PUMP_CONNECTED;
        if (Pump.is_running())        frame.status_flags |= STATUS_PUMP_RUNNING;
        if (Pump.is_emergency())      frame.status_flags |= STATUS_PUMP_EMERGENCY;
        if (Dac.is_pulse_active())    frame.status_flags |= STATUS_DAC_PULSE_ACTIVE;

        // Recompute CRC with updated flags
        frame.crc16 = calculate_crc16((const uint8_t*)&frame, sizeof(StreamFrame) - sizeof(uint16_t));

        // Push frame over USB CDC endpoint
        Serial.write((const uint8_t*)&frame, sizeof(StreamFrame));
        _streamed_frame_count++;
    }
}

void UsbCdcStream::process_commands() {
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\r' || c == '\n') {
            if (_rx_buffer.length() > 0) {
                execute_command(_rx_buffer);
                _rx_buffer = "";
            }
        } else {
            if (_rx_buffer.length() < 120) {
                _rx_buffer += c;
            }
        }
    }
}

void UsbCdcStream::execute_command(const String& cmd) {
    String trimmed = cmd;
    trimmed.trim();
    if (trimmed.length() == 0) return;

    if (trimmed.equalsIgnoreCase("HELP")) {
        Serial.println(F("=== Sentinel Nanopore Commands ==="));
        Serial.println(F("SET:BIAS:<mv>          - Set pore bias (-1587 to +1587 mV)"));
        Serial.println(F("GET:BIAS               - Get current bias in mV"));
        Serial.println(F("CMD:PULSE:<mv>:<ms>    - Inject bias pulse"));
        Serial.println(F("STREAM:START           - Start 100kHz binary stream"));
        Serial.println(F("STREAM:STOP            - Stop binary stream"));
        Serial.println(F("SET:RATE:<hz>          - Set sample rate"));
        Serial.println(F("PUMP:START:<rpm>       - Run peristaltic pump"));
        Serial.println(F("PUMP:REV:<rpm>         - Run pump in reverse"));
        Serial.println(F("PUMP:STOP              - Stop peristaltic pump"));
        Serial.println(F("PUMP:ESTOP             - Emergency stop pump"));
        Serial.println(F("LEAK:RESET             - Reset latched leak error"));
        Serial.println(F("STATUS?                - Get JSON status telemetry"));
        return;
    }

    if (trimmed.startsWith("SET:BIAS:")) {
        float mv = trimmed.substring(9).toFloat();
        float applied = Dac.set_voltage_mv(mv);
        Serial.printf("OK:BIAS:%.2f\n", applied);
        return;
    }

    if (trimmed.equalsIgnoreCase("GET:BIAS")) {
        Serial.printf("BIAS:%.2f\n", Dac.get_current_bias_mv());
        return;
    }

    if (trimmed.startsWith("CMD:PULSE:")) {
        int first_colon = trimmed.indexOf(':', 10);
        if (first_colon > 0) {
            float mv = trimmed.substring(10, first_colon).toFloat();
            uint32_t ms = trimmed.substring(first_colon + 1).toInt();
            Dac.inject_pulse(mv, ms);
            Serial.printf("OK:PULSE:%.1f:%lu\n", mv, (unsigned long)ms);
            return;
        }
    }

    if (trimmed.equalsIgnoreCase("STREAM:START")) {
        Adc.start_sampling(DEFAULT_SAMPLE_RATE_HZ);
        _streaming_enabled = true;
        Serial.println(F("OK:STREAM:STARTED"));
        return;
    }

    if (trimmed.equalsIgnoreCase("STREAM:STOP")) {
        _streaming_enabled = false;
        Adc.stop_sampling();
        Serial.println(F("OK:STREAM:STOPPED"));
        return;
    }

    if (trimmed.startsWith("SET:RATE:")) {
        uint32_t rate = trimmed.substring(9).toInt();
        if (Adc.start_sampling(rate)) {
            Serial.printf("OK:RATE:%lu\n", (unsigned long)rate);
        } else {
            Serial.println(F("ERR:INVALID_RATE"));
        }
        return;
    }

    if (trimmed.startsWith("PUMP:START:")) {
        uint16_t rpm = (uint16_t)trimmed.substring(11).toInt();
        Pump.start(rpm, false);
        Serial.printf("OK:PUMP:START:%u\n", rpm);
        return;
    }

    if (trimmed.startsWith("PUMP:REV:")) {
        uint16_t rpm = (uint16_t)trimmed.substring(9).toInt();
        Pump.start(rpm, true);
        Serial.printf("OK:PUMP:REV:%u\n", rpm);
        return;
    }

    if (trimmed.equalsIgnoreCase("PUMP:STOP")) {
        Pump.stop();
        Serial.println(F("OK:PUMP:STOP"));
        return;
    }

    if (trimmed.equalsIgnoreCase("PUMP:ESTOP")) {
        Pump.emergency_stop();
        Dac.emergency_zero();
        Serial.println(F("OK:PUMP:ESTOP"));
        return;
    }

    if (trimmed.equalsIgnoreCase("LEAK:RESET")) {
        Leak.reset();
        Serial.println(F("OK:LEAK:RESET"));
        return;
    }

    if (trimmed.equalsIgnoreCase("STATUS?")) {
        send_status_json();
        return;
    }

    Serial.printf("ERR:UNKNOWN_CMD:%s\n", trimmed.c_str());
}

void UsbCdcStream::send_status_json() {
    Serial.printf("{\"bias_mv\":%.2f,\"pulse_active\":%s,\"sampling\":%s,\"streaming\":%s,\"rate_hz\":%lu,\"leak\":%s,\"pump_conn\":%s,\"pump_run\":%s,\"pump_rpm\":%u,\"frames\":%lu,\"dropped\":%lu}\n",
        Dac.get_current_bias_mv(),
        Dac.is_pulse_active() ? "true" : "false",
        Adc.is_sampling() ? "true" : "false",
        _streaming_enabled ? "true" : "false",
        (unsigned long)DEFAULT_SAMPLE_RATE_HZ,
        Leak.is_leak_detected() ? "true" : "false",
        Pump.is_connected() ? "true" : "false",
        Pump.is_running() ? "true" : "false",
        Pump.get_speed(),
        (unsigned long)Adc.get_total_frames(),
        (unsigned long)Adc.get_dropped_frames()
    );
}
