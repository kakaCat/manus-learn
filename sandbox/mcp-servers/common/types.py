"""Common type definitions for MCP servers."""

from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass


class ErrorCode(Enum):
    """Standard error codes for MCP tool results."""
    SUCCESS = 0
    INVALID_INPUT = 1
    PERMISSION_DENIED = 2
    NOT_FOUND = 3
    TIMEOUT = 4
    EXECUTION_ERROR = 5
    SECURITY_VIOLATION = 6
    INTERNAL_ERROR = 99


@dataclass
class ToolResult:
    """
    Standardized result format for MCP tool execution.

    Attributes:
        success: Whether the operation succeeded
        data: Result data (command output, file content, etc.)
        error: Error message if operation failed
        error_code: Standard error code
        metadata: Additional metadata (execution time, file size, etc.)
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: ErrorCode = ErrorCode.SUCCESS
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP response."""
        result = {
            "success": self.success,
        }

        if self.data is not None:
            result["data"] = self.data

        if self.error is not None:
            result["error"] = self.error
            result["error_code"] = self.error_code.value

        if self.metadata is not None:
            result["metadata"] = self.metadata

        return result


@dataclass
class CommandResult:
    """Result of a shell command execution."""
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float


@dataclass
class FileInfo:
    """Information about a file or directory."""
    name: str
    path: str
    type: str  # 'file', 'directory', 'symlink', etc.
    size: int  # in bytes
    modified: str  # ISO format timestamp
    created: str  # ISO format timestamp
    permissions: str  # e.g., 'rwxr-xr-x'


@dataclass
class ProcessInfo:
    """Information about a running process."""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    username: str
