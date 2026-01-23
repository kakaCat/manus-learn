#!/usr/bin/env python3
"""
Direct test of the LangGraph workflow with web search.
"""

import asyncio
import os
from agent import (
    AgentState,
    AgentType,
    Task,
    TaskStatus,
    Plan,
    web_search,
    create_graph_with_tools,
)


async def test_direct_workflow():
    """Test the workflow directly with a web search task."""
    print("Testing direct LangGraph workflow with web search...")

    # Create web search tools
    web_search_tools = [web_search]

    # Create the graph
    agent_graph = create_graph_with_tools([], [], [], web_search_tools)

    # Create a plan with web search task
    plan = Plan(
        goal="Search for Python programming information",
        tasks=[
            Task(
                id=1,
                description="Search the web for information about Python programming",
                status=TaskStatus.PENDING,
                assigned_agent=AgentType.WEB_SEARCH,
            )
        ],
    )

    # Initial state
    initial_state = AgentState(
        messages=[],
        user_input="Tell me about Python programming",
        intent=None,
        plan=plan,
        current_task_index=0,
        scratchpad={},
    )

    print("Running workflow...")
    result = await agent_graph.ainvoke(initial_state)

    print("✅ Workflow completed!")
    print(f"Final task status: {result['plan'].tasks[0].status}")
    if result["plan"].tasks[0].result:
        print(f"Result: {result['plan'].tasks[0].result[:200]}...")


if __name__ == "__main__":
    asyncio.run(test_direct_workflow())
