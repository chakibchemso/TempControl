# Temperature Control Project
- Hello, this was an M2 lab assignment for an embedded engineering class.
- The work to do was to create any kind of a temperature controller using an `MCU` and equipment of choice.

# Project
- I wanted to try a different approach to embedded this time, so I went with `MicroPythong` on an `ESP32`.
- To add a bit of a challenge, I chose to create a `PID` controlled `BLDC` fan, an `NTC` thermistor, and a touch `TFT` panel.
- Each device got its own driver under the `./drivers/` directory.
- The `main.py` glues everything in place and allows tweaking the parameters of the system easily.
- There's also a `renderer.py` to handle screen output and touch input.

# Pics
- `Overview:` Used `Jetbrains PyCharm` and a `MPY` extension to develop with ease:
<img width="4032" height="3024" alt="20251110_104739" src="https://github.com/user-attachments/assets/5cbe57b1-4888-4271-94b6-2004fe5fa215" />

---
- `Close-up:` to keep it simple, everything was installed on a breadboard with a power regulator header:
<img width="4032" height="3024" alt="20251110_104749" src="https://github.com/user-attachments/assets/0094e454-62e4-4b77-9657-455552cb1299" />

# Vids
- 4AM coding sessions on Snapchat `(you definetly dont wanna add me lol)`

https://github.com/user-attachments/assets/f1ac3a09-7b4f-4b25-aa5d-3bb45a9ab7bc
