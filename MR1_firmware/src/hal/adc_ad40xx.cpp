/*
 * Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
 * Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
 * SPDX-License-Identifier: CC0-1.0
 */

/**
 * @file adc_ad40xx.cpp
 * @brief Implementation of High-Speed AD40xx SAR ADC Driver
 */

#include "adc_ad40xx.h"
#include <esp_timer.h>

AdcAD40xx Adc;

static esp_timer_handle_t s_adc_timer = nullptr;

static void IRAM_ATTR adc_timer_callback(void* arg) {
    Adc.on_timer_tick();
}

AdcAD40xx::AdcAD40xx()
    : _spi(nullptr)
    , _sampling_active(false)
    , _active_route(1)
    , _sample_rate_hz(DEFAULT_SAMPLE_RATE_HZ)
    , _frame_sequence(0)
    , _dropped_frames(0)
    , _write_idx(0)
    , _read_idx(0)
    , _sample_in_frame(0)
    , _decimation_accumulator(0)
    , _decimation_count(0)
    , _latest_decimated(0) {
    memset(_frames, 0, sizeof(_frames));
}

void AdcAD40xx::begin() {
    pinMode(PIN_ADC_CNV, OUTPUT);
    digitalWrite(PIN_ADC_CNV, LOW);

    pinMode(PIN_ROUTE_SEL, OUTPUT);
    digitalWrite(PIN_ROUTE_SEL, LOW); // Default to Route 1
    _active_route = 1;

    // AD40xx uses SPI: SCK (GPIO10), SDO/MISO (GPIO9)
    _spi = new SPIClass(FSPI);
    _spi->begin(PIN_ADC_SCK, PIN_ADC_SDO, -1, -1);

    // Initialize frame metadata
    for (int i = 0; i < RING_BUFFER_FRAME_COUNT; i++) {
        _frames[i].magic = STREAM_MAGIC_WORD;
        _frames[i].sample_count = SAMPLES_PER_FRAME;
    }
}

int16_t AdcAD40xx::read_single() {
    if (!_spi) return 0;

    // 1. Pulse CNV high to start conversion
    digitalWrite(PIN_ADC_CNV, HIGH);
    esp_rom_delay_us(1); // Conversion time t_conv ~ 300ns
    digitalWrite(PIN_ADC_CNV, LOW);

    // 2. Read 16-bit differential value over SPI
    _spi->beginTransaction(SPISettings(40000000, MSBFIRST, SPI_MODE0));
    uint16_t raw = _spi->transfer16(0x0000);
    _spi->endTransaction();

    return (int16_t)raw;
}

bool AdcAD40xx::start_sampling(uint32_t sample_rate_hz) {
    if (sample_rate_hz < MIN_SAMPLE_RATE_HZ || sample_rate_hz > MAX_SAMPLE_RATE_HZ) {
        sample_rate_hz = DEFAULT_SAMPLE_RATE_HZ;
    }
    _sample_rate_hz = sample_rate_hz;

    _write_idx = 0;
    _read_idx = 0;
    _sample_in_frame = 0;
    _frame_sequence = 0;
    _dropped_frames = 0;
    _decimation_accumulator = 0;
    _decimation_count = 0;

    uint64_t period_us = 1000000ULL / _sample_rate_hz;
    if (period_us < 10) period_us = 10;

    esp_timer_create_args_t timer_args = {
        .callback = &adc_timer_callback,
        .arg = nullptr,
        .dispatch_method = ESP_TIMER_TASK,
        .name = "adc_100k"
    };

    if (s_adc_timer) {
        esp_timer_stop(s_adc_timer);
        esp_timer_delete(s_adc_timer);
        s_adc_timer = nullptr;
    }

    esp_err_t err = esp_timer_create(&timer_args, &s_adc_timer);
    if (err != ESP_OK) return false;

    err = esp_timer_start_periodic(s_adc_timer, period_us);
    if (err != ESP_OK) return false;

    _sampling_active = true;
    return true;
}

void AdcAD40xx::stop_sampling() {
    if (s_adc_timer) {
        esp_timer_stop(s_adc_timer);
        esp_timer_delete(s_adc_timer);
        s_adc_timer = nullptr;
    }
    _sampling_active = false;
}

void AdcAD40xx::set_route(uint8_t route) {
    if (route == 2) {
        digitalWrite(PIN_ROUTE_SEL, HIGH);
        _active_route = 2;
    } else {
        digitalWrite(PIN_ROUTE_SEL, LOW);
        _active_route = 1;
    }
}

void IRAM_ATTR AdcAD40xx::on_timer_tick() {
    if (!_sampling_active) return;

    // Direct GPIO toggle for low jitter conversion trigger
    gpio_set_level((gpio_num_t)PIN_ADC_CNV, 1);
    // AD40xx conversion time ~290ns
    __asm__ __volatile__("nop; nop; nop; nop; nop; nop; nop; nop;");
    gpio_set_level((gpio_num_t)PIN_ADC_CNV, 0);

    // Read SPI sample
    uint16_t raw = _spi->transfer16(0x0000);
    int16_t sample = (int16_t)raw;

    // Buffer sample into current frame
    uint8_t w_idx = _write_idx;
    StreamFrame* curr_frame = &_frames[w_idx];

    if (_sample_in_frame == 0) {
        curr_frame->timestamp_us = (uint32_t)esp_timer_get_time();
        curr_frame->frame_index = _frame_sequence;
        curr_frame->status_flags = STATUS_STREAMING_ACTIVE;
    }

    curr_frame->samples[_sample_in_frame++] = sample;

    // Decimation calculation for Web Portal
    _decimation_accumulator += sample;
    _decimation_count++;
    if (_decimation_count >= WEBSOCKET_DECIMATION_FACTOR) {
        _latest_decimated = (int16_t)(_decimation_accumulator / _decimation_count);
        _decimation_accumulator = 0;
        _decimation_count = 0;
    }

    // Check if frame is complete
    if (_sample_in_frame >= SAMPLES_PER_FRAME) {
        curr_frame->crc16 = calculate_crc16((const uint8_t*)curr_frame, sizeof(StreamFrame) - sizeof(uint16_t));
        _sample_in_frame = 0;
        _frame_sequence++;

        uint8_t next_write = (w_idx + 1) % RING_BUFFER_FRAME_COUNT;
        if (next_write == _read_idx) {
            // Overflow: drop oldest frame
            _dropped_frames++;
            _read_idx = (_read_idx + 1) % RING_BUFFER_FRAME_COUNT;
        }
        _write_idx = next_write;
    }
}

bool AdcAD40xx::get_next_frame(StreamFrame* out_frame) {
    if (_read_idx == _write_idx) {
        return false; // No frame available
    }

    uint8_t r_idx = _read_idx;
    memcpy(out_frame, &_frames[r_idx], sizeof(StreamFrame));
    _read_idx = (r_idx + 1) % RING_BUFFER_FRAME_COUNT;
    return true;
}
