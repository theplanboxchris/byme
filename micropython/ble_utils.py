import bluetooth, ubinascii, struct, time, machine, neopixel, ujson
import json
from micropython import const

# filenames
KEYWORDS_FILE = "keywords.json"


# UUIDs and flags
SERVICE_UUID = bluetooth.UUID("a07498ca-ad5b-474e-940d-16f1fbe7e8cd")
KEYWORDS_UUID = bluetooth.UUID("b07498ca-ad5b-474e-940d-16f1fbe7e8cd")

_FLAG_WRITE = const(0x08)
_FLAG_READ  = const(0x02)


# BLE IRQ aliases for readability - check these are right???????????????????????????
IRQ_SCAN_RESULT = const(5)        # bluetooth.IRQ_SCAN_RESULT
IRQ_SCAN_DONE = const(6)
IRQ_CENTRAL_CONNECT = const(1)    # bluetooth.IRQ_CENTRAL_CONNECT
IRQ_CENTRAL_DISCONNECT = const(2) # bluetooth.IRQ_CENTRAL_DISCONNECT
IRQ_GATTS_WRITE = const(3)       # bluetooth.IRQ_GATTS_WRITE ????????????????????????????????

# Open the keywords.json file to start the process
def load_keywords():
    try:
        with open(KEYWORDS_FILE, "r") as f:
            keywords = ujson.load(f)
    except Exception as e:
        print("Failed to load keywords.json:", e)
        keywords = {}
    return keywords

# Create a device name with the last 4 letters from the MAC name
def device_name(ble):
    mac = ubinascii.hexlify(ble.config('mac')[1]).decode().upper()
    dev_name = "NIMI_DEV_" + mac[-4:]
    return dev_name #.encode()

def advertising_payload(name=None, manufacturer_data=None, services=None):
    """
    Build BLE advertising and scan response payloads (bytes).
    Returns: (adv_data, sr_data)
      adv_data  -> includes name, optional services
      sr_data   -> includes manufacturer data
    """

    adv_data = bytearray()
    sr_data = bytearray()

    def _append(buf, ad_type, value_bytes):
        length = 1 + len(value_bytes)
        buf.extend(bytes((length, ad_type)))
        buf.extend(value_bytes)

    # Complete local name (0x09) -> goes in advertising packet
    if name:
        name_bytes = name.encode()
        _append(adv_data, 0x09, name_bytes)

    # 16-bit Service UUIDs (0x03) -> optional, also advertising
    if services:
        svc_bytes = bytearray()
        for s in services:
            svc_bytes.extend(bytes((s & 0xFF, (s >> 8) & 0xFF)))
        _append(adv_data, 0x03, svc_bytes)

    # Manufacturer specific data (0xFF) -> goes in scan response
    if manufacturer_data:
        if not isinstance(manufacturer_data, (bytes, bytearray)):
            raise TypeError("manufacturer_data must be bytes or bytearray")
        _append(sr_data, 0xFF, bytes(manufacturer_data))

    return bytes(adv_data), bytes(sr_data)


def decode_name(adv_data):
    """Extract the first complete/short name field from adv_data (bytes) or None."""
    i = 0
    while i + 1 < len(adv_data):
        length = adv_data[i]
        if length == 0:
            break
        ad_type = adv_data[i + 1]
        if ad_type in (0x09, 0x08):  # complete or short local name
            start = i + 2
            end = start + length - 1
            try:
                return adv_data[start:end].decode().strip() # stripping any trailing whitespace here fixes name invalid error - check it doesnt break if we have more than name in packet
            except Exception:
                return None
        i += 1 + length
    return None

def decode_manufacturer(adv_data):

    adv_data = bytes(adv_data)

    """Return manufacturer data as a list of 4-byte little-endian integers (first AD type 0xFF) or None."""
    i = 0
    while i + 1 < len(adv_data):
        length = adv_data[i]
        if length == 0:
            break
        ad_type = adv_data[i + 1]
        if ad_type == 0xFF:
            start = i + 2
            end = start + length - 1
            mdata = adv_data[start:end]
            # Convert to array of 4-byte little-endian ints
            return [int.from_bytes(mdata[j:j+4], 'little') for j in range(0, len(mdata), 4) if len(mdata[j:j+4]) == 4]
        i += 1 + length
    return None

