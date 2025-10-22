BLE device with the following specification:

Device Name: NIMI_PEER_ALERT
Hardware: ESP32 with BLE

Service: KEYWORDS
- Service UUID: a07498ca-ad5b-474e-940d-16f1fbe7e8cd

Characteristics:
1. KEYWORDS_WRITE (UUID: b07498ca-ad5b-474e-940d-16f1fbe7e8cd)
   - Properties: WRITE
   - Purpose: Write keyword list to device
   - Format: JSON string like {"keywords": ["python", "iot"]}

2. KEYWORDS_READ (UUID: c07498ca-ad5b-474e-940d-16f1fbe7e8cd)
   - Properties: READ, NOTIFY
   - Purpose: Read current keywords and get updates
   - Format: JSON string like {"keywords": ["python", "iot"], "count": 2}

The device has two modalities:

- Modality 1 - accepts Keyword Writes to the KEYWORDS_WRITE - these are initiated from a browser and interrupt all other operations of the device;
- Modality 2 - continually scan for nearby devices with the same name ('NIMI_PEER_ALERT') in order to connect, exchange their KEYWORDS_READ characteristic data, disconnect and each peer then performs a comparison between the received keywords and their local KEYWORDS_READ data, alerting by means of a sound and neopixel colour if any matches of keywords are found  

**See 'ble_device_spec.md' for detailed device specification**