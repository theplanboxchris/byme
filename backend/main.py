from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional
import datetime

# Database setup
import os
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/keywords.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class KeywordDB(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=func.now())

# Pydantic Models
class KeywordCreate(BaseModel):
    word: str
    category: str

class KeywordResponse(BaseModel):
    id: int
    word: str
    category: str
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True

class KeywordExport(BaseModel):
    keywords: List[str]

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="Keyword Management API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoints
@app.get("/")
def read_root():
    return {"message": "Keyword Management API", "version": "1.0.0"}

@app.post("/keywords", response_model=KeywordResponse)
def add_keyword(keyword: KeywordCreate, db: Session = Depends(get_db)):
    """Add a new keyword with duplicate prevention"""
    # Check for duplicates (case-insensitive)
    existing = db.query(KeywordDB).filter(
        func.lower(KeywordDB.word) == keyword.word.lower()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Keyword '{keyword.word}' already exists"
        )
    
    # Create new keyword
    db_keyword = KeywordDB(
        word=keyword.word.strip(),
        category=keyword.category.strip()
    )
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    
    return db_keyword

@app.get("/keywords", response_model=List[KeywordResponse])
def get_keywords(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search keywords"),
    db: Session = Depends(get_db)
):
    """List keywords with optional filtering"""
    query = db.query(KeywordDB)
    
    if category:
        query = query.filter(KeywordDB.category.ilike(f"%{category}%"))
    
    if search:
        query = query.filter(KeywordDB.word.ilike(f"%{search}%"))
    
    return query.order_by(KeywordDB.category, KeywordDB.word).all()

@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get all unique categories"""
    categories = db.query(KeywordDB.category).distinct().all()
    return {"categories": [cat[0] for cat in categories]}

@app.post("/keywords/export", response_model=KeywordExport)
def export_keywords(keyword_ids: List[int], db: Session = Depends(get_db)):
    """Export selected keywords as JSON for ESP32 device"""
    keywords = db.query(KeywordDB).filter(KeywordDB.id.in_(keyword_ids)).all()
    
    if not keywords:
        raise HTTPException(status_code=404, detail="No keywords found")
    
    return KeywordExport(keywords=[kw.word for kw in keywords])

# ESP32-C3 Communication Endpoints
@app.get("/esp32/status")
def get_esp32_status():
    """Check ESP32-C3 connection status"""
    try:
        import serial
        import serial.tools.list_ports
        
        # Find ESP32-C3 on COM ports
        esp32_port = None
        for port in serial.tools.list_ports.comports():
            if 'COM3' in port.device:  # ESP32-C3 QT Py
                esp32_port = port.device
                break
        
        if esp32_port:
            return {
                "status": "connected",
                "port": esp32_port,
                "device": "ESP32-C3"
            }
        else:
            return {
                "status": "disconnected",
                "port": None,
                "device": "ESP32-C3"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "device": "ESP32-C3"
        }

@app.post("/esp32/upload-keywords")
def upload_keywords_to_esp32(keyword_ids: List[int], db: Session = Depends(get_db)):
    """Upload keywords.json to ESP32-C3 using cp_to_device.py"""
    try:
        import subprocess
        import tempfile
        import os
        import json
        
        # Get keywords from database
        keywords = db.query(KeywordDB).filter(KeywordDB.id.in_(keyword_ids)).all()
        
        if not keywords:
            raise HTTPException(status_code=404, detail="No keywords found")
        
        # Create keywords.json
        keywords_data = {
            "keywords": [kw.word for kw in keywords]
        }
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(keywords_data, f)
            temp_file = f.name
        
        try:
            # Use cp_to_device.py to upload (assumes it's in parent directory)
            result = subprocess.run([
                'python', '../cp_to_device.py', temp_file, 'keywords.json'
            ], capture_output=True, text=True, timeout=30, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": f"Uploaded {len(keywords)} keywords to device",
                    "keywords": [kw.word for kw in keywords],
                    "output": result.stdout
                }
            else:
                return {
                    "status": "error",
                    "message": f"Upload failed: {result.stderr}"
                }
        finally:
            # Clean up temp file
            os.unlink(temp_file)
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Upload error: {str(e)}"
        }

@app.get("/esp32/serial")
def get_esp32_serial():
    """Get recent serial output from ESP32-C3"""
    try:
        import serial
        import time
        
        ser = serial.Serial('COM3', 115200, timeout=1)
        time.sleep(0.1)
        
        lines = []
        for _ in range(20):  # Read up to 20 lines
            line = ser.readline()
            if line:
                lines.append(line.decode('utf-8', errors='ignore').strip())
            else:
                break
        
        ser.close()
        
        return {
            "status": "success",
            "output": lines
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)