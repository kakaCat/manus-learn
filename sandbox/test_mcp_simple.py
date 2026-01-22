#!/usr/bin/env python3
"""Simple test script to verify MCP servers are working correctly."""

import subprocess
import json
import sys
import time


def test_shell_mcp():
    """Test Shell MCP server."""
    print("\n" + "=" * 60)
    print("Testing Shell MCP")
    print("=" * 60)

    cmd = [
        "docker", "exec", "-i",
        "-e", "PYTHONPATH=/opt/mcp-servers",
        "sandbox-sandbox-os-1",
        "/opt/mcp-venv/bin/python",
        "/opt/mcp-servers/shell_mcp/server.py"
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait a bit for server to start
        time.sleep(0.5)

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }

        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        # Read response (skip stderr lines)
        response = None
        for _ in range(10):  # Try up to 10 lines
            line = proc.stdout.readline()
            if not line:
                break
            try:
                data = json.loads(line)
                if "result" in data:
                    response = data
                    break
            except json.JSONDecodeError:
                continue

        if response:
            print(f"✅ Shell MCP responded successfully!")
            print(f"Server info: {response.get('result', {}).get('serverInfo', {})}")

            # Test tools/list
            list_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
            proc.stdin.write(json.dumps(list_request) + "\n")
            proc.stdin.flush()

            for _ in range(10):
                line = proc.stdout.readline()
                if not line:
                    break
                try:
                    data = json.loads(line)
                    if "result" in data:
                        tools = data.get("result", {}).get("tools", [])
                        print(f"Available tools: {len(tools)}")
                        for tool in tools[:5]:  # Show first 5
                            print(f"  - {tool.get('name')}")
                        break
                except json.JSONDecodeError:
                    continue

            proc.terminate()
            return True
        else:
            print(f"❌ Shell MCP did not respond")
            stderr = proc.stderr.read()
            print(f"Stderr: {stderr[:500]}")
            proc.terminate()
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_filesystem_mcp():
    """Test Filesystem MCP server."""
    print("\n" + "=" * 60)
    print("Testing Filesystem MCP (Official)")
    print("=" * 60)

    cmd = [
        "docker", "exec", "-i",
        "sandbox-sandbox-os-1",
        "/usr/bin/npx", "-y",
        "@modelcontextprotocol/server-filesystem",
        "/root/shared/workspace"
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        time.sleep(1)  # Wait for npm to download/start

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }

        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        response = None
        for _ in range(10):
            line = proc.stdout.readline()
            if not line:
                break
            try:
                data = json.loads(line)
                if "result" in data:
                    response = data
                    break
            except json.JSONDecodeError:
                continue

        if response:
            print(f"✅ Filesystem MCP responded successfully!")
            print(f"Server info: {response.get('result', {}).get('serverInfo', {})}")
            proc.terminate()
            return True
        else:
            print(f"❌ Filesystem MCP did not respond")
            stderr = proc.stderr.read()
            print(f"Stderr: {stderr[:500]}")
            proc.terminate()
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chrome_mcp():
    """Test Chrome MCP server."""
    print("\n" + "=" * 60)
    print("Testing Chrome MCP (Official)")
    print("=" * 60)

    cmd = [
        "docker", "exec", "-i",
        "-e", "DISPLAY=:1",
        "-e", "NODE_ENV=production",
        "sandbox-sandbox-os-1",
        "/usr/bin/node",
        "/usr/lib/node_modules/chrome-devtools-mcp/build/src/index.js"
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        time.sleep(0.5)

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }

        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        response = None
        for _ in range(10):
            line = proc.stdout.readline()
            if not line:
                break
            try:
                data = json.loads(line)
                if "result" in data:
                    response = data
                    break
            except json.JSONDecodeError:
                continue

        if response:
            print(f"✅ Chrome MCP responded successfully!")
            print(f"Server info: {response.get('result', {}).get('serverInfo', {})}")
            proc.terminate()
            return True
        else:
            print(f"❌ Chrome MCP did not respond")
            stderr = proc.stderr.read()
            print(f"Stderr: {stderr[:500]}")
            proc.terminate()
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Test all MCP servers."""
    print("MCP Server Functionality Test")
    print("=" * 60)

    results = {
        "Shell MCP": test_shell_mcp(),
        "Filesystem MCP": test_filesystem_mcp(),
        "Chrome MCP": test_chrome_mcp(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")

    if all(results.values()):
        print(f"\n✅ All MCP servers are working correctly!")
        sys.exit(0)
    else:
        print(f"\n❌ Some MCP servers failed tests")
        sys.exit(1)


if __name__ == "__main__":
    main()
