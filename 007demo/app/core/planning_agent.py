import os
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.core.state import AgentState
from app.core.utils import print_todo_list
from app.models.schemas import MainMemory, SharedBlackboard, Plan, IntentAnalysis, Task, TaskStatus, AgentType
from app.core.prompts.intent import INTENT_ANALYSIS_SYSTEM_PROMPT
from app.core.prompts.planning import PLANNER_SYSTEM_PROMPT, CREATE_PLAN_PROMPT

class PlanStep(BaseModel):
    id: str = Field(description="Step identifier")
    description: str = Field(description="Step description")

class CreatePlanResponse(BaseModel):
    message: str = Field(description="Response to user's message and thinking about the task")
    language: str = Field(description="The working language")
    steps: List[PlanStep] = Field(description="Array of steps")
    goal: str = Field(description="Plan goal")
    title: str = Field(description="Plan title")

def _get_llm():
    return ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=0,
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )

async def analyze_intent(state: AgentState) -> Dict:
    """Analyze intent and initialize Main Memory."""
    print(f"\n🧠 [Main Agent] Analyzing Intent: {state['user_input']}")

    llm = _get_llm()
    parser = PydanticOutputParser(pydantic_object=IntentAnalysis)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", INTENT_ANALYSIS_SYSTEM_PROMPT),
        ("user", "{request}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        analysis = await chain.ainvoke({
            "request": state["user_input"],
            "format_instructions": parser.get_format_instructions()
        })
        print(f"  🔍 Analysis Result - Intent: {analysis.intent} | Complexity: {analysis.complexity} | Theme: {analysis.theme}")
    except Exception as e:
        print(f"  ⚠️ Intent Analysis Failed: {e}. Using defaults.")
        analysis = IntentAnalysis(intent=state["user_input"], complexity="simple", theme="general", needs_sandbox=False)

    # Initialize Main Memory
    main_mem = state.get("main_memory")
    if not main_mem:
        main_mem = MainMemory(
            final_goal=state["user_input"],
            complexity=analysis.complexity,
            theme=analysis.theme
        )
    else:
        main_mem.complexity = analysis.complexity
        main_mem.theme = analysis.theme

    # Check shared blackboard
    blackboard = state.get("shared_blackboard")
    if not blackboard:
        blackboard = SharedBlackboard()

    return {
        "main_memory": main_mem,
        "shared_blackboard": blackboard,
        "active_task_ids": [],
    }

async def create_simple_plan(state: AgentState) -> Dict:
    """Create a plan for simple tasks (Default Plan Agent)."""
    print(f"\n📋 [Main Agent] Creating Simple Plan...")
    return await _generate_plan(state)

async def create_complex_plan(state: AgentState) -> Dict:
    """Create a plan for complex tasks (Theme-based Plan Agent)."""
    theme = state["main_memory"].theme
    print(f"\n📋 [Main Agent] Creating Complex Plan for Theme: {theme}...")
    return await _generate_plan(state)

async def _generate_plan(state: AgentState) -> Dict:
    """Helper to generate plan using the new structured prompt."""
    llm = _get_llm()
    parser = PydanticOutputParser(pydantic_object=CreatePlanResponse)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", PLANNER_SYSTEM_PROMPT),
            ("user", CREATE_PLAN_PROMPT),
        ]
    )

    chain = prompt | llm | parser
    try:
        # Default empty attachments if not present
        attachments = "[]"
        
        response = await chain.ainvoke({
            "message": state["main_memory"].final_goal,
            "attachments": attachments
        })
        
        # Convert response to Plan object
        tasks = []
        for step in response.steps:
            # Try to keep original ID if it's an int, otherwise generate one or use 0
            # Since existing Task expects int id, we need to map string ids.
            # Ideally we change Task.id to str, but that might break other things.
            # For now, let's just use a simple counter or hash if possible, 
            # but better to rely on order.
            try:
                task_id = int(step.id)
            except ValueError:
                # If id is not int, use hash or random. 
                # Or just re-index based on list position + 1
                task_id = 0 # Placeholder, we will re-index below
            
            tasks.append(Task(
                id=task_id,
                description=step.description,
                assigned_agent=AgentType.GENERAL
            ))
        
        # Re-index tasks to ensure unique int IDs starting from 1
        for i, task in enumerate(tasks):
            task.id = i + 1
            
        plan = Plan(goal=response.goal, tasks=tasks)
        
        print(f"✅ Plan Created with {len(plan.tasks)} tasks.")
        print_todo_list(plan)
        
        return {
            "plan": plan,
            # Reset active tasks
            "active_task_ids": []
        }

    except Exception as e:
        print(f"❌ Planning Failed: {e}")
        # Fallback to a single task with the user input
        return {
            "plan": Plan(
                goal=state["main_memory"].final_goal,
                tasks=[Task(id=1, description=state["main_memory"].final_goal, status=TaskStatus.PENDING)]
            ),
            "active_task_ids": []
        }
