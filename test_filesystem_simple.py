#!/usr/bin/env python3
"""Simple test to verify MCP Filesystem Server is working."""

import subprocess
import json
import sys


def test_filesystem_mcp():
    """Test MCP Filesystem Server directly."""
    print("Testing MCP Filesystem Server...")

    try:
        # Test by calling the MCP server directly
        cmd = [
            "docker",
            "exec",
            "-i",
            "sandbox-sandbox-os-1",
            "npx",
            "-y",
            "@modelcontextprotocol/server-filesystem",
            "/root/shared/workspace",
        ]

        print(f"Running command: {' '.join(cmd)}")

        # Start the process
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Send MCP initialize request
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

        # Write the request
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        # Read response
        response_line = proc.stdout.readline()
        print(f"Response: {response_line.strip()}")

        # Try to parse JSON response
        try:
            response = json.loads(response_line.strip())
            if "result" in response:
                print("✅ MCP Filesystem Server initialized successfully!")
                return True
            else:
                print(f"❌ Unexpected response: {response}")
                return False
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {response_line}")
            return False

    except Exception as e:
        print(f"❌ Error testing filesystem MCP: {e}")
        return False


if __name__ == "__main__":
    success = test_filesystem_mcp()
    sys.exit(0 if success else 1)
