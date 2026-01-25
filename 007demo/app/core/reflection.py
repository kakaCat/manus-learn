import os
from typing import Dict
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.core.state import AgentState
from app.core.utils import print_todo_list
from app.models.schemas import TaskStatus

async def reflection_node(state: AgentState) -> Dict:
    """Main Agent reflects on the progress."""
    print(f"\n🤔 [Main Agent] Reflecting on progress...")

    plan = state["plan"]
    main_mem = state["main_memory"]
    print_todo_list(plan)

    # --- Level A Memory Update (LangChain ConversationSummaryMemory) ---
    # Identify new summaries to process
    all_summaries = main_mem.sub_agent_summaries
    start_idx = main_mem.summarized_idx
    new_summaries = all_summaries[start_idx:]

    if new_summaries:
        print(f"  🧠 Processing {len(new_summaries)} new sub-agent reports into Global Summary...")
        
        llm = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            temperature=0,
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
        )
        
        # Prepare new lines
        new_lines = ""
        for summary in new_summaries:
            new_lines += f"Sub-Agent Report: {summary}\nAI: Acknowledged.\n"
            
        current_summary = main_mem.global_summary
        
        template = """Progressively summarize the lines of conversation provided, adding to the previous summary returning a new summary.
EXAMPLE
Current summary:
The human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good.

New lines of conversation:
Human: Why do you think artificial intelligence is a force for good?
AI: Because artificial intelligence will help humans reach their full potential.

New summary:
The human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good because it will help humans reach their full potential.
END OF EXAMPLE

Current summary:
{summary}

New lines of conversation:
{new_lines}

New summary:"""
        
        prompt = PromptTemplate(template=template, input_variables=["summary", "new_lines"])
        chain = prompt | llm
        
        response = chain.invoke({"summary": current_summary, "new_lines": new_lines})
        new_global_summary = response.content
        
        main_mem.global_summary = new_global_summary
        main_mem.summarized_idx = len(all_summaries)
        
        print(f"  📝 Updated Global Summary: {new_global_summary[:100]}...")

    # Check completion
    if all(t.status == TaskStatus.COMPLETED for t in plan.tasks):
        print("🎉 All tasks completed!")
        return {"main_memory": main_mem}

    return {"main_memory": main_mem}
