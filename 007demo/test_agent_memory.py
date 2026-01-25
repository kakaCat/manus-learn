import asyncio
import os
from unittest.mock import MagicMock, patch
from typing import Any, List

# Set dummy env vars before importing agent
os.environ["DEEPSEEK_API_KEY"] = "dummy"
os.environ["DEEPSEEK_BASE_URL"] = "http://dummy"

# Import agent (this will load .env but we overrode vars)
import agent
from agent import AgentState, MainMemory, SharedBlackboard, Plan, Task, TaskStatus, AgentType
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
    # Input data for _agenerate is 'messages' (List[BaseMessage])
    # But wait, in 'create_plan', the chain is prompt | llm | parser.
    # The input to llm is PromptValue or List[BaseMessage].
    
    if isinstance(input_data, list):
        # Check if it's Plan or Intent prompt (System message)
        last_msg = input_data[-1] if input_data else None
        first_msg = input_data[0] if input_data else None
        
        # Check Message content for formatting instructions and task info
        sys_content = ""
        all_content = ""
        for m in input_data:
            if isinstance(m, SystemMessage):
                sys_content += m.content
            if hasattr(m, "content"):
                all_content += str(m.content)
                
        if "Task" in sys_content and "goal" in sys_content: # Create Plan Prompt
             plan = Plan(
                goal="Test Goal",
                tasks=[
                    Task(id=1, description="Task 1", assigned_agent=AgentType.GENERAL),
                    Task(id=2, description="Task 2", assigned_agent=AgentType.GENERAL)
                ]
             )
             return AIMessage(content=plan.model_dump_json())
             
        elif "intent" in sys_content and "sandbox" in sys_content: # Intent Prompt
             from agent import IntentAnalysis
             intent = IntentAnalysis(intent="Test Intent", needs_sandbox=False, confidence=1.0)
             return AIMessage(content=intent.model_dump_json())

        # Sub-agent prompts
        if "Task: Task 1" in all_content:
             return AIMessage(content="Executed Task 1. Conclusion: A=1.")
        elif "Task: Task 2" in all_content:
             return AIMessage(content="Executed Task 2. Conclusion: B=2.")
             
    return AIMessage(content="Default Mock Response")

async def run_test():
    print("🧪 Starting Memory System Verification...")
    
    # Patch ChatOpenAI with Fake Class
    with patch("agent.ChatOpenAI", new=FakeChatOpenAI):
        
        # Patch MCPClientManager to avoid connecting to real MCP
        with patch("agent.MCPClientManager") as MockMCP:
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
                "user_input": "Run test",
                "main_memory": MainMemory(final_goal="Run test"),
                "shared_blackboard": SharedBlackboard(),
                "sub_agent_scratchpad": {},
                "active_task_ids": []
            }
            
            print("\n🏃 Running Graph...")
            final_state = None
            async for s in graph.astream(initial_state):
                for key, value in s.items():
                    print(f"  -> Node '{key}' finished.")
                    if key == "execute_batch":
                         # Check partial state
                         print(f"     Current Summaries: {value['main_memory'].sub_agent_summaries}")
                         final_state = value # Capture state at update
                    elif key == "scheduler":
                        pass
            
            print("\n✅ Execution Finished.")
            
            if final_state:
                 summaries = final_state['main_memory'].sub_agent_summaries
                 conclusions = final_state['shared_blackboard'].key_conclusions
                 print(f"\nFinal Summaries: {summaries}")
                 print(f"Final Conclusions: {conclusions}")
                 
                 assert len(summaries) == 2, "Should have 2 summaries"
                 assert "Task 1" in summaries[0]
                 assert "Task 2" in summaries[1]
                 print("🎉 Memory Hierarchy Verified!")
            else:
                 print("❌ Failed to capture final state.")

if __name__ == "__main__":
    asyncio.run(run_test())
