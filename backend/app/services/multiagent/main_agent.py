"""
主智能体实现 - 分层多智能体系统的核心协调器

负责意图分析、规划制定、任务分配和执行协调。
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from app.core.config import settings
from app.core.llm import get_llm
from app.services.multiagent.base_agent import BaseAgent, SubAgent
from app.services.multiagent.models import (
    AgentType,
    Task,
    Plan,
    TaskStatus,
    IntentAnalysis,
    ExecutionResult,
    PlanExecutionSummary,
)
from app.services.multiagent.subagents import (
    ShellSubAgent,
    FilesystemSubAgent,
    BrowserSubAgent,
    ManagerSubAgent,
    GeneralSubAgent,
)

logger = logging.getLogger(__name__)


class MainAgent(BaseAgent):
    """主智能体 - 分层多智能体系统的核心协调器"""

    def __init__(self):
        system_prompt = """
你是 DeepAgent 系统的主智能体，负责协调和管理整个智能体团队。

**核心职责**：
1. **意图识别**: 分析用户输入，确定意图和复杂度
2. **澄清系统**: 当意图不明确时请求澄清
3. **规划制定**: 为复杂任务创建详细执行计划
4. **任务协调**: 分配任务给合适的子智能体
5. **并行执行**: 协调并发任务执行
6. **结果合成**: 整合各子智能体的执行结果

**可用子智能体**：
- **Shell Commander**: 终端命令执行和系统操作
- **File System Manager**: 文件和目录操作
- **Chrome Browser Controller**: 网页浏览和自动化
- **MCP Manager**: MCP 工具生命周期管理
- **General Assistant**: 通用查询和信息提供

**决策原则**：
- 优先考虑安全性
- 最大化并行执行效率
- 提供清晰的用户反馈
- 优雅处理错误和异常

始终以用户为中心，提供有帮助、准确和及时的响应。
"""

        super().__init__(
            name="DeepAgent Main",
            agent_type=AgentType.MAIN,
            system_prompt=system_prompt,
        )

        # 初始化子智能体
        self.subagents: Dict[str, SubAgent] = {}
        self.dynamic_agents: Dict[str, SubAgent] = {}
        self.plans: Dict[str, Plan] = {}
        self.active_tasks: Dict[str, Task] = {}

        self._initialize_subagents()

        logger.info("主智能体初始化完成")

    def _initialize_subagents(self):
        """初始化所有子智能体"""
        try:
            # 固定子智能体
            self.subagents["shell"] = ShellSubAgent()
            self.subagents["filesystem"] = FilesystemSubAgent()
            self.subagents["browser"] = BrowserSubAgent()
            self.subagents["manager"] = ManagerSubAgent()
            self.subagents["general"] = GeneralSubAgent()

            logger.info(f"已初始化 {len(self.subagents)} 个子智能体")

        except Exception as e:
            logger.error(f"子智能体初始化失败: {e}")
            raise

    async def process_task(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """
        主任务处理流程

        Args:
            user_input: 用户输入
            context: 上下文信息
            timeout_seconds: 超时时间

        Returns:
            处理结果
        """
        try:
            logger.info(f"主智能体开始处理任务: {user_input[:50]}...")

            # 1. 意图分析
            intent_analysis = await self.analyze_intent(user_input)
            logger.info(
                f"意图分析完成: {intent_analysis.intent} (置信度: {intent_analysis.confidence:.2f})"
            )

            # 2. 检查是否需要澄清
            if intent_analysis.clarification_needed:
                clarification_response = self._build_clarification_response(
                    intent_analysis
                )
                return clarification_response

            # 3. 根据复杂度决定处理方式
            if intent_analysis.complexity_level in ["high", "medium"]:
                # 复杂任务 - 创建计划并执行
                plan = await self.create_plan(user_input, intent_analysis)
                execution_result = await self.execute_plan(plan)
                return self._format_execution_result(execution_result)
            else:
                # 简单任务 - 直接路由到对应子智能体
                result = await self._route_simple_task(user_input, intent_analysis)
                return result

        except Exception as e:
            logger.error(f"主智能体处理任务失败: {e}")
            return f"""❌ 处理请求失败

**错误信息**: {str(e)}

