#!/usr/bin/env python3
"""
Test script for DeepAgent plan creation functionality.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.deep_agent_core import deep_agent_core

async def test_plan_creation():
    """Test plan creation with various complex queries."""

    test_queries = [
        "创建test.txt文件，写入一些内容，然后读取文件内容",
        "首先安装依赖，然后配置环境，最后启动服务器",
    ]

    print("🧪 Testing DeepAgent Plan Creation\n")

    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: {query}")
        print("-" * 50)

        try:
            result = await deep_agent_core.process(query)

            print(f"Intent: {result.get('intent_analysis', {}).get('intent', 'unknown')}")
            print(f"Plan Used: {result.get('plan_used', False)}")
            print(f"Status: {result.get('status', 'unknown')}")

            if result.get('plan_used'):
                plan = result.get('plan', {})
                print(f"Tasks: {plan.get('task_count', 0)}")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(test_plan_creation())</content>
<parameter name="filePath">backend/test_plan_creation.py