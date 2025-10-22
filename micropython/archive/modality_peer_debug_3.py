# modality_peer_debug.py - Enhanced with detailed logging
import time
import ujson as json
from micropython import const
import machine

class PeerScanner:
    """
    Modality 2: Scan for peers advertising DEVICE_NAME, connect, read KEYWORDS_READ,
    compare with local keywords, and alert on match.
    """
    def __init__(self, ble, defs, writer_instance, device_mac=None, neopixel=None, buzzer_pin=None):
        print("[SCANNER] Initializing PeerScanner...")
        self._ble = ble
        self._defs = defs
        self.writer = writer_instance
        self.device_mac = device_mac
        self.neopixel = neopixel
        self.buzzer_pin = buzzer_pin
        self._ble.irq(self._irq)
        self._scanning = False
        self._found = {}
        self._conn_handle = None
        self._peer_char_handle = None
        self._peer_read_results = None
        print("[SCANNER] ✅ PeerScanner initialized (MAC: {})".format(device_mac.hex() if device_mac else "unknown"))

    def _irq(self, event, data):
        if event == self._defs.IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            addr_bytes = bytes(addr)
            print("[SCANNER] 📡 Scan result: addr_type={}, rssi={}, adv_len={}".format(addr_type, rssi, len(adv_data)))

            if self._advertisement_has_name(adv_data, self._defs.DEVICE_NAME):
                print("[SCANNER] ✅ Found device: {} (rssi={})".format(self._defs.DEVICE_NAME, rssi))
                print("XXXXX YES YES YES YES YES XXXXXX")
                self._found[addr_bytes] = (addr_type, addr_bytes, rssi, adv_data)
            else:
                print("[SCANNER] ❌ Device found but name doesn't match")

        elif event == self._defs.IRQ_SCAN_COMPLETE:
            print("[SCANNER] 🏁 SCAN COMPLETE")
            print("[SCANNER] Found {} peer(s)".format(len(self._found)))

            for addr_bytes, info in list(self._found.items()):
                if self.writer.interrupted:
                    print("[SCANNER] ⚠️  Write in progress, skipping peer connection")
                    break

                addr_type, addr, rssi, adv_data = info

                # MAC address comparison for role determination
                peer_mac = addr  # addr is already addr_bytes from storage
                print("[SCANNER] [DEBUG] Peer MAC: {}".format(peer_mac.hex()))
                print("[SCANNER] [DEBUG] Our MAC:  {}".format(self.device_mac.hex()))

                if self.device_mac and peer_mac > self.device_mac:
                    print("[SCANNER] ℹ️  Peer MAC is higher, we are CLIENT (will initiate connection)")
                    should_connect = True
                else:
                    print("[SCANNER] ℹ️  Peer MAC is lower or equal, we are SERVER (waiting for peer to connect)")
                    should_connect = False

                if not should_connect:
                    print("[SCANNER] Skipping connection attempt (not client role)")
                    continue

                print("[SCANNER] Attempting to connect to peer (rssi={})...".format(rssi))

                try:
                    print("[SCANNER] Calling gap_connect...")
                    self._ble.gap_connect(addr_type, addr)

                    # Wait for connection
                    t0 = time.ticks_ms()
                    timeout = 5000
                    while self._conn_handle is None and time.ticks_diff(time.ticks_ms(), t0) < timeout:
                        time.sleep_ms(50)

                    if self._conn_handle is None:
                        print("[SCANNER] ❌ Connection timeout")
                        continue

                    print("[SCANNER] ✅ Connected! conn_handle={}".format(self._conn_handle))

                    # Discover services
                    print("[SCANNER] Discovering services...")
                    self._ble.gattc_discover_services(self._conn_handle)

                    # Wait for service discovery
                    t0 = time.ticks_ms()
                    timeout = 4000
                    while self._peer_char_handle is None and time.ticks_diff(time.ticks_ms(), t0) < timeout:
                        time.sleep_ms(50)

                    if self._peer_char_handle is None:
                        print("[SCANNER] ❌ Service discovery timeout")
                        continue

                    print("[SCANNER] ✅ Characteristic found: handle={}".format(self._peer_char_handle))

                    # Read the characteristic
                    print("[SCANNER] Reading peer keywords...")
                    self._ble.gattc_read(self._conn_handle, self._peer_char_handle)

                    # Wait for read result
                    t0 = time.ticks_ms()
                    timeout = 3000
                    while self._peer_read_results is None and time.ticks_diff(time.ticks_ms(), t0) < timeout:
                        time.sleep_ms(50)

                    if self._peer_read_results:
                        print("[SCANNER] ✅ Read complete: {} bytes".format(len(self._peer_read_results)))
                        self._process_peer_payload(self._peer_read_results)
                    else:
                        print("[SCANNER] ❌ Read timeout")

                    # Disconnect
                    try:
                        print("[SCANNER] Disconnecting...")
                        self._ble.gap_disconnect(self._conn_handle)
                    except Exception as e:
                        print("[SCANNER] ⚠️  Disconnect error: {}".format(e))

                except Exception as e:
                    print("[SCANNER] ❌ Error during peer connection: {}".format(e))

                finally:
                    # Reset per-connection state
                    self._conn_handle = None
                    self._peer_char_handle = None
                    self._peer_read_results = None

            # Done with current scan cycle
            self._found = {}
            print("[SCANNER] Scan cycle complete\n")

        elif event == self._defs.IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            print("[SCANNER] 🔗 PERIPHERAL_CONNECT: conn_handle={}".format(conn_handle))
            self._conn_handle = conn_handle

        elif event == self._defs.IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            print("[SCANNER] 🔌 PERIPHERAL_DISCONNECT: conn_handle={}".format(conn_handle))
            if conn_handle == self._conn_handle:
                self._conn_handle = None

        elif event == self._defs.IRQ_GATTC_SERVICE_RESULT:
            try:
                conn_handle, start_handle, end_handle, uuid = data
                print("[SCANNER] 🔍 SERVICE_RESULT: uuid={}, handles={}-{}".format(uuid, start_handle, end_handle))

                try:
                    if bytes(uuid).find(bytes(self._defs.SERVICE_UUID)) != -1:
                        print("[SCANNER] ✅ Found our service! Discovering characteristics...")
                        self._ble.gattc_discover_characteristics(self._conn_handle, start_handle, end_handle)
                except Exception:
                    print("[SCANNER] ⚠️  UUID comparison failed, attempting discovery anyway...")
                    self._ble.gattc_discover_characteristics(self._conn_handle, start_handle, end_handle)
            except Exception as e:
                print("[SCANNER] ❌ SERVICE_RESULT error: {}".format(e))

        elif event == self._defs.IRQ_GATTC_CHARACTERISTIC_RESULT:
            try:
                conn_handle, def_handle, value_handle, properties, uuid = data
                print("[SCANNER] 📋 CHAR_RESULT: uuid={}, value_handle={}".format(uuid, value_handle))

                try:
                    if uuid == self._defs.KEYWORDS_READ_UUID:
                        print("[SCANNER] ✅ Found KEYWORDS_READ characteristic!")
                        self._peer_char_handle = value_handle
                except Exception:
                    try:
                        if bytes(uuid) == bytes(self._defs.KEYWORDS_READ_UUID):
                            print("[SCANNER] ✅ Found KEYWORDS_READ characteristic (bytes match)!")
                            self._peer_char_handle = value_handle
                    except Exception as e:
                        print("[SCANNER] ⚠️  UUID match error: {}".format(e))
            except Exception as e:
                print("[SCANNER] ❌ CHAR_RESULT error: {}".format(e))

        elif event == self._defs.IRQ_GATTC_READ_RESULT:
            conn_handle, value_handle, char_data = data
            print("[SCANNER] 📖 READ_RESULT: {} bytes".format(len(char_data) if char_data else 0))
            self._peer_read_results = char_data

        elif event == self._defs.IRQ_GATTC_READ_DONE:
            print("[SCANNER] ✅ READ_DONE")

    def _advertisement_has_name(self, adv_data, name):
        """Parse adv_data for AD type 0x09 (complete local name)"""
        print("[SCANNER] [DEBUG] Parsing adv_data ({} bytes): {}".format(len(adv_data), adv_data.hex()))
        print("[SCANNER] [DEBUG] Looking for name: '{}'".format(name))

        i = 0
        found_types = []
        while i + 1 < len(adv_data):
            length = adv_data[i]
            if length == 0:
                print("[SCANNER] [DEBUG] Found length=0, stopping")
                break

            ad_type = adv_data[i+1]
            found_types.append(ad_type)
            print("[SCANNER] [DEBUG] At offset {}: length={}, type=0x{:02x}".format(i, length, ad_type))

            if ad_type == 0x09:  # Complete Local Name
                start = i + 2
                end = start + (length - 1)
                print("[SCANNER] [DEBUG] Found type 0x09 at offset {}".format(i))
                print("[SCANNER] [DEBUG] Name data: bytes[{}:{}] = {}".format(start, end+1, adv_data[start:end+1]))
                try:
                    adv_name = bytes(adv_data[start:end+1]).decode('utf-8')
                    print("[SCANNER] [DEBUG] Decoded name: '{}'".format(adv_name))
                    matches = adv_name == name
                    print("[SCANNER] [DEBUG] Matches '{}': {}".format(name, matches))
                    return matches
                except Exception as e:
                    print("[SCANNER] [DEBUG] Decode error: {}".format(e))
                    return False

            i += 1 + length

        print("[SCANNER] [DEBUG] Found AD types: {}".format([hex(t) for t in found_types]))
        print("[SCANNER] [DEBUG] Type 0x09 not found in advertisement")
        return False

    def _process_peer_payload(self, raw):
        print("[SCANNER] Processing peer payload...")
        try:
            s = raw.decode('utf-8')
            print("[SCANNER] Decoded: {}".format(s))
            payload = json.loads(s)
            print("[SCANNER] Parsed JSON: {}".format(payload))
        except Exception as e:
            print("[SCANNER] ❌ Failed to parse: {}".format(e))
            return

        their = payload.get("keywords", [])
        print("[SCANNER] Peer keywords: {}".format(their))

        if not isinstance(their, list):
            print("[SCANNER] ❌ Keywords not a list")
            return

        their = [x.lower().strip() for x in their if isinstance(x, str)]
        local = [k.lower().strip() for k in self.writer.get_keywords()]

        print("[SCANNER] Local keywords: {}".format(local))
        print("[SCANNER] Comparing...")

        # Find intersection
        matches = set(local).intersection(set(their))

        if matches:
            print("[SCANNER] 🎯 MATCH FOUND: {}".format(matches))
            self.alert(matches)
        else:
            print("[SCANNER] ❌ No matches")

    def alert(self, matches):
        """Provide a simple alert: blink neopixel and pulse buzzer."""
        try:
            print("[ALERT] 🚨 ALERT TRIGGERED: {}".format(matches))

            # NeoPixel: blink sequence
            if self.neopixel is not None:
                print("[ALERT] Blinking NeoPixel...")
                for i in range(3):
                    print("[ALERT] Blink {}/3".format(i+1))
                    self.neopixel.fill((255, 0, 0))  # Red
                    self.neopixel.write()
                    time.sleep_ms(200)
                    self.neopixel.fill((0, 0, 0))    # Off
                    self.neopixel.write()
                    time.sleep_ms(200)
                print("[ALERT] ✅ NeoPixel sequence complete")

            # Buzzer: drive PWM tone
            if self.buzzer_pin is not None:
                print("[ALERT] Beeping buzzer...")
                pwm = machine.PWM(self.buzzer_pin)
                pwm.freq(1000)
                pwm.duty_u16(20000)
                time.sleep_ms(400)
                pwm.duty_u16(0)
                pwm.deinit()
                print("[ALERT] ✅ Buzzer beep complete")

        except Exception as e:
            print("[ALERT] ❌ Alert error: {}".format(e))

    def start_scan(self, scan_ms=3000):
        """Trigger a scan for nearby devices."""
        if self.writer.interrupted:
            print("[SCANNER] ⏸️  Scan skipped (write in progress)")
            return

        try:
            print("[SCANNER] Starting BLE scan ({} ms)...".format(scan_ms))
            self._ble.gap_scan(scan_ms, 30000, 30000)
            self._scanning = True
            print("[SCANNER] ✅ Scan started")
        except Exception as e:
            print("[SCANNER] ❌ Scan failed: {}".format(e))

    def stop_scan(self):
        try:
            self._ble.gap_scan(None)
            print("[SCANNER] ✅ Scan stopped")
        except Exception:
            pass
        self._scanning = False
