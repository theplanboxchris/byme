"""
ESP32-C3 BLE File Receiver with Dual Modes
Mode 1: Continuous scanning for nearby ESP32 devices, compare keywords.json
Mode 2: Receive new keywords.json file from frontend (sendKeywordsOnce)
"""

import bluetooth
import machine
import neopixel
import time
import ujson as json

# -------------------- LED SETUP --------------------
np = neopixel.NeoPixel(machine.Pin(2), 1)

def set_led(color):
    np[0] = color
    np.write()

# LED color codes
LED_IDLE = (255, 0, 0)
LED_SCANNING = (0, 0, 255)
LED_SUCCESS = (0, 255, 0)
LED_ERROR = (255, 0, 255)
LED_RECEIVING = (255, 255, 0)

# -------------------- GLOBALS --------------------
DEVICE_NAME = "ESP32-BLE-FILE"
SERVICE_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")

mode = "scanner"
transfer_done = False

ADVERTISE_MS = 1000
SCAN_MS = 3000
SLEEP_STEP = 0.05  # responsiveness to receiver mode

# -------------------- BLE FILE RECEIVER --------------------
class BLEFileReceiver:
    def __init__(self, ble, service_uuid, char_uuid):
        self.ble = ble
        self.service_uuid = service_uuid
        self.char_uuid = char_uuid
        self.buffer = bytearray()
        self.connected = False

        # Register characteristic
        self.char = (self.char_uuid,
                     bluetooth.FLAG_READ | bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE)
        self.service = (self.service_uuid, (self.char,))
        ((self.char_handle,),) = self.ble.gatts_register_services((self.service,))
        self.ble.irq(self._irq_handler)

    def _irq_handler(self, event, data):
        global transfer_done, mode
        if event == 1:  # connected
            print("[BLE] ✅ Connected — receive mode")
            self.connected = True
            mode = "receiver"
            set_led(LED_RECEIVING)
        elif event == 2:  # disconnected
            print("[BLE] ❌ Disconnected")
            self.connected = False
            set_led(LED_IDLE)
            mode = "scanner"
        elif event == 3:  # write received
            conn_handle, attr_handle = data
            if attr_handle == self.char_handle:
                value = self.ble.gatts_read(attr_handle)
                if value:
                    eof_idx = value.find(b"<EOF>")
                    if eof_idx != -1:
                        value = value[:eof_idx]
                    self.buffer = value
                    try:
                        with open("keywords.json", "wb") as f:
                            f.write(self.buffer)
                        print(f"[FILE] ✅ Received and saved {len(self.buffer)} bytes")
                        set_led(LED_SUCCESS)
                        transfer_done = True
                    except Exception as e:
                        print(f"[FILE] ❌ Save error: {e}")
                        set_led(LED_ERROR)

    def start_advertising(self):
        flags = b'\x02\x01\x06'
        name = DEVICE_NAME.encode()
        name_ad = bytes([len(name) + 1, 0x09]) + name
        adv = flags + name_ad
        self.ble.gap_advertise(100, adv, connectable=True)
        print("[ADV] BLE advertising started")

    def stop_advertising(self):
        self.ble.gap_advertise(None)
        print("[ADV] BLE advertising stopped")

    def get_keywords_for_read(self):
        return self.buffer

