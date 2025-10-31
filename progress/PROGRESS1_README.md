
## 23/10/25

- Reviewed front end code that allows the keywords file to be updated
- Edited code to work with frontend
- TO DO - create JSON files of the required structure and save to back end
- Realised a few [robpems with the architecture and need to reconsider. The client and the peer code needed to be integrated]

## 22/10/25

Keyword matches achieved!
neopixel flashing if matches
no inbuiltcapacity to make sounds or buzz 



## 22/10/25
Created a simplified single file main.py based version that successfully finds another NIMI device and extracts its name from its advertising payload.
**We do not create a connection in this implementation. This is because connections add a lot of complexity.**

This example proves the concept and is easier to test and follow:
- An advertising payload is created which contains numbers and a device name. We call ble.gap_advertise()
- We call ble.gap_scan() to start scanning which passes all notifications to a BLE IRQ handler (callback function) we define ourselves: bt_irq()
- bt_irq() responds to a connection notification by checking the name. If it includes '_NIMI' we are interested and explore, otherwise we ignore
- we have implemented a simple ignore_list. NIMIs are added with their timestamp.  We ignore recent additions, and process any new ones or ones that have an old entry in that list

This is a basis for adding more developed features:
- keyword matching i a good objective for today




## 22/10/25

- some success in the _2.py files (see archive) in scanning for nearby BLE and matching on name
- realisation that connection may not be necessary
- advertising can include payloads, add the keywords to that payload avoids need to connect
- if using a 5 digit number '0123' instead of the keyword, we can have 4 entries in 20 bytes (look up the ayload limits)
- device advertises with keywords; scanner reads, checks ignore list, if missing adds device to ignore list (timestamped) and alerts if a match;if on ignore list do nothing;
- archived previous project code as _2 which had taken a few days to learn concepts - it was overly complicated
Tasks:
- learn how to scan/advertise
- learn how to read an advertising payload for keywords
- how to add to an ignore list


## 1. Using Claude
- Initial progress with Copilot was good and Claude seems the better solution
- Co pilot ($10 USD pm) exhausted the free claude API tier (Pro tier $30 USD pm)
- Found anthropic console allows API generation and credits (https://console.anthropic.com/) login with google, use ladyerin42
- Bought $5 for testing
- See LESSON4_USING_CLAUDE_README.md
- Succesfully integrated into VS code with ability to edit files/folders etc
- Learnt to use with moderation, try to do what you can yourself (executing commands in terminal) and use claude to generate code fragments that you dont know how to do yourself
- Claude is a good way to get code quickly

## 2. Micropython
- Downloaded the latest .bin and flashed to QT (20/10/25)
- tested and works with mpremote
- tested simple main.py script and executed it on the QT without copying it - faster!

## 3. Architecture
- Understanding that the chip is just running python
- if you can script it, the chip will run it
- a script just gets copied as main
- custom modules needed by the scrip can be included by placing them as py (or the compiled py equivalent m?) in the lib folder
- you dont need thonny. It can be done within VS Code

## Experiments
- 20/10/25 starting to experiment with main.py scripts towards understanding BLE methods
- Used BLE to allow frontend to pair with the esp32 (index.html)
- transferred the keywords file to the device using bluetooth

#### Improvements
- is there a better way to transfer files (the file transfer logic involved a lot of errors in chunking and writing the file in fragments - it was difficult to develop)

## 4. Keywords loaded
- 20/10/25 we have succesfully loaded two esp32 QTpy boards with keywords
- Board 1 : ["dating","jenga"]
- BOard 2 : ["dating","kayak","catamarans","jenga"]
There are clear matches on two keywords

The next step is to:

- have the device work in one of two modes: a continual scanning mode (1) unless we are transferring our keywords (mode 2)
- mode 2 is working
- next is to implement the scanning mode (1)



## 5. Design specification

- Added lesson on Bluetooth BLE concepts at / lessons/LESSON6_BLUETOOTH_README.md
- Added a comprehensive specification for the Bluetooth Device and characteristics at /progress/ble_device_spec.md including **prompt instructions for interacting with AI**


