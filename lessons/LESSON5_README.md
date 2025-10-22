## 1. How to make Windows assign a fixed COM port

You can manually reserve a COM port for a device:

1. Open Device Manager.
2. Find your ESP32 under Ports (COM & LPT).

Example: USB Serial Device (COM5).
3. Right-click → Properties → Port Settings → Advanced…
4. Look for COM Port Number.
5. Change it to a fixed number that is free (e.g., COM3).
6. Click OK, then Close.

Windows now remembers this COM port for this particular device. Plugging this same ESP32 in the future will always get COM3.

# Standard commands (directed at COM3)

-# erase flash
esptool --port COM3 erase_flash
-# copy latest micropython .bin
esptool --port COM3 write_flash -z 0x0 micropython/firmware_micropython_latest.bin

-# copy main.py
mpremote connect COM3 cp micropython/main.py :main.py
-# run main.py locally
mpremote connect COM3 run micropython/main.py

-# list all files
mpremote connect COM3 fs ls

-# read file
mpremote connect COM3 fs cat keywords.json