# -------------------- KEYWORD SCANNER --------------------
class KeywordScanner:
    def __init__(self, ble):
        self.ble = ble
        self.local_keywords = self._load_local_keywords()
        try:
            self.local_mac = ble.config('mac')[1]
            print(f"[INIT] Local MAC: {self.local_mac}")
        except:
            self.local_mac = b''

    def _load_local_keywords(self):
        try:
            with open("keywords.json", "r") as f:
                data = json.load(f)
                return set(data.get("keywords", []))
        except:
            print("[SCAN] No local keywords.json, starting empty")
            return set()

    def scan_and_exchange(self):
        devices = self._discover_devices(scan_time=SCAN_MS)
        for dev in devices:
            if dev["name"] != DEVICE_NAME or dev["addr"] == self.local_mac:
                continue
            print(f"[SCAN] Found peer {dev['name']} at {dev['addr']}")
            peer_keywords = self._exchange_keywords(dev)
            if peer_keywords:
                common = self.local_keywords.intersection(peer_keywords)
                if common:
                    print(f"[ALERT] Keyword match found! {common}")
                    self._alert_match(common)
                else:
                    set_led(LED_SCANNING)

    def _discover_devices(self, scan_time=3000):
        devices = []

        def irq(event, data):
            # Numeric events: 5 = scan result, 6 = scan complete
            if event == 5:
                addr_type, addr, adv_type, rssi, adv_data = data
                try:
                    name = bluetooth.decode_name(adv_data) or "Unknown"
                except:
                    name = "Unknown"
                devices.append({"name": name, "addr": bytes(addr), "addr_type": addr_type})
            elif event == 6:
                print("[SCAN] Scan complete")

        self.ble.irq(irq)
        self.ble.gap_scan(scan_time)
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < scan_time:
            if mode != "scanner":
                break
            time.sleep(SLEEP_STEP)
        self.ble.gap_scan(None)
        return devices

    def _exchange_keywords(self, device):
        try:
            conn_handle = self.ble.gap_connect(device["addr_type"], device["addr"])
            start_time = time.ticks_ms()
            while not self.ble.gattc_services(conn_handle):
                if time.ticks_diff(time.ticks_ms(), start_time) > 5000:
                    raise RuntimeError("Timeout waiting for services")
            services = self.ble.gattc_services(conn_handle)
            char_handle = None
            for srv in services:
                if srv[0] == SERVICE_UUID:
                    chars = self.ble.gattc_characteristics(conn_handle, srv[0])
                    for c in chars:
                        if c[0] == CHAR_UUID:
                            char_handle = c[1]
                            break
            if char_handle is None:
                raise RuntimeError("Peer characteristic not found")

            # Write local keywords
            with open("keywords.json", "r") as f:
                payload = f.read().encode() + b"<EOF>"
            self.ble.gattc_write(conn_handle, char_handle, payload, 1)
            print(f"[SCAN] Sent {len(payload)} bytes to peer")

            # Read peer keywords
            start_time = time.ticks_ms()
            peer_data = b""
            while True:
                val = self.ble.gattc_read(conn_handle, char_handle)
                if val:
                    peer_data += val
                    if b"<EOF>" in peer_data:
                        break
                if time.ticks_diff(time.ticks_ms(), start_time) > 5000:
                    raise RuntimeError("Timeout reading peer data")
                time.sleep(SLEEP_STEP)

            self.ble.gap_disconnect(conn_handle)
            eof = peer_data.index(b"<EOF>")
            data = json.loads(peer_data[:eof].decode())
            return set(data.get("keywords", []))
        except Exception as e:
            print(f"[SCAN] BLE exchange error: {e}")
            return None

    def _alert_match(self, common):
        for _ in range(3):
            set_led(LED_SUCCESS)
            time.sleep(0.3)
            set_led(LED_SCANNING)
            time.sleep(0.3)

# -------------------- MAIN LOOP --------------------
ble = bluetooth.BLE()
ble.active(True)

receiver = BLEFileReceiver(ble, SERVICE_UUID, CHAR_UUID)
scanner = KeywordScanner(ble)

print("✅ Device ready")
set_led(LED_IDLE)

while True:
    if mode == "scanner":
        # --- Advertise ---
        receiver.start_advertising()
        start_adv = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_adv) < ADVERTISE_MS:
            if mode != "scanner":
                break
            time.sleep(SLEEP_STEP)
        receiver.stop_advertising()

        # --- Scan ---
        scanner.scan_and_exchange()
    elif mode == "receiver":
        set_led(LED_RECEIVING)
        if transfer_done:
            print("[MAIN] Transfer complete — back to scan mode")
            transfer_done = False
            mode = "scanner"

    time.sleep(0.2)
