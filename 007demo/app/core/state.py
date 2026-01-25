from typing import List, Optional, TypedDict, Annotated, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from app.models.schemas import MainMemory, SharedBlackboard, Plan

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  # Global audit log
    user_input: str
    session_id: Optional[str]  # Unique session identifier

    # Memory Layers
    main_memory: MainMemory
    shared_blackboard: SharedBlackboard

    # Execution State
    plan: Optional[Plan]
    active_task_ids: List[int]  # IDs of tasks currently being executed

    # Sub-Agent specific (Level B - Transient)
    sub_agent_scratchpad: Dict[str, Any]
