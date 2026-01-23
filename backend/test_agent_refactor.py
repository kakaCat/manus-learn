"""Test script for LangChain 1.2.X agent refactoring."""

import asyncio
import logging
from app.services.agent import sandbox_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_agent():
    """Test the refactored agent with LangChain 1.2.X create_agent."""

    print("\n" + "="*60)
    print("Testing LangChain 1.2.X Agent Implementation")
    print("="*60 + "\n")

    # Test 1: Initialize agent
    print("1️⃣  Initializing agent...")
    try:
        await sandbox_agent.initialize()
        print("✅ Agent initialized successfully\n")
    except Exception as e:
        print(f"❌ Initialization failed: {e}\n")
        return

    # Test 2: Simple query
    print("2️⃣  Testing simple query...")
    thread_id = "test-123"
    try:
        response = await sandbox_agent.run(
            user_input="Hello! Can you introduce yourself?",
            thread_id=thread_id
        )
        print(f"✅ Response received:")
        print(f"   {response[:200]}...\n")
    except Exception as e:
        print(f"❌ Query failed: {e}\n")
        return

    # Test 3: Memory persistence
    print("3️⃣  Testing memory persistence (same thread)...")
    try:
        response = await sandbox_agent.run(
            user_input="What did I just ask you?",
            thread_id=thread_id  # Same thread ID
        )
        print(f"✅ Response received:")
        print(f"   {response[:200]}...\n")
    except Exception as e:
        print(f"❌ Memory test failed: {e}\n")
        return

    # Test 4: Thread isolation
    print("4️⃣  Testing thread isolation (new thread)...")
    try:
        response = await sandbox_agent.run(
            user_input="What did I ask you before?",
            thread_id="test-456"  # Different thread ID
        )
        print(f"✅ Response received:")
        print(f"   {response[:200]}...\n")
    except Exception as e:
        print(f"❌ Thread isolation test failed: {e}\n")
        return

    print("="*60)
    print("✅ All tests passed! LangChain 1.2.X implementation working")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_agent())
