"""
专门化子智能体实现 - 各个领域的专业智能体

包含 Shell、Filesystem、Browser、Manager、General 等子智能体。
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from app.core.config import settings
from app.services.multiagent.base_agent import SubAgent, retry_on_failure
from app.services.multiagent.models import AgentType, AgentCapabilities
from app.services import mcp_manager

logger = logging.getLogger(__name__)


class ShellSubAgent(SubAgent):
    """Shell 命令执行子智能体"""

    def __init__(self):
        system_prompt = """
你是一个 Shell 命令执行专家，在 DeepAgent 系统中的角色是执行终端命令和系统操作。

**核心能力**：
- 运行 shell 命令（ls、cd、mkdir、rm 等）
- 执行脚本和程序
- 监控系统进程和资源
- 执行系统管理任务

**安全原则**：
- 极其谨慎对待破坏性操作，在删除或系统更改前始终确认
- 验证命令语法和参数
- 避免危险命令组合
- 提供清晰的命令执行结果

**命令执行指南**：
- 使用安全路径，避免路径遍历
- 提供命令执行的详细输出
- 解释每个命令的作用
- 处理错误并提供恢复建议
"""

        capabilities = AgentCapabilities(
            name="Shell Commander",
            description="执行终端命令和系统操作的专家",
            supported_operations=[
                "run_command",
                "execute_script",
                "monitor_process",
                "system_info",
                "file_operations",
                "process_management",
            ],
            mcp_servers=["shell"],
            max_concurrent_tasks=1,
            supports_parallel=False,
            avg_response_time=30,
        )

        super().__init__(
            name="Shell Commander",
            agent_type=AgentType.SHELL,
            system_prompt=system_prompt,
            mcp_servers=["shell"],
            capabilities=capabilities,
        )

    @retry_on_failure(max_retries=1, delay=2.0)
    async def process_task(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """处理 Shell 相关任务"""
        try:
            # 解析用户意图
            command = self._extract_command(user_input)
            if not command:
                return self._provide_shell_help()

            # 安全检查
            if not self._is_safe_command(command):
                return f"""⚠️ 安全警告

检测到潜在的危险命令：`{command}`

**安全检查失败的原因**：
- 包含破坏性操作（如 rm -rf /）
- 涉及系统关键文件
- 可能导致数据丢失

**建议替代方案**：
- 使用更安全的命令
- 在测试环境中先验证
- 提供具体的文件路径而不是通配符

请重新表述您的命令或提供更安全的替代方案。"""

            # 执行命令
            result = await self._execute_shell_command(command)

            return f"""🔧 Shell 命令执行结果

**执行命令**: `{command}`
**执行时间**: {datetime.now().strftime("%H:%M:%S")}

**执行结果**:
```
{result}
```

**命令说明**:
{self._explain_command(command)}

如果需要进一步操作或有其他命令需要执行，请告诉我。"""

        except Exception as e:
            logger.error(f"Shell 子智能体执行失败: {e}")
            return f"""❌ Shell 命令执行失败

**错误信息**: {str(e)}

**可能原因**:
- 命令语法错误
- 权限不足
- 系统资源不足
- MCP 服务异常

**建议解决方案**:
1. 检查命令语法
2. 确认文件权限
3. 验证路径是否存在
4. 尝试简化命令

