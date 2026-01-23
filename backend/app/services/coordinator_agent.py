"""
DeepAgent Architecture - Main Agent + SubAgents System.

This implements a hierarchical agent architecture:
- Main Agent (Coordinator): Intelligent routing and task coordination
- SubAgents: Specialized agents for different MCP server domains
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum

from app.core.config import settings
from app.core.llm import get_llm
from app.services.mcp_client import mcp_manager

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of subagents in the DeepAgent system."""

    COORDINATOR = "coordinator"  # Main routing agent
    SHELL = "shell"  # Shell command execution
    FILESYSTEM = "filesystem"  # File operations
    BROWSER = "chrome"  # Web browser automation
    MANAGER = "manager"  # MCP tool management


class SubAgent:
    """Base class for specialized subagents."""

    def __init__(
        self,
        name: str,
        agent_type: AgentType,
        mcp_servers: List[str],
        system_prompt: str,
    ):
        self.name = name
        self.agent_type = agent_type
        self.mcp_servers = mcp_servers
        self.system_prompt = system_prompt
        self.llm = get_llm()

    async def process_task(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a task specific to this subagent's domain.

        Args:
            user_input: User's task description
            context: Additional context information

        Returns:
            Subagent response
        """
        try:
            # Create specialized prompt for this subagent
            context_info = ""
            if context:
                context_info = f"\nContext: {context}"

            full_prompt = f"{self.system_prompt}{context_info}\n\nUser Task: {user_input}\n\nResponse:"

            # Get LLM response
            from langchain_core.messages import HumanMessage

            messages = [HumanMessage(content=full_prompt)]
            response = await self.llm.ainvoke(messages)

            return (
                str(response.content)
                if response.content
                else "Task completed but no output generated."
            )

        except Exception as e:
            logger.error(f"SubAgent {self.name} error: {e}")
            return f"I encountered an error while processing your request: {str(e)}"

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a specific MCP tool.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            # Determine which MCP server this tool belongs to
            server_name = self._get_server_for_tool(tool_name)
            if not server_name:
                raise ValueError(f"Unknown tool: {tool_name}")

            # Execute the tool
            result = await mcp_manager.call_tool(server_name, tool_name, arguments)
            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            raise

    def _get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Map tool name to MCP server."""
        # This would need a proper mapping based on actual MCP tool definitions
        # For now, use simple heuristics
        if any(keyword in tool_name.lower() for keyword in ["execute", "run", "shell"]):
            return "shell"
        elif any(
            keyword in tool_name.lower()
            for keyword in ["read", "write", "list", "file"]
        ):
            return "filesystem"
        elif any(
            keyword in tool_name.lower()
            for keyword in ["navigate", "browser", "page", "screenshot"]
        ):
            return "chrome"
        elif any(
            keyword in tool_name.lower()
            for keyword in ["install", "list", "status", "mcp"]
        ):
            return "manager"
        return None


class CoordinatorAgent:
    """Main agent that coordinates tasks across all subagents."""

    def __init__(self):
        self.subagents: Dict[AgentType, SubAgent] = {}
        self.llm = get_llm()
        self._initialize_subagents()

    def _initialize_subagents(self):
        """Initialize all subagents."""

        # Shell SubAgent
        self.subagents[AgentType.SHELL] = SubAgent(
            name="Shell Commander",
            agent_type=AgentType.SHELL,
            mcp_servers=["shell"],
            system_prompt=(
                "You are the Shell Commander SubAgent in the DeepAgent system.\n"
                "Your specialization: Executing terminal commands and system operations.\n"
                "Capabilities:\n"
                "- Run shell commands (ls, cd, mkdir, rm, etc.)\n"
                "- Execute scripts and programs\n"
                "- Monitor system processes\n"
                "- Perform system administration\n"
                "Safety: Be extremely careful with destructive operations. Always confirm before deletion or system changes."
            ),
        )

        # Filesystem SubAgent
        self.subagents[AgentType.FILESYSTEM] = SubAgent(
            name="File System Manager",
            agent_type=AgentType.FILESYSTEM,
            mcp_servers=["filesystem"],
            system_prompt=(
                "You are the File System Manager SubAgent in the DeepAgent system.\n"
                "Your specialization: File operations and workspace management.\n"
                "Capabilities:\n"
                "- Read file contents\n"
                "- Create and write files\n"
                "- List directory contents\n"
                "- Navigate the file system\n"
                "Guidelines: Work within workspace, preserve data, use proper encoding."
            ),
        )

        # Browser SubAgent
        self.subagents[AgentType.BROWSER] = SubAgent(
            name="Chrome Browser Controller",
            agent_type=AgentType.BROWSER,
            mcp_servers=["chrome"],
            system_prompt=(
                "You are the Chrome Browser Controller SubAgent in the DeepAgent system.\n"
                "Your specialization: Web browser automation and control.\n"
                "Capabilities:\n"
                "- Create browser tabs/pages\n"
                "- Navigate to web pages\n"
                "- Take screenshots\n"
                "- Interact with web elements\n"
                "Notes: Operations may be slow, handle timeouts gracefully, respect terms of service."
            ),
        )

        # Manager SubAgent
        self.subagents[AgentType.MANAGER] = SubAgent(
            name="MCP Manager",
            agent_type=AgentType.MANAGER,
            mcp_servers=["manager"],
            system_prompt=(
                "You are the MCP Manager SubAgent in the DeepAgent system.\n"
                "Your specialization: MCP tool lifecycle management.\n"
                "Capabilities:\n"
                "- Install new MCP tools\n"
                "- List available tools\n"
                "- Check system status\n"
                "- Manage tool installations\n"
                "Important: Always inform about container restart requirements."
            ),
        )

    async def route_task(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze user input and route to appropriate subagent.

        Args:
            user_input: User's task description
            context: Additional context

        Returns:
            Dict with routing decision and result
        """
        try:
            # Analyze the task to determine which subagent should handle it
            target_agent = self._analyze_task(user_input)

            logger.info(f"Coordinator routing task to {target_agent.value} subagent")

            # Get the appropriate subagent
            subagent = self.subagents.get(target_agent)
            if not subagent:
                return {
                    "agent": "coordinator",
                    "error": f"No subagent available for task type: {target_agent.value}",
                }

            # Execute the task with the subagent
            result = await subagent.process_task(user_input, context)

            return {
                "agent": target_agent.value,
                "subagent": subagent.name,
                "result": result,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Coordinator routing error: {e}")
            return {"agent": "coordinator", "error": str(e), "success": False}

    def _analyze_task(self, user_input: str) -> AgentType:
        """
        Analyze user input to determine the appropriate subagent.

        This is a simple rule-based routing. In production, this could use
        more sophisticated NLP or ML-based classification.
        """
        input_lower = user_input.lower()

        # Shell-related keywords
        shell_keywords = [
            "run",
            "execute",
            "command",
            "shell",
            "ls",
            "cd",
            "mkdir",
            "rm",
            "ps",
            "top",
        ]
        if any(keyword in input_lower for keyword in shell_keywords):
            return AgentType.SHELL

        # File-related keywords
        file_keywords = [
            "file",
            "read",
            "write",
            "create",
            "list",
            "directory",
            "folder",
            "text",
            "document",
        ]
        if any(keyword in input_lower for keyword in file_keywords):
            return AgentType.FILESYSTEM

        # Browser-related keywords
        browser_keywords = [
            "browser",
            "web",
            "page",
            "navigate",
            "screenshot",
            "chrome",
            "website",
            "url",
        ]
        if any(keyword in input_lower for keyword in browser_keywords):
            return AgentType.BROWSER

        # MCP management keywords
        manager_keywords = ["install", "tool", "mcp", "manager", "available", "status"]
        if any(keyword in input_lower for keyword in manager_keywords):
            return AgentType.MANAGER

        # Default to shell for general tasks
        return AgentType.SHELL

    def list_subagents(self) -> Dict[str, Dict]:
        """List all available subagents with their capabilities."""
        return {
            agent_type.value: {
                "name": subagent.name,
                "mcp_servers": subagent.mcp_servers,
                "description": subagent.system_prompt.split("\n")[1]
                if "\n" in subagent.system_prompt
                else subagent.system_prompt,
            }
            for agent_type, subagent in self.subagents.items()
        }


# Global Coordinator instance
coordinator_agent = CoordinatorAgent()
