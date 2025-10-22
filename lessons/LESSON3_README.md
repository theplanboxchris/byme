# 🛠 Developing and Debugging MicroPython on ESP32 in VS Code

Now that MicroPython is installed on your ESP32, you can write `main.py` scripts that run automatically. To develop efficiently:

---

## 1. Organize Your Project
```
project_root/
│
├─ micropython/
│   └─ main.py       # Your ESP32 program
├─ terminal_setup/
│   └─ requirements.txt  # For mpremote, esptool, etc.
└─ .vscode/
    └─ launch.json   # Debugging configuration (optional)
```

---

## 2. Use a Virtual Environment
Activate the same `.venv` where `mpremote` and `esptool` are installed:
```powershell
.venv\Scripts\activate
```
This ensures VS Code uses the correct Python environment for terminal commands.

---

## 3. Write Code Locally
- Use the **`src/main.py`** file as your main program.
- Use small functions and `print()` statements to check program flow and variable values.
- Example:
```python
# src/main.py
import time

def blink_led(times):
    for i in range(times):
        print(f"Blink {i+1}")
        time.sleep(1)

blink_led(3)
```

---

## 4. Test and Debug Using mpremote
You can test scripts directly **without copying** to the device:
```powershell
mpremote connect COM3 run micropython/main.py
```
- This executes your local file immediately on the ESP32.
- Errors will show in the terminal, so you can fix them before uploading.

---

## 5. Upload and Test on Device
Once your script works locally, copy it to the ESP32:
```powershell
mpremote connect COM3 fs cp micropython/main.py :main.py
```
- Reboot the ESP32 (`mpremote connect COM5 reset`) to run `main.py` automatically.
- Use the REPL for interactive debugging:
```powershell
mpremote connect COM3 repl
```

---

## 6. Debugging Tips
1. **Use print statements** liberally to trace logic and variable values.
2. **Break your code into small functions** for easier testing.
3. **Test locally with `mpremote run`** before overwriting `main.py` on the device.
4. **Catch exceptions** to prevent the board from halting unexpectedly:
```python
try:
    # risky code
except Exception as e:
    print("Error:", e)
```
5. **Monitor the REPL** during execution for real-time feedback.

---

## 7. Optional: VS Code Extensions
- **Python** extension (Microsoft) → syntax highlighting, linting.
- **Pymakr** or **PyMakr for MicroPython** → direct REPL and file transfer (alternative to `mpremote`).

---

✅ **Summary**
- Write code locally, test with `mpremote run`, then upload to ESP32.
- Use `print()`, small functions, and exception handling to debug efficiently.
- Keep your virtual environment active and organized for consistent terminal tools.
