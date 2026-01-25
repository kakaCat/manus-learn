
import asyncio
import os
import json
from typing import List, Dict, Any

from app.core.state import AgentState
from app.models.schemas import SharedBlackboard, Task, TaskStatus, AgentType
from app.core.agents.factory import get_agent_for_task

async def scheduler_node(state: AgentState) -> Dict:
    """Decides which tasks to execute next (Parallel Scheduler)."""
    print(f"\n🗓️ [Scheduler] Checking for executable tasks...")
    plan = state["plan"]
    completed_ids = {t.id for t in plan.tasks if t.status == TaskStatus.COMPLETED}

    executable_tasks = []
    for task in plan.tasks:
        if task.status == TaskStatus.PENDING:
            # Check dependencies
            if not task.dependencies or all(
                dep_id in completed_ids for dep_id in task.dependencies
            ):
                executable_tasks.append(task)

    if not executable_tasks:
        print("  No executable tasks found.")
        return {"active_task_ids": []}

    # Mark them as IN_PROGRESS
    for task in executable_tasks:
        task.status = TaskStatus.IN_PROGRESS

    print(
        f"  🚀 Launching {len(executable_tasks)} tasks in parallel: {[t.id for t in executable_tasks]}"
    )
    return {"plan": plan, "active_task_ids": [t.id for t in executable_tasks]}

async def execute_batch_node(
    state: AgentState, tools_map: Dict[str, List[Any]]
) -> Dict:
    """Executes all active tasks in parallel."""
    plan = state["plan"]
    active_ids = state["active_task_ids"]
    blackboard = state["shared_blackboard"]
    session_id = state.get("session_id")

    tasks_to_run = [t for t in plan.tasks if t.id in active_ids]

    # Prepare coroutines
    coroutines = []
    
    # Collect all tools for GENERAL agents
    all_tools = []
    for tool_list in tools_map.values():
        all_tools.extend(tool_list)
    # Remove duplicates if any (based on name)
    unique_tools = {t.name: t for t in all_tools}.values()
    all_tools = list(unique_tools)

    for task in tasks_to_run:
        # Determine tools based on agent type
        agent_type = task.assigned_agent
        tools = []
        if agent_type == AgentType.SHELL:
            tools = tools_map.get("shell", [])
        elif agent_type == AgentType.FILESYSTEM:
            tools = tools_map.get("filesystem", [])
        elif agent_type == AgentType.BROWSER:
            tools = tools_map.get("browser", [])
        elif agent_type == AgentType.WEB_SEARCH:
            tools = tools_map.get("web_search", [])
        elif agent_type == AgentType.GENERAL:
            # Give general agent all tools
            tools = all_tools
        else:
            # Fallback
            tools = all_tools

        # Use the factory to get the correct agent instance
        agent = get_agent_for_task(task, blackboard, tools, session_id=session_id)
        coroutines.append(agent.run())

    # Execute in parallel
    results = await asyncio.gather(*coroutines)

    # Process results
    new_summaries = []
    new_conclusions = []

    for res in results:
        t_id = res["task_id"]
        summary = res["summary"]
        
        # Update Task
        task = next(t for t in plan.tasks if t.id == t_id)
        task.status = TaskStatus.COMPLETED
        task.result = summary
        
        new_summaries.append(f"Task {t_id} ({task.description}): {summary}")
        # In a real system, we might extract structured conclusions here

    # Update Memory
    main_mem = state["main_memory"]
    main_mem.sub_agent_summaries.extend(new_summaries)
    
    # Update Blackboard (Simplified: just appending summaries as key conclusions for now)
    # Ideally, sub-agents should return specific conclusions to update the blackboard
    blackboard.key_conclusions.extend(new_summaries)

    return {
        "plan": plan, 
        "main_memory": main_mem,
        "shared_blackboard": blackboard,
        "active_task_ids": []
    }
