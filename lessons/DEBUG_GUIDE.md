# Debugging Guide for BLE Peer Alert System

## Problem: No Activity Messages

Your devices are running but you can't see what's happening. The current code is **silent**.

## Solution: Add Logging Everywhere

We need to add `print()` statements to see:
1. ✅ Did the device start?
2. ✅ Is it advertising?
3. ✅ Did someone connect?
4. ✅ Did it receive keywords?
5. ✅ Is it scanning?
6. ✅ Did it find other devices?
7. ✅ Did keywords match?

## How to Debug

### **Step 1: Connect to ESP32 Serial Console**

```bash
# Watch real-time output
mpremote connect COM3 repl
```

You'll see all print() statements in real-time.

### **Step 2: Run the Code**

```bash
mpremote connect COM3 run micropython/main.py
```

The console should show detailed logging.

### **Step 3: Look for These Key Messages**

**Expected output (Device 1):**
```
[INIT] BLE initializing...
[INIT] ✅ Writer registered (GATT server ready)
[INIT] ✅ Scanner ready (GATT client ready)
[ADV] Advertising as: NIMI_PEER_ALERT
[SCAN] Starting scan cycle...
[SCAN] Found 1 peer(s)
[SCAN] Connecting to peer...
[SCAN] ✅ Connected to peer
[SCAN] Reading peer keywords...
[SCAN] Got peer keywords: ["pizza", "tacos"]
[LOCAL] Our keywords: ["pizza", "sushi"]
[ALERT] ✅ MATCH FOUND: pizza
🔴 LED blink 3x + BUZZER beep
```

---

## What's Missing in Current Code

The current files have **minimal logging**. Here's what to add:

### **In `main.py`:**
- Print when BLE starts
- Print when services register
- Print advertising status
- Print async loop running

### **In `modality_write.py`:**
- Print when connected/disconnected
- Print when data received
- Print when file saved
- Print when notification sent

### **In `modality_peer.py`:**
- Print scan start/stop
- Print peers found
- Print connection attempts
- Print keywords compared
- Print match alerts

---

## Common Issues & How to Spot Them

| Issue | What You'll See | Fix |
|-------|-----------------|-----|
| BLE not started | No output at all | Check `ble.active(True)` |
| Services not registered | No "registered" message | Check UUID format |
| Not advertising | No "Advertising" message | Check `gap_advertise()` |
| Scan not working | No "scan" messages | Check `gap_scan()` |
| Can't find peers | "Found 0 peers" | Check device names match |
| Connection fails | "Failed to connect" | Check distance/interference |
| Keywords not received | No "write" message | Check Web Bluetooth or sender |
| No match alerts | Keywords found but no alert | Check keyword comparison |

---

## Next Steps

I will create **enhanced versions** of all 4 files with detailed logging.
You'll replace the current files with these debug versions and see exactly what's happening.

