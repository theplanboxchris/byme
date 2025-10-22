# BLE Device Specification: NIMI_PEER_ALERT

## Device Overview

**Device Name:** `NIMI_PEER_ALERT`  
**Hardware:** ESP32-C3 (or ESP32 variant with BLE support)  
**Purpose:** Proximity-based peer discovery and keyword matching system  
**Protocol:** Bluetooth Low Energy (BLE) 4.0+

---

## Device Characteristics

### Basic Information
- **Advertising Name:** NIMI_PEER_ALERT
- **Connectable:** Yes
- **Discoverable:** Yes
- **Pairing Required:** No (open access)

### Hardware Requirements
- ESP32 microcontroller with BLE radio
- Optional: NeoPixel LED for status indication
- Optional: Button for mode switching

---

## BLE Service Definition

### Service: KEYWORDS

**Service UUID:** `a07498ca-ad5b-474e-940d-16f1fbe7e8cd`  
**Type:** Custom/Proprietary Service  
**Purpose:** Manage and exchange keyword lists for proximity matching

#### Characteristics

##### 1. KEYWORDS_WRITE

**Characteristic UUID:** `b07498ca-ad5b-474e-940d-16f1fbe7e8cd`  
**Properties:** WRITE, WRITE_NO_RESPONSE  
**Permissions:** Write allowed without authentication  
**Data Format:** UTF-8 encoded JSON string  
**Maximum Length:** 512 bytes (can be sent in chunks if larger)

**Purpose:**  
Allows clients to write/update the device's keyword list remotely via BLE.

**Data Structure:**
```json
{
  "keywords": ["python", "iot", "maker", "robotics", "esp32"],
  "device_id": "optional-unique-identifier",
  "timestamp": 1698765432
}
```

**Expected Behavior:**
- When written to, device parses JSON and updates internal keyword list
- Device validates JSON format before accepting
- Device saves keywords to persistent storage (keywords.json)
- Device may restart advertising with updated keywords
- Write acknowledgment depends on property (WRITE vs WRITE_NO_RESPONSE)

**Example Values:**
```json
{"keywords": ["python", "iot"]}
{"keywords": ["maker", "electronics", "3d-printing"]}
{"keywords": []}
```

##### 2. KEYWORDS_READ

**Characteristic UUID:** `c07498ca-ad5b-474e-940d-16f1fbe7e8cd`  
**Properties:** READ, NOTIFY  
**Permissions:** Read allowed without authentication  
**Data Format:** UTF-8 encoded JSON string  
**Maximum Length:** 512 bytes

**Purpose:**  
Allows clients to read the device's current keyword list and receive updates when keywords change.

**Data Structure:**
```json
{
  "keywords": ["python", "iot", "maker"],
  "count": 3,
  "last_updated": 1698765432,
  "device_name": "NIMI_PEER_ALERT"
}
```

**Expected Behavior:**
- READ: Returns current keyword list in JSON format
- NOTIFY: Automatically sends updates when keyword list changes
- Client can subscribe to notifications to receive real-time updates
- Device sends notification immediately after KEYWORDS_WRITE updates

**Example Response:**
```json
{
  "keywords": ["python", "iot", "maker", "robotics"],
  "count": 4,
  "last_updated": 1698765432,
  "device_name": "NIMI_PEER_ALERT"
}
```

---

## GATT Attribute Table

| Handle | Type | UUID | Properties | Description |
|--------|------|------|------------|-------------|
| 0x0001 | Service | 0x1800 | - | Generic Access |
| 0x0002 | Characteristic | 0x2A00 | READ | Device Name |
| 0x0003 | Service | 0x1801 | - | Generic Attribute |
| 0x0010 | Service | a07498ca-ad5b-474e-940d-16f1fbe7e8cd | - | KEYWORDS Service |
| 0x0011 | Characteristic | b07498ca-ad5b-474e-940d-16f1fbe7e8cd | WRITE | KEYWORDS_WRITE |
| 0x0012 | Descriptor | 0x2901 | READ | User Description: "Write Keywords" |
| 0x0013 | Characteristic | c07498ca-ad5b-474e-940d-16f1fbe7e8cd | READ, NOTIFY | KEYWORDS_READ |
| 0x0014 | Descriptor | 0x2902 | READ, WRITE | Client Characteristic Config (CCCD) |
| 0x0015 | Descriptor | 0x2901 | READ | User Description: "Read Keywords" |

---

## Advertising Data

### Advertisement Packet Structure

**Flags:** 0x06 (General Discoverable, BR/EDR not supported)

**Complete Local Name:** NIMI_PEER_ALERT

**Service UUID List:**
- a07498ca-ad5b-474e-940d-16f1fbe7e8cd (KEYWORDS service)

**Manufacturer Data (Optional):**
- Company ID: 0xFFFF (for testing/custom use)
- Data: First 3 keywords comma-separated (e.g., "python,iot,maker")

