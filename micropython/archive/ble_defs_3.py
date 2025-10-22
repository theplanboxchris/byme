# ble_defs.py
from micropython import const
import bluetooth
import struct
import network

# UUIDs from your spec
SERVICE_UUID = bluetooth.UUID("a07498ca-ad5b-474e-940d-16f1fbe7e8cd")
KEYWORDS_WRITE_UUID = bluetooth.UUID("b07498ca-ad5b-474e-940d-16f1fbe7e8cd")
KEYWORDS_READ_UUID = bluetooth.UUID("c07498ca-ad5b-474e-940d-16f1fbe7e8cd")

DEVICE_NAME = "NIMI_PEER_ALERT"

# Get device MAC address for role determination
def get_device_mac():
    """Returns device MAC address as bytes for comparison"""
    try:
        mac_tuple = network.WLAN().config('mac')
        return bytes(mac_tuple)
    except Exception as e:
        print("[INIT] ⚠️  Failed to get MAC address: {}".format(e))
        return None

# GATT flags (from MicroPython examples)
FLAG_READ = const(0x0002)
FLAG_WRITE = const(0x0008)
FLAG_WRITE_NO_RESPONSE = const(0x0004)
FLAG_NOTIFY = const(0x0010)

# IRQ constants (match MicroPython examples)
IRQ_CENTRAL_CONNECT = const(1)
IRQ_CENTRAL_DISCONNECT = const(2)
IRQ_GATTS_WRITE = const(3)
IRQ_SCAN_RESULT = const(5)
IRQ_SCAN_COMPLETE = const(6)
IRQ_PERIPHERAL_CONNECT = const(7)
IRQ_PERIPHERAL_DISCONNECT = const(8)
IRQ_GATTC_READ_RESULT = const(9)
IRQ_GATTC_READ_DONE = const(10)
IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
IRQ_GATTC_SERVICE_RESULT = const(13)
IRQ_GATTC_SERVICE_DONE = const(14) 
IRQ_MTU_EXCHANGED = const(21)

# Advertising payload helper - simplified to include only Flags and Name
def advertising_payload(name=None):
    payload = bytearray()

    # Flags (0x01) - standard BLE requirement
    payload += struct.pack("BB", 2, 0x01) + b'\x06'
    print("[ADV] [DEBUG] Flags added (0x01): 2 bytes")

    # Complete Local Name (0x09) - REQUIRED for peer discovery by name
    if name:
        name_bytes = name.encode('utf-8')
        payload += struct.pack("BB", len(name_bytes) + 1, 0x09) + name_bytes
        print("[ADV] [DEBUG] Name added (0x09): '{}' ({} bytes + 2 header)".format(name, len(name_bytes)))

    print("[ADV] [DEBUG] Final payload hex: {}".format(payload.hex()))
    print("[ADV] [DEBUG] Final payload size: {} bytes".format(len(payload)))
    return payload
