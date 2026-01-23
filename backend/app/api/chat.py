"""Chat API routes - WebSocket and REST endpoints."""

import asyncio
import logging
import uuid
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.models.chat import ChatMessage, ChatRequest, ChatResponse
from app.services.deep_agent import deep_agent
from app.services.chat_history import chat_history_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Global chat history manager for backward compatibility and session management


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

    # Create a new chat session for this WebSocket connection
    # Session tracks message history for backward compatibility
    session_id = chat_history_manager.create_session()
    thread_id = (
        session_id  # Use session ID as LangGraph thread ID for memory consistency
    )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            user_message = data.get("message", "")
            custom_thread_id = data.get(
                "thread_id"
            )  # Allow client to specify thread_id

            if custom_thread_id:
                thread_id = custom_thread_id

            if not user_message:
                await websocket.send_json(
                    {"type": "error", "content": "Empty message received"}
                )
                continue

            logger.info(f"Received message (thread={thread_id}): {user_message}")

            # Add to chat history
            chat_history_manager.add_message(session_id, "user", user_message)

            # Send thinking indicator
            await websocket.send_json(
                {"type": "thinking", "content": "Processing your request..."}
            )

        # Use direct LLM call (simpler than llm_manager)
        from app.core.llm import get_llm
        from langchain_core.messages import HumanMessage

        llm = get_llm()
        messages = [HumanMessage(content=user_message)]
        llm_response = await llm.ainvoke(messages)
        response = llm_response.content

        # Add response to history
        chat_history_manager.add_message(session_id, "assistant", response)

        # Send response
        await websocket.send_json(
            {"type": "response", "content": response, "thread_id": thread_id}
        )

        logger.info(f"Sent response (thread={thread_id}): {response[:100]}...")

    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed (session={session_id})")

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)

        try:
            await websocket.send_json(
                {"type": "error", "content": f"Server error: {str(e)}"}
            )
        except:
            pass


@router.post("", response_model=ChatResponse)
async def api_chat(request: ChatRequest):
    """
    REST API endpoint for chat (alternative to WebSocket).

    Accessible at: POST /api/chat

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
        thread_id = getattr(request, "thread_id", None) or str(uuid.uuid4())

        if not user_message:
            return ChatResponse(status="error", error="Empty message")

        logger.info(f"API chat request: {user_message}")

        # Convert incoming chat history from dict format to ChatMessage objects
        # This handles legacy API compatibility where roles might be 'human'/'ai' instead of 'user'/'assistant'
        formatted_history = []
        for i, msg in enumerate(history):
            try:
                if not isinstance(msg, dict):
                    raise ValueError(f"Message {i} is not a dict: {type(msg)} - {msg}")

                role = msg.get("role", "user")
                content = msg.get("content", "")

                if not isinstance(role, str) or not isinstance(content, str):
                    raise ValueError(
                        f"Message {i} has invalid role/content types: role={type(role)}, content={type(content)}"
                    )

                # Normalize role names for consistency with LangChain standards
                if role == "human":
                    role = "user"
                elif role == "ai":
                    role = "assistant"

                formatted_history.append(ChatMessage(role=role, content=content))
            except Exception as msg_error:
                logger.warning(f"Skipping invalid message {i}: {msg_error}")
                continue

        # Use DeepAgent Core for advanced multi-agent processing
        from app.services.deep_agent_core import deep_agent_core

        # Process through DeepAgent Core with longer timeout for complex operations
        try:
            processing_result = await asyncio.wait_for(
                deep_agent_core.process(
                    user_input=user_message,
                    context={
                        "thread_id": thread_id,
                        "chat_history": formatted_history if formatted_history else [],
                        "api_request": True,
                    },
                ),
                timeout=120.0,  # 120 seconds timeout for agent processing (needed for complex LLM calls)
            )
        except asyncio.TimeoutError:
            return ChatResponse(
                status="error",
                response="请求处理超时，请稍后重试或简化您的问题。",
                error="Agent processing timeout",
            )

        # Format response based on processing result
        print(f"DEBUG: Processing result: {processing_result}")

        if processing_result.get("status") == "clarification_needed":
            # Need clarification from user
            questions = processing_result.get("clarification_questions", [])
            response = f"🤔 我需要更多信息来理解您的需求：\n" + "\n".join(
                f"• {q}" for q in questions
            )

        elif processing_result.get("status") == "completed":
            # Processing completed successfully
            agent_name = processing_result.get("agent", "Unknown")
            task_result = processing_result.get("result", "")

            # Debug logging
            print(
                f"DEBUG: agent_name={agent_name}, task_result length={len(task_result) if task_result else 0}"
            )
            print(
                f"DEBUG: task_result preview: {task_result[:100] if task_result else 'None'}"
            )

            if task_result and task_result.strip():
                response = f"[{agent_name}] {task_result}"
            else:
                response = f"[{agent_name}] 任务已完成，但没有返回结果。"

        elif processing_result.get("status") == "error":
            # Processing failed
            error_msg = processing_result.get("error", "Unknown error")
            response = f"❌ 处理过程中出现错误: {error_msg}"

        else:
            # Fallback for unknown status
            response = f"处理完成。状态: {processing_result.get('status', 'unknown')}"

        logger.info(f"API chat response: {response[:100]}...")

        # Add assistant response to history
        chat_history_manager.add_message(thread_id, "assistant", response)

        return ChatResponse(status="success", response=response, thread_id=thread_id)

    except Exception as e:
        error_type = type(e).__name__
        error_details = str(e) if str(e) else "Unknown error"
        error_msg = f"Error processing chat: {error_type} - {error_details}"
        logger.error(error_msg, exc_info=True)
        return ChatResponse(status="error", error=error_msg)


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
        "sessions": list(chat_history_manager.sessions.keys()),
    }