**Example Advertisement:**
```
02 01 06                          // Flags
10 09 4E 49 4D 49 5F 50 45 45    // Complete name "NIMI_PEER_ALERT"
   52 5F 41 4C 45 52 54
11 06 CD E8 E7 FB F1 16 0D 94    // 128-bit service UUID
   4E 47 5B AD CA 98 74 A0
```

---

## Connection Parameters

**Connection Interval:** 7.5ms - 4000ms (preferred: 100ms)  
**Slave Latency:** 0  
**Supervision Timeout:** 4000ms  
**MTU Size:** 23 bytes (default), negotiable up to 512 bytes

---

## Example code

### Example 1: Implementing two modalities (MicroPython)

This example implements two device modalities:
- Modality 1 - accepts Keyword Writes to the KEYWORDS_WRITE - these are initiated from a browser and interrupt all other operations of the device;
- Modality 2 - continually scan for nearby devices with the same name ('NIMI_PEER_ALERT') in order to connect, exchange their KEYWORDS_READ characteristic data, disconnect and each peer then performs a comparison between the received keywords and their local KEYWORDS_READ data, alerting by means of a sound and neopixel colour if any matches of keywords are found  


This example a complete, ready-to-copy MicroPython project split into four files:

ble_defs.py — BLE UUIDs, flags, small helper (advertising payload).

modality_write.py — Modality 1 class: GATT server write handler, JSON validation, save to keywords.json, send NOTIFY on KEYWORDS_READ, and set a shared "interrupt" flag.

modality_peer.py — Modality 2 class: scanner/central logic to find other NIMI_PEER_ALERT devices, connect, read their KEYWORDS_READ, compare with local keywords and call alert() (neopixel + buzzer) when matches found.

main.py — Wire them together, run both modalities concurrently via uasyncio, ensure "peer-to-peer" is default and is interrupted when a browser write arrives.


### main.py

```python
"""
ESP32 as BLE Server - Accepts keyword writes from clients
Run this on the ESP32 that will receive keywords
"""
# main.py
import uasyncio as asyncio
import bluetooth
from ble_defs import DEVICE_NAME, SERVICE_UUID, KEYWORDS_WRITE_UUID, KEYWORDS_READ_UUID, advertising_payload, _FLAG_READ, _FLAG_WRITE, _FLAG_WRITE_NO_RESPONSE, _FLAG_NOTIFY
import ble_defs as defs
from modality_write import KeywordWriter
from modality_peer import PeerScanner
import time
import machine
import neopixel

# Hardware config (adjust pins)
NEOPIXEL_PIN = 4  # example
NEOPIXEL_COUNT = 1
BUZZER_PIN = 15  # example PWM-capable pin

# Setup BLE
ble = bluetooth.BLE()
ble.active(True)

# instantiate writer (GATT server)
writer = KeywordWriter(ble, defs)
writer.load_from_storage()

# NeoPixel optional
np = None
try:
    np = neopixel.NeoPixel(machine.Pin(NEOPIXEL_PIN), NEOPIXEL_COUNT)
except Exception:
    np = None

# Buzzer pin optional
buzzer_pin = None
try:
    buzzer_pin = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
except Exception:
    buzzer_pin = None

# instantiate peer scanner (central)
peer = PeerScanner(ble, defs, writer, neopixel=np, buzzer_pin=buzzer_pin)

# Advertising payload
payload = advertising_payload(name=DEVICE_NAME, services=[SERVICE_UUID])
# Advertise indefinitely
def advertise():
    try:
        ble.gap_advertise(100_000, adv_data=payload)
    except Exception:
        try:
            ble.gap_advertise(100_000)
        except Exception:
            pass

advertise()

async def peer_task():
    """
    Default modality: continuously scan for peers periodically,
    unless interrupted by a KEYWORDS_WRITE incoming request.
    When interrupted: pause scanning briefly to let the write complete.
    """
    while True:
        if writer.interrupted:
            # pause peer work for a short time to let the write modality finish
            print("Peer modality paused due to write interrupt")
            # clear the interrupt flag after a short settle time
            await asyncio.sleep(1)
            writer.clear_interrupt()
            print("Resuming peer modality")
            # re-advertise (in case write caused state update)
            advertise()
            await asyncio.sleep(1)
            continue
        # scan cycle
        peer.start_scan(scan_ms=3000)
        # wait for scan+connect cycle to finish (modality_peer will process found peers on _IRQ_SCAN_COMPLETE)
        await asyncio.sleep(4)
        # small delay before next scan
        await asyncio.sleep(1)

async def keep_alive_task():
    # optional heartbeat LED or print
    while True:
        # re-advertise periodically to ensure advertising continues
        advertise()
        await asyncio.sleep(20)

async def main_loop():
    await asyncio.gather(peer_task(), keep_alive_task())

# run
try:
    asyncio.run(main_loop())
finally:
    asyncio.new_event_loop()

```

### ble_defs.py

