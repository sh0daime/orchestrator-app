# Quick Start Guide - Python Orchestrator App

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test the Installation

Run the test script to verify everything works:

```bash
python test_app.py
```

### 3. Configure Your Server

Create your configuration (or use the Settings UI):

**Option A: Use the test configuration**
```bash
# The test script creates a sample config with your server details
# Edit if needed: %APPDATA%\orchestrator-app\config.json (Windows)
```

**Option B: Use the Settings UI**
1. Run the app: `python backend/main.py`
2. Right-click tray icon → Settings
3. Fill in your server details:
   - Host: `192.168.50.101`
   - Port: `22`
   - Username: `calvin`
   - SSH Key Path: `C:\Users\plab\calvin@desktop`
   - Portal Port: `8080`
   - Portal Path: `/home/calvin/calvinsidharta/unified-gradio-portal`

### 4. Configure VCTT App

In Settings → Local App Configuration:
- App Name: `VCTT`
- Executable Path: `main.py`
- Working Directory: `C:\Users\plab\calvinsidharta\data\VCTT_app`
- ✓ Use Shell Command
- Conda Environment Name: `vctt_env`

## Running the App

### Development Mode

```bash
python backend/main.py
```

The app will:
- Start in the system tray (look bottom-right, near clock)
- Show no windows initially (tray-only app)
- Create windows on demand when you click tray menu items

### System Tray Menu

Right-click the tray icon to access:

- **Launch Portal** - Starts Docker containers on remote server
- **Launch VCTT** - Launches local VCTT app with conda
- **Settings** - Configure servers and apps
- **Status** - View container status and portal health
- **Quit** - Exit the app

## Testing SSH Connection

1. Open Settings from tray
2. Fill in server details
3. Click "Test Connection"
4. Should see: "✓ Connection successful!"

**Note:** Your ED25519 OpenSSH key (`calvin@desktop`) works natively with Python!

## Building Executable

Create a standalone .exe file:

```bash
python build.py
```

Output: `dist/Orchestrator.exe` (~50MB)

## Troubleshooting

### App doesn't start
```bash
# Check for errors
python backend/main.py

# Common issues:
# - Missing dependencies: pip install -r requirements.txt
# - Icon file missing: check src-tauri/icons/icon.png exists
```

### SSH connection fails
```bash
# Test SSH manually
ssh -i C:\Users\plab\calvin@desktop calvin@192.168.50.101

# Common issues:
# - Wrong key path
# - Key not in authorized_keys on server
# - Firewall blocking port 22
```

### VCTT doesn't launch
```bash
# Test conda manually
conda activate vctt_env
python C:\Users\plab\calvinsidharta\data\VCTT_app\main.py

# Common issues:
# - Conda not in PATH
# - Wrong environment name
# - Wrong working directory
```

### Settings window doesn't open
```bash
# Check console output for errors
# Verify HTML files exist in src/ directory
# Try: ls src/settings.html
```

## File Locations

- **Config**: `%APPDATA%\orchestrator-app\config.json` (Windows)
- **Source**: `backend/` (Python code)
- **Frontend**: `src/` (HTML/CSS/JS)
- **Icons**: `src-tauri/icons/`

## Next Steps

1. **Test Portal Launch**: Click "Launch Portal" from tray → opens in browser
2. **Test VCTT**: Click "Launch VCTT" from tray → app starts in new window
3. **Check Status**: Click "Status" from tray → view containers
4. **Build Executable**: Run `python build.py` for distribution

## Key Advantages

✓ **Pure Python** - Easy for AI team to maintain
✓ **ED25519 Support** - Your OpenSSH key works natively
✓ **No Compilation** - Instant code changes
✓ **Cross-Platform** - Works on Windows, Mac, Linux

## Documentation

- `README-PYTHON.md` - Full documentation
- `MIGRATION_GUIDE.md` - Tauri → Python migration details
- `test_app.py` - Automated tests

## Getting Help

If something doesn't work:
1. Check console output for errors
2. Run `python test_app.py` to diagnose
3. Verify configuration in Settings UI
4. Check MIGRATION_GUIDE.md for troubleshooting

---

**Ready to go!** Run `python backend/main.py` and look for the tray icon.

