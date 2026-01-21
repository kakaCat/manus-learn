"""Configuration for Shell MCP server."""

import os
from typing import Set

# Server metadata
SERVER_NAME = "shell-mcp"
SERVER_VERSION = "1.0.0"

# Command execution defaults
DEFAULT_TIMEOUT = 60  # seconds
DEFAULT_CWD = "/root/shared/workspace"
MAX_OUTPUT_SIZE = 1024 * 1024  # 1MB

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
