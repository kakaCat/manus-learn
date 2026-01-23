# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Manus Learn** is an AI-powered Docker sandbox control system that enables AI agents to safely operate in an isolated environment via MCP (Model Context Protocol). The system uses **LangChain 1.X + LangGraph** agents to execute commands, manipulate files, and control browsers inside a sandboxed container with VNC visualization.

**Version**: 2.0.0 (Refactored with LangGraph + MemorySaver)

## Architecture

The system consists of three main components:

### 1. Docker Sandbox Container (`sandbox/`)
- Ubuntu 22.04 container with X11vnc + Xvfb for headless display
- Runs **3 MCP servers** (all official packages) managed by supervisord:
  - `mcp-shell`: Command execution (@kevinwatt/shell-mcp, secure whitelisted commands)
  - `mcp-filesystem`: File operations (@modelcontextprotocol/server-filesystem, 8 tools)
  - `mcp-chrome`: Browser automation (chrome-devtools-mcp, 9 tools)
- Workspace directory: `/root/shared/workspace/` (mounted volume)
- VNC accessible on ports 5900 (VNC) and 6080 (noVNC WebSocket)

### 2. Backend Server (`backend/app/`)
**New modular architecture (v2.0.0)**:
```
backend/app/
├── core/          # Configuration (config.py, llm.py, logging.py)
├── models/        # Pydantic models (chat.py, sandbox.py)
├── services/      # Business logic (agent.py, mcp_client.py)
├── api/           # API routes (chat.py, sandbox.py)
└── main.py        # FastAPI application factory
```

**Key Technologies**:
- **LangGraph**: ReAct agent with `create_react_agent` (NOT AgentExecutor)
- **MemorySaver**: Thread-based conversation memory
- **FastAPI**: Async web framework with WebSocket support
- **MCP Protocol**: Tool integration via docker exec + stdio

**LLM Requirements**:
- Model MUST support tool calling
- ✅ Recommended: `qwen2.5:3b`, `qwen2.5:7b`, `llama3.1:8b`
- ❌ NOT compatible: `deepseek-r1:1.5b` (no tool support)

### 3. Frontend UI (`frontend/`)
- Vue 3 + Vite + Tailwind CSS application
- noVNC viewer for real-time sandbox visualization
- Chat interface for AI agent interaction
- Monitoring dashboard for sandbox status

### Communication Flow
```
User Browser (localhost:5173)
    ↓ WebSocket
Backend FastAPI (localhost:8000)
    ↓ LangGraph Agent (with MemorySaver)
    ↓ MCP Tools (StructuredTool wrappers)
    ↓ MCP Protocol (stdio)
Docker exec → MCP Servers → Sandbox Environment
```

## Development Commands

### Starting the Full System

**Prerequisites:**
```bash
# 1. Install and start Ollama (required for local LLM)
brew install ollama
ollama serve  # Keep running in background

# 2. Pull a tool-compatible model
ollama pull qwen2.5:3b  # Recommended: 1.9GB, supports tools
```

**Start all services:**
```bash
# Terminal 1: Start Docker sandbox
cd sandbox
docker-compose up -d

# Terminal 2: Start backend (NEW WAY)
cd backend
python3 -m venv venv  # First time only
source venv/bin/activate
pip install -r requirements.txt  # First time only
python -m app.main  # NEW: module execution
# OR: uvicorn app.main:app --reload

# Terminal 3: Start frontend
cd frontend
npm install  # First time only
npm run dev  # http://localhost:5173
```

### Backend Development (New Structure)

```bash
cd backend

# Start server (NEW)
python -m app.main

# Test imports (NEW)
python -c "from app.services import sandbox_agent; print('Agent imported')"

# Test MCP connection
python -c "
import asyncio
from app.services import mcp_manager

async def test():
    tools = await mcp_manager.list_tools('shell')
    print(f'Found {len(tools)} shell tools')

asyncio.run(test())
"

# Test agent directly
python -c "
import asyncio
from app.services import sandbox_agent

async def test():
    await sandbox_agent.initialize()
    response = await sandbox_agent.run('List available tools', thread_id='test-123')
    print(response)

asyncio.run(test())
"
```

### Docker/MCP Development

```bash
cd sandbox

# Rebuild after changes
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check MCP server status
docker exec sandbox-sandbox-os-1 ps aux | grep mcp

# View MCP server logs
docker exec sandbox-sandbox-os-1 tail -f /var/log/mcp/shell-stderr.log
docker exec sandbox-sandbox-os-1 tail -f /var/log/mcp/filesystem-stderr.log

# Test MCP servers directly
docker exec -i sandbox-sandbox-os-1 /opt/mcp-venv/bin/python /opt/mcp-servers/shell_mcp/server.py
```

## Critical Architecture Decisions

### 1. LangGraph with MemorySaver (NEW v2.0.0)

**Old way (deprecated)**:
```python
from langchain.agents import AgentExecutor  # ❌ Don't use
```

**New way**:
```python
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()  # In-memory conversation state

agent = create_react_agent(
    llm,
    tools,
    prompt=prompt,
    checkpointer=checkpointer,  # ✅ Enable memory
)
```

**Benefits**:
- Thread-based conversation isolation
- Automatic state checkpointing
- No manual history management needed

### 2. Thread-based Memory Management

