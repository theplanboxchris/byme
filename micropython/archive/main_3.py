# main_debug.py - Enhanced with detailed logging
import uasyncio as asyncio
import bluetooth
from ble_defs import DEVICE_NAME, SERVICE_UUID, KEYWORDS_WRITE_UUID, KEYWORDS_READ_UUID, advertising_payload, FLAG_READ, FLAG_WRITE, FLAG_WRITE_NO_RESPONSE, FLAG_NOTIFY, get_device_mac
import ble_defs as defs
from modality_write_debug import KeywordWriter
from modality_peer_debug import PeerScanner
import time
import machine
import neopixel


print("\n" + "="*60)
print("NIMI PEER ALERT - DEBUG VERSION")
print("="*60)

# Hardware config
NEOPIXEL_PIN = 4
NEOPIXEL_COUNT = 1
BUZZER_PIN = 15

print("[INIT] Starting initialization...")
print("[INIT] Device name: {}".format(DEVICE_NAME))
print("[INIT] Service UUID: {}".format(SERVICE_UUID))

# Setup BLE
print("[INIT] Initializing BLE...")
ble = bluetooth.BLE()
ble.active(True)
print("[INIT] ✅ BLE active")

# Get device MAC address for role determination
print("[INIT] Getting device MAC address...")
device_mac = get_device_mac()
if device_mac:
    print("[INIT] ✅ Device MAC: {}".format(device_mac.hex()))
else:
    print("[INIT] ⚠️  Could not get device MAC, using fallback")
    device_mac = b'\x00\x00\x00\x00\x00\x00'

# Instantiate writer (GATT server)
print("[INIT] Creating Writer (GATT server)...")
writer = KeywordWriter(ble, defs)
writer.load_from_storage()
print("[INIT] ✅ Writer created")
print("[INIT] Loaded keywords: {}".format(writer.get_keywords()))

# NeoPixel optional
np = None
try:
    print("[INIT] Initializing NeoPixel...")
    np = neopixel.NeoPixel(machine.Pin(NEOPIXEL_PIN), NEOPIXEL_COUNT)
    np[0] = (0, 255, 0)  # Green = ready
    np.write()
    print("[INIT] ✅ NeoPixel ready")
except Exception as e:
    print("[INIT] ⚠️  NeoPixel not available: {}".format(e))
    np = None

# Buzzer pin optional
buzzer_pin = None
try:
    print("[INIT] Initializing Buzzer...")
    buzzer_pin = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
    print("[INIT] ✅ Buzzer ready")
except Exception as e:
    print("[INIT] ⚠️  Buzzer not available: {}".format(e))
    buzzer_pin = None

# Instantiate peer scanner (central)
print("[INIT] Creating Scanner (GATT client)...")
peer = PeerScanner(ble, defs, writer, device_mac=device_mac, neopixel=np, buzzer_pin=buzzer_pin)
print("[INIT] ✅ Scanner created")

# Advertising payload
print("[INIT] Creating advertising payload...")
payload = advertising_payload(name=DEVICE_NAME)
print("[INIT] Payload size: {} bytes".format(len(payload)))

# Advertise indefinitely
def advertise():
    try:
        print("[ADV] Starting advertisement with name: {}".format(DEVICE_NAME))
        ble.gap_advertise(100_000, adv_data=payload)
        print("[ADV] ✅ Advertising started")
    except Exception as e:
        print("[ADV] ❌ Advertising failed: {}".format(e))
        raise  # Don't silently fall back - let the error propagate so we can debug

advertise()

async def peer_task():
    """
    Scan for peers periodically, unless interrupted by a KEYWORDS_WRITE incoming request.
    """
    scan_count = 0
    while True:
        scan_count += 1
        try:
            if writer.interrupted:
                print("[PEER] ⏸️  Peer scan paused (write in progress)...")
                await asyncio.sleep(1)
                writer.clear_interrupt()
                print("[PEER] ▶️  Peer scan resumed")
                advertise()
                await asyncio.sleep(1)
                continue

            print("\n[PEER] ===== SCAN CYCLE #{} =====".format(scan_count))
            print("[PEER] Starting scan (3000ms)...")
            peer.start_scan(scan_ms=3000)

            print("[PEER] Waiting for scan to complete...")
            await asyncio.sleep(4)

            print("[PEER] Scan cycle complete")
            await asyncio.sleep(1)

        except Exception as e:
            print("[PEER] ❌ Error in peer task: {}".format(e))
            await asyncio.sleep(2)


async def keep_alive_task():
    """Re-advertise periodically to ensure advertising continues"""
    keep_alive_count = 0
    while True:
        keep_alive_count += 1
        try:
            print("[KEEPALIVE] Cycle #{} - Re-advertising...".format(keep_alive_count))
            advertise()
            await asyncio.sleep(20)
        except Exception as e:
            print("[KEEPALIVE] ❌ Error: {}".format(e))
            await asyncio.sleep(5)


async def main_loop():
    print("\n[MAIN] 🚀 Starting main event loop...")
    print("[MAIN] Running peer_task and keep_alive_task in parallel...")
    await asyncio.gather(peer_task(), keep_alive_task())


print("\n[MAIN] ✅ Initialization complete!")
print("[MAIN] Entering async event loop...")
print("="*60)
print("\n")

# Run
try:
    asyncio.run(main_loop())
finally:
    print("\n[MAIN] ❌ Main loop exited unexpectedly!")
    asyncio.new_event_loop()
