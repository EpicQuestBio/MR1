/*
 * Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
 * Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
 * SPDX-License-Identifier: CC0-1.0
 */

#pragma once
#include <Arduino.h>

/**
 * MR1 Pump & USB-PD Hub - Hardware Pinout Definitions
 * Target MCU: STM32G431CBU6 (UFQFPN-48, 170 MHz ARM Cortex-M4)
 * Schematic Reference: Pump/MCU_STM32.kicad_sch
 */

// =============================================================================
// I2C Buses
// =============================================================================
// I2C1: Pressure Transducers & STUSB4500 USB-PD Controller
#define PIN_I2C1_SCL            PB8
#define PIN_I2C1_SDA            PB9

// I2C2 / UART: USB-C SBU Inter-Board Link to MR1 Reader
#define PIN_SBU_I2C_SCL         PB10
#define PIN_SBU_I2C_SDA         PB11
#define PIN_SBU_UART_TX         PA2
#define PIN_SBU_UART_RX         PA3

// =============================================================================
// Motor Drivers (TI DRV8837C)
// =============================================================================
// Pump 1: Cis Chamber Feed Line
#define PIN_PUMP1_PWM           PA8     // TIM1_CH1 (Hardware PWM)
#define PIN_PUMP1_DIR           PB12    // Direction (HIGH = Forward, LOW = Reverse)

// Pump 2: Trans Chamber Recirculation / Waste Line
#define PIN_PUMP2_PWM           PA9     // TIM1_CH2 (Hardware PWM)
#define PIN_PUMP2_DIR           PB13    // Direction

// Emergency Stop Hardware Interlock Line
#define PIN_ESTOP_TRIGGER       PB0     // Active LOW (EXTI0 interrupt)

// =============================================================================
// Power Management & Multiplexer Control
// =============================================================================
#define PIN_MR1_PWR_EN          PA4     // High-side enable for +5V_MR1_CLEAN buck rail
#define PIN_USB_SEL_PASS        PA5     // Controls TS3USB221 USB pass-through mux

// External Alert Lines (Open-drain, active LOW)
#define PIN_PD_ALERT            PB1     // STUSB4500 Interrupt
#define PIN_PRESS_ALERT         PB2     // Pressure Transducer Alert

// =============================================================================
// Diagnostic Status LEDs
// =============================================================================
#define PIN_LED_FAULT           PC13    // Red LED (Occlusion / Overpressure / ESTOP)
#define PIN_LED_PUMP1           PB14    // Yellow LED (Pump 1 Cis active)
#define PIN_LED_PUMP2           PB15    // Yellow LED (Pump 2 Trans active)
#define PIN_LED_PD_READY        PA10    // Green LED (Negotiated PD contract active)
#define PIN_LED_MR1_5V          PA15    // Blue LED (+5V clean rail to MR1 enabled)
