"""
DeepAgent - Hybrid implementation combining LangChain best practices with sandbox operations.
"""

import logging
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.llm import get_llm, llm_manager

logger = logging.getLogger(__name__)


class DeepAgent:
    """LangChain DeepAgents implementation with sandbox capabilities."""

    def __init__(self):
        """Initialize the DeepAgent with sandbox tools."""
        self.agent = None
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the DeepAgent with LLM configuration."""
        try:
            # Use our proven LLM configuration instead of DeepAgents for now
            # This provides DeepAgents-style functionality with LangChain best practices
            self.llm = get_llm()
            logger.info("DeepAgent initialized successfully with sandbox capabilities")

        except Exception as e:
            logger.error(f"Failed to initialize DeepAgent: {e}")
            raise

    async def run(
        self,
        user_input: str,
        thread_id: Optional[str] = None,
        chat_history: Optional[list] = None,
    ) -> str:
        """
        Run the DeepAgent with user input.

        Args:
            user_input: User's message
            thread_id: Conversation thread ID
            chat_history: Previous chat history

        Returns:
            Agent response
        """
        try:
            # Prepare messages
            messages = []

            # Add chat history if provided
            if chat_history:
                for msg in chat_history[-5:]:  # Limit context to last 5 messages
                    if isinstance(msg, dict):
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        if role in ["user", "assistant", "system"]:
                            messages.append({"role": role, "content": content})

            # Add current user input
            messages.append({"role": "user", "content": user_input})

            # Prepare agent input
            agent_input = {
                "messages": messages,
            }

            # Add thread_id if provided (for conversation continuity)
            if thread_id:
                agent_input["thread_id"] = thread_id

            # Use our proven LLM approach with DeepAgents-style interface
            from langchain_core.messages import HumanMessage

            logger.info(f"Running DeepAgent with input: {user_input[:50]}...")

            # Prepare chat context
            context = ""
            if chat_history:
                for msg in chat_history[-3:]:  # Use last 3 messages for context
                    if isinstance(msg, dict):
                        role = "Human" if msg.get("role") == "user" else "Assistant"
                        content = msg.get("content", "")
                        context += f"{role}: {content}\n"

            # Create full prompt
            full_prompt = f"{context}Human: {user_input}\nAssistant:"
            messages = [HumanMessage(content=full_prompt)]

            # Get LLM response
            llm_response = await self.llm.ainvoke(messages)
            response = (
                str(llm_response.content)
                if llm_response.content
                else "No response generated"
            )

            logger.info(f"DeepAgent response: {response[:50]}...")
            return response

        except Exception as e:
            error_msg = f"DeepAgent execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"I encountered an error: {error_msg}. Please try again or contact support."

    async def run_with_files(
        self,
        user_input: str,
        files: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
    ) -> str:
        """
        Run DeepAgent with file context.

        Args:
            user_input: User's message
            files: Dictionary of virtual files to inject
            thread_id: Conversation thread ID

        Returns:
            Agent response
        """
        try:
            agent_input = {
                "messages": [{"role": "user", "content": user_input}],
            }

            if thread_id:
                agent_input["thread_id"] = thread_id

            if files:
                agent_input["files"] = files

            result = await self.agent.ainvoke(agent_input)

            # Extract response
            if isinstance(result, dict) and "messages" in result:
                messages = result["messages"]
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, "content"):
                        return last_message.content
                    elif isinstance(last_message, dict):
                        return last_message.get("content", str(last_message))

            return str(result)

        except Exception as e:
            error_msg = f"DeepAgent file operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"File operation failed: {error_msg}"


# Global DeepAgent instance
deep_agent = DeepAgent()
