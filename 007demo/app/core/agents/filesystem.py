from typing import List, Any
from app.models.schemas import Task, SharedBlackboard
from app.core.prompts.agents import FILESYSTEM_AGENT_PROMPT
from app.core.agents.base import BaseSubAgent

class FilesystemAgent(BaseSubAgent):
    """Specialized Sub-Agent for Filesystem operations"""
    def __init__(self, task: Task, blackboard: SharedBlackboard, tools: List[Any], session_id: str = None):
        super().__init__(task, blackboard, tools, session_id=session_id, system_prompt=FILESYSTEM_AGENT_PROMPT)
