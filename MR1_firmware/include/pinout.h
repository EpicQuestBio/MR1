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
// Analog-to-Digital Converter & Readout Route Selection
// =============================================================================
#define PIN_ADC_CNV          5  // Conversion Start / Chip Select (Net: /Insturmentation/ADC_EN via R36)
#define PIN_ADC_SCK          8  // Serial Clock up to 40MHz (Net: /Insturmentation/ADC_CLK via R37)
#define PIN_ADC_SDO          6  // Serial Data Out / MISO (Net: /Insturmentation/ADC_SDO via R10)
#define PIN_ADC_SDI          4  // Serial Data In / MOSI (Net: /Insturmentation/ADC_SDI via R33)
#define PIN_ROUTE_SEL        7  // Readout Route Multiplexer Select (Net: /Insturmentation/ROUTE_SEL via R27)

// =============================================================================
// Digital-to-Analog Converter (MCP4822 - U9 on Ignition)
// =============================================================================
#define PIN_DAC_CS          12  // Chip Select (Active Low) (Net: /Ignition/CS_ via R41)
#define PIN_DAC_SCK         11  // Serial Clock (Net: /Ignition/SCK via R28)
#define PIN_DAC_SDI         10  // Serial Data In / MOSI (Net: /Ignition/SDI via R40)
#define PIN_DAC_LDAC         9  // Latch Update (Active Low) (Net: /Ignition/LDAC_ via R39)

// =============================================================================
// Native USB Interface (J3 Receptacle)
// =============================================================================
#define PIN_USB_DM          19  // USB D- (Net: /Power/D- via R16)
#define PIN_USB_DP          20  // USB D+ (Net: /Power/D+ via R15)

// =============================================================================
// USB-C Sideband Use (SBU) & I2C Auto-Polarity Interface
// =============================================================================
#define PIN_USB_SBU1        21  // USB-C SBU1 (Pin A8 via R53)
#define PIN_USB_SBU2        26  // USB-C SBU2 (Pin B8 via R54)
#define PIN_SBU_MUX_SEL     14  // Hardware cross-multiplexer select (optional)

// =============================================================================
// External Peristaltic Pump Port (J22 - B4B-PH Connector)
// =============================================================================
#define PIN_PUMP_TX         33  // UART TX to Pump Module (J22 Pin 2 via GPIO33)
#define PIN_PUMP_RX         47  // UART RX from Pump Module (J22 Pin 3 via GPIO47)
#define PUMP_UART_NUM        1  // Hardware UART Port 1

// =============================================================================
// Safety & Power Supervision (Power Good Monitors & Fault Interlocks)
// =============================================================================
#define PIN_PG_VSSA          1  // Power Good negative supply (Net: /Power/PG_VSSA via R57)
#define PIN_PG_VDDA          2  // Power Good positive supply (Net: /Power/PG_VDDA via R58)
#define PIN_PG_CP            3  // Power Good charge pump LM27762 (Net: /Power/PG_CP via R59)
#define PIN_LEAK_SENSE       PIN_PG_VSSA  // VSSA power rail fault trips emergency shutoff

// =============================================================================
// Host / Debug UART (Optional Header / Programming Console)
// =============================================================================
#define PIN_DEBUG_TX        43  // TXD0
#define PIN_DEBUG_RX        44  // RXD0