**可能原因**:
- 系统负载过高
- 部分服务不可用
- 请求格式异常

**建议解决方案**:
1. 检查输入格式是否正确
2. 稍后重试
3. 尝试简化请求

如果问题持续，请联系技术支持。"""

    async def analyze_intent(self, user_input: str) -> IntentAnalysis:
        """
        高级意图分析

        使用 LLM 进行意图识别、实体提取和复杂度评估。
        """
        try:
            analysis_prompt = f"""
分析以下用户输入并确定其意图。提供详细的分析结果。

**用户输入**: "{user_input}"

**分析要求**:
1. **意图分类**: 从可用意图中选择最合适的
2. **置信度评分**: 0.0-1.0之间的浮点数
3. **实体提取**: 提取关键信息和参数
4. **复杂度评估**: low/medium/high
5. **澄清需求**: 是否需要更多信息

**可用意图类别**:
- file_operation: 文件读写、创建、删除等操作
- shell_command: 终端命令执行和系统操作
- web_browsing: 网页访问、搜索、截图等
- tool_management: 安装/管理 MCP 工具
- information_query: 一般性问题和信息查询
- complex_task: 多步骤复杂任务
- unclear: 无法明确确定意图

**复杂度标准**:
- **low**: 单个简单操作，无依赖
- **medium**: 多个相关操作，或需要一些配置
- **high**: 多步骤任务、涉及多个工具、需要规划

**输出格式**:
意图: [意图类别]
置信度: [0.0-1.0]
实体: [提取的实体，JSON格式]
复杂度: [low/medium/high]
需要澄清: [true/false]
澄清问题: [如果需要澄清的问题列表]

**示例**:
意图: shell_command
置信度: 0.95
实体: {{"command": "ls -la", "target": "/home/user"}}
复杂度: low
需要澄清: false
澄清问题: []
"""

            from langchain_core.messages import HumanMessage

            messages = [HumanMessage(content=analysis_prompt)]
            response = await self.llm.ainvoke(messages)
            analysis_text = str(response.content)

            # 解析分析结果
            intent = "unclear"
            confidence = 0.5
            entities = {}
            complexity_level = "medium"
            clarification_needed = False
            clarification_questions = []

            lines = analysis_text.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("意图:"):
                    intent = line.split(":", 1)[1].strip()
                elif line.startswith("置信度:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                    except:
                        confidence = 0.5
                elif line.startswith("复杂度:"):
                    complexity_level = line.split(":", 1)[1].strip()
                elif line.startswith("需要澄清:"):
                    clarification_needed = "true" in line.lower()
                elif line.startswith("澄清问题:") and clarification_needed:
                    questions_str = line.split(":", 1)[1].strip()
                    if questions_str and questions_str != "[]":
                        # 简单解析
                        clarification_questions = [
                            q.strip() for q in questions_str.split(",") if q.strip()
                        ]

            # 解析实体（简化处理）
            if "实体:" in analysis_text:
                try:
                    entities_part = analysis_text.split("实体:", 1)[1].split("\n")[0]
                    # 这里可以添加更复杂的 JSON 解析
                    entities = {"raw": entities_part}
                except:
                    entities = {}

            return IntentAnalysis(
                intent=intent,
                confidence=confidence,
                entities=entities,
                clarification_needed=clarification_needed,
                clarification_questions=clarification_questions,
            )

        except Exception as e:
            logger.error(f"意图分析失败: {e}")
            return IntentAnalysis(
                "unclear", 0.0, {}, True, ["无法分析您的请求，请提供更多详细信息"]
            )

    async def create_plan(
        self, user_input: str, intent_analysis: IntentAnalysis
    ) -> Plan:
        """
        创建详细的执行计划

        将复杂任务分解为可管理的步骤，考虑依赖关系和并行执行。
        """
        try:
            logger.info("开始创建执行计划")

            plan_prompt = f"""
为用户的复杂任务创建详细的执行计划。

**用户任务**: "{user_input}"
**分析意图**: {intent_analysis.intent} (置信度: {intent_analysis.confidence:.2f})
**复杂度**: {intent_analysis.complexity_level}

