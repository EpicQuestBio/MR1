#pragma once
#include <Arduino.h>
#include <Wire.h>

/**
 * STMicroelectronics STUSB4500 Autonomous USB-PD Sink Controller Driver
 * Negotiates USB Power Delivery contracts (5V, 9V, 12V, 15V, 20V) over CC lines.
 */
class STUSB4500PD {
public:
    enum PDOContract {
        PDO_5V = 1,
        PDO_9V = 2,
        PDO_12V = 3,
        PDO_15V = 4,
        PDO_20V = 5,
        PDO_UNKNOWN = 0
    };

    STUSB4500PD(TwoWire& wire, uint8_t i2c_addr = 0x28);

    bool begin();
    bool requestProfile(PDOContract profile);
    PDOContract getActiveContract();
    float getVbusVoltageMv();
    bool isContractActive() const { return contract_active_; }

private:
    TwoWire& wire_;
    uint8_t addr_;
    PDOContract active_pdo_;
    bool contract_active_;

    uint8_t readReg(uint8_t reg);
    bool writeReg(uint8_t reg, uint8_t val);

    static constexpr uint8_t REG_ALERT_STATUS_1 = 0x0B;
    static constexpr uint8_t REG_PORT_STATUS_0   = 0x0D;
    static constexpr uint8_t REG_DPM_PDO_NUM     = 0x70;
    static constexpr uint8_t REG_RDO_REG_STATUS  = 0x91;
};
