#!/usr/bin/env python3
"""Test script to verify MCP servers are working correctly."""

import subprocess
import json
import sys

def test_mcp_server(server_name, server_path, server_type="python"):
    """Test an MCP server by sending initialize request."""
    print(f"\n{'='*60}")
    print(f"Testing {server_name}")
    print(f"{'='*60}")

    try:
        # Start MCP server via docker exec
        if server_type == "python":
            cmd = [
                'docker', 'exec', '-i', '-e', 'PYTHONPATH=/opt/mcp-servers',
                'sandbox-sandbox-os-1',
                '/opt/mcp-venv/bin/python',
                server_path
            ]
        elif server_type == "node":
            # Check if it's an npm package (starts with @) or local path
            if server_path.startswith('@'):
                # Official npm package - use npx
                cmd = [
                    'docker', 'exec', '-i',
                    'sandbox-sandbox-os-1',
                    '/usr/bin/npx', '-y',
                    server_path,
                    '/root/shared/workspace'  # For filesystem server
                ]
            else:
                # Local Node.js file
                cmd = [
                    'docker', 'exec', '-i', '-e', 'DISPLAY=:1',
                    'sandbox-sandbox-os-1',
                    '/usr/bin/node',
                    server_path
                ]
        else:
            raise ValueError(f"Unknown server type: {server_type}")

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send MCP initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        # Send request
        proc.stdin.write(json.dumps(init_request) + '\n')
        proc.stdin.flush()

        # Read response (with timeout)
        try:
            response_line = proc.stdout.readline()
            if response_line:
                response = json.loads(response_line)
                print(f"✅ {server_name} responded successfully!")
                print(f"Server info: {response.get('result', {}).get('serverInfo', {})}")

                # Send tools/list request
                list_tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }
                proc.stdin.write(json.dumps(list_tools_request) + '\n')
                proc.stdin.flush()

                tools_response = proc.stdout.readline()
                if tools_response:
                    tools_data = json.loads(tools_response)
                    tools = tools_data.get('result', {}).get('tools', [])
                    print(f"Available tools: {len(tools)}")
                    for tool in tools:
                        print(f"  - {tool.get('name')}: {tool.get('description', '')[:60]}")

                return True
            else:
                print(f"❌ {server_name} did not respond")
                stderr = proc.stderr.read()
                if stderr:
                    print(f"Error: {stderr[:200]}")
                return False

        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

    except Exception as e:
        print(f"❌ Error testing {server_name}: {e}")
        return False

def main():
    """Test all three MCP servers."""
    print("MCP Server Functionality Test")
    print("=" * 60)

    servers = [
        ("Shell MCP", "/opt/mcp-servers/shell_mcp/server.py", "python"),
        ("Filesystem MCP (Official)", "@modelcontextprotocol/server-filesystem", "node"),
        ("Chrome MCP (Official)", "/usr/local/lib/node_modules/chrome-devtools-mcp/build/index.js", "node"),
    ]

    results = {}
    for name, path, server_type in servers:
        results[name] = test_mcp_server(name, path, server_type)

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")

    # Exit code
    if all(results.values()):
        print(f"\n✅ All MCP servers are working correctly!")
        sys.exit(0)
    else:
        print(f"\n❌ Some MCP servers failed tests")
        sys.exit(1)

if __name__ == "__main__":
    main()
