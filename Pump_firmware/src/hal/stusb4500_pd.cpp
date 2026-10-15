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

#include "stusb4500_pd.h"

STUSB4500PD::STUSB4500PD(TwoWire& wire, uint8_t i2c_addr)
    : wire_(wire), addr_(i2c_addr), active_pdo_(PDO_5V), contract_active_(false) {}

uint8_t STUSB4500PD::readReg(uint8_t reg) {
    wire_.beginTransmission(addr_);
    wire_.write(reg);
    if (wire_.endTransmission() != 0) return 0;
    if (wire_.requestFrom(addr_, (uint8_t)1) == 1) {
        return wire_.read();
    }
    return 0;
}

bool STUSB4500PD::writeReg(uint8_t reg, uint8_t val) {
    wire_.beginTransmission(addr_);
    wire_.write(reg);
    wire_.write(val);
    return (wire_.endTransmission() == 0);
}

bool STUSB4500PD::begin() {
    uint8_t status = readReg(REG_PORT_STATUS_0);
    // Bit 0 indicates source connection active
    if (status & 0x01) {
        contract_active_ = true;
        getActiveContract();
        return true;
    }
    contract_active_ = false;
    return false;
}

bool STUSB4500PD::requestProfile(PDOContract profile) {
    // STUSB4500 dynamic PDO request: write to DPM_PDO_NUM
    uint8_t pdo_idx = (uint8_t)profile;
    if (pdo_idx < 1 || pdo_idx > 3) pdo_idx = 1;

    bool ok = writeReg(REG_DPM_PDO_NUM, pdo_idx);
    if (ok) {
        active_pdo_ = profile;
        contract_active_ = true;
    }
    return ok;
}

STUSB4500PD::PDOContract STUSB4500PD::getActiveContract() {
    uint8_t rdo = readReg(REG_RDO_REG_STATUS);
    uint8_t obj_pos = (rdo >> 4) & 0x07;
    switch (obj_pos) {
        case 1: active_pdo_ = PDO_5V; break;
        case 2: active_pdo_ = PDO_9V; break;
        case 3: active_pdo_ = PDO_12V; break;
        case 4: active_pdo_ = PDO_15V; break;
        case 5: active_pdo_ = PDO_20V; break;
        default: active_pdo_ = PDO_5V; break;
    }
    return active_pdo_;
}

float STUSB4500PD::getVbusVoltageMv() {
    switch (active_pdo_) {
        case PDO_5V:  return 5000.0f;
        case PDO_9V:  return 9000.0f;
        case PDO_12V: return 12000.0f;
        case PDO_15V: return 15000.0f;
        case PDO_20V: return 20000.0f;
        default:      return 5000.0f;
    }
}
