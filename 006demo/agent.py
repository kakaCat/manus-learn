import asyncio
import os
import sys
import json
import readline  # Enable command history
from datetime import datetime
from typing import List, Optional, TypedDict, Annotated, Dict, Any
from enum import Enum
from functools import partial
from pydantic import BaseModel, Field
import aiohttp
from bs4 import BeautifulSoup

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    BaseMessage,
    AIMessage,
    ToolMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.tools import tool, StructuredTool
import httpx
from bs4 import BeautifulSoup
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables
from pathlib import Path

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# --- Global MCP Session ---
# Managed by MCPClientManager in main()

# --- Web Search Tools ---


@tool
async def web_search(query: str, num_results: int = 8) -> str:
    """
    Search the web using DuckDuckGo (with fallback to mock results).

    Args:
        query: Search query
        num_results: Number of results to return (default: 8, max: 20)

    Returns:
        Search results formatted as text
    """
    # Limit num_results
    num_results = min(max(num_results, 1), 20)

    try:
        import urllib.parse

        # DuckDuckGo search URL
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

        # Find search results
        results = []
        result_divs = soup.find_all("div", class_="result")

        for i, div in enumerate(result_divs[:num_results], 1):
            # Extract title
            title_elem = div.find("a", class_="result__a")
            title = title_elem.get_text(strip=True) if title_elem else "No title"

            # Extract URL
            url = (
                title_elem["href"] if title_elem and "href" in title_elem.attrs else ""
            )

            # Extract snippet
            snippet_elem = div.find("a", class_="result__snippet")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            if title and url:
                results.append(f"{i}. **{title}**\n   URL: {url}\n   {snippet[:300]}\n")

        if results:
            return "\n".join(results)
        else:
            # Fallback to mock results for testing
            return _mock_web_search_results(query, num_results)

    except Exception as e:
        # Fallback to mock results on any error
        print(f"Web search failed, using mock results: {e}")
        return _mock_web_search_results(query, num_results)


def _mock_web_search_results(query: str, num_results: int) -> str:
    """Generate mock search results for testing purposes."""
    mock_results = [
        {
            "title": f"Latest {query} Developments",
            "url": f"https://example.com/{query.replace(' ', '-')}",
            "snippet": f"Recent advancements in {query} technology and research findings.",
        },
        {
            "title": f"{query} Best Practices Guide",
            "url": f"https://example.com/{query.replace(' ', '-')}-guide",
            "snippet": f"Comprehensive guide covering {query} implementation and best practices.",
        },
        {
            "title": f"Understanding {query}",
            "url": f"https://example.com/understanding-{query.replace(' ', '-')}",
            "snippet": f"In-depth explanation of {query} concepts and applications.",
        },
        {
            "title": f"{query} Tools and Resources",
            "url": f"https://example.com/{query.replace(' ', '-')}-tools",
            "snippet": f"Collection of useful tools and resources for working with {query}.",
        },
        {
            "title": f"Future of {query}",
            "url": f"https://example.com/future-{query.replace(' ', '-')}",
            "snippet": f"Predictions and trends shaping the future of {query} technology.",
        },
    ]

    results = []
    for i, result in enumerate(mock_results[:num_results], 1):
        results.append(
            f"{i}. **{result['title']}**\n   URL: {result['url']}\n   {result['snippet']}\n"
        )

    return "\n".join(results)


import urllib.parse
from mcp_client import MCPClientManager

# --- Data Models ---


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str, Enum):
    """Types of agents in DeepAgent system."""

    MAIN = "main"  # Main coordinator agent
    SHELL = "shell"  # Shell command execution
    FILESYSTEM = "filesystem"  # File operations
    BROWSER = "browser"  # Web browser automation (chrome-devtools-mcp)
    WEB_SEARCH = "web_search"  # Web search using Exa AI
    GENERAL = "general"  # No-tool queries


class Task(BaseModel):
    id: int = Field(description="Unique identifier for the task")
    description: str = Field(description="Description of what needs to be done")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    assigned_agent: AgentType = Field(
        description="The agent type best suited for this task",
        default=AgentType.GENERAL,
    )
    result: Optional[str] = None


class Plan(BaseModel):
    goal: str = Field(description="The overall goal of the plan")
    tasks: List[Task] = Field(description="List of tasks to achieve the goal")


class IntentAnalysis(BaseModel):
    intent: str = Field(description="A concise description of the user's intent")
    needs_sandbox: bool = Field(
        description="Whether the request requires sandbox operations"
    )
    confidence: float = Field(description="Confidence score between 0 and 1")


