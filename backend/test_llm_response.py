#!/usr/bin/env python3
"""Test LLM response format"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.llm import get_llm
from langchain_core.messages import HumanMessage


async def test_llm():
    print("Testing LLM response...")
    llm = get_llm()
    print(f"LLM type: {type(llm)}")

    test_prompt = """You are the Shell Commander SubAgent in the DeepAgent system.
Your specialization: Executing terminal commands and system operations.

Capabilities:
- Run shell commands (ls, cd, mkdir, rm, etc.)
- Execute scripts and programs
- Monitor system processes and resources
- Perform system administration tasks

Safety: Be extremely careful with destructive operations. Always confirm before deletion or system changes.
Provide clear output and explain what each command does.

Task: 运行pwd命令

Assistant:"""

    messages = [HumanMessage(content=test_prompt)]
    response = await llm.ainvoke(messages)

    print(f"Response type: {type(response)}")
    print(f"Response content: {repr(response.content)}")
    print(
        f"Response content length: {len(response.content) if response.content else 0}"
    )

    if hasattr(response, "__dict__"):
        print(f"Response attributes: {response.__dict__}")


if __name__ == "__main__":
    asyncio.run(test_llm())
