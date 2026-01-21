# Sandbox Monitoring Dashboard

## Overview

The Sandbox Monitoring Dashboard provides real-time visibility into the Docker sandbox container's status, resource usage, running processes, MCP servers, and logs. It replaces the standalone VNC viewer with a tabbed interface that allows switching between monitoring view and VNC remote desktop.

## Features

### 📊 Real-Time Monitoring

The monitoring dashboard displays comprehensive sandbox information updated every 5 seconds:

1. **Status Overview**
   - Container status (Running/Stopped/Error)
   - Number of active MCP servers
   - Total process count

2. **Resource Usage**
   - CPU usage percentage with visual bar
   - Memory usage percentage with visual bar
   - Disk usage percentage with visual bar

3. **MCP Server Status**
   - List of all MCP servers with running status
   - Process ID (PID) for each server
   - Visual indicators (green = running, red = stopped/fatal)

4. **Running Processes**
   - Top 10 processes by CPU usage
   - Process ID, name, CPU%, and memory% for each
   - Sorted by CPU consumption

5. **Recent Logs**
   - Last 50 lines from supervisord logs
   - Scrollable log viewer with monospace font
   - Auto-updates every 5 seconds

### 🖥️ VNC Remote Desktop

The VNC tab provides the traditional remote desktop view:
- Full noVNC integration
- Connect/disconnect controls
- Real-time connection status
- Displays X11 desktop from sandbox

## Architecture

### Frontend Components

**[SandboxMonitor.vue](sandbox/frontend/src/components/SandboxMonitor.vue)**
```
├── Status Section (3 cards: Container, MCP Count, Process Count)
├── Resource Section (3 bars: CPU, Memory, Disk)
├── MCP Servers List (all installed MCPs with status)
├── Process List (top 10 by CPU)
└── Logs Viewer (last 50 lines)
```

**[App.vue](sandbox/frontend/src/App.vue)** - Updated Layout
```
Left Panel (Tabbed):
  ├── 📊 Monitor Tab (default) → SandboxMonitor component
  └── 🖥️ VNC Tab → noVNC viewer

Middle Panel:
  └── ChatPanel (AI conversation)

Right Panel (Tabbed):
  ├── 📦 Marketplace Tab
  └── 🛠️ Tools Tab
```

### Backend API Endpoints

All monitoring endpoints are in [backend/main.py](backend/main.py):

#### GET `/api/sandbox/status`
**Description**: Get overall sandbox status including MCP servers and container health.

**Response**:
```json
{
  "status": "running",
  "container": "sandbox-sandbox-os-1",
  "mcp_status": "mcp-shell RUNNING pid 12...",
  "installed_mcps": "{...}",
  "timestamp": 1234567890.123
}
```

**Implementation**:
- Calls `manager_get_mcp_status` tool
- Calls `manager_list_installed_mcps` tool
- Returns combined status information

#### GET `/api/sandbox/processes`
**Description**: Get list of running processes in the sandbox.

**Response**:
```json
{
  "status": "success",
  "processes": "PID NAME CPU% MEM%\n123 python 45.2 12.3\n...",
  "timestamp": 1234567890.123
}
```

**Implementation**:
- Calls `shell_get_running_processes` tool
- Returns process list with CPU and memory usage

#### GET `/api/sandbox/resources`
**Description**: Get container resource usage (CPU, memory, disk).

**Response**:
```json
{
  "status": "success",
  "resources": "CPU:\n23.5\nMemory:\n45.2\nDisk:\n67%",
  "timestamp": 1234567890.123
}
```

**Implementation**:
- Executes `shell_execute_command` with bash script
- Uses `top`, `free`, and `df` commands
- Parses CPU%, memory%, and disk usage

#### GET `/api/sandbox/logs`
**Description**: Get recent logs from MCP servers.

**Response**:
```json
{
  "status": "success",
  "logs": "2024-01-20 10:00:00 INFO Starting...\n...",
  "timestamp": 1234567890.123
}
```

**Implementation**:
- Executes `tail -n 50 /var/log/supervisor/supervisord.log`
- Returns last 50 log lines

#### GET `/api/mcp/marketplace`
**Description**: Get list of available MCPs from the marketplace.

**Response**:
```json
{
  "status": "success",
  "marketplace": "{\"total\": 5, \"mcps\": [...]}",
  "timestamp": 1234567890.123
}
```

