"""Chat API routes - WebSocket and REST endpoints."""

import logging
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.models.chat import ChatMessage, ChatRequest, ChatResponse
from app.services.agent import sandbox_agent
from app.services.chat_history import chat_history_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat with the AI agent.

    Protocol:
    - Client sends JSON: {"message": "user message", "thread_id": "optional"}
    - Server sends JSON: {"type": "response"|"error"|"thinking", "content": "..."}
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    # Create session for this WebSocket connection
    session_id = chat_history_manager.create_session()
    thread_id = session_id  # Use same ID for LangGraph thread

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            user_message = data.get("message", "")
            custom_thread_id = data.get("thread_id")  # Allow client to specify thread_id

            if custom_thread_id:
                thread_id = custom_thread_id

            if not user_message:
                await websocket.send_json({
                    "type": "error",
                    "content": "Empty message received"
                })
                continue

            logger.info(f"Received message (thread={thread_id}): {user_message}")

            # Add to chat history
            chat_history_manager.add_message(session_id, "user", user_message)

            # Send thinking indicator
            await websocket.send_json({
                "type": "thinking",
                "content": "Processing your request..."
            })

            try:
                # Run agent with thread ID for memory
                response = await sandbox_agent.run(
                    user_input=user_message,
                    thread_id=thread_id,
                )

                # Add response to history
                chat_history_manager.add_message(session_id, "assistant", response)

                # Send response
                await websocket.send_json({
                    "type": "response",
                    "content": response,
                    "thread_id": thread_id
                })

                logger.info(f"Sent response (thread={thread_id}): {response[:100]}...")

            except Exception as e:
                error_msg = f"Error processing request: {str(e)}"
                logger.error(error_msg, exc_info=True)

                await websocket.send_json({
                    "type": "error",
                    "content": error_msg
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed (session={session_id})")

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)

        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Server error: {str(e)}"
            })
        except:
            pass


@router.post("/api", response_model=ChatResponse)
async def api_chat(request: ChatRequest):
    """
    REST API endpoint for chat (alternative to WebSocket).

    Request body:
        {
            "message": "user message",
            "chat_history": [{"role": "user|assistant", "content": "..."}],
            "thread_id": "optional thread ID for memory"
        }

    Returns:
        {
            "status": "success"|"error",
            "response": "AI response",
            "error": null|"error message",
            "thread_id": "thread ID used"
        }
    """
    try:
        user_message = request.message
        history = request.chat_history
        thread_id = getattr(request, 'thread_id', None)

        if not user_message:
            return ChatResponse(
                status="error",
                error="Empty message"
            )

        logger.info(f"API chat request: {user_message}")

        # Convert chat history to ChatMessage format
        formatted_history = []
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # Map 'human' to 'user' for consistency
            if role == "human":
                role = "user"
            elif role == "ai":
                role = "assistant"
            formatted_history.append(ChatMessage(role=role, content=content))

        # Run agent
        response = await sandbox_agent.run(
            user_input=user_message,
            thread_id=thread_id,
            chat_history=formatted_history if formatted_history else None
        )

        logger.info(f"API chat response: {response[:100]}...")

        return ChatResponse(
            status="success",
            response=response
        )

    except Exception as e:
        error_msg = f"Error processing chat: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return ChatResponse(
            status="error",
            error=error_msg
        )


@router.post("/clear")
async def clear_chat(session_id: str = None):
    """
    Clear chat history for a session.

    Query params:
        session_id: Session ID to clear (clears default if not provided)
    """
    if session_id:
        chat_history_manager.clear_session(session_id)
    else:
        # Clear all sessions (for backward compatibility)
        for sid in list(chat_history_manager.sessions.keys()):
            chat_history_manager.clear_session(sid)

    return {"status": "cleared", "session_id": session_id}


@router.get("/sessions")
async def get_sessions():
    """Get information about active chat sessions."""
    return {
        "total_sessions": chat_history_manager.get_session_count(),
        "sessions": list(chat_history_manager.sessions.keys())
    }
