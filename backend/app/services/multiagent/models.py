"""
数据模型 - 分层多智能体系统的核心数据结构

包含任务、计划、意图分析、状态枚举等基础模型。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务执行状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AgentType(Enum):
    """智能体类型"""

    MAIN = "main"  # 主智能体
    SHELL = "shell"  # Shell命令执行
    FILESYSTEM = "filesystem"  # 文件操作
    BROWSER = "browser"  # 网页自动化
    MANAGER = "manager"  # MCP工具管理
    GENERAL = "general"  # 通用查询处理
    DYNAMIC = "dynamic"  # 动态创建的智能体


@dataclass
class Task:
    """任务数据模型"""

    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    timeout_seconds: Optional[int] = None

    def __post_init__(self):
        """初始化后处理"""
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class Plan:
    """计划数据模型"""

    id: str
    goal: str
    tasks: List[Task] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    estimated_duration: Optional[int] = None  # 预估执行时间（秒）

    def __post_init__(self):
        """初始化后处理"""
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class IntentAnalysis:
    """意图分析结果"""

    intent: str
    confidence: float
    entities: Dict[str, Any]
    clarification_needed: bool = False
    clarification_questions: List[str] = field(default_factory=list)
    suggested_agents: List[str] = field(default_factory=list)
    complexity_level: str = "medium"  # low, medium, high

    def is_clear(self) -> bool:
        """判断意图是否清晰"""
        return self.confidence >= 0.7 and not self.clarification_needed

    def needs_clarification(self) -> bool:
        """判断是否需要澄清"""
        return self.confidence < 0.5 or self.clarification_needed


@dataclass
class AgentCapabilities:
    """智能体能力描述"""

    name: str
    description: str
    supported_operations: List[str]
    mcp_servers: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 1
    supports_parallel: bool = False
    avg_response_time: Optional[int] = None  # 平均响应时间（秒）


@dataclass
class ExecutionResult:
    """任务执行结果"""

    task_id: str
    agent_name: str
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }


@dataclass
class PlanExecutionSummary:
    """计划执行摘要"""

    plan_id: str
    goal: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    blocked_tasks: int
    total_execution_time: float
    success_rate: float
    results: List[ExecutionResult]
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理"""
        self.success_rate = (
            self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0.0
        )
