# 后端 AI Agent 部署指南

## 概述

后端 AI Agent 使用 LangChain + Ollama 集成了所有 MCP 服务器，包括革命性的 **MCP Manager** 元服务器，让 AI 可以自主安装新工具。

## 架构

```
User Request
    ↓
FastAPI Endpoints (main.py)
    ↓
Sandbox Agent (agent.py)
    ↓
LangChain Tools ← MCP Client (mcp_client.py)
    ↓
Docker exec → MCP Servers in Container
    ├── mcp-manager (Meta-MCP) ⭐
    ├── mcp-shell
    ├── mcp-filesystem  
    ├── mcp-chrome
    └── 动态安装的 MCP...
```

## 前置条件

### 1. Docker 容器运行

```bash
cd sandbox
docker-compose up -d

# 验证 MCP 服务器运行
docker exec sandbox-sandbox-os-1 supervisorctl status | grep mcp
```

**预期输出**:
```
mcp-shell                        RUNNING   pid 12, uptime 0:10:00
mcp-filesystem                   RUNNING   pid 13, uptime 0:10:00
mcp-chrome                       RUNNING   pid 14, uptime 0:10:00
mcp-manager                      RUNNING   pid 15, uptime 0:10:00  ⭐
```

### 2. Ollama 安装并运行

```bash
# macOS
brew install ollama
ollama serve

# 拉取模型（推荐 qwen2.5 或 llama3）
ollama pull qwen2.5:latest
# 或
ollama pull llama3:latest
```

### 3. Python 环境

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 环境配置

### 1. 创建 .env 文件

```bash
cd backend
cp .env.example .env
```

### 2. 编辑 .env

```bash
# LLM Configuration
LLM_PROVIDER=ollama  # 使用本地 Ollama
OLLAMA_MODEL=qwen2.5:latest  # 或 llama3:latest
OLLAMA_BASE_URL=http://localhost:11434

# MCP Configuration
SANDBOX_CONTAINER_NAME=sandbox-sandbox-os-1
MCP_SERVERS_DIR=/opt/mcp-servers

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## 启动后端

### 方式 1: 直接运行

```bash
cd backend
python main.py
```

### 方式 2: 使用 Uvicorn (推荐生产环境)

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**预期输出**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 测试 AI Agent

### 测试模式（自动化测试）

```bash
cd backend
python test_agent.py --mode test
```

**测试内容**:
1. ✅ 检查已安装的 MCP
2. ✅ 浏览 MCP 市场
3. ✅ AI 自主安装新工具（如 brave-search）
4. ✅ 文件操作测试
5. ✅ 进程监控测试

### 交互模式（聊天测试）

```bash
cd backend
python test_agent.py --mode interactive
```

**示例对话**:
```
👤 You: What tools do you have?

🤖 Agent: I have access to several tools:
- MCP Manager for installing new capabilities
- Shell commands for running Linux commands  
- File operations for reading/writing files
- Chrome browser automation
...

👤 You: I need you to search for "latest AI news"

🤖 Agent: I don't currently have web search capability, but I can install it!
Let me check the marketplace... [calls manager_list_available_mcps]
I found "Brave Search MCP" which provides web search. Installing it now...
[calls manager_install_mcp with mcp_id="brave-search"]
✅ Installed! Please restart the container:
   cd sandbox && docker-compose restart
After restart, I'll be able to search the web for you!
```

### 单次提示测试

```bash
cd backend
python test_agent.py --prompt "Show me what's in the MCP marketplace"
```

## API 端点

### 1. 聊天端点

**POST /api/chat**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "List all installed MCPs",
    "chat_history": []
  }'
```

**响应**:
```json
{
  "response": "Currently installed MCPs: filesystem, chrome, memory",
  "status": "success"
}
```

### 2. 健康检查

**GET /health**

```bash
curl http://localhost:8000/health
```

## AI 自主安装工具示例

### 场景 1: 用户需要搜索能力

