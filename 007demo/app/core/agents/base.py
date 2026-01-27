import os
import json
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage, HumanMessage
from app.models.schemas import SharedBlackboard, Task, AgentType
from app.core.prompts.execution import EXECUTION_SYSTEM_PROMPT
from app.core.logger import SessionRecorder

SIMPLE_EXECUTION_PROMPT = """
You are executing the task:
{step}

Please use your tools to complete this task.
"""


class BaseSubAgent:
    """
    Base Independent Sub-Agent that executes a single task using its own Level B Memory.
    """

    def __init__(
        self,
        task: Task,
        blackboard: SharedBlackboard,
        tools: List[Any],
        session_id: Optional[str] = None,
        system_prompt: str = EXECUTION_SYSTEM_PROMPT,
    ):
        self.task = task
        self.blackboard = blackboard
        self.tools = tools
        self.agent_name = f"Agent-{task.assigned_agent.value}"
        self.system_prompt = system_prompt
        self.session_id = session_id
        self.recorder = SessionRecorder(session_id) if session_id else None

        # Initialize LLM
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")

        self.llm = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            temperature=0,
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
            api_key=api_key,
        )
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

        # Level B Memory: Transient context for this specific task
        self.memory: List = []

    def _initialize_memory(self):
        """Initialize memory with System Prompt"""
        self.memory.append(SystemMessage(content=self.system_prompt))

    async def run(self) -> Dict:
        """
        Executes the task using a ReAct loop.
        """
        self._initialize_memory()

        print(
            f"  ▶️ [{self.agent_name}] Starting Task {self.task.id}: {self.task.description}"
        )

        # Prepare Initial Context
        blackboard_context = f"Shared Variables: {self.blackboard.variables}\nKey Conclusions: {self.blackboard.key_conclusions}"

        # Use Simple Prompt for specialized agents (or fallback to EXECUTION_PROMPT if complex JSON is needed)
        # Since we are decoupled, we use SIMPLE_EXECUTION_PROMPT by default for the ReAct loop context
        context_content = SIMPLE_EXECUTION_PROMPT.format(
            message="Please execute the assigned task.",
            attachments="[]",
            language="English",
            step=self.task.description,
        )
        context_content += f"\n\nContext from Blackboard:\n{blackboard_context}"

        self.memory.append(HumanMessage(content=context_content))

        final_summary = "Task completed (timeout)."

        # ReAct Loop (Max 10 turns)
        for _ in range(10):
            try:
                # Load current messages from memory
                messages = self.memory

                response = await self.llm_with_tools.ainvoke(messages)
                self.memory.append(response)

                # Log Thought (AI Response)
                if self.recorder:
                    self.recorder.log_execution(
                        self.task.id,
                        self.agent_name,
                        f"### Step {_ + 1} - Thought\n\n{response.content}",
                    )

                # Check if response has tool calls (LangChain 1.x compatible)
                if (
                    isinstance(response, AIMessage)
                    and hasattr(response, "tool_calls")
                    and response.tool_calls
                ):
                    for tool_call in response.tool_calls:
                        selected_tool = next(
                            (t for t in self.tools if t.name == tool_call["name"]), None
                        )
                        if selected_tool:
                            print(
                                f"    🛠️ [{self.agent_name}] Calling {selected_tool.name}..."
                            )

                            # Log Tool Call
                            if self.recorder:
                                self.recorder.log_execution(
                                    self.task.id,
                                    self.agent_name,
                                    f"### Step {_ + 1} - Tool Call\n\n**Tool**: `{tool_call['name']}`\n**Args**: ```json\n{json.dumps(tool_call['args'], indent=2)}\n```",
                                )

                            try:
                                tool_result = await selected_tool.ainvoke(
                                    tool_call["args"]
                                )
                            except Exception as e:
                                tool_result = f"Error: {e}"

                            print(f"    📝 Tool Result: {str(tool_result)[:100]}...")
                            self.memory.append(
                                ToolMessage(
                                    content=str(tool_result),
                                    tool_call_id=tool_call["id"],
                                )
                            )

                            # Log Tool Result
                            if self.recorder:
                                # Save full result if it's large or complex
                                result_str = str(tool_result)
                                if len(result_str) > 500 or isinstance(
                                    tool_result, (dict, list)
                                ):
                                    tool_call_id = tool_call.get("id", "unknown")[:8]
                                    output_filename = f"tool_{self.task.id}_{_ + 1}_{tool_call['name']}_{tool_call_id}.txt"
                                    # Use executions subdirectory for tool outputs to keep root clean
                                    full_output_path = f"executions/{output_filename}"
                                    self.recorder.log_data(
                                        full_output_path, tool_result
                                    )

                                    log_msg = f"### Step {_ + 1} - Tool Result\n\n**Full Output Saved**: `{full_output_path}`\n\n**Preview**:\n```\n{result_str[:2000]}\n```"
                                else:
                                    log_msg = f"### Step {_ + 1} - Tool Result\n\n```\n{result_str}\n```"

                                self.recorder.log_execution(
                                    self.task.id, self.agent_name, log_msg
                                )

                        else:
                            self.memory.append(
                                ToolMessage(
                                    content="Tool not found",
                                    tool_call_id=tool_call["id"],
                                )
                            )
                else:
                    # Final response parsing
                    content = str(response.content) if response.content else ""
                    print(
                        f"  ✅ [{self.agent_name}] Finished Task {self.task.id}. Content: {content[:100]}..."
                    )

                    try:
                        # Try to extract JSON if it's wrapped in markdown
                        if "```json" in content:
                            content = (
                                content.split("```json")[1].split("```")[0].strip()
                            )
                        elif "```" in content:
                            content = content.split("```")[1].split("```")[0].strip()

                        data = json.loads(content)
                        final_summary = data.get("result", content)
                        if not final_summary:
                            final_summary = data.get("message", "Task completed.")
                    except json.JSONDecodeError:
                        # Fallback to raw content if not JSON
                        final_summary = content

                    break
            except Exception as e:
                print(f"  ❌ [{self.agent_name}] Error: {e}")
                final_summary = f"Error: {e}"
                break

        return {"task_id": self.task.id, "summary": final_summary}
