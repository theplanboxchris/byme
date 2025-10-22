# Simple neopixel stub for testing
# This is a minimal implementation to test if we can get neopixel working

import digitalio
import time

class NeoPixel:
    def __init__(self, pin, num_pixels):
        # For now, just create a simple LED on the pin
        self.led = digitalio.DigitalInOut(pin)
        self.led.direction = digitalio.Direction.OUTPUT
        self.num_pixels = num_pixels
        self._pixels = [(0, 0, 0)] * num_pixels
    
    def __setitem__(self, index, color):
        if isinstance(color, (tuple, list)) and len(color) >= 3:
            self._pixels[index] = color
            # Simple brightness mapping - if any color > 0, turn LED on
            brightness = max(color[:3])
            self.led.value = brightness > 0
    
    def __getitem__(self, index):
        return self._pixels[index]