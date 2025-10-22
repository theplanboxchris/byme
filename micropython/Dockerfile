FROM python:3.12-slim

WORKDIR /micropython

# Install system dependencies for USB/serial communication
RUN apt-get update && apt-get install -y \
    libusb-1.0-0 \
    libusb-dev \
    udev \
    gcc \
    git \
    make \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install MicroPython development tools for ESP32
RUN pip install --no-cache-dir \
    esptool>=4.6.0 \
    mpremote>=1.20.0 \
    adafruit-ampy>=1.1.1

# Copy project files
COPY . .

# Set environment variables for serial communication
ENV PYTHONUNBUFFERED=1

# Default to interactive shell
CMD ["/bin/bash"]