```python

# ble_defs.py
from micropython import const
import bluetooth
import struct

# UUIDs from your spec
SERVICE_UUID = bluetooth.UUID("a07498ca-ad5b-474e-940d-16f1fbe7e8cd")
KEYWORDS_WRITE_UUID = bluetooth.UUID("b07498ca-ad5b-474e-940d-16f1fbe7e8cd")
KEYWORDS_READ_UUID = bluetooth.UUID("c07498ca-ad5b-474e-940d-16f1fbe7e8cd")

DEVICE_NAME = "NIMI_PEER_ALERT"

# GATT flags (from MicroPython examples)
_FLAG_READ = const(0x0002)
_FLAG_WRITE = const(0x0008)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_NOTIFY = const(0x0010)

# IRQ constants (match MicroPython examples)
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_COMPLETE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_READ_RESULT = const(9)
_IRQ_GATTC_READ_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_SERVICE_RESULT = const(13)
_IRQ_GATTC_SERVICE_DONE = const(14)
_IRQ_MTU_EXCHANGED = const(21)

# Advertising payload helper (from micropython examples)
def advertising_payload(name=None, services=None):
    payload = bytearray()
    def _append(adv_type, value):
        nonlocal payload
        payload += struct.pack("BB", len(value) + 1, adv_type) + value

    # Flags
    _append(0x01, b'\x06')
    if name:
        _append(0x09, name.encode())
    if services:
        # only supports 128-bit UUIDs in this helper
        for u in services:
            b = u.uuid if isinstance(u, bluetooth.UUID) and hasattr(u, "uuid") else None
            # For UUID 128-bits we just append the raw bytes using .bytes() when available
            try:
                # cpymicro: bluetooth.UUID has .bytes (MicroPython >= certain versions)
                raw = u.uuid if isinstance(u, bluetooth.UUID) and isinstance(u.uuid, bytes) else None
            except Exception:
                raw = None
            # fallback: represent uuid as string isn't suitable here; better to include service in scan filters
            try:
                _append(0x07, bytes(u))  # complete list of 128-bit service UUIDs
            except Exception:
                pass
    return payload


```

### modality_write.py

```python
# modality_write.py
import ujson as json
import time
from micropython import const

class KeywordWriter:
    """
    Modality 1: GATT server for KEYWORDS service.
    Exposes KEYWORDS_WRITE (write-only) and KEYWORDS_READ (read/notify).
    When a write arrives: parse JSON, save to keywords.json, update internal state,
    send NOTIFY to subscribed clients, and set interrupt flag (to pause peer scanning temporarily).
    """
    def __init__(self, ble, defs, storage_path="keywords.json"):
        self._ble = ble
        self._defs = defs
        self._storage_path = storage_path
        self._connections = set()
        self._cccd_handles = {}  # Not used deeply, but kept for reference
        self.interrupted = False  # set to True when a write arrives (other modalities should check)
        # load existing keywords if any
        self.keywords = []
        self.last_updated = 0
        self._register_services()
        # set BLE IRQ for server events
        self._ble.irq(self._irq)

    def _register_services(self):
        # create characteristics tuples: (UUID, flags)
        write_chr = (self._defs.KEYWORDS_WRITE_UUID, self._defs._FLAG_WRITE | self._defs._FLAG_WRITE_NO_RESPONSE)
        read_chr  = (self._defs.KEYWORDS_READ_UUID, self._defs._FLAG_READ | self._defs._FLAG_NOTIFY)
        service = (self._defs.SERVICE_UUID, (write_chr, read_chr))
        ((self._handle_write, self._handle_read),) = self._ble.gatts_register_services((service,))
        # set an initial value for read characteristic
        self._update_read_value()
        # advertise is done in main (not here)

    def _irq(self, event, data):
        if event == self._defs._IRQ_CENTRAL_CONNECT:
            conn_handle, _, = data
            self._connections.add(conn_handle)
        elif event == self._defs._IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
        elif event == self._defs._IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            # check if write was to our write characteristic
            if value_handle == self._handle_write:
                # read the data that was written
                raw = self._ble.gatts_read(self._handle_write)
                self._on_write(raw, conn_handle)

    def _on_write(self, raw_data, conn_handle):
        """
        Handle incoming JSON write: validate, persist, update read char, notify.
        """
        try:
            s = raw_data.decode('utf-8')
        except Exception:
            return  # ignore invalid encoding
        try:
            payload = json.loads(s)
        except Exception:
            # invalid json: ignore or optionally write an error characteristic / LED blink
            return
        # Validate expected structure
        keywords = payload.get("keywords")
        if not isinstance(keywords, list):
            return
        # normalize to lowercase strings
        clean = []
        for k in keywords:
            if isinstance(k, str):
                v = k.strip()
                if v:
                    clean.append(v.lower())
        self.keywords = clean
        self.last_updated = int(time.time())
        # persist
        try:
            with open(self._storage_path, "w") as f:
                json.dump({
                    "keywords": self.keywords,
                    "last_updated": self.last_updated
                }, f)
        except Exception:
            pass
        # update GATT read characteristic value
        self._update_read_value()
        # notify connected centrals if any
        for conn in list(self._connections):
            try:
                self._ble.gatts_notify(conn, self._handle_read, self._gatt_read_payload())
            except Exception:
                # ignore notify failures
                pass
        # set interrupted flag so peer modality can pause if desired
        self.interrupted = True

    def _gatt_read_payload(self):
        obj = {
            "keywords": self.keywords,
            "count": len(self.keywords),
            "last_updated": self.last_updated,
            "device_name": self._defs.DEVICE_NAME
        }
        return json.dumps(obj).encode('utf-8')

    def _update_read_value(self):
        try:
            self._ble.gatts_write(self._handle_read, self._gatt_read_payload())
        except Exception:
            pass

    def load_from_storage(self):
        import ujson as json
        try:
            with open(self._storage_path, "r") as f:
                data = json.load(f)
            kws = data.get("keywords", [])
            if isinstance(kws, list):
                self.keywords = [k.lower().strip() for k in kws if isinstance(k, str) and k.strip()]
            self.last_updated = data.get("last_updated", int(time.time()))
        except Exception:
            # no file / invalid: keep defaults
            self.keywords = []
            self.last_updated = 0
        # ensure GATT read char has latest
        self._update_read_value()

    def clear_interrupt(self):
        self.interrupted = False

    def get_keywords(self):
        return list(self.keywords)


```

