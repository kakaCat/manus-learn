"""FastAPI backend server with WebSocket support for chat."""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from agent import sandbox_agent
from mcp_client import mcp_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting backend server...")
    try:
        await sandbox_agent.initialize()
        logger.info("Sandbox agent initialized")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")

    yield

    # Shutdown
    logger.info("Shutting down backend server...")
    try:
        await mcp_manager.close_all()
        logger.info("MCP connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="Sandbox AI Backend",
    description="LangChain + MCP backend for AI-powered sandbox control",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Data models
class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # "user" or "assistant"
    content: str


class ChatHistory:
    """Simple in-memory chat history manager."""

    def __init__(self):
        self.messages: List[ChatMessage] = []

    def add_message(self, role: str, content: str):
        """Add a message to history."""
        self.messages.append(ChatMessage(role=role, content=content))

    def get_messages(self) -> List[ChatMessage]:
        """Get all messages."""
        return self.messages

    def clear(self):
        """Clear history."""
        self.messages.clear()


# Global chat history (in production, use per-session storage)
chat_history = ChatHistory()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Sandbox AI Backend",
        "status": "running",
        "llm_provider": settings.llm_provider,
        "sandbox_container": settings.sandbox_container_name,
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for chat with the AI agent.

    Protocol:
    - Client sends JSON: {"message": "user message"}
    - Server sends JSON: {"type": "response", "content": "AI response"}
    - Server sends JSON: {"type": "error", "content": "error message"}
    - Server sends JSON: {"type": "thinking", "content": "..."} (optional)
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            user_message = data.get("message", "")

            if not user_message:
                await websocket.send_json({
                    "type": "error",
                    "content": "Empty message received"
                })
                continue

            logger.info(f"Received message: {user_message}")

            # Add to chat history
            chat_history.add_message("user", user_message)

            # Send thinking indicator
            await websocket.send_json({
                "type": "thinking",
                "content": "Processing your request..."
            })

            try:
                # Run agent
                response = await sandbox_agent.run(
                    user_input=user_message,
                    chat_history=chat_history.get_messages(),
                )

                # Add response to history
                chat_history.add_message("assistant", response)

                # Send response
                await websocket.send_json({
                    "type": "response",
                    "content": response
                })

                logger.info(f"Sent response: {response[:100]}...")

            except Exception as e:
                error_msg = f"Error processing request: {str(e)}"
                logger.error(error_msg)

                await websocket.send_json({
                    "type": "error",
                    "content": error_msg
                })

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Server error: {str(e)}"
            })
        except:
            pass


@app.post("/chat/clear")
async def clear_chat():
    """Clear chat history."""
    chat_history.clear()
    return {"status": "cleared"}


@app.post("/api/chat")
async def api_chat(request: dict):
    """
    REST API endpoint for chat (alternative to WebSocket).

    Request body:
        {
            "message": "user message",
            "chat_history": [{"role": "human|ai", "content": "..."}]
        }

    Returns:
        {
            "status": "success",
            "response": "AI response"
        }
    """
    try:
        user_message = request.get("message", "")
        history = request.get("chat_history", [])

        if not user_message:
            return {
                "status": "error",
                "error": "Empty message"
            }

        logger.info(f"API chat request: {user_message}")

        # Convert to ChatMessage format if needed
        formatted_history = []
        for msg in history:
            role = msg.get("role", "human")
            content = msg.get("content", "")
            # Map 'human' to 'user' and 'ai' to 'assistant' for consistency
            formatted_role = "user" if role == "human" else "assistant"
            formatted_history.append(ChatMessage(role=formatted_role, content=content))

        # Run agent
        response = await sandbox_agent.run(
            user_input=user_message,
            chat_history=formatted_history
        )

        logger.info(f"API chat response: {response[:100]}...")

        return {
            "status": "success",
            "response": response
        }

    except Exception as e:
        error_msg = f"Error processing chat: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }


# ==================== Sandbox Monitoring Endpoints ====================

@app.get("/api/sandbox/status")
async def get_sandbox_status():
    """
    Get overall sandbox status including MCP servers and container health.

    Returns:
        JSON with MCP server statuses, container info, and health metrics
    """
    try:
        # Get MCP server status
        mcp_status = await mcp_manager.call_tool(
            server_name="manager",
            tool_name="get_mcp_status",
            arguments={}
        )

        # Get installed MCPs
        installed_mcps = await mcp_manager.call_tool(
            server_name="manager",
            tool_name="list_installed_mcps",
            arguments={}
        )

        return {
            "status": "running",
            "container": settings.sandbox_container_name,
            "mcp_status": mcp_status[0].text if mcp_status else "Unknown",
            "installed_mcps": installed_mcps[0].text if installed_mcps else "Unknown",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Error getting sandbox status: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/sandbox/processes")
async def get_sandbox_processes():
    """
    Get list of running processes in the sandbox.

    Returns:
        JSON with process list (pid, name, cpu%, memory%)
    """
    try:
        result = await mcp_manager.call_tool(
            server_name="shell",
            tool_name="get_running_processes",
            arguments={}
        )

        return {
            "status": "success",
            "processes": result[0].text if result else "No processes found",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Error getting processes: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/sandbox/resources")
async def get_sandbox_resources():
    """
    Get container resource usage (CPU, memory, disk).

    Returns:
        JSON with resource metrics
    """
    try:
        # Execute command to get resource usage
        result = await mcp_manager.call_tool(
            server_name="shell",
            tool_name="execute_command",
            arguments={
                "command": "bash",
                "args": ["-c", "echo 'CPU:'; top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'; echo 'Memory:'; free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2 }'; echo ''; echo 'Disk:'; df -h / | awk 'NR==2{print $5}'"]
            }
        )

        return {
            "status": "success",
            "resources": result[0].text if result else "Unknown",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Error getting resources: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/sandbox/logs")
async def get_sandbox_logs():
    """
    Get recent logs from MCP servers.

    Returns:
        JSON with log entries
    """
    try:
        # Read recent logs from supervisord
        result = await mcp_manager.call_tool(
            server_name="shell",
            tool_name="execute_command",
            arguments={
                "command": "tail",
                "args": ["-n", "50", "/var/log/supervisor/supervisord.log"]
            }
        )

        return {
            "status": "success",
            "logs": result[0].text if result else "No logs available",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/mcp/marketplace")
async def get_mcp_marketplace():
    """
    Get list of available MCPs from the marketplace.

    Returns:
        JSON with available MCP tools
    """
    try:
        result = await mcp_manager.call_tool(
            server_name="manager",
            tool_name="list_available_mcps",
            arguments={}
        )

        return {
            "status": "success",
            "marketplace": result[0].text if result else "No MCPs available",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Error getting marketplace: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