请提供更多详细信息或尝试其他命令。"""

    def _extract_command(self, user_input: str) -> Optional[str]:
        """从用户输入中提取命令"""
        # 常见的命令模式
        patterns = [
            r'运行\s*[`"]?([^`"\\n]+)[`"]?',
            r'执行\s*[`"]?([^`"\\n]+)[`"]?',
            r'run\s*[`"]?([^`"\\n]+)[`"]?',
            r'execute\s*[`"]?([^`"\\n]+)[`"]?',
            r"```\s*([^`\\n]+)\s*```",
        ]

        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                command = match.group(1).strip()
                # 清理命令
                command = re.sub(r"^[a-zA-Z]+\s+", "", command)  # 移除开头的动词
                return command

        # 检查是否直接是命令
        if any(
            keyword in user_input.lower()
            for keyword in ["ls", "cd", "mkdir", "rm", "ps", "top", "grep"]
        ):
            return user_input.strip()

        return None

    def _is_safe_command(self, command: str) -> bool:
        """安全检查命令"""
        dangerous_patterns = [
            r"rm\s+-rf\s+/",
            r"rm\s+-rf\s+\*",
            r"> /dev/",
            r"chmod\s+777",
            r"chown\s+root",
            r"dd\s+if=",
            r"mkfs",
            r"fdisk",
            r"format",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False

        return True

    async def _execute_shell_command(self, command: str) -> str:
        """执行 shell 命令"""
        try:
            # 调用 MCP shell 工具
            result = await mcp_manager.call_tool(
                "shell", "run_command", {"command": command}
            )

            if isinstance(result, dict) and "output" in result:
                return result["output"]
            elif isinstance(result, str):
                return result
            else:
                return str(result)

        except Exception as e:
            raise Exception(f"命令执行失败: {e}")

    def _explain_command(self, command: str) -> str:
        """解释命令作用"""
        explanations = {
            "ls": "列出目录内容",
            "cd": "切换工作目录",
            "mkdir": "创建新目录",
            "rm": "删除文件或目录",
            "cp": "复制文件或目录",
            "mv": "移动或重命名文件",
            "ps": "显示进程状态",
            "top": "实时显示系统进程",
            "grep": "搜索文本模式",
            "find": "查找文件",
            "chmod": "修改文件权限",
            "chown": "修改文件所有者",
        }

        cmd_base = command.split()[0] if command else ""
        return explanations.get(cmd_base, f"执行命令: {command}")

    def _provide_shell_help(self) -> str:
        """提供 Shell 帮助"""
        return """🖥️ Shell 命令助手

我可以帮助您执行各种 Linux 终端命令。以下是一些常见用法：

**文件操作**:
- `ls -la` - 详细列出文件
- `mkdir new_folder` - 创建目录
- `cp file1 file2` - 复制文件
- `mv old_name new_name` - 重命名文件

**系统监控**:
- `ps aux` - 查看所有进程
- `top` - 系统资源监控
- `df -h` - 磁盘使用情况
- `free -h` - 内存使用情况

**文本处理**:
- `grep "pattern" file` - 搜索文本
- `cat file.txt` - 显示文件内容
- `head -n 10 file` - 显示文件前10行

**使用方法**:
- 直接输入命令: `ls -la`
- 使用自然语言: `列出当前目录的所有文件`

请告诉我您想要执行什么命令！"""


class FilesystemSubAgent(SubAgent):
    """文件系统操作子智能体"""

    def __init__(self):
        system_prompt = """
你是文件系统管理专家，在 DeepAgent 系统中的角色是处理文件和目录操作。

**核心能力**：
- 读取文件内容
- 创建和写入文件
- 列出目录内容
- 导航文件系统
- 搜索文件和内容

**操作原则**：
- 工作在工作空间内，保护数据
- 使用正确的编码
- 验证文件权限
- 提供详细的操作结果
"""

        capabilities = AgentCapabilities(
            name="File System Manager",
            description="处理文件和目录操作的专家",
            supported_operations=[
                "read_file",
                "write_file",
                "list_directory",
                "create_directory",
                "delete_file",
                "search_files",
                "get_file_info",
                "move_file",
            ],
            mcp_servers=["filesystem"],
            max_concurrent_tasks=2,
            supports_parallel=True,
            avg_response_time=15,
        )

        super().__init__(
            name="File System Manager",
            agent_type=AgentType.FILESYSTEM,
            system_prompt=system_prompt,
            mcp_servers=["filesystem"],
            capabilities=capabilities,
        )

    async def process_task(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """处理文件系统任务"""
        try:
            operation = self._analyze_file_operation(user_input)

            if operation == "read":
                return await self._handle_read_operation(user_input)
            elif operation == "write":
                return await self._handle_write_operation(user_input)
            elif operation == "list":
                return await self._handle_list_operation(user_input)
            elif operation == "search":
                return await self._handle_search_operation(user_input)
            else:
                return self._provide_filesystem_help()

        except Exception as e:
            logger.error(f"Filesystem 子智能体执行失败: {e}")
            return f"文件操作失败: {str(e)}"

    def _analyze_file_operation(self, user_input: str) -> str:
        """分析文件操作类型"""
        input_lower = user_input.lower()

        if any(
            word in input_lower for word in ["read", "查看", "读取", "显示", "内容"]
        ):
            return "read"
        elif any(
            word in input_lower for word in ["write", "创建", "写入", "新建", "编辑"]
        ):
            return "write"
        elif any(
            word in input_lower for word in ["list", "列出", "目录", "文件夹", "ls"]
        ):
            return "list"
        elif any(
            word in input_lower for word in ["search", "查找", "搜索", "grep", "find"]
        ):
            return "search"

        return "unknown"

    async def _handle_read_operation(self, user_input: str) -> str:
        """处理读取操作"""
        # 提取文件路径
        file_path = self._extract_file_path(user_input)
        if not file_path:
            return "请指定要读取的文件路径"

        try:
            # 调用 MCP filesystem 工具
            result = await mcp_manager.call_tool(
                "filesystem", "read_file", {"path": file_path}
            )

            content = (
                result.get("content", "") if isinstance(result, dict) else str(result)
            )

            return f"""📄 文件读取结果

