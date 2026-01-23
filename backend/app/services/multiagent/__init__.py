"""
多智能体系统入口 - DeepAgent 核心接口

提供统一的接口来访问分层多智能体系统。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.services.multiagent.main_agent import MainAgent
from app.services.multiagent.models import ExecutionResult

logger = logging.getLogger(__name__)


class DeepAgent:
    """DeepAgent 多智能体系统主接口"""

    def __init__(self):
        """初始化 DeepAgent 系统"""
        self.main_agent = MainAgent()
        self.initialized_at = datetime.now()
        logger.info("DeepAgent 多智能体系统已初始化")

    async def initialize(self):
        """异步初始化系统"""
        # 这里可以添加额外的初始化逻辑
        # 比如检查 MCP 连接、预热模型等
        logger.info("DeepAgent 系统异步初始化完成")

    async def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """
        执行用户请求

        Args:
            user_input: 用户输入文本
            context: 额外的上下文信息
            timeout_seconds: 超时时间（秒）

        Returns:
            执行结果
        """
        try:
            logger.info(f"DeepAgent 处理请求: {user_input[:50]}...")

            # 调用主智能体处理
            result = await self.main_agent.process_task(
                user_input=user_input, context=context, timeout_seconds=timeout_seconds
            )

            logger.info(f"DeepAgent 请求处理完成")
            return result

        except Exception as e:
            logger.error(f"DeepAgent 执行失败: {e}")
            return f"""❌ 系统错误

**错误信息**: {str(e)}

**发生时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**建议解决方案**:
1. 检查输入格式是否正确
2. 确认系统服务正在运行
3. 查看系统日志了解详细错误信息
4. 稍后重试或联系技术支持

如果问题持续存在，请提供错误发生的具体操作步骤。"""

    async def run_with_files(
        self,
        user_input: str,
        files: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        带文件上下文的执行

        Args:
            user_input: 用户输入
            files: 文件信息字典
            context: 额外上下文

        Returns:
            执行结果
        """
        # 合并文件信息到上下文
        enhanced_context = context or {}
        if files:
            enhanced_context["files"] = files

        return await self.run(user_input, enhanced_context)

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        stats = self.main_agent.get_system_stats()

        return {
            "system_name": "DeepAgent Multi-Agent System",
            "version": "2.0.0",
            "architecture": "Hierarchical Multi-Agent",
            "initialized_at": self.initialized_at.isoformat(),
            "main_agent": stats["main_agent"],
            "subagents_count": stats["total_subagents"],
            "available_agents": self.main_agent.list_available_agents(),
            "capabilities": {
                "intent_analysis": True,
                "task_planning": True,
                "parallel_execution": True,
                "error_recovery": True,
                "mcp_integration": True,
            },
        }

    def get_agent_list(self) -> List[Dict[str, Any]]:
        """获取可用智能体列表"""
        return self.main_agent.list_available_agents()

    async def health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        try:
            # 检查主智能体健康状态
            main_health = await self.main_agent.health_check()

            # 检查子智能体健康状态
            subagent_health = {}
            for name, agent in self.main_agent.subagents.items():
                try:
                    subagent_health[name] = await agent.health_check()
                except Exception as e:
                    subagent_health[name] = {
                        "status": "error",
                        "error": str(e),
                        "last_check": datetime.now().isoformat(),
                    }

            # 综合健康状态
            all_healthy = main_health.get("status") == "healthy" and all(
                h.get("status") == "healthy" for h in subagent_health.values()
            )

            return {
                "status": "healthy" if all_healthy else "degraded",
                "timestamp": datetime.now().isoformat(),
                "main_agent": main_health,
                "subagents": subagent_health,
                "overall_health": "good" if all_healthy else "needs_attention",
            }

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def execute_simple_command(
        self, command: str, agent_type: str = "auto"
    ) -> str:
        """
        执行简单命令（快捷方式）

        Args:
            command: 命令字符串
            agent_type: 指定智能体类型，"auto"表示自动选择

        Returns:
            执行结果
        """
        if agent_type == "auto":
            # 让主智能体自动决定
            return await self.run(command)
        else:
            # 直接路由到指定智能体
            agent = self.main_agent.subagents.get(agent_type)
            if agent:
                return await agent.process_task(command)
            else:
                return f"未知的智能体类型: {agent_type}"

    def get_supported_operations(self) -> Dict[str, List[str]]:
        """获取系统支持的操作"""
        operations = {}

        # 主智能体操作
        operations["main"] = [
            "intent_analysis",
            "task_planning",
            "plan_execution",
            "system_coordination",
            "error_handling",
        ]

        # 子智能体操作
        for name, agent in self.main_agent.subagents.items():
            operations[name] = agent.capabilities.supported_operations

        return operations

    async def cleanup(self):
        """清理系统资源"""
        # 这里可以添加清理逻辑
        # 比如关闭连接、清理临时文件等
        logger.info("DeepAgent 系统清理完成")


# 全局实例
deep_agent = DeepAgent()
