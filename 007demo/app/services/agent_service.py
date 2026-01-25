import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Ensure we are in the right directory or path is correct
import sys
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.graph import create_graph_with_tools
from app.models.schemas import MainMemory, SharedBlackboard
from app.infrastructure.mcp import MCPClientManager
from app.infrastructure.tools import web_search
from langgraph.checkpoint.memory import MemorySaver
import uuid
from langchain_core.messages import HumanMessage
from app.core.logger import SessionRecorder

load_dotenv()

class AgentService:
    def __init__(self):
        self.mcp_manager = MCPClientManager()
        self.graph = None
        self.checkpointer = MemorySaver()
        
    async def initialize(self):
        """Initialize the agent service by connecting to MCP and building the graph."""
        print("🔌 Connecting to MCP servers...")
        await self.mcp_manager.connect()
        
        print("🛠️  Loading tools...")
        # Note: In a real service, we might want to handle failures gracefully here
        try:
            shell_tools = await self.mcp_manager.get_tools("shell")
        except Exception:
            print("⚠️ Failed to load shell tools")
            shell_tools = []
            
        try:
            filesystem_tools = await self.mcp_manager.get_tools("filesystem")
        except Exception:
            print("⚠️ Failed to load filesystem tools")
            filesystem_tools = []
            
        try:
            browser_tools = await self.mcp_manager.get_tools("chrome")
        except Exception:
            print("⚠️ Failed to load browser tools")
            browser_tools = []
            
        web_search_tools = [web_search]
        
        print(f"✅ Tools loaded: Shell={len(shell_tools)}, FS={len(filesystem_tools)}, Browser={len(browser_tools)}")
        
        self.graph = create_graph_with_tools(
            shell_tools, filesystem_tools, browser_tools, web_search_tools, checkpointer=self.checkpointer
        )
        print("✅ AgentService Initialized")

    async def shutdown(self):
        """Cleanup resources."""
        await self.mcp_manager.close()
        print("🛑 AgentService Shutdown")

    async def run_task_stream(self, user_input: str, session_id: Optional[str] = None):
        """Run a task and yield events."""
        if not self.graph:
            raise RuntimeError("AgentService not initialized")
            
        thread_id = session_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        # Initialize Session Recorder
        recorder = SessionRecorder(thread_id)
        recorder.log_chat("User", user_input)
        
        # Check if state exists for this thread
        current_state = await self.graph.aget_state(config)
        
        if current_state.values:
            # Continue existing session
            # We just append the new user input message
            inputs = {
                "messages": [HumanMessage(content=user_input)],
                "user_input": user_input,
                "session_id": thread_id
            }
        else:
            # New session
            inputs = {
                "messages": [HumanMessage(content=user_input)],
                "user_input": user_input,
                "session_id": thread_id,
                "main_memory": MainMemory(final_goal=user_input),
                "shared_blackboard": SharedBlackboard(),
                "sub_agent_scratchpad": {},
                "active_task_ids": [],
                "plan": None
            }
            
        # Yield thread_id as the first event for client reference
        yield {"meta": {"session_id": thread_id}}
        
        async for event in self.graph.astream(inputs, config=config):
            # Capture output events for logging
            for node_name, node_state in event.items():
                if node_name == "reflection":
                     # Snapshot state after reflection
                     recorder.save_state(node_state)
                
                # Log AI response if present
                # Depending on how the graph yields messages
                pass
                
            yield event
