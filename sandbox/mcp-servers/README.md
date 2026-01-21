# MCP Tool Servers for Sandbox Environment

This directory contains three MCP (Model Context Protocol) servers that enable AI agents to interact with the Docker sandbox environment:

1. **Shell MCP** - Safe command execution
2. **Filesystem MCP** - File and directory operations
3. **Chrome MCP** - Browser automation via Chrome DevTools Protocol

## Architecture

```
Docker Container (sandbox-os)
├── Existing VNC Services
│   ├── Xvfb (display :1)
│   ├── x11vnc (port 5900)
│   ├── websockify (port 6080)
│   └── Fluxbox window manager
└── MCP Servers (managed by supervisord)
    ├── shell-mcp (command execution)
    ├── filesystem-mcp (file operations)
    └── chrome-mcp (browser automation)
```

## Directory Structure

```
mcp-servers/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── common/                     # Shared utilities
│   ├── __init__.py
│   ├── logging_config.py       # Stderr logging setup
│   ├── security.py             # Input validation
│   └── types.py                # Common types
├── shell_mcp/                  # Shell command execution
│   ├── __init__.py
│   ├── server.py               # MCP server
│   ├── tools.py                # Tool implementations
│   └── config.py               # Configuration
├── filesystem_mcp/             # Filesystem operations
│   ├── __init__.py
│   ├── server.py
│   ├── tools.py
│   └── config.py
└── chrome_mcp/                 # Browser automation
    ├── __init__.py
    ├── server.py
    ├── tools.py
    ├── cdp_client.py           # CDP wrapper
    └── config.py
```

## MCP Servers

### 1. Shell MCP Server

**Purpose:** Execute shell commands safely within the sandbox.

**Available Tools:**
- `execute_command` - Run commands from allowed list (ls, cat, echo, python3, node, git, etc.)
- `execute_shell_script` - Execute bash scripts in temporary files
- `get_running_processes` - List all running processes with stats
- `kill_process` - Terminate processes (except supervisord and system processes)

**Security Features:**
- Command whitelist (only approved commands allowed)
- Command blacklist (forbidden: rm, dd, sudo, etc.)
- Working directory restriction (/root/shared/workspace)
- Timeout enforcement (max 60s per command)
- No shell=True (prevents command injection)

### 2. Filesystem MCP Server

**Purpose:** Provide safe file and directory operations.

**Available Tools:**
- `read_file` - Read text files (max 10MB)
- `write_file` - Write content to files
- `list_directory` - List files and directories (recursive option)
- `search_files` - Search using glob patterns
- `create_directory` - Create directories with parents
- `delete_file` - Delete files/directories (recursive option)
- `move_file` - Move or rename files
- `get_file_info` - Get file metadata (size, permissions, timestamps)

**Security Features:**
- Root directory restriction (only /root/shared/workspace)
- Path traversal prevention
- File size limits (10MB per operation)
- Binary file detection
- All operations logged

### 3. Chrome MCP Server

**Purpose:** Enable browser automation and web scraping.

**Available Tools:**
- `launch_browser` - Start Chrome with CDP (headless or visible in VNC)
- `close_browser` - Cleanup browser resources
- `navigate_to_url` - Navigate to URLs (with security checks)
- `get_page_content` - Extract HTML and text from page
- `click_element` - Click elements by CSS selector
- `type_text` - Type into input fields
- `wait_for_element` - Wait for elements to appear
- `take_screenshot` - Capture screenshots to /root/shared/workspace/screenshots/
- `execute_javascript` - Run JS in page context

**Security Features:**
- URL blocklist (no localhost, private IPs, file://)
- Max tabs limit (5 concurrent)
- Page load timeout (30 seconds)
- JavaScript timeout (10 seconds)
- Downloads restricted to /root/shared/workspace/downloads/

## Running in Docker

The MCP servers run automatically via supervisord when the Docker container starts.

### Check Server Status

```bash
# Enter the container
docker exec -it sandbox-os bash

# Check status of all services
supervisorctl status

# View MCP server logs
tail -f /var/log/mcp/shell-stderr.log
tail -f /var/log/mcp/filesystem-stderr.log
tail -f /var/log/mcp/chrome-stderr.log
```

### Restart MCP Servers

```bash
# Restart individual server
docker exec sandbox-os supervisorctl restart mcp-shell

# Restart all MCP servers
docker exec sandbox-os supervisorctl restart mcp-shell mcp-filesystem mcp-chrome
```

## Testing MCP Servers

### Using docker exec with stdio transport

The recommended way to connect to MCP servers from the host machine:

```python
# test_mcp.py
import subprocess
import json

def test_shell_mcp():
    cmd = [
        'docker', 'exec', '-i', 'sandbox-os',
        '/opt/mcp-servers/venv/bin/python',
        '/opt/mcp-servers/shell_mcp/server.py'
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Send MCP initialize request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }

    proc.stdin.write(json.dumps(request) + '\n')
    proc.stdin.flush()

    response = proc.stdout.readline()
    print("Response:", response)

    proc.terminate()

if __name__ == "__main__":
    test_shell_mcp()
```

## Future Backend Integration

When implementing the AI agent backend (LangChain + Ollama), connect to MCP servers using the MCP Python SDK:

```python
# backend/mcp_client.py (FUTURE)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class SandboxMCPClient:
    async def connect_shell_mcp(self):
        server_params = StdioServerParameters(
            command="docker",
            args=[
                "exec", "-i", "sandbox-os",
                "/opt/mcp-servers/venv/bin/python",
                "/opt/mcp-servers/shell_mcp/server.py"
            ]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Call tools
                result = await session.call_tool(
                    "execute_command",
                    {"command": "ls", "args": ["-la"]}
                )
                return result
```

## Security Best Practices

1. **Input Validation** - All inputs are validated before execution
2. **Path Restrictions** - Filesystem operations limited to workspace
3. **Command Whitelist** - Only approved commands can be executed
4. **Timeout Enforcement** - All operations have timeouts
5. **Audit Logging** - All operations logged to stderr
6. **No Privileged Operations** - No sudo or system-level access
7. **URL Filtering** - Chrome blocked from accessing private networks

## Troubleshooting

### MCP Server Won't Start

```bash
# Check logs
docker exec sandbox-os cat /var/log/mcp/shell-stderr.log

# Check if Python and dependencies are installed
docker exec sandbox-os /opt/mcp-servers/venv/bin/python --version
docker exec sandbox-os /opt/mcp-servers/venv/bin/pip list
```

### Chrome Won't Launch

```bash
# Check if Chrome is installed
docker exec sandbox-os chromium-browser --version

# Check if Xvfb is running
docker exec sandbox-os ps aux | grep Xvfb

# Test Chrome manually
docker exec -e DISPLAY=:1 sandbox-os chromium-browser --no-sandbox
```

### Path Traversal Errors

```bash
# Verify workspace directory exists
docker exec sandbox-os ls -la /root/shared/workspace/

# Check file permissions
docker exec sandbox-os ls -la /root/shared/
```

## Development

### Modifying MCP Servers

1. Edit files in `sandbox/mcp-servers/` on host machine
2. Changes are reflected immediately via volume mount
3. Restart the affected MCP server:
   ```bash
   docker exec sandbox-os supervisorctl restart mcp-shell
   ```

### Adding New Tools

1. Add tool implementation in `tools.py`
2. Register tool in `server.py` `list_tools()` method
3. Add call handler in `server.py` `call_tool()` method
4. Update security validation in `common/security.py` if needed
5. Restart the server

## Resources

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [Supervisor Documentation](http://supervisord.org/)
