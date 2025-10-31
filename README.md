# BLE Keyword Transfer System

## Introduction

This project enables robust transfer and matching of keyword data between devices using Bluetooth Low Energy (BLE). It consists of a FastAPI backend, a React frontend, and MicroPython-based BLE peripherals. The system allows users to select keywords, transfer them to a device, and detect nearby devices with matching keywords using BLE advertising and scan responses.

## System Overview

- **Backend (FastAPI):** Manages group, category, and keyword data. Exposes APIs for keyword selection and hash generation. Persists selected keywords in a SQLite database.
- **Frontend (React):** Provides a user interface for selecting keywords. Uses Web Bluetooth API to transfer selected keywords to BLE devices. Sends keywords as a JSON dictionary, chunked and terminated with `<EOF>`.
- **MicroPython BLE Peripheral:** Receives keywords as a JSON dictionary via BLE GATT write. Stores keywords locally and updates BLE advertising payload. Advertises device name and keywords as manufacturer-specific data in scan response packets. Scans for nearby devices, decodes manufacturer data, and matches received keywords against its own.

## BLE Data Flow

- **Advertising Packet:** Contains device name (`NIMI_DEV_xxxx`) and optional service UUIDs.
- **Scan Response Packet:** Contains manufacturer-specific data (packed keyword indexes as 4-byte little-endian integers).
- **Keyword Transfer:** Frontend sends selected keywords to the device, which updates its advertising payload.

## Keyword Matching Logic

- Each device maintains a dictionary of keywords (`{ "1432244": "Keyword1", ... }`).
- When scanning, devices decode manufacturer data from scan responses into a list of integers.
- Devices compare received keyword indexes against their own and report matches.

## Usage Notes

- Devices must scan with `active=True` to receive scan responses.
- Manufacturer data is limited in size; only a subset of keywords may be advertised.
- The ignore logic prevents repeated processing of the same device within a short interval.

## Extensibility

- Easily add new keyword categories or device features.
- Can be adapted for other BLE data transfer scenarios.
# Keyword Management System & ESP32-C3 P2P BLE Device

A complete peer-to-peer BLE keyword matching system with:
- **Backend API**: FastAPI-based keyword management server
- **Frontend**: Web interface for keyword management  
- **ESP32-C3 Device**: Arduino-based BLE P2P keyword matcher with NeoPixel feedback

## Project Components

### 🌐 Backend API (`/backend`)
FastAPI server for keyword management with SQLite database

### 🖥️ Frontend (`/frontend-react`) 
Web interface for keyword selection and device management

### 🔧 ESP32-C3 Device (`/micropython`)
micropython-based firmware for Adafruit QT Py ESP32-C3:
- BLE peer-to-peer communication
- Real-time keyword matching
- NeoPixel visual feedback
- LittleFS keyword storage

## Quick Start

### Full System (Recommended)
```bash
# Start all services
docker-compose up --build -d

# Start frontend-react development environment
cd frontend-react
npm run dev       # Windows

```

### Powershell scripts
```bash
# copy specified files to COM3/COM5 for development
micropython\upload_esp32.ps1

# run main.py on either device
mpremote connect COM3 run micropython/main.py
mpremote connect COM5 run micropython/main.py

# copy individual files
mpremote connect COM3 cp micropython/main.py :main.py
mpremote connect COM3 cp micropython/ble_utils.py :ble_utils.py
mpremote connect COM3 cp keywords.json :keywords.json

# Delete a file
mpremote connect COM3 fs rm main.py
mpremote connect COM5 fs rm keywords.json
mpremote connect COM3 fs rm ble_utils.py

# list all files
mpremote connect COM3 fs ls

# read file
mpremote connect COM5 fs cat keywords.json
mpremote connect COM3 fs cat keywords.json

# run a python script line
mpremote connect auto repl
```

## REVIEW THIS ADVICE!
### Option 1: Docker (Recommended)

```bash
# Run the setup script
./setup.sh

# Or manually:
docker-compose up --build -d
```

### Option 2: Local Development

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run the server
python main.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/keywords` | Add new keyword |
| GET | `/keywords` | List/filter keywords |
| GET | `/categories` | Get all categories |
| POST | `/keywords/export` | Export selected keywords |

## Usage Examples

### Add Keywords
```bash
curl -X POST "http://localhost:8000/keywords" \
  -H "Content-Type: application/json" \
  -d '{"word": "sailing", "category": "maritime"}'
```

### List Keywords
```bash
# All keywords
curl "http://localhost:8000/keywords"

# Filter by category
curl "http://localhost:8000/keywords?category=maritime"

# Search keywords
curl "http://localhost:8000/keywords?search=sail"
```

### Export for ESP32
```bash
curl -X POST "http://localhost:8000/keywords/export" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3, 4]'
```

## Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── dev-requirements.txt # Development dependencies
│   ├── test_api.py         # API test script
│   └── Dockerfile          # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── setup.sh               # Quick setup script
└── README.md              # This file
```

## Development

### Testing
```bash
# Install dev dependencies
pip install -r dev-requirements.txt

# Run tests
python test_api.py
```

### API Documentation
When running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database

- **Type**: SQLite
- **Location**: `./backend/data/keywords.db` (Docker) or `./keywords.db` (local)
- **Schema**: Auto-created on first run

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `./data/keywords.db` | SQLite database file path |

## Next Steps

- [ ] Create React frontend for keyword selection
- [ ] Add user authentication
- [ ] Implement keyword categories management
- [ ] Add bulk keyword import/export
- [ ] Create mobile app for ESP32 device management