# 🚀 Manus AI Sandbox 启动指南

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│ 浏览器 (http://localhost:5173)                              │
│   ├── 📊 监控面板 - 实时查看沙盒状态                        │
│   ├── 💬 AI 聊天 - 与 AI Agent 对话                         │
│   └── 📦 MCP 市场 - 安装新工具                              │
└────────────────┬────────────────────────────────────────────┘
                 │ WebSocket + HTTP
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 后端服务器 (http://localhost:8000)                          │
│   ├── FastAPI - REST API 和 WebSocket                       │
│   ├── LangChain Agent - AI 编排                             │
│   └── Ollama LLM - 本地大语言模型                            │
└────────────────┬────────────────────────────────────────────┘
                 │ MCP Protocol (stdio)
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Docker 沙盒容器 (sandbox-os)                                │
│   ├── VNC 服务 (port 6080) - 远程桌面                       │
│   ├── mcp-manager - MCP 管理服务                            │
│   ├── mcp-shell - 命令执行                                   │
│   ├── mcp-filesystem - 文件操作                             │
│   └── mcp-chrome - 浏览器自动化                             │
└─────────────────────────────────────────────────────────────┘
```

## 前置要求

### 1. Docker 和 Docker Compose

**macOS**:
```bash
# 检查 Docker 是否安装
docker --version
docker-compose --version

# 如果没有安装，使用 Homebrew 安装
brew install docker docker-compose
```

**启动 Docker Desktop**:
- 打开 Docker Desktop 应用
- 等待 Docker 守护进程启动（菜单栏图标变绿）

### 2. Node.js 和 npm

**检查版本**:
```bash
node --version  # 应该 >= 18.x
npm --version   # 应该 >= 9.x
```

**如果需要安装**:
```bash
brew install node
```

### 3. Python 3.11+

**检查版本**:
```bash
python3 --version  # 应该 >= 3.11
```

**如果需要安装**:
```bash
brew install python@3.11
```

### 4. Ollama (本地 LLM)

**安装 Ollama**:
```bash
# 下载并安装
curl -fsSL https://ollama.com/install.sh | sh

# 或使用 Homebrew
brew install ollama
```

**下载模型**:
```bash
# 下载 qwen2.5 模型（推荐，速度快）
ollama pull qwen2.5

# 或下载 llama3 模型
ollama pull llama3

# 验证模型
ollama list
```

**启动 Ollama 服务**:
```bash
# 启动服务（在后台运行）
ollama serve

# 测试服务
curl http://localhost:11434/api/tags
```

## 启动步骤

### 第 1 步：构建并启动 Docker 沙盒容器

```bash
# 进入沙盒目录
cd /Users/yunpeng/Documents/github/manus-learn/sandbox

# 构建 Docker 镜像（首次启动或 Dockerfile 更改后）
docker-compose build

# 启动容器
docker-compose up -d

# 查看容器状态
docker-compose ps

# 查看日志（确认所有服务启动成功）
docker-compose logs -f
```

**预期输出**:
```
NAME                  IMAGE           STATUS         PORTS
sandbox-sandbox-os-1  sandbox-os      Up 10 seconds  0.0.0.0:6080->6080/tcp
```

**验证 MCP 服务**:
```bash
# 进入容器
docker exec -it sandbox-sandbox-os-1 bash

# 检查 supervisord 状态
supervisorctl status

# 预期输出：
# mcp-manager      RUNNING   pid 10, uptime 0:01:00
# mcp-shell        RUNNING   pid 11, uptime 0:01:00
# mcp-filesystem   RUNNING   pid 12, uptime 0:01:00
# mcp-chrome       RUNNING   pid 13, uptime 0:01:00
# websockify       RUNNING   pid 14, uptime 0:01:00
# x11vnc           RUNNING   pid 15, uptime 0:01:00
# xvfb             RUNNING   pid 16, uptime 0:01:00
# fluxbox          RUNNING   pid 17, uptime 0:01:00

# 退出容器
exit
```

### 第 2 步：启动后端服务

**打开新的终端窗口**:

```bash
# 进入后端目录
cd /Users/yunpeng/Documents/github/manus-learn/backend

# 创建虚拟环境（首次运行）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖（首次运行或 requirements.txt 更改后）
pip install -r requirements.txt

# 启动后端服务
python main.py
```

**预期输出**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**验证后端 API**:

打开新终端：
```bash
# 检查健康状态
curl http://localhost:8000/health

# 预期输出：{"status":"healthy"}

# 检查沙盒状态
curl http://localhost:8000/api/sandbox/status

# 应该返回 JSON 数据包含 MCP 状态
```

### 第 3 步：启动前端

**打开新的终端窗口**:

```bash
# 进入前端目录
cd /Users/yunpeng/Documents/github/manus-learn/sandbox/frontend

# 安装依赖（首次运行或 package.json 更改后）
npm install

# 启动开发服务器
npm run dev
```

**预期输出**:
```
VITE v5.0.0  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

### 第 4 步：访问 Web 界面

**打开浏览器访问**: http://localhost:5173

你应该看到三栏布局：

**左侧面板**:
- **📊 Monitor 标签（默认）**: 实时监控沙盒状态
  - 容器状态卡片
  - CPU/内存/磁盘资源使用率
  - MCP 服务器状态列表
  - 运行进程列表
  - 最近日志

- **🖥️ VNC 标签**: 远程桌面查看器
  - 点击 "Connect" 连接到 VNC
  - 可以看到沙盒的图形化桌面

**中间面板**:
- **💬 AI 聊天**: 与 AI Agent 交互
  - 输入命令让 AI 执行任务
  - 实时查看 AI 响应

**右侧面板**:
- **📦 Marketplace 标签**: MCP 工具市场
  - 浏览可用的 MCP 工具
  - 点击 "Install" 安装新工具

- **🛠️ Tools 标签**: 已安装的工具（开发中）

## 使用示例

### 1. 监控沙盒健康状态

1. 打开 http://localhost:5173
2. 默认就在 Monitor 标签
3. 查看状态卡片：
   - Container: Running ✅
   - MCP Servers: 4 ✅
   - Processes: 20+ ✅
4. 查看资源使用率（应该都在正常范围）
5. 确认所有 MCP 服务器都是绿点（RUNNING）

### 2. 与 AI Agent 交互

**切换到中间面板的聊天界面**:

```
你: Hello! 你能做什么？
AI: 我可以帮你控制沙盒环境，包括执行命令、操作文件、自动化浏览器等...

你: 列出当前工作目录的文件
AI: [调用 filesystem_list_directory]
    当前有以下文件...

你: 创建一个 hello.txt 文件，内容是 "Hello Manus!"
AI: [调用 filesystem_write_file]
    文件创建成功！

你: 执行 Python 命令打印 "Hello World"
AI: [调用 shell_execute_command]
    输出: Hello World

你: 打开浏览器访问 example.com 并截图
AI: [调用 chrome_launch_browser, chrome_navigate_to_url, chrome_take_screenshot]
    已保存截图到 workspace/screenshots/example.png
```

### 3. 安装新的 MCP 工具

**AI 主动发现并安装工具**:

```
你: 帮我搜索一下最新的 Python 新闻
AI: 我需要搜索能力，让我检查市场...
    [调用 manager_list_available_mcps]
    找到了 Brave Search MCP，我来安装它
    [调用 manager_install_mcp with mcp_id="brave-search"]
    安装完成！请重启容器: docker-compose restart
```

**手动从市场安装**:

1. 点击右侧 "📦 Marketplace" 标签
2. 浏览可用的 MCP 工具
3. 选择需要的工具（如 Memory MCP）
4. 点击 "Install" 按钮
5. 等待安装完成
6. 重启容器：
   ```bash
   docker-compose restart
   ```
7. 刷新页面，新工具就可以使用了

### 4. 使用 VNC 查看图形界面

1. 点击左侧面板的 "🖥️ VNC" 标签
2. 点击 "Connect" 按钮
3. 等待连接成功（状态变为绿色）
4. 你会看到沙盒的桌面环境（Fluxbox + Xterm）
5. 在聊天中让 AI 执行图形化操作，可以在 VNC 中实时看到

**示例**:
```
你: 在终端中运行 htop 命令
AI: [执行命令]

# 切换到 VNC 标签，你会看到 xterm 中运行着 htop
```

## 故障排除

### 问题 1: Docker 容器无法启动

**症状**: `docker-compose up -d` 失败

**解决方案**:
```bash
# 检查 Docker 守护进程
docker ps

# 检查日志
docker-compose logs

# 重新构建镜像
docker-compose build --no-cache

# 清理旧容器和镜像
docker-compose down -v
docker system prune -a
```

### 问题 2: 后端无法连接到 MCP 服务器

**症状**: `/api/sandbox/status` 返回错误

**解决方案**:
```bash
# 检查容器是否运行
docker ps

# 检查 MCP 服务状态
docker exec -it sandbox-sandbox-os-1 supervisorctl status

# 查看 MCP 日志
docker exec -it sandbox-sandbox-os-1 cat /var/log/mcp/shell-stdout.log
docker exec -it sandbox-sandbox-os-1 cat /var/log/mcp/manager-stdout.log

# 重启 MCP 服务
docker exec -it sandbox-sandbox-os-1 supervisorctl restart all
```

### 问题 3: Ollama 无法连接

**症状**: 后端日志显示 "Connection refused to localhost:11434"

**解决方案**:
```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 如果没有运行，启动 Ollama
ollama serve

# 确认模型已下载
ollama list

# 如果没有模型，下载一个
ollama pull qwen2.5
```

### 问题 4: 前端无法连接后端

**症状**: 监控面板显示 "Loading..." 或 "Disconnected"

**解决方案**:
```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查浏览器控制台（F12）查看 CORS 错误

# 如果有 CORS 错误，检查 backend/config.py
# 确保 cors_origins 包含 "http://localhost:5173"
```

### 问题 5: VNC 无法连接

**症状**: 点击 "Connect" 后显示 "Connection Lost"

**解决方案**:
```bash
# 检查 websockify 是否运行
docker exec -it sandbox-sandbox-os-1 supervisorctl status websockify

# 检查端口映射
docker ps | grep 6080

# 重启 VNC 服务
docker exec -it sandbox-sandbox-os-1 supervisorctl restart websockify x11vnc

# 查看 VNC 日志
docker exec -it sandbox-sandbox-os-1 cat /var/log/x11vnc.log
```

### 问题 6: 监控数据不更新

**症状**: 资源使用率一直是 0% 或不变化

**解决方案**:
```bash
# 检查 shell MCP 是否正常
docker exec -it sandbox-sandbox-os-1 supervisorctl status mcp-shell

# 手动测试命令
docker exec -it sandbox-sandbox-os-1 top -bn1

# 查看 shell MCP 日志
docker exec -it sandbox-sandbox-os-1 cat /var/log/mcp/shell-stderr.log

# 重启 shell MCP
docker exec -it sandbox-sandbox-os-1 supervisorctl restart mcp-shell
```

## 开发工作流

### 修改后端代码

```bash
# 代码会自动重载（uvicorn reload=True）
# 修改 backend/*.py 文件后，后端会自动重启
# 查看终端确认重启成功
```

### 修改前端代码

```bash
# Vite 热重载（HMR）
# 修改 sandbox/frontend/src/*.vue 文件后，浏览器会自动刷新
# 无需手动操作
```

### 修改 Docker 配置

```bash
# 修改 Dockerfile 或 supervisord.conf 后需要重新构建
cd sandbox
docker-compose down
docker-compose build
docker-compose up -d
```

### 查看实时日志

**后端日志**:
```bash
# 在后端终端中查看（自动输出）
```

**前端日志**:
```bash
# 在前端终端中查看（自动输出）
# 或在浏览器控制台（F12）查看
```

**Docker 日志**:
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务
docker exec -it sandbox-sandbox-os-1 supervisorctl tail -f mcp-manager
docker exec -it sandbox-sandbox-os-1 supervisorctl tail -f mcp-shell
```

## 停止系统

### 优雅停止

```bash
# 停止前端（在前端终端按 Ctrl+C）

# 停止后端（在后端终端按 Ctrl+C）

# 停止 Docker 容器
cd sandbox
docker-compose down
```

### 完全清理

```bash
# 停止并删除所有资源
docker-compose down -v

# 删除构建的镜像
docker rmi sandbox-os

# 清理 Python 虚拟环境
rm -rf backend/venv

# 清理 Node 模块
rm -rf sandbox/frontend/node_modules
```

## 性能优化建议

### 1. 降低监控刷新频率

编辑 `sandbox/frontend/src/components/SandboxMonitor.vue`:
```javascript
// 从 5 秒改为 10 秒
const refreshInterval = 10000
```

### 2. 使用更轻量的 LLM 模型

```bash
# qwen2.5 比 llama3 更快
ollama pull qwen2.5:0.5b  # 超小模型，速度极快
```

编辑 `backend/config.py`:
```python
ollama_model: str = Field(default="qwen2.5:0.5b")
```

### 3. 限制日志大小

编辑 `sandbox/docker/supervisord.conf`:
```ini
# 限制单个日志文件大小
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=3
```

## 下一步

系统启动成功后，你可以：

1. **探索监控面板**: 熟悉各种指标和状态
2. **与 AI 交互**: 尝试各种命令和任务
3. **安装新工具**: 从市场安装 Memory、Brave Search 等 MCP
4. **开发自定义功能**: 修改代码添加新特性
5. **阅读文档**: 查看 [SANDBOX_MONITORING.md](SANDBOX_MONITORING.md)、[BACKEND_IMPLEMENTATION_COMPLETE.md](BACKEND_IMPLEMENTATION_COMPLETE.md) 了解更多细节

## 快速启动脚本

创建 `start.sh` 快速启动所有服务：

```bash
#!/bin/bash

echo "🚀 启动 Manus AI Sandbox..."

# 启动 Ollama（如果未运行）
if ! pgrep -x "ollama" > /dev/null; then
    echo "📦 启动 Ollama..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# 启动 Docker 容器
echo "🐳 启动 Docker 容器..."
cd sandbox
docker-compose up -d
cd ..

# 等待容器启动
echo "⏳ 等待容器启动..."
sleep 10

# 启动后端（在新终端）
echo "🔧 启动后端..."
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)'/backend && source venv/bin/activate && python main.py"'

# 等待后端启动
sleep 5

# 启动前端（在新终端）
echo "🎨 启动前端..."
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)'/sandbox/frontend && npm run dev"'

# 等待前端启动
sleep 5

# 打开浏览器
echo "🌐 打开浏览器..."
open http://localhost:5173

echo "✅ 所有服务已启动！"
echo ""
echo "📊 监控面板: http://localhost:5173"
echo "🔧 后端 API: http://localhost:8000"
echo "🖥️  VNC 桌面: http://localhost:6080"
echo ""
echo "使用 Ctrl+C 停止各个服务"
```

**使用方法**:
```bash
chmod +x start.sh
./start.sh
```

---

**创建日期**: 2026-01-21
**作者**: Manus AI Sandbox Team
**版本**: 1.0.0
