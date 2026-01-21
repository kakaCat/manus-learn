#!/usr/bin/env python3
"""
MCP Manager Server - 元 MCP 服务器
允许 AI Agent 通过 MCP 协议管理其他 MCP 服务器

提供工具:
- list_available_mcps: 列出市场中所有可用的 MCP
- list_installed_mcps: 列出已安装的 MCP
- install_mcp: 安装新的 MCP 工具
- uninstall_mcp: 卸载 MCP 工具
- get_mcp_status: 查看 MCP 运行状态
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# MCP 市场注册表
MCP_REGISTRY = {
    "filesystem": {
        "name": "Filesystem MCP",
        "description": "官方文件系统操作服务器 - 提供文件读写、目录管理等功能",
        "type": "npm",
        "package": "@modelcontextprotocol/server-filesystem",
        "args": ["/root/shared/workspace"],
        "official": True,
        "category": "文件操作",
        "capabilities": ["read_file", "write_file", "list_directory", "search_files"],
    },
    "chrome": {
        "name": "Chrome DevTools MCP",
        "description": "Chrome 官方浏览器自动化服务器 - 基于 Puppeteer 的强大浏览器控制",
        "type": "npm",
        "package": "chrome-devtools-mcp",
        "args": [],
        "official": True,
        "category": "浏览器",
        "capabilities": ["navigate", "screenshot", "click", "fill_form", "execute_js"],
    },
    "puppeteer": {
        "name": "Puppeteer MCP",
        "description": "官方 Puppeteer 浏览器自动化 - 完整的浏览器控制能力",
        "type": "npm",
        "package": "@modelcontextprotocol/server-puppeteer",
        "args": [],
        "official": True,
        "category": "浏览器",
        "capabilities": ["browser_automation", "web_scraping", "testing"],
    },
    "brave-search": {
        "name": "Brave Search MCP",
        "description": "Brave 搜索引擎集成 - 隐私友好的网络搜索",
        "type": "npm",
        "package": "@modelcontextprotocol/server-brave-search",
        "args": [],
        "official": True,
        "category": "搜索",
        "capabilities": ["web_search"],
    },
    "memory": {
        "name": "Memory MCP",
        "description": "官方记忆存储服务器 - 为 AI 提供持久化记忆能力",
        "type": "npm",
        "package": "@modelcontextprotocol/server-memory",
        "args": [],
        "official": True,
        "category": "工具",
        "capabilities": ["store_memory", "recall_memory", "search_memory"],
    },
}

CONTAINER_NAME = "sandbox-sandbox-os-1"
SUPERVISORD_CONF = "/etc/supervisor/conf.d/supervisord.conf"
INSTALLED_JSON = Path("/opt/mcp-servers/mcp_manager/installed.json")


class MCPManagerServer:
    """MCP Manager 服务器 - 让 AI 管理其他 MCP"""

    def __init__(self):
        self.server = Server("mcp-manager")
        self.installed = self._load_installed()
        self._register_handlers()

    def _load_installed(self) -> dict:
        """加载已安装的 MCP 列表"""
        if INSTALLED_JSON.exists():
            return json.loads(INSTALLED_JSON.read_text())
        return {}

    def _save_installed(self):
        """保存已安装的 MCP 列表"""
        INSTALLED_JSON.parent.mkdir(parents=True, exist_ok=True)
        INSTALLED_JSON.write_text(json.dumps(self.installed, indent=2, ensure_ascii=False))

    def _register_handlers(self):
        """注册所有工具处理器"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="list_available_mcps",
                    description="列出 MCP 市场中所有可用的工具服务器。返回包含名称、描述、类别、能力的列表。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "可选：按类别过滤 (浏览器/文件操作/搜索/工具)",
                            }
                        },
                    },
                ),
                Tool(
                    name="list_installed_mcps",
                    description="列出当前已安装的所有 MCP 服务器及其状态",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="install_mcp",
                    description="从市场安装一个新的 MCP 工具。安装后需要重启容器才能生效。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "mcp_id": {
                                "type": "string",
                                "description": "要安装的 MCP ID (如: memory, puppeteer, brave-search)",
                            }
                        },
                        "required": ["mcp_id"],
                    },
                ),
                Tool(
                    name="uninstall_mcp",
                    description="卸载一个已安装的 MCP 工具",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "mcp_id": {
                                "type": "string",
                                "description": "要卸载的 MCP ID",
                            }
                        },
                        "required": ["mcp_id"],
                    },
                ),
                Tool(
                    name="get_mcp_status",
                    description="查看所有已安装 MCP 的运行状态 (通过 supervisord)",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            if name == "list_available_mcps":
                return await self._list_available_mcps(arguments)
            elif name == "list_installed_mcps":
                return await self._list_installed_mcps()
            elif name == "install_mcp":
                return await self._install_mcp(arguments)
            elif name == "uninstall_mcp":
                return await self._uninstall_mcp(arguments)
            elif name == "get_mcp_status":
                return await self._get_mcp_status()
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _list_available_mcps(self, args: dict) -> list[TextContent]:
        """列出可用的 MCP"""
        category_filter = args.get("category")

        result = {
            "total": len(MCP_REGISTRY),
            "mcps": []
        }

        for mcp_id, info in MCP_REGISTRY.items():
            if category_filter and info["category"] != category_filter:
                continue

            mcp_info = {
                "id": mcp_id,
                "name": info["name"],
                "description": info["description"],
                "category": info["category"],
                "official": info["official"],
                "capabilities": info.get("capabilities", []),
                "installed": mcp_id in self.installed,
            }
            result["mcps"].append(mcp_info)

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]

    async def _list_installed_mcps(self) -> list[TextContent]:
        """列出已安装的 MCP"""
        if not self.installed:
            return [TextContent(type="text", text="没有已安装的 MCP 服务器")]

        result = {
            "total": len(self.installed),
            "mcps": []
        }

        for mcp_id, info in self.installed.items():
            result["mcps"].append({
                "id": mcp_id,
                "name": info.get("name", "Unknown"),
                "type": info.get("type", "unknown"),
                "package": info.get("package"),
                "category": info.get("category"),
            })

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]

    async def _install_mcp(self, args: dict) -> list[TextContent]:
        """安装 MCP 工具"""
        mcp_id = args["mcp_id"]

        if mcp_id not in MCP_REGISTRY:
            return [TextContent(
                type="text",
                text=f"❌ 错误: 未知的 MCP ID '{mcp_id}'. 请使用 list_available_mcps 查看可用的 MCP。"
            )]

        if mcp_id in self.installed:
            return [TextContent(
                type="text",
                text=f"⚠️  MCP '{mcp_id}' 已经安装"
            )]

        info = MCP_REGISTRY[mcp_id]

        try:
            # 在容器中安装 npm 包
            if info["type"] == "npm":
                cmd = [
                    "docker", "exec", CONTAINER_NAME,
                    "npm", "install", "-g", info["package"]
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    return [TextContent(
                        type="text",
                        text=f"❌ 安装失败: {result.stderr}"
                    )]

                # 生成 supervisord 配置
                config = self._generate_supervisord_config(mcp_id, info)

                # 保存到已安装列表
                self.installed[mcp_id] = info
                self._save_installed()

                return [TextContent(
                    type="text",
                    text=f"""✅ {info['name']} 安装成功！

📦 包: {info['package']}
📝 Supervisord 配置已生成:
{config}

⚠️  重要: 需要重启 Docker 容器才能启动此 MCP 服务:
docker-compose restart

或者手动添加配置到 {SUPERVISORD_CONF} 并执行:
supervisorctl reread && supervisorctl update
"""
                )]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 安装失败: {str(e)}")]

    async def _uninstall_mcp(self, args: dict) -> list[TextContent]:
        """卸载 MCP 工具"""
        mcp_id = args["mcp_id"]

        if mcp_id not in self.installed:
            return [TextContent(type="text", text=f"❌ MCP '{mcp_id}' 未安装")]

        info = self.installed[mcp_id]

        try:
            if info["type"] == "npm":
                cmd = [
                    "docker", "exec", CONTAINER_NAME,
                    "npm", "uninstall", "-g", info["package"]
                ]
                subprocess.run(cmd, capture_output=True, text=True)

            # 从已安装列表移除
            del self.installed[mcp_id]
            self._save_installed()

            return [TextContent(
                type="text",
                text=f"""✅ {info['name']} 已卸载

⚠️  注意: 请手动从 {SUPERVISORD_CONF} 中删除 [program:mcp-{mcp_id}] 配置段，
然后重启容器: docker-compose restart
"""
            )]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 卸载失败: {str(e)}")]

    async def _get_mcp_status(self) -> list[TextContent]:
        """查看 MCP 状态"""
        cmd = ["docker", "exec", CONTAINER_NAME, "supervisorctl", "status"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"❌ 无法获取状态: {result.stderr}")]

        # 过滤出 MCP 相关进程
        mcp_processes = []
        for line in result.stdout.split("\n"):
            if "mcp-" in line.lower():
                mcp_processes.append(line)

        if not mcp_processes:
            return [TextContent(type="text", text="没有运行中的 MCP 服务器")]

        return [TextContent(
            type="text",
            text=f"MCP 服务器状态:\n\n" + "\n".join(mcp_processes)
        )]

    def _generate_supervisord_config(self, mcp_id: str, info: dict) -> str:
        """生成 supervisord 配置"""
        args_str = " ".join(info.get("args", []))
        config = f"""
; MCP {info['name']}
[program:mcp-{mcp_id}]
command=/usr/bin/npx -y {info['package']} {args_str}
directory=/root/shared/workspace
environment=NODE_ENV="production"
autorestart=true
priority=60{len(self.installed) + 3}
stdout_logfile=/var/log/mcp/{mcp_id}-stdout.log
stderr_logfile=/var/log/mcp/{mcp_id}-stderr.log
startsecs=5
"""
        return config

    async def run(self):
        """运行服务器"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """主函数"""
    import asyncio
    server = MCPManagerServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
