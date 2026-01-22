"""Sandbox-related data models."""

from pydantic import BaseModel


class SandboxStatus(BaseModel):
    """Sandbox status response model."""
    status: str
    container: str | None = None
    mcp_status: str | None = None
    installed_mcps: str | None = None
    timestamp: float | None = None
    error: str | None = None


class ProcessListResponse(BaseModel):
    """Process list response model."""
    status: str
    processes: str | None = None
    timestamp: float | None = None
    error: str | None = None


class ResourceUsageResponse(BaseModel):
    """Resource usage response model."""
    status: str
    resources: str | None = None
    timestamp: float | None = None
    error: str | None = None


class LogsResponse(BaseModel):
    """Logs response model."""
    status: str
    logs: str | None = None
    timestamp: float | None = None
    error: str | None = None


class MarketplaceResponse(BaseModel):
    """MCP marketplace response model."""
    status: str
    marketplace: str | None = None
    timestamp: float | None = None
    error: str | None = None