### modality_peer.py

```python
# modality_peer.py
import time
import ujson as json
from micropython import const
import machine

class PeerScanner:
    """
    Modality 2: Scan for peers advertising DEVICE_NAME, connect, read KEYWORDS_READ,
    compare with local keywords, and alert on match.

    NOTE: This class expects the BLE object to be active and that a GATT server for
    the same service is registered (so the device can be both peripheral and central).
    """
    def __init__(self, ble, defs, writer_instance, neopixel=None, buzzer_pin=None):
        self._ble = ble
        self._defs = defs
        self.writer = writer_instance  # to get local keywords
        self.neopixel = neopixel
        self.buzzer_pin = buzzer_pin
        self._ble.irq(self._irq)
        self._scanning = False
        self._found = {}  # addr -> advertisement data
        # central connection resources
        self._conn_handle = None
        self._peer_char_handle = None
        self._peer_read_results = None

    def _irq(self, event, data):
        if event == self._defs._IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            # simple parse: check for device name in adv_data (complete local name 0x09)
            if self._advertisement_has_name(adv_data, self._defs.DEVICE_NAME):
                # store peer address and attempt connect
                self._found[bytes(addr)] = (addr_type, addr, rssi, adv_data)
        elif event == self._defs._IRQ_SCAN_COMPLETE:
            # scanning ended, proceed to connect sequentially to found peers
            for addr_bytes, info in list(self._found.items()):
                if self.writer.interrupted:
                    # if a write happened, stop attempting to connect
                    break
                addr_type, addr, rssi, adv_data = info
                # attempt to connect as central
                try:
                    self._ble.gap_connect(addr_type, addr)
                    # wait for _IRQ_PERIPHERAL_CONNECT to trigger; handled below
                    # we'll block/wait for a short time; but don't block too long
                    t0 = time.ticks_ms()
                    while self._conn_handle is None and time.ticks_diff(time.ticks_ms(), t0) < 5000:
                        time.sleep_ms(50)
                    if self._conn_handle is None:
                        # failed to connect in time; continue to next peer
                        continue
                    # discover services/characteristics
                    # request service discovery (emit GATTC service result events)
                    self._ble.gattc_discover_services(self._conn_handle)
                    # wait for service discovery to finish (use a timeout)
                    t0 = time.ticks_ms()
                    while self._peer_char_handle is None and time.ticks_diff(time.ticks_ms(), t0) < 4000:
                        time.sleep_ms(50)
                    if self._peer_char_handle:
                        # read the characteristic
                        self._ble.gattc_read(self._conn_handle, self._peer_char_handle)
                        # wait for read result
                        t0 = time.ticks_ms()
                        while self._peer_read_results is None and time.ticks_diff(time.ticks_ms(), t0) < 3000:
                            time.sleep_ms(50)
                        if self._peer_read_results:
                            self._process_peer_payload(self._peer_read_results)
                    # disconnect
                    try:
                        self._ble.gap_disconnect(self._conn_handle)
                    except Exception:
                        pass
                except Exception:
                    pass
                finally:
                    # reset per-connection state
                    self._conn_handle = None
                    self._peer_char_handle = None
                    self._peer_read_results = None
            # done with current found list; clear
            self._found = {}
        elif event == self._defs._IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._conn_handle = conn_handle
        elif event == self._defs._IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            if conn_handle == self._conn_handle:
                self._conn_handle = None
        elif event == self._defs._IRQ_GATTC_SERVICE_RESULT:
            # data = (conn_handle, start_handle, end_handle, uuid_bytes)
            try:
                conn_handle, start_handle, end_handle, uuid = data
            except Exception:
                conn_handle, start_handle, end_handle, uuid = data
            # check if this is our service uuid (128-bit). UUID may be bytes or bluetooth.UUID.
            try:
                if bytes(uuid).find(bytes(self._defs.SERVICE_UUID)) != -1:
                    # discover characteristics within this service
                    self._ble.gattc_discover_characteristics(self._conn_handle, start_handle, end_handle)
            except Exception:
                # fallback: attempt characteristic discovery anyway
                self._ble.gattc_discover_characteristics(self._conn_handle, start_handle, end_handle)
        elif event == self._defs._IRQ_GATTC_CHARACTERISTIC_RESULT:
            # (conn_handle, def_handle, value_handle, properties, uuid)
            conn_handle, def_handle, value_handle, properties, uuid = data
            # check for KEYWORDS_READ UUID
            try:
                if uuid == self._defs.KEYWORDS_READ_UUID:
                    self._peer_char_handle = value_handle
            except Exception:
                # compare bytes fallback
                try:
                    if bytes(uuid) == bytes(self._defs.KEYWORDS_READ_UUID):
                        self._peer_char_handle = value_handle
                except Exception:
                    pass
        elif event == self._defs._IRQ_GATTC_READ_RESULT:
            conn_handle, value_handle, char_data = data
            # store read result
            self._peer_read_results = char_data
        elif event == self._defs._IRQ_GATTC_READ_DONE:
            # nothing to do here in this simple flow
            pass

    def _advertisement_has_name(self, adv_data, name):
        # parse adv_data for AD type 0x09 (complete local name)
        i = 0
        while i + 1 < len(adv_data):
            length = adv_data[i]
            if length == 0:
                break
            ad_type = adv_data[i+1]
            if ad_type == 0x09:
                start = i + 2
                end = start + (length - 1)
                try:
                    adv_name = adv_data[start:end+1].decode('utf-8')
                except Exception:
                    adv_name = None
                return adv_name == name
            i += 1 + length
        return False

    def _process_peer_payload(self, raw):
        try:
            s = raw.decode('utf-8')
            payload = json.loads(s)
            their = payload.get("keywords", [])
            if not isinstance(their, list):
                return
            their = [x.lower().strip() for x in their if isinstance(x, str)]
        except Exception:
            return
        local = [k.lower().strip() for k in self.writer.get_keywords()]
        # find intersection
        matches = set(local).intersection(set(their))
        if matches:
            # perform alert
            self.alert(matches)

    def alert(self, matches):
        """
        Provide a simple alert: blink neopixel if present and pulse buzzer if present.
        """
        try:
            print("ALERT: matched keywords:", matches)
            # neopixel: simple blink sequence (if provided)
            if self.neopixel is not None:
                for _ in range(3):
                    self.neopixel.fill((255, 0, 0))
                    self.neopixel.write()
                    time.sleep_ms(200)
                    self.neopixel.fill((0, 0, 0))
                    self.neopixel.write()
                    time.sleep_ms(200)
            # buzzer: drive PWM tone if provided
            if self.buzzer_pin is not None:
                pwm = machine.PWM(self.buzzer_pin)
                pwm.freq(1000)
                pwm.duty_u16(20000)
                time.sleep_ms(400)
                pwm.duty_u16(0)
                pwm.deinit()
        except Exception as e:
            print("alert error:", e)

    def start_scan(self, scan_ms=3000):
        """
        Trigger a scan for nearby devices. Non-blocking: results come via IRQ and
        _IRQ_SCAN_COMPLETE will lead to connection attempts.
        """
        if self.writer.interrupted:
            return
        try:
            # active scan, interval and window values are optional
            self._ble.gap_scan(scan_ms, 30000, 30000)
            self._scanning = True
        except Exception:
            pass

    def stop_scan(self):
        try:
            self._ble.gap_scan(None)
        except Exception:
            pass
        self._scanning = False


```







