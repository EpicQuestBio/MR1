#include "drv8837c_motor.h"

DRV8837CMotor::DRV8837CMotor(uint8_t pwm_pin, uint8_t dir_pin, float ul_per_rev)
    : pwm_pin_(pwm_pin), dir_pin_(dir_pin), ul_per_rev_(ul_per_rev),
      current_dir_(DIR_FORWARD), current_mode_(MODE_STOPPED),
      target_rate_ul_min_(0.0f), target_volume_ul_(0.0f),
      dispensed_ul_(0.0f), current_duty_(0.0f) {}

void DRV8837CMotor::begin() {
    pinMode(dir_pin_, OUTPUT);
    digitalWrite(dir_pin_, LOW);

    pinMode(pwm_pin_, OUTPUT);
    analogWriteResolution(12);
    analogWrite(pwm_pin_, 0);

    current_mode_ = MODE_STOPPED;
}

void DRV8837CMotor::setDirection(Direction dir) {
    current_dir_ = dir;
    digitalWrite(dir_pin_, (dir == DIR_FORWARD) ? HIGH : LOW);
}

void DRV8837CMotor::setPwmDuty(float duty_pct) {
    if (duty_pct < 0.0f) duty_pct = 0.0f;
    if (duty_pct > 100.0f) duty_pct = 100.0f;
    current_duty_ = duty_pct;

    uint32_t val = (uint32_t)((duty_pct / 100.0f) * PWM_MAX_COUNT);
    analogWrite(pwm_pin_, val);
}

void DRV8837CMotor::setFlowRate(float ul_per_min, Direction dir) {
    if (ul_per_min <= 0.0f) {
        stop();
        return;
    }

    setDirection(dir);
    target_rate_ul_min_ = ul_per_min;

    // Linear speed conversion based on displacement per rev:
    // RPM = Rate (uL/min) / (uL/rev)
    float rpm = ul_per_min / ul_per_rev_;
    float duty = (rpm / MAX_RPM) * 100.0f;

    // Minimum motor starting threshold ~ 15% duty
    if (duty > 0.0f && duty < 15.0f) {
        duty = 15.0f;
    }

    setPwmDuty(duty);
    current_mode_ = MODE_CONTINUOUS;
}

void DRV8837CMotor::dispenseVolume(float target_ul, float rate_ul_min) {
    target_volume_ul_ = target_ul;
    dispensed_ul_ = 0.0f;
    setFlowRate(rate_ul_min, DIR_FORWARD);
    current_mode_ = MODE_DISPENSE_VOLUME;
}

void DRV8837CMotor::flush(Direction dir) {
    setDirection(dir);
    target_rate_ul_min_ = MAX_RPM * ul_per_rev_;
    setPwmDuty(100.0f);
    current_mode_ = MODE_FLUSH;
}

void DRV8837CMotor::stop() {
    setPwmDuty(0.0f);
    target_rate_ul_min_ = 0.0f;
    current_mode_ = MODE_STOPPED;
}

void DRV8837CMotor::emergencyStop() {
    // Immediate active braking: both inputs LOW
    digitalWrite(dir_pin_, LOW);
    analogWrite(pwm_pin_, 0);
    current_duty_ = 0.0f;
    target_rate_ul_min_ = 0.0f;
    current_mode_ = MODE_ESTOP;
}

void DRV8837CMotor::update(uint32_t dt_ms) {
    if (current_mode_ == MODE_STOPPED || current_mode_ == MODE_ESTOP) {
        return;
    }

    // Integrate dispensed volume: dV = Rate (uL/min) * (dt_ms / 60000)
    float dv = target_rate_ul_min_ * ((float)dt_ms / 60000.0f);
    dispensed_ul_ += dv;

    if (current_mode_ == MODE_DISPENSE_VOLUME) {
        if (dispensed_ul_ >= target_volume_ul_) {
            stop();
        }
    }
}
