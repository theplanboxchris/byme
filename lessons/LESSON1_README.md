# Lesson 1: MicroPython Development on ESP32-C3

A comprehensive guide to developing MicroPython code for your Adafruit QT Py ESP32-C3 device.

---

## 1. Development Environment

You can use **VS Code** to develop Python code for the ESP32.

### Tools Often Used

- **mpremote** — Interact with MicroPython REPL, copy/run files to device
- **esptool.py** — Flash firmware onto the ESP32
- **Docker** — Optional containerized development environment

### REPL (Read-Eval-Print Loop)

The REPL lets you execute Python commands interactively on the device in real-time. It's useful for testing code snippets and debugging.

```bash
# Enter REPL
mpremote connect COM3 repl

# Exit REPL
Ctrl+D  # soft reboot, returns to host terminal
Ctrl+X  # alternative exit
```

**Important**: Only one program can access COM3 at a time; REPL locks the port.

---

## 2. File Transfer and Execution

### Copy a File to ESP32

```bash
mpremote connect COM3 cp micropython/main.py :main.py
```

**Key Points:**
- `:main.py` → root of ESP32 filesystem
- Must exit REPL first; serial port cannot be shared
- File paths on ESP32 start with `:` (colon)

### Run a Script

```bash
mpremote connect COM3 run main.py
```

**Auto-Boot:**
- `main.py` runs automatically on boot if it's in the root directory
- Useful for deployments where you want code to run immediately on power-up

### Check Files on Device

```bash
mpremote connect COM3 ls :
```

---

## 3. MicroPython Firmware

### Why Firmware Matters

MicroPython **must be flashed** onto the ESP32 for full functionality. CircuitPython may run some Python code but lacks essential modules.

### Correct Firmware for Adafruit QT Py ESP32-C3

