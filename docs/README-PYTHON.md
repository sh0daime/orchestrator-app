# Orchestrator App - Python Version

This is the Python implementation of the Orchestrator App using PyWebView.

## Requirements

- Python 3.11+
- pip

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running in Development

```bash
python backend/main.py
```

The app will run in the system tray. Right-click the tray icon to access features:
- Launch Portal - Start the remote Docker portal
- Launch VCTT - Launch the local VCTT application
- Settings - Configure servers and apps
- Status - View server and container status
- Quit - Exit the application

## Building Executable

To create a standalone executable:

```bash
python build.py
```

The executable will be created in the `dist/` directory.

## Configuration

The app stores configuration in:
- Windows: `%APPDATA%\orchestrator-app\config.json`
- Mac/Linux: `~/.config/orchestrator-app/config.json`

### SSH Key Setup

For SSH connections:
1. The app supports ED25519 OpenSSH format keys (paramiko handles them natively)
2. Place your private key at a known location (e.g., `C:\Users\YourName\.ssh\id_ed25519`)
3. Configure the path in Settings

### VCTT App with Conda

To launch Python apps with conda environments:
1. In Settings, check "Use Shell Command"
2. Enter your conda environment name
3. The app will run: `conda activate <env> && python <script>`

## Project Structure

```
orchestrator-app/
├── backend/                 # Python backend
│   ├── __init__.py
│   ├── main.py             # Entry point with PyWebView & tray
│   ├── config.py           # Configuration management
│   ├── ssh_client.py       # SSH/Docker operations  
│   ├── process_manager.py  # Local app launcher
│   └── api.py              # API functions
├── src/                     # Frontend (HTML/CSS/JS)
│   ├── settings.html
│   ├── settings.js
│   ├── status.html
│   ├── status.js
│   └── styles.css
├── requirements.txt
├── build.py
└── README-PYTHON.md
```

## Migration from Tauri

This Python version provides the same functionality as the Tauri version:

**Advantages:**
- Pure Python - easier maintenance for AI team
- ED25519 OpenSSH keys work natively
- No Rust compilation required
- Simpler debugging

**Trade-offs:**
- Larger executable (~50MB vs 15MB)
- Slightly slower startup

## Troubleshooting

### SSH Connection Issues

If you get authentication errors:
1. Verify the SSH key path is correct
2. Check that the key file exists
3. Ensure the public key is in the server's `~/.ssh/authorized_keys`
4. Test with: `ssh -i <key_path> user@host`

### VCTT Launch Issues

If VCTT doesn't launch:
1. Verify conda is in PATH
2. Test manually: `conda activate <env> && python <script>`
3. Check the working directory is correct
4. Look at console output for errors

### Build Issues

If PyInstaller fails:
1. Make sure all dependencies are installed
2. Try running from a clean virtual environment
3. Check that icon files exist in `src-tauri/icons/`

