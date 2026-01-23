#!/usr/bin/env python3
"""
Simple test for complex task detection logic.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.deep_agent_core import IntentAnalysis

def test_complex_task_detection():
    """Test the _detect_complex_task logic."""

    # Create a mock main agent just for testing the detection logic
    class MockMainAgent:
        def _detect_complex_task(self, user_input: str, intent_analysis: IntentAnalysis) -> bool:
            """Enhanced logic to detect if a task requires planning and multiple steps."""
            input_lower = user_input.lower()

            # Direct intent classification
            if (
                intent_analysis.intent == "complex_task"
                and intent_analysis.confidence > 0.7
            ):
                return True

            # Multi-step indicators
            step_indicators = [
                # Chinese step words
                "首先", "然后", "接下来", "之后", "最后", "第一步", "第二步", "第三步",
                "第一", "第二", "第三", "第四", "第五",
                # English step words
                "first", "then", "next", "after", "finally", "step 1", "step 2", "step 3",
                "1.", "2.", "3.", "4.", "5.",
                # Sequence words
                "and then", "followed by", "subsequently",
            ]
            has_steps = any(indicator in input_lower for indicator in step_indicators)

            # Multi-action indicators
            action_indicators = [
                # Chinese actions
                "创建", "安装", "配置", "设置", "测试", "运行", "部署", "上传", "下载",
                "修改", "更新", "删除", "备份", "恢复", "检查", "验证",
                # English actions
                "create", "install", "configure", "setup", "test", "run", "deploy",
                "upload", "download", "modify", "update", "delete", "backup", "restore",
                "check", "verify", "build", "compile",
            ]
            action_count = sum(1 for action in action_indicators if action in input_lower)

            # Complex task patterns
            complex_patterns = [
                "请帮我", "帮我", "help me", "i need to", "i want to",
                "项目", "project", "application", "app",
                "开发环境", "development environment", "workflow",
                "自动化", "automation", "pipeline",
            ]
            has_complex_pattern = any(pattern in input_lower for pattern in complex_patterns)

            # Length and complexity indicators
            word_count = len(user_input.split())
            has_numbers = any(char.isdigit() for char in user_input)
            has_lists = any(char in user_input for char in ["•", "-", "*"]) and has_numbers

            # Decision logic
            is_complex = (
                # High confidence intent classification
                (intent_analysis.intent == "complex_task" and intent_analysis.confidence > 0.6) or
                # Multiple steps explicitly mentioned
                (has_steps and has_numbers) or
                # Multiple actions in one request
                (action_count >= 3) or
                # Complex patterns
                (has_complex_pattern and action_count >= 2) or
                # Long requests with multiple elements
                (word_count > 25) or
                # Structured lists
                (has_lists and word_count > 15) or
                # Very long single sentences
                (word_count > 40)
            )

            print(f"  Complex task detection: {is_complex}")
            print(f"    - steps: {has_steps}, actions: {action_count}, words: {word_count}")
            print(f"    - intent: {intent_analysis.intent}, confidence: {intent_analysis.confidence}")

            return is_complex

    agent = MockMainAgent()

    test_cases = [
        ("创建test.txt文件，写入一些内容，然后读取文件内容", IntentAnalysis("complex_task", 0.8, {})),
        ("首先安装依赖，然后配置环境，最后启动服务器", IntentAnalysis("complex_task", 0.9, {})),
        ("帮我创建一个Python项目，包含多个文件和配置", IntentAnalysis("complex_task", 0.7, {})),
        ("请列出当前目录的文件", IntentAnalysis("shell_command", 0.9, {})),
        ("今天天气怎么样", IntentAnalysis("information_query", 0.8, {})),
    ]

    print("🧪 Testing Complex Task Detection\n")

    for query, intent in test_cases:
        print(f"Query: {query}")
        is_complex = agent._detect_complex_task(query, intent)
        print(f"Result: {'✅ Complex Task' if is_complex else '❌ Simple Task'}")
        print("-" * 50)

if __name__ == "__main__":
    test_complex_task_detection()</content>
<parameter name="filePath">backend/test_detection.py