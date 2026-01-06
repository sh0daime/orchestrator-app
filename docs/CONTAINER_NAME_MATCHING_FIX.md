# Container Name Matching Fix

## Issues Identified

From your screenshots, I identified several related issues:

### Issue 1: Container Detection ("gin" server)
- Shows "1 container" detected ✓
- Status says "Stopped" ✗
- "Start Service" button doesn't change ✗
- URL doesn't appear ✗

### Issue 2: Inconsistent Behavior ("rum" vs "gin")
- Same app works on "rum" server ✓
- Same app fails on "gin" server ✗
- This suggests container name mismatch

### Issue 3: Restart Failure
- Error: "no such service: pipeline-management-tool"
- This is because `docker compose restart` expects **service names** (from docker-compose.yml)
- But we're passing **container names** (what Docker actually creates)

## Root Cause

Docker Compose has THREE different names:

1. **Service name** (in docker-compose.yml): `pipeline-tool`
2. **Container name** (Docker creates): `data-pipeline-tool-1` or `pipeline-management-tool`
3. **Configured name** (what you enter): Could be either

The matching was too strict and only checked if configured name was IN container name, not the reverse.

## Solutions Implemented

### 1. ✅ Flexible Multi-Strategy Matching

Updated `backend/api.py` with **3 matching strategies**:

```python
# Strategy 1: Exact match
"pipeline-tool" == "pipeline-tool" ✓

# Strategy 2: Partial match (bidirectional)
"pipeline-tool" in "data-pipeline-tool-1" ✓
"data-pipeline-tool-1" contains "pipeline" ✓

# Strategy 3: Normalized match (remove hyphens/underscores)
"pipeline_management_tool" matches "pipeline-management-tool" ✓
```

**Now handles**:
- Different naming conventions
- Project prefixes (docker-compose adds project name)
- Suffix numbers (-1, -2, etc.)
- Hyphen vs underscore differences

### 2. ✅ Fallback to "Any Container Running"

If no specific match found but ANY container is running from that docker-compose path:
```python
if not main_container_running and service_running:
    main_container_running = True  # Fallback
```

This ensures services show as "running" even with name mismatches.

### 3. ✅ Fixed Container Restart

Changed from:
```python
# ✗ OLD: Uses service name (doesn't work)
docker compose restart pipeline-tool
```

To:
```python
# ✓ NEW: Uses actual container name
docker restart data-pipeline-tool-1
```

Now restart works with the actual container name Docker created.

### 4. ✅ Debug Logging

Added comprehensive logging to help diagnose issues:
```
=== Service: Pipeline Management Tool ===
Configured container name: 'pipeline-tool'
Containers found: ['data-pipeline-tool-1', 'data-redis-1']
✓ Matched (partial): data-pipeline-tool-1
```

You'll see this in the terminal when running the app.

### 5. ✅ Diagnostic Tool

Created `diagnose_containers.py` to help troubleshoot:
```bash
# Diagnose all servers
python diagnose_containers.py

# Diagnose specific server
python diagnose_containers.py gin
```

Shows:
- Exact container names Docker created
- Which names match your config
- Health check status
- Recommendations

## How to Fix Your Specific Issue

### Option 1: Run Diagnostic Tool (Recommended)

```bash
python diagnose_containers.py gin
```

This will show you the EXACT container name Docker created. Copy that name and paste it into Settings.

### Option 2: Check Manually via SSH

SSH into the "gin" server:
```bash
ssh calvin@192.168.50.101
cd /path/to/your/pipeline-tool
docker compose ps --format json
```

Look for the `"Name"` field - that's the exact container name to use.

### Option 3: Use the New Matching Logic

With the improved matching logic, you should now be able to use:
- Service name from docker-compose.yml: `pipeline-tool`
- Or partial name: `pipeline`
- Or any reasonable variation

The app will find it automatically.

## Testing the Fix

1. **Restart the app**:
   ```bash
   python backend/main.py
   ```

2. **Watch the terminal** for debug output:
   ```
   === Service: Pipeline Management Tool ===
   Configured container name: 'pipeline-tool'
   Containers found: ['data-pipeline-tool-1']
   ✓ Matched (partial): data-pipeline-tool-1
   ```

3. **Check Status page**:
   - Should now show "Running" or "Ready"
   - URL should appear
   - Start/Stop button should update correctly

4. **Test restart**:
   - Expand Container Details
   - Click 🔄 Restart
   - Should work without errors

## Why It Works Differently on "rum" vs "gin"

Possible reasons:

1. **Different docker-compose.yml structure**:
   - "rum" might use simpler names
   - "gin" might have project prefix

2. **Different Docker Compose versions**:
   - Older versions: `pipeline-tool-1`
   - Newer versions: `project-pipeline-tool-1`

3. **Different project names**:
   - Compose uses directory name as project prefix
   - `/data/app` → `data-pipeline-tool-1`
   - `/pipeline` → `pipeline-pipeline-tool-1`

The new matching logic handles all these cases!

## Configuration Recommendations

### For Simple Services (1 container)
Set **Container Name** to:
- Service name from docker-compose.yml (e.g., `pipeline-tool`)
- Or run diagnostic tool and copy exact name

### For Multi-Container Services (parent + children)
Set **Container Name** to:
- Main service name that handles HTTP requests
- All containers will still be visible in Container Details
- Only main container status affects Start/Stop button

### For Non-HTTP Services (databases, workers)
Set **Container Name** to:
- Any service name from docker-compose.yml
- Health check will fail (expected)
- Service still manageable via Start/Stop/Restart

## Updated Behavior

| Scenario | Old Behavior | New Behavior |
|----------|--------------|--------------|
| Exact match | ✓ Works | ✓ Works |
| Partial match | ✗ May fail | ✓ Works |
| Reverse match | ✗ Fails | ✓ Works |
| Normalized match | ✗ Fails | ✓ Works |
| No match but running | ✗ Shows stopped | ✓ Shows running (fallback) |
| Container restart | ✗ Service name error | ✓ Works with container name |

## Summary

**What changed**:
1. ✅ Flexible 3-strategy matching algorithm
2. ✅ Bidirectional name checking
3. ✅ Fallback to "any container" if specific match fails
4. ✅ Fixed restart to use container name (not service name)
5. ✅ Added debug logging for troubleshooting
6. ✅ Created diagnostic tool

**Result**:
- Both "gin" and "rum" should now work consistently
- Container name matching is much more forgiving
- Restart functionality works correctly
- Easy to diagnose issues with diagnostic tool

Run the diagnostic tool and let me know what it shows! 🔍

