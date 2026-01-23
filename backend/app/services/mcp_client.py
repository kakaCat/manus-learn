"""MCP Client wrapper for connecting to sandbox MCP servers."""

import asyncio
import logging
from typing import Any, Dict, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.config import settings

logger = logging.getLogger(__name__)


class MCPClientManager:
    """Manages connections to multiple MCP servers in the sandbox."""

    def __init__(self):
        """Initialize the MCP client manager."""
        self.sessions: Dict[str, ClientSession] = {}
        self.context_managers: Dict[
            str, Any
        ] = {}  # Store context managers to keep connections alive
        self.servers = {
            "shell": f"{settings.mcp_servers_dir}/shell_mcp/server.py",
            "filesystem": "@modelcontextprotocol/server-filesystem",  # Official Filesystem MCP
            "chrome": "chrome-devtools-mcp",  # Official Chrome DevTools MCP
            "manager": f"{settings.mcp_servers_dir}/mcp_manager/server.py",  # MCP Manager (Meta-MCP)
        }
        self.server_types = {
            "shell": "python",
            "filesystem": "node",  # Node.js server
            "chrome": "node",  # Node.js server
            "manager": "python",  # MCP Manager server
        }
        self.server_args = {
            "filesystem": ["/root/shared/workspace"],  # Restrict to workspace
        }

    async def connect_server(self, server_name: str) -> ClientSession:
        """
        Connect to a specific MCP server.

        Args:
            server_name: Name of the server (shell, filesystem, chrome)

        Returns:
            ClientSession instance

        Raises:
            ValueError: If server_name is unknown
        """
        if server_name not in self.servers:
            logger.error(f"❌ Unknown server requested: {server_name}")
            raise ValueError(f"Unknown server: {server_name}")

        if server_name in self.sessions:
            logger.info(f"✓ Reusing existing session for {server_name}")
            return self.sessions[server_name]

        logger.info(f"🔌 Connecting to {server_name} MCP server...")

        server_path = self.servers[server_name]
        server_type = self.server_types.get(server_name, "python")
        extra_args = self.server_args.get(server_name, [])

        # Configure stdio server parameters for docker exec
        if server_type == "python":
            # Python-based MCP server
            server_params = StdioServerParameters(
                command="docker",
                args=[
                    "exec",
                    "-i",
                    "-e",
                    f"PYTHONPATH={settings.mcp_servers_dir}",
                    settings.sandbox_container_name,
                    settings.mcp_python_path,
                    server_path,
                ],
            )
            logger.debug(
                f"  Python server command: docker exec -i {settings.sandbox_container_name} {settings.mcp_python_path} {server_path}"
            )
        elif server_type == "node":
            # Node.js-based MCP server
            # For official npm packages, use npx
            if server_path.startswith("@") or "/" not in server_path:
                # Official package like @modelcontextprotocol/server-filesystem
                base_args = [
                    "exec",
                    "-i",
                    settings.sandbox_container_name,
                    "/usr/bin/npx",
                    "-y",
                    server_path,
                ]
                # Add extra args (like workspace path for filesystem)
                base_args.extend(extra_args)

                server_params = StdioServerParameters(
                    command="docker",
                    args=base_args,
                )
                logger.debug(
                    f"  Node.js server command: docker exec -i {settings.sandbox_container_name} /usr/bin/npx -y {server_path} {' '.join(extra_args)}"
                )
            else:
                # Custom Node.js server with full path
                server_params = StdioServerParameters(
                    command="docker",
                    args=[
                        "exec",
                        "-i",
                        "-e",
                        "DISPLAY=:1",
                        settings.sandbox_container_name,
                        "/usr/bin/node",
                        f"/usr/lib/node_modules/{server_path}/build/src/index.js",
                    ]
                    + extra_args,
                )
                logger.debug(
                    f"  Custom Node.js server command: docker exec -i {settings.sandbox_container_name} /usr/bin/node /usr/local/lib/node_modules/{server_path}/build/index.js"
                )
        else:
            logger.error(f"❌ Unknown server type: {server_type}")
            raise ValueError(f"Unknown server type: {server_type}")

        try:
            # Connect to server - IMPORTANT: Keep context manager reference alive!
            logger.debug(f"  Opening stdio connection...")
            stdio_ctx = stdio_client(server_params)
            read, write = await stdio_ctx.__aenter__()

            # Store context manager to prevent connection from closing
            self.context_managers[server_name] = stdio_ctx

            logger.debug(f"  Creating client session...")
            session = ClientSession(read, write)
            await session.__aenter__()

            # Initialize session
            logger.debug(f"  Initializing session...")
            await session.initialize()

            # Store session
            self.sessions[server_name] = session

            logger.info(f"✅ Successfully connected to {server_name} MCP server")

            return session

        except Exception as e:
            logger.error(f"❌ Failed to connect to {server_name} MCP server")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error message: {str(e)}")
            import traceback

            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            raise

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """
        Call a tool on a specific MCP server.

        Args:
            server_name: Name of the server (shell, filesystem, chrome)
            tool_name: Name of the tool to call
            arguments: Tool arguments as dictionary

        Returns:
            Tool result

        Raises:
            ValueError: If server or tool is unknown
            Exception: If tool execution fails
        """
        logger.info(f"🔧 Calling tool: {server_name}.{tool_name}")
        logger.debug(f"   Arguments: {arguments}")

        try:
            # Get or create session
            session = await self.connect_server(server_name)

            # Call tool with timeout
            logger.debug(f"   Executing tool...")
            timeout_seconds = 30  # Default timeout

            # Adjust timeouts based on operation type
            if "browser" in tool_name.lower() or server_name == "chrome":
                if "screenshot" in tool_name.lower():
                    timeout_seconds = (
                        120  # 2 minutes for screenshots (pages need time to load)
                    )
                elif "navigate" in tool_name.lower():
                    timeout_seconds = 60  # 1 minute for navigation
                else:
                    timeout_seconds = 300  # 5 minutes for other browser ops
            elif "shell" in server_name and (
                "run" in tool_name.lower() or "execute" in tool_name.lower()
            ):
                timeout_seconds = 120  # 2 minutes for shell commands
            elif "filesystem" in server_name:
                timeout_seconds = 60  # 1 minute for file operations

            logger.debug(
                f"   Timeout set to {timeout_seconds}s for {server_name}.{tool_name}"
            )

            try:
                result = await asyncio.wait_for(
                    session.call_tool(tool_name, arguments), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"⏰ Tool {server_name}.{tool_name} timed out after {timeout_seconds}s"
                )
                raise Exception(
                    f"Tool execution timed out after {timeout_seconds} seconds"
                )

            logger.info(f"✅ Tool {server_name}.{tool_name} completed successfully")
            logger.debug(f"   Result type: {type(result)}")
            logger.debug(f"   Result: {result}")

            return result

        except Exception as e:
            logger.error(f"❌ Tool {server_name}.{tool_name} failed")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error message: {str(e)}")
            import traceback

            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            raise

    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """
        List available tools on a specific MCP server.

        Args:
            server_name: Name of the server

        Returns:
            List of tool definitions
        """
        session = await self.connect_server(server_name)
        tools_response = await session.list_tools()
        return tools_response.tools

    async def close_all(self):
        """Close all active sessions and context managers."""
        logger.info("Closing all MCP sessions...")

        for server_name, session in self.sessions.items():
            try:
                await session.__aexit__(None, None, None)
                logger.info(f"Closed session for {server_name}")
            except Exception as e:
                logger.error(f"Error closing {server_name} session: {e}")

        # Close stdio context managers
        for server_name, ctx in self.context_managers.items():
            try:
                await ctx.__aexit__(None, None, None)
                logger.info(f"Closed stdio context for {server_name}")
            except Exception as e:
                logger.error(f"Error closing {server_name} stdio context: {e}")

        self.sessions.clear()
        self.context_managers.clear()


# Global MCP client manager instance
mcp_manager = MCPClientManager()
