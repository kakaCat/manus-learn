
import asyncio
import os
import sys
import json
from unittest.mock import MagicMock, patch
from typing import Any, List, Dict

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_core.messages import AIMessage, SystemMessage, BaseMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

# Mock ChatModel to avoid real API calls
class FakeChatOpenAI(BaseChatModel):
    def __init__(self, *args, **kwargs):
        super().__init__()
        
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        # Default sync generate
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Sync"))])
        
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        return await self.mock_ainvoke(messages, **kwargs)

    async def mock_ainvoke(self, input_data, **kwargs):
        # Determine context based on input messages
        content_str = ""
        if isinstance(input_data, list):
            for m in input_data:
                if hasattr(m, "content"):
                    content_str += str(m.content)
        
        # 1. Intent Analysis
        # Check if the system prompt mentions "Intent Analysis" or returns IntentAnalysis format
        if "Intent Analysis" in content_str or "needs_sandbox" in content_str:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=json.dumps({
                "intent": "Run memory test",
                "complexity": "simple",
                "theme": "general",
                "needs_sandbox": False
            })))])

        # 2. Planning Response
        if "creating a plan based on the user's message" in content_str or "CreatePlanResponse" in content_str:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=json.dumps({
                "message": "I will create a plan to test the memory.",
                "language": "English",
                "title": "Memory Test Plan",
                "goal": "Test Goal",
                "steps": [
                    {"id": "1", "description": "Task 1"}
                ]
            })))])

        # 3. Execution Response (Sub-Agent)
        if "Task 1" in content_str:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Executed Task 1 successfully. Result: A=1."))])
        if "Task 2" in content_str:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Executed Task 2 successfully. Result: B=2."))])
            
        # 4. Reflection/Summary Response
        if "Progressively summarize" in content_str or "New lines of conversation" in content_str:
             return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Global Summary: Tasks 1 and 2 completed."))])

        # Fallback
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Default Mock Response"))])

    @property
    def _llm_type(self):
        return "fake-chat-model"

    def bind_tools(self, tools):
        return self

# Import project modules
from app.core.graph import create_graph_with_tools
from app.models.schemas import MainMemory, SharedBlackboard, Task, TaskStatus
from app.core.state import AgentState

@patch("app.core.planning_agent.ChatOpenAI", new=FakeChatOpenAI)
# @patch("app.core.execution.ChatOpenAI", new=FakeChatOpenAI) # No longer needed as execution delegates to SubAgent
@patch("app.core.agents.base.ChatOpenAI", new=FakeChatOpenAI) # Added patch for SubAgent
@patch("app.core.reflection.ChatOpenAI", new=FakeChatOpenAI) 
async def run_test():
    print("🧪 Starting Memory Refactor Verification...")
    
    # Setup State
    initial_state = {
        "messages": [],
        "user_input": "Run memory test",
        "main_memory": None, # Let intent node initialize it
        "shared_blackboard": None,
        "sub_agent_scratchpad": {},
        "active_task_ids": [],
        "plan": None
    }

    # Create Graph
    graph = create_graph_with_tools([], [], [], [])
    
    # Run Graph
    print("🚀 Running Graph...")
    async for event in graph.astream(initial_state):
        for key, value in event.items():
            print(f"  📍 Node: {key}")
            if key == "reflection":
                mem = value['main_memory']
                print(f"     Global Summary: '{mem.global_summary}'")
                print(f"     Summarized Index: {mem.summarized_idx}")
                
                # Check if summary was updated
                if mem.global_summary:
                    print("     ✅ Global Summary populated via ConversationSummaryMemory!")
                else:
                    print("     ⚠️ Global Summary is empty.")
            
            if key == "execution":
                # Check if sub-agent summaries are present
                mem = value['main_memory']
                print(f"     Sub-Agent Summaries Count: {len(mem.sub_agent_summaries)}")

    print("🏁 Test Completed.")

if __name__ == "__main__":
    asyncio.run(run_test())
