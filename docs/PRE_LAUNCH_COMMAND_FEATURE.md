# Pre-Launch Command Feature

## Problem Solved

Docker containers with **file permission requirements** or **environment setup needs** can now be properly initialized before starting.

### Use Case: Pipeline Management Tool

Your Pipeline Management Tool needs:
1. Dynamic UID/GID detection
2. `.env` file creation
3. File permission setup
4. **THEN** docker compose up

## Solution: Pre-Launch Command Field

Added an **optional** `pre_launch_command` field to each service that runs **before** `docker compose up`.

## How It Works

### Backend Changes

**1. ServiceConfig** (`backend/config.py`):
```python
@dataclass
class ServiceConfig:
    pre_launch_command: Optional[str] = None  # New field
```

**2. SSHClient** (`backend/ssh_client.py`):
```python
def start_service(self, path, service_name, pre_launch_command):
    # Run pre-launch command if specified
    if pre_launch_command:
        self.execute_command(f"cd {path} && {pre_launch_command}")
    
    # Then start service
    self.execute_command(f"cd {path} && docker compose up -d")
```

**3. API** (`backend/api.py`):
```python
# Pass pre-launch command to SSH client
ssh.start_service(service.path, None, service.pre_launch_command)
```

### Frontend Changes

**Settings UI** (`src/settings.js`):
```
Service Configuration:
├─ Service Name: "Pipeline Management Tool"
├─ Container Name: "pipeline-tool"
├─ Port: 7860
├─ Path: "/home/calvin/data/pipeline"
├─ Health Check: "/"
└─ Pre-Launch Command: "python launcher.py"  ← NEW FIELD
```

## Configuration Examples

### Example 1: Pipeline Management Tool

**Setup**:
- Service Name: Pipeline Management Tool
- Path: `/home/calvin/data/pipeline`
- Pre-Launch Command: `python launcher.py`

**What Happens**:
1. SSH into server
2. `cd /home/calvin/data/pipeline`
3. `python launcher.py` → Creates `.env`, sets UID/GID, fixes permissions
4. `docker compose up -d` → Starts container with correct permissions

### Example 2: Environment File Creation

**Pre-Launch Command**:
```bash
echo "UID=$(id -u)" > .env && echo "GID=$(id -g)" >> .env
```

**What Happens**:
1. Creates `.env` file
2. Adds current user's UID/GID
3. Docker Compose reads `.env` automatically
4. Container runs with matching permissions

### Example 3: Multiple Setup Steps

**Pre-Launch Command**:
```bash
./setup.sh && chmod +x scripts/*.sh && mkdir -p logs data
```

**What Happens**:
1. Runs setup script
2. Makes scripts executable
3. Creates required directories
4. Then starts containers

### Example 4: Cleanup Before Start

**Pre-Launch Command**:
```bash
rm -f .lock && docker compose down
```

**What Happens**:
1. Removes lock file
2. Ensures clean state
3. Then starts fresh

## Your Specific Use Case

### Your launcher.py Does:
```python
def launch_app():
    # 1. Detect UID/GID
    uid, gid = get_user_ids()
    
    # 2. Create .env file
    create_env_file(uid, gid)
    
    # 3. Check Docker
    check_docker()
    
    # 4. Start containers
    docker compose up -d
```

### In Orchestrator Settings:

**Service Configuration**:
- Service Name: `Pipeline Management Tool`
- Container Name: `pipeline-tool`
- Port: `7860`
- Path: `/home/calvin/data/pipeline`
- Health Check: `/`
- **Pre-Launch Command**: `python launcher.py` ← Runs steps 1-3, orchestrator does step 4

## How To Use

### Step 1: Copy Your launcher.py to Server

SSH into your Linux server:
```bash
cd /home/calvin/data/pipeline
# Copy your launcher.py here
```

### Step 2: Modify launcher.py

Remove the actual docker compose call since orchestrator will do that:

**Current launcher.py**:
```python
def launch_app(action='up'):
    # ...setup code...
    subprocess.run(['docker', 'compose', 'up', '-d'])  # ← Remove this
```

