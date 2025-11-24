from machine import idle

from drivers.ili934x import color565, Display
from drivers.xpt2046 import Touch

# === Display Colors ===
COLOR_WHITE = color565(0xFF, 0xFF, 0xFF)
COLOR_RED = color565(0xFF, 0x00, 0x00)
COLOR_CYAN = color565(0x00, 0xFF, 0xFF)
COLOR_BLACK = color565(0x00, 0x00, 0x00)

# === Sprites and Touch ===
DOT = bytearray(
    b"\x00\x00\x07\xE0\xF8\x00\x07\xE0\x00\x00\x07\xE0\xF8\x00\xF8\x00\xF8\x00\x07\xE0\xF8\x00\xF8\x00\xF8"
    b"\x00\xF8\x00\xF8\x00\x07\xE0\xF8\x00\xF8\x00\xF8\x00\x07\xE0\x00\x00\x07\xE0\xF8\x00\x07\xE0\x00\x00"
)


class Renderer:
    def __init__(self, display: Display, touch: Touch, shared: dict):
        self.display = display
        self.touch = touch
        self.shared = shared

        self.draw_grid()
        self.draw_patches()

    def draw_grid(self):
        for x in range(0, 240, 40):
            self.display.fill_rectangle(x, 0, 1, 320, COLOR_WHITE)

        for y in range(0, 320, 40):
            self.display.fill_rectangle(0, y, 240, 1, COLOR_WHITE)

        self.display.fill_rectangle(0, 319, 240, 1, COLOR_WHITE)
        self.display.fill_rectangle(239, 0, 1, 320, COLOR_WHITE)

    def draw_patches(self):
        self.display.fill_rectangle(1, 41, 158, 39, COLOR_BLACK)  # Temperature Bar
        self.display.fill_rectangle(161, 41, 78, 39, COLOR_BLACK)
        self.display.fill_rectangle(1, 81, 158, 39, COLOR_BLACK)  # RPM Bar
        self.display.fill_rectangle(161, 81, 78, 39, COLOR_BLACK)

        self.display.fill_rectangle(1, 161, 79, 79, COLOR_BLACK)  # Min Minus
        self.display.draw_text8x8(36, 197, "-", COLOR_CYAN)
        self.display.fill_rectangle(1, 241, 79, 78, COLOR_BLACK)  # Max Minus
        self.display.draw_text8x8(36, 277, "-", COLOR_CYAN)

        self.display.fill_rectangle(161, 161, 78, 79, COLOR_BLACK)  # Min Plus
        self.display.draw_text8x8(197, 197, "+", COLOR_CYAN)
        self.display.fill_rectangle(161, 241, 78, 78, COLOR_BLACK)  # Max Plus
        self.display.draw_text8x8(197, 277, "+", COLOR_CYAN)

        self.display.fill_rectangle(81, 161, 79, 79, COLOR_BLACK)  # Min Value
        self.display.draw_text8x8(90, 180, f"min", COLOR_WHITE)
        self.display.fill_rectangle(81, 241, 79, 78, COLOR_BLACK)  # Max Value
        self.display.draw_text8x8(90, 260, f"max", COLOR_WHITE)
        

    def draw_progress_bar(self, x, y, width, height, progress, color_fg, color_bg):
        progress = max(0, min(1, progress))  # clamp between 0..1
        filled = int(width * progress)
        unfilled = width - filled
        if filled:
            self.display.fill_rectangle(x, y, filled, height, color_fg)
        if unfilled:
            self.display.fill_rectangle(x + filled, y, unfilled, height, color_bg)

    def draw_dot(self, _x: int, _y: int):
        self.display.draw_sprite(DOT, _x - 2, _y - 2, 5, 5)

    def int_touch(self, _x, _y):
        # self.draw_dot(_x, _y)
        print(f'Touch: {_x}, {_y}')

        if 1 <= _x <= 80 and 161 <= _y <= 240:  # Min Minus
            self.shared['min_temp'] = max(0.0, self.shared['min_temp'] - 0.5)
        elif 161 <= _x <= 239 and 161 <= _y <= 240:  # Min Plus
            self.shared['min_temp'] = min(self.shared['max_temp'] - 0.5, self.shared['min_temp'] + 0.5)
        elif 1 <= _x <= 80 and 241 <= _y <= 318:  # Max Minus
            self.shared['max_temp'] = max(self.shared['min_temp'] + 0.5, self.shared['max_temp'] - 0.5)
        elif 161 <= _x <= 239 and 241 <= _y <= 318:  # Max Plus
            self.shared['max_temp'] = min(100.0, self.shared['max_temp'] + 0.5)

    def update(self):
        self.draw_progress_bar(10, 55, 140, 10,
                               ((self.shared['temp'] - self.shared['min_temp']) / (
                                           self.shared['max_temp'] - self.shared['min_temp'])),
                               COLOR_RED, COLOR_WHITE)
        self.draw_progress_bar(10, 95, 140, 10, (self.shared['rpm'] / self.shared['max_rpm']), COLOR_CYAN, COLOR_WHITE)

        self.display.draw_text8x8(172, 56, f"{self.shared['temp']:.2f} C", COLOR_RED)
        self.display.draw_text8x8(172, 96, f"{self.shared['rpm']} RPM", COLOR_CYAN)

        self.display.draw_text8x8(90, 170, f"{self.shared['min_temp']:.2f} C", COLOR_WHITE)
        self.display.draw_text8x8(90, 250, f"{self.shared['max_temp']:.2f} C", COLOR_WHITE)

        idle()
        return
