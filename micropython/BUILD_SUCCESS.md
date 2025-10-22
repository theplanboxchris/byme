# MicroPython Docker Service - Build Successful ✅

The `micropython-dev` Docker service has been successfully built and is ready to use.

## Build Details

- **Image Name**: `byme-micropython-dev:latest`
- **Base Image**: `python:3.12-slim`
- **Image Size**: ~592 MB
- **Build Time**: ~1 minute

## Installed Tools

All required development tools are confirmed installed and working:

✅ **esptool** v5.1.0
- Flash ESP32 devices
- Communicate with ESP32 via serial

✅ **mpremote** v1.26.1
- MicroPython REPL and interactive shell
- File transfer to/from device
- Script execution on device

✅ **adafruit-ampy**
- Alternative file transfer tool
- Device interaction capabilities

## Quick Start

### 1. Start Interactive Shell
```bash
docker-compose run --rm micropython-dev bash
```

### 2. Common Commands (inside container)

#### List connected devices
```bash
mpremote list-device
```

#### Connect to device REPL
```bash
mpremote connect /dev/ttyACM0
```

#### Upload files to device
```bash
mpremote cp main.py :main.py
mpremote cp ble_proximity.py :ble_proximity.py
```

#### Run a script on device
```bash
mpremote run main.py
```

#### Soft reset device
```bash
mpremote reset
```

## Device Connection

### Linux/macOS
- USB devices appear as `/dev/ttyACM0`, `/dev/ttyUSB0`, etc.
- The container is configured to access these automatically

### Windows (with WSL2 Docker Desktop)
- COM ports are mapped as `/dev/ttyS*` inside container
- COM3 → `/dev/ttyS2` (COM ports are 0-indexed)
- Requires proper Docker Desktop USB passthrough configuration

## Next Steps

1. **Mount and edit files** - Project files in `./micropython/` are available at `/micropython/` in the container
2. **Upload to device** - Use `mpremote` to transfer `.py` files to your ESP32-C3
3. **Monitor output** - Use `mpremote` REPL to interact with the device in real-time

## Troubleshooting

### Device not found
```bash
# List available serial devices inside container
docker-compose run --rm micropython-dev ls -la /dev/tty*

# Check specific device
docker-compose run --rm micropython-dev mpremote list-device
```

### Permission issues on Linux
```bash
# Run with elevated privileges (inside container)
docker-compose run --rm --privileged micropython-dev bash
```

### View container logs
```bash
docker logs micropython-dev
```

## Documentation

For detailed usage guide, see [micropython/DOCKER_README.md](./DOCKER_README.md)

---

Ready to develop! 🚀
