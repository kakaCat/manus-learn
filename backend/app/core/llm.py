"""LLM integration supporting Ollama and DeepSeek (LangChain 1.X)."""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_llm() -> BaseChatModel:
    """
    Get configured LLM instance based on settings.

    Returns:
        BaseChatModel instance (Ollama or DeepSeek)

    Raises:
        ValueError: If llm_provider is unsupported
    """
    if settings.llm_provider == "ollama":
        logger.info(f"Initializing Ollama LLM: {settings.ollama_model}")

        # Use native Ollama integration for LangChain 1.X
        llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.7,
        )

        logger.info("Ollama LLM initialized successfully")
        return llm

    elif settings.llm_provider == "deepseek":
        logger.info("Initializing DeepSeek LLM via OpenAI SDK")

        if not settings.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required for DeepSeek provider")

        llm = ChatOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model="deepseek-chat",  # DeepSeek's chat model
            temperature=0.7,
            streaming=True,
        )

        logger.info("DeepSeek LLM initialized successfully")
        return llm

    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


class LLMManager:
    """Manages LLM instance and provides helper methods."""

    def __init__(self):
        """Initialize LLM manager."""
        self.llm: Optional[BaseChatModel] = None

    def get_or_create_llm(self) -> BaseChatModel:
        """Get existing LLM or create new one."""
        if self.llm is None:
            self.llm = get_llm()
        return self.llm

    async def invoke(self, messages: List[Dict[str, str]]) -> Any:
        """
        Invoke LLM with messages.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            LLM response content
        """
        llm = self.get_or_create_llm()

        # Convert to LangChain message format
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))

        response = await llm.ainvoke(lc_messages)
        return response.content


# Global LLM manager instance
llm_manager = LLMManager()
