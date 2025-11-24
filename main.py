from time import sleep

from machine import Pin, SPI, ADC

from drivers.fan import Fan
from drivers.ili934x import Display
from drivers.thermistor import Thermistor
from drivers.xpt2046 import Touch
from renderer import Renderer

# === Pin Definitions ===
# Display Pins:
PIN_DISP_CS = Pin(27)
PIN_DISP_RST = Pin(33)
PIN_DISP_DC = Pin(32)
# Touch Pins:
PIN_TOUCH_CS = Pin(17)
PIN_TOUCH_INT = Pin(16)
# NTC Pin:
PIN_NTC_ADC = Pin(36)
# Fan Pins:
PIN_FAN_PWM = Pin(25)
PIN_FAN_TACH = Pin(26)

# === Constants ===
KP = 0.000_080 # 0.000_01
KI = 0.000_002 # KP * 0.1
KD = 0.000_024 # KP * 0.08

shared = dict(rpm=0, min_rpm=100, max_rpm=7_000, temp=25.0, min_temp=20.0, max_temp=30.0)

spi1 = SPI(1, baudrate=80_000_000)
spi2 = SPI(2, baudrate= 1_000_000)
adc = ADC(PIN_NTC_ADC, atten=ADC.ATTN_11DB)

touch = Touch(spi=spi2, cs=PIN_TOUCH_CS, int_pin=PIN_TOUCH_INT, int_handler=lambda x, y: renderer.int_touch(x, y))
display = Display(spi=spi1, cs=PIN_DISP_CS, dc=PIN_DISP_DC, rst=PIN_DISP_RST)

therm = Thermistor(adc, beta=3435, therm_ohm=10_000, divider_ohm=10_000)
fan = Fan(pwm_pin=PIN_FAN_PWM, tach_pin=PIN_FAN_TACH, target_rpm=3_000, kp=KP, ki=KI, kd=KD)

renderer = Renderer(display, touch, shared)

while True:
    temp = therm.read_temperature_celsius()
    rpm, duty = fan.update()
    renderer.update()
    
    shared['temp'] = temp
    shared['rpm'] = rpm
    min_temp = shared['min_temp']
    max_temp = shared['max_temp']
    max_rpm = shared['max_rpm']
    
    temp_normalized = (temp - min_temp) / (max_temp - min_temp)

    fan.set_target_rpm(max_rpm * max(0.001, min(1.0, temp_normalized)))

    print(f"Temp:{shared['temp']:.2f} RPM:{shared['rpm']} Duty:{duty / 65535.0:.2f}")
    sleep(1 / 60)  # 60 FPS max (gamedev habits die hard lol)
