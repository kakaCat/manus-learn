from typing import List, Any
from app.models.schemas import Task, SharedBlackboard
from app.core.prompts.agents import WEB_SEARCH_AGENT_PROMPT
from app.core.agents.base import BaseSubAgent

class WebSearchAgent(BaseSubAgent):
    """Specialized Sub-Agent for Web Search operations"""
    def __init__(self, task: Task, blackboard: SharedBlackboard, tools: List[Any], session_id: str = None):
        super().__init__(task, blackboard, tools, session_id=session_id, system_prompt=WEB_SEARCH_AGENT_PROMPT)
