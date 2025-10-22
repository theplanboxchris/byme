# modality_write_debug.py - Enhanced with detailed logging
import ujson as json
import time
from micropython import const

class KeywordWriter:
    """
    Modality 1: GATT server for KEYWORDS service.
    Exposes KEYWORDS_WRITE (write-only) and KEYWORDS_READ (read/notify).
    When a write arrives: parse JSON, save to keywords.json, update internal state,
    send NOTIFY to subscribed clients, and set interrupt flag.
    """
    def __init__(self, ble, defs, storage_path="keywords.json"):
        print("[WRITER] Initializing KeywordWriter...")
        self._ble = ble
        self._defs = defs
        self._storage_path = storage_path
        self._connections = set()
        self._cccd_handles = {}
        self.interrupted = False
        self.keywords = []
        self.last_updated = 0
        self._register_services()
        self._ble.irq(self._irq)
        print("[WRITER] ✅ KeywordWriter initialized")

    def _register_services(self):
        print("[WRITER] Registering GATT services...")
        write_chr = (self._defs.KEYWORDS_WRITE_UUID, self._defs.FLAG_WRITE | self._defs.FLAG_WRITE_NO_RESPONSE)
        read_chr  = (self._defs.KEYWORDS_READ_UUID, self._defs.FLAG_READ | self._defs.FLAG_NOTIFY)
        service = (self._defs.SERVICE_UUID, (write_chr, read_chr))

        try:
            ((self._handle_write, self._handle_read),) = self._ble.gatts_register_services((service,))
            print("[WRITER] ✅ Services registered")
            print("[WRITER] Write characteristic handle: {}".format(self._handle_write))
            print("[WRITER] Read characteristic handle: {}".format(self._handle_read))
        except Exception as e:
            print("[WRITER] ❌ Failed to register services: {}".format(e))
            raise

        self._update_read_value()

    def _irq(self, event, data):
        if event == self._defs.IRQ_CENTRAL_CONNECT:
            conn_handle, _, = data
            print("[WRITER] 🔗 CENTRAL CONNECTED: conn_handle={}".format(conn_handle))
            self._connections.add(conn_handle)
            print("[WRITER] Total connections: {}".format(len(self._connections)))

        elif event == self._defs.IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, = data
            print("[WRITER] 🔌 CENTRAL DISCONNECTED: conn_handle={}".format(conn_handle))
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            print("[WRITER] Remaining connections: {}".format(len(self._connections)))

        elif event == self._defs.IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            print("[WRITER] ✏️  WRITE EVENT: conn_handle={}, handle={}".format(conn_handle, value_handle))

            if value_handle == self._handle_write:
                print("[WRITER] Write to KEYWORDS_WRITE characteristic")
                raw = self._ble.gatts_read(self._handle_write)
                print("[WRITER] Raw data received: {} bytes".format(len(raw) if raw else 0))
                print("[WRITER] Data: {}".format(raw))
                self._on_write(raw, conn_handle)
            else:
                print("[WRITER] Write to unknown handle (not our characteristic)")

    def _on_write(self, raw_data, conn_handle):
        """Handle incoming JSON write: validate, persist, update read char, notify."""
        print("[WRITER] Processing write payload...")

        try:
            s = raw_data.decode('utf-8')
            print("[WRITER] Decoded as UTF-8: {}".format(s))
        except Exception as e:
            print("[WRITER] ❌ Failed to decode UTF-8: {}".format(e))
            return

        try:
            payload = json.loads(s)
            print("[WRITER] ✅ Parsed JSON: {}".format(payload))
        except Exception as e:
            print("[WRITER] ❌ Failed to parse JSON: {}".format(e))
            return

        # Validate expected structure
        keywords = payload.get("keywords")
        print("[WRITER] Keywords field: {}".format(keywords))

        if not isinstance(keywords, list):
            print("[WRITER] ❌ Keywords is not a list")
            return

        # Normalize to lowercase strings
        clean = []
        for k in keywords:
            if isinstance(k, str):
                v = k.strip()
                if v:
                    clean.append(v.lower())

        print("[WRITER] Cleaned keywords: {}".format(clean))
        self.keywords = clean
        self.last_updated = int(time.time())

        # Persist
        print("[WRITER] Saving to {}...".format(self._storage_path))
        try:
            with open(self._storage_path, "w") as f:
                json.dump({
                    "keywords": self.keywords,
                    "last_updated": self.last_updated
                }, f)
            print("[WRITER] ✅ File saved successfully")
        except Exception as e:
            print("[WRITER] ❌ Failed to save file: {}".format(e))
            return

        # Update GATT read characteristic value
        self._update_read_value()

        # Notify connected centrals
        print("[WRITER] Notifying {} connected client(s)...".format(len(self._connections)))
        for conn in list(self._connections):
            try:
                self._ble.gatts_notify(conn, self._handle_read, self._gatt_read_payload())
                print("[WRITER] ✅ Notification sent to conn_handle={}".format(conn))
            except Exception as e:
                print("[WRITER] ⚠️  Notify failed for conn_handle={}: {}".format(conn, e))

        # Set interrupted flag
        self.interrupted = True
        print("[WRITER] 🚨 Interrupt flag set (scanner will pause)")

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
            payload = self._gatt_read_payload()
            self._ble.gatts_write(self._handle_read, payload)
            print("[WRITER] ✅ Read characteristic updated ({} bytes)".format(len(payload)))
        except Exception as e:
            print("[WRITER] ⚠️  Failed to update read characteristic: {}".format(e))

    def load_from_storage(self):
        print("[WRITER] Loading keywords from storage...")
        try:
            with open(self._storage_path, "r") as f:
                data = json.load(f)
            print("[WRITER] ✅ File loaded")

            kws = data.get("keywords", [])
            if isinstance(kws, list):
                self.keywords = [k.lower().strip() for k in kws if isinstance(k, str) and k.strip()]
                print("[WRITER] ✅ Loaded {} keywords: {}".format(len(self.keywords), self.keywords))
            self.last_updated = data.get("last_updated", int(time.time()))
        except Exception as e:
            print("[WRITER] ⚠️  Could not load file: {}".format(e))
            print("[WRITER] Starting with empty keywords")
            self.keywords = []
            self.last_updated = 0

        self._update_read_value()

    def clear_interrupt(self):
        self.interrupted = False
        print("[WRITER] 🚨 Interrupt flag cleared")

    def get_keywords(self):
        return list(self.keywords)
