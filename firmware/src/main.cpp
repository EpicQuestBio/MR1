/**
 * @file main.cpp
 * @brief Sentinel Nanopore Reader (MR1 Board) Firmware Main Entry Point
 * 
 * Hardware Architecture:
 * - Dual-Core Xtensa LX7 @ 240 MHz (ESP32-S3-MINI-1U)
 * - Core 1: Dedicated 100 kHz Hard Real-Time SPI+DMA Acquisition & USB CDC Streaming
 * - Core 0: Wi-Fi SoftAP, Web Portal, Pump UART Protocol & Leak Protection Supervisor
 */

#include <Arduino.h>
#include "pinout.h"
#include "config.h"
#include "hal/adc_ad40xx.h"
#include "hal/dac_mcp4822.h"
#include "hal/leak_detector.h"
#include "comm/pump_uart.h"
#include "comm/usb_cdc_stream.h"
#include "web/web_portal.h"

// Task handles
static TaskHandle_t s_acquisition_task_handle = nullptr;
static TaskHandle_t s_supervisor_task_handle  = nullptr;

/**
 * @brief Core 1: Real-Time High-Speed Acquisition & Native USB Streamer Task
 */
void TaskAcquisition(void* pvParameters) {
    (void)pvParameters;

    for (;;) {
        // High-speed drain of ADC frames over USB CDC
        UsbStream.process_streaming();
    }
}

/**
 * @brief Core 0: Supervisor Task (Wi-Fi, Web Portal, Pump UART, Leak Monitoring)
 */
void TaskSupervisor(void* pvParameters) {
    (void)pvParameters;

    for (;;) {
        // 1. Process host commands over native USB CDC
        UsbStream.process_commands();

        // 2. Service leak detector & weep moat check
        Leak.update();

        // 3. Service DAC pulse timing
        Dac.update();

        // 4. Service external pump module communication over J22
        Pump.update();

        // 5. Service Web Portal HTTP requests
        Portal.update();

        // Manage Wi-Fi / USB trade-off: throttle portal when USB streaming at 100 kHz
        if (UsbStream.is_streaming()) {
            Portal.set_active(false); // Silence Wi-Fi broadcast to eliminate radio DMA contention
            vTaskDelay(pdMS_TO_TICKS(10));
        } else {
            Portal.set_active(true);
            vTaskDelay(pdMS_TO_TICKS(2));
        }
    }
}

void setup() {
    // 1. Initialize native USB CDC
    UsbStream.begin();

    // 2. Initialize MCP4822 DAC (Ignition sheet)
    Dac.begin();

    // 3. Initialize AD40xx ADC (Insturmentation sheet)
    Adc.begin();

    // 4. Initialize external pump UART port (J22 connector)
    Pump.begin();

    // 5. Initialize weep moat / leak sensor with automatic emergency shutoff hook
    Leak.begin();
    Leak.set_emergency_callback([]() {
        Pump.emergency_stop();
        Dac.emergency_zero();
    });

    // 6. Initialize Wi-Fi Access Point & Web Portal
    Portal.begin();

    // 7. Spawn dedicated FreeRTOS tasks pinned to respective Xtensa cores
    xTaskCreatePinnedToCore(
        TaskAcquisition,
        "AcquisitionCore1",
        8192,
        nullptr,
        configMAX_PRIORITIES - 1, // Highest priority for real-time streaming
        &s_acquisition_task_handle,
        1                          // Core 1
    );

    xTaskCreatePinnedToCore(
        TaskSupervisor,
        "SupervisorCore0",
        8192,
        nullptr,
        2,                         // Low-to-medium priority for networking/UI
        &s_supervisor_task_handle,
        0                          // Core 0
    );
}

void loop() {
    // Both worker tasks are pinned to Core 0 and Core 1.
    // Yield the default Arduino task.
    vTaskDelay(pdMS_TO_TICKS(1000));
}
