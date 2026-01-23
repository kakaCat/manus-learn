#!/usr/bin/env python3
"""
测试 006demo 的所有功能
"""

import asyncio
import os
import sys

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

try:
    from dotenv import load_dotenv
    from agent import (
        AgentType,
        IntentAnalysis,
        Plan,
        Task,
        create_graph_with_tools,
        MCPClientManager,
    )

    # Load environment variables
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=env_path)

    async def test_functionality():
        print("🧪 开始测试 006demo 功能...")

        # Initialize MCP Manager
        mcp_manager = MCPClientManager()
        try:
            await mcp_manager.connect()

            # Get Tools
            shell_tools = await mcp_manager.get_tools("shell")
            filesystem_tools = await mcp_manager.get_tools("filesystem")
            browser_tools = await mcp_manager.get_tools("chrome")
            web_search_tools = []  # We'll test this separately

            print(f"✅ 工具加载成功:")
            print(f"   - Shell: {len(shell_tools)} 个工具")
            print(f"   - Filesystem: {len(filesystem_tools)} 个工具")
            print(f"   - Browser: {len(browser_tools)} 个工具")

            # Create Graph
            agent_graph = create_graph_with_tools(
                shell_tools, filesystem_tools, browser_tools, web_search_tools
            )

            # Test cases
            test_cases = [
                {
                    "name": "Shell Test",
                    "input": "运行命令 'echo Hello World' 并显示结果",
                    "expected_agent": AgentType.SHELL,
                },
                {
                    "name": "Filesystem Test",
                    "input": "创建一个名为 test.txt 的文件，内容为 'Hello from filesystem test'",
                    "expected_agent": AgentType.FILESYSTEM,
                },
                {
                    "name": "Browser Test",
                    "input": "打开浏览器访问 https://www.example.com 并截图",
                    "expected_agent": AgentType.BROWSER,
                },
                {
                    "name": "Web Search Test",
                    "input": "搜索 Python 编程教程",
                    "expected_agent": AgentType.WEB_SEARCH,
                },
            ]

            for test_case in test_cases:
                print(f"\n🔍 测试: {test_case['name']}")
                print(f"   输入: {test_case['input']}")

                try:
                    # Create test state
                    initial_state = {
                        "user_input": test_case["input"],
                        "intent": IntentAnalysis(
                            intent=test_case["input"],
                            needs_sandbox=True,
                            confidence=0.9,
                        ),
                        "plan": None,
                        "messages": [],
                        "current_task_index": 0,
                        "scratchpad": {},
                    }

                    # Run agent
                    result = await agent_graph.ainvoke(
                        initial_state, {"recursion_limit": 50}
                    )

                    print(f"   ✅ 执行成功")
                    print(
                        f"   📝 结果摘要: {str(result['messages'][-1].content)[:200]}..."
                    )

                except Exception as e:
                    print(f"   ❌ 执行失败: {e}")

        finally:
            await mcp_manager.close()

    if __name__ == "__main__":
        asyncio.run(test_functionality())

except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保已安装所有依赖: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ 测试失败: {e}")
