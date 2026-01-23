#!/usr/bin/env python3
"""
Simple test of the agent workflow focusing on web search without MCP dependencies.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))


# Mock MCPClientManager to avoid connection issues
class MockMCPClientManager:
    async def connect(self):
        print("Mock MCP connection established")
        return []

    async def get_tools(self, server_name: str):
        print(f"Mock tools for {server_name}: []")
        return []

    async def close(self):
        print("Mock MCP connection closed")


# Monkey patch the MCP client
import agent

agent.MCPClientManager = MockMCPClientManager


async def test_agent_web_search():
    """Test agent with web search query."""
    print("Testing agent workflow with web search...")

    # Import after monkey patching
    from agent import main

    # Mock the MCP connection in main
    original_main = main

    async def mock_main():
        # Override the MCP manager in main scope
        import agent

        agent.mcp_manager = MockMCPClientManager()

        # Get web search tools directly
        from agent import web_search

        web_search_tools = [web_search]

        print("✅ Loaded Tools: Web Search (mock MCP)")

        # Create graph
        from agent import create_graph_with_tools

        agent_graph = create_graph_with_tools([], [], [], web_search_tools)

        # Test query
        user_input = "Search for information about Python programming"
        print(f"User Input: {user_input}")

        initial_state = {
            "user_input": user_input,
            "plan": agent.Plan(goal="", tasks=[]),
            "messages": [],
            "current_task_index": 0,
        }

        # Run the agent
        await agent_graph.ainvoke(initial_state)
        print("\n✨ Agent execution completed.")

    await mock_main()


if __name__ == "__main__":
    asyncio.run(test_agent_web_search())