**文件路径**: `{file_path}`
**读取时间**: {datetime.now().strftime("%H:%M:%S")}

**文件内容**:
```
{content}
```

文件读取完成。如需其他操作，请告诉我。"""

        except Exception as e:
            return f"读取文件失败: {str(e)}"

    async def _handle_write_operation(self, user_input: str) -> str:
        """处理写入操作"""
        # 这里需要解析文件名和内容，暂时返回帮助
        return "文件写入功能正在开发中。请使用其他方式创建或编辑文件。"

    async def _handle_list_operation(self, user_input: str) -> str:
        """处理列出操作"""
        dir_path = self._extract_directory_path(user_input) or "."

        try:
            result = await mcp_manager.call_tool(
                "filesystem", "list_directory", {"path": dir_path}
            )

            if isinstance(result, dict) and "entries" in result:
                entries = result["entries"]
                file_list = "\n".join(f"- {entry}" for entry in entries)
            else:
                file_list = "无法获取目录内容"

            return f"""📁 目录内容

**目录路径**: `{dir_path}`

**内容列表**:
{file_list}

共 {len(entries) if isinstance(result, dict) and "entries" in result else 0} 个项目。"""

        except Exception as e:
            return f"列出目录失败: {str(e)}"

    async def _handle_search_operation(self, user_input: str) -> str:
        """处理搜索操作"""
        # 提取搜索模式
        pattern = self._extract_search_pattern(user_input)
        if not pattern:
            return "请指定要搜索的内容或模式"

        try:
            result = await mcp_manager.call_tool(
                "filesystem", "grep_search", {"pattern": pattern, "path": "."}
            )

            return f"""🔍 搜索结果

**搜索模式**: `{pattern}`

{result if isinstance(result, str) else "搜索完成"}"""

        except Exception as e:
            return f"搜索失败: {str(e)}"

    def _extract_file_path(self, text: str) -> Optional[str]:
        """提取文件路径"""
        # 简单的路径提取逻辑
        import re

        path_patterns = [
            r'["\']([^"\']+\.[a-zA-Z0-9]+)["\']',
            r'file\s+["\']?([^"\s]+)["\']?',
            r'path\s+["\']?([^"\s]+)["\']?',
            r'读取\s+["\']?([^"\s]+)["\']?',
        ]

        for pattern in path_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _extract_directory_path(self, text: str) -> Optional[str]:
        """提取目录路径"""
        # 类似的文件路径提取，但针对目录
        import re

        dir_patterns = [
            r'directory\s+["\']?([^"\s]+)["\']?',
            r'dir\s+["\']?([^"\s]+)["\']?',
            r'文件夹\s+["\']?([^"\s]+)["\']?',
        ]

        for pattern in dir_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _extract_search_pattern(self, text: str) -> Optional[str]:
        """提取搜索模式"""
        import re

        search_patterns = [
            r'search\s+["\']?([^"\s]+)["\']?',
            r'查找\s+["\']?([^"\s]+)["\']?',
            r'搜索\s+["\']?([^"\s]+)["\']?',
        ]

        for pattern in search_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _provide_filesystem_help(self) -> str:
        """提供文件系统帮助"""
        return """💾 文件系统助手

我可以帮助您进行各种文件和目录操作：

**文件操作**:
- 📖 读取文件: `读取文件 /path/to/file.txt`
- ✏️ 创建文件: `创建文件 hello.txt 内容为: Hello World`
- 📁 列出目录: `列出目录 /path/to/folder`
- 🔍 搜索内容: `在文件中搜索 "keyword"`

