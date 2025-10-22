# Bluetooth Low Energy (BLE) Lessons

## Lesson 1: Understanding Services & Characteristics

### The Restaurant Analogy

Think of a BLE device like a **restaurant**:

- **The Device** = The Restaurant Building
- **Services** = Different Sections (Bar, Dining Room, Takeout Counter)
- **Characteristics** = Individual Menu Items at each section

Each service groups related functionality, and characteristics are the actual data points you can interact with.

### Real Structure

**BLE Device** (ESP32)
```
├── Service: Heart Rate Monitor (UUID: 0x180D)
│   ├── Characteristic: Heart Rate Measurement (UUID: 0x2A37)
│   │   └── Properties: READ, NOTIFY
│   └── Characteristic: Body Sensor Location (UUID: 0x2A38)
│       └── Properties: READ
│
├── Service: Battery Service (UUID: 0x180F)
│   └── Characteristic: Battery Level (UUID: 0x2A19)
│       └── Properties: READ, NOTIFY
│
└── Service: Custom File Transfer (UUID: 12345678-1234-5678-1234-56789abcdef0)
    ├── Characteristic: File Data (UUID: 12345678-1234-5678-1234-56789abcdef1)
    │   └── Properties: WRITE
    └── Characteristic: File Control (UUID: 12345678-1234-5678-1234-56789abcdef2)
        └── Properties: READ, WRITE
```

### Key Concepts

**UUID (Universally Unique Identifier)**
- 128-bit number that identifies services and characteristics
- Standard services use 16-bit short UUIDs (e.g., `0x180D` for Heart Rate)
- Custom services use full 128-bit UUIDs
- Example: `12345678-1234-5678-1234-56789abcdef0`

**Properties (What You Can Do)**
- **READ**: Get the current value (like checking a scoreboard)
- **WRITE**: Send data to the device (like ordering food)
- **NOTIFY**: Device pushes updates automatically (like getting notifications)
- **INDICATE**: Like NOTIFY but with acknowledgment
- **WRITE_NO_RESPONSE**: Fast write without waiting for confirmation

---

## Lesson 2: How to Connect to a Service & Characteristic

### Step-by-Step Connection Process

#### **Step 1: Scan for Devices**

Your phone/computer scans for advertising BLE devices:

```
[Scanning...]
Found: "ESP32-Keywords" (Address: AA:BB:CC:DD:EE:FF)
Found: "Fitness Tracker" (Address: 11:22:33:44:55:66)
Found: "Smart Bulb" (Address: 77:88:99:AA:BB:CC)
```

**What's happening:**
- Devices broadcast their name and available services
- You pick the device you want to connect to

#### **Step 2: Connect to Device**

Establish a connection with the chosen device:

```
Connecting to "ESP32-Keywords"...
Connected! 
Connection Handle: 0x0001
```

**What's happening:**
- A persistent connection is established
- The device stops advertising (usually)
- You get a "connection handle" to reference this connection

#### **Step 3: Discover Services**

Ask the device what services it offers:

```
Discovering services...

Service 1: UUID 0x1800 (Generic Access)
Service 2: UUID 0x1801 (Generic Attribute)
Service 3: UUID 12345678-1234-5678-1234-56789abcdef0 (File Transfer)
```

**What's happening:**
- Device lists all available services
- Each service has a UUID
- Standard services (0x1800, 0x1801) are always present

#### **Step 4: Discover Characteristics**

For each service, discover what characteristics it has:

```
Service: File Transfer (12345678-1234-5678-1234-56789abcdef0)
├── Characteristic: File Data
│   UUID: 12345678-1234-5678-1234-56789abcdef1
│   Properties: WRITE
│   Handle: 0x0010
│
└── Characteristic: File Control
    UUID: 12345678-1234-5678-1234-56789abcdef2
    Properties: READ, WRITE
    Handle: 0x0012
```

**What's happening:**
- Each characteristic has a UUID
- Properties tell you what operations are allowed
- Handle is used to reference this characteristic in operations

#### **Step 5: Interact with Characteristics**

Now you can read/write data!

```python
# Read a value
battery_level = read(battery_characteristic_handle)
# Returns: 87 (87% battery)

# Write a value
write(file_control_handle, "START")
# Sends command to device

# Subscribe to notifications
subscribe(heart_rate_handle)
# Device will now push updates automatically
```

### Practical Example: Using nRF Connect App

**On Your Phone:**

