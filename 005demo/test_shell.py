import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_shell_operations():
    """Test MCP Shell Server operations."""
    # Configure connection to containerized MCP server
    server_params = StdioServerParameters(
        command="docker",
        args=[
            "exec", "-i",
            "sandbox-shell-mcp",  # Container name from docker-compose.yml
            "node", "/usr/lib/node_modules/@kevinwatt/shell-mcp/build/index.js"
        ],
        env=None
    )

    print("🔌 Connecting to MCP Shell Server...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # List tools
                tools = await session.list_tools()
                print(f"✨ Connected! Found tools: {[t.name for t in tools.tools]}")

                # Test 1: Simple echo
                print("\n📝 Test 1: Echo command")
                result = await session.call_tool("run_command", {
                    "command": "echo 'Hello from MCP Shell!'"
                })
                print(f"Result: {result}")

                # Test 2: Check system info
                print("\n💻 Test 2: System info")
                result = await session.call_tool("run_command", {
                    "command": "uname -a"
                })
                print(f"System Info: {result}")

                # Test 3: Create a file via shell
                print("\n📂 Test 3: Create file via shell")
                await session.call_tool("run_command", {
                    "command": "echo 'Created via shell' > /root/shared/workspace/shell_test.txt"
                })
                
                # Verify file creation
                verify = await session.call_tool("run_command", {
                    "command": "cat /root/shared/workspace/shell_test.txt"
                })
                print(f"File content: {verify}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_shell_operations())
