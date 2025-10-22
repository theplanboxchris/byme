# BLE File Transfer Setup Guide

## Current Working Implementation

### ESP32 Firmware
**Correct file path**: `micropython/main_fixed.py`

This is the fixed BLE GATT server implementation that properly handles file transfers from Web Bluetooth.

### Upload to Device

```bash
# Copy the main fixed firmware
mpremote connect COM3 cp micropython/main_fixed.py :main_fixed.py

# Run the firmware
mpremote connect COM3 run micropython/main_fixed.py
```

### Frontend
**Correct file path**: `frontend/index.html`

Contains the Web Bluetooth client that sends keywords to the ESP32.

### Testing the Transfer

1. **Start ESP32 firmware:**
   ```bash
   mpremote connect COM3 run micropython/main_fixed.py
   ```

   Expected output:
   ```
   ==================================================
   BLE FILE RECEIVER - FIXED VERSION
   ==================================================
   [GATT] Service registered
   [GATT] Characteristic handle: 16
   [GATT] Service UUID:         12345678-1234-5678-1234-56789abcdef0
   [GATT] Characteristic UUID:  12345678-1234-5678-1234-56789abcdef1

   [ADV] Starting advertisement...
   [ADV] Advertising as: ESP32-BLE-FILE

   ✅ Ready for connections
   📍 Scanning on your phone for: ESP32-BLE-FILE
   ==================================================
   ```

2. **Open frontend in browser:**
   - Hard refresh with Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Open browser console (F12)

3. **Select keywords and transfer:**
   - Check keywords you want to send
   - Click "Send Keywords to ESP32"
   - Monitor browser console for transfer progress

4. **Verify on device:**
   ```bash
   # List files
   mpremote connect COM3 fs ls

   # Read the file
   mpremote connect COM3 fs cat keywords.json
   ```

## Key UUIDs (Must Match on Both Sides)

- **Service UUID**: `12345678-1234-5678-1234-56789abcdef0`
- **Characteristic UUID**: `12345678-1234-5678-1234-56789abcdef1`

These are hardcoded in both:
- ESP32: `micropython/main_fixed.py`
- Browser: `frontend/index.html`

## Device Status Indicator (NeoPixel)

- 🔴 **Red** - Waiting for connection
- 🔵 **Blue** - Device connected
- 🟢 **Green** - File saved successfully
- 🟣 **Magenta** - Error occurred

## Troubleshooting

### File not appearing after transfer

1. Check ESP32 console for `🎯 EOF MARKER FOUND!` message
2. Look for `✅ File written successfully!` confirmation
3. Verify NeoPixel turned green

### Browser console shows errors

1. Hard refresh browser (Ctrl+Shift+R)
2. Check that device is advertising
3. Verify UUIDs match between browser and ESP32

### Device not discoverable

1. Restart ESP32: Press RESET button
2. Check that `micropython/main_fixed.py` is running
3. Look for `[ADV] Starting advertisement...` in console

## File Structure

```
byme/
├── micropython/
│   ├── main_fixed.py          ← USE THIS (BLE GATT server)
│   ├── main.py                (old version)
│   ├── debug_main.py          (debug version)
│   └── ble_proximity.py        (advertising-only version)
├── frontend/
│   └── index.html             ← Web Bluetooth client
└── BLE_TRANSFER_FIXES.md      (old fixes documentation)
```

## References

- [Web Bluetooth API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API)
- [MicroPython BLE](https://docs.micropython.org/en/latest/library/bluetooth.html)
- [UUID Format](https://en.wikipedia.org/wiki/Universally_unique_identifier)

---

Last Updated: October 2025
**Current Working Version: micropython/main_fixed.py**
