# ESP32-S3 Nanopore Firmware Stack

This directory contains the production C++ firmware for the **Sentinel Nanopore Reader (MR1 Main Board)** running on an **ESP32-S3** microcontroller.

---

## 1. Overview & Key Capabilities

- **100 kHz Continuous Sampling**: Hardware timer triggering SPI DMA transfers from the AD40xx high-speed analog-to-digital converter.
- **Native USB CDC-ACM Streaming**: Zero-driver high-throughput binary streaming directly to a host PC or Python data acquisition script.
- **Bipolar Pore Bias DAC Control**: Software-controlled dual MCP4822 12-bit DACs providing sub-millivolt precision pore bias (-1.587V to +1.587V) and programmable wetting/clearing pulses.
- **Dual-Core FreeRTOS Partitioning**: Complete isolation of real-time sampling (Core 1) from Wi-Fi networking and pump communications (Core 0).
- **Leak Detection Safety Interlock**: Hardware interrupt and polling on the cartridge weep-hole moat (GPIO1) executing emergency shutoff (<1 ms) of external pumps and zeroing pore bias.
- **Bidirectional Pump UART Protocol**: Serial link over connector J22 to the dual-channel peristaltic pump module.
- **Embedded Web Portal & Oscilloscope**: Responsive HTML5/WebSocket oscilloscope served directly from ESP32 flash with live voltage sliders and pump actuation buttons.

---

## 2. Hardware Pinout Mapping

All pin definitions mirror the canonical **KiCad MR1 schematic** (`include/pinout.h`):

| Signal Name | ESP32-S3 GPIO | Function / Bus | Connection / Component |
| :--- | :--- | :--- | :--- |
| **ADC_CNV** | GPIO 11 | SPI DMA / Timer | AD40xx Conversion Start trigger |
| **ADC_SCK** | GPIO 10 | SPI Clock (up to 40 MHz) | AD40xx Serial Clock |
| **ADC_SDO** | GPIO 9 | SPI MISO / DMA | AD40xx Data Output |
| **DAC_CS_** | GPIO 6 | SPI Chip Select (Active Low) | MCP4822 DAC Chip Select |
| **DAC_SCK** | GPIO 7 | SPI Clock (20 MHz) | MCP4822 SPI Bus Clock |
| **DAC_SDI** | GPIO 8 | SPI MOSI | MCP4822 Serial Data In |
| **DAC_LDAC_** | GPIO 5 | Synchronous Latch (Active Low) | MCP4822 Dual Channel Simultaneous Update |
| **USB_DM** | GPIO 19 | Native USB D- | Direct USB-C receptacle |
| **USB_DP** | GPIO 20 | Native USB D+ | Direct USB-C receptacle |
| **PUMP_TX** | GPIO 17 | UART TX (115200 baud) | J22 Pump Connector Pin 2 |
| **PUMP_RX** | GPIO 47 | UART RX (115200 baud) | J22 Pump Connector Pin 3 |
| **LEAK_SENSE** | GPIO 1 | ADC1_CH0 / Digital Input | Flow cell weep moat conductive traces |
| **STATUS_LED** | GPIO 38 | Digital Output | Onboard RGB / status indicator |

---

## 3. Dual-Core FreeRTOS Architecture

To prevent Wi-Fi stack jitter from corrupting 100 kHz continuous ADC acquisition, tasks are strictly pinned to dedicated CPU cores:

```
[ Core 1: Acquisition Engine ]
  └── adc_usb_task (Priority: MAX - 1)
        ├── Hardware Timer triggers ADC conversion at 100,000 Hz
        ├── SPI DMA double-buffering fills 64-sample frames
        └── Writes binary StreamFrame packets to Native USB CDC

[ Core 0: Supervision & Telemetry ]
  ├── leak_monitor_task (Priority: MAX - 2)
  │     └── Continuous weep-sensor monitoring & emergency interlock
  ├── pump_supervision_task (Priority: 2)
  │     └── UART packet framing to peristaltic pump module
  └── wifi_web_task (Priority: 1)
        ├── AsyncWebServer & WebSocket server
        └── Decimates 100 kHz stream to 100 Hz for web canvas display
```

---

## 4. Communication Protocols

### High-Throughput Binary USB Protocol
Stream data is emitted over Native USB CDC in structured binary frames (`StreamFrame`):

```cpp
struct __attribute__((packed)) StreamFrame {
    uint16_t sync_word;        // 0xAA55
    uint32_t sequence_id;      // Monotonically increasing frame counter
    uint64_t timestamp_us;     // Microsecond timestamp from ESP timer
    uint16_t sample_count;     // Number of samples (fixed 64)
    int32_t  samples[64];      // Signed ADC counts (16/18-bit sign-extended)
    uint16_t status_flags;     // Bit 0: Leak, Bit 1: Pump Active, Bit 2: Clipping
    uint16_t crc16;            // CRC-16-CCITT across entire packet payload
};
```

### External Pump Module Protocol (UART @ 115200)
Packets between MR1 and the pump controller use a 5-byte framed protocol with XOR checksum:
- `Byte 0`: Sync Header 1 (`0x55`)
- `Byte 1`: Sync Header 2 (`0xAA`)
- `Byte 2`: Command (`0x01` Set Flow, `0x02` Direction, `0x03` Status, `0x00` Emergency Stop)
- `Byte 3`: Parameter 1 (Pump channel / Speed high byte)
- `Byte 4`: Parameter 2 (Speed low byte)
- `Byte 5`: Checksum (`Byte 2 ^ Byte 3 ^ Byte 4`)

---

## 5. Building & Flashing

### Using PlatformIO Core (CLI)
```bash
cd firmware
pio run                          # Compile release firmware
pio run --target upload          # Flash via USB CDC
pio device monitor               # Open serial monitor
```

### Staging Release Binaries via Universal Exporter
The top-level project Makefile compiles and copies all binaries to `exports/firmware/`:
```bash
# From repository root:
make export-firmware
```
Staged deliverables include:
- `exports/firmware/firmware.bin` (Application binary)
- `exports/firmware/bootloader.bin` (ESP32-S3 2nd-stage bootloader)
- `exports/firmware/partitions.bin` (Flash partition table)

---

## 6. Testing & Validation

Firmware protocols are validated by Python unit tests in `tests/test_firmware_protocol.py`:
- `test_crc16_calculation`: Asserts bit-level CRC-16-CCITT parity with firmware C++ implementation.
- `test_stream_frame_packing_and_unpacking`: Validates memory alignment, padding, and packet unpacking.
- `test_pore_bias_voltage_clamping_and_mapping`: Asserts linear mapping between physical millivolts and 12-bit DAC registers (-1.587V to +1.587V).
- `test_pump_packet_xor_checksum`: Verifies UART checksum calculation and error rejection.

Run tests with:
```bash
python tests/test_firmware_protocol.py
```
