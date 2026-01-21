"""Shell MCP Server - Provides safe shell command execution."""

import os
import sys
import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from common.logging_config import setup_logging
from shell_mcp.config import SERVER_NAME, SERVER_VERSION, LOG_LEVEL
from shell_mcp.tools import (
    execute_command,
    execute_shell_script,
    get_running_processes,
    kill_process
)

# Set up logging
logger = setup_logging(SERVER_NAME, LOG_LEVEL)

# Create MCP server
app = Server(SERVER_NAME)

logger.info(f"Initializing {SERVER_NAME} v{SERVER_VERSION}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="execute_command",
            description="Execute a shell command safely with timeout. Commands must be in the allowed list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute (must be in allowed list: ls, cat, echo, python3, node, git, etc.)"
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Command arguments (optional)"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (default: /root/shared/workspace)",
                        "default": "/root/shared/workspace"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 60, max: 300)",
                        "default": 60,
                        "minimum": 1,
                        "maximum": 300
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="execute_shell_script",
            description="Execute a bash script safely. Script is written to a temporary file and executed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "Shell script content to execute"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (default: /root/shared/workspace)",
                        "default": "/root/shared/workspace"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 60, max: 300)",
                        "default": 60,
                        "minimum": 1,
                        "maximum": 300
                    }
                },
                "required": ["script"]
            }
        ),
        Tool(
            name="get_running_processes",
            description="Get list of all running processes with CPU and memory usage.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="kill_process",
            description="Kill a process by PID. Cannot kill supervisord or system processes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pid": {
                        "type": "integer",
                        "description": "Process ID to kill"
                    },
                    "signal_name": {
                        "type": "string",
                        "description": "Signal to send (SIGTERM, SIGKILL, etc.)",
                        "default": "SIGTERM",
                        "enum": ["SIGTERM", "SIGKILL", "SIGINT", "SIGHUP"]
                    }
                },
                "required": ["pid"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    try:
        if name == "execute_command":
            result = await execute_command(
                command=arguments["command"],
                args=arguments.get("args"),
                cwd=arguments.get("cwd", "/root/shared/workspace"),
                timeout=arguments.get("timeout", 60)
            )
            return [TextContent(
                type="text",
                text=f"Command executed successfully\n\n"
                     f"Exit code: {result['exit_code']}\n"
                     f"Execution time: {result['execution_time']:.2f}s\n\n"
                     f"STDOUT:\n{result['stdout']}\n\n"
                     f"STDERR:\n{result['stderr']}"
            )]

        elif name == "execute_shell_script":
            result = await execute_shell_script(
                script=arguments["script"],
                cwd=arguments.get("cwd", "/root/shared/workspace"),
                timeout=arguments.get("timeout", 60)
            )
            return [TextContent(
                type="text",
                text=f"Script executed successfully\n\n"
                     f"Exit code: {result['exit_code']}\n"
                     f"Execution time: {result['execution_time']:.2f}s\n\n"
                     f"STDOUT:\n{result['stdout']}\n\n"
                     f"STDERR:\n{result['stderr']}"
            )]

        elif name == "get_running_processes":
            processes = await get_running_processes()
            # Format as table
            output = f"Found {len(processes)} running processes:\n\n"
            output += f"{'PID':<8} {'Name':<20} {'Status':<12} {'CPU%':<8} {'Mem%':<8} {'User':<12}\n"
            output += "-" * 80 + "\n"
            for proc in processes[:50]:  # Limit to first 50
                output += (
                    f"{proc['pid']:<8} "
                    f"{proc['name']:<20} "
                    f"{proc['status']:<12} "
                    f"{proc['cpu_percent']:<8.1f} "
                    f"{proc['memory_percent']:<8.1f} "
                    f"{proc['username']:<12}\n"
                )
            if len(processes) > 50:
                output += f"\n... and {len(processes) - 50} more processes"
            return [TextContent(type="text", text=output)]

        elif name == "kill_process":
            result = await kill_process(
                pid=arguments["pid"],
                signal_name=arguments.get("signal_name", "SIGTERM")
            )
            return [TextContent(
                type="text",
                text=f"Process killed successfully\n{result['message']}"
            )]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool execution failed: {name}, error: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Main entry point for the server."""
    logger.info(f"Starting {SERVER_NAME} server...")

    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    # Run the server
    asyncio.run(main())
