"""FastAPI application factory - Main entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.services.agent import sandbox_agent
from app.services.mcp_client import mcp_manager
from app.api import chat, sandbox

# Setup logging
setup_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown.

    Handles:
    - Agent initialization on startup
    - MCP connection cleanup on shutdown
    """
    # === STARTUP ===
    logger.info("=" * 60)
    logger.info("🚀 Starting Manus Learn Backend Server")
    logger.info("=" * 60)
    logger.info(f"   Version: 2.0.0 (LangChain 1.X + LangGraph)")
    logger.info(f"   LLM Provider: {settings.llm_provider}")
    logger.info(f"   Container: {settings.sandbox_container_name}")
    logger.info(f"   Port: {settings.backend_port}")
    logger.info(f"   Log Level: {settings.log_level}")
    logger.info("=" * 60)

    try:
        logger.info("⚙️  Initializing sandbox agent with MemorySaver...")
        await sandbox_agent.initialize()
        logger.info("✅ Sandbox agent initialized successfully")
    except Exception as e:
        logger.error("❌ Failed to initialize agent")
        logger.error(f"   Error: {e}", exc_info=True)

    yield

    # === SHUTDOWN ===
    logger.info("=" * 60)
    logger.info("🛑 Shutting down backend server...")
    try:
        await mcp_manager.close_all()
        logger.info("✅ MCP connections closed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}", exc_info=True)
    logger.info("=" * 60)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI instance
    """
    app = FastAPI(
        title="Manus Learn Backend",
        description="LangGraph + MCP backend for AI-powered sandbox control",
        version="2.0.0",
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

    # Register routers
    app.include_router(chat.router)
    app.include_router(sandbox.router, prefix="/api")

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with service information."""
        return {
            "service": "Manus Learn Backend",
            "version": "2.0.0",
            "status": "running",
            "llm_provider": settings.llm_provider,
            "sandbox_container": settings.sandbox_container_name,
            "features": [
                "LangGraph ReAct Agent",
                "MemorySaver Checkpointer",
                "MCP Tool Integration",
                "Thread-based Memory",
            ]
        }

    # Health check endpoint
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "agent_initialized": sandbox_agent.agent is not None
        }

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
