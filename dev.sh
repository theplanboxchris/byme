#!/bin/bash
# dev.sh - Automates MicroPython development workflow with Docker

# Set the ESP32 device path (adjust for your system)
ESP32_DEVICE="/dev/ttyACM0"

# Build the Docker container
echo "Building Docker container..."
docker-compose build micropython-dev

# Start the container in the background
echo "Starting Docker container..."
docker-compose up -d

# Copy MicroPython scripts to the ESP32
echo "Copying scripts to ESP32..."
docker-compose run --rm micropython-dev mpremote connect $ESP32_DEVICE cp main.py :main.py
docker-compose run --rm micropython-dev mpremote connect $ESP32_DEVICE cp ble_proximity.py :ble_proximity.py

# Run the main script on the ESP32
echo "Running main.py on ESP32..."
docker-compose run --rm micropython-dev mpremote connect $ESP32_DEVICE run main.py

echo "Done."
