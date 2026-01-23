#!/usr/bin/env python3
"""Simple test script to verify MCP servers are working correctly."""

import subprocess
import json
import sys
import time


def test_shell_mcp():
    """Test Shell MCP server (Official @kevinwatt/shell-mcp)."""
    print("\n" + "=" * 60)
    print("Testing Shell MCP (Official)")
    print("=" * 60)

    cmd = [
        "docker",
        "exec",
        "-i",
        "-e",
        "NODE_ENV=production",
        "sandbox-sandbox-os-1",
        "/usr/bin/node",
        "/usr/lib/node_modules/@kevinwatt/shell-mcp/build/index.js",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        time.sleep(2)  # Wait for npm package to start

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        response = None
        for _ in range(15):
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
            print("✅ Shell MCP (Official) responded successfully!")
            print(f"Server info: {response.get('result', {}).get('serverInfo', {})}")
            proc.terminate()
            return True
        else:
            print("❌ Shell MCP (Official) did not respond")
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
        "docker",
        "exec",
        "-i",
        "sandbox-sandbox-os-1",
        "/usr/bin/npx",
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/root/shared/workspace",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        time.sleep(1)  # Wait for npm to download/start

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
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
            print("✅ Filesystem MCP responded successfully!")
            print(f"Server info: {response.get('result', {}).get('serverInfo', {})}")
            proc.terminate()
            return True
        else:
            print("❌ Filesystem MCP did not respond")
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
        "docker",
        "exec",
        "-i",
        "-e",
        "DISPLAY=:1",
        "-e",
        "NODE_ENV=production",
        "sandbox-sandbox-os-1",
        "/usr/bin/node",
        "/usr/lib/node_modules/chrome-devtools-mcp/build/src/index.js",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        time.sleep(1)

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
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
            print("✅ Chrome MCP responded successfully!")
            print(f"Server info: {response.get('result', {}).get('serverInfo', {})}")
            proc.terminate()
            return True
        else:
            print("❌ Chrome MCP did not respond")
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
        "Shell MCP (Official)": test_shell_mcp(),
        "Filesystem MCP (Official)": test_filesystem_mcp(),
        "Chrome MCP (Official)": test_chrome_mcp(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")

    if all(results.values()):
        print("\n✅ All official MCP servers are working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some MCP servers failed tests")
        sys.exit(1)


if __name__ == "__main__":
    main()
