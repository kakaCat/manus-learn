#!/usr/bin/env python3
"""
Test script for Sandbox Agent with MCP Manager capabilities.

This script demonstrates how the AI agent can:
1. List available MCPs in the marketplace
2. Check installed MCPs
3. Install new capabilities dynamically
4. Use the newly installed tools
"""

import asyncio
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_agent():
    """Test the sandbox agent with various scenarios."""
    from agent import sandbox_agent

    logger.info("🚀 Initializing Sandbox Agent...")
    await sandbox_agent.initialize()

    # Test scenarios
    test_scenarios = [
        {
            "name": "Check MCP Manager Status",
            "prompt": "What MCP tools are currently installed? Use the MCP manager to check.",
        },
        {
            "name": "Browse MCP Marketplace",
            "prompt": "What new capabilities can I get? Show me what's available in the MCP marketplace.",
        },
        {
            "name": "AI Self-Improvement Test",
            "prompt": (
                "I need you to search the web for the latest AI news. "
                "If you don't have search capability, install it from the marketplace."
            ),
        },
        {
            "name": "File Operations Test",
            "prompt": "Create a file called 'test.txt' with the content 'Hello from AI Agent!' and then read it back.",
        },
        {
            "name": "Process Monitoring",
            "prompt": "Show me what processes are running in the sandbox.",
        },
    ]

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*80}")
        print(f"📝 Test {i}/{len(test_scenarios)}: {scenario['name']}")
        print(f"{'='*80}")
        print(f"User: {scenario['prompt']}")
        print(f"{'-'*80}")

        try:
            response = await sandbox_agent.run(scenario['prompt'])
            print(f"\n🤖 Agent:\n{response}")

        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)
            print(f"\n❌ Error: {e}")

        # Wait a bit between tests
        if i < len(test_scenarios):
            print(f"\n⏸️  Waiting 3 seconds before next test...")
            await asyncio.sleep(3)

    print(f"\n{'='*80}")
    print("✅ All tests completed!")
    print(f"{'='*80}")


async def interactive_mode():
    """Run agent in interactive mode."""
    from agent import sandbox_agent

    print("🤖 Sandbox Agent - Interactive Mode")
    print("="*80)
    print("Commands:")
    print("  - Type your question/command")
    print("  - Type 'quit' or 'exit' to stop")
    print("  - Type 'status' to check MCP servers")
    print("  - Type 'marketplace' to see available MCPs")
    print("="*80)

    await sandbox_agent.initialize()

    chat_history = []

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            if user_input.lower() == 'status':
                user_input = "Check the status of all MCP servers"

            if user_input.lower() == 'marketplace':
                user_input = "Show me all available MCPs in the marketplace with their categories"

            print("\n🤖 Agent: ", end="", flush=True)
            response = await sandbox_agent.run(user_input, chat_history)
            print(response)

            # Update chat history (keep last 10 exchanges)
            chat_history.append(("human", user_input))
            chat_history.append(("ai", response))
            if len(chat_history) > 20:
                chat_history = chat_history[-20:]

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Sandbox Agent with MCP Manager")
    parser.add_argument(
        '--mode',
        choices=['test', 'interactive'],
        default='test',
        help="Run mode: 'test' for automated tests, 'interactive' for chat"
    )
    parser.add_argument(
        '--prompt',
        type=str,
        help="Single prompt to run (skips test/interactive modes)"
    )

    args = parser.parse_args()

    if args.prompt:
        # Single prompt mode
        async def run_single():
            from agent import sandbox_agent
            await sandbox_agent.initialize()
            response = await sandbox_agent.run(args.prompt)
            print(f"\n🤖 Agent:\n{response}")

        asyncio.run(run_single())

    elif args.mode == 'interactive':
        asyncio.run(interactive_mode())
    else:
        asyncio.run(test_agent())


if __name__ == "__main__":
    main()
