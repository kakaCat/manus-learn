# Manus Learn - AI-Powered Sandbox System

基于Docker的AI沙盒控制系统,允许AI Agent通过MCP(Model Context Protocol)安全地操作隔离环境。

## ✨ 特性

- 🐳 **Docker沙盒**: 完全隔离的执行环境
- 🖥️ **VNC可视化**: 通过noVNC实时查看沙盒桌面
- 🔧 **21个MCP工具**: Shell命令、文件操作、浏览器控制
- 🤖 **LangChain Agent**: AI驱动的自动化任务执行
- 💬 **WebSocket API**: 实时聊天接口
- 🔒 **安全框架**: 多层防护(路径验证、命令白名单、资源限制)
- 🌐 **浏览器自动化**: 支持Chrome DevTools Protocol

## 🚀 快速开始

详细步骤请参考: [QUICKSTART.md](./QUICKSTART.md)

### 1分钟启动

```bash
# 方法1: 使用快速启动脚本 (推荐)
./scripts/quick_start.sh

# 方法2: 手动启动
# 启动沙盒容器
cd sandbox && docker-compose up -d

# 安装后端依赖
cd ../backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 安装并启动Ollama
brew install ollama
ollama serve
ollama pull qwen2.5:3b  # 或 deepseek-r1:1.5b

# 配置并启动后端
cp .env.example .env
python -m app.main

# 启动前端
cd ../frontend
npm install
npm run dev
```

**访问地址**:
- VNC前端: http://localhost:5173
- 后端API: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/chat/ws

## 📁 项目结构

```
manus-learn/
├── backend/             # LangChain + FastAPI 后端
│   ├── app/
│   │   ├── api/        # API路由 (chat, sandbox)
│   │   ├── core/       # 核心配置 (config, llm, logging)
│   │   ├── models/     # Pydantic模型
│   │   ├── services/   # 业务逻辑 (agent, mcp_client)
│   │   └── main.py     # FastAPI应用入口
│   ├── tests/          # 测试文件
│   └── requirements.txt
│
├── frontend/           # Vue 3 + noVNC 前端
│   ├── src/
│   │   ├── components/ # UI组件 (Chat, Monitor, VNC)
│   │   └── App.vue
│   └── package.json
│
├── sandbox/            # Docker沙盒环境
│   ├── docker/         # Dockerfile + supervisord
│   ├── mcp-servers/    # MCP服务器代码
│   │   ├── shell_mcp/  # Shell工具 (4个)
│   │   ├── mcp_manager/# Meta-MCP管理器
│   │   └── common/     # 公共模块
│   ├── shared/         # workspace卷挂载
│   └── docker-compose.yml
│
├── scripts/            # 启动和部署脚本
│   ├── quick_start.sh
│   └── start-docker.sh
│
├── docs/               # 项目文档
│   └── blog/          # 博客文章
│
├── .gitignore
├── CLAUDE.md          # Claude Code 指引
└── README.md          # 本文件
```

## 🏗️ 系统架构

```
┌─────────────┐
│ 用户浏览器   │
└──────┬──────┘
       │
       ├─→ http://localhost:5173 (VNC前端)
       │   └─→ 查看沙盒桌面
       │
       └─→ ws://localhost:8000/ws/chat (后端WebSocket)
           └─→ AI聊天接口
                  │
                  ↓
           ┌──────────────┐
           │ LangChain     │
           │ Agent         │
           └──────┬───────┘
                  │ MCP Protocol
                  ↓
           ┌──────────────────────┐
           │ Docker Container      │
           │ ├─ Shell MCP (4工具)  │
           │ ├─ Filesystem (8工具) │
           │ └─ Chrome (9工具)     │
           └──────────────────────┘
```

## 🔧 可用工具

### Shell工具 (4个)
- 执行命令、运行脚本
- 查看进程、终止进程

### 文件系统工具 (8个)
- 读写文件、列出目录
- 搜索文件、移动/删除
- 获取文件信息

### 浏览器工具 (9个)
- 启动Chrome、导航URL
- 点击元素、输入文本
- 截图、执行JavaScript

完整工具列表: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md#已完成功能)

## 💡 使用示例

### Python API

```python
import asyncio
from app.services import sandbox_agent

async def main():
    await sandbox_agent.initialize()

    # 让AI帮你操作沙盒
    response = await sandbox_agent.run(
        user_input="创建一个Python脚本,爬取example.com的标题",
        thread_id="user-123"  # 线程ID用于保持会话上下文
    )

    print(response)

asyncio.run(main())
```

### WebSocket聊天

```javascript
const ws = new WebSocket('ws://localhost:8000/chat/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: "列出所有Python文件并统计行数",
    thread_id: "user-123"  // 保持会话上下文
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content);
};
```

## 📚 文档

- [Claude Code 指引](./CLAUDE.md) - AI开发助手配置
- [后端文档](./backend/README.md) - API和配置详情
- [前端文档](./frontend/FRONTEND_GUIDE.md) - Vue组件说明
- [博客文章](./docs/blog/) - 技术分享和架构设计

## 🛠️ 技术栈

**沙盒环境**:
- Docker + Ubuntu 22.04
- Python 3.11 + Node.js 20
- Chromium + Chrome DevTools Protocol
- X11vnc + noVNC

**MCP服务器**:
- MCP SDK 1.25.0
- Supervisord管理
- stdio传输协议

**后端**:
- FastAPI + WebSocket
- LangChain 1.X + LangGraph
- MemorySaver (线程化会话)
- Ollama/DeepSeek LLM

**前端**:
- Vue 3 + Vite
- Tailwind CSS
- noVNC WebSocket客户端

## 🔒 安全特性

- ✅ Docker容器隔离
- ✅ 路径遍历防护(限制在workspace)
- ✅ 命令白名单/黑名单
- ✅ URL黑名单(禁止localhost/私有IP)
- ✅ 资源限制(文件大小、超时、进程数)
- ✅ 完整审计日志

## 📊 项目状态

✅ **已完成**:
- MCP工具服务器(21个工具)
- LangChain后端集成
- Ollama/DeepSeek LLM支持
- WebSocket聊天API
- VNC可视化界面

⏳ **进行中**:
- Vue前端Chat窗口集成

🔮 **计划中**:
- 流式响应
- 多用户会话
- 工具权限审批
- 聊天历史持久化

## 🐛 故障排除

常见问题和解决方案: [QUICKSTART.md#故障排除](./QUICKSTART.md#故障排除)

## 📝 更新日志

### 2026-01-21
- ✅ 完成3个MCP服务器实现(21个工具)
- ✅ 完成LangChain后端集成
- ✅ 完成WebSocket聊天API
- ✅ 添加Ollama/DeepSeek LLM支持
- ✅ 完善安全框架和文档

### 2026-01-20
- ✅ Docker沙盒环境搭建
- ✅ VNC可视化完成
- ✅ Vue前端noVNC集成

## 🤝 贡献

欢迎提交Issue和Pull Request!

## 📄 许可证

MIT License

## 👥 作者

Manus Learn Team

---

**开始使用**: [QUICKSTART.md](./QUICKSTART.md)
**完整文档**: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)
