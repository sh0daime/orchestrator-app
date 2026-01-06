# Quick Start: Multi-Service Orchestrator

## What's New

You can now manage **multiple servers** with **multiple Docker services** each from one orchestrator!

## Getting Started

### 1. Start the App

```bash
python backend/main.py
```

The app will:
- Automatically migrate your old v1.0 config to v2.0 (if you have one)
- Start with a system tray icon
- Create default server entry if none exists

### 2. First Time Setup

Right-click the tray icon → **Settings**

You'll see a new tabbed interface:

```
[Server 1] [+ Add Server]
```

#### Configure Your First Server

Fill in the server details:
- **Server Name**: "Main Server" (or whatever you like)
- **Host**: Your server IP (e.g., `192.168.50.101`)
- **Port**: SSH port (usually `22`)
- **Username**: Your SSH username (e.g., `calvin`)
- **SSH Key Path**: Path to your private key (e.g., `C:\Users\plab\calvin@desktop`)

Click **Test Connection** to verify it works.

#### Add Your First Service

Under "Services", click **+ Add Service**

An accordion item appears. Click it to expand and configure:
- **Service Name**: "AI Portal"
- **Container Name**: "ai-portal" (the Docker container name)
- **Port**: 8080 (the port your service runs on)
- **Path on Server**: "/home/calvin/ai-portal" (where docker-compose.yml is)
- **Health Check Path**: "/" (or your custom health endpoint)

Click **Save Configuration**

### 3. Add Your Gradio App

Still in Settings, scroll to the same server's Services section.

Click **+ Add Service** again:
- **Service Name**: "Gradio Pipeline Tool"
- **Container Name**: "gradio-app"
- **Port**: 7860
- **Path on Server**: "/home/calvin/gradio-app"
- **Health Check Path**: "/" (or "/api/status" if you have one)

Click **Save Configuration**

### 4. Monitor and Launch Services

Right-click the tray icon → **Status**

You'll see:
```
[🟢 Main Server]
```

The green dot means you're connected. Inside you'll see both services:

#### AI Portal Card
```
AI Portal                           [Ready]
┌─────────────────────────────────────────┐
│ http://192.168.50.101:8080              │
│ [📋 Copy] [🌐 Open]                      │
│ [⏹ Stop Service] [🔄 Refresh]            │
└─────────────────────────────────────────┘
```

#### Gradio Pipeline Tool Card
```
Gradio Pipeline Tool              [Stopped]
┌─────────────────────────────────────────┐
│ [▶ Start Service] [🔄 Refresh]           │
└─────────────────────────────────────────┘
```

Click **▶ Start Service** to launch your Gradio app!

The status will update automatically every 5 seconds.

### 5. Add a Second Server (Optional)

Go back to Settings → Click **+ Add Server**

A new tab appears: `[Server 1] [Server 2] [+ Add Server]`

Configure Server 2:
- Different host (e.g., `192.168.50.102`)
- Different SSH credentials
- Different services

Now you can manage apps across multiple servers from one interface!

## Features

### Per-Service Control
- ▶ **Start** - Launch the service
- ⏹ **Stop** - Stop the service
- 🌐 **Open** - Open in browser
- 📋 **Copy** - Copy URL to clipboard
- 🔄 **Refresh** - Update status

### Multi-Server Management
- Add unlimited servers
- Each server has its own tab
- Switch between servers easily
- Remove servers you don't need

### Service Monitoring
- Auto-refresh every 5 seconds
- Connection status per server
- Health status per service
- Container details

## Example Use Cases

### Use Case 1: Same Server, Multiple Apps
```
Main Server (192.168.50.101)
├─ AI Portal (port 8080)
├─ Gradio Pipeline (port 7860)
└─ Monitoring Dashboard (port 3000)
```

### Use Case 2: Development vs Production
```
Production Server (192.168.50.101)
└─ AI Portal (port 8080)

Development Server (192.168.50.102)
├─ AI Portal Dev (port 8080)
└─ Gradio Pipeline Dev (port 7860)
```

### Use Case 3: Multiple Clients
```
Client A Server (192.168.1.100)
└─ Client A Portal (port 8080)

Client B Server (192.168.2.100)
└─ Client B Portal (port 8080)

Shared Tools Server (192.168.50.101)
├─ Gradio Pipeline (port 7860)
└─ Monitoring (port 3000)
```

## Troubleshooting

### Service Won't Start
1. Check the container name matches your docker-compose.yml
2. Verify the path on server is correct
3. SSH into the server and manually run: `cd <path> && docker compose up -d <container>`
4. Check the logs: `docker compose logs <container>`

### Status Shows "Disconnected"
1. Go to Settings → Click **Test Connection**
2. Verify SSH credentials are correct
3. Check your SSH key permissions
4. Try SSH manually: `ssh -i <key> <user>@<host>`

### Old Config Not Migrating
Your config is automatically migrated when you load it. Check:
```
C:\Users\plab\AppData\Roaming\orchestrator-app\config.json
```

It should show `"version": "2.0"` and have a `"services": []` array instead of `portal_port`.

### CSS Not Loading
Make sure you're running from the project root and the `src/` folder contains:
- `styles.css`
- `settings.html`
- `settings.js`
- `status.html`
- `status.js`

## Tips

1. **Use descriptive names**: Name your services clearly (e.g., "Client A Portal", "Dev Gradio")
2. **Health check paths**: Use custom health endpoints like `/api/status` or `/health` if available
3. **Port conflicts**: Make sure each service on the same server uses a different port
4. **Refresh**: Click 🔄 to manually refresh if auto-refresh seems slow
5. **Copy URLs**: Use 📋 to quickly copy service URLs for sharing

## What's Next?

- Add all your Docker apps as services
- Set up multiple servers if needed
- Configure your local apps (VCTT) in the Local Applications section
- Use the Status page as your operations dashboard

Enjoy your scalable orchestrator! 🚀

