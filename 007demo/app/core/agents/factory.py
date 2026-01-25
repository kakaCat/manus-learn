from typing import List, Any
from app.models.schemas import Task, SharedBlackboard, AgentType
from app.core.agents.base import BaseSubAgent
from app.core.agents.shell import ShellAgent
from app.core.agents.filesystem import FilesystemAgent
from app.core.agents.browser import BrowserAgent
from app.core.agents.web_search import WebSearchAgent
from app.core.agents.general import GeneralAgent

def get_agent_for_task(task: Task, blackboard: SharedBlackboard, tools: List[Any], session_id: str = None) -> BaseSubAgent:
    """Factory function to get the correct agent instance based on task assignment."""
    if task.assigned_agent == AgentType.SHELL:
        return ShellAgent(task, blackboard, tools, session_id=session_id)
    elif task.assigned_agent == AgentType.FILESYSTEM:
        return FilesystemAgent(task, blackboard, tools, session_id=session_id)
    elif task.assigned_agent == AgentType.BROWSER:
        return BrowserAgent(task, blackboard, tools, session_id=session_id)
    elif task.assigned_agent == AgentType.WEB_SEARCH:
        return WebSearchAgent(task, blackboard, tools, session_id=session_id)
    else:
        return GeneralAgent(task, blackboard, tools, session_id=session_id)
