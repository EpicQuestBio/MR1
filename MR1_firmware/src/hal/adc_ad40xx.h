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
 * @file adc_ad40xx.h
 * @brief High-Speed AD40xx Differential SAR ADC Driver (100 kHz Sampling Engine)
 */

#pragma once

#include <Arduino.h>
#include <SPI.h>
#include "pinout.h"
#include "config.h"
#include "protocol.h"

class AdcAD40xx {
public:
    AdcAD40xx();

    /**
     * @brief Initialize SPI peripheral, GPIOs, and DMA buffers
     */
    void begin();

    /**
     * @brief Start continuous hardware-timed sampling at specified frequency
     * @param sample_rate_hz Target rate (up to 100000 Hz)
     */
    bool start_sampling(uint32_t sample_rate_hz = DEFAULT_SAMPLE_RATE_HZ);

    /**
     * @brief Stop continuous sampling
     */
    void stop_sampling();

    /**
     * @brief Single-shot software read of differential sample
     * @return 16-bit signed differential code
     */
    int16_t read_single();

    /**
     * @brief Fetch the next completed StreamFrame from the ring buffer
     * @param out_frame Destination frame pointer
     * @return true if a frame was dequeued, false if buffer empty
     */
    bool get_next_frame(StreamFrame* out_frame);

    /**
     * @brief Fetch latest decimated sample for Web Portal visualization (1 kHz)
     */
    int16_t get_latest_decimated_sample() const { return _latest_decimated; }

    /**
     * @brief Total number of frames captured since start
     */
    uint32_t get_total_frames() const { return _frame_sequence; }

    /**
     * @brief Total number of dropped frames due to ring buffer overflow
     */
    uint32_t get_dropped_frames() const { return _dropped_frames; }

    /**
     * @brief Core ISR handler called by hardware timer
     */
    void IRAM_ATTR on_timer_tick();

    bool is_sampling() const { return _sampling_active; }

private:
    SPIClass*   _spi;
    bool        _sampling_active;
    uint32_t    _sample_rate_hz;
    uint32_t    _frame_sequence;
    uint32_t    _dropped_frames;

    // Ping-pong double buffers
    StreamFrame _frames[RING_BUFFER_FRAME_COUNT];
    volatile uint8_t  _write_idx;
    volatile uint8_t  _read_idx;
    volatile uint16_t _sample_in_frame;

    // Decimation tracking
    int32_t  _decimation_accumulator;
    uint16_t _decimation_count;
    int16_t  _latest_decimated;
};

extern AdcAD40xx Adc;
