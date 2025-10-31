# How to Test the Debug Version

## Quick Setup

You now have **debug versions** of all 4 files with detailed logging. Here's how to use them:

### **Files to Use:**
- ✅ `main_debug.py` - Use instead of `main.py`
- ✅ `modality_write_debug.py` - Use instead of `modality_write.py`
- ✅ `modality_peer_debug.py` - Use instead of `modality_peer.py`
- ✅ `ble_defs.py` - Keep as is (no changes needed)

### **Step 1: Backup Original Files**
```bash
# Make a backup of the original files
mpremote connect COM3 fs cp main.py main_original.py
mpremote connect COM3 fs cp modality_write.py modality_write_original.py
mpremote connect COM3 fs cp modality_peer.py modality_peer_original.py
```

### **Step 2: Upload Debug Files**
```bash
# Upload debug versions
mpremote connect COM3 cp micropython/main_debug.py :main.py
mpremote connect COM3 cp micropython/modality_write_debug.py :modality_write.py
mpremote connect COM3 cp micropython/modality_peer_debug.py :modality_peer.py
```

### **Step 3: Run and Watch Output**
```bash
# Keep this open in one terminal - shows real-time output
mpremote connect COM3 repl

# In another terminal, run the code
mpremote connect COM3 run main.py
```

### **Step 4: Watch the Debug Output**

**Device 1 Output (Server - Receives Keywords):**
```
============================================================
NIMI PEER ALERT - DEBUG VERSION
============================================================
[INIT] Starting initialization...
[INIT] Device name: NIMI_PEER_ALERT
[INIT] Initializing BLE...
[INIT] ✅ BLE active
[INIT] Creating Writer (GATT server)...
[WRITER] Initializing KeywordWriter...
[WRITER] Registering GATT services...
[WRITER] ✅ Services registered
[WRITER] Write characteristic handle: 16
[WRITER] Read characteristic handle: 17
[WRITER] ✅ KeywordWriter initialized
[INIT] Loaded keywords: []
[INIT] ✅ Writer created
[ADV] Starting advertisement (interval: 100000ms)...
[ADV] ✅ Advertising started as: NIMI_PEER_ALERT
[MAIN] ✅ Initialization complete!
[MAIN] Entering async event loop...

[MAIN] 🚀 Starting main event loop...
[MAIN] Running peer_task and keep_alive_task in parallel...

===== SCAN CYCLE #1 =====
[PEER] Starting scan (3000ms)...
[PEER] Waiting for scan to complete...
```

**Device 2 Output (Client - Searches for Other Devices):**
```
Same as Device 1, but also:

===== SCAN CYCLE #1 =====
[PEER] Starting scan (3000ms)...
[SCANNER] Starting BLE scan (3000 ms)...
[SCANNER] ✅ Scan started
[SCANNER] 📡 Scan result: addr_type=1, rssi=-50, adv_len=31
[SCANNER] ✅ Found device: NIMI_PEER_ALERT (rssi=-50)
[PEER] Waiting for scan to complete...
[SCANNER] 🏁 SCAN COMPLETE
[SCANNER] Found 1 peer(s)
[SCANNER] Attempting to connect to peer (rssi=-50)...
[SCANNER] Calling gap_connect...
[SCANNER] 🔗 PERIPHERAL_CONNECT: conn_handle=1
[SCANNER] ✅ Connected! conn_handle=1
[SCANNER] Discovering services...
[SCANNER] 🔍 SERVICE_RESULT: uuid=..., handles=16-17
[SCANNER] ✅ Found our service! Discovering characteristics...
[SCANNER] 📋 CHAR_RESULT: uuid=..., value_handle=17
[SCANNER] ✅ Found KEYWORDS_READ characteristic!
[SCANNER] Reading peer keywords...
[SCANNER] 📖 READ_RESULT: 82 bytes
[SCANNER] ✅ READ_DONE
[SCANNER] Processing peer payload...
[SCANNER] Decoded: {"keywords": [], "count": 0, "last_updated": ..., "device_name": "NIMI_PEER_ALERT"}
[SCANNER] Parsed JSON: {...}
[SCANNER] Peer keywords: []
[SCANNER] Local keywords: []
[SCANNER] Comparing...
[SCANNER] ❌ No matches
```

---

## Testing the Full Workflow

### **Test Case 1: Device 1 Sends Keywords to Device 2**

1. **Using Web Bluetooth (from browser):**
   - Go to your frontend
   - Connect to Device 1
   - Send keywords like `["pizza", "tacos"]`

2. **Watch Device 1 Output:**
```
[WRITER] 🔗 CENTRAL CONNECTED: conn_handle=1
[WRITER] ✏️  WRITE EVENT: conn_handle=1, handle=16
[WRITER] Write to KEYWORDS_WRITE characteristic
[WRITER] Raw data received: 27 bytes
[WRITER] Data: b'{"keywords":["pizza","tacos"]}'
[WRITER] Processing write payload...
[WRITER] Decoded as UTF-8: {"keywords":["pizza","tacos"]}
[WRITER] ✅ Parsed JSON: {'keywords': ['pizza', 'tacos']}
[WRITER] Keywords field: ['pizza', 'tacos']
[WRITER] Cleaned keywords: ['pizza', 'tacos']
[WRITER] Saving to keywords.json...
[WRITER] ✅ File saved successfully
[WRITER] ✅ Read characteristic updated (82 bytes)
[WRITER] Notifying 0 connected client(s)...
[WRITER] 🚨 Interrupt flag set (scanner will pause)
```

3. **Watch Device 2 Output:**
```
[PEER] ⏸️  Peer scan paused (write in progress)...
[WRITER] 🚨 Interrupt flag cleared
[PEER] ▶️  Peer scan resumed
[SCANNER] Found 1 peer(s)
[SCANNER] Attempting to connect to peer...
[SCANNER] ✅ Connected!
[SCANNER] 📖 READ_RESULT: 82 bytes
[SCANNER] Decoded: {"keywords": ["pizza", "tacos"], ...}
[SCANNER] Peer keywords: ['pizza', 'tacos']
[SCANNER] Local keywords: ['pizza', 'pizza']
[SCANNER] 🎯 MATCH FOUND: {'pizza'}
[ALERT] 🚨 ALERT TRIGGERED: {'pizza'}
[ALERT] Blinking NeoPixel...
[ALERT] Blink 1/3
[ALERT] Blink 2/3
[ALERT] Blink 3/3
[ALERT] ✅ NeoPixel sequence complete
[ALERT] Beeping buzzer...
[ALERT] ✅ Buzzer beep complete
```

---

## Troubleshooting

| Problem | What to Look For |
|---------|-----------------|
| Nothing prints | Check serial connection with `mpremote connect COM3 repl` |
| BLE fails | Look for `❌ ERROR` messages during init |
| No scan | Look for `Starting BLE scan` message |
| No peers found | Look for `Found 0 peer(s)` |
| Connection fails | Look for `❌ Connection timeout` |
| No keywords sent | Check browser console for errors |
| No match alerts | Check if keywords actually match (case-sensitive) |
| LED doesn't blink | Check `❌ NeoPixel not available` message |

---

## When Tests Pass

Once you see the full workflow working:
1. ✅ Device 1 receives keywords from browser
2. ✅ Device 1 saves them to file
3. ✅ Device 2 scans and finds Device 1
4. ✅ Device 2 reads keywords from Device 1
5. ✅ Device 2 compares and triggers alert
6. ✅ LED blinks 3 times
7. ✅ Buzzer beeps

**Then you can replace the debug files with the original optimized versions!**

