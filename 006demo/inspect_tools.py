import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def list_tools():
    # Chrome MCP
    server_params = StdioServerParameters(
        command="docker",
        args=[
            "exec", "-i",
            "sandbox-shell-mcp",
            "node", "/usr/lib/node_modules/chrome-devtools-mcp/build/src/index.js",
            "--browserUrl", "http://127.0.0.1:9222"
        ],
        env=None
    )

    print("🔌 Connecting to Chrome MCP...")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools = await session.list_tools()
                print("\n🌐 Chrome Tools:")
                for t in tools.tools:
                    print(f"- {t.name}: {t.description}")
                    
    except Exception as e:
        print(f"❌ Chrome Error: {e}")

    # Filesystem MCP
    server_params_fs = StdioServerParameters(
        command="docker",
        args=[
            "exec", "-i",
            "sandbox-shell-mcp",
            "npx", "-y", "@modelcontextprotocol/server-filesystem",
            "/root/shared/workspace"
        ],
        env=None
    )
    
    print("\n🔌 Connecting to Filesystem MCP...")
    try:
        async with stdio_client(server_params_fs) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools = await session.list_tools()
                print("\n📁 Filesystem Tools:")
                for t in tools.tools:
                    print(f"- {t.name}: {t.description}")

    except Exception as e:
        print(f"❌ Filesystem Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_tools())
