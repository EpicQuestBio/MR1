/**
 * @file web_portal.cpp
 * @brief Implementation of Embedded Web Portal
 */

#include "web_portal.h"
#include "web_ui_assets.h"
#include "hal/dac_mcp4822.h"
#include "hal/adc_ad40xx.h"
#include "hal/leak_detector.h"
#include "comm/pump_uart.h"
#include "comm/usb_cdc_stream.h"

WebPortal Portal;

WebPortal::WebPortal()
    : _server(WEB_PORTAL_PORT)
    , _active(true)
    , _last_broadcast_time(0) {
}

void WebPortal::begin() {
    // Configure Wi-Fi in Access Point mode
    WiFi.mode(WIFI_AP);
    WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASS);

    // Register HTTP endpoints
    _server.on("/", HTTP_GET, [this]() { handle_root(); });
    _server.on("/api/bias", HTTP_POST, [this]() { handle_bias(); });
    _server.on("/api/pulse", HTTP_POST, [this]() { handle_pulse(); });
    _server.on("/api/pump", HTTP_POST, [this]() { handle_pump(); });
    _server.on("/api/leak/reset", HTTP_POST, [this]() { handle_leak_reset(); });
    _server.on("/api/status", HTTP_GET, [this]() { handle_status(); });

    _server.begin();
}

void WebPortal::handle_root() {
    _server.send_P(200, "text/html", INDEX_HTML);
}

void WebPortal::handle_bias() {
    if (_server.hasArg("plain")) {
        float mv = _server.arg("plain").toFloat();
        float applied = Dac.set_voltage_mv(mv);
        _server.send(200, "application/json", String("{\"applied\":") + String(applied) + "}");
    } else {
        _server.send(400, "text/plain", "Missing body");
    }
}

void WebPortal::handle_pulse() {
    float mv = DEFAULT_PULSE_VOLTAGE_MV;
    if (_server.hasArg("plain")) {
        mv = _server.arg("plain").toFloat();
    }
    Dac.inject_pulse(mv, DEFAULT_PULSE_DURATION_MS);
    _server.send(200, "application/json", "{\"status\":\"pulse_started\"}");
}

void WebPortal::handle_pump() {
    if (_server.hasArg("plain")) {
        String body = _server.arg("plain");
        if (body.indexOf("estop") >= 0) {
            Pump.emergency_stop();
            Dac.emergency_zero();
        } else if (body.indexOf("stop") >= 0) {
            Pump.stop();
        } else if (body.indexOf("fwd") >= 0) {
            Pump.start(60, false);
        } else if (body.indexOf("rev") >= 0) {
            Pump.start(60, true);
        }
        _server.send(200, "application/json", "{\"status\":\"ok\"}");
    } else {
        _server.send(400, "text/plain", "Missing body");
    }
}

void WebPortal::handle_leak_reset() {
    Leak.reset();
    _server.send(200, "application/json", "{\"status\":\"reset\"}");
}

void WebPortal::handle_status() {
    char json_buf[320];
    snprintf(json_buf, sizeof(json_buf),
        "{\"bias_mv\":%.2f,\"pulse_active\":%s,\"sampling\":%s,\"streaming\":%s,\"rate_hz\":%lu,\"leak\":%s,\"pump_conn\":%s,\"pump_run\":%s,\"pump_rpm\":%u,\"latest_sample\":%d}",
        Dac.get_current_bias_mv(),
        Dac.is_pulse_active() ? "true" : "false",
        Adc.is_sampling() ? "true" : "false",
        UsbStream.is_streaming() ? "true" : "false",
        (unsigned long)DEFAULT_SAMPLE_RATE_HZ,
        Leak.is_leak_detected() ? "true" : "false",
        Pump.is_connected() ? "true" : "false",
        Pump.is_running() ? "true" : "false",
        Pump.get_speed(),
        Adc.get_latest_decimated_sample()
    );
    _server.send(200, "application/json", json_buf);
}

void WebPortal::update() {
    if (!_active) return;

    _server.handleClient();
}