**可用子智能体**:
- shell: Shell 命令执行 (ls, cd, mkdir, rm, ps, top 等)
- filesystem: 文件系统操作 (读写文件、列目录、搜索)
- browser: 浏览器自动化 (访问网页、截图、导航)
- manager: MCP 工具管理 (安装、列表、状态检查)
- dynamic: 动态创建的专门智能体

**规划要求**:
1. 将任务分解为具体的、可执行的步骤
2. 为每个步骤指定合适的智能体
3. 识别步骤间的依赖关系
4. 优化并行执行的可能性
5. 提供成功标准和预期结果

**输出格式**:
为每个步骤提供以下信息：
步骤编号. 步骤描述
- 分配智能体: [智能体名称]
- 依赖关系: [依赖的步骤编号，如果有]
- 成功标准: [如何判断步骤成功]
- 预期结果: [步骤完成后应该看到什么]

**示例**:
1. 检查当前目录结构
- 分配智能体: shell
- 依赖关系: 无
- 成功标准: 获得目录列表
- 预期结果: 显示当前目录的文件和文件夹

2. 读取配置文件
- 分配智能体: filesystem
- 依赖关系: 1
- 成功标准: 成功读取文件内容
- 预期结果: 显示配置文件的内容
"""

            from langchain_core.messages import HumanMessage

            messages = [HumanMessage(content=plan_prompt)]
            response = await self.llm.ainvoke(messages)
            plan_text = str(response.content)

            # 创建计划对象
            plan = Plan(
                id=str(uuid.uuid4()), goal=user_input, status=TaskStatus.PENDING
            )

            # 解析计划文本
            lines = plan_text.split("\n")
            current_task = None
            task_counter = 1

            for line in lines:
                line = line.strip()
                if line and any(line.startswith(str(i) + ".") for i in range(1, 20)):
                    # 新任务开始
                    if current_task:
                        plan.tasks.append(current_task)

                    task_desc = line.split(".", 1)[1].strip() if "." in line else line
                    current_task = Task(
                        id=str(uuid.uuid4()),
                        description=task_desc,
                        status=TaskStatus.PENDING,
                    )
                    task_counter += 1

                elif current_task and line.startswith("-"):
                    # 任务详情
                    if "分配智能体:" in line:
                        agent_part = line.split(":", 1)[1].strip().lower()
                        if "shell" in agent_part:
                            current_task.assigned_agent = "shell"
                        elif "file" in agent_part or "filesystem" in agent_part:
                            current_task.assigned_agent = "filesystem"
                        elif "browser" in agent_part or "web" in agent_part:
                            current_task.assigned_agent = "browser"
                        elif "manager" in agent_part:
                            current_task.assigned_agent = "manager"
                        else:
                            current_task.assigned_agent = "general"

            if current_task:
                plan.tasks.append(current_task)

            # 如果没有解析到任务，创建一个默认任务
            if not plan.tasks:
                default_task = Task(
                    id=str(uuid.uuid4()),
                    description=user_input,
                    assigned_agent=self._get_default_agent(intent_analysis.intent),
                    status=TaskStatus.PENDING,
                )
                plan.tasks.append(default_task)

            logger.info(f"创建计划完成，共 {len(plan.tasks)} 个任务")
            return plan

        except Exception as e:
            logger.error(f"计划创建失败: {e}")
            # 返回简单计划
            plan = Plan(
                id=str(uuid.uuid4()),
                goal=user_input,
                tasks=[
                    Task(
                        id=str(uuid.uuid4()),
                        description=user_input,
                        assigned_agent="general",
                        status=TaskStatus.PENDING,
                    )
                ],
            )
            return plan

    async def execute_plan(self, plan: Plan) -> Dict[str, Any]:
        """
        执行计划 - 协调各个子智能体的任务执行

        支持并行执行和依赖关系管理。
        """
        try:
            logger.info(f"开始执行计划: {plan.id}")
            plan.status = TaskStatus.IN_PROGRESS

            # 创建任务执行图
            execution_graph = self._build_execution_graph(plan.tasks)

            # 执行任务（考虑依赖关系）
            results = []
            completed_tasks = set()

            # 第一遍：执行无依赖的任务
            independent_tasks = [task for task in plan.tasks if not task.dependencies]

            if independent_tasks:
                logger.info(f"并行执行 {len(independent_tasks)} 个独立任务")
                independent_results = await asyncio.gather(
                    *[self._execute_single_task(task) for task in independent_tasks],
                    return_exceptions=True,
                )

                # 处理结果
                for i, result in enumerate(independent_results):
                    task = independent_tasks[i]
                    if isinstance(result, Exception):
                        task.error = str(result)
                        task.status = TaskStatus.FAILED
                        results.append(
                            ExecutionResult(
                                task_id=task.id,
                                agent_name=task.assigned_agent or "unknown",
                                success=False,
                                error=str(result),
                            )
                        )
                    else:
                        task.result = result
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.now()
                        completed_tasks.add(task.id)
                        results.append(
                            ExecutionResult(
                                task_id=task.id,
                                agent_name=task.assigned_agent or "unknown",
                                success=True,
                                result=result,
                            )
                        )

            # 第二遍：执行有依赖的任务
            remaining_tasks = [
                task for task in plan.tasks if task.id not in completed_tasks
            ]

            for task in remaining_tasks:
                # 检查依赖是否满足
                if not self._are_dependencies_satisfied(task, completed_tasks):
                    logger.warning(f"任务 {task.id} 的依赖未满足，跳过执行")
                    task.status = TaskStatus.BLOCKED
                    task.error = "依赖任务未完成"
                    results.append(
                        ExecutionResult(
                            task_id=task.id,
                            agent_name=task.assigned_agent or "unknown",
                            success=False,
                            error="依赖任务未完成",
                        )
                    )
                    continue

                # 执行任务
                result = await self._execute_single_task(task)
                if isinstance(result, Exception):
                    task.error = str(result)
                    task.status = TaskStatus.FAILED
                    results.append(
                        ExecutionResult(
                            task_id=task.id,
                            agent_name=task.assigned_agent or "unknown",
                            success=False,
                            error=str(result),
                        )
                    )
                else:
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    completed_tasks.add(task.id)
                    results.append(
                        ExecutionResult(
                            task_id=task.id,
                            agent_name=task.assigned_agent or "unknown",
                            success=True,
                            result=result,
                        )
                    )

            plan.status = TaskStatus.COMPLETED

            # 创建执行摘要
            summary = PlanExecutionSummary(
                plan_id=plan.id,
                goal=plan.goal,
                total_tasks=len(plan.tasks),
                completed_tasks=len([r for r in results if r.success]),
                failed_tasks=len([r for r in results if not r.success]),
                blocked_tasks=0,  # 这里可以计算阻塞任务
                total_execution_time=sum(r.execution_time or 0 for r in results),
                results=results,
            )

            logger.info(
                f"计划执行完成: {summary.completed_tasks}/{summary.total_tasks} 任务成功"
            )

            return {
                "plan_id": plan.id,
                "goal": plan.goal,
                "summary": summary,
                "results": [r.to_dict() for r in results],
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"计划执行失败: {e}")
            plan.status = TaskStatus.FAILED
            return {
                "plan_id": plan.id,
                "goal": plan.goal,
                "error": f"计划执行失败: {str(e)}",
                "status": "failed",
            }

    async def _execute_single_task(self, task: Task) -> str:
        """执行单个任务"""
        try:
            logger.info(f"执行任务: {task.description[:50]}...")

            # 获取对应的智能体
            agent = self._get_agent_for_task(task)
            if not agent:
                raise ValueError(f"没有找到适合任务的智能体: {task.assigned_agent}")

            # 执行任务
            result = await agent.execute_with_timeout(task)

            return result.result if result.success else result.error

        except Exception as e:
            logger.error(f"任务执行异常: {e}")
            raise

    def _get_agent_for_task(self, task: Task) -> Optional[SubAgent]:
        """根据任务获取对应的智能体"""
        agent_name = task.assigned_agent or "general"

        # 首先检查固定子智能体
        if agent_name in self.subagents:
            return self.subagents[agent_name]

        # 然后检查动态智能体
        if agent_name in self.dynamic_agents:
            return self.dynamic_agents[agent_name]

        # 默认使用通用智能体
        return self.subagents.get("general")

    def _get_default_agent(self, intent: str) -> str:
        """根据意图获取默认智能体"""
        intent_agent_map = {
            "shell_command": "shell",
            "file_operation": "filesystem",
            "web_browsing": "browser",
            "tool_management": "manager",
            "information_query": "general",
        }
        return intent_agent_map.get(intent, "general")

    async def _route_simple_task(
        self, user_input: str, intent_analysis: IntentAnalysis
    ) -> str:
        """路由简单任务到对应子智能体"""
        try:
            agent_name = self._get_default_agent(intent_analysis.intent)
            agent = self.subagents.get(agent_name)

            if agent:
                return await agent.process_task(user_input)
            else:
                return await self.subagents["general"].process_task(user_input)

        except Exception as e:
            logger.error(f"简单任务路由失败: {e}")
            return f"任务执行失败: {str(e)}"

    def _build_execution_graph(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """构建任务执行图（依赖关系）"""
        graph = {}
        for task in tasks:
            graph[task.id] = task.dependencies or []
        return graph

    def _are_dependencies_satisfied(self, task: Task, completed_tasks: set) -> bool:
        """检查任务依赖是否满足"""
        if not task.dependencies:
            return True
        return all(dep_id in completed_tasks for dep_id in task.dependencies)

    def _build_clarification_response(self, intent_analysis: IntentAnalysis) -> str:
        """构建澄清请求响应"""
        questions = "\n".join(f"- {q}" for q in intent_analysis.clarification_questions)

        return f"""🤔 需要更多信息来理解您的请求

