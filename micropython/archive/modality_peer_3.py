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
    def __init__(self, ble, defs, writer_instance, device_mac=None, neopixel=None, buzzer_pin=None):
        self._ble = ble
        self._defs = defs
        self.writer = writer_instance  # to get local keywords
        self.device_mac = device_mac
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
        if event == self._defs.IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            # simple parse: check for device name in adv_data (complete local name 0x09)
            if self._advertisement_has_name(adv_data, self._defs.DEVICE_NAME):
                # store peer address and attempt connect
                addr_bytes = bytes(addr)
                self._found[addr_bytes] = (addr_type, addr_bytes, rssi, adv_data)
        elif event == self._defs.IRQ_SCAN_COMPLETE:
            # scanning ended, proceed to connect sequentially to found peers
            for addr_bytes, info in list(self._found.items()):
                if self.writer.interrupted:
                    # if a write happened, stop attempting to connect
                    break
                addr_type, addr, rssi, adv_data = info

                # MAC address comparison for role determination
                peer_mac = addr
                if self.device_mac and peer_mac > self.device_mac:
                    # We are CLIENT - initiate connection
                    pass  # continue to connect
                else:
                    # We are SERVER - skip connection attempt
                    continue

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
        elif event == self._defs.IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._conn_handle = conn_handle
        elif event == self._defs.IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            if conn_handle == self._conn_handle:
                self._conn_handle = None
        elif event == self._defs.IRQ_GATTC_SERVICE_RESULT:
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
        elif event == self._defs.IRQ_GATTC_CHARACTERISTIC_RESULT:
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
        elif event == self._defs.IRQ_GATTC_READ_RESULT:
            conn_handle, value_handle, char_data = data
            # store read result
            self._peer_read_results = char_data
        elif event == self._defs.IRQ_GATTC_READ_DONE:
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
                    adv_name = bytes(adv_data[start:end+1]).decode('utf-8')
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
