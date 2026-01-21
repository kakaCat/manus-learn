"""LangChain agent with MCP tools integration - Updated with MCP Manager support."""

import logging
from typing import Any, Dict, List, Optional

from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool

from mcp_client import mcp_manager
from llm import llm_manager

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
        """Execute the MCP tool."""
        try:
            result = await mcp_manager.call_tool(
                server_name=self.server_name,
                tool_name=self.tool_name,
                arguments=kwargs,
            )

            # Extract text content from MCP response
            if isinstance(result, list) and len(result) > 0:
                return result[0].text
            return str(result)

        except Exception as e:
            error_msg = f"Error calling {self.tool_name}: {str(e)}"
            logger.error(error_msg)
            return error_msg


async def create_mcp_tools() -> List[StructuredTool]:
    """
    Create LangChain tools from all MCP servers including MCP Manager.

    Returns:
        List of LangChain Tool instances
    """
    logger.info("Creating LangChain tools from MCP servers...")

    tools = []

    # Define which tools to expose to the agent
    tool_configs = [
        # ==================== MCP Manager Tools ====================
        {
            "server": "manager",
            "name": "list_available_mcps",
            "description": (
                "List all available MCP tools in the marketplace. "
                "Use this when user needs a capability you don't have. "
                "Optional arg: category (str) to filter"
            ),
        },
        {
            "server": "manager",
            "name": "list_installed_mcps",
            "description": "List currently installed MCP tools. No arguments.",
        },
        {
            "server": "manager",
            "name": "install_mcp",
            "description": (
                "Install a new MCP tool to gain new capabilities. "
                "Required arg: mcp_id (str). "
                "After install, user must restart container."
            ),
        },
        {
            "server": "manager",
            "name": "get_mcp_status",
            "description": "Check MCP servers running status. No arguments.",
        },

        # ==================== Shell MCP Tools ====================
        {
            "server": "shell",
            "name": "execute_command",
            "description": (
                "Execute shell command in sandbox. "
                "Args: command (str), args (list), cwd (str, optional)"
            ),
        },
        {
            "server": "shell",
            "name": "get_running_processes",
            "description": "Get running processes with CPU/memory. No args.",
        },

        # ==================== Filesystem MCP Tools ====================
        {
            "server": "filesystem",
            "name": "read_file",
            "description": "Read file in workspace. Args: path (str)",
        },
        {
            "server": "filesystem",
            "name": "write_file",
            "description": "Write file. Args: path (str), content (str)",
        },
        {
            "server": "filesystem",
            "name": "list_directory",
            "description": "List directory. Args: path (str, default '.')",
        },

        # ==================== Chrome MCP Tools ====================
        {
            "server": "chrome",
            "name": "launch_browser",
            "description": "Launch Chrome browser. Args: headless (bool)",
        },
        {
            "server": "chrome",
            "name": "navigate_to_url",
            "description": "Navigate to URL. Args: url (str)",
        },
        {
            "server": "chrome",
            "name": "get_page_content",
            "description": "Get page content. Args: selector (str, default 'body')",
        },
        {
            "server": "chrome",
            "name": "take_screenshot",
            "description": "Screenshot. Args: filename (str)",
        },
    ]

    for config in tool_configs:
        wrapper = MCPToolWrapper(
            server_name=config["server"],
            tool_name=config["name"],
            tool_description=config["description"],
        )

        tool = StructuredTool.from_function(
            coroutine=wrapper.execute,
            name=f"{config['server']}_{config['name']}",
            description=config["description"],
        )

        tools.append(tool)

    logger.info(f"Created {len(tools)} tools from MCP servers")
    return tools


class SandboxAgent:
    """LangChain agent with MCP tools for sandbox control."""

    def __init__(self):
        """Initialize the sandbox agent."""
        self.llm = None
        self.agent = None
        self.tools: List[StructuredTool] = []

    async def initialize(self):
        """Initialize the agent with LLM and tools."""
        logger.info("Initializing Sandbox Agent...")

        self.llm = llm_manager.get_or_create_llm()
        self.tools = await create_mcp_tools()

        system_message = (
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

        self.agent = create_react_agent(
            self.llm,
            self.tools
        )
        self.system_message = system_message

        logger.info("Agent initialized with MCP Manager support")

    async def run(self, user_input: str, chat_history: Optional[List] = None) -> str:
        """Run agent with user input."""
        if self.agent is None:
            await self.initialize()

        logger.info(f"Running agent: {user_input}")

        # Include system message and user input
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": user_input}
        ]

        result = await self.agent.ainvoke({
            "messages": messages
        })

        # Extract final message from result
        result_messages = result.get("messages", [])
        if result_messages:
            final_message = result_messages[-1]
            if hasattr(final_message, "content"):
                return final_message.content
            elif isinstance(final_message, dict):
                return final_message.get("content", str(final_message))

        return str(result)


# Global agent instance
sandbox_agent = SandboxAgent()
