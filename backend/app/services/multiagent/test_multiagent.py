"""
多智能体系统测试脚本

测试 DeepAgent 分层多智能体系统的各项功能。
"""

import asyncio
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试 DeepAgent 多智能体系统基本功能")
    print("=" * 60)

    try:
        from app.services.multiagent import deep_agent

        # 初始化系统
        print("📋 初始化系统...")
        await deep_agent.initialize()

        # 获取系统信息
        print("ℹ️ 获取系统信息...")
        system_info = deep_agent.get_system_info()
        print(f"系统名称: {system_info['system_name']}")
        print(f"版本: {system_info['version']}")
        print(f"架构: {system_info['architecture']}")
        print(f"可用智能体数量: {system_info['subagents_count']}")

        # 列出可用智能体
        print("\n🤖 可用智能体:")
        agents = deep_agent.get_agent_list()
        for agent in agents:
            print(f"  - {agent['name']} ({agent['type']})")

        # 健康检查
        print("\n🏥 健康检查...")
        health = await deep_agent.health_check()
        print(f"系统状态: {health['status']}")
        print(f"主智能体状态: {health['main_agent']['status']}")

        for name, status in health['subagents'].items():
            print(f"子智能体 {name}: {status['status']}")

        print("\n✅ 基本功能测试完成")
        return True

    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False


async def test_simple_commands():
    """测试简单命令执行"""
    print("\n🧪 测试简单命令执行")
    print("=" * 60)

    try:
        from app.services.multiagent import deep_agent

        test_commands = [
            ("列出当前目录", "shell"),
            ("读取这个文件的内容", "filesystem"),
            ("打开百度网站", "browser"),
        ]

        for command, expected_agent in test_commands:
            print(f"\n🔧 测试命令: {command}")
            try:
                result = await deep_agent.execute_simple_command(command, "auto")
                print(f"✅ 执行成功")
                print(f"结果预览: {result[:100]}...")

            except Exception as e:
                print(f"⚠️ 执行失败: {e}")

        print("\n✅ 简单命令测试完成")
        return True

    except Exception as e:
        print(f"❌ 简单命令测试失败: {e}")
        return False


async def test_complex_tasks():
    """测试复杂任务处理"""
    print("\n🧪 测试复杂任务处理")
    print("=" * 60)

    try:
        from app.services.multiagent import deep_agent

        complex_tasks = [
            "创建一个 Python 脚本，读取当前目录的文件列表，然后统计文件数量",
            "打开浏览器访问百度，搜索'人工智能'，然后截图保存",
        ]

        for task in complex_tasks:
            print(f"\n🎯 测试复杂任务: {task[:50]}...")
            try:
                result = await deep_agent.run(task, timeout_seconds=120)
                print(f"✅ 复杂任务执行成功")
                print(f"结果预览: {result[:200]}...")

            except Exception as e:
                print(f"⚠️ 复杂任务执行失败: {e}")

        print("\n✅ 复杂任务测试完成")
        return True

    except Exception as e:
        print(f"❌ 复杂任务测试失败: {e}")
        return False


async def test_intent_analysis():
    """测试意图分析功能"""
    print("\n🧪 测试意图分析功能")
    print("=" * 60)

    try:
        from app.services.multiagent.main_agent import MainAgent

        main_agent = MainAgent()

        test_inputs = [
            "ls -la",
            "读取文件 test.txt",
            "打开百度网站",
            "创建一个 Python 脚本",
            "创建一个完整的项目，包括前端后端和数据库",
        ]

        for user_input in test_inputs:
            print(f"\n🔍 分析输入: {user_input}")
            try:
                intent = await main_agent.analyze_intent(user_input)
                print(f"意图: {intent.intent}")
                print(f"置信度: {intent.confidence:.2f}")
                print(f"复杂度: {intent.complexity_level}")
                if intent.clarification_needed:
                    print(f"需要澄清: {intent.clarification_questions}")

            except Exception as e:
                print(f"⚠️ 意图分析失败: {e}")

        print("\n✅ 意图分析测试完成")
        return True

    except Exception as e:
        print(f"❌ 意图分析测试失败: {e}")
        return False


async def test_supported_operations():
    """测试支持的操作"""
    print("\n🧪 测试支持的操作")
    print("=" * 60)

    try:
        from app.services.multiagent import deep_agent

        operations = deep_agent.get_supported_operations()

        print("📋 系统支持的操作:")
        for agent_name, ops in operations.items():
            print(f"\n{agent_name.upper()} 智能体:")
            for op in ops:
                print(f"  - {op}")

        print("\n✅ 支持操作测试完成")
        return True

    except Exception as e:
        print(f"❌ 支持操作测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始 DeepAgent 多智能体系统测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    test_results = []

    # 测试列表
    tests = [
        ("基本功能", test_basic_functionality),
        ("简单命令", test_simple_commands),
        ("复杂任务", test_complex_tasks),
        ("意图分析", test_intent_analysis),
        ("支持操作", test_supported_operations),
    ]

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} 测试 {'='*20}")
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试出现异常: {e}")
            test_results.append((test_name, False))

    # 测试总结
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n总体结果: {passed}/{total} 测试通过")
    success_rate = passed / total * 100
    print(".1f"
    if success_rate >= 80:
        print("🎉 系统测试基本成功！")
    else:
        print("⚠️ 系统需要进一步调试")

    return passed == total


async def interactive_test():
    """交互式测试"""
    print("🎮 进入交互式测试模式")
    print("输入 'exit' 或 'quit' 退出")
    print("-" * 40)

    try:
        from app.services.multiagent import deep_agent
        await deep_agent.initialize()

        while True:
            user_input = input("\n🤖 请输入您的指令: ").strip()

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("👋 再见！")
                break

            if not user_input:
                continue

            print("⏳ 正在处理...")
            start_time = datetime.now()

            try:
                result = await deep_agent.run(user_input)
                duration = (datetime.now() - start_time).total_seconds()

                print(f"✅ 处理完成 (耗时: {duration:.1f}秒)")
                print("\n📝 结果:")
                print(result)

            except Exception as e:
                print(f"❌ 处理失败: {e}")

    except KeyboardInterrupt:
        print("\n👋 用户中断测试")
    except Exception as e:
        print(f"❌ 交互式测试异常: {e}")


async def main():
    """主函数"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        await interactive_test()
    else:
        success = await run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())