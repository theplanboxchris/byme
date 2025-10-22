# ⚙️ Programming an ESP32 with MicroPython

## 🧩 How It Works
When you program an ESP32 device using **MicroPython**:
- You write one or more Python files (`.py`).
- The file named **`main.py`** runs automatically every time the device boots.
- Optionally, a **`boot.py`** file runs first to handle setup (like Wi-Fi or configuration).
- Files are stored in the ESP32’s internal filesystem (flash memory).

---

## 🧰 Setting Up the VS Code Terminal for ESP32 Tools

If your VS Code terminal shows an error such as:

```
mpremote : The term 'mpremote' is not recognized
```
or  
```
esptool : The term 'esptool' is not recognized
```

it means the tools aren’t yet installed in your local Python environment.

---

### 📁 Step 1. Create a Dedicated Folder for Terminal Setup

Inside your project, create a new folder (for example):

```
project_root/
│
├─ src/
│   └─ main.py
│
└─ terminal_setup/
    └─ requirements.txt
```

This makes it clear that the tools in this folder are **for configuring your local terminal only**, not for code that runs on the ESP32.

---

### ⚙️ Step 2. Add a `requirements.txt` File

Inside `terminal_setup/requirements.txt`, add:

```
# Tools for setting up the local VS Code terminal
mpremote
esptool
uasyncio
```

---

### 🧩 Step 3. Create and Activate a Virtual Environment

In VS Code’s PowerShell terminal:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

You’ll see `(.venv)` appear at the start of your terminal prompt — this means the environment is active.

---

### 📥 Step 4. Install the Terminal Tools

Run the installer using the path to your setup folder:

```powershell
pip install -r micropython/terminal_setup/requirements.txt
```

---

### ✅ Step 5. Verify Installation

```powershell
mpremote --help
esptool.py --help
```

If you see help text, both tools are installed and ready to use.


After installing `esptool` in your virtual environment, you might see this error:

```
esptool.py : The term 'esptool.py' is not recognized...
```

### 💡 Why This Happens
On Windows, the tool installs a command called **`esptool.exe`**, not `esptool.py`.  
The `.py` version works on Linux/macOS, but Windows uses `.exe` instead.

---

### ✅ Fix Option 1 — Use `esptool` (no `.py`)
In PowerShell, simply run:
```powershell
esptool --help
```
That should work immediately.

---



---

**Summary**
- Keep `terminal_setup/requirements.txt` separate from your source code.  
- Activate `.venv` each time you open the project.  
- Install or update your terminal tools with:
  ```powershell
  pip install -r terminal_setup/requirements.txt
  ```



## 🐳 Method 1: Using Docker to Transfer `main.py`

You can use a Docker container that has tools like `mpremote` or `ampy` preinstalled.

### Example Command
```bash
docker run -it --rm --device=/dev/ttyS2 -v /micropython:/app micropython-env bash
```

**Explanation:**
- `--device=/dev/ttyS2` gives the container access to the ESP32 serial port.  
- `-v /micropython:/app` mounts your host folder (where `main.py` lives) into the container.  
- `micropython-env` is your Docker image name.  
- You’ll now be inside the container’s bash terminal.

### Transfer Your File
Once inside the container:
```bash
mpremote connect /dev/ttyS2 fs cp /app/main.py :main.py
```
or
```bash
ampy --port /dev/ttyS2 put /app/main.py
```

To open the REPL:
```bash
mpremote connect /dev/ttyS2 repl
```

When the ESP32 reboots, it will automatically execute `main.py`.

---

## 💻 Method 2: Using VS Code Terminal (No Docker)

You can also use VS Code’s integrated terminal to copy files directly to the ESP32.

1. **Plug in your ESP32** and note the COM port (e.g. `COM5` on Windows or `/dev/ttyS2` on Linux/Mac).
2. **Open the terminal in VS Code**.
3. **Use `mpremote` (or `ampy`) to copy your script:**

### Example (Windows)
```powershell
mpremote connect COM5 fs cp main.py :main.py
```

### Example (Linux/Mac)
```bash
mpremote connect /dev/ttyS2 fs cp main.py :main.py
```

4. **Optional:** Open a REPL session to test:
```bash
mpremote connect /dev/ttyS2 repl
```

Once the file is uploaded, **reboot the ESP32** and `main.py` will start automatically.

---

✅ **Summary**
- `main.py` runs automatically on boot.  
- You can transfer it via **Docker tools** or directly in **VS Code’s terminal**.  
- Use `mpremote` for easy file management and REPL access.


# 💻 Programming an ESP32 with MicroPython (Windows + VS Code)

## 🧩 Overview
When programming an ESP32 with **MicroPython**:
- You write Python files (`.py`) that are stored on the ESP32’s internal flash memory.
- The file named **`main.py`** runs automatically each time the device boots.
- You can manage files and interact with the device using **`mpremote`** from a PowerShell terminal in VS Code.

---

## ⚙️ Setup and File Transfer in VS Code

1. **Plug in your ESP32** and note the COM port (e.g. `COM3`).
2. **Open a terminal** in VS Code (**PowerShell**).
3. **Upload your main program:**
   ```powershell
   mpremote connect COM3 fs cp micropython/main.py :main.py
   ```
4. **List files on the device:**
   ```powershell
   mpremote connect COM3 fs ls
   ```
5. **View file contents:**
   ```powershell
   mpremote connect COM3 fs cat main.py
   ```
6. **Delete a file:**
   ```powershell
   mpremote connect COM3 fs rm main.py
   ```
7. **Run a local script (without copying):**
   ```powershell
   mpremote connect COM3 run micropython/main.py
   ```
8. **Open the interactive REPL:**
   ```powershell
   mpremote connect COM3 repl
   ```
   > Exit the REPL with `Ctrl+]` or `Ctrl+A` then `Ctrl+X`.

9. **Run a powershell script to copy multiple files:**
   ```powershell
   micropython\upload_esp32.ps1
   ```

---

## 🧹 Optional: Erase All Files
Erase all files from the ESP32 filesystem (use with caution):
```powershell
mpremote connect COM3 fs erase
```

---

✅ **Summary**
- `main.py` runs automatically on boot.
- Use `mpremote` in VS Code’s PowerShell terminal for file management and REPL access.
