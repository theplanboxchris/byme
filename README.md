# Keyword Management System & ESP32-C3 P2P BLE Device

A complete peer-to-peer BLE keyword matching system with:
- **Backend API**: FastAPI-based keyword management server
- **Frontend**: Web interface for keyword management  
- **ESP32-C3 Device**: Arduino-based BLE P2P keyword matcher with NeoPixel feedback

## Project Components

### 🌐 Backend API (`/backend`)
FastAPI server for keyword management with SQLite database

### 🖥️ Frontend (`/frontend`) 
Web interface for keyword selection and device management

### 🔧 ESP32-C3 Device (`/arduino-esp32c3`)
Arduino-based firmware for Adafruit QT Py ESP32-C3:
- BLE peer-to-peer communication
- Real-time keyword matching
- NeoPixel visual feedback
- LittleFS keyword storage

## Quick Start

### Full System (Recommended)
```bash
# Start all services
docker-compose up --build -d

# Start ESP32-C3 development environment
cd arduino-esp32c3
./dev.bat start        # Windows
./dev.sh start         # Linux/Mac
```

### ESP32-C3 Development Only
```bash
cd arduino-esp32c3

# Start development container
./dev.bat start

# Build firmware
./dev.bat build

# Flash to device (COM3)
./dev.bat flash COM3

# Monitor serial output
./dev.bat monitor COM3
```

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