**Implementation**:
- Calls `manager_list_available_mcps` tool
- Returns marketplace data

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│ Frontend (Vue 3)                                        │
│                                                         │
│  SandboxMonitor.vue                                     │
│    │                                                    │
│    ├─ fetchStatus()      ──┐                          │
│    ├─ fetchProcesses()   ──┤                          │
│    ├─ fetchResources()   ──┼─→ Every 5 seconds        │
│    └─ fetchLogs()        ──┘                          │
│                                                         │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP GET
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ Backend (FastAPI)                                       │
│                                                         │
│  /api/sandbox/status                                    │
│  /api/sandbox/processes                                 │
│  /api/sandbox/resources                                 │
│  /api/sandbox/logs                                      │
│  /api/mcp/marketplace                                   │
│                                                         │
└──────────────────┬──────────────────────────────────────┘
                   │ MCP Protocol (stdio)
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ MCP Servers (Docker Container)                         │
│                                                         │
│  mcp-manager   → get_mcp_status, list_installed_mcps   │
│  mcp-shell     → get_running_processes, execute_command│
│  mcp-filesystem → (not used for monitoring)            │
│  mcp-chrome    → (not used for monitoring)             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Usage

### Starting the System

1. **Start Docker Container**:
   ```bash
   cd sandbox
   docker-compose up -d
   ```

2. **Start Backend**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   python main.py
   ```

3. **Start Frontend**:
   ```bash
   cd sandbox/frontend
   npm install
   npm run dev
   ```

4. **Access Dashboard**:
   - Open browser: http://localhost:5173
   - Default view: Monitor tab (left panel)
   - Switch to VNC tab to see remote desktop

### Using the Monitor

**Status Cards**: Quickly check container health and active services.

**Resource Bars**: Monitor CPU, memory, and disk usage in real-time.
- Green bar: CPU usage
- Blue bar: Memory usage
- Orange bar: Disk usage

**MCP Servers**:
- Green dot (●) = Running
- Red dot (●) = Stopped/Fatal
- Click to see PID and uptime

**Process List**:
- Automatically sorted by CPU usage
- Shows top 10 processes
- Updates every 5 seconds

**Logs**:
- Scrollable log viewer
- Last 50 lines from supervisord
- Useful for debugging MCP server issues

### Using VNC

1. Click **🖥️ VNC** tab in left panel
2. Click **Connect** button
3. View remote desktop in real-time
4. Click **Disconnect** when done

## Monitoring Use Cases

### 1. Check System Health
**Scenario**: Ensure sandbox is running properly before starting work.

**Steps**:
1. Open dashboard (monitor tab)
2. Check status cards: Container = "Running", MCP Servers > 0
3. Verify resource bars: CPU < 80%, Memory < 80%
4. Confirm MCP servers have green dots

**Expected Result**: All green indicators, low resource usage.

### 2. Debug MCP Server Issues
**Scenario**: AI Agent can't execute commands.

**Steps**:
1. Open monitor tab
2. Check MCP Servers section for red dots
3. Scroll to logs section
4. Look for error messages (e.g., "FATAL", "ERROR")
5. Restart container if needed: `docker-compose restart`

**Expected Result**: Identify which MCP server failed and why.

### 3. Monitor Resource Usage During AI Tasks
**Scenario**: AI Agent is running heavy computations.

**Steps**:
1. Start AI task in chat panel
2. Switch to monitor tab
3. Watch resource bars update in real-time
4. Check process list for high CPU consumers

**Expected Result**: Identify resource bottlenecks during execution.

### 4. Verify New MCP Installation
**Scenario**: AI Agent just installed a new MCP (e.g., memory MCP).

**Steps**:
1. Install MCP via chat (AI uses `manager_install_mcp`)
2. Restart container: `docker-compose restart`
3. Open monitor tab
4. Check MCP Servers list for new entry
5. Verify new MCP has green dot (running)

**Expected Result**: New MCP appears in list with "RUNNING" status.

### 5. View Logs for Troubleshooting
**Scenario**: AI commands are timing out or failing silently.

**Steps**:
1. Open monitor tab
2. Scroll to logs section
3. Look for recent errors or warnings
4. Note timestamps and error messages
5. Correlate with AI task execution times

**Expected Result**: Identify root cause from log entries.

## Customization

### Adjust Auto-Refresh Interval

Edit [SandboxMonitor.vue](sandbox/frontend/src/components/SandboxMonitor.vue:124):

```javascript
// Change from 5000ms (5 seconds) to 10000ms (10 seconds)
const refreshInterval = 10000
```

### Change Resource Alert Thresholds

Modify progress bar colors in CSS (line 485-497):

```css
/* Example: Change CPU to red if > 80% */
.progress-fill.cpu {
  background: linear-gradient(90deg,
    v-bind('resources.cpu > 80 ? "#f44336" : "#4caf50"'),
    v-bind('resources.cpu > 80 ? "#e57373" : "#8bc34a"')
  );
}
```

### Add More Process Details

Extend `/api/sandbox/processes` endpoint in [backend/main.py](backend/main.py:239):

```python
# Add more fields like status, threads, open files
result = await mcp_manager.call_tool(
    server_name="shell",
    tool_name="execute_command",
    arguments={
        "command": "ps",
        "args": ["aux", "--sort=-pcpu"]  # More detailed output
    }
)
```

### Filter Logs by MCP Server

Modify `/api/sandbox/logs` to accept query parameter:

```python
@app.get("/api/sandbox/logs")
async def get_sandbox_logs(server: str = None):
    if server:
        log_file = f"/var/log/mcp/{server}-stdout.log"
    else:
        log_file = "/var/log/supervisor/supervisord.log"

    # ... rest of implementation
