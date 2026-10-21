/*
 * Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
 * Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
 * SPDX-License-Identifier: CC0-1.0
 */

#include <Arduino.h>
#include <Wire.h>
#include "pinout.h"
#include "config.h"
#include "hal/abp2_pressure.h"
#include "hal/drv8837c_motor.h"
#include "hal/stusb4500_pd.h"
#include "comm/sbu_link.h"

// Hardware Instances
ABP2Sensor sensorCis(Wire, I2C_ADDR_ABP2_CIS, 0.0f, 15.0f);
ABP2Sensor sensorTrans(Wire, I2C_ADDR_ABP2_TRANS, 0.0f, 5.0f);
DRV8837CMotor pumpCis(PIN_PUMP1_PWM, PIN_PUMP1_DIR, UL_PER_REVOLUTION);
DRV8837CMotor pumpTrans(PIN_PUMP2_PWM, PIN_PUMP2_DIR, UL_PER_REVOLUTION);
STUSB4500PD pdController(Wire, I2C_ADDR_STUSB4500);
SbuLink sbuLink(Serial2, 115200);

// Global State
volatile bool g_estop_tripped = false;
bool g_overpressure_fault = false;
uint32_t g_last_pressure_ms = 0;
uint32_t g_last_telemetry_ms = 0;
uint32_t g_last_heartbeat_ms = 0;
uint32_t g_last_loop_ms = 0;

void handleHardwareEstop() {
    g_estop_tripped = true;
    pumpCis.emergencyStop();
    pumpTrans.emergencyStop();
}

void handleSbuCommand(uint8_t cmd, uint16_t param) {
    switch (cmd) {
        case SbuLink::CMD_RUN_FWD:
            if (!g_estop_tripped && !g_overpressure_fault) {
                pumpCis.setFlowRate((float)param, DRV8837CMotor::DIR_FORWARD);
            }
            break;

        case SbuLink::CMD_RUN_REV:
            if (!g_estop_tripped && !g_overpressure_fault) {
                pumpCis.setFlowRate((float)param, DRV8837CMotor::DIR_REVERSE);
            }
            break;

        case SbuLink::CMD_STOP:
            pumpCis.stop();
            pumpTrans.stop();
            break;

        case SbuLink::CMD_ESTOP:
            handleHardwareEstop();
            break;

        case SbuLink::CMD_HEARTBEAT:
            sbuLink.sendPacket(SbuLink::CMD_HEARTBEAT, 0);
            break;

        default:
            break;
    }
}

void setup() {
    // 1. Diagnostic LEDs
    pinMode(PIN_LED_FAULT, OUTPUT);
    pinMode(PIN_LED_PUMP1, OUTPUT);
    pinMode(PIN_LED_PUMP2, OUTPUT);
    pinMode(PIN_LED_PD_READY, OUTPUT);
    pinMode(PIN_LED_MR1_5V, OUTPUT);

    digitalWrite(PIN_LED_FAULT, LOW);
    digitalWrite(PIN_LED_PUMP1, LOW);
    digitalWrite(PIN_LED_PUMP2, LOW);
    digitalWrite(PIN_LED_PD_READY, LOW);
    digitalWrite(PIN_LED_MR1_5V, LOW);

    // 2. Power enables
    pinMode(PIN_MR1_PWR_EN, OUTPUT);
    pinMode(PIN_USB_SEL_PASS, OUTPUT);
    digitalWrite(PIN_MR1_PWR_EN, HIGH);    // Power on MR1 clean +5V buck
    digitalWrite(PIN_USB_SEL_PASS, HIGH);   // Enable USB pass-through multiplexer
    digitalWrite(PIN_LED_MR1_5V, HIGH);

    // 3. Hardware Emergency Stop Interlock
    pinMode(PIN_ESTOP_TRIGGER, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_ESTOP_TRIGGER), handleHardwareEstop, FALLING);

    // 4. Initialize I2C Bus & Peripherals
    Wire.begin();
    Wire.setClock(400000); // 400 kHz Fast I2C

    sensorCis.begin();
    sensorTrans.begin();

    // 5. USB-PD Negotiation
    if (pdController.begin()) {
        pdController.requestProfile(STUSB4500PD::PDO_9V); // Request 9V for high-torque motor rail
        digitalWrite(PIN_LED_PD_READY, HIGH);
    }

    // 6. Motors
    pumpCis.begin();
    pumpTrans.begin();

    // 7. SBU Link
    sbuLink.setCommandHandler(handleSbuCommand);
    sbuLink.begin();

    g_last_loop_ms = millis();
}

void loop() {
    uint32_t now = millis();
    uint32_t dt_ms = now - g_last_loop_ms;
    g_last_loop_ms = now;

    // 1. Service Communications
    sbuLink.update();

    // 2. Pressure Monitoring Loop (100 Hz)
    if (now - g_last_pressure_ms >= 10) {
        g_last_pressure_ms = now;

        sensorCis.read();
        sensorTrans.read();

        float p_cis = sensorCis.getPressurePsi();
        float p_trans = sensorTrans.getPressurePsi();

        // Safety overpressure check
        if (p_cis > MAX_PRESSURE_CIS_PSI || p_trans > MAX_PRESSURE_TRANS_PSI) {
            g_overpressure_fault = true;
            pumpCis.emergencyStop();
            pumpTrans.emergencyStop();
            digitalWrite(PIN_LED_FAULT, HIGH);
            sbuLink.sendPacket(SbuLink::CMD_ESTOP, 0x0001); // Signal overpressure to MR1
        }
    }

    // 3. Motor Updates
    pumpCis.update(dt_ms);
    pumpTrans.update(dt_ms);

    digitalWrite(PIN_LED_PUMP1, pumpCis.isRunning() ? HIGH : LOW);
    digitalWrite(PIN_LED_PUMP2, pumpTrans.isRunning() ? HIGH : LOW);

    // 4. SBU Telemetry Transmission (20 Hz)
    if (now - g_last_telemetry_ms >= 50) {
        g_last_telemetry_ms = now;
        sbuLink.sendPressureTelemetry(sensorCis.getPressurePsi(), sensorTrans.getPressurePsi());
    }

    // 5. Heartbeat & LED Fault Indicator
    if (now - g_last_heartbeat_ms >= 500) {
        g_last_heartbeat_ms = now;
        if (g_estop_tripped || g_overpressure_fault) {
            digitalWrite(PIN_LED_FAULT, !digitalRead(PIN_LED_FAULT)); // Fast flash fault
        } else {
            digitalWrite(PIN_LED_FAULT, LOW);
        }
    }
}
