# Orchestrator App

A cross-platform desktop application for managing remote AI application portals and launching local applications.

## Features

- **System Tray Interface**: Always-running background app with quick access menu
- **SSH Server Management**: Connect to remote Linux servers and manage Docker containers
- **Portal Launcher**: Automatically start and monitor the unified-gradio-portal
- **Local App Launcher**: Launch local applications like VCTT
- **Settings Window**: Configure servers and local apps
- **Status Dashboard**: Monitor container status and connection health

## Prerequisites

### Windows
- Rust toolchain (install from https://rustup.rs/)
- Node.js (LTS version from https://nodejs.org/)
- Visual Studio Build Tools (for Rust compilation)
  - Download from: https://visualstudio.microsoft.com/downloads/
  - Install "Desktop development with C++" workload

### Mac
- Rust toolchain
- Node.js
- Xcode Command Line Tools: `xcode-select --install`

## Development Setup

1. **Install Tauri CLI**:
   ```bash
   npm install -g @tauri-apps/cli
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run in development mode**:
   ```bash
   npm run tauri dev
   ```

4. **Build for production**:
   ```bash
   npm run tauri build
   ```

## Configuration

The app stores configuration in:
- **Windows**: `%APPDATA%\orchestrator-app\config.json`
- **Mac**: `~/Library/Application Support/orchestrator-app/config.json`
- **Linux**: `~/.config/orchestrator-app/config.json`

See `config/config.example.json` for an example configuration file.

## Usage

1. **First Time Setup**:
   - Right-click the system tray icon
   - Click "Settings"
   - Configure your server (SSH host, username, key path, portal path)
   - Configure local apps (VCTT executable path)
   - Click "Test Connection" to verify SSH access
   - Click "Save Configuration"

2. **Launch Portal**:
   - Right-click system tray icon
   - Click "Launch Portal"
   - The app will:
     - Connect to server via SSH
     - Check if containers are running
     - Start containers if needed
     - Wait for portal to be ready
     - Open browser automatically

3. **Launch VCTT**:
   - Right-click system tray icon
   - Click "Launch VCTT"
   - VCTT will launch as a separate process

4. **Check Status**:
   - Right-click system tray icon
   - Click "Status"
   - View server connection, container status, and portal URL

## Project Structure

```
orchestrator-app/
├── src-tauri/          # Rust backend
│   ├── src/
│   │   ├── main.rs     # Entry point
│   │   ├── lib.rs      # Tauri setup, tray menu
│   │   ├── config.rs   # Configuration management
│   │   ├── ssh.rs      # SSH connection handling
│   │   ├── process.rs  # Local process management
│   │   └── commands.rs # Tauri commands (API)
│   └── Cargo.toml      # Rust dependencies
├── src/                # Frontend
│   ├── index.html      # Main window
│   ├── settings.html   # Settings window
│   ├── status.html     # Status dashboard
│   ├── main.ts         # Main window logic
│   ├── settings.js     # Settings window logic
│   ├── status.js       # Status dashboard logic
│   └── styles.css      # Styling
└── config/             # Configuration examples
```

## Building

### Windows
```bash
npm run tauri build
```
Output: `src-tauri/target/release/orchestrator-app.exe` and installer in `src-tauri/target/release/bundle/`

### Mac
```bash
npm run tauri build
```
Output: `.app` bundle and `.dmg` in `src-tauri/target/release/bundle/`

## Troubleshooting

### SSH Connection Fails
- Verify SSH key path is correct
- Ensure SSH key has proper permissions (chmod 600 on Linux/Mac)
- Test SSH connection manually: `ssh user@host`
- Check firewall settings

### Portal Doesn't Start
- Verify portal path on server is correct
- Check Docker is installed and running on server
- Verify user has permissions to run docker commands
- Check server logs: `docker compose logs`

### VCTT Doesn't Launch
- Verify executable path is correct
- Check file permissions
- Ensure working directory exists (if specified)

## License

[Your License Here]
