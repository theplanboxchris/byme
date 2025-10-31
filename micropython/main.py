import bluetooth, time, os
from ble_utils import BLEPeripheral, device_name, load_keywords

try:
    keywords = load_keywords()
    if keywords:

        ble = bluetooth.BLE()
        ble.active(True)
        device_name = device_name(ble)
        device = BLEPeripheral(ble, name=device_name, keywords=keywords)
        device.advertise()
        device.start_scan()

        while True:
            time.sleep_ms(100)  # Your main loop
    else:
        print("No keywords found in keywords.json.")

except Exception as e:
    print("Error loading keywords.json:", e)
    # Optionally, exit or skip further execution