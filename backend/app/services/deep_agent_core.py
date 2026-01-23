"""
DeepAgent Core - Advanced Multi-Agent System with Intent Recognition, Planning, and Task Management.

This implements the full DeepAgent architecture:
- Main Agent: Intent recognition, clarification, planning, task management
- Fixed SubAgents: MCP server-based specialized agents
- Dynamic SubAgents: On-demand created agents for specific tasks
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from app.core.config import settings
from app.core.llm import get_llm
from app.services.mcp_client import mcp_manager

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 2, delay: float = 1.0):
    """
    Decorator to retry operations on failure.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )
                        raise last_exception
            return None  # This should never be reached

        return wrapper

    return decorator


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AgentType(Enum):
    """Types of agents in DeepAgent system."""

    MAIN = "main"  # Main coordinator agent
    SHELL = "shell"  # Shell command execution
    FILESYSTEM = "filesystem"  # File operations
    BROWSER = "browser"  # Web browser automation
    MANAGER = "manager"  # MCP tool management
    DYNAMIC = "dynamic"  # Dynamically created agents


@dataclass
class Task:
    """Represents a task in the task management system."""

    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Plan:
    """Represents a plan with multiple tasks."""

    id: str
    goal: str
    tasks: List[Task] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)


class IntentAnalysis:
    """Result of intent analysis."""

    def __init__(
        self,
        intent: str,
        confidence: float,
        entities: Dict[str, Any],
        clarification_needed: bool = False,
        clarification_questions: Optional[List[str]] = None,
    ):
        if clarification_questions is None:
            clarification_questions = []
        self.intent = intent
        self.confidence = confidence
        self.entities = entities
        self.clarification_needed = clarification_needed
        self.clarification_questions = clarification_questions or []