### Example 2: ESP32 Client - Writing Keywords to Server (Javascript)

When in Modality 1 the device accepts Keyword Writes to the KEYWORDS_WRITE characteristic. This operation is initiated from a browser and interrupts all other operations of the device

This example code shows how this modality can be implemented at the browser side.


```javascript
"""

/**
 * JavaScript BLE Client - Writes keywords to NIMI_PEER_ALERT ESP32 server
 * Uses Web Bluetooth API (works in Chrome, Edge, Opera browsers)
 * Run this in a browser or Node.js with web-bluetooth package
 */

// UUIDs
const SERVICE_UUID = "a07498ca-ad5b-474e-940d-16f1fbe7e8cd";
const WRITE_CHAR_UUID = "b07498ca-ad5b-474e-940d-16f1fbe7e8cd";
const READ_CHAR_UUID = "c07498ca-ad5b-474e-940d-16f1fbe7e8cd";
const DEVICE_NAME = "NIMI_PEER_ALERT";

class KeywordsClient {
    constructor() {
        this.device = null;
        this.server = null;
        this.service = null;
        this.writeCharacteristic = null;
        this.readCharacteristic = null;
    }

    /**
     * Scan and connect to NIMI_PEER_ALERT device
     */
    async scanAndConnect() {
        try {
            console.log("[Client] Requesting device...");
            
            // Request device (this will show a browser dialog)
            this.device = await navigator.bluetooth.requestDevice({
                filters: [{ name: DEVICE_NAME }],
                optionalServices: [SERVICE_UUID]
            });

            console.log(`[Client] Found device: ${this.device.name}`);
            
            // Connect to GATT server
            console.log("[Client] Connecting to GATT server...");
            this.server = await this.device.gatt.connect();
            console.log("[Client] Connected!");

            // Get service
            console.log("[Client] Getting KEYWORDS service...");
            this.service = await this.server.getPrimaryService(SERVICE_UUID);
            console.log("[Client] Service found!");

            // Get characteristics
            console.log("[Client] Getting characteristics...");
            this.writeCharacteristic = await this.service.getCharacteristic(WRITE_CHAR_UUID);
            this.readCharacteristic = await this.service.getCharacteristic(READ_CHAR_UUID);
            console.log("[Client] Characteristics found!");

            return true;
        } catch (error) {
            console.error("[Client] Connection error:", error);
            return false;
        }
    }

    /**
     * Write keywords to the device
     * @param {Array<string>} keywords - Array of keyword strings
     */
    async writeKeywords(keywords) {
        if (!this.writeCharacteristic) {
            console.error("[Client] Not connected or characteristic not found");
            return false;
        }

        try {
            // Create JSON payload
            const data = {
                keywords: keywords,
                timestamp: Math.floor(Date.now() / 1000)
            };
            const jsonString = JSON.stringify(data);
            
            console.log(`[Client] Writing keywords: ${keywords.join(", ")}`);
            
            // Convert string to Uint8Array
            const encoder = new TextEncoder();
            const dataArray = encoder.encode(jsonString);
            
            // Write to characteristic
            await this.writeCharacteristic.writeValue(dataArray);
            
            console.log("[Client] Keywords written successfully!");
            return true;
        } catch (error) {
            console.error("[Client] Write error:", error);
            return false;
        }
    }

    /**
     * Read keywords from the device
     * @returns {Object} Keywords data object
     */
    async readKeywords() {
        if (!this.readCharacteristic) {
            console.error("[Client] Not connected or characteristic not found");
            return null;
        }

        try {
            console.log("[Client] Reading keywords...");
            
            // Read from characteristic
            const value = await this.readCharacteristic.readValue();
            
            // Convert Uint8Array to string
            const decoder = new TextDecoder();
            const jsonString = decoder.decode(value);
            
            // Parse JSON
            const data = JSON.parse(jsonString);
            
            console.log(`[Client] Read keywords:`, data);
            return data;
        } catch (error) {
            console.error("[Client] Read error:", error);
            return null;
        }
    }

    /**
     * Subscribe to keyword updates (notifications)
     * @param {Function} callback - Called when keywords are updated
     */
    async subscribeToUpdates(callback) {
        if (!this.readCharacteristic) {
            console.error("[Client] Not connected or characteristic not found");
            return false;
        }

        try {
            console.log("[Client] Subscribing to notifications...");
            
            // Set up notification handler
            this.readCharacteristic.addEventListener('characteristicvaluechanged', (event) => {
                const value = event.target.value;
                const decoder = new TextDecoder();
                const jsonString = decoder.decode(value);
                const data = JSON.parse(jsonString);
                
                console.log("[Client] Keywords updated:", data);
                callback(data);
            });

            // Start notifications
            await this.readCharacteristic.startNotifications();
            console.log("[Client] Subscribed to notifications!");
            return true;
        } catch (error) {
            console.error("[Client] Subscribe error:", error);
            return false;
        }
    }

    /**
     * Unsubscribe from notifications
     */
    async unsubscribe() {
        if (!this.readCharacteristic) {
            return;
        }

        try {
            await this.readCharacteristic.stopNotifications();
            console.log("[Client] Unsubscribed from notifications");
        } catch (error) {
            console.error("[Client] Unsubscribe error:", error);
        }
    }

    /**
     * Disconnect from device
     */
    disconnect() {
        if (this.device && this.device.gatt.connected) {
            this.device.gatt.disconnect();
            console.log("[Client] Disconnected");
        }
    }

    /**
     * Check if connected
     * @returns {boolean}
     */
    isConnected() {
        return this.device && this.device.gatt.connected;
    }
}

// ============================================
// Usage Examples
// ============================================

/**
 * Example 1: Simple keyword write
 */
async function example1_writeKeywords() {
    const client = new KeywordsClient();
    
    // Connect
    const connected = await client.scanAndConnect();
    if (!connected) {
        console.error("Failed to connect");
        return;
    }

    // Write keywords
    await client.writeKeywords(["python", "iot", "maker", "esp32"]);
    
    // Disconnect
    setTimeout(() => {
        client.disconnect();
    }, 1000);
}

/**
 * Example 2: Write and then read back
 */
async function example2_writeAndRead() {
    const client = new KeywordsClient();
    
    // Connect
    await client.scanAndConnect();
    
    // Write keywords
    await client.writeKeywords(["javascript", "web", "bluetooth"]);
    
    // Wait a bit for write to complete
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Read keywords back
    const data = await client.readKeywords();
    console.log("Keywords on device:", data.keywords);
    
    // Disconnect
    client.disconnect();
}

/**
 * Example 3: Subscribe to keyword updates
 */
async function example3_subscribeToUpdates() {
    const client = new KeywordsClient();
    
    // Connect
    await client.scanAndConnect();
    
    // Subscribe to updates
    await client.subscribeToUpdates((data) => {
        console.log("🔔 Keywords changed!");
        console.log("New keywords:", data.keywords);
        console.log("Count:", data.count);
    });
    
    console.log("Listening for keyword updates...");
    console.log("Try updating keywords from another device!");
    
    // Keep connection alive for 60 seconds
    setTimeout(() => {
        client.unsubscribe();
        client.disconnect();
        console.log("Example finished");
    }, 60000);
}

/**
 * Example 4: Interactive HTML page
 */
function createInteractivePage() {
    // Add HTML to page
    document.body.innerHTML = `
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h1>NIMI_PEER_ALERT Keyword Manager</h1>
            
            <button id="connectBtn" style="padding: 10px 20px; font-size: 16px; margin: 10px 0;">
                Connect to Device
            </button>
            
            <div id="status" style="margin: 10px 0; padding: 10px; background: #f0f0f0;">
                Status: Not connected
            </div>
            
            <div id="controls" style="display: none;">
                <h3>Write Keywords</h3>
                <input type="text" id="keywordsInput" 
                       placeholder="Enter keywords (comma-separated)" 
                       style="width: 300px; padding: 5px;">
                <button id="writeBtn" style="padding: 5px 15px; margin-left: 10px;">
                    Write Keywords
                </button>
                
                <h3>Current Keywords</h3>
                <button id="readBtn" style="padding: 5px 15px; margin-bottom: 10px;">
                    Read Keywords
                </button>
                <div id="currentKeywords" style="padding: 10px; background: #e8f4f8; min-height: 50px;">
                    Click "Read Keywords" to see current values
                </div>
                
                <h3>Live Updates</h3>
                <button id="subscribeBtn" style="padding: 5px 15px;">
                    Subscribe to Updates
                </button>
                <button id="unsubscribeBtn" style="padding: 5px 15px; display: none;">
                    Unsubscribe
                </button>
                <div id="updates" style="padding: 10px; background: #fff3cd; margin-top: 10px; display: none;">
                    Waiting for updates...
                </div>
                
                <button id="disconnectBtn" style="padding: 10px 20px; margin-top: 20px; background: #dc3545; color: white; border: none;">
                    Disconnect
                </button>
            </div>
        </div>
    `;

    const client = new KeywordsClient();
    let subscribed = false;

    // Connect button
    document.getElementById('connectBtn').addEventListener('click', async () => {
        document.getElementById('status').textContent = "Status: Connecting...";
        const connected = await client.scanAndConnect();
        
        if (connected) {
            document.getElementById('status').textContent = "Status: Connected ✅";
            document.getElementById('connectBtn').style.display = 'none';
            document.getElementById('controls').style.display = 'block';
        } else {
            document.getElementById('status').textContent = "Status: Connection failed ❌";
        }
    });

    // Write button
    document.getElementById('writeBtn').addEventListener('click', async () => {
        const input = document.getElementById('keywordsInput').value;
        const keywords = input.split(',').map(k => k.trim()).filter(k => k);
        
        if (keywords.length === 0) {
            alert("Please enter at least one keyword");
            return;
        }

        const success = await client.writeKeywords(keywords);
        if (success) {
            document.getElementById('status').textContent = `Status: Keywords written! (${keywords.join(", ")})`;
        }
    });

    // Read button
    document.getElementById('readBtn').addEventListener('click', async () => {
        const data = await client.readKeywords();
        if (data) {
            document.getElementById('currentKeywords').innerHTML = `
                <strong>Keywords:</strong> ${data.keywords.join(", ")}<br>
                <strong>Count:</strong> ${data.count}
            `;
        }
    });

    // Subscribe button
    document.getElementById('subscribeBtn').addEventListener('click', async () => {
        await client.subscribeToUpdates((data) => {
            const updatesDiv = document.getElementById('updates');
            updatesDiv.style.display = 'block';
            updatesDiv.innerHTML = `
                🔔 <strong>Update received!</strong><br>
                Keywords: ${data.keywords.join(", ")}<br>
                Count: ${data.count}<br>
                Time: ${new Date().toLocaleTimeString()}
            `;
        });
        
        document.getElementById('subscribeBtn').style.display = 'none';
        document.getElementById('unsubscribeBtn').style.display = 'inline';
        document.getElementById('status').textContent = "Status: Subscribed to updates 🔔";
    });

    // Unsubscribe button
    document.getElementById('unsubscribeBtn').addEventListener('click', async () => {
        await client.unsubscribe();
        document.getElementById('subscribeBtn').style.display = 'inline';
        document.getElementById('unsubscribeBtn').style.display = 'none';
        document.getElementById('updates').style.display = 'none';
        document.getElementById('status').textContent = "Status: Unsubscribed";
    });

    // Disconnect button
    document.getElementById('disconnectBtn').addEventListener('click', () => {
        client.disconnect();
        document.getElementById('status').textContent = "Status: Disconnected";
        document.getElementById('controls').style.display = 'none';
        document.getElementById('connectBtn').style.display = 'block';
    });
}

// ============================================
// Export for use in other files
// ============================================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeywordsClient;
}

// ============================================
// Auto-run example if in browser
// ============================================
if (typeof window !== 'undefined') {
    console.log("KeywordsClient loaded!");
    console.log("Available functions:");
    console.log("- example1_writeKeywords()");
    console.log("- example2_writeAndRead()");
    console.log("- example3_subscribeToUpdates()");
    console.log("- createInteractivePage()");
    console.log("\nTo use: Call any example function or use KeywordsClient class directly");
}



```





