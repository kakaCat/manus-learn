#!/usr/bin/env python3
"""
MCP Manager - 管理 Docker 沙盒中的 MCP 服务器

用法:
    python mcp_manager.py list                    # 列出所有可用的 MCP
    python mcp_manager.py installed               # 列出已安装的 MCP
    python mcp_manager.py install <name>          # 安装 MCP
    python mcp_manager.py uninstall <name>        # 卸载 MCP
    python mcp_manager.py status                  # 查看运行状态
    python mcp_manager.py restart <name>          # 重启 MCP
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# MCP 市场注册表
MCP_REGISTRY = {
    "filesystem": {
        "name": "Filesystem MCP",
        "description": "官方文件系统操作服务器",
        "type": "npm",
        "package": "@modelcontextprotocol/server-filesystem",
        "args": ["/root/shared/workspace"],
        "official": True,
        "category": "文件操作",
    },
    "chrome": {
        "name": "Chrome DevTools MCP",
        "description": "Chrome 官方浏览器自动化服务器",
        "type": "npm",
        "package": "chrome-devtools-mcp",
        "args": [],
        "official": True,
        "category": "浏览器",
    },
    "puppeteer": {
        "name": "Puppeteer MCP",
        "description": "官方 Puppeteer 浏览器自动化",
        "type": "npm",
        "package": "@modelcontextprotocol/server-puppeteer",
        "args": [],
        "official": True,
        "category": "浏览器",
    },
    "brave-search": {
        "name": "Brave Search MCP",
        "description": "Brave 搜索引擎集成",
        "type": "npm",
        "package": "@modelcontextprotocol/server-brave-search",
        "args": [],
        "official": True,
        "category": "搜索",
    },
    "memory": {
        "name": "Memory MCP",
        "description": "官方记忆存储服务器",
        "type": "npm",
        "package": "@modelcontextprotocol/server-memory",
        "args": [],
        "official": True,
        "category": "工具",
    },
    # 社区 MCP
    "mac-shell": {
        "name": "Mac Shell MCP",
        "description": "macOS 终端命令执行（社区）",
        "type": "github",
        "repo": "cfdude/mac-shell-mcp",
        "args": [],
        "official": False,
        "category": "Shell",
    },
}

CONTAINER_NAME = "sandbox-sandbox-os-1"
SUPERVISORD_CONF = "/etc/supervisor/conf.d/supervisord.conf"


class MCPManager:
    """MCP 服务器管理器"""

    def __init__(self):
        self.installed = self._load_installed()

    def _load_installed(self) -> Dict:
        """从 supervisord 配置中加载已安装的 MCP"""
        # 简化版：从本地配置文件读取
        installed_file = Path("sandbox/mcp-servers/installed.json")
        if installed_file.exists():
            return json.loads(installed_file.read_text())
        return {}

    def _save_installed(self):
        """保存已安装的 MCP 列表"""
        installed_file = Path("sandbox/mcp-servers/installed.json")
        installed_file.write_text(json.dumps(self.installed, indent=2))

    def list_available(self):
        """列出所有可用的 MCP"""
        print("\n📦 可用的 MCP 服务器:\n")

        categories = {}
        for mcp_id, info in MCP_REGISTRY.items():
            category = info.get("category", "其他")
            if category not in categories:
                categories[category] = []
            categories[category].append((mcp_id, info))

        for category, mcps in sorted(categories.items()):
            print(f"🏷️  {category}")
            print("─" * 60)
            for mcp_id, info in mcps:
                status = "✅ 已安装" if mcp_id in self.installed else "  "
                official = "🏅 官方" if info["official"] else "👥 社区"
                print(f"  {status} {mcp_id:<20} {official} {info['name']}")
                print(f"      {info['description']}")
            print()

    def list_installed(self):
        """列出已安装的 MCP"""
        if not self.installed:
            print("❌ 没有已安装的 MCP 服务器")
            return

        print("\n✅ 已安装的 MCP 服务器:\n")
        for mcp_id, info in self.installed.items():
            print(f"  • {mcp_id:<20} {info.get('name', 'Unknown')}")
            print(f"    类型: {info.get('type', 'unknown')}")
            if info.get('package'):
                print(f"    包: {info['package']}")
        print()

    def install(self, mcp_id: str):
        """安装 MCP 服务器"""
        if mcp_id not in MCP_REGISTRY:
            print(f"❌ 未知的 MCP: {mcp_id}")
            print(f"💡 运行 'python mcp_manager.py list' 查看可用的 MCP")
            return

        if mcp_id in self.installed:
            print(f"⚠️  {mcp_id} 已经安装")
            return

        info = MCP_REGISTRY[mcp_id]
        print(f"📥 正在安装 {info['name']}...")

        try:
            if info["type"] == "npm":
                # 在容器中安装 npm 包
                cmd = [
                    "docker", "exec", CONTAINER_NAME,
                    "npm", "install", "-g", info["package"]
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"❌ 安装失败: {result.stderr}")
                    return

                print(f"✅ npm 包安装成功")

                # 生成 supervisord 配置
                self._add_supervisord_config(mcp_id, info)

            elif info["type"] == "github":
                print("⚠️  GitHub 安装暂未实现")
                return

            # 保存到已安装列表
            self.installed[mcp_id] = info
            self._save_installed()

            print(f"✅ {info['name']} 安装完成")
            print(f"💡 运行 'docker-compose restart' 重启容器以应用更改")

        except Exception as e:
            print(f"❌ 安装失败: {e}")

    def _add_supervisord_config(self, mcp_id: str, info: Dict):
        """添加 supervisord 配置"""
        if info["type"] == "npm":
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
            print(f"\n📝 Supervisord 配置:")
            print(config)

            # 自动追加配置到容器内的 supervisord.conf
            try:
                # 写入临时文件
                temp_config = Path(f"/tmp/mcp-{mcp_id}.conf")
                temp_config.write_text(config)

                # 复制到容器
                copy_cmd = ["docker", "cp", str(temp_config),
                           f"{CONTAINER_NAME}:/tmp/mcp-{mcp_id}.conf"]
                subprocess.run(copy_cmd, check=True)

                # 追加到 supervisord.conf
                append_cmd = [
                    "docker", "exec", CONTAINER_NAME,
                    "bash", "-c",
                    f"cat /tmp/mcp-{mcp_id}.conf >> {SUPERVISORD_CONF}"
                ]
                subprocess.run(append_cmd, check=True)

                # 重新加载 supervisord 配置
                reload_cmd = [
                    "docker", "exec", CONTAINER_NAME,
                    "supervisorctl", "reread"
                ]
                subprocess.run(reload_cmd, check=True)

                update_cmd = [
                    "docker", "exec", CONTAINER_NAME,
                    "supervisorctl", "update"
                ]
                subprocess.run(update_cmd, check=True)

                print(f"✅ Supervisord 配置已自动添加并重新加载")

                # 清理临时文件
                temp_config.unlink()

            except Exception as e:
                print(f"⚠️  自动配置失败: {e}")
                print(f"💡 请手动将上述配置添加到容器的 {SUPERVISORD_CONF}")

    def uninstall(self, mcp_id: str):
        """卸载 MCP 服务器"""
        if mcp_id not in self.installed:
            print(f"❌ {mcp_id} 未安装")
            return

        info = self.installed[mcp_id]
        print(f"🗑️  正在卸载 {info['name']}...")

        try:
            if info["type"] == "npm":
                cmd = [
                    "docker", "exec", CONTAINER_NAME,
                    "npm", "uninstall", "-g", info["package"]
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"⚠️  卸载警告: {result.stderr}")

            # 从已安装列表移除
            del self.installed[mcp_id]
            self._save_installed()

            print(f"✅ {info['name']} 已卸载")
            print(f"💡 请手动从 supervisord.conf 中删除相关配置")

        except Exception as e:
            print(f"❌ 卸载失败: {e}")

    def status(self):
        """查看所有 MCP 服务状态"""
        print("\n🔍 MCP 服务器状态:\n")

        cmd = ["docker", "exec", CONTAINER_NAME, "supervisorctl", "status"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ 无法获取状态: {result.stderr}")
            return

        # 过滤出 MCP 相关的进程
        for line in result.stdout.split("\n"):
            if "mcp-" in line.lower():
                print(f"  {line}")

    def restart(self, mcp_id: str):
        """重启指定的 MCP 服务器"""
        if mcp_id not in self.installed:
            print(f"❌ {mcp_id} 未安装")
            return

        program_name = f"mcp-{mcp_id}"
        print(f"🔄 正在重启 {program_name}...")

        cmd = [
            "docker", "exec", CONTAINER_NAME,
            "supervisorctl", "restart", program_name
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ {program_name} 重启成功")
        else:
            print(f"❌ 重启失败: {result.stderr}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    manager = MCPManager()
    command = sys.argv[1]

    if command == "list":
        manager.list_available()
    elif command == "installed":
        manager.list_installed()
    elif command == "install":
        if len(sys.argv) < 3:
            print("❌ 请指定要安装的 MCP ID")
            sys.exit(1)
        manager.install(sys.argv[2])
    elif command == "uninstall":
        if len(sys.argv) < 3:
            print("❌ 请指定要卸载的 MCP ID")
            sys.exit(1)
        manager.uninstall(sys.argv[2])
    elif command == "status":
        manager.status()
    elif command == "restart":
        if len(sys.argv) < 3:
            print("❌ 请指定要重启的 MCP ID")
            sys.exit(1)
        manager.restart(sys.argv[2])
    else:
        print(f"❌ 未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
