"""Sandbox monitoring API routes."""

import logging
import asyncio

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.sandbox import (
    SandboxStatus,
    ProcessListResponse,
    ResourceUsageResponse,
    LogsResponse,
    MarketplaceResponse,
)
from app.services.mcp_client import mcp_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


@router.get("/status", response_model=SandboxStatus)
async def get_sandbox_status():
    """
    Get overall sandbox status including MCP servers and container health.

    Returns:
        JSON with MCP server statuses, container info, and health metrics
    """
    try:
        # Get MCP server status
        mcp_status = await mcp_manager.call_tool(
            server_name="manager",
            tool_name="get_mcp_status",
            arguments={}
        )

        # Get installed MCPs
        installed_mcps = await mcp_manager.call_tool(
            server_name="manager",
            tool_name="list_installed_mcps",
            arguments={}
        )

        return SandboxStatus(
            status="running",
            container=settings.sandbox_container_name,
            mcp_status=mcp_status[0].text if mcp_status else "Unknown",
            installed_mcps=installed_mcps[0].text if installed_mcps else "Unknown",
            timestamp=asyncio.get_event_loop().time()
        )
    except Exception as e:
        logger.error(f"Error getting sandbox status: {e}", exc_info=True)
        return SandboxStatus(
            status="error",
            error=str(e)
        )


@router.get("/processes", response_model=ProcessListResponse)
async def get_sandbox_processes():
    """
    Get list of running processes in the sandbox.

    Returns:
        JSON with process list (pid, name, cpu%, memory%)
    """
    try:
        result = await mcp_manager.call_tool(
            server_name="shell",
            tool_name="get_running_processes",
            arguments={}
        )

        return ProcessListResponse(
            status="success",
            processes=result[0].text if result else "No processes found",
            timestamp=asyncio.get_event_loop().time()
        )
    except Exception as e:
        logger.error(f"Error getting processes: {e}", exc_info=True)
        return ProcessListResponse(
            status="error",
            error=str(e)
        )


@router.get("/resources", response_model=ResourceUsageResponse)
async def get_sandbox_resources():
    """
    Get container resource usage (CPU, memory, disk).

    Returns:
        JSON with resource metrics
    """
    try:
        # Execute command to get resource usage
        result = await mcp_manager.call_tool(
            server_name="shell",
            tool_name="execute_command",
            arguments={
                "command": "bash",
                "args": ["-c", "echo 'CPU:'; top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'; echo 'Memory:'; free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2 }'; echo ''; echo 'Disk:'; df -h / | awk 'NR==2{print $5}'"]
            }
        )

        return ResourceUsageResponse(
            status="success",
            resources=result[0].text if result else "Unknown",
            timestamp=asyncio.get_event_loop().time()
        )
    except Exception as e:
        logger.error(f"Error getting resources: {e}", exc_info=True)
        return ResourceUsageResponse(
            status="error",
            error=str(e)
        )


@router.get("/logs", response_model=LogsResponse)
async def get_sandbox_logs():
    """
    Get recent logs from MCP servers.

    Returns:
        JSON with log entries
    """
    try:
        # Read recent logs from supervisord
        result = await mcp_manager.call_tool(
            server_name="shell",
            tool_name="execute_command",
            arguments={
                "command": "tail",
                "args": ["-n", "50", "/var/log/supervisor/supervisord.log"]
            }
        )

        return LogsResponse(
            status="success",
            logs=result[0].text if result else "No logs available",
            timestamp=asyncio.get_event_loop().time()
        )
    except Exception as e:
        logger.error(f"Error getting logs: {e}", exc_info=True)
        return LogsResponse(
            status="error",
            error=str(e)
        )


@router.get("/marketplace", response_model=MarketplaceResponse)
async def get_mcp_marketplace():
    """
    Get list of available MCPs from the marketplace.

    Returns:
        JSON with available MCP tools
    """
    try:
        result = await mcp_manager.call_tool(
            server_name="manager",
            tool_name="list_available_mcps",
            arguments={}
        )

        return MarketplaceResponse(
            status="success",
            marketplace=result[0].text if result else "No MCPs available",
            timestamp=asyncio.get_event_loop().time()
        )
    except Exception as e:
        logger.error(f"Error getting marketplace: {e}", exc_info=True)
        return MarketplaceResponse(
            status="error",
            error=str(e)
        )
