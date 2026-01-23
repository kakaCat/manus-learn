# Manus Learn - 项目结构文档

## 📁 完整目录树

```
manus-learn/
├── backend/                     # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI 应用入口
│   │   ├── api/                # API 路由层
│   │   │   ├── __init__.py
│   │   │   ├── chat.py         # 聊天接口 (WebSocket + REST)
│   │   │   ├── sandbox.py      # 沙盒监控接口
│   │   │   └── deps.py         # 依赖注入
│   │   ├── core/               # 核心配置
│   │   │   ├── __init__.py
│   │   │   ├── config.py       # Pydantic Settings
│   │   │   ├── llm.py          # LLM 初始化
│   │   │   └── logging.py      # 日志配置
│   │   ├── models/             # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── chat.py         # 聊天消息模型
│   │   │   └── sandbox.py      # 沙盒状态模型
│   │   ├── services/           # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        # LangGraph Agent
│   │   │   ├── mcp_client.py   # MCP 客户端管理
│   │   │   └── chat_history.py # 聊天历史管理
│   │   └── utils/              # 工具函数
│   │       └── __init__.py
│   ├── tests/                  # 测试文件
│   ├── .env.example            # 环境变量模板
│   ├── requirements.txt        # Python 依赖
│   └── README.md               # 后端文档
│
├── frontend/                    # 前端应用
│   ├── src/
│   │   ├── App.vue             # 主应用组件
│   │   ├── main.js             # 入口文件
│   │   ├── style.css           # 全局样式
│   │   └── components/         # UI 组件
│   │       ├── ChatPanel.vue   # 聊天面板
│   │       ├── SandboxMonitor.vue  # 沙盒监控
│   │       └── AuxiliaryPanel.vue  # 辅助面板
│   ├── public/                 # 静态资源
│   ├── index.html              # HTML 模板
│   ├── package.json            # NPM 依赖
│   ├── vite.config.js          # Vite 配置
│   ├── tailwind.config.js      # Tailwind 配置
│   └── FRONTEND_GUIDE.md       # 前端文档
│
├── sandbox/                     # Docker 沙盒环境
│   ├── docker/
│   │   ├── Dockerfile          # 沙盒容器镜像
│   │   └── supervisord.conf    # 进程管理配置
│   ├── mcp-servers/            # MCP 服务器代码
│   │   ├── __init__.py
│   │   ├── installed.json      # 已安装的 MCP 服务
│   │   ├── common/             # 公共模块
│   │   │   ├── __init__.py
│   │   │   ├── security.py     # 安全验证
│   │   │   ├── logging_config.py  # 日志配置
│   │   │   └── types.py        # 类型定义
│   │   ├── shell_mcp/          # Shell 执行 MCP
│   │   │   ├── __init__.py
│   │   │   ├── server.py       # MCP 服务器主程序
│   │   │   ├── config.py       # 配置
│   │   │   └── tools.py        # Shell 工具实现
│   │   └── mcp_manager/        # Meta-MCP 管理器
│   │       ├── __init__.py
│   │       └── server.py       # 管理器主程序
│   ├── shared/                 # 挂载卷 (工作空间)
│   │   └── workspace/          # AI 工作目录
│   ├── docker-compose.yml      # Docker Compose 配置
│   ├── test_mcp_servers.py     # MCP 测试脚本
│   └── README.md               # 沙盒文档
│
├── scripts/                     # 启动和部署脚本
│   ├── quick_start.sh          # 快速启动脚本
│   └── start-docker.sh         # Docker 启动脚本
│
├── docs/                        # 项目文档
│   ├── blog/                   # 博客文章
│   │   ├── 001-ai-manus-overview.md
│   │   ├── 002-sandbox-vnc-overview.md
│   │   └── images/
│   ├── Dockerfile.dev          # 旧版 Dockerfile (存档)
│   └── PROJECT_STRUCTURE.md    # 本文件
│
├── .gitignore                  # Git 忽略规则
├── CLAUDE.md                   # Claude Code 开发指引
└── README.md                   # 项目主文档
```

---

## 🎯 各目录职责

### Backend (`backend/`)

**核心功能**: FastAPI Web 服务 + LangGraph AI Agent

**主要组件**:
- `app/main.py`: FastAPI 应用工厂,定义路由和中间件
- `app/api/`: REST 和 WebSocket API 端点
- `app/services/agent.py`: LangGraph ReAct Agent,使用 MemorySaver 管理会话
- `app/services/mcp_client.py`: 通过 `docker exec` 与 MCP 服务器通信
- `app/core/config.py`: 环境变量配置 (Pydantic BaseSettings)

**技术栈**:
- FastAPI (异步 Web 框架)
- LangChain 1.X + LangGraph (AI Agent)
- Pydantic (数据验证)
- Uvicorn (ASGI 服务器)

**运行方式**:
```bash
cd backend
python -m app.main
# 或
uvicorn app.main:app --reload
```

---

### Frontend (`frontend/`)

**核心功能**: Vue 3 单页应用,提供 noVNC 可视化和 AI 聊天界面

