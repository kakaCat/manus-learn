"""
基础智能体类 - 分层多智能体系统的基础架构

包含 BaseAgent 基类和通用智能体框架。
"""

import asyncio
import logging
import functools
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from datetime import datetime

from app.core.config import settings
from app.core.llm import get_llm
from app.services.multiagent.models import (
    AgentType,
    AgentCapabilities,
    Task,
    TaskStatus,
    ExecutionResult,
    IntentAnalysis,
)

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 2, delay: float = 1.0, backoff: float = 2.0):
    """
    失败重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except asyncio.TimeoutError as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"尝试 {attempt + 1} 失败，函数 {func.__name__} 超时，将在 {current_delay:.1f} 秒后重试..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"函数 {func.__name__} 在 {max_retries + 1} 次尝试后仍然超时"
                        )
                        raise last_exception
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"尝试 {attempt + 1} 失败，函数 {func.__name__} 出现错误: {e}，将在 {current_delay:.1f} 秒后重试..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"函数 {func.__name__} 在 {max_retries + 1} 次尝试后仍然失败: {e}"
                        )
                        raise last_exception

            # 这行代码不会被执行到，但为了类型检查器的要求
            return None

        return wrapper

    return decorator


class BaseAgent(ABC):
    """智能体基类 - 所有智能体的基础"""

    def __init__(
        self,
        name: str,
        agent_type: AgentType,
        system_prompt: str,
        capabilities: Optional[AgentCapabilities] = None,
    ):
        self.name = name
        self.agent_type = agent_type
        self.system_prompt = system_prompt
        self.llm = get_llm()

        # 设置能力描述
        if capabilities:
            self.capabilities = capabilities
        else:
            self.capabilities = AgentCapabilities(
                name=name,
                description=f"{name} 智能体",
                supported_operations=self._get_default_operations(),
                max_concurrent_tasks=1,
                supports_parallel=False,
            )

        self.created_at = datetime.now()
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0

        logger.info(f"智能体 {name} ({agent_type.value}) 已初始化")

    def _get_default_operations(self) -> List[str]:
        """获取默认支持的操作"""
        return ["process_task", "execute_command", "analyze_input"]

    @abstractmethod
    async def process_task(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """处理用户任务 - 必须由子类实现"""
        raise NotImplementedError("子类必须实现 process_task 方法")

    async def execute_with_timeout(
        self, task: Task, timeout_seconds: Optional[int] = None
    ) -> ExecutionResult:
        """
        带超时的任务执行

        Args:
            task: 要执行的任务
            timeout_seconds: 超时时间（秒）

        Returns:
            执行结果
        """
        start_time = datetime.now()
        actual_timeout = timeout_seconds or task.timeout_seconds or 300  # 默认5分钟

        try:
            # 设置任务状态
            task.status = TaskStatus.IN_PROGRESS

            # 执行任务（带超时控制）
            result = await asyncio.wait_for(
                self.process_task(
                    user_input=task.description,
                    context={"task_id": task.id},
                    timeout_seconds=actual_timeout,
                ),
                timeout=actual_timeout,
            )

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            # 更新统计
            self.task_count += 1
            self.success_count += 1

            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            return ExecutionResult(
                task_id=task.id,
                agent_name=self.name,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"agent_type": self.agent_type.value},
            )

        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.task_count += 1
            self.failure_count += 1

            error_msg = f"""⏰ 任务执行超时

**任务详情**: {task.description}
**超时时间**: {actual_timeout} 秒
**执行时间**: {execution_time:.1f} 秒

**可能原因**:
- 操作过于复杂或耗时
- 网络连接问题
- 系统资源不足

**建议解决方案**:
- 简化任务，分解为更小的步骤
- 检查系统状态和网络连接
- 稍后重试操作

如果问题持续，请联系技术支持。"""

            task.status = TaskStatus.FAILED
            task.error = "执行超时"

            return ExecutionResult(
                task_id=task.id,
                agent_name=self.name,
                success=False,
                error=error_msg,
                execution_time=execution_time,
                metadata={"timeout_seconds": actual_timeout},
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.task_count += 1
            self.failure_count += 1

            error_msg = f"""❌ 任务执行失败

**任务详情**: {task.description}
**错误信息**: {str(e)}
**执行时间**: {execution_time:.1f} 秒

**故障排除步骤**:
1. 检查输入参数是否正确
2. 确认相关服务正在运行
3. 查看系统日志了解更多信息
4. 尝试简化操作或分步执行

如果问题持续存在，请提供更多详细信息以便诊断。"""

            task.status = TaskStatus.FAILED
            task.error = str(e)

            logger.error(f"智能体 {self.name} 执行任务失败: {e}")

            return ExecutionResult(
                task_id=task.id,
                agent_name=self.name,
                success=False,
                error=error_msg,
                execution_time=execution_time,
                metadata={"exception_type": type(e).__name__},
            )

    def get_stats(self) -> Dict[str, Any]:
        """获取智能体统计信息"""
        success_rate = (
            self.success_count / self.task_count if self.task_count > 0 else 0.0
        )

        return {
            "name": self.name,
            "type": self.agent_type.value,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": f"{success_rate:.1%}",
            "created_at": self.created_at.isoformat(),
            "capabilities": {
                "supported_operations": self.capabilities.supported_operations,
                "max_concurrent_tasks": self.capabilities.max_concurrent_tasks,
                "supports_parallel": self.capabilities.supports_parallel,
            },
        }

    def supports_operation(self, operation: str) -> bool:
        """检查是否支持特定操作"""
        return operation in self.capabilities.supported_operations

    def can_handle_parallel(self) -> bool:
        """检查是否支持并行处理"""
        return self.capabilities.supports_parallel

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 简单的健康检查 - 尝试调用 LLM
            test_response = await self.llm.ainvoke(
                [{"role": "user", "content": "Hello"}]
            )

            return {
                "status": "healthy",
                "agent_name": self.name,
                "llm_status": "ok",
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_name": self.name,
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }


class SubAgent(BaseAgent):
    """子智能体基类 - 专门化的智能体"""

    def __init__(
        self,
        name: str,
        agent_type: AgentType,
        system_prompt: str,
        mcp_servers: List[str] = None,
        capabilities: Optional[AgentCapabilities] = None,
    ):
        super().__init__(name, agent_type, system_prompt, capabilities)

        self.mcp_servers = mcp_servers or []
        self.last_activity = datetime.now()

        # 更新能力描述
        if not capabilities:
            self.capabilities.mcp_servers = self.mcp_servers

    async def process_task(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """处理任务的通用实现"""
        try:
            self.last_activity = datetime.now()

            # 创建专门化的提示
            context_info = ""
            if context:
                context_info = f"\n上下文: {context}"

            full_prompt = (
                f"{self.system_prompt}{context_info}\n\n任务: {user_input}\n\n响应:"
            )

            # 调用 LLM
            from langchain_core.messages import HumanMessage

            messages = [HumanMessage(content=full_prompt)]
            response = await self.llm.ainvoke(messages)

            result = (
                response.content if response.content else "任务已完成但未生成输出。"
            )

            logger.info(f"子智能体 {self.name} 处理任务成功: {user_input[:50]}...")

            return str(result).strip()

        except Exception as e:
            logger.error(f"子智能体 {self.name} 处理任务失败: {e}")
            raise
