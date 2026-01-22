# Backend - Refactored Architecture

## 🎯 Overview

Manus Learn backend 已重构为 **LangChain 1.X + LangGraph** 最佳实践架构,采用模块化设计。

**版本**: 2.0.0
**核心技术**:
- **LangGraph**: ReAct agent with `create_react_agent`
- **MemorySaver**: Thread-based conversation memory
- **MCP Protocol**: Tool integration via stdio
- **FastAPI**: Async web framework

---

## 📁 Project Structure

```
backend/
├── app/                          # 主应用包
│   ├── __init__.py              # App 初始化
│   ├── main.py                  # FastAPI 应用工厂 (精简版)
│   │
│   ├── core/                    # 核心配置和基础设施
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic Settings (环境变量)
│   │   ├── llm.py              # LLM 初始化 (Ollama/DeepSeek)
│   │   └── logging.py          # 日志配置
│   │
│   ├── models/                  # Pydantic 数据模型
│   │   ├── __init__.py
│   │   ├── chat.py             # ChatMessage, ChatRequest, ChatResponse
│   │   └── sandbox.py          # SandboxStatus, ProcessList, etc.
│   │
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── agent.py            # SandboxAgent (LangGraph + MemorySaver)
│   │   ├── mcp_client.py       # MCPClientManager (docker exec)
│   │   └── chat_history.py     # ChatHistoryManager (兼容旧 API)
│   │
│   ├── api/                     # API 路由层
│   │   ├── __init__.py
│   │   ├── deps.py             # 依赖注入 (future auth)
│   │   ├── chat.py             # Chat endpoints (WebSocket + REST)
│   │   └── sandbox.py          # Sandbox monitoring endpoints
│   │
│   └── utils/                   # 工具函数
│       └── __init__.py
│
├── tests/                       # 测试文件
│   └── test_agent.py
│
├── .env                         # 环境变量配置
├── .env.example                 # 环境变量模板
├── requirements.txt             # Python 依赖
└── README.md                    # 本文档
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env to configure LLM provider
```

### 3. Start Server

```bash
# Development mode (auto-reload)
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔧 Key Architectural Changes

### 1. **LangGraph ReAct Agent** ([app/services/agent.py](app/services/agent.py))

使用 `create_react_agent` 替代旧的 `AgentExecutor`:

```python
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

self.checkpointer = MemorySaver()  # In-memory conversation state

self.agent = create_react_agent(
    self.llm,
    self.tools,
    prompt=prompt,
    checkpointer=self.checkpointer,  # Enable memory!
)
```

**新特性**:
- ✅ **Thread-based memory**: 每个对话有独立的 `thread_id`
- ✅ **Automatic checkpointing**: 对话状态自动持久化
- ✅ **Backward compatible**: 仍支持旧的 `chat_history` 参数

### 2. **Memory Management**

两种内存机制:

**A. LangGraph MemorySaver** (推荐)
```python
# Agent 自动管理,通过 thread_id 隔离对话
response = await sandbox_agent.run(
    user_input="Hello",
    thread_id="user-123"  # 同一 thread_id = 同一对话
)
```

**B. ChatHistoryManager** (向后兼容)
```python
# 传统方式,手动管理历史
from app.services import chat_history_manager

chat_history_manager.add_message(session_id, "user", "Hello")
history = chat_history_manager.get_messages(session_id)
```

### 3. **API Router Separation** ([app/api/](app/api/))

路由按功能分离:

- **[chat.py](app/api/chat.py)**: WebSocket + REST chat endpoints
- **[sandbox.py](app/api/sandbox.py)**: Sandbox monitoring endpoints
- **[deps.py](app/api/deps.py)**: Shared dependencies (future auth)

### 4. **Service Layer Pattern** ([app/services/](app/services/))

业务逻辑独立于 API:

- **[agent.py](app/services/agent.py)**: Agent 核心逻辑
- **[mcp_client.py](app/services/mcp_client.py)**: MCP 连接管理
- **[chat_history.py](app/services/chat_history.py)**: 对话历史管理

**优势**:
- 易于单元测试
- 可复用于 CLI、Jupyter、其他接口
- 符合 SOLID 原则

---

## 📡 API Endpoints

### Chat Endpoints

| Method | Path | Description |
|--------|------|-------------|
| WebSocket | `/chat/ws` | Real-time chat with agent |
| POST | `/chat/api` | REST chat endpoint |
| POST | `/chat/clear?session_id=xxx` | Clear chat history |
| GET | `/chat/sessions` | List active sessions |

### Sandbox Monitoring

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sandbox/status` | MCP server status |
| GET | `/api/sandbox/processes` | Running processes |
| GET | `/api/sandbox/resources` | CPU/Memory/Disk usage |
| GET | `/api/sandbox/logs` | Supervisor logs |
| GET | `/api/sandbox/marketplace` | Available MCPs |

### Health & Info

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service information |
| GET | `/health` | Health check |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_agent.py

# With coverage
pytest --cov=app tests/
```

---

## 📚 Migration Guide (from Old Structure)

### Import Changes

**Old**:
```python
from config import settings
from agent import sandbox_agent
from mcp_client import mcp_manager
```

**New**:
```python
from app.core import settings
from app.services import sandbox_agent, mcp_manager
```

### Running the App

**Old**:
```bash
python main.py
```

**New**:
```bash
python -m app.main
# or
uvicorn app.main:app --reload
```

### WebSocket Protocol

协议未变,但新增 `thread_id` 支持:

```json
// Client → Server
{
  "message": "List available tools",
  "thread_id": "optional-thread-id"  // 新增!
}

// Server → Client
{
  "type": "response",
  "content": "Here are the available tools...",
  "thread_id": "user-session-123"  // 返回使用的 thread_id
}
```

---

## 🔮 Future Enhancements

### Production Considerations

1. **PostgreSQL Checkpointer** (替代 MemorySaver):
   ```bash
   pip install langgraph-checkpoint-postgres
   ```
   ```python
   from langgraph.checkpoint.postgres import PostgresSaver
   checkpointer = PostgresSaver(connection_string="postgresql://...")
   ```

2. **Authentication** (使用 `app/api/deps.py`):
   ```python
   from app.api.deps import require_auth

   @router.post("/chat/api")
   async def chat(request: ChatRequest, user=Depends(require_auth)):
       # 认证后才能访问
   ```

3. **Rate Limiting**:
   ```bash
   pip install slowapi
   ```

4. **Observability**:
   - LangSmith for agent tracing
   - Prometheus metrics
   - Structured logging to ELK

---

## 📖 Related Documentation

- [LangGraph Memory Documentation](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [LangChain 1.X Migration Guide](https://python.langchain.com/docs/versions/migrating_chains/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

---

## 🙏 Acknowledgments

This refactoring follows best practices from:
- **LangChain 1.X** official documentation
- **LangGraph** checkpointing patterns (2025-2026)
- **FastAPI** project structure recommendations

**Sources**:
- [Memory - Docs by LangChain](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [Mastering LangGraph Checkpointing: Best Practices for 2025](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025)

---

**Built with ❤️ using LangChain 1.X + LangGraph**