## Error Handling

### Write Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| 0x01 | Invalid JSON format | Check JSON syntax |
| 0x02 | Keywords array too large | Limit to 20 keywords max |
| 0x03 | Invalid keyword format | Use alphanumeric strings only |
| 0x0D | Write not permitted | Check characteristic properties |

### Read Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| 0x0A | Attribute not found | Verify characteristic UUID |
| 0x0E | Unlikely error | Retry connection |

---

## Device States

### Operational Modes

**1. Download Mode (Initial State)**
- Advertising as connectable peripheral
- Accepts keyword writes via KEYWORDS_WRITE
- LED: Purple/Blue

**2. Scan Mode**
- Scanning for nearby devices
- Matching keywords with discovered devices
- LED: Yellow (scanning), Cyan (match found)

**Mode Switching:**
- Press physical button on device
- Or write special command to KEYWORDS_WRITE: `{"command": "switch_mode"}`

---

## Implementation Reference (ESP32 MicroPython)

```python
import bluetooth
import json
from micropython import const

# UUIDs
SERVICE_UUID = bluetooth.UUID("a07498ca-ad5b-474e-940d-16f1fbe7e8cd")
WRITE_CHAR_UUID = bluetooth.UUID("b07498ca-ad5b-474e-940d-16f1fbe7e8cd")
READ_CHAR_UUID = bluetooth.UUID("c07498ca-ad5b-474e-940d-16f1fbe7e8cd")

# Flags
_FLAG_READ = const(0x02)
_FLAG_WRITE = const(0x08)
_FLAG_NOTIFY = const(0x10)

# Define characteristics
write_char = (WRITE_CHAR_UUID, _FLAG_WRITE)
read_char = (READ_CHAR_UUID, _FLAG_READ | _FLAG_NOTIFY)

# Define service
keywords_service = (SERVICE_UUID, (write_char, read_char))

# Register with BLE
ble = bluetooth.BLE()
ble.active(True)
((write_handle, read_handle),) = ble.gatts_register_services((keywords_service,))

# Start advertising
device_name = "NIMI_PEER_ALERT"
adv_data = bytes([0x02, 0x01, 0x06]) + \
           bytes([len(device_name) + 1, 0x09]) + device_name.encode()
ble.gap_advertise(100000, adv_data, connectable=True)
```

