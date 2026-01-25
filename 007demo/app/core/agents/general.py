from typing import List, Any
from app.models.schemas import Task, SharedBlackboard
from app.core.prompts.agents import GENERAL_AGENT_PROMPT
from app.core.agents.base import BaseSubAgent

class GeneralAgent(BaseSubAgent):
    """General Purpose Sub-Agent"""
    def __init__(self, task: Task, blackboard: SharedBlackboard, tools: List[Any], session_id: str = None):
        super().__init__(task, blackboard, tools, session_id=session_id, system_prompt=GENERAL_AGENT_PROMPT)
