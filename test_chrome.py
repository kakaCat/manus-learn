#!/usr/bin/env python3
"""Test Chrome MCP new_page tool."""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from mcp_client import mcp_manager


async def test_chrome_new_page():
    """Test creating a new Chrome page."""
    print("Testing Chrome new_page tool...")

    try:
        # Call new_page tool
        result = await mcp_manager.call_tool(
            server_name="chrome", tool_name="new_page", arguments={}
        )

        print(f"✅ new_page result: {result}")

        # List pages to see if it worked
        pages_result = await mcp_manager.call_tool(
            server_name="chrome", tool_name="list_pages", arguments={}
        )

        print(f"✅ list_pages result: {pages_result}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await mcp_manager.close_all()


if __name__ == "__main__":
    asyncio.run(test_chrome_new_page())
