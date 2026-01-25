from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class MainMemory(BaseModel):
    """Level A: Global/Strategic Memory"""
    final_goal: str = Field(description="The ultimate goal of the user")
    complexity: str = Field(default="simple", description="Task complexity: 'simple' or 'complex'")
    theme: str = Field(default="general", description="Task theme: 'coding', 'research', 'writing', 'general'")
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict, description="User preferences and constraints"
    )
    milestones_completed: List[str] = Field(
        default_factory=list, description="List of completed milestones"
    )
    sub_agent_summaries: List[str] = Field(
        default_factory=list, description="Summaries submitted by sub-agents"
    )
    global_summary: str = Field(
        default="", description="Level A: Global summary of the project progress maintained by ConversationSummaryMemory"
    )
    summarized_idx: int = Field(
        default=0, description="Index of the last summarized sub-agent summary"
    )

class SharedBlackboard(BaseModel):
    """Level C: Shared Blackboard/Short-term Store"""
    variables: Dict[str, Any] = Field(
        default_factory=dict, description="Key variables shared across agents"
    )
    key_conclusions: List[str] = Field(
        default_factory=list, description="Key conclusions from previous turns"
    )

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentType(str, Enum):
    MAIN = "main"
    SHELL = "shell"
    FILESYSTEM = "filesystem"
    BROWSER = "browser"
    WEB_SEARCH = "web_search"
    GENERAL = "general"

class Task(BaseModel):
    id: int = Field(description="Unique identifier for the task")
    description: str = Field(description="Description of what needs to be done")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    assigned_agent: AgentType = Field(default=AgentType.GENERAL)
    dependencies: List[int] = Field(
        default_factory=list,
        description="IDs of tasks that must complete before this one",
    )
    result: Optional[str] = None

class Plan(BaseModel):
    goal: str = Field(description="The overall goal of the plan")
    tasks: List[Task] = Field(description="List of tasks to achieve the goal")

class IntentAnalysis(BaseModel):
    intent: str = Field(description="A concise description of the user's intent")
    complexity: str = Field(description="Task complexity: 'simple' or 'complex'")
    theme: str = Field(description="Task theme: 'coding', 'research', 'writing', 'general'")
    needs_sandbox: bool = Field(
        description="Whether the request requires sandbox operations"
    )

class ReflectionResult(BaseModel):
    success: bool = Field(description="Whether the previous step was successful")
    feedback: str = Field(description="Feedback or suggestions for the next step")
    next_action: str = Field(description="High level description of what to do next")
    should_continue: bool = Field(description="Whether to continue execution")
