# ESP32-C3 Development Notes

## Critical Issues & Workarounds

### ⚠️ mpremote is SEVERELY BROKEN with CircuitPython
**Broken Commands:**
1. ❌ `mpremote cp` / `mpremote fs cp` - Fails with "OSError: [Errno 2] No such file/directory"
2. ❌ `mpremote reset` - Does nothing, no output, device doesn't reset
3. ❌ `mpremote soft-reset` - Does nothing, no output, device doesn't reset
4. ❌ `mpremote ls` / `mpremote mount` - AttributeError

**Working Commands:**
- ✅ `mpremote exec "<code>"` - Execute Python code (ONLY reliable command)
- ✅ `mpremote fs cat :file.txt` - Read files from device

**Root Cause:** Known incompatibility between mpremote and CircuitPython. Only `mpremote exec` works reliably.

**Solution:** 
1. **To copy files:** Use our custom `cp_to_device.py` utility:
   ```bash
   python cp_to_device.py <local_file> <remote_path>
   ```
2. **To reset device:** Physically unplug/replug USB cable (mpremote reset doesn't work)

**Examples:**
```bash
# Copy a library to the device
python cp_to_device.py neopixel.mpy lib/neopixel.mpy

# Copy keywords file
python cp_to_device.py keywords.json keywords.json

# Copy code
python cp_to_device.py esp32/code.py code.py
```

### Device Information
- **Board:** Adafruit QT Py ESP32-C3
- **Port:** COM3
- **MAC Address:** 34:b4:72:e8:57:90
- **CircuitPython Version:** 9.2.1 (2024-10-28) **with BLE support**
- **NeoPixel Pin:** GPIO 2 (board.NEOPIXEL)

**Important:** The standard CircuitPython 9.2.0 build does NOT include BLE (_bleio module). 
We flashed version 9.2.1 which includes BLE support. Download from:
https://downloads.circuitpython.org/bin/adafruit_qtpy_esp32c3/en_US/

### External Libraries Required
CircuitPython on ESP32-C3 has limited flash, so some "built-in" libraries must be installed as .mpy files:
- **neopixel.mpy** - Already installed in `lib/` directory

## Architecture

### Current Design: Persistent code.py + keywords.json
- `code.py` - Persistent program that loads keywords from `keywords.json`
- `keywords.json` - JSON file containing keyword list (updated frequently)
- NeoPixel Status Indicators:
  - **Fast Red Flash** - No keywords.json found or empty
  - **Slow Green Pulse** - Keywords loaded successfully

### Why This Design?
Avoids rewriting entire code.py on every keyword update. Only small JSON file needs transfer.

## Working Commands

### File Operations (use cp_to_device.py)
```bash
# DON'T USE: mpremote cp file.txt :file.txt  ❌ BROKEN
# USE INSTEAD: python cp_to_device.py file.txt file.txt  ✅ WORKS
```

### Code Execution (mpremote exec works fine)
```bash
mpremote exec "print('Hello')"
mpremote exec "import neopixel; print('OK')"
```

### Read Files
```bash
mpremote fs cat :boot_out.txt
mpremote fs cat :code.py
```

### List Directory
```bash
mpremote exec "import os; print(os.listdir('/'))"
mpremote exec "import os; print(os.listdir('lib'))"
```

### Device Info
```bash
mpremote fs cat :boot_out.txt
```

## Next Steps
1. ✅ Install neopixel.mpy library
2. ✅ Create final code.py with keywords.json loading
3. ✅ Test NeoPixel status indicators (Red flash = no keywords, Green pulse = keywords loaded)
4. ✅ Update backend API to transfer keywords.json using cp_to_device.py
5. ✅ Update frontend to use new /esp32/upload-keywords endpoint
6. ⏳ Test full workflow: frontend → backend → device
7. ⏳ Implement BLE proximity detection (Step 1)
8. ⏳ Implement device-to-device communication (Step 2)

## Testing the Complete System

### 1. Start the Backend API
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Open the Frontend
Open `frontend/index.html` in a web browser

### 3. Test the Workflow
1. Add some keywords in the frontend
2. Select keywords you want to transfer
3. Click "Find Nearby Device" (should find ESP32-C3 on COM3)
4. Click "Transfer Keywords to Device"
5. Watch the NeoPixel on the device:
   - Should switch from red flash to green pulse within 5 seconds
6. Keywords are now active on the device!
