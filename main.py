from time import sleep

from machine import Pin, SPI, ADC

from drivers.fan import Fan
from drivers.ili934x import Display
from drivers.thermistor import Thermistor
from drivers.xpt2046 import Touch
from renderer import Renderer

# === Pin Definitions ===
# Display Pins:
PIN_DISP_CS = Pin(15)
PIN_DISP_DC = Pin(2)
PIN_DISP_RST = Pin(4)
# Touch Pins:
PIN_TOUCH_CS = Pin(27)
PIN_TOUCH_INT = Pin(26)
# NTC Pin:
PIN_NTC_ADC = Pin(25)
# Fan Pins:
PIN_FAN_PWM = Pin(17)
PIN_FAN_TACH = Pin(16)

# === Constants ===
FAN_MAX_RPM = 7_000
K = 0.000_01

shared = dict(rpm=7000, temp=25.0, min_temp=20.0, max_temp=30.0)

spi1 = SPI(1, baudrate=1_000_000)
spi2 = SPI(2, baudrate=80_000_000)
adc = ADC(PIN_NTC_ADC, atten=ADC.ATTN_11DB)

touch = Touch(spi=spi1, cs=PIN_TOUCH_CS, int_pin=PIN_TOUCH_INT, int_handler=lambda x, y: renderer.int_touch(x, y))
display = Display(spi=spi2, cs=PIN_DISP_CS, dc=PIN_DISP_DC, rst=PIN_DISP_RST)

therm = Thermistor(adc, beta=3435, therm_ohm=10_000, divider_ohm=10_000)
fan = Fan(pwm_pin=PIN_FAN_PWM, tach_pin=PIN_FAN_TACH, target_rpm=3_000, kp=K, ki=0.1 * K, kd=0.08 * K)

renderer = Renderer(display, touch, shared)

while True:
    shared['temp'] = therm.read_temperature_celsius()
    shared['rpm'], duty = fan.update()
    renderer.update()

    fan.set_target_rpm(
        FAN_MAX_RPM * min(1.0, (shared['temp'] - shared['min_temp']) / (shared['max_temp'] - shared['min_temp'])))

    print(f"Temp: {shared['temp']:.2f} C, RPM: {shared['rpm']}, Duty: {duty / 65535.0:.2f}")
    # idle() not needed here, as other drivers use it internally
    sleep(1 / 60)  # 60 FPS max (gamedev habits die hard lol)