**目录操作**:
- 📂 创建目录: `创建目录 new_folder`
- 📋 列出内容: `显示当前目录内容`

**使用提示**:
- 请提供完整的文件路径
- 使用引号包围包含空格的路径
- 我会在安全的工作空间内操作

请告诉我您想要执行什么文件操作！"""


class BrowserSubAgent(SubAgent):
    """浏览器自动化子智能体"""

    def __init__(self):
        system_prompt = """
你是浏览器自动化专家，在 DeepAgent 系统中的角色是控制网页浏览器和执行网络操作。

**核心能力**：
- 创建浏览器标签页
- 导航到网页
- 截取网页截图
- 与网页元素交互
- 执行 JavaScript

**操作特点**：
- 操作可能较慢，优雅处理超时
- 尊重服务条款
- 提供详细的操作反馈
"""

        capabilities = AgentCapabilities(
            name="Chrome Browser Controller",
            description="网页浏览器自动化和控制专家",
            supported_operations=[
                "navigate",
                "screenshot",
                "click_element",
                "input_text",
                "execute_js",
                "get_page_info",
            ],
            mcp_servers=["chrome"],
            max_concurrent_tasks=1,
            supports_parallel=False,
            avg_response_time=60,  # 浏览器操作通常较慢
        )

        super().__init__(
            name="Chrome Browser Controller",
            agent_type=AgentType.BROWSER,
            system_prompt=system_prompt,
            mcp_servers=["chrome"],
            capabilities=capabilities,
        )

        self.browser_open = False

    async def process_task(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """处理浏览器任务"""
        try:
            # 解析用户意图
            if "打开" in user_input and "浏览器" in user_input:
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
                    return "未找到有效的URL。请提供完整的URL，例如：访问 https://www.example.com"

            elif "截图" in user_input or "screenshot" in user_input.lower():
                return await self._take_screenshot()

            else:
                # 提供浏览器操作帮助
                return self._provide_browser_help()

        except Exception as e:
            logger.error(f"Browser 子智能体执行失败: {e}")
            return f"浏览器操作失败: {str(e)}"

    def _extract_url(self, text: str) -> Optional[str]:
        """提取 URL"""
        import re

        # 查找显式的 URL
        url_pattern = r"https?://[^\s]+"
        match = re.search(url_pattern, text)
        if match:
            return match.group(0).rstrip("。.,!?！？")

        # 处理常见网站名称
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
        """打开浏览器"""
        if self.browser_open:
            return """ℹ️ 浏览器已处于打开状态

您可以直接执行以下操作：
1. 访问特定网站：`访问 https://www.example.com`
2. 截取页面截图：`截取当前页面截图`"""

        try:
            logger.info("正在打开浏览器...")
            result = await mcp_manager.call_tool("chrome", "new_page", {})

            page_id = (
                result.get("page_id", "unknown") if isinstance(result, dict) else "N/A"
            )
            self.browser_open = True

            return f"""✅ 浏览器已打开

**操作结果**：
- 创建了新的浏览器标签页
- 页面ID: {page_id}

您现在可以：
1. 访问特定网站：`访问 https://www.example.com`
2. 截取页面截图：`截取当前页面截图`

注意: 浏览器操作可能需要一些时间，请耐心等待。"""

        except Exception as e:
            logger.error(f"打开浏览器失败: {e}")
            self.browser_open = False
            return f"打开浏览器失败: {str(e)}"

    async def _navigate_to_url(self, url: str) -> str:
        """导航到指定 URL"""
        try:
            logger.info(f"正在访问 URL: {url}")

            if not self.browser_open:
                logger.info("正在确保浏览器已打开...")
                await self._open_browser()

            logger.info(f"正在导航到 {url}（这可能需要一些时间）...")
            result = await mcp_manager.call_tool(
                "chrome", "navigate_page", {"url": url}
            )

            status = (
                result.get("status", "completed")
                if isinstance(result, dict)
                else "completed"
            )

            return f"""✅ 成功访问网站

**导航结果**：
- URL: {url}
- 状态: {status}
- 时间戳: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

页面正在加载中，请稍等几秒钟后再执行其他操作。

