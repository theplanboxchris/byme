# ble_defs.py - BLE Configuration and Constants
from micropython import const
import bluetooth

# Service and Characteristic UUIDs for keyword transfer
SERVICE_UUID = bluetooth.UUID("a07498ca-ad5b-474e-940d-16f1fbe7e8cd")
KEYWORDS_WRITE_UUID = bluetooth.UUID("b07498ca-ad5b-474e-940d-16f1fbe7e8cd")
KEYWORDS_READ_UUID = bluetooth.UUID("c07498ca-ad5b-474e-940d-16f1fbe7e8cd")

# Device naming
DEVICE_NAME_PREFIX = "NIMI_DEV_"

# GATT flags (from MicroPython BLE API)
FLAG_READ = const(0x0002)
FLAG_WRITE = const(0x0008)
FLAG_WRITE_NO_RESPONSE = const(0x0004)
FLAG_NOTIFY = const(0x0010)

# IRQ event constants
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