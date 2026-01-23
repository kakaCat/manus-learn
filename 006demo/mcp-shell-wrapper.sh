#!/bin/bash
# MCP Shell Server Wrapper - Filter debug messages

# Start the MCP shell server with stderr suppressed
exec /usr/bin/node /usr/lib/node_modules/@kevinwatt/shell-mcp/build/index.js 2>/dev/null