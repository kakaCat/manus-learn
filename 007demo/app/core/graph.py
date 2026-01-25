from functools import partial
from langgraph.graph import StateGraph, END, START

from app.core.state import AgentState
from app.models.schemas import TaskStatus
from app.core.planning_agent import analyze_intent, create_simple_plan, create_complex_plan
from app.core.execution import scheduler_node, execute_batch_node
from app.core.reflection import reflection_node

def create_graph_with_tools(
    shell_tools, filesystem_tools, browser_tools, web_search_tools, checkpointer=None
):
    workflow = StateGraph(AgentState)

    # Tool Map
    tools_map = {
        "shell": shell_tools,
        "filesystem": filesystem_tools,
        "browser": browser_tools,
        "web_search": web_search_tools,
    }

    # Helper for batch execution
    execute_batch = partial(execute_batch_node, tools_map=tools_map)

    # Add Nodes
    workflow.add_node("analyze_intent", analyze_intent)
    workflow.add_node("create_simple_plan", create_simple_plan)
    workflow.add_node("create_complex_plan", create_complex_plan)
    workflow.add_node("scheduler", scheduler_node)
    workflow.add_node("execute_batch", execute_batch)
    workflow.add_node("reflection", reflection_node)

    # Edges
    workflow.add_edge(START, "analyze_intent")
    
    # Conditional Routing for Planning
    def route_planning(state: AgentState):
        # Default to simple if complexity is missing
        complexity = state["main_memory"].complexity
        if complexity == "complex":
            return "create_complex_plan"
        return "create_simple_plan"

    workflow.add_conditional_edges(
        "analyze_intent",
        route_planning,
        {
            "create_simple_plan": "create_simple_plan", 
            "create_complex_plan": "create_complex_plan"
        }
    )

    # Both planners go to scheduler
    workflow.add_edge("create_simple_plan", "scheduler")
    workflow.add_edge("create_complex_plan", "scheduler")

    def route_scheduler(state: AgentState):
        if state.get("active_task_ids"):
            return "execute_batch"

        # No active tasks. Check if plan completed.
        plan = state["plan"]
        if plan and all(t.status == TaskStatus.COMPLETED for t in plan.tasks):
            return END
        
        # If plan is None or empty tasks, end
        if not plan or not plan.tasks:
            return END

        return END

    workflow.add_conditional_edges(
        "scheduler", route_scheduler, {"execute_batch": "execute_batch", END: END}
    )

    workflow.add_edge("execute_batch", "reflection")
    workflow.add_edge("reflection", "scheduler")

    return workflow.compile(checkpointer=checkpointer)