**Usage**:
```python
# Each thread_id = independent conversation
response = await sandbox_agent.run(
    user_input="Hello",
    thread_id="user-123"  # Same thread = same conversation
)
```

**Production**: Replace `MemorySaver` with `PostgresSaver`:
```bash
pip install langgraph-checkpoint-postgres
```

### 3. New Import Paths

| Old (v1.x) | New (v2.0.0) |
|------------|--------------|
| `from config import settings` | `from app.core import settings` |
| `from agent import sandbox_agent` | `from app.services import sandbox_agent` |
| `from mcp_client import mcp_manager` | `from app.services import mcp_manager` |
| `python main.py` | `python -m app.main` |

### 4. MCP Tool Integration

MCP tools are wrapped as `StructuredTool`:
```python
# app/services/agent.py
from langchain_core.tools import StructuredTool
from pydantic import create_model, Field

tool = StructuredTool.from_function(
    coroutine=wrapper.execute,  # async def execute(**kwargs)
    name="shell_execute_command",
    description="Execute a shell command",
    args_schema=ArgsModel,  # Pydantic model
)
```

### 5. API Router Structure

Routers are separated by domain:
```python
# app/main.py
from app.api import chat, sandbox

app.include_router(chat.router)  # /chat/ws, /chat/api
app.include_router(sandbox.router, prefix="/api")  # /api/sandbox/*
```

## Configuration

### Backend Configuration (`backend/app/core/config.py`)

Settings use Pydantic BaseSettings:
```python
from app.core import settings

settings.llm_provider  # "ollama" or "deepseek"
settings.ollama_model  # "qwen2.5:3b"
settings.backend_port  # 8000
```

Environment variables (`.env`):
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:3b
SANDBOX_CONTAINER_NAME=sandbox-sandbox-os-1
BACKEND_PORT=8000
LOG_LEVEL=INFO
```

### MCP Server Locations

**Python servers** (`/opt/mcp-servers/` inside container):
- `shell_mcp/server.py` - Custom shell execution
- `mcp_manager/server.py` - Meta-MCP manager

**Node.js servers** (globally installed):
- `@modelcontextprotocol/server-filesystem` - Official filesystem MCP
- `chrome-devtools-mcp` - Official Chrome DevTools MCP

## Common Issues

### Backend won't start
1. Check imports use new paths: `from app.core import ...`
2. Run with: `python -m app.main` (not `python main.py`)
3. Verify Ollama: `curl http://localhost:11434`
4. Check model supports tools: `ollama list`

### Import errors
```bash
# ❌ Wrong
from config import settings

# ✅ Correct
from app.core import settings
```

### MCP tools not working
1. Check servers running: `docker exec sandbox-sandbox-os-1 ps aux | grep mcp`
2. View logs: `docker exec sandbox-sandbox-os-1 tail /var/log/mcp/*-stderr.log`
3. Restart container: `cd sandbox && docker-compose restart`

### Memory not persisting
- Check `thread_id` is consistent across requests
- MemorySaver only persists in-memory (use PostgresSaver for production)

## Testing

```bash
cd backend

# Run all tests
pytest

# Test specific module
pytest tests/test_agent.py

# Test with coverage
pytest --cov=app tests/
```

## File Structure Context

### Backend Key Files (NEW v2.0.0)

**Core Configuration**:
- `app/core/config.py` - Pydantic Settings with env vars
- `app/core/llm.py` - LLM initialization (Ollama/DeepSeek)
- `app/core/logging.py` - Logging setup

**Data Models**:
- `app/models/chat.py` - ChatMessage, ChatRequest, ChatResponse
- `app/models/sandbox.py` - SandboxStatus, ProcessList, etc.

**Business Logic**:
- `app/services/agent.py` - SandboxAgent (LangGraph + MemorySaver)
- `app/services/mcp_client.py` - MCPClientManager (docker exec)
- `app/services/chat_history.py` - ChatHistoryManager (backward compat)

**API Routes**:
- `app/api/chat.py` - Chat endpoints (WebSocket + REST)
- `app/api/sandbox.py` - Sandbox monitoring endpoints
- `app/api/deps.py` - Dependency injection

**Application**:
- `app/main.py` - FastAPI app factory (120 lines, clean!)

### MCP Server Structure
```
sandbox/mcp-servers/
├── common/
│   ├── security.py       # Security validation
│   └── logging_config.py # Stderr logging
├── shell_mcp/
│   └── server.py         # Shell MCP server
└── mcp_manager/
    └── server.py         # Meta-MCP manager
```

## Important Notes

1. **Use LangGraph, NOT AgentExecutor** - AgentExecutor is deprecated
2. **Thread IDs for memory** - Each conversation needs a unique `thread_id`
3. **MCP stderr logging** - stdout reserved for MCP protocol
4. **Tool calling required** - Model must support function calling
5. **Module execution** - Use `python -m app.main` not `python main.py`

## Migration from v1.x to v2.0.0

See [backend/README.md](backend/README.md) for detailed migration guide.

**Quick summary**:
- Update all imports: `from app.core/models/services/api import ...`
- Use `thread_id` instead of manual `chat_history`
- Run with `python -m app.main`
- Agent now has automatic memory via MemorySaver

## Resources

- [LangGraph Memory Documentation](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [LangChain 1.X API Reference](https://python.langchain.com/docs/versions/migrating_chains/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Backend README](backend/README.md) - Full refactoring documentation