**主要组件**:
- `App.vue`: 主应用布局 (3栏: VNC + Chat + Monitor)
- `components/ChatPanel.vue`: WebSocket 聊天界面
- `components/SandboxMonitor.vue`: 沙盒状态监控
- `components/AuxiliaryPanel.vue`: noVNC 集成

**技术栈**:
- Vue 3 (Composition API)
- Vite (构建工具)
- Tailwind CSS (样式)
- noVNC (WebSocket VNC 客户端)

**运行方式**:
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

---

### Sandbox (`sandbox/`)

**核心功能**: Docker 隔离环境 + MCP 工具服务器

**容器特性**:
- Ubuntu 22.04 基础镜像
- X11vnc + Xvfb (无头桌面)
- Chromium 浏览器
- Python 3.11 + Node.js 20
- Supervisord 管理 MCP 进程

**MCP 服务器** (运行在容器内):
1. **shell_mcp** (Python, 4 tools)
   - 执行 Shell 命令
   - 查看/终止进程

2. **filesystem** (Node.js 官方, 8 tools)
   - 文件读写、目录操作
   - 文件搜索、移动/删除

3. **chrome-devtools-mcp** (Node.js 官方, 9 tools)
   - 启动 Chromium
   - 页面导航、元素交互
   - 截图、JavaScript 执行

4. **mcp_manager** (Python 自定义)
   - 列出所有 MCP 服务器
   - 查看工具状态

**运行方式**:
```bash
cd sandbox
docker-compose up -d
```

**进入容器**:
```bash
docker exec -it sandbox-sandbox-os-1 bash
```

---

### Scripts (`scripts/`)

**启动脚本**:
- `quick_start.sh`: 一键启动全系统 (Docker + Backend + Ollama 检查)
- `start-docker.sh`: 仅启动 Docker 沙盒

**使用示例**:
```bash
# 快速启动 (推荐)
./scripts/quick_start.sh

# 仅启动沙盒
./scripts/start-docker.sh
```

---

### Docs (`docs/`)

**文档集合**:
- `blog/`: 技术博客文章
  - `001-ai-manus-overview.md`: AI Manus 系统概述
  - `002-sandbox-vnc-overview.md`: 沙盒和 VNC 架构
- `Dockerfile.dev`: 早期开发版 Dockerfile (已废弃)

---

## 🔄 数据流

### 用户交互流程

```
┌─────────────────────────────────────────────────────┐
│ 1. 用户在浏览器打开 http://localhost:5173           │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ 2. Frontend (Vue) 渲染 3 个面板:                     │
│    - noVNC 连接到 ws://localhost:6080               │
│    - ChatPanel 连接到 ws://localhost:8000/chat/ws   │
│    - SandboxMonitor 轮询 /api/sandbox/status        │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ 3. 用户发送消息 "创建 Python 脚本"                   │
└───────────────────┬─────────────────────────────────┘
                    │ WebSocket
                    ▼
┌─────────────────────────────────────────────────────┐
│ 4. Backend FastAPI 接收消息                          │
│    → app/api/chat.py::websocket_endpoint()          │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ 5. 调用 LangGraph Agent                              │
│    → app/services/agent.py::SandboxAgent.run()     │
│    → Agent 分析任务并规划工具调用                    │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ 6. Agent 调用 MCP 工具                               │
│    → app/services/mcp_client.py::call_tool()       │
│    → docker exec sandbox-sandbox-os-1 python ...    │
└───────────────────┬─────────────────────────────────┘
                    │ stdio (JSON-RPC)
                    ▼
┌─────────────────────────────────────────────────────┐
│ 7. MCP Server 执行工具 (在容器内)                     │
│    → sandbox/mcp-servers/shell_mcp/server.py        │
│    → 执行命令: echo 'print("Hello")' > script.py     │
└───────────────────┬─────────────────────────────────┘
                    │ 返回结果
                    ▼
┌─────────────────────────────────────────────────────┐
│ 8. Agent 收到结果,生成最终回复                        │
│    → 通过 WebSocket 发送回前端                        │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ 9. 用户在 ChatPanel 看到:                            │
│    "✅ 已创建 Python 脚本 script.py"                 │
│    同时在 noVNC 中看到文件出现在桌面                  │
└─────────────────────────────────────────────────────┘
```

---

## 📦 依赖关系

### Backend 依赖 (`requirements.txt`)

**核心依赖**:
- `fastapi` - Web 框架
- `uvicorn[standard]` - ASGI 服务器
- `langchain` / `langchain-core` - AI 框架
- `langgraph` - Agent 编排
- `langchain-ollama` / `langchain-openai` - LLM 集成
- `mcp` - MCP 协议库
- `pydantic` / `pydantic-settings` - 配置管理

**开发工具**:
- `pytest` - 测试框架
- `ruff` - Linter + Formatter

### Frontend 依赖 (`package.json`)

**核心依赖**:
- `vue@^3.5.13` - Vue 框架
- `@novnc/novnc@^1.5.0` - VNC 客户端

**开发工具**:
- `vite@^5.4.11` - 构建工具
- `tailwindcss@^3.4.17` - CSS 框架
- `@vitejs/plugin-vue` - Vue 插件