```

## Security Considerations

### 1. Read-Only Operations
All monitoring endpoints use read-only MCP tools:
- `get_mcp_status` (no modifications)
- `get_running_processes` (no modifications)
- `execute_command` with safe commands (`top`, `free`, `df`, `tail`)

### 2. No Sensitive Data Exposure
- Process list doesn't show command arguments (may contain secrets)
- Logs are limited to last 50 lines (prevents log dumping)
- No access to environment variables or config files

### 3. CORS Protection
Backend has CORS middleware configured in [backend/main.py](backend/main.py:56):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Only localhost by default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Rate Limiting (Recommended)
For production, add rate limiting to monitoring endpoints:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/sandbox/status")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def get_sandbox_status():
    # ... implementation
```

## Troubleshooting

### Monitor Shows "Loading..." Forever

**Cause**: Backend is not running or unreachable.

**Solution**:
1. Check backend is running: `curl http://localhost:8000/health`
2. Check console for CORS errors
3. Verify CORS settings in [backend/config.py](backend/config.py)

### MCP Servers Show as "Unknown"

**Cause**: MCP Manager is not running or not responding.

**Solution**:
1. Check container status: `docker ps`
2. Check MCP Manager logs: `docker exec sandbox-sandbox-os-1 supervisorctl status mcp-manager`
3. Restart container: `docker-compose restart`

### Resource Bars Show 0%

**Cause**: Shell MCP failed to execute commands.

**Solution**:
1. Check shell MCP status in monitor
2. Verify commands work manually: `docker exec -i sandbox-sandbox-os-1 top -bn1`
3. Check shell MCP logs: `docker exec sandbox-sandbox-os-1 cat /var/log/mcp/shell-stdout.log`

### Logs Section is Empty

**Cause**: Log file doesn't exist or has no content.

**Solution**:
1. Check log file exists: `docker exec sandbox-sandbox-os-1 ls -la /var/log/supervisor/`
2. Generate logs by triggering supervisord events
3. Check file permissions

### Process List Shows Wrong Processes

**Cause**: Shell MCP returns unexpected format.

**Solution**:
1. Check raw response in browser console
2. Update `parseProcesses()` function in [SandboxMonitor.vue](sandbox/frontend/src/components/SandboxMonitor.vue:138)
3. Adjust parsing logic to match actual output

## Future Enhancements

### Planned Features

1. **WebSocket Live Updates**
   - Replace polling with WebSocket for real-time streaming
   - Reduce latency and server load
   - Enable push notifications for critical events

2. **Historical Charts**
   - Store resource usage history
   - Display CPU/memory graphs over time
   - Identify trends and patterns

3. **Alert System**
   - Set thresholds for CPU, memory, disk
   - Browser notifications when exceeded
   - Email/Slack integration for critical alerts

4. **Process Management UI**
   - Kill process button (with confirmation)
   - View full command line arguments
   - Filter processes by name or CPU%

5. **Log Search and Filtering**
   - Full-text search in logs
   - Filter by log level (INFO, WARN, ERROR)
   - Export logs to file

6. **MCP Server Controls**
   - Start/stop individual MCP servers
   - Restart servers without container restart
   - View detailed server configuration

## Integration with AI Agent

The monitoring dashboard is designed to complement the AI Agent:

**User**: "Check if the sandbox is healthy"
**AI**: *Calls monitoring endpoints* → "Container is running with 3 active MCP servers. CPU usage is 12.3%, memory at 34.5%. All systems normal."

**User**: "What processes are consuming the most CPU?"
**AI**: *Calls `/api/sandbox/processes`* → "Top 3 processes: python (45.2%), chromium (23.1%), node (12.5%)."

**User**: "Show me recent errors in the logs"
**AI**: *Calls `/api/sandbox/logs`* → *Parses logs and filters ERROR lines* → "Found 2 errors: [shows error details]"

The AI can proactively monitor the sandbox and alert users to issues without requiring manual dashboard checks.

## Summary

✅ **Real-Time Monitoring** - Status, resources, processes, MCPs, logs updated every 5s
✅ **Tabbed Interface** - Switch between Monitor and VNC views in left panel
✅ **5 Backend Endpoints** - Complete API for sandbox visibility
✅ **Visual Indicators** - Color-coded status, progress bars, icons
✅ **Auto-Refresh** - No manual reload needed
✅ **Responsive Design** - Dark theme, scrollable sections
✅ **AI Integration Ready** - Endpoints designed for LLM consumption

The Sandbox Monitoring Dashboard provides comprehensive visibility into the sandbox environment, enabling both human users and AI agents to monitor health, diagnose issues, and ensure smooth operation.

---

**Created**: 2026-01-21
**Author**: Manus AI Sandbox Team
**Version**: 1.0.0
