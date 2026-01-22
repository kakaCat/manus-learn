#!/usr/bin/env python3
"""Test script to verify MCP servers are working correctly."""

import subprocess
import json
import sys


def test_mcp_server(server_name, server_path, server_type="python"):
    """Test an MCP server by sending initialize request."""
    print(f"\n{'=' * 60}")
    print(f"Testing {server_name}")
    print(f"{'=' * 60}")

    try:
        # Start MCP server via docker exec
        if server_type == "python":
            cmd = [
                "docker",
                "exec",
                "-i",
                "-e",
                "PYTHONPATH=/opt/mcp-servers",
                "sandbox-sandbox-os-1",
                "/opt/mcp-venv/bin/python",
                server_path,
            ]
        elif server_type == "node":
            # Check if it's an npm package (starts with @) or local path
            if server_path.startswith("@"):
                # Official npm package - use npx
                cmd = [
                    "docker",
                    "exec",
                    "-i",
                    "sandbox-sandbox-os-1",
                    "/usr/bin/npx",
                    "-y",
                    server_path,
                    "/root/shared/workspace",  # For filesystem server
                ]
            else:
                # Local Node.js file
                env_vars = ["-e", "DISPLAY=:1"]
                args = []
                if "chrome" in server_path.lower():
                    # Chrome MCP needs additional environment and browser URL
                    env_vars.extend(["-e", "NODE_ENV=production"])
                    args = ["--browserUrl", "http://127.0.0.1:9222"]
                cmd = (
                    ["docker", "exec", "-i"]
                    + env_vars
                    + ["sandbox-sandbox-os-1", "/usr/bin/node", server_path]
                    + args
                )

    except Exception as e:
        print(f"❌ Error testing {server_name}: {e}")
        return False


def main():
    """Test all three MCP servers."""
    print("MCP Server Functionality Test")
    print("=" * 60)

    servers = [
        ("Shell MCP", "/opt/mcp-servers/shell_mcp/server.py", "python"),
        (
            "Filesystem MCP (Official)",
            "@modelcontextprotocol/server-filesystem",
            "node",
        ),
        (
            "Chrome MCP (Official)",
            "/usr/lib/node_modules/chrome-devtools-mcp/build/src/index.js",
            "node",
        ),
    ]

    results = {}
    for name, path, server_type in servers:
        results[name] = test_mcp_server(name, path, server_type)

    # Summary
    print(f"\n{'=' * 60}")
    print("Test Summary")
    print(f"{'=' * 60}")
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