```
用户: "帮我搜索最新的 AI 新闻"

AI 思考过程:
1. 我没有搜索能力
2. 调用 manager_list_available_mcps({"category": "搜索"})
3. 发现 brave-search MCP
4. 调用 manager_install_mcp({"mcp_id": "brave-search"})
5. 告诉用户重启容器

AI 响应:
"我已经安装了 Brave Search MCP！
请运行以下命令重启容器:
  cd sandbox && docker-compose restart
重启后我就可以为您搜索新闻了！"
```

### 场景 2: 用户需要记忆能力

```
用户: "记住我的生日是 5 月 10 日"

AI 思考过程:
1. 我没有持久化记忆能力
2. 调用 manager_list_available_mcps({"category": "工具"})
3. 发现 memory MCP
4. 调用 manager_install_mcp({"mcp_id": "memory"})

AI 响应:
"我已经安装了 Memory MCP 来存储长期记忆！
重启容器后，我就能记住您的重要信息了。"
```

## 可用的 MCP 工具

### MCP Manager (元服务器) ⭐

- `manager_list_available_mcps` - 浏览市场
- `manager_list_installed_mcps` - 查看已安装
- `manager_install_mcp` - 安装新工具
- `manager_get_mcp_status` - 检查状态

### Shell MCP

- `shell_execute_command` - 执行命令
- `shell_get_running_processes` - 查看进程

### Filesystem MCP

- `filesystem_read_file` - 读取文件
- `filesystem_write_file` - 写入文件
- `filesystem_list_directory` - 列出目录

### Chrome MCP

- `chrome_launch_browser` - 启动浏览器
- `chrome_navigate_to_url` - 打开网页
- `chrome_get_page_content` - 获取页面内容
- `chrome_take_screenshot` - 截图

## 故障排除

### 1. MCP 连接失败

**问题**: `Error connecting to MCP server`

**解决**:
```bash
# 检查容器运行
docker ps | grep sandbox

# 检查 MCP 服务状态
docker exec sandbox-sandbox-os-1 supervisorctl status

# 重启 MCP 服务
docker exec sandbox-sandbox-os-1 supervisorctl restart mcp-manager
```

### 2. Ollama 连接失败

**问题**: `Cannot connect to Ollama at http://localhost:11434`

**解决**:
```bash
# 检查 Ollama 运行
ps aux | grep ollama

# 启动 Ollama
ollama serve

# 测试连接
curl http://localhost:11434/api/tags
```

### 3. AI 安装工具后无法使用

**问题**: AI 安装了 brave-search，但重启后仍无法使用

**解决**:
```bash
# 1. 检查是否真的重启了
docker-compose restart

# 2. 验证新 MCP 服务运行
docker exec sandbox-sandbox-os-1 supervisorctl status mcp-brave-search

# 3. 如果不存在，手动添加到 supervisord.conf
# 参考 MCP_MANAGER_FOR_AI.md 中的配置
```

## 性能优化

### 1. 使用更快的模型

```bash
# Qwen2.5 (推荐，速度快)
ollama pull qwen2.5:latest

# Llama3 8B (平衡)
ollama pull llama3:latest

# Phi-3 (最快，但能力较弱)
ollama pull phi3:latest
```

### 2. 调整 Agent 参数

编辑 `agent.py`:
```python
self.agent_executor = AgentExecutor(
    agent=agent,
    tools=self.tools,
    verbose=True,
    max_iterations=10,  # 减少迭代次数以加快响应
    handle_parsing_errors=True,
)
```

### 3. 启用 MCP 连接池

编辑 `mcp_client.py` 添加连接复用（未来优化）。

## 下一步

1. **前端集成** - 在 Vue 前端添加聊天界面
2. **WebSocket 支持** - 实时流式响应
3. **多模型支持** - 同时使用 Ollama + DeepSeek
4. **MCP 市场 UI** - 可视化 MCP 安装界面

## 文档参考

- [MCP_MANAGER_FOR_AI.md](../MCP_MANAGER_FOR_AI.md) - MCP Manager 详细文档
- [MCP_SYSTEM_ARCHITECTURE.md](../MCP_SYSTEM_ARCHITECTURE.md) - 完整架构文档
- [backend/README.md](README.md) - 后端 API 文档

---

**更新日期**: 2026-01-21
**版本**: 1.0.0
