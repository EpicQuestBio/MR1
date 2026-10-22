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
 * @file usb_cdc_stream.cpp
 * @brief Implementation of Native USB CDC Streamer and Host Command Parser
 */

#include "usb_cdc_stream.h"
#include "hal/adc_ad40xx.h"
#include "hal/dac_mcp4822.h"
#include "hal/leak_detector.h"
#include "comm/pump_uart.h"
#include "comm/sbu_i2c_detect.h"

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
        if (Dac.is_waveform_active()) frame.status_flags |= STATUS_DAC_WAVE_ACTIVE;

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
        Serial.println(F("=== MR1 Nanopore Commands ==="));
        Serial.println(F("SET:BIAS:<mv>          - Set pore bias (-1587 to +1587 mV)"));
        Serial.println(F("GET:BIAS               - Get current bias in mV"));
        Serial.println(F("CMD:PULSE:<mv>:<ms>    - Inject bias pulse"));
        Serial.println(F("SET:DAC:GAIN:<1X|2X>   - Set DAC gain (1X=85kHz full-power BW, 2X=42.7kHz)"));
        Serial.println(F("SET:DAC:SPEED:<sps>    - Set DAC update rate (up to 1,000,000 SPS)"));
        Serial.println(F("WAVE:CONFIG:<shp>:<f>  - Config waveform (SINE, TRIANGLE, SQUARE, RAMP, CHIRP)"));
        Serial.println(F("WAVE:START / STOP      - Start/stop high-speed DDS waveform synthesis"));
        Serial.println(F("DAC:SET:RAW:<ch>:<code>- Direct raw 12-bit SPI transfer (<850ns)"));
        Serial.println(F("STREAM:START           - Start 100kHz binary stream"));
        Serial.println(F("STREAM:STOP            - Stop binary stream"));
        Serial.println(F("SET:RATE:<hz>          - Set sample rate"));
        Serial.println(F("PUMP:START:<rpm>       - Run peristaltic pump"));
        Serial.println(F("PUMP:REV:<rpm>         - Run pump in reverse"));
        Serial.println(F("PUMP:STOP              - Stop peristaltic pump"));
        Serial.println(F("PUMP:ESTOP             - Emergency stop pump"));
        Serial.println(F("LEAK:RESET             - Reset latched leak error"));
        Serial.println(F("SBU:DETECT             - Auto-detect USB-C SBU I2C polarity"));
        Serial.println(F("SBU:STATUS             - Get SBU orientation & active pins"));
        Serial.println(F("SBU:SCAN               - Scan SBU I2C bus for peripherals"));
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

    if (trimmed.startsWith("SET:DAC:GAIN:")) {
        String mode = trimmed.substring(13);
        mode.toUpperCase();
        if (mode == "1X") {
            Dac.set_gain_mode(false);
            Serial.println(F("OK:DAC:GAIN:1X"));
        } else if (mode == "2X") {
            Dac.set_gain_mode(true);
            Serial.println(F("OK:DAC:GAIN:2X"));
        } else {
            Serial.println(F("ERR:INVALID_GAIN_MODE"));
        }
        return;
    }

    if (trimmed.startsWith("SET:DAC:SPEED:")) {
        uint32_t sps = trimmed.substring(14).toInt();
        Dac.set_update_rate_sps(sps);
        Serial.printf("OK:DAC:SPEED:%lu\n", (unsigned long)Dac.get_update_rate_sps());
        return;
    }

    if (trimmed.startsWith("WAVE:CONFIG:")) {
        // Format: WAVE:CONFIG:<shape>:<freq_hz>:<amp_mv>[:<offset_mv>]
        // Shapes: SINE, TRIANGLE, SQUARE, RAMP, CHIRP, OFF
        String rest = trimmed.substring(12);
        int c1 = rest.indexOf(':');
        int c2 = (c1 >= 0) ? rest.indexOf(':', c1 + 1) : -1;
        if (c1 > 0 && c2 > c1) {
            String shape_str = rest.substring(0, c1);
            shape_str.toUpperCase();
            int c3 = rest.indexOf(':', c2 + 1);
            float freq_hz = rest.substring(c1 + 1, c2).toFloat();
            float amp_mv = (c3 > c2) ? rest.substring(c2 + 1, c3).toFloat() : rest.substring(c2 + 1).toFloat();
            float offset_mv = (c3 > c2) ? rest.substring(c3 + 1).toFloat() : 0.0f;

            DacWaveformShape shape = WAVE_SHAPE_OFF;
            if (shape_str == "SINE") shape = WAVE_SHAPE_SINE;
            else if (shape_str == "TRIANGLE") shape = WAVE_SHAPE_TRIANGLE;
            else if (shape_str == "SQUARE") shape = WAVE_SHAPE_SQUARE;
            else if (shape_str == "RAMP") shape = WAVE_SHAPE_RAMP;
            else if (shape_str == "CHIRP") shape = WAVE_SHAPE_CHIRP;
            else if (shape_str == "OFF") shape = WAVE_SHAPE_OFF;
            else {
                Serial.println(F("ERR:INVALID_WAVE_SHAPE"));
                return;
            }

            Dac.configure_waveform(shape, freq_hz, amp_mv, offset_mv);
            Serial.printf("OK:WAVE:CONFIG:%s:%.2f:%.2f:%.2f\n", shape_str.c_str(), freq_hz, amp_mv, offset_mv);
            return;
        } else {
            Serial.println(F("ERR:WAVE:SYNTAX"));
            return;
        }
    }

    if (trimmed.equalsIgnoreCase("WAVE:START")) {
        Dac.start_waveform();
        Serial.println(F("OK:WAVE:STARTED"));
        return;
    }

    if (trimmed.equalsIgnoreCase("WAVE:STOP")) {
        Dac.stop_waveform();
        Serial.println(F("OK:WAVE:STOPPED"));
        return;
    }

    if (trimmed.startsWith("DAC:SET:RAW:")) {
        // Fast direct raw channel write: DAC:SET:RAW:<ch>:<code 0-4095>
        int c1 = trimmed.indexOf(':', 12);
        if (c1 > 0) {
            uint8_t ch = (uint8_t)trimmed.substring(12, c1).toInt();
            uint16_t code = (uint16_t)trimmed.substring(c1 + 1).toInt();
            Dac.set_raw(ch, code, Dac.is_gain_2x());
            Serial.printf("OK:DAC:RAW:%u:%u\n", ch, code);
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

    if (trimmed.equalsIgnoreCase("SBU:DETECT")) {
        SbuOrientation orient = SbuDetector.detect_orientation();
        Serial.printf("OK:SBU:%s\n", SbuDetector.get_orientation_str());
        return;
    }

    if (trimmed.equalsIgnoreCase("SBU:STATUS")) {
        Serial.printf("{\"sbu_orient\":\"%s\",\"scl_gpio\":%d,\"sda_gpio\":%d,\"connected\":%s}\n",
            SbuDetector.get_orientation_str(),
            SbuDetector.get_scl_pin(),
            SbuDetector.get_sda_pin(),
            SbuDetector.is_connected() ? "true" : "false"
        );
        return;
    }

    if (trimmed.equalsIgnoreCase("SBU:SCAN")) {
        std::vector<uint8_t> devs = SbuDetector.scan_bus();
        Serial.printf("{\"sbu_orient\":\"%s\",\"device_count\":%u,\"devices\":[",
            SbuDetector.get_orientation_str(),
            (unsigned int)devs.size()
        );
        for (size_t i = 0; i < devs.size(); i++) {
            Serial.printf("\"0x%02X\"%s", devs[i], (i + 1 < devs.size()) ? "," : "");
        }
        Serial.println("]}");
        return;
    }

    if (trimmed.equalsIgnoreCase("STATUS?")) {
        send_status_json();
        return;
    }

    Serial.printf("ERR:UNKNOWN_CMD:%s\n", trimmed.c_str());
}

void UsbCdcStream::send_status_json() {
    const char* shape_str = "OFF";
    switch (Dac.get_waveform_shape()) {
        case WAVE_SHAPE_SINE: shape_str = "SINE"; break;
        case WAVE_SHAPE_TRIANGLE: shape_str = "TRIANGLE"; break;
        case WAVE_SHAPE_SQUARE: shape_str = "SQUARE"; break;
        case WAVE_SHAPE_RAMP: shape_str = "RAMP"; break;
        case WAVE_SHAPE_CHIRP: shape_str = "CHIRP"; break;
        default: shape_str = "OFF"; break;
    }

    Serial.printf("{\"bias_mv\":%.2f,\"dac_gain\":\"%s\",\"dac_sps\":%lu,\"wave_active\":%s,\"wave_shape\":\"%s\",\"wave_freq\":%.1f,\"pulse_active\":%s,\"sampling\":%s,\"streaming\":%s,\"rate_hz\":%lu,\"leak\":%s,\"pump_conn\":%s,\"pump_run\":%s,\"pump_rpm\":%u,\"sbu_orient\":\"%s\",\"frames\":%lu,\"dropped\":%lu}\n",
        Dac.get_current_bias_mv(),
        Dac.is_gain_2x() ? "2X" : "1X",
        (unsigned long)Dac.get_update_rate_sps(),
        Dac.is_waveform_active() ? "true" : "false",
        shape_str,
        Dac.get_waveform_freq_hz(),
        Dac.is_pulse_active() ? "true" : "false",
        Adc.is_sampling() ? "true" : "false",
        _streaming_enabled ? "true" : "false",
        (unsigned long)DEFAULT_SAMPLE_RATE_HZ,
        Leak.is_leak_detected() ? "true" : "false",
        Pump.is_connected() ? "true" : "false",
        Pump.is_running() ? "true" : "false",
        Pump.get_speed(),
        SbuDetector.get_orientation_str(),
        (unsigned long)Adc.get_total_frames(),
        (unsigned long)Adc.get_dropped_frames()
    );
}