# --- State ---


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_input: str
    intent: Optional[IntentAnalysis]
    plan: Optional[Plan]
    current_task_index: int
    scratchpad: Dict[str, Any]  # For storing intermediate results


# --- Nodes ---


async def analyze_intent(state: AgentState) -> Dict:
    """Analyze the user's input to determine intent."""
    print(f"\n🧠 Analyzing Intent for: {state['user_input']}")

    llm = ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=0,
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    parser = PydanticOutputParser(pydantic_object=IntentAnalysis)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"你是一个智能助手，负责分析用户请求。\n"
                f"当前日期: {{current_date}}\n"
                "请确定用户的意图，并判断是否需要沙箱操作（如Shell命令、文件操作等）。\n"
                "请务必使用中文进行回复。\n"
                "\n{format_instructions}",
            ),
            ("user", "{input}"),
        ]
    )

    chain = prompt | llm | parser
    try:
        intent = await chain.ainvoke(
            {
                "input": state["user_input"],
                "current_date": datetime.now().strftime("%Y-%m-%d"),
                "format_instructions": parser.get_format_instructions(),
            }
        )
        print(f"✅ Intent: {intent.intent} (Sandbox: {intent.needs_sandbox})")
        return {"intent": intent}
    except Exception as e:
        print(f"❌ Intent Analysis Failed: {e}")
        # Fallback
        return {
            "intent": IntentAnalysis(
                intent=state["user_input"], needs_sandbox=True, confidence=0.5
            )
        }