### Sandbox 依赖 (Docker 镜像)

**系统包** (Ubuntu 22.04):
- `python3.11`
- `nodejs` / `npm`
- `chromium-browser`
- `x11vnc` / `xvfb`
- `novnc`
- `supervisor`

**MCP 服务器**:
- Python: `mcp` SDK
- Node.js: `@modelcontextprotocol/server-filesystem`, `chrome-devtools-mcp`

---

## 🚀 快速开发指南

### 添加新的 API 端点

1. 在 `backend/app/api/` 创建新路由文件
2. 定义 Pydantic 模型 (在 `app/models/`)
3. 在 `app/main.py` 注册路由

```python
# backend/app/api/new_feature.py
from fastapi import APIRouter
from app.models.new_feature import FeatureRequest, FeatureResponse

router = APIRouter()

@router.post("/feature", response_model=FeatureResponse)
async def create_feature(request: FeatureRequest):
    # 业务逻辑
    return FeatureResponse(...)

# backend/app/main.py
from app.api import new_feature
app.include_router(new_feature.router, prefix="/api", tags=["feature"])
```

### 添加新的前端组件

1. 在 `frontend/src/components/` 创建 `.vue` 文件
2. 在 `App.vue` 中引入并使用

```vue
<!-- frontend/src/components/NewPanel.vue -->
<script setup>
// 组件逻辑
</script>

<template>
  <div class="new-panel">
    <!-- UI -->
  </div>
</template>

<style scoped>
/* 样式 */
</style>
```

### 添加新的 MCP 工具

1. 在沙盒容器内安装 MCP 服务器 (Node.js 或 Python)
2. 更新 `supervisord.conf` 添加进程管理
3. 重新构建 Docker 镜像

```bash
# 安装 Node.js MCP 服务器
cd sandbox/docker
# 在 Dockerfile 中添加:
# RUN npm install -g @myorg/new-mcp-server

# 更新 supervisord.conf
[program:new_mcp]
command=/usr/bin/new-mcp-server
stdout_logfile=/var/log/mcp/new-stdout.log
stderr_logfile=/var/log/mcp/new-stderr.log
```

---

## 🔧 配置文件说明

### Backend 配置 (`.env`)

```bash
# LLM 提供商
LLM_PROVIDER=deepseek  # 或 ollama

# DeepSeek API
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Ollama (本地)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

# 沙盒容器
SANDBOX_CONTAINER_NAME=sandbox-sandbox-os-1

# 后端服务
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173

# 日志
LOG_LEVEL=INFO
```

### Frontend 配置 (`.env`)

```bash
# API 端点
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/chat/ws

# VNC 配置
VITE_VNC_URL=ws://localhost:6080
```

### Docker Compose (`sandbox/docker-compose.yml`)

```yaml
services:
  sandbox-os:
    build: ./docker
    ports:
      - "5900:5900"  # VNC
      - "6080:6080"  # noVNC
    volumes:
      - ./shared:/root/shared
      - ./mcp-servers:/opt/mcp-servers
    environment:
      - DISPLAY=:99
```

---

## 📝 开发规范

### 代码风格

**Python** (Backend + MCP Servers):
- 使用 `ruff` 进行 linting 和 formatting
- 遵循 PEP 8
- 类型提示: 使用 `typing` 模块

**JavaScript/Vue** (Frontend):
- 使用 ESLint + Prettier
- Composition API (Vue 3)
- Tailwind CSS 实用类优先

### Git 提交规范

```bash
# 功能: feat(scope): description
git commit -m "feat(backend): add new MCP tool wrapper"

# 修复: fix(scope): description
git commit -m "fix(frontend): resolve WebSocket reconnection issue"

# 文档: docs(scope): description
git commit -m "docs(readme): update project structure"

# 重构: refactor(scope): description
git commit -m "refactor(agent): simplify tool calling logic"
```

---

## 🐛 故障排除

### Backend 启动失败

**问题**: `ModuleNotFoundError: No module named 'app'`

**解决**:
```bash
# 确保在 backend/ 目录下
cd backend
# 使用模块方式运行
python -m app.main
```

### MCP 工具不可用

**问题**: Agent 报告 "Tool not found"

**解决**:
```bash
# 检查 MCP 服务器状态
docker exec sandbox-sandbox-os-1 supervisorctl status

# 重启 MCP 服务
docker exec sandbox-sandbox-os-1 supervisorctl restart mcp-shell
```

### Frontend 无法连接 WebSocket

**问题**: ChatPanel 显示 "Connection failed"

**解决**:
```bash
# 检查后端是否运行
curl http://localhost:8000/docs

# 检查 CORS 配置
# backend/.env 中确保:
CORS_ORIGINS=http://localhost:5173
```

---

## 📚 相关文档

- [CLAUDE.md](../CLAUDE.md) - Claude Code 开发指引
- [README.md](../README.md) - 项目主文档
- [backend/README.md](../backend/README.md) - 后端详细文档
- [frontend/FRONTEND_GUIDE.md](../frontend/FRONTEND_GUIDE.md) - 前端开发指南