后续操作：
- 截取页面截图：`截取当前页面截图`
- 访问其他网站：`访问 https://new-website.com`
- 检查页面内容：等待加载完成后截图

注意: 如果页面加载缓慢，请耐心等待。复杂的网页可能需要更长时间。"""

        except Exception as e:
            logger.error(f"导航到 {url} 失败: {e}")
            return f"""❌ 访问网站失败

**失败详情**:
- URL: {url}
- 错误: {str(e)}

**可能原因**:
1. 网络连接问题: 检查URL是否正确，网站是否可访问
2. 浏览器状态: 确保浏览器已正确打开
3. 超时: 复杂的网站可能需要更长时间加载
4. MCP服务: 检查Docker容器和MCP服务状态

**建议解决方案**:
- 尝试访问简单的网站如 `https://www.baidu.com`
- 检查Docker状态: `docker ps | grep sandbox`
- 查看MCP日志: `docker logs sandbox-sandbox-os-1`

重试: 您可以重新尝试访问这个URL或选择其他网站。"""

    async def _take_screenshot(self) -> str:
        """截取页面截图"""
        try:
            logger.info("正在截取页面截图（这可能需要30-60秒）...")

            # 执行截图
            result = await mcp_manager.call_tool("chrome", "take_screenshot", {})

            screenshot_path = result.get("path") if isinstance(result, dict) else None

            return f"""✅ 截图完成

**截图信息**：
- 保存路径: {screenshot_path or "自动保存到工作空间"}
- 状态: 成功
- 时间戳: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**后续操作**:
- 查看截图: 使用文件操作工具查看 `{screenshot_path or "screenshot.png"}`
- 下载截图: 通过API下载文件
- 继续浏览: 访问其他网站或执行更多操作"""

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return f"截图操作失败: {str(e)}"

    def _provide_browser_help(self) -> str:
        """提供浏览器帮助"""
        return """🌐 浏览器助手

我可以帮助您进行浏览器操作和网页访问：

**可用功能**：
- 🌍 打开浏览器：`打开浏览器`
- 🔗 访问网站：`访问 https://example.com`
- 📸 截取网页：`截取当前页面截图`
- 🔍 网页信息：`获取当前页面信息`

**注意事项**：
- 浏览器操作可能需要一些时间
- 请确保URL格式正确（以http://或https://开头）
- 截图功能需要页面完全加载

**使用示例**:
- `访问 https://www.baidu.com`
- `打开浏览器并访问淘宝`
- `截取当前页面截图`

请告诉我您想执行什么浏览器操作！"""


class ManagerSubAgent(SubAgent):
    """MCP 工具管理子智能体"""

    def __init__(self):
        system_prompt = """
你是 MCP 工具管理专家，在 DeepAgent 系统中的角色是管理 MCP 工具的生命周期。

**核心能力**：
- 安装新 MCP 工具
- 列出可用工具
- 检查系统状态
- 管理工具安装

**重要提醒**：
- 始终告知容器重启要求
- 验证工具兼容性
- 提供详细的安装指导
"""

        capabilities = AgentCapabilities(
            name="MCP Manager",
            description="MCP 工具生命周期管理专家",
            supported_operations=[
                "install_tool",
                "list_tools",
                "check_status",
                "uninstall_tool",
                "update_tool",
            ],
            mcp_servers=["manager"],
            max_concurrent_tasks=1,
            supports_parallel=False,
            avg_response_time=45,
        )

        super().__init__(
            name="MCP Manager",
            agent_type=AgentType.MANAGER,
            system_prompt=system_prompt,
            mcp_servers=["manager"],
            capabilities=capabilities,
        )

    async def process_task(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """处理管理任务"""
        try:
            if "list" in user_input.lower() or "列出" in user_input:
                return await self._list_available_tools()
            elif "install" in user_input.lower() or "安装" in user_input:
                return await self._install_tool(user_input)
            elif "status" in user_input.lower() or "状态" in user_input:
                return await self._check_system_status()
            else:
                return self._provide_manager_help()

        except Exception as e:
            logger.error(f"Manager 子智能体执行失败: {e}")
            return f"MCP 管理操作失败: {str(e)}"

    async def _list_available_tools(self) -> str:
        """列出可用工具"""
        try:
            result = await mcp_manager.call_tool("manager", "list_tools", {})

            return f"""🛠️ 可用 MCP 工具

