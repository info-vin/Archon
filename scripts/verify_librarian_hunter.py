import asyncio
import os
import logging
from src.agents.workflow_engine import LibrarianNode, SharedState
from pydantic_graph import GraphRunContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_librarian_hunter():
    print("🚀 [Librarian] Starting Hunter Mode Verification...")
    
    # Mock context and state
    state = SharedState(
        messages=[
            {"role": "user", "content": "Tell me what's the latest version of Python mentioned at https://www.python.org/downloads/"}
        ]
    )
    
    # We need to mock the context properly for pydantic-graph
    # For a quick test, we'll manually invoke the run method
    node = LibrarianNode()
    
    # Create a dummy context
    class MockContext:
        def __init__(self, state):
            self.state = state
    
    ctx = MockContext(state)
    
    print("🔍 Asking Librarian to hunt for info at python.org...")
    try:
        # Note: In a real graph, this would be await node.run(ctx)
        # Here we directly call it to verify tool access and service integration
        await node.run(ctx)
        
        last_msg = state.messages[-1]
        print(f"✅ Librarian Response: {last_msg['content'][:200]}...")
        
        if "python.org" in last_msg['content'].lower() or "source" in str(last_msg).lower():
            print("💎 SUCCESS: Librarian successfully used tools to gather info!")
        else:
            print("⚠️ WARNING: Response didn't seem to contain hunted info. Check logs.")
            
        if "citations" in last_msg and isinstance(last_msg["citations"], list):
            print(f"🔗 Citations Found: {len(last_msg['citations'])}")
        elif "citations" in last_msg:
            print(f"🔗 Citations Found (Raw): {last_msg['citations']}")
            
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ensure environment variables are set for the test
    # Phase 5.1.4: Use GOOGLE_API_KEY as requested by user
    if os.getenv("GOOGLE_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")
        
    # Reverting to Git Log specified model: gemini-3.1-flash-lite
    os.environ["WORKER_AGENT_MODEL"] = os.getenv("WORKER_AGENT_MODEL", "gemini-3.1-flash-lite")
    asyncio.run(test_librarian_hunter())
