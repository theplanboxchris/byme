"""
File Transfer Utility for CircuitPython devices
Because mpremote cp is broken with CircuitPython, this provides a working alternative.

Usage:
    python cp_to_device.py <local_file> <remote_path>
    
Example:
    python cp_to_device.py neopixel.mpy lib/neopixel.mpy
    python cp_to_device.py keywords.json keywords.json
"""

import subprocess
import sys
import os

def transfer_file(local_path, remote_path):
    """Transfer a file to the CircuitPython device using mpremote exec"""
    
    if not os.path.exists(local_path):
        print(f"❌ Error: Local file '{local_path}' not found")
        return False
    
    # Read the file
    with open(local_path, 'rb') as f:
        file_data = f.read()
    
    file_size = len(file_data)
    print(f"Transferring: {local_path} -> {remote_path} ({file_size} bytes)")
    
    # Convert to hex string for safe transfer
    hex_data = file_data.hex()
    
    # Split into chunks (500 chars hex = 250 bytes per chunk)
    chunk_size = 500
    chunks = [hex_data[i:i+chunk_size] for i in range(0, len(hex_data), chunk_size)]
    
    # Create empty file on device
    cmd = f"f = open('{remote_path}', 'wb'); f.close()"
    result = subprocess.run(['mpremote', 'exec', cmd], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error creating file: {result.stderr}")
        return False
    
    # Write chunks with progress indicator
    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks):
        progress = int((i + 1) / total_chunks * 20)
        bar = '#' * progress + '.' * (20 - progress)
        print(f"\r[{bar}] {i+1}/{total_chunks}", end='', flush=True)
        
        cmd = f"f = open('{remote_path}', 'ab'); f.write(bytes.fromhex('{chunk}')); f.close()"
        result = subprocess.run(['mpremote', 'exec', cmd], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"\n❌ Error writing chunk {i+1}: {result.stderr}")
            return False
    
    print()  # New line after progress bar
    
    # Verify file size
    cmd = f"import os; print(os.stat('{remote_path}')[6])"
    result = subprocess.run(['mpremote', 'exec', cmd], capture_output=True, text=True)
    if result.returncode == 0:
        remote_size = int(result.stdout.strip())
        if remote_size == file_size:
            print(f"Transfer successful! ({remote_size} bytes)")
            return True
        else:
            print(f"Size mismatch! Expected {file_size}, got {remote_size}")
            return False
    else:
        print(f"Warning: Could not verify file size")
        return True

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    
    local_file = sys.argv[1]
    remote_file = sys.argv[2]
    
    success = transfer_file(local_file, remote_file)
    sys.exit(0 if success else 1)