---

## Testing Checklist

- [ ] Device advertises with correct name "NIMI_PEER_ALERT"
- [ ] KEYWORDS service is discoverable
- [ ] KEYWORDS_WRITE accepts valid JSON
- [ ] KEYWORDS_WRITE rejects invalid JSON
- [ ] KEYWORDS_READ returns current keywords
- [ ] KEYWORDS_READ notifications work when keywords update
- [ ] Multiple clients can connect sequentially
- [ ] Keywords persist after device reboot
- [ ] LED status indicators work correctly
- [ ] Mode switching functions properly

---

## AI Integration Prompt Template

Use this template when describing the device to an AI:

```
I have a BLE device with the following specification:

Device Name: NIMI_PEER_ALERT
Hardware: ESP32 with BLE

Service: KEYWORDS
- Service UUID: a07498ca-ad5b-474e-940d-16f1fbe7e8cd

Characteristics:
1. KEYWORDS_WRITE (UUID: b07498ca-ad5b-474e-940d-16f1fbe7e8cd)
   - Properties: WRITE
   - Purpose: Write keyword list to device
   - Format: JSON string like {"keywords": ["python", "iot"]}

2. KEYWORDS_READ (UUID: c07498ca-ad5b-474e-940d-16f1fbe7e8cd)
   - Properties: READ, NOTIFY
   - Purpose: Read current keywords and get updates
   - Format: JSON string like {"keywords": ["python", "iot"], "count": 2}

Please help me [write code to / troubleshoot / implement / ...]
```

---

## Version History

**v1.0** - Initial specification
- Basic KEYWORDS service
- READ and WRITE characteristics
- JSON data format

---

## References

- [Bluetooth Core Specification](https://www.bluetooth.com/specifications/specs/)
- [ESP32 MicroPython BLE Documentation](https://docs.micropython.org/en/latest/library/bluetooth.html)
- [GATT Specification](https://www.bluetooth.com/specifications/specs/gatt-specification-supplement/)
- [UUID Generator](https://www.uuidgenerator.net/)