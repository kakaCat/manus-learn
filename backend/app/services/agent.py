"""LangGraph agent with MCP tools integration (LangChain 1.X)."""

import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import Field, create_model

from app.services.mcp_client import mcp_manager
from app.core.llm import llm_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


class MCPToolWrapper:
    """Wrapper to convert MCP tools to LangChain tools."""

    def __init__(self, server_name: str, tool_name: str, tool_description: str):
        """
        Initialize MCP tool wrapper.

        Args:
            server_name: MCP server name (shell, filesystem, chrome, manager)
            tool_name: Tool name on the MCP server
            tool_description: Tool description for LLM
        """
        self.server_name = server_name
        self.tool_name = tool_name
        self.tool_description = tool_description

    async def execute(self, **kwargs) -> str:
        """
        Execute the MCP tool.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool execution result as string
        """
        try:
            # Filter out None values - MCP tools don't accept None for optional parameters
            filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

            logger.debug(f"Executing {self.server_name}.{self.tool_name} with args: {filtered_kwargs}")

            result = await mcp_manager.call_tool(
                server_name=self.server_name,
                tool_name=self.tool_name,
                arguments=filtered_kwargs,
            )

            # Extract text content from MCP CallToolResult
            if hasattr(result, 'content') and result.content:
                first_content = result.content[0]
                if hasattr(first_content, 'text'):
                    return first_content.text
                return str(first_content)

            return str(result)

        except Exception as e:
            error_msg = f"Error calling {self.tool_name}: {str(e)}"
            logger.error(error_msg)
            return error_msg


async def create_mcp_tools() -> List[StructuredTool]:
    """
    Create LangChain tools from all MCP servers.

    Returns:
        List of LangChain StructuredTool instances
    """
    logger.info("Creating LangChain tools from MCP servers...")

    tools = []

    # Tool configurations with schemas
    tool_configs = [
        # ==================== MCP Manager Tools ====================
        {
            "server": "manager",
            "name": "list_available_mcps",
            "description": "List all available MCP tools in the marketplace that can be installed",
            "args_schema": {},
        },
        {
            "server": "manager",
            "name": "list_installed_mcps",
            "description": "List currently installed MCP tools",
            "args_schema": {},
        },
        {
            "server": "manager",
            "name": "install_mcp",
            "description": "Install a new MCP tool to gain new capabilities. User must restart container after installation.",
            "args_schema": {"mcp_id": {"type": "string", "description": "ID of the MCP to install", "required": True}},
        },
        {
            "server": "manager",
            "name": "get_mcp_status",
            "description": "Check status of all MCP servers",
            "args_schema": {},
        },
        # ==================== Shell MCP Tools ====================
        {
            "server": "shell",
            "name": "execute_command",
            "description": "Execute a shell command in the sandbox environment",
            "args_schema": {
                "command": {"type": "string", "description": "Command to execute (e.g., 'ls', 'echo', 'python3')", "required": True},
                "args": {"type": "array", "items": {"type": "string"}, "description": "Arguments for the command"},
                "cwd": {"type": "string", "description": "Working directory (optional)"},
            },
        },
        {
            "server": "shell",
            "name": "get_running_processes",
            "description": "Get list of running processes with CPU and memory usage",
            "args_schema": {},
        },
        # ==================== Filesystem MCP Tools ====================
        {
            "server": "filesystem",
            "name": "read_file",
            "description": "Read contents of a file in the workspace",
            "args_schema": {"path": {"type": "string", "description": "Path to the file to read", "required": True}},
        },
        {
            "server": "filesystem",
            "name": "write_file",
            "description": "Write content to a file in the workspace",
            "args_schema": {
                "path": {"type": "string", "description": "Path to the file to write", "required": True},
                "content": {"type": "string", "description": "Content to write to the file", "required": True},
            },
        },
        {
            "server": "filesystem",
            "name": "list_directory",
            "description": "List files and directories in a path",
            "args_schema": {"path": {"type": "string", "description": "Directory path (default: '.')"}},
        },
        # ==================== Chrome MCP Tools ====================
        {
            "server": "chrome",
            "name": "new_page",
            "description": "Create a new Chrome browser page/tab",
            "args_schema": {},
        },
        {
            "server": "chrome",
            "name": "list_pages",
            "description": "List all open Chrome browser pages/tabs",
            "args_schema": {},
        },
        {
            "server": "chrome",
            "name": "navigate_page",
            "description": "Navigate current Chrome page to a URL",
            "args_schema": {"url": {"type": "string", "description": "URL to navigate to", "required": True}},
        },
        {
            "server": "chrome",
            "name": "take_screenshot",
            "description": "Take a screenshot of the current Chrome page",
            "args_schema": {"filename": {"type": "string", "description": "Filename for screenshot (optional)"}},
        },
        {
            "server": "chrome",
            "name": "select_page",
            "description": "Select a Chrome page/tab to work with",
            "args_schema": {"index": {"type": "integer", "description": "Index of the page to select", "required": True}},
        },
    ]

    # Create tools from configs
    for config in tool_configs:
        wrapper = MCPToolWrapper(
            server_name=config["server"],
            tool_name=config["name"],
            tool_description=config["description"],
        )

        # Build Pydantic model for arguments
        args_schema = config.get("args_schema", {})
        field_definitions = {}

        if args_schema:
            for arg_name, arg_spec in args_schema.items():
                arg_type = str  # Default type
                arg_desc = arg_spec.get("description", "")
                is_required = arg_spec.get("required", False)

                # Type mapping
                if arg_spec.get("type") == "integer":
                    arg_type = int
                elif arg_spec.get("type") == "array":
                    arg_type = Optional[list]
                    is_required = False

                # Field definition
                if is_required:
                    field_definitions[arg_name] = (arg_type, Field(description=arg_desc))
                else:
                    field_definitions[arg_name] = (Optional[arg_type], Field(default=None, description=arg_desc))

            ArgsModel = create_model(
                f"{config['server']}_{config['name']}_args",
                **field_definitions
            )
        else:
            # No arguments model
            ArgsModel = create_model(f"{config['server']}_{config['name']}_args")

        # Create StructuredTool
        tool = StructuredTool.from_function(
            coroutine=wrapper.execute,
            name=f"{config['server']}_{config['name']}",
            description=config["description"],
            args_schema=ArgsModel,
        )

        tools.append(tool)

    logger.info(f"Created {len(tools)} tools from MCP servers")
    return tools


