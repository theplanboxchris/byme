# BLE Transfer Reliability Fixes

This document outlines the critical fixes made to ensure reliable BLE file transfer between the Web Bluetooth frontend and ESP32-C3 device.

## Issues Identified and Fixed

### 1. ✅ Characteristic Write Mode (ESP32 Side)

**Problem**: The characteristic was only flagged with `FLAG_WRITE`, which might not accept write commands from Web Bluetooth properly.

**Fix**: Added `FLAG_WRITE_NO_RESPONSE` flag:
```python
# OLD
char = (CHAR_UUID, bluetooth.FLAG_WRITE)

# NEW
char = (CHAR_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE)
```

This ensures the characteristic accepts both "write with response" and "write without response" modes, improving compatibility.

---

### 2. ✅ Chunk Size Optimization (Frontend Side)

**Problem**: 200 bytes per chunk is at the limit of BLE MTU (Maximum Transmission Unit). This can cause reliability issues and dropped packets.

**Fix**: Reduced chunk size from 200 to 128 bytes:
```javascript
// OLD
const chunkSize = 200;

// NEW
const chunkSize = 128;  // More reliable, leaves buffer for BLE overhead
```

---

### 3. ✅ Chunk Boundary Protection (ESP32 Side)

**Problem**: If the `<EOF>` marker gets split across chunks or dropped, the file never gets saved. The ESP32 has no way to know the transfer is complete.

**Fix**: Added comprehensive EOF detection and boundary checking:
```python
# Check buffer length first
if len(file_buffer) >= 5:
    if file_buffer[-5:] == b"<EOF>":
        # EOF found at end - save file
    elif b"<EOF>" in file_buffer:
        # EOF found in middle - warn and wait for more data
```

Also added detailed logging to show when EOF is detected and confirm file was saved with exact byte count.

---

### 4. ✅ Timing/Processing Delays (Frontend Side)

**Problem**: Chunks were sent back-to-back, and the device was disconnected immediately after the last write. The ESP32 BLE stack might still be processing the final chunk.

**Fix**: Added strategic delays:
```javascript
// 50ms delay between each chunk (gives ESP32 time to process)
await new Promise(r => setTimeout(r, 50));

// After all chunks sent: 500ms delay before disconnect
await new Promise(r => setTimeout(r, 500));
```

This ensures the ESP32 has time to:
1. Receive and process each chunk
2. Detect the EOF marker
3. Save the file
3. Before the connection is dropped

---

### 5. ✅ UUID Verification & Logging

**Problem**: Silent failures if UUIDs don't match exactly (typos, missing hyphens, etc.).

**Fix**: Added UUID verification on ESP32 startup:
```python
print(f"[MAIN] UUIDs:")
print(f"  Service:         {SERVICE_UUID}")
print(f"  Characteristic:  {CHAR_UUID}")
```

And detailed logging on frontend:
```javascript
console.log('[Frontend] Found service: 12345678-1234-5678-1234-56789abcdef0');
console.log('[Frontend] Found characteristic: 12345678-1234-5678-1234-56789abcdef1');
```

Both should show: `12345678-1234-5678-1234-56789abcdef0` and `12345678-1234-5678-1234-56789abcdef1`

---

### 6. ✅ Enhanced Buffer Handling (ESP32 Side)

**Problem**: No visibility into what data is being received or if the file was actually saved.

**Fix**: Added comprehensive logging:
```python
# When chunk arrives
print(f"[BLE] 📥 Chunk #{(len(file_buffer) // 200)}: {len(chunk)} bytes | Total: {len(file_buffer)} bytes")

# When EOF detected
print("[BLE] 🎯 EOF marker detected!")

# After successful save
print(f"[BLE] ✅ File saved successfully! ({file_size} bytes)")
print(f"[BLE] File content: {file_buffer[:-5].decode('utf-8', errors='ignore')}")

# Color feedback
np[0] = (0, 255, 0)  # Green = success
np[0] = (255, 0, 255)  # Magenta = error
```

---

## Testing Checklist

After these fixes, follow this checklist to verify the transfer works:

- [ ] **ESP32 Output**: Run `mpremote connect COM3 run main.py` and verify:
  - Service and characteristic UUIDs print correctly
  - NeoPixel is **RED** (waiting for connection)
  - No errors on startup

- [ ] **Frontend**: Open browser console (F12) and check for:
  - `[Frontend] Requesting BLE device: ESP32-BLE-FILE`
  - `[Frontend] Connected to GATT server`
  - `[Frontend] Found service: ...` (correct UUID)
  - `[Frontend] Found characteristic: ...` (correct UUID)

- [ ] **BLE Connection**: When you click "Send Keywords to ESP32":
  - Browser shows Bluetooth device picker
  - Select "ESP32-BLE-FILE"
  - NeoPixel turns **BLUE** (connected)
  - Frontend shows "Sending... in X chunks"

- [ ] **File Transfer**: While sending:
  - ESP32 serial shows chunk reception: `📥 Chunk #1: 128 bytes | Total: 128 bytes`
  - Frontend console shows chunk sends

- [ ] **File Saved**: After transfer:
  - ESP32 serial shows: `🎯 EOF marker detected!`
  - ESP32 serial shows: `✅ File saved successfully! (X bytes)`
  - ESP32 serial shows: `[BLE] File content: {"keywords":[...]}`
  - NeoPixel turns **GREEN** (success)

- [ ] **Verify File**: On device:
  ```bash
  mpremote connect COM3 fs ls
  # Should show: keywords.json

  mpremote connect COM3 fs cat keywords.json
  # Should show your JSON with the selected keywords
  ```

---

## Common Issues After Fixes

| Symptom | Cause | Solution |
|---------|-------|----------|
| File still not appearing | BLE service/char UUID mismatch | Print UUIDs from both sides, compare exactly |
| Random failures | Weak connection or interference | Try transfer multiple times, move closer |
| File appears but is incomplete | Chunks being dropped | Confirm all chunks logged on ESP32 side |
| Transfer completes but no file | EOF marker not detected | Check ESP32 logs for "EOF marker detected" message |

---

## Files Modified

1. **micropython/main.py**
   - Added `FLAG_WRITE_NO_RESPONSE` flag
   - Enhanced BLE event handler with better EOF detection
   - Added UUID verification logging
   - Added detailed chunk reception logging
   - Added file save confirmation and content preview

2. **frontend/index.html**
   - Reduced chunk size from 200 to 128 bytes
   - Added 50ms delay between chunk writes
   - Added 500ms delay before disconnection
   - Added comprehensive console logging
   - Added UUID verification in console output

---

## Expected Success Sequence

```
[MAIN] Service registered. Handles: ((16,),)
[MAIN] Characteristic handle: 16
[MAIN] UUIDs:
  Service:         12345678-1234-5678-1234-56789abcdef0
  Characteristic:  12345678-1234-5678-1234-56789abcdef1
[MAIN] ✅ BLE ready. Advertising as 'ESP32-BLE-FILE'

[BLE] ✅ Connected: <MAC_ADDRESS>
[BLE] 📥 Chunk #0: 128 bytes | Total: 128 bytes
[BLE] 📥 Chunk #1: 45 bytes | Total: 173 bytes
[BLE] 🎯 EOF marker detected!
[BLE] ✅ File saved successfully! (168 bytes)
[BLE] File content: {"keywords": ["keyword1", "keyword2"]}
```

---

Last Updated: October 2025
