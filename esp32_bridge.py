"""
ESP32-C3 Communication Bridge
Runs on the host to bridge between web interface and ESP32-C3
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import tempfile
import os

app = FastAPI(title="ESP32-C3 Bridge", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeUpload(BaseModel):
    code: str

@app.get("/")
def root():
    return {"message": "ESP32-C3 Communication Bridge", "status": "running"}

@app.get("/esp32/status")
def get_esp32_status():
    """Check ESP32-C3 connection status"""
    try:
        import serial.tools.list_ports
        
        # Find ESP32-C3 on COM ports
        esp32_port = None
        for port in serial.tools.list_ports.comports():
            if 'COM3' in port.device:  # Your ESP32-C3 port
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

@app.post("/esp32/upload-code")
def upload_code_to_esp32(upload: CodeUpload):
    """Upload Python code to ESP32-C3 via mpremote"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting code upload - code length: {len(upload.code)} characters")
        
        # Create temporary file with the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(upload.code)
            temp_file = f.name
        
        logger.info(f"Created temp file: {temp_file}")
        
        try:
            # Check if device is available first
            logger.info("Checking device connection...")
            test_result = subprocess.run([
                'mpremote', 'connect', 'COM3', 'exec', 'print("connection test")'
            ], capture_output=True, text=True, timeout=10)
            
            if test_result.returncode != 0:
                logger.error(f"Device connection test failed: {test_result.stderr}")
                return {
                    "status": "error",
                    "message": f"Device connection failed: {test_result.stderr}",
                    "details": {
                        "step": "connection_test",
                        "stdout": test_result.stdout,
                        "stderr": test_result.stderr,
                        "returncode": test_result.returncode
                    }
                }
            
            logger.info("Device connection successful")
            
            # Use mpremote to upload the file
            logger.info("Starting file upload...")
            result = subprocess.run([
                'mpremote', 'connect', 'COM3', 'cp', temp_file, ':code.py'
            ], capture_output=True, text=True, timeout=30)
            
            logger.info(f"Upload result - return code: {result.returncode}")
            logger.info(f"Upload stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"Upload stderr: {result.stderr}")
            
            if result.returncode == 0:
                logger.info("File upload successful, resetting device...")
                
                # Reset the device to run the new code
                reset_result = subprocess.run([
                    'mpremote', 'connect', 'COM3', 'reset'
                ], capture_output=True, timeout=10)
                
                logger.info(f"Reset result - return code: {reset_result.returncode}")
                
                return {
                    "status": "success",
                    "message": "Code uploaded and device restarted",
                    "details": {
                        "upload_stdout": result.stdout,
                        "upload_stderr": result.stderr,
                        "reset_success": reset_result.returncode == 0,
                        "file_size": len(upload.code)
                    }
                }
            else:
                logger.error(f"Upload failed with return code {result.returncode}")
                return {
                    "status": "error",
                    "message": f"Upload failed: {result.stderr or 'Unknown error'}",
                    "details": {
                        "step": "file_upload",
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                        "temp_file": temp_file
                    }
                }
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                logger.info(f"Cleaned up temp file: {temp_file}")
            
    except subprocess.TimeoutExpired as e:
        logger.error(f"Operation timed out: {e}")
        return {
            "status": "error",
            "message": f"Operation timed out: {e}",
            "details": {
                "step": "timeout",
                "timeout_duration": "30 seconds"
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "status": "error",
            "message": f"Upload error: {str(e)}",
            "details": {
                "step": "exception",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
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
    uvicorn.run(app, host="0.0.0.0", port=8002)