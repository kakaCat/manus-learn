"""Logging configuration for MCP servers.

MCP servers using stdio transport MUST log to stderr only.
Stdout is reserved for the MCP protocol JSON-RPC messages.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    name: str,
    level: str = "INFO",
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging for an MCP server.

    Args:
        name: Logger name (typically the server name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string (optional)

    Returns:
        Configured logger instance

    Note:
        All logs are sent to stderr to avoid interfering with stdio transport.
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove any existing handlers
    logger.handlers.clear()

    # Create stderr handler (required for stdio transport)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(getattr(logging, level.upper()))

    # Create formatter
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger
