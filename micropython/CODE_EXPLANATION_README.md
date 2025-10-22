# Simple Explanation of Your MicroPython BLE Files

Think of BLE (Bluetooth Low Energy) like a walkie-talkie system between
devices. Your ESP32 is running a system that can both broadcast messages
and listen to other devices.

## The 4 Files Explained

### 1. `ble_defs.py` - The "Instruction Manual"

This file defines all the constants and settings:

-   **UUIDs (unique identifiers)** - Like phone numbers for different
    services\
-   **FLAG_READ, FLAG_WRITE** - Permissions (can you read data? can you
    write data?)\
-   **Device name** - `"NIMI_PEER_ALERT"` - what your device is called\
-   **IRQ events** - Numbers that represent different "things happening"
    (connection, disconnect, data received, etc.)

Think of it as a rulebook everyone follows.

------------------------------------------------------------------------

### 2. `modality_write.py` - The "Receiver" (GATT Server)

This creates a listening post on your ESP32 that other devices can write
to.

**What it does:** - Waits for data from phones/browsers using Web
Bluetooth\
- Receives keywords (like `{"keywords":["dating", "jenga"]}`)\
- Saves them to a file (`keywords.json`)\
- Tells listening devices "Hey, I got new keywords!" using
notifications\
- Sets an interrupt flag to pause scanning temporarily

**Real-world analogy:** Like a letter box on your house. People can put
letters in, and you save them.

------------------------------------------------------------------------

### 3. `modality_peer.py` - The "Scanner" (GATT Client)

This is your device searching for other nearby devices.

**What it does:** - Scans the air looking for devices called
`"NIMI_PEER_ALERT"`\
- Connects to found devices\
- Reads their keywords\
- Compares your keywords with theirs\
- If they match - trigger an ALERT (blink LED, beep buzzer)

**Real-world analogy:** Like going door-to-door, asking "What are your
favorite keywords?" then comparing to your list.

------------------------------------------------------------------------

### 4. `main.py` - The "Orchestra Conductor"

This coordinates everything.

**What it does:** - Starts BLE (turns on the radio)\
- Loads the Writer (starts listening for incoming keywords)\
- Loads the Scanner (starts looking for nearby devices)\
- Runs two tasks in parallel:\
- `peer_task()` - Repeatedly scans for nearby devices\
- `keep_alive_task()` - Re-advertises itself every 20 seconds so others
can find it

------------------------------------------------------------------------

## How It All Works Together (The Story)

1.  Your ESP32 advertises itself: "Hi, I'm NIMI_PEER_ALERT! I'm
    listening!"\
2.  A phone connects and sends keywords: `"I have ['pizza', 'tacos']"`\
3.  Your ESP32 receives and saves them: Stores to `keywords.json`\
4.  Your ESP32 pauses scanning briefly (the interrupt)\
5.  Your ESP32 starts scanning: "Who else is NIMI_PEER_ALERT?"\
6.  It finds another device and asks "What are YOUR keywords?"\
7.  If keywords match: 🚨 **ALERT!** (LED blinks red, buzzer beeps)\
8.  Goes back to listening for new keywords or scanning

------------------------------------------------------------------------

## Key Concepts

  Term              Meaning
  ----------------- --------------------------------------------------
  **GATT Server**   Listens for data (like a phone's inbox)
  **GATT Client**   Connects and reads data (like a phone's caller)
  **Scan**          Search for nearby devices
  **Connect**       Establish a temporary link with a device
  **UUID**          A unique ID number (like a house address)
  **Notify**        Send an unsolicited message to connected devices
  **IRQ**           An interrupt - "something happened!"

------------------------------------------------------------------------

## Simple Version

Your ESP32 is like a two-way radio station that:\
📻 **Broadcasts:** "I'm here, listening for keywords!"\
📥 **Receives:** Keywords from phones/browsers\
📡 **Searches:** For other radio stations with same name\
🚨 **Alerts:** When keywords match