class SandboxAgent:
    """
    LangGraph ReAct agent with MCP tools for sandbox control.

    Features:
    - Memory persistence using MemorySaver checkpointer
    - MCP tool integration
    - Thread-based conversation isolation
    """

    def __init__(self):
        """Initialize the sandbox agent."""
        self.llm = None
        self.agent = None
        self.tools: List[StructuredTool] = []
        self.checkpointer = MemorySaver()  # In-memory checkpointer for development
        self.system_prompt = (
            "You are an AI assistant with sandbox access and self-improvement capability.\n"
            "\n"
            "🎯 KEY FEATURE: You can install new tools!\n"
            "When user needs something you can't do:\n"
            "1. Use manager_list_available_mcps to browse marketplace\n"
            "2. Use manager_install_mcp with mcp_id to install\n"
            "3. Tell user to run: docker-compose restart\n"
            "\n"
            "Available capabilities:\n"
            "- MCP Manager: install/manage tools\n"
            "- Shell: execute commands\n"
            "- Files: read/write in workspace\n"
            "- Browser: Chrome automation\n"
            "\n"
            "Be proactive: if you need search, install brave-search!\n"
            "If you need memory, install memory MCP!"
        )

    async def initialize(self):
        """Initialize the agent with LLM, tools, and checkpointer."""
        logger.info("Initializing Sandbox Agent (LangGraph + MemorySaver)...")

        # Get LLM instance
        self.llm = llm_manager.get_or_create_llm()

        # Create MCP tools
        self.tools = await create_mcp_tools()

        # Create prompt template with system message
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("placeholder", "{messages}"),
        ])

        # Create ReAct agent with checkpointer for memory
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            prompt=prompt,
            checkpointer=self.checkpointer,  # Enable memory
        )

        logger.info(f"Agent initialized with {len(self.tools)} tools and MemorySaver checkpointer")

    async def run(
        self,
        user_input: str,
        thread_id: Optional[str] = None,
        chat_history: Optional[List] = None,
    ) -> str:
        """
        Run agent with user input.

        Args:
            user_input: User message
            thread_id: Thread ID for conversation isolation (auto-generated if None)
            chat_history: Legacy chat history (deprecated, use thread_id instead)

        Returns:
            Agent response string
        """
        if self.agent is None:
            await self.initialize()

        # Generate thread ID if not provided
        if thread_id is None:
            thread_id = str(uuid4())
            logger.info(f"Generated new thread ID: {thread_id}")

        logger.info(f"Running agent (thread={thread_id}): {user_input}")

        # Prepare messages
        messages = []

        # Add legacy chat history if provided (for backward compatibility)
        if chat_history:
            for msg in chat_history:
                role = msg.get("role") if isinstance(msg, dict) else msg.role
                content = msg.get("content") if isinstance(msg, dict) else msg.content

                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))

        # Add current user input
        messages.append(HumanMessage(content=user_input))

        # Invoke agent with thread configuration
        config = RunnableConfig(
            configurable={"thread_id": thread_id}
        )

        result = await self.agent.ainvoke(
            {"messages": messages},
            config=config
        )

        # Extract final message
        result_messages = result.get("messages", [])
        if result_messages:
            final_message = result_messages[-1]
            if hasattr(final_message, "content"):
                return final_message.content
            elif isinstance(final_message, dict):
                return final_message.get("content", str(final_message))

        return str(result)

    def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation state for a thread.

        Args:
            thread_id: Thread ID

        Returns:
            Thread state dict or None
        """
        try:
            config = RunnableConfig(configurable={"thread_id": thread_id})
            state = self.checkpointer.get(config)
            return state
        except Exception as e:
            logger.error(f"Error getting thread state: {e}")
            return None


# Global agent instance
sandbox_agent = SandboxAgent()
