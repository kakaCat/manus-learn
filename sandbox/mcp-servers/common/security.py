"""Security utilities for MCP servers.

Provides input validation and sanitization functions to prevent:
- Path traversal attacks
- Command injection
- Unauthorized access
- URL-based attacks
"""

import os
import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse


# Workspace root - all filesystem operations must be within this directory
WORKSPACE_ROOT = Path("/root/shared/workspace")

# Command whitelist - allowed commands for shell execution
ALLOWED_COMMANDS = {
    "ls", "cat", "echo", "pwd", "whoami", "date", "hostname",
    "python3", "node", "npm", "npx", "git",
    "touch", "mkdir", "cp", "mv",
    "grep", "find", "head", "tail", "wc",
    "xterm", "chromium-browser"
}

# Command blacklist - explicitly forbidden commands
FORBIDDEN_COMMANDS = {
    "rm", "dd", "mkfs", "fdisk", "parted",
    "sudo", "su", "chown", "chmod", "chgrp",
    "shutdown", "reboot", "halt", "poweroff",
    "kill", "killall", "pkill"
}

# URL blocklist patterns (regex)
BLOCKED_URL_PATTERNS = [
    r'^file://.*',                          # Local files
    r'^http://localhost.*',                 # Localhost
    r'^http://127\.0\.0\.1.*',             # Loopback
    r'^http://10\..*',                      # Private network 10.x.x.x
    r'^http://172\.(1[6-9]|2[0-9]|3[01])\..*',  # Private network 172.16-31.x.x
    r'^http://192\.168\..*',                # Private network 192.168.x.x
    r'^https://localhost.*',
    r'^https://127\.0\.0\.1.*',
]


def validate_path(path: str, must_exist: bool = False) -> Path:
    """
    Validate and resolve a filesystem path.

    Args:
        path: Path to validate (relative or absolute)
        must_exist: If True, raise error if path doesn't exist

    Returns:
        Resolved absolute Path object

    Raises:
        ValueError: If path is outside workspace or contains traversal attempts
        FileNotFoundError: If must_exist=True and path doesn't exist
    """
    # Convert to Path object and make absolute
    if os.path.isabs(path):
        full_path = Path(path)
    else:
        full_path = WORKSPACE_ROOT / path

    # Resolve to absolute path (handles .., symlinks, etc.)
    try:
        resolved_path = full_path.resolve()
    except (RuntimeError, OSError) as e:
        raise ValueError(f"Invalid path: {path}") from e

    # Check if path is within workspace
    if not str(resolved_path).startswith(str(WORKSPACE_ROOT)):
        raise ValueError(
            f"Path traversal detected: {path} resolves to {resolved_path}, "
            f"which is outside workspace {WORKSPACE_ROOT}"
        )

    # Check existence if required
    if must_exist and not resolved_path.exists():
        raise FileNotFoundError(f"Path does not exist: {resolved_path}")

    return resolved_path


def is_path_safe(path: str) -> bool:
    """
    Check if a path is safe (quick check without raising exceptions).

    Args:
        path: Path to check

    Returns:
        True if path is safe, False otherwise
    """
    try:
        validate_path(path, must_exist=False)
        return True
    except (ValueError, FileNotFoundError):
        return False


def validate_command(command: str, args: Optional[List[str]] = None) -> None:
    """
    Validate a shell command before execution.

    Args:
        command: Command to execute
        args: Command arguments (optional)

    Raises:
        ValueError: If command is not allowed or contains suspicious patterns
    """
    # Check if command is in forbidden list
    if command in FORBIDDEN_COMMANDS:
        raise ValueError(f"Command '{command}' is forbidden")

    # Check if command is in allowed list
    if command not in ALLOWED_COMMANDS:
        raise ValueError(
            f"Command '{command}' is not in the allowed list. "
            f"Allowed commands: {', '.join(sorted(ALLOWED_COMMANDS))}"
        )

    # Check for suspicious patterns in command
    suspicious_patterns = [
        r'[;&|`$]',  # Shell metacharacters
        r'\$\(',     # Command substitution
        r'>\s*/dev', # Writing to device files
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, command):
            raise ValueError(f"Command contains suspicious pattern: {pattern}")

    # Check arguments for suspicious content
    if args:
        for arg in args:
            # Check for command injection attempts
            if any(char in arg for char in [';', '&', '|', '`', '$', '\n']):
                raise ValueError(f"Argument contains suspicious characters: {arg}")


def is_command_allowed(command: str) -> bool:
    """
    Check if a command is allowed (quick check without raising exceptions).

    Args:
        command: Command to check

    Returns:
        True if command is allowed, False otherwise
    """
    try:
        validate_command(command)
        return True
    except ValueError:
        return False


def validate_url(url: str) -> None:
    """
    Validate a URL before navigation.

    Args:
        url: URL to validate

    Raises:
        ValueError: If URL matches blocklist patterns
    """
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL: {url}") from e

    # Check scheme
    if parsed.scheme not in ['http', 'https']:
        raise ValueError(f"URL scheme not allowed: {parsed.scheme}")

    # Check against blocklist patterns
    for pattern in BLOCKED_URL_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            raise ValueError(
                f"URL blocked by security policy: {url} matches pattern {pattern}"
            )


def is_url_allowed(url: str) -> bool:
    """
    Check if a URL is allowed (quick check without raising exceptions).

    Args:
        url: URL to check

    Returns:
        True if URL is allowed, False otherwise
    """
    try:
        validate_url(url)
        return True
    except ValueError:
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove dangerous characters.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')

    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext

    return filename
