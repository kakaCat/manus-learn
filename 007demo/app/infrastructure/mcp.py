import asyncio
from typing import List, Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, create_model, Field
from contextlib import AsyncExitStack

class MCPClientManager:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """Connect to all MCP servers."""
        # Shell MCP
        await self._connect_server(
            "shell",
            "docker",
            [
                "exec",
                "-i",
                "-e",
                "NODE_ENV=production",
                "-e",
                "LOG_LEVEL=error",
                "sandbox-shell-mcp",
                "node",
                "/usr/lib/node_modules/@kevinwatt/shell-mcp/build/index.js",
            ],
        )

        # Filesystem MCP
        await self._connect_server(
            "filesystem",
            "docker",
            [
                "exec",
                "-i",
                "-e",
                "NODE_ENV=production",
                "-e",
                "LOG_LEVEL=error",
                "sandbox-shell-mcp",
                "npx",
                "-y",
                "@modelcontextprotocol/server-filesystem",
                "/root/shared/workspace",
            ],
        )

        # Chrome MCP
        await self._connect_server(
            "chrome",
            "docker",
            [
                "exec",
                "-i",
                "-e",
                "NODE_ENV=production",
                "-e",
                "LOG_LEVEL=error",
                "sandbox-shell-mcp",
                "node",
                "/usr/lib/node_modules/chrome-devtools-mcp/build/src/index.js",
                "--browserUrl",
                "http://127.0.0.1:9222",
            ],
        )

    async def _connect_server(self, name: str, command: str, args: List[str]):
        print(f"🔌 Connecting to {name} MCP server...")
        server_params = StdioServerParameters(command=command, args=args, env=None)

        try:
            # We need to keep the context managers alive
            stdio_ctx = stdio_client(server_params)
            read, write = await self.exit_stack.enter_async_context(stdio_ctx)

            session = ClientSession(read, write)
            await self.exit_stack.enter_async_context(session)

            await session.initialize()
            self.sessions[name] = session
            print(f"✅ Connected to {name}")
        except Exception as e:
            print(f"❌ Failed to connect to {name}: {e}")

    async def get_tools(self, server_name: str) -> List[StructuredTool]:
        if server_name not in self.sessions:
            return []

        session = self.sessions[server_name]
        mcp_tools = await session.list_tools()

        langchain_tools = []
        for tool in mcp_tools.tools:
            langchain_tools.append(self._convert_tool(tool, session))

        return langchain_tools

    def _convert_tool(self, tool_info: Any, session: ClientSession) -> StructuredTool:
        """Convert MCP tool to LangChain StructuredTool."""

        async def _tool_func(**kwargs):
            try:
                result = await session.call_tool(tool_info.name, kwargs)
                # MCP returns a list of content (TextContent or ImageContent)
                # We concatenate text content for LLM
                output = []
                for content in result.content:
                    if content.type == "text":
                        output.append(content.text)
                    elif content.type == "image":
                        output.append(
                            f"[Image: {content.mimeType}]"
                        )  # We can't pass image data easily to text-only LLM yet

                full_output = "\n".join(output)
                if len(full_output) > 20000:
                    return (
                        full_output[:20000] + "\n... (Output truncated due to length)"
                    )
                return full_output
            except Exception as e:
                return f"Error executing {tool_info.name}: {e}"

        # Create Pydantic model for arguments
        fields = {}
        if hasattr(tool_info, "inputSchema") and "properties" in tool_info.inputSchema:
            for name, schema in tool_info.inputSchema["properties"].items():
                # Simplified type mapping
                type_map = {
                    "string": str,
                    "integer": int,
                    "number": float,
                    "boolean": bool,
                    "array": list,
                    "object": dict,
                }
                py_type = type_map.get(schema.get("type", "string"), str)
                description = schema.get("description", "")

                # Check if required
                required = name in tool_info.inputSchema.get("required", [])
                if required:
                    fields[name] = (py_type, Field(description=description))
                else:
                    fields[name] = (
                        Optional[py_type],
                        Field(default=None, description=description),
                    )

        ArgsModel = create_model(f"{tool_info.name}Args", **fields)

        return StructuredTool.from_function(
            func=None,
            coroutine=_tool_func,
            name=tool_info.name,
            description=tool_info.description,
            args_schema=ArgsModel,
        )

    async def close(self):
        await self.exit_stack.aclose()
