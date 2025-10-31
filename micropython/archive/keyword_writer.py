# keyword_writer.py - GATT Server for keyword JSON transfer with chunk reassembly
import ujson as json
import time
from ble_defs import (
    SERVICE_UUID, KEYWORDS_WRITE_UUID, KEYWORDS_READ_UUID,
    FLAG_READ, FLAG_WRITE, FLAG_WRITE_NO_RESPONSE, FLAG_NOTIFY,
    IRQ_CENTRAL_CONNECT, IRQ_CENTRAL_DISCONNECT, IRQ_GATTS_WRITE
)

class KeywordWriter:
    """
    GATT server for receiving keyword JSON data from frontend.
    Handles chunked transfers with EOF marker detection and 10-second timeout.
    """

    def __init__(self, ble, storage_path="keywords.json"):
        print("[WRITER] Initializing KeywordWriter...")
        self._ble = ble
        self._storage_path = storage_path
        self._connections = set()
        self._receive_buffer = ""  # Buffer for accumulating chunks
        self._buffer_start_time = None  # Track when first chunk arrives
        self.transfer_complete = False
        self.transfer_error = None

        self._register_services()
        self._ble.irq(self._irq)
        print("[WRITER] ✅ KeywordWriter initialized")

    def _register_services(self):
        """Register GATT service with write and read characteristics"""
        print("[WRITER] Registering GATT services...")

        write_chr = (KEYWORDS_WRITE_UUID, FLAG_WRITE | FLAG_WRITE_NO_RESPONSE)
        read_chr = (KEYWORDS_READ_UUID, FLAG_READ | FLAG_NOTIFY)
        service = (SERVICE_UUID, (write_chr, read_chr))

        try:
            ((self._handle_write, self._handle_read),) = self._ble.gatts_register_services((service,))
            print("[WRITER] ✅ Services registered")
            print("[WRITER] Write characteristic handle: {}".format(self._handle_write))
            print("[WRITER] Read characteristic handle: {}".format(self._handle_read))

            # Initialize read characteristic with status message
            self._update_read_value("ready")
        except Exception as e:
            print("[WRITER] ❌ Failed to register services: {}".format(e))
            raise

    def _irq(self, event, data):
        """Handle BLE IRQ events"""
        if event == IRQ_CENTRAL_CONNECT:
            conn_handle, _ = data
            print("[WRITER] 🔗 CENTRAL CONNECTED: conn_handle={}".format(conn_handle))
            self._connections.add(conn_handle)
            self.transfer_complete = False
            self.transfer_error = None
            self._receive_buffer = ""
            self._buffer_start_time = None
            print("[WRITER] Buffer reset, ready to receive data")

        elif event == IRQ_CENTRAL_DISCONNECT:
            conn_handle, _ = data
            print("[WRITER] 🔌 CENTRAL DISCONNECTED: conn_handle={}".format(conn_handle))
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)

            # Check if transfer was incomplete
            if self._receive_buffer and not self.transfer_complete:
                print("[WRITER] ⚠️  Transfer incomplete at disconnect - buffer cleared")
                self._receive_buffer = ""
                self._buffer_start_time = None

        elif event == IRQ_GATTS_WRITE:
            conn_handle, value_handle = data

            if value_handle == self._handle_write:
                print("[WRITER] ✏️  WRITE EVENT: conn_handle={}, handle={}".format(conn_handle, value_handle))
                raw = self._ble.gatts_read(self._handle_write)
                print("[WRITER] Data received: {} bytes".format(len(raw) if raw else 0))
                self._on_write(raw, conn_handle)

    def _on_write(self, raw_data, conn_handle):
        """Handle incoming chunk of data"""
        if not raw_data:
            print("[WRITER] ⚠️  Empty data received, ignoring")
            return

        try:
            chunk_str = raw_data.decode('utf-8')
            print("[WRITER] Decoded chunk: '{}'".format(chunk_str))
        except Exception as e:
            print("[WRITER] ❌ Failed to decode UTF-8: {}".format(e))
            self.transfer_error = "Decode error"
            return

        # Record start time on first chunk
        if not self._receive_buffer:
            self._buffer_start_time = time.time()
            print("[WRITER] First chunk received, starting 10-second timeout")

        # Add chunk to buffer
        self._receive_buffer += chunk_str
        print("[WRITER] Buffer size: {} bytes".format(len(self._receive_buffer)))

        # Check for EOF marker
        if "<eof>" in self._receive_buffer.lower():
            print("[WRITER] 🎉 EOF marker detected!")
            self._process_complete_transfer()
        else:
            # Check for timeout (10 seconds since first chunk)
            elapsed = time.time() - self._buffer_start_time
            if elapsed > 10:
                print("[WRITER] ❌ TIMEOUT: No data for 10 seconds")
                self.transfer_error = "Transfer timeout"
                self._receive_buffer = ""
                self._buffer_start_time = None
                self._update_read_value("error: timeout")

    def _process_complete_transfer(self):
        """Process the complete JSON transfer"""
        print("[WRITER] Processing complete transfer...")

        # Remove EOF marker and clean up
        json_str = self._receive_buffer.replace("<eof>", "").replace("<EOF>", "")
        json_str = json_str.strip()

        print("[WRITER] JSON string (without EOF): '{}'".format(json_str))

        # Parse JSON
        try:
            keywords_dict = json.loads(json_str)
            print("[WRITER] ✅ Parsed JSON: {}".format(keywords_dict))
        except Exception as e:
            print("[WRITER] ❌ Failed to parse JSON: {}".format(e))
            self.transfer_error = "JSON parse error"
            self._receive_buffer = ""
            self._buffer_start_time = None
            self._update_read_value("error: invalid json")
            return

        # Validate that it's a dict (not a list)
        if not isinstance(keywords_dict, dict):
            print("[WRITER] ❌ JSON is not a dict, received: {}".format(type(keywords_dict)))
            self.transfer_error = "Invalid format"
            self._receive_buffer = ""
            self._buffer_start_time = None
            self._update_read_value("error: not a dict")
            return

        # Save to keywords.json
        print("[WRITER] Saving to {}...".format(self._storage_path))
        try:
            with open(self._storage_path, "w") as f:
                json.dump(keywords_dict, f)
            print("[WRITER] ✅ File saved successfully")
            print("[WRITER] Keywords: {}".format(list(keywords_dict.keys())))
        except Exception as e:
            print("[WRITER] ❌ Failed to save file: {}".format(e))
            self.transfer_error = "File save error"
            self._receive_buffer = ""
            self._buffer_start_time = None
            self._update_read_value("error: save failed")
            return

        # Mark transfer as complete
        self.transfer_complete = True
        self._update_read_value("success")
        print("[WRITER] ✅ Transfer complete!")
        print("[WRITER] 📝 Please restart the device for changes to take effect")

    def _update_read_value(self, status="ready"):
        """Update the read characteristic with status"""
        try:
            status_obj = {
                "status": status,
                "timestamp": int(time.time())
            }
            payload = json.dumps(status_obj).encode('utf-8')
            self._ble.gatts_write(self._handle_read, payload)
            print("[WRITER] ✅ Read characteristic updated: {}".format(status))
        except Exception as e:
            print("[WRITER] ⚠️  Failed to update read characteristic: {}".format(e))

    def get_transfer_status(self):
        """Return current transfer status"""
        return {
            "complete": self.transfer_complete,
            "error": self.transfer_error,
            "buffer_size": len(self._receive_buffer)
        }