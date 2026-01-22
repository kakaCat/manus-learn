"""Chat history management service."""

import logging
from typing import List, Dict, Optional
from uuid import uuid4

from app.models.chat import ChatMessage

logger = logging.getLogger(__name__)


class ChatHistoryManager:
    """
    In-memory chat history manager.

    For production, replace with persistent storage (Redis, PostgreSQL, etc.)
    Note: With LangGraph's MemorySaver, this is mostly for backward compatibility.
    """

    def __init__(self):
        """Initialize chat history manager."""
        self.sessions: Dict[str, List[ChatMessage]] = {}

    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new chat session.

        Args:
            session_id: Optional session ID (auto-generated if None)

        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid4())

        if session_id not in self.sessions:
            self.sessions[session_id] = []
            logger.info(f"Created new chat session: {session_id}")

        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to session history.

        Args:
            session_id: Session ID
            role: Message role ("user" or "assistant")
            content: Message content
        """
        if session_id not in self.sessions:
            self.create_session(session_id)

        message = ChatMessage(role=role, content=content)
        self.sessions[session_id].append(message)

        logger.debug(f"Added {role} message to session {session_id}")

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        """
        Get all messages for a session.

        Args:
            session_id: Session ID

        Returns:
            List of ChatMessage objects
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found, creating new")
            self.create_session(session_id)

        return self.sessions[session_id]

    def clear_session(self, session_id: str):
        """
        Clear all messages in a session.

        Args:
            session_id: Session ID
        """
        if session_id in self.sessions:
            self.sessions[session_id].clear()
            logger.info(f"Cleared session: {session_id}")

    def delete_session(self, session_id: str):
        """
        Delete a session entirely.

        Args:
            session_id: Session ID
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")

    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        return len(self.sessions)


# Global chat history manager instance
chat_history_manager = ChatHistoryManager()
