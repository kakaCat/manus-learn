#!/usr/bin/env python3
"""Test plan functionality directly"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.deep_agent_core import deep_agent_core


async def test_plan():
    print("Testing plan functionality...")

    try:
        # Test simple task (should not use plan)
        print("\n1. Testing simple task...")
        result1 = await deep_agent_core.process("运行pwd命令")
        print(f"Simple task result: {result1.get('status')}")
        print(f"Plan used: {result1.get('plan_used', False)}")

        # Test complex task (should use plan)
        print("\n2. Testing complex task...")
        result2 = await deep_agent_core.process(
            "第一步创建test.txt文件，第二步读取文件内容"
        )
        print(f"Complex task result: {result2.get('status')}")
        print(f"Plan used: {result2.get('plan_used', False)}")

        if result2.get("plan_used"):
            print("Plan details:")
            if "plan" in result2:
                plan = result2["plan"]
                print(f"  Plan ID: {plan.get('plan_id')}")
                print(f"  Tasks: {plan.get('task_count')}")
                print(f"  Goal: {plan.get('goal')[:50]}...")

            if "execution" in result2:
                execution = result2["execution"]
                print(f"  Execution status: {execution.get('status')}")
                print(f"  Results: {len(execution.get('results', []))}")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_plan())