async def create_plan(state: AgentState) -> Dict:
    """Create a plan based on the intent."""
    print(f"\n📋 Creating Plan...")

    llm = ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=0,
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    parser = PydanticOutputParser(pydantic_object=Plan)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个任务规划专家。请创建一个逐步计划来实现用户的目标。\n"
                "该计划将在 Linux 沙箱环境中执行。\n"
                "请将每个任务分配给最合适的智能体类型：\n"
                "- 'shell': 用于运行 shell 命令、安装包、系统检查。\n"
                "- 'filesystem': 用于创建、读取、编辑、删除文件。\n"
                "- 'browser': 用于网页浏览、截图、访问网站。\n"
                "- 'web_search': 用于网页搜索、查找信息。\n"
                "- 'general': 用于纯推理或不需要工具的问题。\n"
                "将复杂任务分解为简单、可验证的步骤。\n"
                "请务必使用中文描述任务。\n"
                "\n{format_instructions}",
            ),
            ("user", "Goal: {intent}"),
        ]
    )

    chain = prompt | llm | parser
    try:
        plan = await chain.ainvoke(
            {
                "intent": state["intent"].intent,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        print(f"✅ Plan Created with {len(plan.tasks)} tasks:")
        for task in plan.tasks:
            print(f"  - [{task.id}] ({task.assigned_agent}) {task.description}")

        return {"plan": plan, "current_task_index": 0}
    except Exception as e:
        print(f"❌ Planning Failed: {e}")
        return {"plan": Plan(goal="Error", tasks=[]), "current_task_index": 0}


def route_task(state: AgentState):
    """Route the current task to the assigned agent."""
    plan = state["plan"]
    idx = state["current_task_index"]

    if idx >= len(plan.tasks):
        return END

    task = plan.tasks[idx]
    if task.assigned_agent == AgentType.SHELL:
        return "agent_shell"
    elif task.assigned_agent == AgentType.FILESYSTEM:
        return "agent_filesystem"
    elif task.assigned_agent == AgentType.BROWSER:
        return "agent_browser"
    elif task.assigned_agent == AgentType.WEB_SEARCH:
        return "agent_web_search"
    else:
        return "agent_general"


# --- Sub-Agent Definitions ---

# Moved inside create_graph_fixed to support dynamic tool binding


async def _execute_subagent(
    state: AgentState, agent_name: str, tools: List[Any]
) -> Dict:
    """Helper to execute a sub-agent."""
    plan = state["plan"]
    idx = state["current_task_index"]
    current_task = plan.tasks[idx]

    print(
        f"\n🤖 [{agent_name}] Executing Task {current_task.id}: {current_task.description}"
    )

    llm = ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=0,
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )

    if tools:
        llm_with_tools = llm.bind_tools(tools)
    else:
        llm_with_tools = llm

    # Context from previous tasks
    context = ""
    for i in range(idx):
        t = plan.tasks[i]
        if t.result:
            context += f"Task {t.id} ({t.description}) Result: {t.result}\n"

    system_prompt = f"你是在 Linux 沙箱中的 {agent_name}。\n"
    system_prompt += f"当前日期: {datetime.now().strftime('%Y-%m-%d')}\n"
    if agent_name == "Browser Controller":
        system_prompt += (
            "你可以访问网络浏览器。 "
            "搜索信息时，请使用浏览器的 'navigate' 工具访问搜索引擎（如 https://www.baidu.com/s?wd=...），"
            "然后使用 'get_content' 或 'take_snapshot' 查看结果。\n"
        )

    system_prompt += (
        f"你当前的任务是: {current_task.description}\n"
        f"来自之前任务的上下文:\n{context}\n"
    )

    if tools:
        system_prompt += "使用可用的工具来完成任务。\n"
    else:
        system_prompt += "根据你的知识提供有帮助的回复。\n"

    system_prompt += "如果任务已完成，请用中文回复最终结果。"

    # Limit message history to prevent context overflow
    # Keep last 30 messages
    history_messages = state["messages"]
    if len(history_messages) > 30:
        print(f"DEBUG: Truncating history from {len(history_messages)} to 30 messages")
        history_messages = history_messages[-30:]

        # Ensure first message is not a ToolMessage to avoid orphan tool outputs
        while history_messages and isinstance(history_messages[0], ToolMessage):
            print("DEBUG: Dropping orphan ToolMessage from start of history")
            history_messages.pop(0)

    # Sanitize messages to ensure tool consistency
    sanitized_history = []
    for i, msg in enumerate(history_messages):
        if isinstance(msg, AIMessage) and msg.tool_calls:
            valid_calls = []
            for tc in msg.tool_calls:
                # Check if this tool call is answered by a subsequent ToolMessage
                is_answered = False
                for j in range(i + 1, len(history_messages)):
                    if (
                        isinstance(history_messages[j], ToolMessage)
                        and history_messages[j].tool_call_id == tc["id"]
                    ):
                        is_answered = True
                        break
                if is_answered:
                    valid_calls.append(tc)

            if len(valid_calls) != len(msg.tool_calls):
                print(
                    f"DEBUG: Removed {len(msg.tool_calls) - len(valid_calls)} orphan tool calls from AIMessage"
                )
                # Create new AIMessage with only valid calls
                new_msg = AIMessage(
                    content=msg.content,
                    tool_calls=valid_calls,
                    id=msg.id,
                    response_metadata=msg.response_metadata,
                    usage_metadata=msg.usage_metadata,
                )
                sanitized_history.append(new_msg)
            else:
                sanitized_history.append(msg)
        else:
            sanitized_history.append(msg)

    messages = [SystemMessage(content=system_prompt)] + sanitized_history

    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState):
    """Determine if we should continue task execution or move to next task."""
    messages = state["messages"]
    last_message = messages[-1]

    # If tool call, go to tools
    if last_message.tool_calls:
        return "tools"

    # If text response, we assume the task is done
    return "update_task_status"


async def update_task_status(state: AgentState) -> Dict:
    """Update the status of the completed task and move to the next."""
    plan = state["plan"]
    idx = state["current_task_index"]
    messages = state["messages"]
    last_message = messages[-1]

    result_text = last_message.content

    # Update current task
    plan.tasks[idx].status = TaskStatus.COMPLETED
    plan.tasks[idx].result = result_text
    print(f"✅ Task {plan.tasks[idx].id} Completed. Result: {result_text[:100]}...")

    return {
        "plan": plan,
        "current_task_index": idx + 1,
    }


# --- Graph Construction ---


