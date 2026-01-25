import asyncio
import os
import sys
import uuid
from dotenv import load_dotenv

# Ensure we are in the right directory and can import app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)
sys.path.append(current_dir)

from app.services.agent_service import AgentService

# Load env
load_dotenv()

async def execute_task(user_input: str):
    print(f"\n🚀 Executing Task: {user_input}")
    print("---------------------------------------------------")
    
    # Generate a session ID for logging
    session_id = str(uuid.uuid4())
    print(f"📝 Session ID: {session_id}")
    print(f"📂 Logging to: workspace/sessions/{session_id}/")
    print("---------------------------------------------------")

    service = AgentService()
    await service.initialize()
    
    try:
        async for event in service.run_task_stream(user_input, session_id):
            # Print events as they happen
            event_type = list(event.keys())[0]
            # You can print more details if needed
            # print(f"Event: {event_type}") 
            pass
        
        print("\n---------------------------------------------------")
        print("✅ Task Execution Finished.")
        
        # Verify logs
        log_dir = f"workspace/sessions/{session_id}"
        if os.path.exists(log_dir):
            print(f"\n📂 Session Files created in {log_dir}:")
            for root, dirs, files in os.walk(log_dir):
                level = root.replace(log_dir, '').count(os.sep)
                indent = ' ' * 4 * (level)
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 4 * (level + 1)
                for f in files:
                    print(f"{subindent}{f}")
        else:
            print(f"\n❌ Warning: Session directory not found at {log_dir}")
            
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await service.shutdown()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = "007执行北京到哈尔滨7日游的旅行策划"
    
    asyncio.run(execute_task(task))