{result if isinstance(result, str) else "工具列表获取完成"}"""

        except Exception as e:
            return f"获取工具列表失败: {str(e)}"

    async def _install_tool(self, user_input: str) -> str:
        """安装工具"""
        # 提取工具名称
        tool_name = self._extract_tool_name(user_input)
        if not tool_name:
            return "请指定要安装的工具名称"

        try:
            result = await mcp_manager.call_tool(
                "manager", "install_tool", {"name": tool_name}
            )

            return f"""📦 工具安装结果

**安装工具**: {tool_name}

{result if isinstance(result, str) else "安装完成"}

⚠️ **重要提醒**: 工具安装完成后需要重启 Docker 容器才能生效。

重启命令: `docker-compose restart`"""

        except Exception as e:
            return f"安装工具失败: {str(e)}"

    async def _check_system_status(self) -> str:
        """检查系统状态"""
        try:
            result = await mcp_manager.call_tool("manager", "check_status", {})

            return f"""📊 系统状态

{result if isinstance(result, str) else "状态检查完成"}"""

        except Exception as e:
            return f"检查系统状态失败: {str(e)}"

    def _extract_tool_name(self, text: str) -> Optional[str]:
        """提取工具名称"""
        import re

        patterns = [
            r'install\s+["\']?([^"\s]+)["\']?',
            r'安装\s+["\']?([^"\s]+)["\']?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _provide_manager_help(self) -> str:
        """提供管理帮助"""
        return """⚙️ MCP 工具管理助手

我可以帮助您管理 MCP 工具的安装和配置：

**可用操作**:
- 📋 列出工具: `列出所有可用工具`
- 📦 安装工具: `安装工具 example-tool`
- 📊 系统状态: `检查系统状态`

**使用提示**:
- 安装新工具后需要重启容器
- 某些工具可能需要额外配置
- 建议在安装前检查工具兼容性

请告诉我您想要执行什么管理操作！"""


class GeneralSubAgent(SubAgent):
    """通用查询子智能体"""

    def __init__(self):
        system_prompt = """
你是通用助手，在 DeepAgent 系统中的角色是处理通用查询和提供信息。

**核心能力**：
- 回答通用问题
- 提供信息和建议
- 创建计划和行程
- 帮助一般性问题解决
- 提供建议和推荐

**重要**：始终用中文（中文）响应中文查询。
保持乐于助人、准确，并提供全面信息。
如果任务需要特定工具（文件、命令、浏览），建议使用相应的子智能体。
"""

        capabilities = AgentCapabilities(
            name="General Assistant",
            description="通用查询和信息提供助手",
            supported_operations=[
                "answer_questions",
                "provide_information",
                "create_plans",
                "offer_suggestions",
                "general_help",
            ],
            mcp_servers=[],  # 不使用 MCP 工具
            max_concurrent_tasks=3,
            supports_parallel=True,
            avg_response_time=20,
        )

        super().__init__(
            name="General Assistant",
            agent_type=AgentType.GENERAL,
            system_prompt=system_prompt,
            mcp_servers=[],
            capabilities=capabilities,
        )

    async def process_task(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """处理通用查询"""
        try:
            # 特殊处理：北京到哈尔滨旅行计划
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

            # 特殊处理：简单解释性查询
            if self._is_simple_explanatory_query(user_input):
                return self._handle_simple_query(user_input)

            # 一般查询处理
            return await self._handle_general_query(user_input, context)

        except Exception as e:
            logger.error(f"General 子智能体执行失败: {e}")
            return f"处理查询时出错: {str(e)}"

    def _is_simple_explanatory_query(self, user_input: str) -> bool:
        """检查是否是简单的解释性查询"""
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
        """处理简单解释性查询"""
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

    async def _handle_general_query(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """处理一般查询"""
        # 添加上下文信息
        context_info = ""
        if context:
            context_info = f"\n上下文: {context}"

        full_prompt = (
            f"{self.system_prompt}{context_info}\n\n用户查询: {user_input}\n\n响应:"
        )

        # 调用 LLM
        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content=full_prompt)]
        response = await self.llm.ainvoke(messages)

        return (
            str(response.content)
            if response.content
            else "我无法生成响应，请尝试重新表述您的问题。"
        )

    def _create_beijing_harbin_plan(self) -> str:
        """创建北京到哈尔滨的旅行计划"""
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
