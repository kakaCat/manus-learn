from app.models.schemas import Plan, TaskStatus

def print_todo_list(plan: Plan):
    """Prints the current Todo List with status."""
    print("\n📝 [Todo List]")
    for task in plan.tasks:
        status_icon = "⬜"
        if task.status == TaskStatus.COMPLETED:
            status_icon = "✅"
        elif task.status == TaskStatus.IN_PROGRESS:
            status_icon = "⏳"
        elif task.status == TaskStatus.FAILED:
            status_icon = "❌"

        deps = f" (Deps: {task.dependencies})" if task.dependencies else ""
        print(
            f"  {status_icon} {task.id}. {task.description} [{task.assigned_agent.value}]{deps}"
        )
    print("---------------------------------------------------")