def create_graph_with_tools(
    shell_tools, filesystem_tools, browser_tools, web_search_tools
):
    workflow = StateGraph(AgentState)

    # Helper to create agent function with bound tools
    async def create_agent_node(state: AgentState, name: str, tools: List[Any]):
        return await _execute_subagent(state, name, tools)

    # Define Agent Nodes using partial to bind tools
    agent_shell = partial(create_agent_node, name="Shell Commander", tools=shell_tools)
    agent_filesystem = partial(
        create_agent_node, name="File System Manager", tools=filesystem_tools
    )
    agent_browser = partial(
        create_agent_node, name="Browser Controller", tools=browser_tools
    )
    agent_web_search = partial(
        create_agent_node, name="Web Search Assistant", tools=web_search_tools
    )
    agent_general = partial(create_agent_node, name="General Assistant", tools=[])

    # Add Nodes
    workflow.add_node("analyze_intent", analyze_intent)
    workflow.add_node("create_plan", create_plan)

    # Sub-Agents
    workflow.add_node("agent_shell", agent_shell)
    workflow.add_node("agent_filesystem", agent_filesystem)
    workflow.add_node("agent_browser", agent_browser)
    workflow.add_node("agent_web_search", agent_web_search)
    workflow.add_node("agent_general", agent_general)

    # Combine all tools for the ToolNode
    all_tools = shell_tools + filesystem_tools + browser_tools + web_search_tools
    workflow.add_node("tools", ToolNode(all_tools))
    workflow.add_node("update_task_status", update_task_status)

    # Add Edges
    workflow.add_edge(START, "analyze_intent")
    workflow.add_edge("analyze_intent", "create_plan")

    # Initial Routing
    workflow.add_conditional_edges(
        "create_plan",
        route_task,
        {
            "agent_shell": "agent_shell",
            "agent_filesystem": "agent_filesystem",
            "agent_browser": "agent_browser",
            "agent_web_search": "agent_web_search",
            "agent_general": "agent_general",
            END: END,
        },
    )

    # Agent -> Tools or Update
    for agent in [
        "agent_shell",
        "agent_filesystem",
        "agent_browser",
        "agent_web_search",
        "agent_general",
    ]:
        workflow.add_conditional_edges(
            agent,
            should_continue,
            {"tools": "tools", "update_task_status": "update_task_status"},
        )

    # Tools -> Back to Agent
    workflow.add_conditional_edges(
        "tools",
        route_task,
        {
            "agent_shell": "agent_shell",
            "agent_filesystem": "agent_filesystem",
            "agent_browser": "agent_browser",
            "agent_web_search": "agent_web_search",
            "agent_general": "agent_general",
            END: END,
        },
    )

    # Update Status -> Next Task or End
    def next_step_router(state: AgentState):
        if state["current_task_index"] >= len(state["plan"].tasks):
            return END
        # Route to the assigned agent for the NEW current task
        return route_task(state)

    workflow.add_conditional_edges(
        "update_task_status",
        next_step_router,
        {
            "agent_shell": "agent_shell",
            "agent_filesystem": "agent_filesystem",
            "agent_browser": "agent_browser",
            "agent_web_search": "agent_web_search",
            "agent_general": "agent_general",
            END: END,
        },
    )

    return workflow.compile()


# --- Main ---


async def main():
    # Load .env
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    # Initialize MCP Manager
    mcp_manager = MCPClientManager()
    try:
        await mcp_manager.connect()

        # Get Tools
        shell_tools = await mcp_manager.get_tools("shell")
        filesystem_tools = await mcp_manager.get_tools("filesystem")
        browser_tools = await mcp_manager.get_tools("chrome")

        # Web Search Tools (direct implementation)
        web_search_tools = [web_search]

        print(
            f"✅ Loaded Tools: Shell({len(shell_tools)}), Filesystem({len(filesystem_tools)}), Browser({len(browser_tools)})"
        )

        # Debug tool sizes
        for t in browser_tools:
            print(
                f"Browser Tool: {t.name}, Args Schema Size: {len(str(t.args_schema.model_json_schema()))}"
            )

        # Create Graph
        agent_graph = create_graph_with_tools(
            shell_tools, filesystem_tools, browser_tools, web_search_tools
        )

        if len(sys.argv) > 1:
            # One-shot mode
            user_input = sys.argv[1]
            print(f"User Input: {user_input}")
            initial_state = {
                "user_input": user_input,
                "plan": Plan(goal="", tasks=[]),
                "messages": [],
                "current_task_index": 0,
            }
            await agent_graph.ainvoke(initial_state)
        else:
            # Interactive mode
            print("🤖 DeepAgent Interactive Mode")
            print("Type 'exit' or 'quit' to stop.")

            while True:
                try:
                    user_input = input("\nUser: ").strip()
                    if not user_input:
                        continue
                    if user_input.lower() in ["exit", "quit"]:
                        break

                    initial_state = {
                        "user_input": user_input,
                        "plan": Plan(goal="", tasks=[]),
                        "messages": [],
                        "current_task_index": 0,
                    }

                    await agent_graph.ainvoke(initial_state)
                    print("\n✨ Done.")
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    import traceback

                    traceback.print_exc()
    finally:
        await mcp_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