def pack_numbers(numbers):
    """
    Convert a list of integers into a bytes array.
    Each number is packed as 4 bytes (little-endian).
    If the list is empty, returns empty bytes.
    """
    if not numbers:  # empty list
        return b''
    return b''.join(struct.pack('<I', n) for n in numbers)

def blink_neopixel(pin_num=2, color=(255, 0, 0), blink_time=0.1, duration=5):
    pin = machine.Pin(pin_num)
    np = neopixel.NeoPixel(pin, 1)
    end_time = time.time() + duration
    while time.time() < end_time:
        np[0] = color      # On
        np.write()
        time.sleep(blink_time)
        np[0] = (0, 0, 0)  # Off
        np.write()
        time.sleep(blink_time)

class BLEPeripheral:

    seen = {}  # class-level dictionary

    def __init__(self, ble, name="NIMI_DEV_0000", keywords=None):
        self._ble = ble
        self._ble.irq(self._irq)
        self.name = name
        self._receive_buffer = ""
        self.ignore_list = {}
        self.IGNORE_DURATION = 3  # seconds - !! make this longer in practice !!
        self.MAX_DISTANCE = 60
        self.MIN_DISTANCE = 0

        self._update_keywords(keywords)

        self._connections = set()

        # register GATT service + characteristic (read/write)
        keywords_char = (KEYWORDS_UUID, _FLAG_READ | _FLAG_WRITE)
        service = (SERVICE_UUID, (keywords_char,))
        handles = self._ble.gatts_register_services((service,))
        # handles is a tuple of services; each service entry is a tuple of handles for its characteristics.
        # handles[0] -> tuple of char handles for service 0; the first char's handle is handles[0][0]
        self._keywords_handle = handles[0][0]

        # ready to advertise & scan (user must call advertise() and start_scan())
        self._adv_interval_ms = 500_000

    # set the internal keywords (full JSON dictionary) and numbers (list of the indexes only)
    def _update_keywords(self, keywords):
        # Store the keywords as a JSON array and the numbers (for matches) as a python list
        self.keywords = keywords or {} # e.g. {"1432244": "Keyword1", "6543244": "Keyword2"}
        self.numbers = [int(k) for k in self.keywords.keys()] if self.keywords else []


    def _irq(self, event, data):

        #print('[DEBUG] IRQ handler called with event #:', event)

        if event == IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            self._handle_scan_result(addr_type, addr, adv_type, rssi, adv_data)

        elif event == IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._connections.add(conn_handle)
            print("[TRANSFER] Central connected:", bytes(addr))

        elif event == IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            self._connections.discard(conn_handle)
            print("[TRANSFER] Central disconnected")
            # restart advertising after disconnect
            self.advertise()

        elif event == IRQ_GATTS_WRITE:
            print("[TRANSFER] GATTS WRITE")
            conn_handle, attr_handle = data
            if attr_handle == self._keywords_handle:
                raw = self._ble.gatts_read(attr_handle)
                self._on_keywords_write(raw)

    def _handle_scan_result(self, addr_type, addr, adv_type, rssi, adv_data):
        
        adv_data_ba = bytes(adv_data)
        name = decode_name(adv_data_ba)
        addr_str = ":".join(f"{b:02X}" for b in bytes(addr))
        entry = self.seen.get(addr_str)
        now = time.time()
        
        # advertising packet
        if adv_type == 0x00 and name and name.startswith("NIMI_DEV"):
            # This is a regular NIMI_DEV advertising packet
            if entry is None:
                # first time seeing it, add it to the NIMI devices list, set ignore to false for new entries
                entry = {"name": name, "resp": None, "timestamp": now, "ignore": False}
                self.seen[addr_str] = entry
                #print(f"[SCAN] New NIMI_DEV device added: {addr_str}")
                return
            else:
                # Previously seen, set ignore flag based on age of the entry (set to true when recent, false otherwise). 
                interval = now - entry['timestamp']
                entry['ignore'] = True if interval <= self.IGNORE_DURATION else False
                return

        # scan response packet (immediately follows advertising packet)
        if adv_type == 0x04 and entry:
            # Skip any entries with ignore = True
            if entry['ignore'] == False: 
                #entry["resp"] = adv_data_ba
                #print(f"[SCAN] Scan response received for {entry["name"]} at {addr_str}, resp_data: {adv_data_ba}")
                #print(f"[SCAN] ACTIONABLE, Ignore is:", entry['ignore'] )
                
                # Further actions here
                matches = self._check_for_matches(adv_data)
                if matches:      
                    print("[MATCH] Matches found:", matches) 


                # RESETS: 
                # Set IGNORE to True to stop processing next time and reset timestamp to now, waive the scan response data field
                entry['ignore'] = True
                entry['resp'] = None
                entry['timestamp'] = now
                self.seen[addr_str] = entry
            #else:
                # it was recently processed and should be ignored 
                # print(f"[SCAN] IGNORE, Recently processed..Ignore is:", entry['ignore'] )


    # input is a list of scanned keyword indexes. Compare the to internal list and return overlaps as a list
    def _check_for_matches(self, adv_data):
        values = []
        scanned_numbers = decode_manufacturer(adv_data)
        print(f"[SCAN] Scanned numbers are:", scanned_numbers )
        if scanned_numbers:
            ints = list(scanned_numbers)
            matches = [n for n in ints if n in self.numbers]
            if matches:
                values = [self.keywords[str(k)] for k in matches if str(k) in self.keywords]
        return values
       

    def _on_keywords_write(self, raw):
        # raw is bytes written by the client. Expect JSON string representing a list of ints.
        try:
            s = raw.decode() if isinstance(raw, (bytes, bytearray)) else raw
            self._receive_buffer += s
            print("[TRANSFER] Received keywords JSON:", s)
            if "<EOF>" in self._receive_buffer or "<eof>" in self._receive_buffer:
                # Remove <EOF> marker (case-insensitive)
                s_clean = self._receive_buffer.replace("<EOF>", "").replace("<eof>", "").strip()
                # write the manufacturer data to JSON file locally
                with open("keywords.json", "w") as f:
                    json.dump(json.loads(s_clean), f)
                print("[TRANSFER] Saved keywords to keywords.json:", s_clean)

                # renew the advertising package
                self.keywords = json.loads(s_clean)
                self.update_advertising_data()
                self._receive_buffer = ""  # reset for next transfer

        except Exception as e:
            print("Failed to parse keywords JSON:", e)

    def _make_adv_payload(self):
        # manufacturer_data must be bytes and must keep whole adv packet < 31 bytes.
        # We'll pack the keywords as 4 bytes. Trim if too long.

        m = pack_numbers(self.numbers)
        
        # ensure manufacturer_data not too long (conservative)
        if m and len(m) > 100:
            m = m[:100]
        
        # returns two variables: advertising data and scan response data
        return advertising_payload(name=self.name, manufacturer_data=m)

    def advertise(self):
        adv_data, sr_data =  self._make_adv_payload()
        # DEBUG - save the advertising package
        #self.adv_payload = adv_data
        #self.sr_data = sr_data
        # duration_ms=0 (or None) usually means continuous advertising until stopped
        self._ble.gap_advertise(self._adv_interval_ms, adv_data=adv_data, resp_data=sr_data)
        print("Advertising as:", self.name, "payload len:", len(adv_data))
        print("[ DEBUG ] Payload is ", adv_data)
        print("[ DEBUG ] Service response data is ", sr_data)

    # Called after new keywords are downloaded
    def update_advertising_data(self):
        # stop then restart to update adv payload
        try:
            self._ble.gap_advertise(None)  # stop advertising
            # updated keywords before readvertising   
            self._update_keywords(load_keywords()) # load from keyword.json
        except Exception:
            pass
        self.advertise()

    def start_scan(self, duration_ms=0):
        # duration_ms=0 -> continuous, else duration in ms
        # scan_window & scan_interval left default, but micropython API may vary by port.
        self._ble.gap_scan(duration_ms or 0, 50000, 50000, True)
        print("Started scan (duration_ms=%s)" % (duration_ms or "default"))

