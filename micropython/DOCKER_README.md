# MicroPython Development Container

This Docker service provides a containerized development environment for MicroPython development on the ESP32-C3 device.

## Included Tools

- **esptool** - Flashing and communicating with ESP32 devices
- **mpremote** - MicroPython REPL and file management
- **adafruit-ampy** - File transfer and code execution on MicroPython devices

## Building the Service

```bash
docker-compose build micropython-dev
```

## Usage

### Interactive Shell

Start an interactive bash shell in the container:

```bash
docker-compose run --rm micropython-dev bash
```

### Running mpremote Commands

Once inside the container, you can use mpremote to interact with your ESP32:

```bash
# Connect to device and open REPL
mpremote connect /dev/ttyACM0

# List connected devices
mpremote list-device

# Run a file on the device
mpremote run main.py

# Copy files to device
mpremote cp main.py :main.py
mpremote cp ble_proximity.py :ble_proximity.py

# Soft reset the device
mpremote reset
```

### Running esptool Commands

Flash firmware or interact with the ESP32:

```bash
# List connected devices
esptool.py --port /dev/ttyACM0 chip_id

# Flash firmware (if needed)
esptool.py --port /dev/ttyACM0 --baud 460800 write_flash -z 0x0 esp32c3-20231226-v1.21.0.bin
```

### Running One-Off Commands

Execute commands without entering the shell:

```bash
# Run a single mpremote command
docker-compose run --rm micropython-dev mpremote list-device

# Run a single esptool command
docker-compose run --rm micropython-dev esptool.py --port /dev/ttyACM0 chip_id
```

## Serial Device Configuration

### Linux/macOS

The container is configured to access `/dev/ttyACM*` and `/dev/ttyUSB*` devices by default. Your ESP32 should appear as one of these.

### Windows (Docker Desktop with WSL2)

Windows COM ports need special handling. To use COM3 on Windows:

1. Uncomment the Windows device mapping in `docker-compose.yml`:
   ```yaml
   devices:
     - /dev/ttyS0:/dev/ttyS0
     - /dev/ttyS3:/dev/ttyS3
   ```

2. Comment out the Linux device mappings

3. Use `/dev/ttyS3` inside the container to access `COM3` on the host

**Note**: COM port mapping is complex in Docker on Windows. For the most reliable setup, consider:
- Using WSL2 + Docker Desktop with proper device passthrough
- Mounting USB devices through Docker Desktop settings
- Running esptool/mpremote directly on the host (recommended for Windows)

## Troubleshooting

### Device Not Found

If you get "device not found" errors:

1. Check if device is connected:
   ```bash
   docker-compose run --rm micropython-dev ls -la /dev/tty*
   ```

2. Verify the correct device path (usually `/dev/ttyACM0` on Linux)

3. Check device permissions:
   ```bash
   docker-compose run --rm micropython-dev --privileged bash
   # Then try mpremote commands
   ```

### Permission Denied

If you get permission errors on Linux:

1. Add your user to the dialout group:
   ```bash
   sudo usermod -a -G dialout $USER
   ```

2. Or uncomment `privileged: true` in docker-compose.yml (less secure)

### Python Path Issues

Make sure the container can find `ble_proximity.py`:

```bash
docker-compose run --rm micropython-dev ls -la /micropython/
```

## Mounting Custom Scripts

To run custom scripts inside the container, place them in the `micropython/` directory. They'll be available at `/micropython/` inside the container.

## Next Steps

1. Copy your MicroPython scripts to the `micropython/` directory
2. Use `mpremote` to transfer files to the device
3. Use the interactive shell for development and testing

For more information:
- [mpremote documentation](https://docs.micropython.org/en/latest/reference/mpremote.html)
- [esptool documentation](https://github.com/espressif/esptool)
