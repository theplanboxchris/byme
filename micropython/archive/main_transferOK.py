"""
ESP32-C3 BLE File Receiver - ROBUST VERSION
Handles chunk splitting and reliable file transfer
"""

import bluetooth
import machine
import neopixel
import time
import os

# NeoPixel setup on GPIO 2
np = neopixel.NeoPixel(machine.Pin(2), 1)
np[0] = (255, 0, 0)  # Red = waiting
np.write()

# BLE setup
ble = bluetooth.BLE()
ble.active(True)

DEVICE_NAME = "ESP32-BLE-FILE"
SERVICE_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")

class BLEFileReceiver:
    def __init__(self, ble, service_uuid, char_uuid):
        self.ble = ble
        self.service_uuid = service_uuid
        self.char_uuid = char_uuid
        self.buffer = bytearray()
        self.connected = False
        self.write_count = 0

        print("\n[INIT] Starting BLE setup...")

        try:
            # Try to set MTU to 128 bytes to handle larger transfers
            # This must be done BEFORE registering services
            try:
                print("[INIT] Configuring BLE MTU...")
                # Try to use config method if available in this MicroPython version
                import sys
                if hasattr(ble, 'config'):
                    ble.config(mtu=128)
                    print("[INIT] ✅ MTU set to 128 bytes")
                else:
                    print("[INIT] ⚠️  MTU config not available in this MicroPython version")
                    print("[INIT] BLE will use default MTU (usually 23-27 bytes)")
            except Exception as e:
                print(f"[INIT] ⚠️  Could not set MTU: {e}")

            # Register GATT service
            print("[INIT] Registering characteristic...")
            self.char = (
                self.char_uuid,
                bluetooth.FLAG_READ | bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE,
            )

            self.service = (self.service_uuid, (self.char,))
            print("[INIT] Registering service...")
            self.handles = self.ble.gatts_register_services((self.service,))
            self.char_handle = self.handles[0][0]

            print(f"[INIT] ✅ Service registered!")
            print(f"[INIT] Characteristic handle: {self.char_handle}")

            # Set initial value with larger buffer size
            # Allocate 128 bytes to handle larger writes
            self.ble.gatts_write(self.char_handle, bytearray(128))
            print(f"[INIT] Initial characteristic value set (128 bytes)")

            # Attach IRQ handler
            self.ble.irq(self._irq_handler)
            print(f"[INIT] IRQ handler attached")

        except Exception as e:
            print(f"[INIT] ❌ ERROR: {e}")
            import sys
            sys.exit(1)

    def _irq_handler(self, event, data):
        if event == 1:  # Central connected
            conn_handle, addr_type, addr = data
            self.connected = True
            print(f"\n[BLE] ✅ CONNECTION")
            np[0] = (0, 0, 255)  # Blue
            np.write()

        elif event == 2:  # Central disconnected
            conn_handle, addr_type, addr = data
            self.connected = False
            print(f"\n[BLE] ❌ DISCONNECTION")
            print(f"[BLE] Final buffer state:")
            print(f"  - Size: {len(self.buffer)} bytes")
            print(f"  - Write count: {self.write_count}")
            print(f"  - Content: {self.buffer}")

            # Check if EOF is anywhere in buffer
            if b"<EOF>" in self.buffer:
                print(f"[BLE] 🎯 EOF found in buffer, saving...")
                self._save_file()
            else:
                print(f"[BLE] ⚠️  No EOF marker in buffer")

            np[0] = (255, 0, 0)  # Red
            np.write()

        elif event == 3:  # Characteristic written
            self.write_count += 1
            conn_handle, attr_handle = data

            try:
                value = self.ble.gatts_read(attr_handle)

                if value is None or len(value) == 0:
                    print(f"[BLE] ⚠️  Write #{self.write_count}: Empty value")
                    return

                print(f"\n[BLE] 📝 Write #{self.write_count}: {len(value)} bytes received")
                print(f"  Data: {value}")

                # Append to buffer
                self.buffer.extend(value)
                print(f"  Buffer size now: {len(self.buffer)} bytes")

                # Check for EOF ANYWHERE in buffer (not just last 5 bytes)
                if b"<EOF>" in self.buffer:
                    print(f"[BLE] 🎯 EOF marker found in buffer!")
                    eof_pos = self.buffer.index(b"<EOF>")
                    print(f"  EOF position: {eof_pos}")
                    print(f"  Buffer length: {len(self.buffer)}")
                    print(f"  Content up to EOF: {self.buffer[:eof_pos + 5]}")

                    # Save immediately
                    self._save_file()

            except Exception as e:
                print(f"[BLE] ❌ Error in write handler: {e}")

    def _save_file(self):
        """Save buffer to file with robust error handling"""
        try:
            print("\n[FILE] Saving keywords.json...")

            # Check if EOF exists
            if b"<EOF>" not in self.buffer:
                print("[FILE] No EOF marker in buffer, skipping save")
                return

            # Find EOF position
            eof_pos = self.buffer.index(b"<EOF>")
            file_data = self.buffer[:eof_pos]  # Everything before EOF
            file_size = len(file_data)

            print("[FILE] File size: {} bytes".format(file_size))
            print("[FILE] Content: {}".format(file_data))
            try:
                decoded = file_data.decode('utf-8')
                print("[FILE] Decoded: {}".format(decoded))
            except:
                print("[FILE] Could not decode as UTF-8")

            # Write to file
            print("[FILE] Attempting to write {} bytes...".format(file_size))
            with open("keywords.json", "wb") as f:
                bytes_written = f.write(file_data)
                print("[FILE] Write returned: {} bytes".format(bytes_written))

            # Verify file exists by trying to open it
            print("[FILE] Verifying file exists...")
            try:
                # Try to stat the file
                os.stat("keywords.json")
                print("[FILE] File exists!")
            except OSError:
                print("[FILE] File does NOT exist after write!")
                np[0] = (255, 0, 255)  # Magenta
                np.write()
                return

            # Read back to verify
            print("[FILE] Reading file back to verify...")
            with open("keywords.json", "rb") as f:
                verify = f.read()
                print("[FILE] Verified! Read {} bytes".format(len(verify)))
                print("[FILE] Content: {}".format(verify))

                # Check if content matches
                if verify == file_data:
                    print("[FILE] Content matches!")
                else:
                    print("[FILE] Content mismatch!")

            # Success!
            print("[FILE] SUCCESS! File saved")
            self.buffer = self.buffer[eof_pos + 5:]  # Remove <EOF> and earlier from buffer
            self.write_count = 0
            np[0] = (0, 255, 0)  # Green
            np.write()

        except Exception as e:
            print("[FILE] Error: {}".format(e))
            np[0] = (255, 0, 255)  # Magenta
            np.write()

    def start_advertising(self):
        """Start BLE advertising"""
        flags = b'\x02\x01\x06'
        name = DEVICE_NAME.encode()
        name_ad = bytes([len(name) + 1, 0x09]) + name
        ad_data = flags + name_ad

        print(f"\n[ADV] Starting advertisement...")
        print(f"[ADV] Device name: {DEVICE_NAME}")
        print(f"[ADV] Service UUID:         {self.service_uuid}")
        print(f"[ADV] Characteristic UUID:  {self.char_uuid}")

        self.ble.gap_advertise(100, ad_data, connectable=True)
        print(f"[ADV] ✅ Advertising started")

# Create and run
print("\n" + "="*60)
print("BLE FILE RECEIVER - ROBUST VERSION")
print("="*60)

receiver = BLEFileReceiver(ble, SERVICE_UUID, CHAR_UUID)
receiver.start_advertising()

print(f"\n✅ Ready for connections!")
print(f"📍 Look for: {DEVICE_NAME}")
print("="*60 + "\n")

# Main loop
start_time = time.time()
last_status = start_time

while True:
    current_time = time.time()
    elapsed = int(current_time - start_time)

    # Status every 5 seconds
    if int(current_time - last_status) >= 5:
        print(f"[STATUS] {elapsed}s - Connected: {receiver.connected}, Writes: {receiver.write_count}, Buffer: {len(receiver.buffer)} bytes")
        last_status = current_time

    time.sleep(0.5)
