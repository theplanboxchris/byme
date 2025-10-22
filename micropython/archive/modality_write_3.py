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
        write_chr = (self._defs.KEYWORDS_WRITE_UUID, self._defs.FLAG_WRITE | self._defs.FLAG_WRITE_NO_RESPONSE)
        read_chr  = (self._defs.KEYWORDS_READ_UUID, self._defs.FLAG_READ | self._defs.FLAG_NOTIFY)
        service = (self._defs.SERVICE_UUID, (write_chr, read_chr))
        ((self._handle_write, self._handle_read),) = self._ble.gatts_register_services((service,))
        # set an initial value for read characteristic
        self._update_read_value()
        # advertise is done in main (not here)

    def _irq(self, event, data):
        if event == self._defs.IRQ_CENTRAL_CONNECT:
            conn_handle, _, = data
            self._connections.add(conn_handle)
        elif event == self._defs.IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
        elif event == self._defs.IRQ_GATTS_WRITE:
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
