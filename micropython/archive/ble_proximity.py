"""
BLE Dual Mode System for ESP32-C3
Mode 1: Download mode - Accept keywords file via BLE
Mode 2: Scan mode - Scan for nearby devices and match keywords
"""

import bluetooth
import json
import time
import os
from micropython import const

# BLE constants
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)

# Service and Characteristic UUIDs for file transfer
_FILE_TRANSFER_SERVICE_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
_FILE_DATA_CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")
_FILE_CONTROL_CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef2")

# BLE flags
_FLAG_READ = const(0x02)
_FLAG_WRITE = const(0x08)
_FLAG_NOTIFY = const(0x10)


class BLEDualMode:
    """BLE device with download and scan modes"""

    MODE_DOWNLOAD = "download"
    MODE_SCAN = "scan"

    def __init__(self, device_name="ESP32-C3", neopixel=None, button_pin=None):
        """
        Initialize BLE dual mode system
        
        Args:
            device_name: Name to advertise
            neopixel: Optional neopixel object for status indication
            button_pin: Optional button pin to toggle modes
        """
        self.device_name = device_name
        self.neopixel = neopixel
        self.button_pin = button_pin
        self.keywords = []
        self.mode = self.MODE_DOWNLOAD  # Start in download mode
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._ble_irq)
        
        # Download mode variables
        self.connected_client = None
        self.file_buffer = bytearray()
        self.receiving_file = False
        
        # Scan mode variables
        self.scanning = False
        self.nearby_devices = {}
        self.matched_devices = []
        
        # Load existing keywords
        self._load_keywords()
        
        # Start in appropriate mode
        self._enter_mode(self.mode)

    def _load_keywords(self):
        """Load keywords from keywords.json file"""
        try:
            if os.path.exists('keywords.json'):
                with open('keywords.json', 'r') as f:
                    data = json.load(f)
                    self.keywords = data.get('keywords', [])
                print(f"[BLE] Loaded {len(self.keywords)} keywords: {self.keywords}")
                return True
            else:
                print("[BLE] keywords.json not found")
                self.keywords = []
                return False
        except Exception as e:
            print(f"[BLE] Error loading keywords: {e}")
            self.keywords = []
            return False

    def _save_keywords(self, keywords_data):
        """Save keywords to keywords.json file"""
        try:
            with open('keywords.json', 'w') as f:
                json.dump({'keywords': keywords_data}, f)
            self.keywords = keywords_data
            print(f"[BLE] Saved {len(self.keywords)} keywords: {self.keywords}")
            self._set_status_color('green')
            return True
        except Exception as e:
            print(f"[BLE] Error saving keywords: {e}")
            self._set_status_color('red')
            return False

    def _set_status_color(self, color):
        """Set NeoPixel status color"""
        if not self.neopixel:
            return

        try:
            if color == 'purple':
                # Purple = Download mode, waiting for connection
                self.neopixel[0] = (16, 0, 16)
            elif color == 'blue':
                # Blue = Download mode, connected
                self.neopixel[0] = (0, 0, 32)
            elif color == 'green':
                # Green = Keywords loaded successfully
                self.neopixel[0] = (0, 32, 0)
            elif color == 'yellow':
                # Yellow = Scan mode, scanning
                self.neopixel[0] = (32, 32, 0)
            elif color == 'cyan':
                # Cyan = Scan mode, match found
                self.neopixel[0] = (0, 32, 32)
            elif color == 'red':
                # Red = Error or no keywords
                self.neopixel[0] = (32, 0, 0)
            else:
                self.neopixel[0] = (0, 0, 0)

            self.neopixel.write()
        except Exception as e:
            print(f"[BLE] Error setting NeoPixel: {e}")

    def _register_services(self):
        """Register GATT services for download mode"""
        # File data characteristic (write to send file chunks)
        file_data_char = (
            _FILE_DATA_CHAR_UUID,
            _FLAG_WRITE,
        )
        
        # File control characteristic (write commands like "START", "END")
        file_control_char = (
            _FILE_CONTROL_CHAR_UUID,
            _FLAG_WRITE | _FLAG_READ,
        )
        
        # Define service with characteristics
        file_transfer_service = (
            _FILE_TRANSFER_SERVICE_UUID,
            (file_data_char, file_control_char),
        )
        
        # Register services
        ((self.file_data_handle, self.file_control_handle),) = self.ble.gatts_register_services(
            (file_transfer_service,)
        )
        
        print("[BLE] GATT services registered")

    def _start_download_mode(self):
        """Start download mode - advertise as connectable for file transfer"""
        try:
            print("[BLE] Entering DOWNLOAD mode")
            self._set_status_color('purple')
            
            # Register GATT services
            self._register_services()
            
            # Create advertisement
            name = self.device_name.encode('utf-8')
            ad_data = bytes([
                0x02, 0x01, 0x06,  # Flags: General discoverable
                len(name) + 1, 0x09,  # Complete local name
            ]) + name
            
            # Start advertising
            self.ble.gap_advertise(100000, ad_data, connectable=True)
            print("[BLE] Download mode active - waiting for connection")
            
        except Exception as e:
            print(f"[BLE] Error starting download mode: {e}")
            self._set_status_color('red')

    def _start_scan_mode(self):
        """Start scan mode - scan for nearby devices with keywords"""
        try:
            print("[BLE] Entering SCAN mode")
            
            if not self.keywords:
                print("[BLE] No keywords loaded - cannot scan")
                self._set_status_color('red')
                return
            
            print(f"[BLE] Scanning for devices with keywords: {self.keywords}")
            self._set_status_color('yellow')
            
            # Start scanning
            self.scanning = True
            self.ble.gap_scan(0, 30000, 30000)  # Scan indefinitely, 30ms interval/window
            
        except Exception as e:
            print(f"[BLE] Error starting scan mode: {e}")
            self._set_status_color('red')

    def _stop_scan_mode(self):
        """Stop scanning"""
        try:
            if self.scanning:
                self.ble.gap_scan(None)
                self.scanning = False
                print("[BLE] Scanning stopped")
        except Exception as e:
            print(f"[BLE] Error stopping scan: {e}")

    def _parse_advertisement(self, adv_data):
        """Parse advertisement data to extract keywords"""
        keywords = []
        i = 0
        
        try:
            while i < len(adv_data):
                length = adv_data[i]
                if length == 0:
                    break
                    
                ad_type = adv_data[i + 1]
                
                # Manufacturer-specific data (0xFF)
                if ad_type == 0xFF and length > 3:
                    # Extract keywords (skip company ID)
                    keyword_data = adv_data[i + 4:i + 1 + length]
                    keyword_str = keyword_data.decode('utf-8', 'ignore')
                    keywords = keyword_str.split(',')
                    break
                
                i += length + 1
                
        except Exception as e:
            print(f"[BLE] Error parsing advertisement: {e}")
        
        return keywords

    def _check_keyword_match(self, device_keywords):
        """Check if device keywords match our keywords"""
        matches = set(self.keywords) & set(device_keywords)
        return list(matches)

    def _ble_irq(self, event, data):
        """Handle BLE events"""
        try:
            # Download mode events
            if event == _IRQ_CENTRAL_CONNECT:
                conn_handle, addr_type, addr = data
                self.connected_client = conn_handle
                print(f"[BLE] Client connected: {addr}")
                self._set_status_color('blue')
                
            elif event == _IRQ_CENTRAL_DISCONNECT:
                conn_handle, addr_type, addr = data
                self.connected_client = None
                print(f"[BLE] Client disconnected: {addr}")
                self._set_status_color('purple')
                
            elif event == _IRQ_GATTS_WRITE:
                conn_handle, attr_handle = data
                
                if attr_handle == self.file_control_handle:
                    # Control command received
                    command = self.ble.gatts_read(self.file_control_handle).decode('utf-8')
                    print(f"[BLE] Control command: {command}")
                    
                    if command == "START":
                        self.file_buffer = bytearray()
                        self.receiving_file = True
                        print("[BLE] Starting file reception")
                        
                    elif command == "END":
                        self.receiving_file = False
                        # Parse and save keywords
                        try:
                            data = json.loads(self.file_buffer.decode('utf-8'))
                            keywords = data.get('keywords', [])
                            self._save_keywords(keywords)
                            print(f"[BLE] File received and saved: {keywords}")
                        except Exception as e:
                            print(f"[BLE] Error processing file: {e}")
                        
                elif attr_handle == self.file_data_handle:
                    # File data chunk received
                    if self.receiving_file:
                        chunk = self.ble.gatts_read(self.file_data_handle)
                        self.file_buffer.extend(chunk)
                        print(f"[BLE] Received chunk: {len(chunk)} bytes")
            
            # Scan mode events
            elif event == _IRQ_SCAN_RESULT:
                addr_type, addr, adv_type, rssi, adv_data = data
                
                # Convert address to string
                addr_str = ':'.join(['%02x' % b for b in bytes(addr)])
                
                # Parse advertisement for keywords
                device_keywords = self._parse_advertisement(adv_data)
                
                if device_keywords:
                    # Check for matches
                    matches = self._check_keyword_match(device_keywords)
                    
                    if matches:
                        print(f"[BLE] MATCH FOUND! Device: {addr_str}")
                        print(f"      Keywords: {device_keywords}")
                        print(f"      Matches: {matches}")
                        print(f"      RSSI: {rssi}")
                        
                        self.matched_devices.append({
                            'address': addr_str,
                            'keywords': device_keywords,
                            'matches': matches,
                            'rssi': rssi,
                            'timestamp': time.time()
                        })
                        
                        self._set_status_color('cyan')
                    
                    # Store device info
                    self.nearby_devices[addr_str] = {
                        'keywords': device_keywords,
                        'rssi': rssi,
                        'last_seen': time.time()
                    }
            
            elif event == _IRQ_SCAN_DONE:
                if self.scanning:
                    # Restart scan
                    self.ble.gap_scan(0, 30000, 30000)
                    
        except Exception as e:
            print(f"[BLE] IRQ Error: {e}")

    def _enter_mode(self, mode):
        """Switch between modes"""
        # Clean up current mode
        if self.mode == self.MODE_SCAN:
            self._stop_scan_mode()
        elif self.mode == self.MODE_DOWNLOAD:
            self.ble.gap_advertise(None)
        
        # Enter new mode
        self.mode = mode
        
        if mode == self.MODE_DOWNLOAD:
            self._start_download_mode()
        elif mode == self.MODE_SCAN:
            self._start_scan_mode()

    def switch_mode(self):
        """Toggle between download and scan modes"""
        if self.mode == self.MODE_DOWNLOAD:
            self._enter_mode(self.MODE_SCAN)
        else:
            self._enter_mode(self.MODE_DOWNLOAD)
        
        print(f"[BLE] Switched to {self.mode.upper()} mode")

    def get_matches(self):
        """Get list of matched devices"""
        return self.matched_devices

    def clear_matches(self):
        """Clear matched devices list"""
        self.matched_devices = []

    def get_status(self):
        """Get current system status"""
        return {
            'mode': self.mode,
            'device_name': self.device_name,
            'keywords_count': len(self.keywords),
            'keywords': self.keywords,
            'connected': self.connected_client is not None,
            'scanning': self.scanning,
            'nearby_devices': len(self.nearby_devices),
            'matched_devices': len(self.matched_devices)
        }

    def shutdown(self):
        """Gracefully shutdown BLE"""
        try:
            self._stop_scan_mode()
            self.ble.gap_advertise(None)
            self.ble.active(False)
            print("[BLE] Shutdown complete")
        except Exception as e:
            print(f"[BLE] Error during shutdown: {e}")