- **Download**: Latest USB variant from [MicroPython ESP32-C3 downloads](https://micropython.org/download/esp32c3/) - saved as micropython/firmware_micropython_latest.bin.
- **Look for**: `esp32c3-*.bin` files (choose the latest non-beta version)
- **USB variant** is critical for serial communication

### Flashing Steps

#### Step 1: Enter Bootloader Mode

Press and hold **BOOT** button, then press **RESET** button. Release BOOT.

#### Step 2: Erase Flash

```bash
esptool --port COM3 erase_flash
```

**Output should show:**
```
Connecting....
Erasing flash (this may take a few seconds)...
```

#### Step 3: Flash Firmware

```bash
esptool --port COM3 write_flash -z 0x0 micropython/firmware_micropython_latest.bin
```

Replace `firmware.bin` with your actual firmware file name.

#### Step 4: Reset Board

Press the **RESET** button and reconnect.

#### Step 5: Verify

```bash
mpremote connect COM3 repl
```

You should see the MicroPython banner and `>>>` prompt.

### Available Modules

MicroPython provides these commonly-used modules:

- `uos` — Operating system interface (file handling)
- `machine` — Hardware access (GPIO, pins, ADC)
- `time` — Time and sleep functions
- `neopixel` — WS2812B RGB LED control
- `json` — JSON parsing and encoding
- `bluetooth` — BLE wireless communication

---

## 4. CircuitPython vs MicroPython

### CircuitPython Limitations

CircuitPython can run some Python code, but has significant limitations:

❌ **Missing modules:**
- `uos` — No OS/file system functions
- `ilistdir()` — No directory listing
- `machine` — Limited hardware access

❌ **mpremote compatibility:**
- Many commands fail with `AttributeError` or `ImportError`
- File transfer often doesn't work properly

❌ **File handling:**
- Usually via USB drag-and-drop only
- No direct file transfer commands

### Why You Need MicroPython

✅ **Full mpremote support** — All file transfer and REPL commands work

✅ **Required modules** — `uos`, `machine`, `neopixel` available

✅ **This workflow** — Your NeoPixel scripts require MicroPython

**Bottom Line**: If you see `CircuitPython` on the device, flash MicroPython immediately.

---

## 5. Common Issues and Solutions

| Issue | Cause | Fix |
|-------|-------|-----|
| `OSError: No such file/directory` | ESP32 filesystem busy, REPL running, or path issue | Exit REPL, ensure COM port free, verify path starts with `:` |
| `AttributeError: 'module' object has no attribute 'ilistdir'` | Old MicroPython firmware or wrong variant | Flash latest MicroPython firmware (USB variant) |
| `ImportError: no module named 'uos'` | CircuitPython firmware installed | Flash MicroPython firmware |
| `Port in use` | REPL or another program holding COM port | Close other apps, exit REPL, restart mpremote |
| `device descriptor read/64, error -71` (Windows) | USB connection issue or bootloader mode failed | Try different USB cable, press BOOT+RESET sequence again |
| `Connection refused` | Device not detected or wrong port | Check device is powered, verify COM port number |

---

## 6. REPL Tips

### Entering REPL

```bash
mpremote connect COM3 repl
```

You'll see:
```
MicroPython vX.X.X on YYYY-MM-DD; Adafruit QT Py ESP32-C3 with ESP32C3
Type "help()" for more information.
>>>
```

### Exiting REPL

```bash
Ctrl+D    # Soft reboot, returns to host terminal
Ctrl+X    # Alternative exit
```

### Important Constraints

- **Only one program** can access COM3 at a time
- REPL locks the port while active
- Must exit before running `mpremote cp` or `mpremote run` commands
- If port is locked, restart the device or use `Ctrl+C` multiple times

### Quick Testing

```python
>>> import machine
>>> import neopixel
>>> import time
>>> help(machine.Pin)  # View documentation
>>> exit()
```

---

## 7. NeoPixel Notes

### NeoPixel Library

- **Library**: `neopixel.mpy` in `/lib` folder on ESP32
- **Control**: `neopixel` module in MicroPython
- **Usage**: Import in your scripts and define GPIO pin

### Setup for Your Project

1. **Ensure neopixel.mpy is on device:**

```bash
mpremote connect COM3 cp path/to/neopixel.mpy :/lib/neopixel.mpy
```

2. **Use in code:**

```python
import machine
import neopixel

# GPIO 2 is connected to NeoPixel
np = neopixel.NeoPixel(machine.Pin(2), 1)

# Set color to green
np[0] = (0, 255, 0)
np.write()
```

3. **Run on device:**

```bash
mpremote connect COM3 cp main.py :main.py
mpremote connect COM3 run main.py
```

---

## ✅ Key Takeaways

1. **MicroPython firmware is required** to run your NeoPixel scripts with mpremote
2. **CircuitPython may mislead you** — Python commands work, but essential modules are missing
3. **REPL vs host commands** — `mpremote cp` and `mpremote run` must be executed from the host, not inside REPL
4. **Filesystem errors** often come from REPL locking the serial port, full/dirty flash, or incorrect firmware
5. **COM port mapping is crucial** on Windows; COM3 is your device in this setup
6. **Always exit REPL** before running file transfer commands
7. **One connection at a time** — Serial port is exclusive; close REPL before using mpremote commands

---

## 🚀 Quick Start Checklist

- [ ] Download latest MicroPython firmware for ESP32-C3 (USB variant)
- [ ] Flash firmware using esptool.py
- [ ] Verify REPL works: `mpremote connect COM3 repl`
- [ ] Copy your scripts: `mpremote connect COM3 cp main.py :main.py`
- [ ] Run and test: `mpremote connect COM3 run main.py`
- [ ] Copy NeoPixel library if needed: `mpremote connect COM3 cp neopixel.mpy :/lib/neopixel.mpy`
- [ ] Monitor with REPL for debugging

---

## Additional Resources

- [MicroPython Official Docs](https://docs.micropython.org/)
- [mpremote Documentation](https://docs.micropython.org/en/latest/reference/mpremote.html)
- [esptool GitHub](https://github.com/espressif/esptool)
- [Adafruit QT Py ESP32-C3](https://learn.adafruit.com/adafruit-qt-py-esp32-c3)

---

## Docker Alternative

If you prefer using Docker for development:

```bash
# Start interactive development environment
docker-compose run --rm micropython-dev bash

# Inside container
mpremote connect /dev/ttyS2 repl  # For Windows COM3
mpremote cp main.py :main.py
```

See [DOCKER_README.md](./DOCKER_README.md) for more details.

---

Last Updated: October 2025
