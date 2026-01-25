from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import json
from app.services.agent_service import AgentService

router = APIRouter()
# We need a way to inject service, for simplicity we use a global instance or dependency injection
# For this demo, we'll instantiate it in main.py and pass it, or access via app state.
# But here we can't easily access app state without request.
# Let's assume a singleton pattern for the service for simplicity in this refactor.

_service: AgentService = None

def get_service() -> AgentService:
    global _service
    if _service is None:
        _service = AgentService()
    return _service

from typing import Optional

class TaskRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

@router.post("/run")
async def run_task(request: TaskRequest):
    """
    Run a task and return the final result (blocking).
    For streaming, use /stream.
    """
    service = get_service()
    try:
        async for event in service.run_task_stream(request.query, request.session_id):
            # We are just consuming the stream to completion
            pass
        return {"status": "completed", "message": "Task finished"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_task(request: TaskRequest):
    """
    Stream the execution events of the task.
    """
    service = get_service()
    async def event_generator():
        try:
            async for event in service.run_task_stream(request.query, request.session_id):
                # Simplified event yielding
                event_type = list(event.keys())[0]
                yield f"data: {json.dumps({'type': event_type, 'content': json.dumps(event, default=str)})}\n\n"
                
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
