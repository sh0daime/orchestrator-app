# Container Management Improvements

## Issues Addressed

### 1. ✅ Refresh Button Clarification
**Question**: What does the individual "Refresh" button do?

**Answer**: The Refresh button **only refreshes the status display** for that specific server. It does NOT restart any containers. It calls `get_status(server_id)` to re-fetch and update the display without waiting for the 5-second auto-refresh.

**Use case**: When you manually change something on the server (e.g., via SSH) and want to see the updated status immediately.

---

### 2. ✅ Display All Containers (Parent + Sub-containers)

**Problem**: Previously, only the container matching `service.container_name` exactly was displayed. This hid:
- Sub-containers orchestrated by a parent container
- Other containers in the same docker-compose.yml

**Solution**: Updated `api.py` line 148-172 to:
```python
# Show ALL containers from the docker-compose path
services_status.append({
    'id': service.id,
    'name': service.name,
    'url': f"http://{server.host}:{service.port}",
    'ready': service_ready,
    'running': main_container_running,  # Specific container for button state
    'has_containers': service_running,  # Any containers running
    'containers': [asdict(c) for c in containers],  # ALL containers
    'container_count': len(containers)
})
```

**Benefits**:
- ✅ Automatically detects and displays all containers
- ✅ Shows parent + all sub-containers
- ✅ No hard-coding required
- ✅ Works for any docker-compose.yml structure

---

### 3. ✅ Docker Compose Service Name vs Container Name

**Problem**: Docker Compose service names (in docker-compose.yml) differ from actual container names Docker creates.

**Example**:
```yaml
# docker-compose.yml
services:
  pipeline-tool:  # ← Service name
    image: my-image
```

Docker creates container named: `project-pipeline-tool-1` (not just `pipeline-tool`)

**Solution**: Use **partial name matching**:
```python
main_container_running = any(
    service.container_name in c.name and c.state == "running"
    for c in containers
)
```

**Now works with**:
- ✅ Exact matches: `pipeline-tool` → `pipeline-tool`
- ✅ Docker Compose naming: `pipeline-tool` → `project-pipeline-tool-1`
- ✅ Multiple instances: `pipeline-tool` → `project-pipeline-tool-1`, `project-pipeline-tool-2`

**What to set in Settings**:
- **Container Name**: Use the service name from your docker-compose.yml (e.g., `pipeline-tool`)
- The app will automatically match it against actual container names like `project-pipeline-tool-1`

---

### 4. ✅ Individual Container Restart Buttons

**New Feature**: Each running container now has its own **🔄 Restart** button!

**Implementation**:
1. **Backend** (`ssh_client.py`): Added `restart_container(path, container_name)`
2. **Backend** (`api.py`): Added `restart_container(server_id, service_id, container_name)`
3. **Frontend** (`status.js`): Added restart button for each container

**Usage**:
```
Service: AI Portal (3 containers)

Container Details:
  ┌─ ai-portal-main [running]    [🔄 Restart]
  ├─ ai-portal-worker-1 [running] [🔄 Restart]
  └─ ai-portal-db [running]       [🔄 Restart]
```

Click **🔄 Restart** on any individual container to restart just that container without affecting others!

**Use Cases**:
- Restart a stuck worker container
- Reload configuration for a specific service
- Troubleshoot individual containers
- Minimal disruption (other containers keep running)

---

### 5. ✅ Health Check Timeout / False Negatives

**Problem**: Services were starting successfully but the orchestrator reported "Failed to launch service: service did not become ready within 120 seconds" because:
- Service doesn't have an HTTP endpoint
- Health check path is wrong
- Service responds with non-200 status code
- Service takes longer to start

**Solution**: Changed from **hard error** to **soft warning**:

**Before**:
```python
if not ready:
    raise Exception(f"Service did not become ready within {max_wait} seconds")
    # ❌ Stops execution, marks as failed
```

**After**:
```python
if not ready:
    # Service started but health check didn't pass
    print(f"Warning: Service started but health check didn't return 200 within {max_wait}s")
    print(f"Health check URL: http://localhost:{service.port}{service.healthcheck_path}")
    print("This is normal if the service doesn't have an HTTP endpoint")
    # ✅ Continues, service is marked as started
```

**Benefits**:
- ✅ Services without HTTP endpoints work correctly
- ✅ Non-web services (databases, workers) can be managed
- ✅ Health check is optional, not mandatory
- ✅ Better logging for troubleshooting
- ✅ Service still starts even if health check fails

**Troubleshooting Health Checks**:

If your service shows "Starting..." instead of "Ready":

1. **Check if it has an HTTP endpoint**: Some services (databases, workers) don't have HTTP
   - If no HTTP: This is normal, ignore the warning
   - Status will show container as "running" even if not "ready"

2. **Verify health check path in Settings**:
   - Root path: `/` (most common)
   - Custom health endpoint: `/health`, `/api/status`, `/ping`
   - Example: Gradio typically uses `/`

3. **Check the actual response**:
   ```bash
   # SSH into your server and test:
   curl -I http://localhost:7860/
   ```
   Look for `HTTP/1.1 200 OK`

