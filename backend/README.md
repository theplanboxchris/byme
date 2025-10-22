# Keyword Management Backend

FastAPI backend for managing keywords for the BLE proximity alert system.

## Features

- Add keywords with duplicate prevention (case-insensitive)
- List and filter keywords by category or search term
- Export selected keywords as JSON for ESP32 devices
- SQLite database with automatic schema creation

## API Endpoints

### GET /
- Health check endpoint

### POST /keywords
- Add a new keyword
- Body: `{"word": "sailing", "category": "maritime"}`
- Returns: Keyword object with ID and timestamp
- Error 400: If keyword already exists

### GET /keywords
- List all keywords with optional filtering
- Query params:
  - `category`: Filter by category (partial match)
  - `search`: Search keyword text (partial match)

### GET /categories
- Get list of all unique categories

### POST /keywords/export
- Export selected keywords for ESP32
- Body: `[1, 2, 3, 4]` (list of keyword IDs)
- Returns: `{"keywords": ["sailing", "diving", "storm"]}`

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Usage

Server runs on http://localhost:8000
API documentation available at http://localhost:8000/docs

## Database

SQLite database `keywords.db` is created automatically on first run.

Schema:
- id (primary key)
- word (unique, indexed)
- category (indexed)
- created_at (timestamp)