**当前分析**: {intent_analysis.intent} (置信度: {intent_analysis.confidence:.2f})

**需要澄清的问题**:
{questions}

请提供更多详细信息，我就能更好地帮助您！"""

    def _format_execution_result(self, execution_result: Dict[str, Any]) -> str:
        """格式化执行结果"""
        try:
            summary = execution_result.get("summary")
            if not summary:
                return "执行完成，但没有可用的结果摘要。"

            # 构建结果摘要
            result_text = f"""🎯 任务执行完成

**目标**: {summary.goal}

**执行统计**:
- 总任务数: {summary.total_tasks}
- 成功任务: {summary.completed_tasks}
- 失败任务: {summary.failed_tasks}
- 执行时间: {summary.total_execution_time:.1f}秒

**详细结果**:
"""

            # 添加每个任务的结果
            for result in summary.results:
                status_icon = "✅" if result["success"] else "❌"
                agent_info = (
                    f" ({result['agent_name']})"
                    if result.get("agent_name") != "unknown"
                    else ""
                )

                result_text += (
                    f"\n{status_icon} {result['task_description']}{agent_info}"
                )

                if result["success"]:
                    # 截取结果预览
                    result_preview = str(result.get("result", ""))[:200]
                    if len(str(result.get("result", ""))) > 200:
                        result_preview += "..."
                    result_text += f"\n   结果: {result_preview}"
                else:
                    result_text += f"\n   错误: {result.get('error', '未知错误')}"

            return result_text

        except Exception as e:
            logger.error(f"格式化执行结果失败: {e}")
            return f"任务执行完成，但结果格式化失败: {str(e)}"

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        subagent_stats = {}
        for name, agent in self.subagents.items():
            subagent_stats[name] = agent.get_stats()

        return {
            "main_agent": self.get_stats(),
            "subagents": subagent_stats,
            "total_subagents": len(self.subagents),
            "dynamic_agents": len(self.dynamic_agents),
            "active_plans": len(self.plans),
            "active_tasks": len(self.active_tasks),
        }

    def list_available_agents(self) -> List[Dict[str, Any]]:
        """列出所有可用智能体"""
        agents = []

        # 主智能体
        agents.append(
            {
                "name": self.name,
                "type": self.agent_type.value,
                "capabilities": self.capabilities.to_dict()
                if hasattr(self.capabilities, "to_dict")
                else {},
                "is_main": True,
            }
        )

        # 子智能体
        for name, agent in self.subagents.items():
            agents.append(
                {
                    "name": agent.name,
                    "type": agent.agent_type.value,
                    "capabilities": agent.capabilities.to_dict()
                    if hasattr(agent.capabilities, "to_dict")
                    else {},
                    "is_main": False,
                }
            )

        return agents
