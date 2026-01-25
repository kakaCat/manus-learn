import os
import json
import logging
from typing import Any, Dict, List
from datetime import datetime
from pathlib import Path

class SessionRecorder:
    """
    Handles file-based logging for agent sessions.
    Structure:
    workspace/
      └── sessions/
          └── {session_id}/
              ├── chat_history.md       # Human readable chat log
              ├── state.json            # Latest state snapshot
              └── executions/           # Detailed logs for each task execution
                  ├── task_{id}_{agent}.md
                  └── ...
    """
    
    def __init__(self, session_id: str, base_dir: str = "workspace/sessions"):
        self.session_id = session_id
        self.base_path = Path(base_dir) / session_id
        self.executions_path = self.base_path / "executions"
        
        # Ensure directories exist
        self.executions_path.mkdir(parents=True, exist_ok=True)
        
        self.chat_log_path = self.base_path / "chat_history.md"
        self.state_log_path = self.base_path / "state.json"
        
    def log_chat(self, role: str, content: str):
        """Append a message to the chat history log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.chat_log_path, "a", encoding="utf-8") as f:
            f.write(f"\n### [{timestamp}] {role}\n\n")
            f.write(f"{content}\n\n")
            f.write("---\n")

    def save_state(self, state_data: Dict[str, Any]):
        """Save the current state snapshot."""
        try:
            # Serialize Pydantic models if present
            def default_serializer(obj):
                if hasattr(obj, "model_dump"):
                    return obj.model_dump()
                if hasattr(obj, "dict"):
                    return obj.dict()
                return str(obj)

            with open(self.state_log_path, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, default=default_serializer, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save state snapshot: {e}")

    def log_execution(self, task_id: int, agent_name: str, content: str):
        """Log details of a sub-agent execution."""
        filename = f"task_{task_id}_{agent_name}.md"
        file_path = self.executions_path / filename
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n## [{timestamp}] Execution Update\n\n")
            f.write(f"{content}\n\n")

    def log_data(self, filename: str, data: Any):
        """Save raw data (e.g., search results) to a specific file in the session folder."""
        file_path = self.base_path / filename
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(data))
        except Exception as e:
            print(f"⚠️ Failed to log data to {filename}: {e}")
