import asyncio
import os
from unittest.mock import MagicMock, patch
from typing import Any, List
import json

# Set dummy env vars
os.environ["DEEPSEEK_API_KEY"] = "dummy"
os.environ["DEEPSEEK_BASE_URL"] = "http://dummy"

import agent
from agent import AgentState, MainMemory, SharedBlackboard, Plan, Task, TaskStatus, AgentType, IntentAnalysis
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

class FakeChatOpenAI(BaseChatModel):
    def __init__(self, *args, **kwargs):
        super().__init__()
        
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Sync"))])
        
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        res = await mock_ainvoke(messages, **kwargs)
        return ChatResult(generations=[ChatGeneration(message=res)])

    @property
    def _llm_type(self):
        return "fake-chat-model"

    def bind_tools(self, tools):
        return self

async def mock_ainvoke(input_data, **kwargs):
    if isinstance(input_data, list):
        sys_content = ""
        for m in input_data:
            if hasattr(m, "content"):
                sys_content += str(m.content)
                
        # 1. Intent Analysis
        if "intent" in sys_content and "sandbox" in sys_content:
             intent = IntentAnalysis(intent="Research Python and Rust", needs_sandbox=False)
             return AIMessage(content=intent.model_dump_json())

        # 2. Plan Creation
        if "Task" in sys_content and "Goal:" in sys_content:
             plan = Plan(
                goal="Research Python and Rust",
                tasks=[
                    Task(id=1, description="Research Python", assigned_agent=AgentType.WEB_SEARCH),
                    Task(id=2, description="Research Rust", assigned_agent=AgentType.WEB_SEARCH),
                    Task(id=3, description="Compare Languages", assigned_agent=AgentType.GENERAL, dependencies=[1, 2])
                ]
             )
             return AIMessage(content=plan.model_dump_json())

        # 3. Sub-Agents
        if "Task: Research Python" in sys_content:
             return AIMessage(content="Found: Python is a dynamic language created in 1991.")
        elif "Task: Research Rust" in sys_content:
             return AIMessage(content="Found: Rust is a systems language created in 2010, focusing on safety.")
        elif "Task: Compare Languages" in sys_content:
             if "1991" in sys_content and "2010" in sys_content:
                 return AIMessage(content="Comparison: Python (1991) is older and dynamic, Rust (2010) is newer and static/safe.")
             else:
                 return AIMessage(content="Comparison: Both are popular languages.")
             
    return AIMessage(content="Default Mock Response")

async def run_demo():
    print("\n🚀 Starting Agent 007 Demo (Parallel Execution)...")
    print("---------------------------------------------------")
    
    with patch("agent.ChatOpenAI", new=FakeChatOpenAI):
        with patch("agent.MCPClientManager") as MockMCP:
            # Mock MCP
            mock_mcp = MockMCP.return_value
            mock_mcp.connect = asyncio.Future()
            mock_mcp.connect.set_result(None)
            mock_mcp.get_tools.return_value = asyncio.Future()
            mock_mcp.get_tools.return_value.set_result([])
            mock_mcp.close = asyncio.Future()
            mock_mcp.close.set_result(None)

            # Create Graph
            graph = agent.create_graph_with_tools([], [], [], [])
            
            # Initial State
            initial_state = {
                "messages": [],
                "user_input": "Research Python and Rust",
                "main_memory": MainMemory(final_goal="Research Python and Rust"),
                "shared_blackboard": SharedBlackboard(),
                "sub_agent_scratchpad": {},
                "active_task_ids": []
            }
            
            print(f"👤 User: {initial_state['user_input']}")
            
            async for s in graph.astream(initial_state):
                for key, value in s.items():
                    if key == "execute_batch":
                         print(f"\n✨ [System] Batch Execution Completed.")
                         mem = value['main_memory']
                         bb = value['shared_blackboard']
                         print(f"   📝 Level A (Main Memory) Summaries: {len(mem.sub_agent_summaries)}")
                         for summary in mem.sub_agent_summaries[-len(value.get('active_task_ids', [])):]: # Just show new ones
                             print(f"      - {summary}")
                         
                    elif key == "scheduler":
                         # Scheduler doesn't modify state significantly in output, but we can see it triggered
                         pass
            
            print("\n---------------------------------------------------")
            print("✅ Demo Finished.")

if __name__ == "__main__":
    asyncio.run(run_demo())
