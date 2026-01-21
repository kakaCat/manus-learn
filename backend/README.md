# Sandbox AI Backend

LangChain + MCP backend for AI-powered sandbox control.

## Architecture

```
┌─────────────────────────────────────────────┐
│ Frontend (Vue + noVNC + Chat)               │
│   - Port 5173                               │
│   - WebSocket client                        │
└─────────────────┬───────────────────────────┘
                  │ WebSocket
                  ↓
┌─────────────────────────────────────────────┐
│ Backend (FastAPI + LangChain)               │
│   - Port 8000                               │
│   - LangChain Agent                         │
│   - Ollama/DeepSeek LLM                    │
└─────────────────┬───────────────────────────┘
                  │ MCP Protocol (stdio)
                  ↓
┌─────────────────────────────────────────────┐
│ Docker Container (sandbox-os)               │
│   - Shell MCP Server (4 tools)             │
│   - Filesystem MCP Server (8 tools)        │
│   - Chrome MCP Server (9 tools)            │
│   - VNC Display at :1                       │
└─────────────────────────────────────────────┘
```

## Features

- **LangChain Agent**: AI agent with MCP tool access
- **21 MCP Tools**: Shell commands, file operations, browser control
- **WebSocket API**: Real-time chat with the AI
- **Ollama Support**: Local LLM (no API keys required)
- **DeepSeek Support**: Cloud LLM option

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Ollama (Recommended)

```bash
# macOS
brew install ollama

# Start Ollama service
ollama serve

# Pull a model (choose one)
ollama pull deepseek-r1:1.5b  # Fastest, 1.5B params
ollama pull qwen2.5:7b         # Balanced, 7B params
ollama pull llama3.1:8b        # High quality, 8B params
```

### 3. Configure Environment

```bash
cp .env.example .env

# Edit .env
# Set OLLAMA_MODEL to the model you pulled
```

### 4. Start Backend Server

```bash
python main.py
```

Server will start at: http://localhost:8000

## Configuration

### Environment Variables

See [.env.example](.env.example) for all available options.

**Key Settings:**

- `LLM_PROVIDER`: `ollama` or `deepseek`
- `OLLAMA_MODEL`: Model name (e.g., `deepseek-r1:1.5b`)
- `SANDBOX_CONTAINER_NAME`: Docker container name
- `BACKEND_PORT`: API server port (default: 8000)

### Choosing an LLM

**Ollama (Recommended for Development):**
- ✅ Free and local
- ✅ No API keys needed
- ✅ Fast on M1/M2/M3 Macs
- ⚠️ Requires ~4GB RAM minimum

**DeepSeek (Cloud Option):**
- ✅ More powerful models
- ✅ No local resources needed
- ⚠️ Requires API key
- ⚠️ Costs money per request

## API Endpoints

### HTTP Endpoints

- `GET /` - Server info
- `GET /health` - Health check
- `POST /chat/clear` - Clear chat history

### WebSocket

- `ws://localhost:8000/ws/chat` - Chat with AI

**Message Format:**

Client → Server:
```json
{
  "message": "List files in the workspace"
}
```

Server → Client:
```json
{
  "type": "response",  // or "error", "thinking"
  "content": "Here are the files..."
}
```

## Available MCP Tools

The agent has access to 21 tools across 3 MCP servers:

### Shell Tools (4)
- `execute_command` - Run shell commands
- `execute_shell_script` - Run bash scripts
- `get_running_processes` - List processes
- `kill_process` - Terminate processes

### Filesystem Tools (8)
- `read_file` - Read file contents
- `write_file` - Write to files
- `list_directory` - List directory contents
- `search_files` - Search with glob patterns
- `create_directory` - Create directories
- `delete_file` - Delete files/directories
- `move_file` - Move/rename files
- `get_file_info` - Get file metadata

### Chrome Tools (9)
- `launch_browser` - Start Chrome browser
- `close_browser` - Close browser
- `navigate_to_url` - Navigate to URL
- `get_page_content` - Get page HTML/text
- `click_element` - Click elements by selector
- `type_text` - Type into input fields
- `wait_for_element` - Wait for element to appear
- `take_screenshot` - Capture screenshots
- `execute_javascript` - Run JavaScript

## Example Usage

### Via Python

```python
import asyncio
from agent import sandbox_agent

async def main():
    # Initialize agent
    await sandbox_agent.initialize()

    # Run command
    response = await sandbox_agent.run(
        "List all Python files in the workspace"
    )

    print(response)

asyncio.run(main())
```

### Via WebSocket (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: "Create a file called hello.txt with 'Hello World'"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data.content);
};
```

## Development

### Project Structure

```
backend/
├── main.py           # FastAPI server
├── agent.py          # LangChain agent with MCP tools
├── mcp_client.py     # MCP client wrapper
├── llm.py            # LLM configuration (Ollama/DeepSeek)
├── config.py         # Settings and configuration
├── requirements.txt  # Python dependencies
└── .env.example      # Environment variables template
```

### Testing

```bash
# Test MCP connection
python -c "
import asyncio
from mcp_client import mcp_manager

async def test():
    tools = await mcp_manager.list_tools('shell')
    print(f'Found {len(tools)} tools')

asyncio.run(test())
"
```

### Debugging

Set `LOG_LEVEL=DEBUG` in `.env` for verbose logging.

## Troubleshooting

### "Module 'mcp' not found"

```bash
pip install mcp
```

### "Cannot connect to Ollama"

```bash
# Make sure Ollama is running
ollama serve

# Check if model is available
ollama list
```

### "Cannot connect to sandbox container"

```bash
# Check container is running
docker ps | grep sandbox

# Check MCP servers are running
docker exec sandbox-sandbox-os-1 ps aux | grep mcp
```

## Next Steps

1. **Frontend Integration**: Add chat window to Vue frontend
2. **Session Management**: Implement per-user chat sessions
3. **Tool Permissions**: Add approval workflow for destructive operations
4. **Streaming**: Implement streaming responses for better UX
5. **Persistence**: Save chat history to database

## License

MIT