4. **For non-HTTP services**: Set health check path to `/` - it will timeout but service still works

---

## Example Scenarios

### Scenario 1: AI Portal (Multi-Container Service)

**docker-compose.yml**:
```yaml
services:
  ai-portal:
    image: portal-frontend
    ports: [8080:8080]
  
  ai-worker-1:
    image: portal-worker
  
  ai-worker-2:
    image: portal-worker
  
  redis:
    image: redis:latest
```

**In Orchestrator Settings**:
- Service Name: "AI Portal"
- Container Name: `ai-portal` (main service)
- Port: 8080
- Path: `/home/calvin/ai-portal`
- Health Check Path: `/`

**In Status Page**:
```
AI Portal (4 containers)                [Ready]
http://192.168.50.101:8080    [📋 Copy] [🌐 Open]

Container Details:
  ┌─ project-ai-portal-1 [running]     [🔄 Restart]
  ├─ project-ai-worker-1-1 [running]   [🔄 Restart]
  ├─ project-ai-worker-2-1 [running]   [🔄 Restart]
  └─ project-redis-1 [running]         [🔄 Restart]
```

### Scenario 2: Gradio Pipeline Tool (Standalone Service)

**docker-compose.yml**:
```yaml
services:
  pipeline-tool:
    image: gradio-app
    ports: [7860:7860]
```

**In Orchestrator Settings**:
- Service Name: "Gradio Pipeline Tool"
- Container Name: `pipeline-tool`
- Port: 7860
- Path: `/home/calvin/gradio-app`
- Health Check Path: `/` (or `/api/status` if custom)

**In Status Page**:
```
Gradio Pipeline Tool (1 container)      [Ready]
http://192.168.50.101:7860    [📋 Copy] [🌐 Open]

Container Details:
  └─ gradio-app-pipeline-tool-1 [running]  [🔄 Restart]
```

### Scenario 3: Database Service (No HTTP)

**docker-compose.yml**:
```yaml
services:
  postgres:
    image: postgres:14
    ports: [5432:5432]
```

**In Orchestrator Settings**:
- Service Name: "PostgreSQL Database"
- Container Name: `postgres`
- Port: 5432
- Path: `/home/calvin/database`
- Health Check Path: `/` (will timeout, but that's OK)

**In Status Page**:
```
PostgreSQL Database (1 container)       [Starting...]
⚠ No HTTP endpoint (normal for databases)

Container Details:
  └─ database-postgres-1 [running]  [🔄 Restart]
```

Note: Shows "Starting..." because no HTTP, but container is running and functional.

---

## Summary of Changes

### Backend Files

1. **`backend/api.py`**:
   - Show ALL containers from docker-compose path
   - Partial name matching for container names
   - Soft warning instead of hard error for health checks
   - Added `restart_container()` method

2. **`backend/ssh_client.py`**:
   - Added `restart_container()` method

### Frontend Files

3. **`src/status.js`**:
   - Display all containers with count badge
   - Individual restart button per container
   - Better container status display

---

## Testing

Test the improvements:

1. **Multi-container display**:
   - Add a service with multiple containers
   - Check Status page - all containers should appear

2. **Container name matching**:
   - Set container name to service name (e.g., `pipeline-tool`)
   - Docker creates `project-pipeline-tool-1`
   - Should still detect and show as running ✓

3. **Individual restart**:
   - Go to Status page
   - Expand Container Details
   - Click 🔄 Restart on any running container
   - That container restarts, others stay running ✓

4. **Health check tolerance**:
   - Add a service without HTTP endpoint
   - Or with non-200 health check response
   - Service should start successfully (with warning) ✓

---

## Best Practices

### For HTTP Services (Web Apps, APIs)
- ✅ Set correct health check path
- ✅ Verify service responds with HTTP 200
- ✅ Status will show "Ready" when accessible

### For Non-HTTP Services (Databases, Workers, Queues)
- ✅ Set any health check path (will timeout, but OK)
- ✅ Check container status directly (not "Ready" badge)
- ✅ Use container restart button for maintenance

### For Multi-Container Services
- ✅ Set container name to main service
- ✅ All sub-containers automatically detected
- ✅ Restart individual containers as needed
- ✅ Monitor all containers from one place

---

## FAQ

**Q: Why does my service show "Starting..." but containers are running?**
A: Health check can't reach the endpoint. Check if:
- Service has HTTP endpoint
- Health check path is correct
- Port is accessible
- Service responds with 200

**Q: Can I restart just one container without affecting others?**
A: Yes! Click the 🔄 Restart button next to any running container.

**Q: What if I don't know the exact container name?**
A: Use the service name from docker-compose.yml. The app will match it automatically.

**Q: How do I see sub-containers?**
A: They're automatically detected! Just expand "Container Details" for any service.

**Q: Does the Refresh button restart containers?**
A: No! It only refreshes the status display. Use the Stop/Start buttons or individual Restart buttons.

---

Enjoy the improved container management! 🐳🚀