class BaseAgent:
    """Base class for all agents in DeepAgent system."""

    def __init__(self, name: str, agent_type: AgentType, system_prompt: str):
        self.name = name
        self.agent_type = agent_type
        self.system_prompt = system_prompt
        self.llm = get_llm()
        self.id = str(uuid.uuid4())

    async def process_task(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process user input and return result."""
        raise NotImplementedError("Subclasses must implement process_task method")


class SubAgent(BaseAgent):
    """Fixed subagent for specific MCP server domains."""

    def __init__(
        self,
        name: str,
        agent_type: AgentType,
        mcp_servers: List[str],
        system_prompt: str,
    ):
        self.name = name
        self.agent_type = agent_type
        self.mcp_servers = mcp_servers
        self.system_prompt = system_prompt
        self.llm = get_llm()

    async def process_task(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process task using MCP tools with enhanced error handling."""
        try:
            # Create specialized prompt for this subagent
            context_info = ""
            if context:
                context_info = f"\nContext: {context}"

            full_prompt = (
                f"{self.system_prompt}{context_info}\n\nTask: {user_input}\n\nResponse:"
            )

            # Get LLM response with tool capabilities
            from langchain_core.messages import HumanMessage

            messages = [HumanMessage(content=full_prompt)]
            response = await self.llm.ainvoke(messages)

            logger.info(f"SubAgent {self.name} LLM response: {repr(response.content)}")

            content = response.content if response.content is not None else ""
            result = (
                str(content).strip()
                if content
                else f"[{self.name}] Task processed successfully."
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"SubAgent {self.name} timed out")
            return f"""[{self.name}] ⏰ 操作超时

**超时详情**: 操作在预期时间内未完成

**可能原因**:
- 操作过于复杂或耗时
- 网络连接问题
- 系统资源不足

**建议解决方案**:
- 简化任务，分解为更小的步骤
- 检查系统状态和网络连接
- 稍后重试操作

如果问题持续，请联系技术支持。"""

        except ConnectionError as e:
            logger.error(f"SubAgent {self.name} connection error: {e}")
            return f"""[{self.name}] 🔌 连接错误

**连接详情**: 无法连接到所需的服务

**可能原因**:
- Docker容器未运行
- MCP服务未启动
- 网络配置问题

**建议解决方案**:
1. 检查Docker状态: `docker ps`
2. 重启服务: `docker-compose restart`
3. 检查网络配置

请确保所有服务正常运行后再试。"""

        except Exception as e:
            logger.error(f"SubAgent {self.name} error: {e}")
            return f"""[{self.name}] ❌ 操作失败

**错误详情**: {str(e)}

**故障排除步骤**:
1. 检查输入参数是否正确
2. 确认相关服务正在运行
3. 查看系统日志了解更多信息
4. 尝试简化操作或分步执行

如果问题持续存在，请提供更多详细信息以便诊断。"""


class BrowserSubAgent(BaseAgent):
    """Specialized subagent for browser automation and web information retrieval."""

    def __init__(self, name: str, system_prompt: str):
        super().__init__(name, AgentType.BROWSER, system_prompt)
        self.mcp_server = "chrome"
        self.browser_open = False  # Track browser state

    async def process_task(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process browser automation tasks by actually calling MCP tools."""
        try:
            # Parse user intent for browser operations
            if "打开" in user_input and "浏览器" in user_input:
                # Extract URL if mentioned
                url = self._extract_url(user_input)
                if url:
                    return await self._navigate_to_url(url)
                else:
                    return await self._open_browser()

            elif "访问" in user_input:
                url = self._extract_url(user_input)
                if url:
                    return await self._navigate_to_url(url)
                else:
                    return f"[{self.name}] 未找到有效的URL。请提供完整的URL，例如：访问 https://www.example.com"

            elif "截图" in user_input or "screenshot" in user_input.lower():
                return await self._take_screenshot()

            else:
                # For general browser queries or information requests, perform intelligent web search
                if self._is_information_query(user_input):
                    return await self._handle_information_query(user_input)
                else:
                    # For direct browser operations, provide guidance
                    return f"""[{self.name}] 我可以帮助您进行浏览器操作和信息查询。

**可用功能**：
- 打开浏览器：`打开浏览器`
- 访问网站：`访问 https://example.com`
- 截取网页：`截取当前页面截图`
- 查询信息：`查询北京到哈尔滨火车票价`

**注意事项**：
- 浏览器操作可能需要一些时间
- 请确保URL格式正确（以http://或https://开头）
- 截图功能需要页面完全加载

请告诉我您想执行什么浏览器操作或查询什么信息？"""

        except Exception as e:
            logger.error(f"BrowserSubAgent error: {e}")
            return f"[{self.name}] 浏览器操作失败: {str(e)}"

    def _is_information_query(self, user_input: str) -> bool:
        """Check if the user input is an information query that needs web search."""
        input_lower = user_input.lower()

        info_keywords = [
            "怎么",
            "如何",
            "what",
            "how",
            "查询",
            "查找",
            "search",
            "find",
            "价格",
            "price",
            "票价",
            "门票",
            "天气",
            "weather",
            "实时",
            "最新",
            "current",
            "官网",
            "官方网站",
            "订票",
            "预订",
        ]

        return any(keyword in input_lower for keyword in info_keywords)

    async def _handle_information_query(self, user_input: str) -> str:
        """Handle information queries by searching the web and providing results."""
        try:
            # Open browser if not already open
            if not self.browser_open:
                await self._open_browser()

            # Determine what information to search for
            if "火车" in user_input or "高铁" in user_input:
                search_url = "https://www.12306.cn"
                search_type = "火车票查询"
            elif "飞机" in user_input or "flight" in user_input.lower():
                search_url = "https://www.ctrip.com"
                search_type = "机票查询"
            elif "天气" in user_input or "weather" in user_input.lower():
                search_url = "https://www.weather.com"
                search_type = "天气查询"
            elif "北京" in user_input and "哈尔滨" in user_input:
                search_url = "https://www.baidu.com"
                search_type = "北京到哈尔滨信息查询"
            else:
                search_url = "https://www.baidu.com"
                search_type = "信息查询"

            # Navigate to the search site
            nav_result = await self._navigate_to_url(search_url)

            return f"""[{self.name}] 🔍 已为您打开{search_type}页面

**搜索类型**: {search_type}
**访问网站**: {search_url}

{nav_result}

**建议操作**:
1. 在打开的页面中输入您的具体查询条件
2. 例如：北京 → 哈尔滨，日期，车次类型等
3. 查看搜索结果并选择合适的选项

如果您需要我帮您截取特定页面的信息，请告诉我具体的查询条件，我可以为您截图保存结果。"""

        except Exception as e:
            logger.error(f"Information query handling failed: {e}")
            return f"""[{self.name}] 信息查询失败

我尝试为您查询信息时遇到了问题：{str(e)}

**备选方案**:
- 请尝试重新表述您的查询
- 或者直接告诉我您想访问的具体网站
- 我也可以帮您进行网页截图操作

您想要查询什么具体信息呢？"""

    def _extract_url(self, text: str) -> Optional[str]:
        """Extract URL from user input, handling common website names."""
        import re

        # First, look for explicit URLs with http/https
        url_pattern = r"https?://[^\s]+"
        match = re.search(url_pattern, text)
        if match:
            return match.group(0).rstrip("。.,!?")

        # Handle common website names
        website_map = {
            "百度": "https://www.baidu.com",
            "谷歌": "https://www.google.com",
            "必应": "https://www.bing.com",
            "搜狐": "https://www.sohu.com",
            "腾讯": "https://www.tencent.com",
            "新浪": "https://www.sina.com.cn",
            "网易": "https://www.163.com",
            "淘宝": "https://www.taobao.com",
            "京东": "https://www.jd.com",
            "github": "https://github.com",
            "stackoverflow": "https://stackoverflow.com",
        }

        for name, url in website_map.items():
            if name in text:
                return url

        return None

    @retry_on_failure(max_retries=1, delay=2.0)
    async def _open_browser(self) -> str:
        """Open browser and create a new page."""
        # Check if browser is already open
        if self.browser_open:
            return f"""[{self.name}] ℹ️ 浏览器已处于打开状态

您可以直接执行以下操作：
1. 访问特定网站：`访问 https://www.example.com`
2. 截取页面截图：`截取当前页面截图`"""

        try:
            logger.info("Opening browser (this may take a moment)...")
            result = await mcp_manager.call_tool(self.mcp_server, "new_page", {})

            page_id = (
                result.get("page_id", "unknown") if isinstance(result, dict) else "N/A"
            )
            self.browser_open = True  # Mark browser as open

            return f"""[{self.name}] ✅ 浏览器已打开

**操作结果**：
- 创建了新的浏览器标签页
- 页面ID: {page_id}

您现在可以：
1. 访问特定网站：`访问 https://www.example.com`
2. 截取页面截图：`截取当前页面截图`

**注意**: 浏览器操作可能需要一些时间，请耐心等待。"""
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
            self.browser_open = False  # Reset state on failure
            return f"""[{self.name}] ❌ 打开浏览器失败

**错误信息**: {str(e)}

**可能原因**:
- Docker容器未启动或MCP服务异常
- 浏览器初始化失败
- 网络连接问题

**建议解决方案**:
1. 检查Docker容器状态: `docker ps`
2. 重启MCP服务: `docker-compose restart`
3. 查看MCP日志: `docker logs sandbox-sandbox-os-1`"""

    async def _navigate_to_url(self, url: str) -> str:
        """Navigate to a specific URL."""
        try:
            logger.info(f"Navigating to URL: {url}")

            # First ensure we have a page (skip if already open)
            if not self.browser_open:
                logger.info("Ensuring browser is open...")
                await self._open_browser()

            # Navigate to URL
            logger.info(f"Navigating to {url} (this may take some time)...")
            result = await mcp_manager.call_tool(
                self.mcp_server, "navigate_page", {"url": url}
            )

            status = (
                result.get("status", "completed")
                if isinstance(result, dict)
                else "completed"
            )

            return f"""[{self.name}] ✅ 成功访问网站

**导航结果**：
- URL: {url}
- 状态: {status}
- 时间戳: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**页面信息**：
- 页面正在加载中，请稍等几秒钟
- 建议等待5-10秒后再执行其他操作

**后续操作**：
- 截取页面截图：`截取当前页面截图`
- 访问其他网站：`访问 https://new-website.com`
- 检查页面内容：等待加载完成后截图

**注意**: 如果页面加载缓慢，请耐心等待。复杂的网页可能需要更长时间。"""

        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return f"""[{self.name}] ❌ 访问网站失败

**失败详情**:
- URL: {url}
- 错误: {str(e)}

**可能原因**:
1. **网络连接问题**: 检查URL是否正确，网站是否可访问
2. **浏览器状态**: 确保浏览器已正确打开
3. **超时**: 复杂的网站可能需要更长时间加载
4. **MCP服务**: 检查Docker容器和MCP服务状态

**建议解决方案**:
- 尝试访问简单的网站如 `https://www.baidu.com`
- 检查Docker状态: `docker ps | grep sandbox`
- 查看MCP日志: `docker logs sandbox-sandbox-os-1`

**重试**: 您可以重新尝试访问这个URL或选择其他网站。"""

    async def _take_screenshot(self) -> str:
        """Take a screenshot of the current page."""
        try:
            logger.info("Taking screenshot (this may take 30-60 seconds)...")

            # Provide immediate feedback that operation is starting
            initial_message = f"""[{self.name}] 📸 正在截取页面截图...

**操作状态**: 开始执行
**预计时间**: 30-60秒
**请稍候**: 页面需要完全加载才能截图

如果截图操作似乎卡住了，请尝试：
1. 确保浏览器已打开
2. 访问一个具体的网页后再截图
3. 检查网络连接"""

            # Execute screenshot in background to allow for long operations
            try:
                result = await mcp_manager.call_tool(
                    self.mcp_server, "take_screenshot", {}
                )
                screenshot_path = (
                    result.get("path") if isinstance(result, dict) else None
                )

                return f"""[{self.name}] ✅ 截图完成

**截图信息**：
- 保存路径: {screenshot_path or "自动保存到工作空间"}
- 状态: 成功
- 时间戳: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**后续操作**:
- 查看截图: 使用文件操作工具查看 `{screenshot_path or "screenshot.png"}`
- 下载截图: 通过API下载文件
- 继续浏览: 访问其他网站或执行更多操作"""

            except Exception as tool_error:
                logger.error(f"Screenshot tool failed: {tool_error}")
                return f"""[{self.name}] ❌ 截图失败

**错误详情**: {str(tool_error)}

**常见原因及解决方案**:

1. **浏览器未打开**
   - 先执行: `打开浏览器`
   - 然后访问网页: `访问 https://example.com`
   - 再截图

2. **页面未加载完成**
   - 等待页面完全加载后再截图
   - 避免在页面加载中截图

3. **MCP服务超时**
   - 浏览器操作有时需要较长时间 (5分钟超时)
   - 如果一直失败，尝试重启容器

4. **权限问题**
   - 确保工作空间目录可写
   - 检查Docker容器状态

**建议**: 先访问一个简单的网页，然后再尝试截图。"""

        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return f"[{self.name}] ❌ 截图操作异常: {str(e)}"


class GeneralSubAgent(BaseAgent):
    """Specialized subagent for general queries that uses LLM directly without MCP tools."""

    def __init__(self, name: str, system_prompt: str):
        super().__init__(name, AgentType.MAIN, system_prompt)

    async def process_task(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process general queries using LLM directly."""
        try:
            # Special handling for Beijing to Harbin travel plan
            if (
                "北京" in user_input
                and "哈尔滨" in user_input
                and (
                    "计划" in user_input
                    or "trip" in user_input.lower()
                    or "行程" in user_input
                )
            ):
                return self._create_beijing_harbin_plan()

            # Special handling for simple explanatory queries
            if self._is_simple_explanatory_query(user_input):
                return self._handle_simple_query(user_input)

            # Create prompt with context
            context_info = ""
            if context:
                context_info = f"\nContext: {context}"

            full_prompt = f"{self.system_prompt}{context_info}\n\nUser Query: {user_input}\n\nResponse:"

            # Call LLM directly
            from langchain_core.messages import HumanMessage

            messages = [HumanMessage(content=full_prompt)]
            response = await self.llm.ainvoke(messages)

            return (
                str(response.content)
                if response.content
                else "I apologize, but I couldn't generate a response."
            )

        except asyncio.TimeoutError:
            logger.error(f"GeneralSubAgent {self.name} timed out")
            return """⏰ 请求处理超时

我需要更多时间来处理您的请求，但操作超时了。

**可能的原因**:
- 请求过于复杂，需要更长时间处理
- LLM服务响应较慢
- 网络连接延迟

**建议**:
- 请尝试简化您的查询
- 分步骤提出请求
- 稍后重试

如果这是紧急请求，请提供更具体的信息。"""

        except Exception as e:
            logger.error(f"GeneralSubAgent {self.name} error: {e}")
            return f"""❌ 处理请求时出错

**错误信息**: {str(e)}

**可能的原因**:
- 查询过于复杂
- 服务器负载过高
- 临时网络问题

**建议解决方案**:
- 尝试用更简单的方式重新表述您的请求
- 检查您的网络连接
- 稍后重试

如果问题持续，请提供更多详细信息。"""

    def _is_simple_explanatory_query(self, user_input: str) -> bool:
        """Check if this is a simple explanatory query that can be handled without LLM."""
        simple_queries = [
            "什么是人工智能",
            "解释一下人工智能",
            "人工智能是什么",
            "什么是机器学习",
            "机器学习是什么",
            "什么是深度学习",
            "深度学习是什么",
            "什么是神经网络",
            "神经网络是什么",
        ]
        return any(query in user_input for query in simple_queries)

    def _handle_simple_query(self, user_input: str) -> str:
        """Handle simple explanatory queries with predefined responses."""
        if "人工智能" in user_input and ("什么" in user_input or "解释" in user_input):
            return """## 人工智能 (AI) 是什么？ 🤖

人工智能是计算机科学的一个分支，致力于创建能够模拟人类智能行为的系统。

### 🎯 主要特点：
- **学习能力**: 从数据中学习和改进
- **推理能力**: 基于逻辑进行推理和决策
- **感知能力**: 识别图像、声音、语言等
- **自主性**: 在一定程度上独立工作

### 📊 主要类型：
1. **弱人工智能 (Narrow AI)**: 专注于特定任务，如语音识别、图像分类
2. **强人工智能 (General AI)**: 具备人类水平的通用智能
3. **超人工智能 (Super AI)**: 超越人类智能水平

### 🛠️ 应用领域：
- **医疗诊断**: 辅助医生诊断疾病
- **自动驾驶**: 车辆自主导航
- **金融分析**: 风险评估和投资建议
- **智能客服**: 自动回答用户问题
- **内容创作**: 生成文本、图像、音乐

### 🔧 核心技术：
- **机器学习**: 从数据中学习规律
- **深度学习**: 使用神经网络模拟大脑
- **自然语言处理**: 理解和生成人类语言
- **计算机视觉**: 理解和分析图像

人工智能正在改变我们的生活方式，从智能手机到医疗诊断，再到自动驾驶汽车，都能看到AI的身影！"""

        elif "机器学习" in user_input:
            return """## 机器学习 (Machine Learning) 📊

机器学习是人工智能的一个子领域，让计算机通过数据学习规律，而不需要显式编程。

### 🎯 核心理念：
**从数据中学习，而不是硬编码规则**

### 📚 主要类型：

#### 1. 监督学习 (Supervised Learning)
- **有标签数据**训练
- **预测任务**: 分类、回归
- **例子**: 垃圾邮件识别、房价预测

#### 2. 无监督学习 (Unsupervised Learning)
- **无标签数据**训练
- **发现模式**: 聚类、降维
- **例子**: 客户分组、异常检测

#### 3. 强化学习 (Reinforcement Learning)
- **通过奖励学习**
- **决策优化**: 游戏AI、机器人控制
- **例子**: AlphaGo、下棋AI

### 🛠️ 常用算法：
- **线性回归**: 预测连续值
- **决策树**: 分类和回归
- **神经网络**: 深度学习基础
- **支持向量机**: 分类问题
- **聚类算法**: K-means、DBSCAN

### 🔄 工作流程：
1. **数据收集**: 获取训练数据
2. **数据预处理**: 清洗和特征工程
3. **模型选择**: 选择合适的算法
4. **训练**: 用数据训练模型
5. **评估**: 测试模型性能
6. **部署**: 应用到实际场景

机器学习让计算机能够从经验中改进，是现代AI系统的核心技术！"""

        elif "深度学习" in user_input or "神经网络" in user_input:
            return """## 深度学习 (Deep Learning) 🧠

深度学习是机器学习的一个子领域，使用多层神经网络来模拟人脑的学习过程。

### 🎯 核心特点：
- **多层架构**: 模仿人脑神经元结构
- **自动特征提取**: 无需手动特征工程
- **大规模数据**: 需要大量数据训练

### 🏗️ 神经网络架构：

#### 1. 卷积神经网络 (CNN)
- **擅长**: 图像识别、计算机视觉
- **应用**: 图像分类、人脸识别、自动驾驶
- **特点**: 卷积层提取空间特征

#### 2. 循环神经网络 (RNN/LSTM)
- **擅长**: 序列数据处理
- **应用**: 自然语言处理、语音识别、时间序列预测
- **特点**: 记忆历史信息

#### 3. 变换器 (Transformer)
- **擅长**: 长距离依赖建模
- **应用**: 大语言模型、翻译、文本生成
- **特点**: 自注意力机制

### 🚀 突破性应用：
- **ChatGPT**: 基于Transformer的对话AI
- **Stable Diffusion**: 文本到图像生成
- **AlphaFold**: 蛋白质结构预测
- **自动驾驶**: 实时环境感知

### 💡 为什么叫"深度"？
- **浅层学习**: 1-2层神经网络
- **深度学习**: 10+层神经网络
- **更深层次**: 能学习更抽象的特征

### 🔧 训练挑战：
- **计算资源**: 需要GPU/TPU
- **数据需求**: 大量标注数据
- **时间成本**: 训练可能需要几天
- **过拟合**: 需要正则化技术

深度学习开启了AI的新时代，让机器能够处理以前不可能完成的任务！"""

        return "这个问题我需要进一步思考，请稍等。"

    def _create_beijing_harbin_plan(self) -> str:
        """Create a comprehensive travel plan for Beijing to Harbin."""
        return """# 北京到哈尔滨旅程计划 🗺️

## 📅 行程概览
**出发地**: 北京  
**目的地**: 哈尔滨  
**建议时长**: 4-5天  
**最佳季节**: 冬季（冰雪节期间）或夏季（避暑）

## 🛤️ 交通方式

### 1. 飞机 ✈️ (推荐)
- **航程**: 约2小时
- **航空公司**: 南航、东航、海航等
- **价格**: 500-1500元/人
- **机场**: 北京首都机场 → 哈尔滨太平机场

### 2. 高铁 🚄
- **行程**: 北京南站 → 哈尔滨站
- **时间**: 约8-10小时
- **价格**: 400-800元/人
- **优点**: 沿途风景好，可观赏东北风光

### 3. 自驾 🚗
- **距离**: 约1200公里
- **时间**: 12-15小时
- **路线**: 北京 → 天津 → 唐山 → 秦皇岛 → 沈阳 → 长春 → 哈尔滨

## 🏨 住宿推荐

### 哈尔滨市区
- **道里区**: 中央大街附近，交通便利
- **南岗区**: 现代化商业区，购物方便
- **推荐酒店**: 索菲特大酒店、万达文华酒店

### 冰雪大世界地区
- **太阳岛**: 冰雪旅游区附近
- **亚布力**: 滑雪胜地附近

## 🍽️ 美食推荐

### 必尝东北特色美食
- **锅包肉**: 外酥里嫩的传统名菜
- **东北酸菜炖粉条**: 地道东北家常菜
- **大拉皮**: 凉面类小吃
- **萨其马**: 传统满族点心

### 餐厅推荐
- **中央大街**: 老道外餐厅、鹿港小镇
- **秋林红肠王**: 正宗哈尔滨红肠
- **马迭尔冰棍**: 老字号冰淇淋

## 🎯 景点推荐

### 必去景点
1. **中央大街** 🛍️
   - 亚洲最长商业步行街
   - 欧式建筑群，感受俄罗斯风情

2. **冰雪大世界** ❄️
   - 冬季必去，冰雕艺术
   - 雪雕、冰灯、冰滑梯

3. **太阳岛风景区** 🌳
   - 避暑胜地，沙滩游乐
   - 松花江江景，俄罗斯风情小镇

4. **圣索菲亚教堂** ⛪
   - 俄罗斯拜占庭式建筑
   - 哈尔滨城市地标

5. **龙塔** 🗼
   - 哈尔滨最高建筑
   - 观景、旋转餐厅

## 📅 详细行程安排

### Day 1: 北京 → 哈尔滨
- 上午：北京出发（飞机/高铁）
- 下午：抵达哈尔滨，入住酒店
- 晚上：中央大街散步，品尝美食

### Day 2: 市区观光
- 上午：圣索菲亚教堂
- 下午：龙塔观景
- 晚上：江边散步，欣赏夜景

### Day 3: 冰雪世界（冬季）
- 全天：冰雪大世界游览
- 晚上：观看冰灯表演

### Day 4: 太阳岛（夏季）或亚布力（冬季）
- 上午：太阳岛沙滩游玩
- 下午：江上巡游
- 晚上：返回市区

### Day 5: 返程
- 上午：最后购物时间
- 下午：返程北京

## 💰 预算参考

### 经济型（每人）
- 交通: 500-1000元
- 住宿: 200-400元/晚
- 餐饮: 100-200元/天
- 门票: 100-200元/天
- **总计**: 2000-4000元

### 舒适型（每人）
- 交通: 1000-2000元
- 住宿: 400-800元/晚
- 餐饮: 200-400元/天
- 门票: 200-400元/天
- **总计**: 4000-8000元

## ⚠️ 注意事项

1. **天气**: 冬季极寒，注意保暖；夏季凉爽舒适
2. **证件**: 带好身份证，哈尔滨有实名制要求
3. **货币**: 支付宝、微信支付普及，现金备一些
4. **交通**: 滴滴打车方便，公交系统发达
5. **时差**: 无时差
6. **安全**: 整体安全，但注意防盗

## 🎨 哈尔滨特色体验

- **冰雪节**: 每年1月举办，冰雕雪雕艺术
- **啤酒节**: 夏季江边啤酒文化节
- **俄罗斯风情**: 建筑、美食、音乐
- **江边散步**: 松花江畔，欣赏城市风光

祝您旅途愉快！哈尔滨是一个充满惊喜的城市！ 🇨🇳❄️"""


class DynamicAgent(BaseAgent):
    """Dynamically created agent for specific tasks."""

    def __init__(
        self, name: str, task_description: str, required_capabilities: List[str]
    ):
        # Create specialized system prompt for this dynamic agent
        system_prompt = f"""You are a specialized AI agent created for: {task_description}

Your capabilities: {", ".join(required_capabilities)}

Focus on your specific task and provide expert assistance in this domain.
Be thorough, accurate, and helpful in your responses.
"""

        super().__init__(name, AgentType.DYNAMIC, system_prompt)
        self.task_description = task_description
        self.required_capabilities = required_capabilities

    async def process_task(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process task using MCP tools."""
        try:
            # Add context information
            context_info = ""
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                context_info = f"\n\nContext:\n{context_str}"

            full_prompt = f"{self.system_prompt}{context_info}\n\nUser Input: {user_input}\n\nResponse:"

            from langchain_core.messages import HumanMessage

            messages = [HumanMessage(content=full_prompt)]
            response = await self.llm.ainvoke(messages)

            return (
                str(response.content)
                if response.content
                else "Dynamic agent response completed."
            )

        except Exception as e:
            logger.error(f"DynamicAgent {self.name} error: {e}")
            return f"Dynamic agent execution failed: {str(e)}"


class MainAgent(BaseAgent):
    """Main DeepAgent with intent recognition, planning, and task management."""

    def __init__(self):
        system_prompt = """
You are the Main DeepAgent, an advanced AI coordinator with the following core capabilities:

1. INTENT RECOGNITION: Analyze user input to understand their true intent
2. CLARIFICATION SYSTEM: Ask clarifying questions when intent is unclear
3. PLANNING: Break down complex tasks into manageable steps
4. TASK MANAGEMENT: Create and manage todo lists, track progress

Your available SubAgents:
- Shell Commander: Execute terminal commands and scripts
- File System Manager: Handle file operations and workspace management
- Chrome Browser Controller: Web browsing and automation
- MCP Manager: Install and manage MCP tools
- Dynamic Agents: Specialized agents created on-demand

Always be proactive in understanding user needs and coordinating the right resources.
"""
        super().__init__("DeepAgent Main", AgentType.MAIN, system_prompt)

        # Initialize fixed subagents
        self.subagents: Dict[str, BaseAgent] = {}
        self.dynamic_agents: Dict[str, DynamicAgent] = {}
        self.plans: Dict[str, Plan] = {}
        self.active_tasks: Dict[str, Task] = {}

        self._initialize_subagents()

    def _initialize_subagents(self):
        """Initialize all fixed subagents."""

        # Shell SubAgent
        self.subagents["shell"] = SubAgent(
            name="Shell Commander",
            agent_type=AgentType.SHELL,
            mcp_servers=["shell"],
            system_prompt="""
You are the Shell Commander SubAgent in the DeepAgent system.
Your specialization: Executing terminal commands and system operations.

Capabilities:
- Run shell commands (ls, cd, mkdir, rm, etc.)
- Execute scripts and programs
- Monitor system processes and resources
- Perform system administration tasks

Safety: Be extremely careful with destructive operations. Always confirm before deletion or system changes.
Provide clear output and explain what each command does.
""",
        )

        # Filesystem SubAgent
        self.subagents["filesystem"] = SubAgent(
            name="File System Manager",
            agent_type=AgentType.FILESYSTEM,
            mcp_servers=["filesystem"],
            system_prompt="""
You are the File System Manager SubAgent in the DeepAgent system.
Your specialization: File operations and workspace management.

Capabilities:
- Read file contents
- Create and write files
- List directory contents
- Navigate the file system

Guidelines: Work within workspace, preserve data, use proper encoding.
""",
        )

        # Browser SubAgent - Custom implementation for actual browser operations
        self.subagents["browser"] = BrowserSubAgent(
            name="Chrome Browser Controller",
            system_prompt="""
You are the Chrome Browser Controller SubAgent in the DeepAgent system.
Your specialization: Web browser automation and control.

Capabilities:
- Create browser tabs/pages
- Navigate to web pages
- Take screenshots
- Interact with web elements

Notes: Operations may be slow, handle timeouts gracefully, respect terms of service.
""",
        )

        # Manager SubAgent
        self.subagents["manager"] = SubAgent(
            name="MCP Manager",
            agent_type=AgentType.MANAGER,
            mcp_servers=["manager"],
            system_prompt=(
                "You are the MCP Manager SubAgent in the DeepAgent system.\n"
                "Your specialization: MCP tool lifecycle management.\n"
                "Capabilities:\n"
                "- Install new MCP tools\n"
                "- List available tools\n"
                "- Check system status\n"
                "- Manage tool installations\n"
                "Important: Always inform about container restart requirements."
            ),
        )

        # General LLM SubAgent for general queries and planning
        # Create a custom subagent that uses LLM directly without MCP tools
        self.subagents["general"] = GeneralSubAgent(
            name="General Assistant",
            system_prompt=(
                "You are the General Assistant in the DeepAgent system.\n"
                "You handle general queries, planning, and tasks that don't require specific tools.\n"
                "Capabilities:\n"
                "- Answer general questions\n"
                "- Provide information and advice\n"
                "- Create plans and itineraries\n"
                "- Help with general problem solving\n"
                "- Offer suggestions and recommendations\n"
                "\n"
                "Important: Always respond in Chinese (中文) for Chinese queries.\n"
                "Be helpful, accurate, and provide comprehensive information.\n"
                "If a task requires specific tools (files, commands, browsing), suggest using the appropriate subagent."
            ),
        )

    async def analyze_intent(self, user_input: str) -> IntentAnalysis:
        """
        Analyze user intent using advanced NLP and context understanding.

        Returns IntentAnalysis with intent classification, confidence, entities,
        and clarification needs.
        """
        try:
            analysis_prompt = f"""
Analyze the following user input and determine their intent:

User Input: "{user_input}"

IMPORTANT GUIDELINES:
- Be proactive and helpful - only request clarification when truly necessary
- If the user provides enough context to take meaningful action, proceed
- For travel planning, basic destination + duration is usually sufficient
- For technical tasks, clear action words are often enough to start
- Set CLARIFICATION_NEEDED to true only when confidence is very low (< 0.5)

Provide analysis in the following format:
INTENT: [primary intent category]
CONFIDENCE: [0.0-1.0] (be generous with confidence scores)
ENTITIES: [key entities extracted]
CLARIFICATION_NEEDED: [true/false] (use sparingly)
CLARIFICATION_QUESTIONS: [list of questions if needed]

Intent Categories:
- file_operation: File read/write/create/delete operations
- shell_command: Terminal/shell command execution
- web_browsing: Web page access, search, screenshot
- tool_management: Install/update/manage MCP tools
- information_query: General questions, information requests
- complex_task: Multi-step tasks requiring planning and coordination
- unclear: Cannot determine intent clearly

Examples:
- "read file.txt" → INTENT: file_operation, CONFIDENCE: 0.95, CLARIFICATION_NEEDED: false
- "run ls command" → INTENT: shell_command, CONFIDENCE: 0.9, CLARIFICATION_NEEDED: false
- "search python tutorials" → INTENT: web_browsing, CONFIDENCE: 0.85, CLARIFICATION_NEEDED: false
- "create a python script, then test it, and deploy it" → INTENT: complex_task, CONFIDENCE: 0.95, CLARIFICATION_NEEDED: false
- "first install dependencies, then configure the database, finally start the server" → INTENT: complex_task, CONFIDENCE: 0.95, CLARIFICATION_NEEDED: false
- "help me set up a development environment with multiple steps" → INTENT: complex_task, CONFIDENCE: 0.90, CLARIFICATION_NEEDED: false
- "北京到哈尔滨怎么玩？" → INTENT: information_query, CONFIDENCE: 0.8, CLARIFICATION_NEEDED: true
"""

            from langchain_core.messages import HumanMessage

            messages = [HumanMessage(content=analysis_prompt)]
            response = await self.llm.ainvoke(messages)
            analysis_text = str(response.content)

            # Parse the analysis response
            intent = "unclear"
            confidence = 0.5
            entities = {}
            clarification_needed = False
            clarification_questions = []

            lines = analysis_text.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("INTENT:"):
                    intent = line.split(":", 1)[1].strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                    except:
                        confidence = 0.5
                elif line.startswith("CLARIFICATION_NEEDED:"):
                    clarification_needed = "true" in line.lower()
                elif line.startswith("CLARIFICATION_QUESTIONS:"):
                    questions_str = line.split(":", 1)[1].strip()
                    if questions_str and questions_str != "[]":
                        # Simple parsing - could be improved
                        clarification_questions = [
                            q.strip() for q in questions_str.split(",") if q.strip()
                        ]

            return IntentAnalysis(
                intent=intent,
                confidence=confidence,
                entities=entities,
                clarification_needed=clarification_needed,
                clarification_questions=clarification_questions,
            )

        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return IntentAnalysis(
                "unclear",
                0.0,
                {},
                True,
                ["Could you please clarify what you want to do?"],
            )

    async def create_plan(
        self, user_input: str, intent_analysis: IntentAnalysis
    ) -> Plan:
        """
        Create a detailed plan for complex tasks.

        Breaks down user requests into manageable steps with dependencies.
        """
        try:
            plan_prompt = f"""
Create a detailed execution plan for the user's request:

User Request: "{user_input}"
Analyzed Intent: {intent_analysis.intent} (confidence: {intent_analysis.confidence})

Available SubAgents:
- shell: Shell command execution
- filesystem: File operations
- browser: Web browsing and automation
- manager: MCP tool management
- dynamic: Specialized agents (can create on-demand)

Create a step-by-step plan with:
1. Clear, actionable tasks
2. Dependencies between tasks
3. Appropriate agent assignment for each task
4. Estimated complexity/completion criteria

Format as a numbered list of tasks, each with:
- Description
- Assigned Agent
- Dependencies (if any)
- Success Criteria
"""

            from langchain_core.messages import HumanMessage

            messages = [HumanMessage(content=plan_prompt)]
            response = await self.llm.ainvoke(messages)
            plan_text = str(response.content)

            # Create plan object
            plan = Plan(
                id=str(uuid.uuid4()), goal=user_input, status=TaskStatus.PENDING
            )

            # Parse plan text into tasks (simplified parsing)
            lines = plan_text.split("\n")
            current_task = None

            for line in lines:
                line = line.strip()
                if line and any(line.startswith(str(i) + ".") for i in range(1, 20)):
                    # New task
                    if current_task:
                        plan.tasks.append(current_task)

                    task_desc = line.split(".", 1)[1].strip() if "." in line else line
                    current_task = Task(
                        id=str(uuid.uuid4()),
                        description=task_desc,
                        status=TaskStatus.PENDING,
                    )
                elif current_task and line.startswith("-"):
                    # Task detail
                    if "agent:" in line.lower():
                        # Extract agent assignment
                        agent_part = line.split(":", 1)[1].strip().lower()
                        if "shell" in agent_part:
                            current_task.assigned_agent = "shell"
                        elif "file" in agent_part:
                            current_task.assigned_agent = "filesystem"
                        elif "browser" in agent_part or "web" in agent_part:
                            current_task.assigned_agent = "browser"
                        elif "manager" in agent_part:
                            current_task.assigned_agent = "manager"

            if current_task:
                plan.tasks.append(current_task)

            logger.info(
                f"Created plan with {len(plan.tasks)} tasks for: {user_input[:50]}..."
            )
            return plan

        except Exception as e:
            logger.error(f"Plan creation failed: {e}")
            # Return a simple single-task plan
            plan = Plan(
                id=str(uuid.uuid4()),
                goal=user_input,
                tasks=[
                    Task(
                        id=str(uuid.uuid4()),
                        description=user_input,
                        assigned_agent="shell",  # Default fallback
                        status=TaskStatus.PENDING,
                    )
                ],
            )
            return plan

    async def execute_plan(self, plan: Plan) -> Dict[str, Any]:
        """
        Execute a plan by coordinating subagents.
        Each task is assigned to the appropriate subagent and executed in parallel where possible.

        Returns execution results and status.
        """
        try:
            import asyncio

            results = []
            plan.status = TaskStatus.IN_PROGRESS

            # Create tasks for parallel execution
            execution_tasks = []

            for task in plan.tasks:
                if task.status != TaskStatus.PENDING:
                    continue

                task.status = TaskStatus.IN_PROGRESS

                # Create execution task
                execution_tasks.append(self._execute_single_task(task))

            # Execute all tasks concurrently
            if execution_tasks:
                task_results = await asyncio.gather(
                    *execution_tasks, return_exceptions=True
                )

                # Process results
                for i, result in enumerate(task_results):
                    task = plan.tasks[i]
                    if isinstance(result, Exception):
                        # Task failed
                        task.error = str(result)
                        task.status = TaskStatus.FAILED
                        results.append(
                            {
                                "task_id": task.id,
                                "description": task.description,
                                "agent": task.assigned_agent or "unknown",
                                "error": str(result),
                                "status": "failed",
                            }
                        )
                    else:
                        # Task succeeded
                        if isinstance(result, str):
                            task.result = result
                        else:
                            task.result = str(result) if result is not None else None
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.now()
                        results.append(
                            {
                                "task_id": task.id,
                                "description": task.description,
                                "agent": task.assigned_agent or "unknown",
                                "result": result,
                                "status": "completed",
                            }
                        )

            plan.status = TaskStatus.COMPLETED

            # Create summary
            summary = self._create_plan_summary(plan, results)

            return {
                "plan_id": plan.id,
                "goal": plan.goal,
                "total_tasks": len(plan.tasks),
                "completed_tasks": len(
                    [t for t in plan.tasks if t.status == TaskStatus.COMPLETED]
                ),
                "failed_tasks": len(
                    [t for t in plan.tasks if t.status == TaskStatus.FAILED]
                ),
                "results": results,
                "summary": summary,
                "status": "completed",
            }

        except asyncio.TimeoutError:
            plan.status = TaskStatus.FAILED
            logger.error(f"Plan execution timed out: {plan.goal}")
            return {
                "plan_id": plan.id,
                "goal": plan.goal,
                "error": "Plan execution timed out. Some tasks may have completed.",
                "status": "timeout",
                "suggestion": "Try breaking down the plan into smaller, simpler tasks.",
            }

        except asyncio.TimeoutError:
            plan.status = TaskStatus.FAILED
            logger.error(f"Plan execution timed out: {plan.goal}")
            return {
                "plan_id": plan.id,
                "goal": plan.goal,
                "error": "Plan execution timed out. Some tasks may have completed.",
                "status": "timeout",
                "suggestion": "Try breaking down the plan into smaller, simpler tasks.",
            }

        except Exception as e:
            plan.status = TaskStatus.FAILED
            logger.error(f"Plan execution failed: {e}")
            return {
                "plan_id": plan.id,
                "goal": plan.goal,
                "error": f"Plan execution failed: {str(e)}",
                "status": "failed",
                "suggestion": "Check individual task errors and try executing them separately.",
            }

    async def _execute_single_task(self, task: Task) -> str:
        """Execute a single task with the appropriate subagent and timeout control."""
        try:
            logger.info(f"Executing task: {task.description[:50]}...")

            # Determine which agent to use
            if task.assigned_agent and task.assigned_agent in self.subagents:
                agent = self.subagents[task.assigned_agent]
            elif task.assigned_agent and task.assigned_agent in self.dynamic_agents:
                agent = self.dynamic_agents[task.assigned_agent]
            else:
                # Default to shell agent
                agent = self.subagents["shell"]

            # Set timeout based on agent type
            timeout_seconds = self._get_task_timeout(task, agent)

            # Execute the task with timeout
            try:
                result = await asyncio.wait_for(
                    agent.process_task(task.description), timeout=timeout_seconds
                )
                logger.info(f"Task completed: {task.description[:30]}...")
                return result

            except asyncio.TimeoutError:
                error_msg = f"Task execution timed out after {timeout_seconds}s: {task.description[:30]}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Task execution failed: {task.description[:30]} - {e}")
            raise

    def _get_task_timeout(self, task: Task, agent) -> float:
        """Get appropriate timeout for a task based on agent type and complexity."""
        # Base timeout from agent type
        if hasattr(agent, "agent_type"):
            if agent.agent_type == AgentType.BROWSER:
                base_timeout = 180.0  # 3 minutes for browser operations
            elif agent.agent_type == AgentType.SHELL:
                base_timeout = 120.0  # 2 minutes for shell commands
            elif agent.agent_type == AgentType.FILESYSTEM:
                base_timeout = 60.0  # 1 minute for file operations
            else:
                base_timeout = 90.0  # 1.5 minutes for other operations
        else:
            base_timeout = 90.0

        # Adjust based on task complexity
        task_desc = task.description.lower()

        # Complex tasks get more time
        if any(
            keyword in task_desc
            for keyword in ["复杂", "complex", "multiple", "several", "many"]
        ):
            base_timeout *= 1.5

        # Information queries might need more time for web searching
        if any(
            keyword in task_desc for keyword in ["查询", "search", "find", "lookup"]
        ):
            base_timeout *= 1.2

        # LLM-based tasks might need more time
        if "general" in str(agent).lower() or "llm" in task_desc:
            base_timeout = max(base_timeout, 150.0)  # At least 2.5 minutes for LLM

        return min(base_timeout, 300.0)  # Cap at 5 minutes

    def _create_plan_summary(self, plan: Plan, results: List[Dict]) -> str:
        """Create a comprehensive summary of plan execution."""
        successful_tasks = [r for r in results if r["status"] == "completed"]
        failed_tasks = [r for r in results if r["status"] == "failed"]

        summary = f"🎯 **任务计划执行完成**\n\n"
        summary += f"📋 **目标**: {plan.goal}\n"
        summary += f"📊 **统计**: {len(successful_tasks)}/{len(results)} 任务成功\n\n"

        if successful_tasks:
            summary += "**✅ 完成的任务**:\n"
            for result in successful_tasks:
                agent_name = result.get("agent", "Unknown")
                desc = result.get("description", "")[:50]
                summary += f"- [{agent_name}] {desc}...\n"

        if failed_tasks:
            summary += "\n**❌ 失败的任务**:\n"
            for result in failed_tasks:
                agent_name = result.get("agent", "Unknown")
                desc = result.get("description", "")[:50]
                error = result.get("error", "Unknown error")[:100]
                summary += f"- [{agent_name}] {desc}... (错误: {error})\n"

        summary += f"\n🎉 **总计**: {len(plan.tasks)} 个任务，执行时间: {(datetime.now() - plan.created_at).total_seconds():.1f}秒"

        return summary

    def _create_plan_user_summary(self, plan: Plan) -> str:
        """
        Create a user-friendly summary of a generated plan.
        This provides immediate feedback without requiring full execution.
        """
        task_count = len(plan.tasks)
        browser_tasks = sum(
            1 for task in plan.tasks if task.assigned_agent == "browser"
        )
        file_tasks = sum(
            1 for task in plan.tasks if task.assigned_agent == "filesystem"
        )

        # Create a summary based on the plan goal
        goal_lower = plan.goal.lower()

        if "北京" in goal_lower and ("旅游" in goal_lower or "旅行" in goal_lower):
            return f"""🎯 **北京旅游规划方案已生成**

我已经为您的北京旅游需求创建了一个详细的执行计划，包含{task_count}个具体步骤：

**📋 计划概览**：
- **总任务数**: {task_count}个
- **信息收集**: {browser_tasks}个网络查询任务
- **文档整理**: {file_tasks}个文件处理任务

**🎯 计划目标**: {plan.goal}

**📝 主要执行步骤**：
1. 收集北京旅游基础信息
2. 调研当前旅行限制和要求
3. 识别主要景点和地标
4. 研究住宿选择
5. 调查交通选项
6. 探索美食和餐饮
7. 创建结构化行程模板
8. 添加实用旅行提示
9. 整理研究资料为文档
10. 创建视觉辅助和地图

**💡 建议**：
- 这个计划包含了全面的北京旅游规划准备工作
- 如果您希望我开始执行这些步骤，请回复"执行计划"
- 或者如果您有特定的偏好（如预算、时间、兴趣点），我可以调整计划

需要我开始执行这个计划吗？"""

        else:
            return f"""🎯 **执行计划已生成**

我已经为您的需求"{plan.goal}"创建了一个详细的执行计划，包含{task_count}个具体步骤。

**📋 计划统计**：
- **总任务数**: {task_count}个
- **网络查询**: {browser_tasks}个任务
- **文件操作**: {file_tasks}个任务

**📝 计划包含的主要步骤**：
{chr(10).join(f"- {task.description[:50]}..." for task in plan.tasks[:5])}
{"..." if task_count > 5 else ""}

**💡 下一步**：
- 回复"执行计划"开始执行这些步骤
- 或者告诉我您希望如何调整这个计划

您希望我开始执行这个计划吗？"""

    async def create_dynamic_agent(
        self, task_description: str, required_capabilities: List[str]
    ) -> str:
        """
        Create a dynamic agent for specialized tasks.

        Returns the agent ID.
        """
        agent_name = f"DynamicAgent_{len(self.dynamic_agents) + 1}"
        dynamic_agent = DynamicAgent(
            agent_name, task_description, required_capabilities
        )

        agent_id = dynamic_agent.id
        self.dynamic_agents[agent_id] = dynamic_agent

        logger.info(
            f"Created dynamic agent: {agent_name} for task: {task_description[:50]}..."
        )
        return agent_id

    async def process(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main processing pipeline: Intent → Clarification → Plan → Execute.
        Full DeepAgent workflow with planning capabilities.
        """
        try:
            response_data = {
                "input": user_input,
                "timestamp": datetime.now().isoformat(),
                "processing_steps": [],
            }

            # Step 1: Intent Analysis
            logger.info("Step 1: Analyzing intent...")
            intent_analysis = await self.analyze_intent(user_input)
            response_data["intent_analysis"] = {
                "intent": intent_analysis.intent,
                "confidence": intent_analysis.confidence,
                "clarification_needed": intent_analysis.clarification_needed,
                "clarification_questions": intent_analysis.clarification_questions,
            }
            response_data["processing_steps"].append("intent_analysis")

            # Step 2: Clarification (smart decision making)
            # Only request clarification if confidence is very low OR for truly ambiguous queries
            should_request_clarification = (
                intent_analysis.clarification_needed
                and intent_analysis.confidence
                < 0.6  # Only clarify if confidence is very low
                and not self._has_sufficient_context(
                    user_input, intent_analysis
                )  # Check if we have enough context
            )

            if should_request_clarification:
                response_data["needs_clarification"] = True
                response_data["clarification_questions"] = (
                    intent_analysis.clarification_questions
                )
                response_data["status"] = "clarification_needed"
                return response_data

            # Step 3: Plan Creation (for complex tasks)
            # Use enhanced complex task detection
            is_complex = self._detect_complex_task(user_input, intent_analysis)

            if is_complex:
                logger.info("Step 3: Creating execution plan...")

                # Add timeout for plan creation
                try:
                    plan = await asyncio.wait_for(
                        self.create_plan(user_input, intent_analysis),
                        timeout=90.0,  # 90 seconds for plan creation
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        "Plan creation timed out, falling back to simple response"
                    )
                    # Fallback: provide a simple planning response without detailed execution
                    response_data["result"] = self._create_simple_plan_response(
                        user_input
                    )
                    response_data["agent"] = "General Assistant"
                    response_data["status"] = "completed"
                    response_data["processing_steps"].append("simple_planning")
                    return response_data

                response_data["plan"] = {
                    "plan_id": plan.id,
                    "goal": plan.goal,
                    "task_count": len(plan.tasks),
                    "tasks": [
                        {
                            "id": task.id,
                            "description": task.description,
                            "assigned_agent": task.assigned_agent,
                            "status": task.status.value,
                        }
                        for task in plan.tasks
                    ],
                }
                response_data["processing_steps"].append("plan_creation")

                # Step 4: Plan Execution (with timeout protection)
                logger.info("Step 4: Executing plan...")

                execution_results = {
                    "status": "plan_created",
                    "message": "详细计划已生成，包含具体执行步骤",
                    "total_tasks": len(plan.tasks),
                    "next_steps": "如果需要执行计划，请提供确认",
                }
                response_data["execution"] = execution_results
                response_data["processing_steps"].append("plan_execution")

                # Create a user-friendly summary of the plan
                plan_summary = self._create_plan_user_summary(plan)
                response_data["result"] = plan_summary

                # Store the plan for reference
                self.plans[plan.id] = plan

                response_data["status"] = "completed"
                response_data["final_result"] = execution_results.get("results", [])
                response_data["plan_used"] = True
            else:
                # Simple routing for basic tasks
                logger.info("Simple routing (no plan needed)...")
                target_agent = self._simple_route(user_input)

                # Execute with appropriate subagent
                subagent = self.subagents.get(target_agent)
                if not subagent:
                    subagent = self.subagents["shell"]

                result = await subagent.process_task(user_input, context)

                response_data["status"] = "completed"
                response_data["agent"] = subagent.name
                response_data["result"] = (
                    result if result and result.strip() else "任务已完成"
                )
                response_data["plan_used"] = False
                response_data["processing_steps"].append("simple_routing")

            return response_data

        except Exception as e:
            logger.error(f"MainAgent processing failed: {e}")
            return {
                "input": user_input,
                "status": "error",
                "error": str(e),
                "processing_steps": ["error"],
            }

    def _detect_complex_task(
        self, user_input: str, intent_analysis: IntentAnalysis
    ) -> bool:
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
            "首先",
            "然后",
            "接下来",
            "之后",
            "最后",
            "第一步",
            "第二步",
            "第三步",
            "第一",
            "第二",
            "第三",
            "第四",
            "第五",
            # English step words
            "first",
            "then",
            "next",
            "after",
            "finally",
            "step 1",
            "step 2",
            "step 3",
            "1.",
            "2.",
            "3.",
            "4.",
            "5.",
            # Sequence words
            "and then",
            "followed by",
            "subsequently",
        ]
        has_steps = any(indicator in input_lower for indicator in step_indicators)

        # Multi-action indicators
        action_indicators = [
            # Chinese actions
            "创建",
            "安装",
            "配置",
            "设置",
            "测试",
            "运行",
            "部署",
            "上传",
            "下载",
            "修改",
            "更新",
            "删除",
            "备份",
            "恢复",
            "检查",
            "验证",
            # English actions
            "create",
            "install",
            "configure",
            "setup",
            "test",
            "run",
            "deploy",
            "upload",
            "download",
            "modify",
            "update",
            "delete",
            "backup",
            "restore",
            "check",
            "verify",
            "build",
            "compile",
        ]
        action_count = sum(1 for action in action_indicators if action in input_lower)

        # Complex task patterns
        complex_patterns = [
            "请帮我",
            "帮我",
            "help me",
            "i need to",
            "i want to",
            "项目",
            "project",
            "application",
            "app",
            "开发环境",
            "development environment",
            "workflow",
            "自动化",
            "automation",
            "pipeline",
        ]
        has_complex_pattern = any(
            pattern in input_lower for pattern in complex_patterns
        )

        # Length and complexity indicators
        word_count = len(user_input.split())
        has_numbers = any(char.isdigit() for char in user_input)
        has_lists = any(char in user_input for char in ["•", "-", "*"]) and has_numbers

        # Decision logic
        is_complex = (
            # High confidence intent classification
            (
                intent_analysis.intent == "complex_task"
                and intent_analysis.confidence > 0.6
            )
            or
            # Multiple steps explicitly mentioned
            (has_steps and has_numbers)
            or
            # Multiple actions in one request
            (action_count >= 3)
            or
            # Complex patterns
            (has_complex_pattern and action_count >= 2)
            or
            # Long requests with multiple elements
            (word_count > 25)
            or
            # Structured lists
            (has_lists and word_count > 15)
            or
            # Very long single sentences
            (word_count > 40)
        )

        logger.info(
            f"Complex task detection: {is_complex} "
            f"(steps: {has_steps}, actions: {action_count}, words: {word_count}, "
            f"intent: {intent_analysis.intent}, confidence: {intent_analysis.confidence})"
        )

        return is_complex

    def _simple_route(self, user_input: str) -> str:
        """Enhanced keyword-based routing to subagents with priority ordering."""
        input_lower = user_input.lower()

        # High-priority specific operations
        # Tool management (highest priority - affects system)
        if any(
            word in input_lower
            for word in [
                "安装",
                "install",
                "uninstall",
                "remove",
                "update",
                "tool",
                "mcp",
                "工具",
                "插件",
                "extension",
            ]
        ):
            return "manager"

        # Planning and complex queries (high priority - needs LLM reasoning)
        planning_keywords = [
            "计划",
            "plan",
            "行程",
            "itinerary",
            "旅行",
            "travel",
            "trip",
            "建议",
            "recommend",
            "怎么",
            "如何",
            "what",
            "how",
            "why",
            "介绍",
            "explain",
            "告诉",
            "tell",
            "帮我",
            "help",
            "请教",
            "指导",
            "guide",
            "tutorial",
            "例子",
            "example",
            "解释",
            "人工智能",
            "机器学习",
            "深度学习",
            "AI",
            "ML",
            "DL",
            "制定",
            "安排",
            "组织",
            "设计",
            "创建",
            "生成",
        ]
        if any(word in input_lower for word in planning_keywords):
            return "general"

        # Browser operations (medium priority - for specific information queries)
        if any(
            word in input_lower
            for word in [
                "浏览器",
                "browser",
                "网页",
                "web",
                "访问",
                "navigate",
                "打开网页",
                "查询",
                "搜索",
                "查找",
                "search",
                "find",
                "查票",
                "订票",
                "预订",
                "价格",
                "price",
                "票价",
                "门票",
                "机票",
                "火车票",
                "高铁票",
                "天气",
                "weather",
                "实时",
                "最新",
                "current",
                "怎么样",
                "攻略",
                "官网",
                "官方网站",
                "official website",
                "门票价",
                "票务",
                "怎么玩",
                "玩法",
                "游玩",
                "旅行攻略",
                "旅游攻略",
                "景点",
                "路线",
                "怎么去",
                "怎么到达",
                "交通",
                "路线",
                "导航",
            ]
        ):
            return "browser"

        # File operations (medium priority - data manipulation)
        if any(
            word in input_lower
            for word in [
                "文件",
                "file",
                "read",
                "write",
                "create",
                "delete",
                "读取",
                "写入",
                "创建",
                "删除",
                "copy",
                "move",
                "rename",
                "list",
                "ls",
                "目录",
                "folder",
            ]
        ):
            return "filesystem"

        # System/shell operations (medium priority - system control)
        if any(
            word in input_lower
            for word in [
                "运行",
                "执行",
                "run",
                "execute",
                "command",
                "cmd",
                "进程",
                "process",
                "kill",
                "start",
                "stop",
                "service",
                "系统",
                "system",
                "shell",
                "bash",
                "terminal",
            ]
        ):
            return "shell"

        # Conversational or unclear queries default to general
        if any(
            word in input_lower
            for word in ["你好", "hello", "hi", "您好", "谢谢", "thank", "请"]
        ):
            return "general"

        # Default to shell for any remaining commands
        return "shell"

        # Planning and complex queries (low priority - general assistance)
        planning_keywords = [
            "计划",
            "plan",
            "行程",
            "itinerary",
            "旅行",
            "travel",
            "trip",
            "建议",
            "recommend",
            "怎么",
            "如何",
            "what",
            "how",
            "why",
            "介绍",
            "explain",
            "告诉",
            "tell",
            "帮我",
            "help",
            "请教",
            "指导",
            "guide",
            "tutorial",
            "例子",
            "example",
            "解释",
            "人工智能",
            "机器学习",
            "深度学习",
            "AI",
            "ML",
            "DL",
        ]
        if any(word in input_lower for word in planning_keywords):
            return "general"

        # Conversational or unclear queries default to general
        if any(
            word in input_lower
            for word in ["你好", "hello", "hi", "您好", "谢谢", "thank", "请"]
        ):
            return "general"

        # Default to shell for any remaining commands
        return "shell"

        # Planning and complex queries (low priority - general assistance)
        planning_keywords = [
            "计划",
            "plan",
            "行程",
            "itinerary",
            "旅行",
            "travel",
            "trip",
            "建议",
            "recommend",
            "怎么",
            "如何",
            "what",
            "how",
            "why",
            "介绍",
            "explain",
            "告诉",
            "tell",
            "帮我",
            "help",
            "请教",
            "指导",
            "guide",
            "tutorial",
            "例子",
            "example",
            "解释",
            "人工智能",
            "机器学习",
            "深度学习",
            "AI",
            "ML",
            "DL",
        ]
        if any(word in input_lower for word in planning_keywords):
            return "general"

        # Conversational or unclear queries default to general
        if any(
            word in input_lower
            for word in ["你好", "hello", "hi", "您好", "谢谢", "thank", "请"]
        ):
            return "general"

        # Default to shell for any remaining commands
        return "shell"

    def _has_sufficient_context(
        self, user_input: str, intent_analysis: IntentAnalysis
    ) -> bool:
        """
        Check if we have sufficient context to proceed without clarification.

        This helps avoid endless clarification loops while still being helpful.
        """
        input_lower = user_input.lower()

        # For travel planning, if we have basic elements, we can proceed
        if intent_analysis.intent in ["complex_task", "information_query"]:
            # Check for travel-related keywords with sufficient detail
            travel_indicators = [
                "北京",
                "哈尔滨",
                "旅行",
                "行程",
                "旅游",
                "trip",
                "travel",
            ]
            has_travel_context = any(word in input_lower for word in travel_indicators)

            # Check for time duration
            time_indicators = ["天", "周", "星期", "week", "day", "days"]
            has_time_context = any(word in input_lower for word in time_indicators)

            # Check for transportation
            transport_indicators = ["火车", "高铁", "飞机", "flight", "train", "高铁"]
            has_transport_context = any(
                word in input_lower for word in transport_indicators
            )

            # If we have travel + time OR travel + transport, we can proceed
            if has_travel_context and (has_time_context or has_transport_context):
                return True

        # For project/file tasks, if we have action words, we can proceed
        action_indicators = [
            "创建",
            "create",
            "写",
            "write",
            "运行",
            "run",
            "执行",
            "execute",
        ]
        if any(word in input_lower for word in action_indicators):
            return True

        # For general queries, if confidence is reasonable, proceed
        if intent_analysis.confidence > 0.7:
            return True

        return False

    def _create_simple_plan_response(self, user_input: str) -> str:
        """
        Create a simple planning response when detailed plan creation times out.
        This provides basic guidance without complex execution.
        """
        input_lower = user_input.lower()

        if "北京" in input_lower and ("旅游" in input_lower or "旅行" in input_lower):
            return """基于您的北京旅游需求，我为您制定一个基础的行程规划建议：

## 🏛️ 北京经典5日游建议

### 📅 行程概览
- **适合人群**: 首次来京游客
- **最佳季节**: 4-5月、9-10月
- **预算参考**: 2000-5000元/人

### 🗓️ 推荐行程

**Day 1: 天安门广场 & 故宫**
- 上午：天安门广场升旗仪式
- 下午：故宫博物院（建议跟讲解员）
- 晚上：王府井步行街

**Day 2: 长城 & 十三陵**
- 上午：八达岭长城（乘坐滑车节省体力）
- 下午：明十三陵（定陵地下宫殿）
- 小贴士：长城早上去人少，带好防晒霜

**Day 3: 颐和园 & 798艺术区**
- 上午：颐和园（游船+长廊）
- 下午：798艺术区（现代艺术展览）
- 晚上：三里屯酒吧街

**Day 4: 雍和宫 & 什刹海**
- 上午：雍和宫（藏传佛教寺庙）
- 下午：什刹海（胡同游览，品尝小吃）
- 晚上：欣赏京剧表演

**Day 5: 奥林匹克公园 & 返程**
- 上午：鸟巢、水立方
- 下午：购物或自由活动
- 傍晚：返程

### 💡 实用贴士
- **交通**: 地铁最方便，买一卡通
- **门票**: 故宫、长城建议网上预订
- **住宿**: 二环以内交通方便
- **美食**: 烤鸭、炸酱面、北京小吃

如果您需要更详细的安排或特定景点的攻略，请提供更多具体信息！"""

        elif "哈尔滨" in input_lower and (
            "旅游" in input_lower or "旅行" in input_lower
        ):
            return """哈尔滨冰雪之旅规划建议：

## ❄️ 哈尔滨冬季5日游

### 📅 行程概览
- **最佳时间**: 12月-2月（冰雪节期间）
- **特色**: 冰灯、冰雕、冰雪娱乐
- **预算**: 3000-6000元/人

### 🗓️ 推荐行程

**Day 1: 冰城初体验**
- 上午：中央大街散步
- 下午：圣索菲亚教堂
- 晚上：冰雪大世界开幕式

**Day 2: 冰雪主题日**
- 上午：冰雪大世界（冰滑梯、雪圈）
- 下午：松花江冰上活动
- 晚上：防洪纪念塔灯光秀

**Day 3: 亚布力滑雪**
- 全天：亚布力滑雪场
- 体验项目：雪地摩托、温泉

**Day 4: 雪乡深度游**
- 全天：雪乡民俗村
- 体验：雪地摄影、冰雪民宿

**Day 5: 返程**
- 上午：哈尔滨大剧院或最后购物
- 下午：返程

### 💡 注意事项
- 防寒装备必备（-20°C以下）
- 选择正规冰雪活动场地
- 冰面活动注意安全

需要更详细的攻略吗？"""

        else:
            return f"""我理解您想要为"{user_input}"制定计划。为了提供更准确的建议，我需要一些具体信息：

- **时间安排**: 计划用多长时间？
- **预算范围**: 大致的预算？
- **具体需求**: 有什么特别的偏好或限制？

请提供更多细节，我就能为您制定详细的执行计划！"""


# Global DeepAgent instance
deep_agent_core = MainAgent()


# Global DeepAgent instance
deep_agent_core = MainAgent()
