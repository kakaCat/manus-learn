"""Configuration for backend services."""

import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    llm_provider: Literal["ollama", "deepseek"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "deepseek-r1:1.5b"

    # DeepSeek Configuration (optional)
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"

    # MCP Sandbox Configuration
    sandbox_container_name: str = "sandbox-sandbox-os-1"
    mcp_python_path: str = "/opt/mcp-venv/bin/python"
    mcp_servers_dir: str = "/opt/mcp-servers"

    # Backend API Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
