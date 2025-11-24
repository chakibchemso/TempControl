# fan.py (smoothed PID, minimal changes)
import time

import machine
from machine import Pin, PWM, idle


class Fan:
    def __init__(self, pwm_pin: Pin, tach_pin: Pin, target_rpm=2000, freq=25000, kp=0.0, ki=0.0, kd=0.0):
        # PWM (use duty_u16). Constructor sets freq and initial duty.
        self.pwm = PWM(pwm_pin, freq=freq, duty_u16=0)

        # Tachometer pin (pull-up assumed)
        self.tach = tach_pin
        self.tach.init(Pin.IN, Pin.PULL_UP)
        self.tach.irq(trigger=Pin.IRQ_FALLING, handler=self._tach_irq)

        # control setpoints and PID gains (note: gains in normalized domain)
        self.target_rpm = int(target_rpm)
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)

        # PID state (works on normalized duty 0..1)
        self.I = 0.0
        self.last_error = 0.0
        self.last_time_ms = time.ticks_ms()

        # tach timing (microseconds), raw period between pulses
        self._last_tach_us = None
        self._period_us = None

        # smoothing / anti-noise
        self.filtered_rpm = 0.0
        self.filter_alpha = 0.25  # 0.1..0.3 typical; smaller = smoother/slower
        self.max_rpm_multiplier = 1.5  # reject readings > 1.5 * target as spikes
        self.deadband_rpm = 10  # treat error < 10 RPM as zero

        # output stored as normalized duty (0.0..1.0)
        self._duty_f = 0.0

        # safety / tuning defaults
        self._pulses_per_rev = 2
        self._integral_limit = 1.0  # integral in normalized units
        self._no_pulse_timeout_ms = 1500
        self._max_step = 0.12  # max change in duty_f per update (12%)

    # minimal IRQ handler (fast)
    def _tach_irq(self, _):
        now = time.ticks_us()
        if self._last_tach_us is not None:
            self._period_us = time.ticks_diff(now, self._last_tach_us)
        self._last_tach_us = now

    def _raw_rpm(self):
        """Compute raw RPM from last measured period_us, or 0 if not available."""
        if not self._period_us:
            # check age of last pulse
            if self._last_tach_us is None:
                return 0
            age_us = time.ticks_diff(time.ticks_us(), self._last_tach_us)
            if (age_us / 1000.0) > self._no_pulse_timeout_ms:
                return 0
            return 0
        rpm = 60_000_000.0 / (self._period_us * self._pulses_per_rev)
        return int(rpm)

    def _get_smoothed_rpm(self):
        """Return filtered RPM with outlier rejection."""
        raw = self._raw_rpm()
        # reject obvious spikes: if raw > max_multiplier * target treat as no new reading
        if self.target_rpm > 0 and raw > (self.target_rpm * self.max_rpm_multiplier):
            # ignore this sample (do not update filter), keep previous filtered value
            return self.filtered_rpm
        # exponential smoothing
        if self.filtered_rpm == 0.0:
            # initialization: set to first reading (avoids long ramp)
            self.filtered_rpm = raw
        else:
            self.filtered_rpm = (1.0 - self.filter_alpha) * self.filtered_rpm + self.filter_alpha * raw
        return self.filtered_rpm

    def _pid_compute(self, measured_rpm):
        """PID operating on normalized duty (0..1). Returns duty_f."""
        now_ms = time.ticks_ms()
        dt_ms = time.ticks_diff(now_ms, self.last_time_ms)
        self.last_time_ms = now_ms
        if dt_ms <= 0:
            dt_ms = 1
        dt = dt_ms / 1000.0

        error = float(self.target_rpm - measured_rpm)

        # deadband
        if abs(error) < self.deadband_rpm:
            error = 0.0

        # Proportional (note: kp tuned for normalized duty)
        p = self.kp * error

        # Integral with anti-windup (clamped)
        self.I += error * dt
        # clamp integral (in RPM units scaled by ki)
        if self.I > (self._integral_limit / max(self.ki, 1e-12)):
            self.I = (self._integral_limit / max(self.ki, 1e-12))
        elif self.I < -(self._integral_limit / max(self.ki, 1e-12)):
            self.I = -(self._integral_limit / max(self.ki, 1e-12))
        i = self.ki * self.I

        # Derivative on filtered measurement (reduces noise)
        d = 0.0
        if dt > 0:
            deriv = (error - self.last_error) / dt
            d = self.kd * deriv

        self.last_error = error

        # compute new duty (normalized)
        new_duty = self._duty_f + (p + i + d)

        # clamp to [0..1]
        if new_duty < 0.0:
            new_duty = 0.0
        elif new_duty > 1.0:
            new_duty = 1.0

        # limit step change to avoid bang-bang behavior
        max_step = self._max_step
        if new_duty > self._duty_f + max_step:
            new_duty = self._duty_f + max_step
        elif new_duty < self._duty_f - max_step:
            new_duty = self._duty_f - max_step

        return new_duty

    def update(self):
        """
        Call periodically (e.g. every 120..300 ms).
        Returns (measured_rpm:int, applied_duty:int).
        """
        # read + smooth rpm
        rpm = int(self._get_smoothed_rpm())

        # compute dt based on last update inside _pid_compute
        duty_f = self._pid_compute(rpm)

        # apply with conversion to duty_u16
        duty_u16 = int(duty_f * 65535.0)
        self.pwm.duty_u16(duty_u16)
        self._duty_f = duty_f

        idle()
        return rpm, duty_u16

    def set_target_rpm(self, rpm):
        self.target_rpm = int(rpm)

    def stop(self):
        self.pwm.duty_u16(0)
        self._duty_f = 0.0
        self.I = 0.0
        self.last_error = 0.0
