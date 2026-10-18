# MR1 Pump & USB-PD Hub Firmware

This directory contains the production C++ firmware for the **MR1 Pump & USB-PD Hub Board (`Pump/`)** targeting the **STM32G431CBU6** microcontroller (ARM Cortex-M4 @ 170 MHz).

---

## 1. Overview & Capabilities

The Pump Subsystem manages automated fluid delivery and power distribution for the MR1 Nanopore Reader:

- **Autonomous USB-PD Negotiation**: Manages the STUSB4500 autonomous USB-PD sink controller to negotiate 9V/12V/15V/20V power profiles from host USB-C power supplies.
- **Ultra-Clean +5V Output**: Controls the high-efficiency step-down buck converter and LC $\pi$-filter supplying clean, isolated 5V power to the MR1 Reader analog frontend.
- **Dual Peristaltic Motor Control**: Hardware TIM1 PWM velocity control and direction management for two TI DRV8837C motor drivers:
  - **Pump 1**: Cis chamber fluid feed ($210^\circ$).
  - **Pump 2**: Trans chamber recirculation and waste drain ($330^\circ$).
- **Dual Pressure Transducers**: Real-time I2C telemetry from dual Honeywell TruStability / ABP2 sensors:
  - Sensor 1 (0-15 psi gauge): Monitors Cis chamber inlet pressure.
  - Sensor 2 (0-5 psi gauge): Monitors Trans chamber differential/recirculation pressure.
- **Hardware Emergency Stop**: Dedicated active-low EXTI interrupt (`PIN_ESTOP_TRIGGER` on PB0) that instantly halts both motors upon leak detection or overpressure breach.
- **SBU Inter-Board Link**: Communication back to the MR1 Reader over USB-C Sideband Use (SBU1/SBU2) pins via I2C or UART.
- **High-Speed USB 2.0 Pass-Through**: Directs the TI TS3USB221 multiplexer to pass high-speed telemetry directly from MR1 to the host laptop without MCU buffering.

---

## 2. Hardware Pinout

Pin mappings correspond directly to `Pump/MCU_STM32.kicad_sch` and `include/pinout.h`:

| Signal Name | STM32 Pin | Function / Peripheral | Description |
| :--- | :--- | :--- | :--- |
| **PIN_I2C1_SCL** | PB8 | I2C1 SCL | Pressure sensors & STUSB4500 bus clock |
| **PIN_I2C1_SDA** | PB9 | I2C1 SDA | Pressure sensors & STUSB4500 bus data |
| **PIN_SBU_I2C_SCL** | PB10 | I2C2 SCL | Inter-board SBU I2C link to MR1 |
| **PIN_SBU_I2C_SDA** | PB11 | I2C2 SDA | Inter-board SBU I2C link to MR1 |
| **PIN_SBU_UART_TX** | PA2 | USART2 TX | Fallback SBU serial telemetry |
| **PIN_SBU_UART_RX** | PA3 | USART2 RX | Fallback SBU serial telemetry |
| **PIN_PUMP1_PWM** | PA8 | TIM1_CH1 (PWM) | Cis pump motor speed control |
| **PIN_PUMP1_DIR** | PB12 | GPIO Output | Cis pump forward/reverse direction |
| **PIN_PUMP2_PWM** | PA9 | TIM1_CH2 (PWM) | Trans pump motor speed control |
| **PIN_PUMP2_DIR** | PB13 | GPIO Output | Trans pump forward/reverse direction |
| **PIN_ESTOP_TRIGGER** | PB0 | EXTI0 Interrupt | Hardware leak detector emergency stop |
| **PIN_MR1_PWR_EN** | PA4 | GPIO Output | High-side enable for +5V_MR1_CLEAN rail |
| **PIN_USB_SEL_PASS** | PA5 | GPIO Output | TS3USB221 USB pass-through mux switch |
| **PIN_STATUS_LED** | PB2 | GPIO Output | Heartbeat / operational status indicator |

---

## 3. Build & Upload Instructions

The firmware is built using **PlatformIO Core**:

```bash
# Navigate to the pump firmware directory
cd Pump_firmware

# Compile the firmware
pio run

# Upload via ST-Link (SWD interface)
pio run --target upload
```

Configuration parameters (maximum allowable pressure limits, PWM base frequencies, and default flow rates) are defined in `include/config.h`.
