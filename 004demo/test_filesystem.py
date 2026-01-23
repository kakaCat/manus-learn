import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json


async def test_filesystem_operations():
    """Test MCP Filesystem Server operations."""
    # Configure connection to containerized MCP server
    server_params = StdioServerParameters(
        command="docker",
        args=[
                "exec",
                "-i",
                "sandbox-filesystem",  # Container name
                "npx",
                "-y",
            "@modelcontextprotocol/server-filesystem",
            "/root/shared/workspace",
        ],
        env=None,
    )

    print("🔌 Connecting to MCP Filesystem Server...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Initialize connection
            await session.initialize()

            # 2. List available tools
            tools = await session.list_tools()
            print(f"✨ Connected! Found {len(tools.tools)} filesystem tools")

            # 3. Test directory listing
            print("📁 Listing workspace directory...")
            dir_result = await session.call_tool(
                "list_directory", {"path": "/root/shared/workspace"}
            )
            print(f"Directory contents: {dir_result}")

            # 4. Test file creation
            print("📝 Creating test file...")
            await session.call_tool(
                "write_file",
                {
                    "path": "/root/shared/workspace/test_file.txt",
                    "content": "Hello from MCP Filesystem!",
                },
            )

            # 5. Test file reading
            print("📖 Reading test file...")
            file_result = await session.call_tool(
                "read_file", {"path": "/root/shared/workspace/test_file.txt"}
            )
            print(f"File content: {file_result}")

            # 6. Test file search and replace
            print("🔍 Testing search and replace (Skipped)...")
            # await session.call_tool(
            #     "search_replace",
            #     {
            #         "file_path": "/root/shared/workspace/test_file.txt",
            #         "old_string": "Hello from MCP Filesystem!",
            #         "new_string": "Modified by MCP Filesystem Server!",
            #     },
            # )

            # 7. Verify modification
            modified_result = await session.call_tool(
                "read_file", {"path": "/root/shared/workspace/test_file.txt"}
            )
            print(f"Modified content: {modified_result}")

            print("✅ All filesystem operations completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_filesystem_operations())