1. **Open nRF Connect** (free app for iOS/Android)
2. **Tap SCAN** → See nearby devices
3. **Tap CONNECT** on your ESP32 device
4. **View Services** → Expand to see characteristics
5. **Tap characteristic** → Choose operation:
   - ↓ Icon = READ
   - ↑ Icon = WRITE
   - (( Icon = ENABLE NOTIFICATIONS

---

## Lesson 3: What You Can Do With Characteristics

### Common Use Cases

#### **1. READ - Get Information**

**Example: Reading Temperature**

```python
# On ESP32 (Server)
temp_value = encode_temperature(23.5)  # 23.5°C
ble.gatts_write(temp_characteristic, temp_value)

# On Phone (Client)
temperature = ble.gattc_read(temp_characteristic)
print(f"Temperature: {decode(temperature)}°C")
# Output: Temperature: 23.5°C
```

**Real-world uses:**
- Read sensor data (temperature, humidity, pressure)
- Check device status (battery level, WiFi status)
- Get configuration settings

#### **2. WRITE - Send Commands**

**Example: Sending Keywords File**

```python
# On Phone (Client)
keywords_json = '{"keywords": ["python", "iot", "maker"]}'

# Send START command
ble.gattc_write(control_characteristic, "START")

# Send data in chunks
for chunk in split_into_chunks(keywords_json, 20):
    ble.gattc_write(data_characteristic, chunk)

# Send END command
ble.gattc_write(control_characteristic, "END")

# On ESP32 (Server)
# Receives data, assembles, and saves to file
```

**Real-world uses:**
- Control devices (turn on/off, change settings)
- Send configuration data
- Transfer files or firmware updates
- Send commands (START, STOP, RESET)

#### **3. NOTIFY - Automatic Updates**

**Example: Heart Rate Monitor**

```python
# On Phone (Client)
def heart_rate_callback(data):
    bpm = decode_heart_rate(data)
    print(f"Heart Rate: {bpm} BPM")

# Subscribe to notifications
ble.gattc_subscribe(heart_rate_characteristic, heart_rate_callback)

# On ESP32 (Server) - runs in a loop
while True:
    bpm = read_heart_sensor()
    ble.gatts_notify(heart_rate_characteristic, encode(bpm))
    time.sleep(1)

# Phone automatically receives:
# Heart Rate: 72 BPM
# Heart Rate: 74 BPM
# Heart Rate: 73 BPM
```

**Real-world uses:**
- Streaming sensor data (no need to constantly poll)
- Real-time alerts (motion detected, button pressed)
- Live status updates (download progress, connection status)

### Complete Example: File Transfer Service

```python
# === ESP32 Server Code ===
import bluetooth

# Define service and characteristics
FILE_SERVICE = "12345678-1234-5678-1234-56789abcdef0"
FILE_DATA_CHAR = "12345678-1234-5678-1234-56789abcdef1"      # WRITE
FILE_CONTROL_CHAR = "12345678-1234-5678-1234-56789abcdef2"   # READ, WRITE

ble = bluetooth.BLE()
ble.active(True)

file_buffer = bytearray()

def ble_irq_handler(event, data):
    if event == IRQ_GATTS_WRITE:
        conn_handle, attr_handle = data
        
        if attr_handle == control_handle:
            command = ble.gatts_read(control_handle).decode()
            
            if command == "START":
                file_buffer.clear()
                print("Starting file reception")
                
            elif command == "END":
                print(f"File received: {file_buffer.decode()}")
                save_file(file_buffer)
        
        elif attr_handle == data_handle:
            chunk = ble.gatts_read(data_handle)
            file_buffer.extend(chunk)
            print(f"Received {len(chunk)} bytes")

ble.irq(ble_irq_handler)

# Register services...
# Start advertising...
```

```python
# === Phone/Computer Client Code (Pseudocode) ===

# 1. Connect
device = scan_and_find("ESP32-Keywords")
connect(device)

# 2. Discover
services = discover_services(device)
file_service = services.find(FILE_SERVICE)
characteristics = discover_characteristics(file_service)

control_char = characteristics.find(FILE_CONTROL_CHAR)
data_char = characteristics.find(FILE_DATA_CHAR)

# 3. Transfer file
write(control_char, "START")

file_content = load_file("keywords.json")
for chunk in split_chunks(file_content, 20):  # BLE packets are small
    write(data_char, chunk)
    sleep(0.01)  # Small delay between chunks

write(control_char, "END")

print("File transferred successfully!")
```

### Data Size Limitations

**Important:** BLE characteristics have size limits!

- **MTU (Maximum Transmission Unit)**: Default is 23 bytes
- **Usable payload**: 20 bytes (3 bytes overhead)
- For larger data, split into chunks or negotiate higher MTU

```python
# Sending large data
def send_large_data(characteristic, data, chunk_size=20):
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        write(characteristic, chunk)
        time.sleep(0.01)  # Small delay to avoid overwhelming device
```

---

## Quick Reference Card

| Operation | When to Use | Example |
|-----------|-------------|---------|
| **READ** | Get current value once | Check battery level |
| **WRITE** | Send data/command to device | Turn on LED, send config |
| **NOTIFY** | Get continuous updates | Heart rate monitoring |
| **INDICATE** | Updates with confirmation | Critical alerts |

### Connection Flow Summary

```
1. SCAN → Find devices advertising
2. CONNECT → Establish connection to chosen device
3. DISCOVER SERVICES → Ask "what can you do?"
4. DISCOVER CHARACTERISTICS → Ask "how do I do it?"
5. READ/WRITE/NOTIFY → Actually interact with data
6. DISCONNECT → End session
```

### Practice Exercise

Try this with nRF Connect app and your ESP32:

1. Flash the BLE code to ESP32
2. Open nRF Connect and scan
3. Connect to "ESP32-Keywords"
4. Find the File Transfer service
5. Write "START" to the Control characteristic
6. Write "test data" to the Data characteristic
7. Write "END" to the Control characteristic
8. Check ESP32 output to see if it received the data!

---

**Next Steps:**
- Experiment with different characteristic properties
- Try reading and writing different data types
- Build a simple app that communicates with your ESP32
- Explore standard BLE services (Heart Rate, Battery, etc.)