**Modified launcher.py** (for orchestrator):
```python
def setup_only():
    """Setup env and permissions, but don't start containers"""
    uid, gid = get_user_ids()
    create_env_file(uid, gid)
    check_docker()
    print("Setup complete, ready for docker compose up")
    return 0

if __name__ == '__main__':
    sys.exit(setup_only())
```

### Step 3: Configure in Orchestrator

Open Settings → Your Server → Pipeline Management Tool:

**Pre-Launch Command**:
```
python launcher.py
```

or if launcher.py needs specific Python version:
```
python3 launcher.py
```

or if you need to ensure it's executable:
```
chmod +x launcher.py && python launcher.py
```

### Step 4: Start from Orchestrator

Click **Start Service** in Status page.

**Execution Flow**:
```
1. SSH connects to server
2. cd /home/calvin/data/pipeline
3. python launcher.py
   - Detects UID: 1001, GID: 1001
   - Creates .env with UID=1001, GID=1001
   - Checks Docker is running
4. docker compose up -d
   - Reads .env file
   - Builds/starts container with correct UID/GID
   - Container has proper file permissions
```

## Alternative: Direct Shell Commands

If you don't want to use launcher.py, you can do the setup directly:

**Pre-Launch Command**:
```bash
echo "UID=$(id -u)" > .env && echo "GID=$(id -g)" >> .env && echo "CUDA_VISIBLE_DEVICES=0" >> .env
```

This creates the `.env` file inline without needing a separate script.

## Important Notes

### 1. Pre-Launch Runs EVERY TIME

The command runs **every time** you click Start Service. Make sure it's idempotent (safe to run multiple times).

**Good** (idempotent):
```bash
echo "UID=$(id -u)" > .env  # Overwrites, always safe
```

**Bad** (not idempotent):
```bash
echo "UID=$(id -u)" >> .env  # Appends, duplicates on re-run
```

### 2. Command Runs in Service Path

The command automatically runs in the service's path directory, so:
```bash
# Pre-launch command: python launcher.py
# Actually runs: cd /home/calvin/data/pipeline && python launcher.py
```

### 3. Errors Stop Startup

If pre-launch command fails, the service won't start. Check terminal output for errors.

### 4. Empty = No Pre-Launch

Leave the field empty for services that don't need setup:
- AI Portal: (empty) - no pre-launch needed
- Pipeline Tool: `python launcher.py` - needs setup

## Benefits

✅ **Not hard-coded**: Generic solution, works for any service
✅ **Optional**: Only use when needed
✅ **Flexible**: Can run any shell command
✅ **Reusable**: Same approach for different permission/setup needs
✅ **Visible**: Clear in UI what setup happens
✅ **Debuggable**: Can test command manually via SSH

## Testing

### Test Pre-Launch Command Manually

SSH into server:
```bash
cd /home/calvin/data/pipeline
python launcher.py
# Check if .env created
cat .env
# Should show: UID=1001, GID=1001, etc.
```

### Test in Orchestrator

1. Configure pre-launch command in Settings
2. Save configuration
3. Go to Status page
4. Click Start Service
5. Watch terminal for output:
   ```
   Starting service Pipeline Management Tool...
   Running pre-launch command: python launcher.py
   Detected user IDs - UID: 1001, GID: 1001
   Created/updated .env file with UID=1001, GID=1001
   Setup complete
   Service start command sent
   ```

## Troubleshooting

### Error: "command not found"

**Problem**: Python or script not in PATH

**Solution**: Use full path
```bash
/usr/bin/python3 /home/calvin/data/pipeline/launcher.py
```

### Error: "Permission denied"

**Problem**: Script not executable

**Solution**: Make it executable first
```bash
chmod +x launcher.py && python launcher.py
```

### Error: ".env file not created"

**Problem**: Pre-launch command didn't run or failed

**Solution**: Check terminal output, test manually via SSH

## Summary

**What Changed**:
- ✅ Added optional `pre_launch_command` field to ServiceConfig
- ✅ Backend runs command before `docker compose up`
- ✅ Frontend shows field in Settings UI
- ✅ Solves file permission issues generically

**For Your Pipeline Tool**:
1. Set Pre-Launch Command: `python launcher.py`
2. Launcher creates `.env` with UID/GID
3. Docker Compose uses correct permissions
4. File access works! 🎉

No hard-coding needed - this approach works for ANY service that needs pre-launch setup!

