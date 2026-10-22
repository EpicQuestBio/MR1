/*
 * Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
 * Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
 * SPDX-License-Identifier: CC0-1.0
 */

/**
 * @file pinout.h
 * @brief Canonical Hardware Pin Mapping for MR1 Nanopore Reader (MR1 Board)
 * 
 * Target MCU: ESP32-S3-MINI-1U
 * Schematics: MR1 (Microcontroller, Ignition, Insturmentation, Power)
 */

#pragma once

#include <stdint.h>

// =============================================================================
// Analog-to-Digital Converter (AD40xxBRMZ - U10 on Insturmentation)
// =============================================================================
#define PIN_ADC_CNV         11  // Conversion Start / Chip Select (Net: /Insturmentation/DAC_EN)
#define PIN_ADC_SCK         10  // Serial Clock up to 40MHz (Net: /Insturmentation/DAC_CLK)
#define PIN_ADC_SDO          9  // Serial Data Out / MISO (Net: /Microcontroller/DAC_Dout)

// =============================================================================
// Digital-to-Analog Converter (MCP4822 - U9 on Ignition)
// =============================================================================
#define PIN_DAC_CS           6  // Chip Select (Active Low) (Net: /Ignition/CS_)
#define PIN_DAC_SCK          7  // Serial Clock (Net: /Ignition/SCK)
#define PIN_DAC_SDI          8  // Serial Data In / MOSI (Net: /Ignition/SDI)
#define PIN_DAC_LDAC         5  // Latch Update (Active Low) (Net: /Ignition/LDAC_)

// =============================================================================
// Native USB Interface (J3 Receptacle)
// =============================================================================
#define PIN_USB_DM          19  // USB D- (Net: /Power/D-)
#define PIN_USB_DP          20  // USB D+ (Net: /Power/D+)

// =============================================================================
// USB-C Sideband Use (SBU) & I2C Auto-Polarity Interface
// =============================================================================
#define PIN_USB_SBU1        12  // USB-C SBU1 (Pin A8)
#define PIN_USB_SBU2        13  // USB-C SBU2 (Pin B8)
#define PIN_SBU_MUX_SEL     14  // Hardware cross-multiplexer select (optional)

// =============================================================================
// External Peristaltic Pump Port (J22 - B4B-PH Connector)
// =============================================================================
#define PIN_PUMP_TX         17  // UART TX to Pump Module (J22 Pin 2)
#define PIN_PUMP_RX         47  // UART RX from Pump Module (J22 Pin 3)
#define PUMP_UART_NUM        1  // Hardware UART Port 1

// =============================================================================
// Safety & Leak Detection (Weep Moats & Conductivity Sensor)
// =============================================================================
#define PIN_LEAK_SENSE       1  // Leak detect sense line (Active Low or Analog Threshold)

// =============================================================================
// Host / Debug UART (Optional Header / Programming Console)
// =============================================================================
#define PIN_DEBUG_TX        43  // TXD0
#define PIN_DEBUG_RX        44  // RXD0
