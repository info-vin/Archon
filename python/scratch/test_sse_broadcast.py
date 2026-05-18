
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def test_sse_broadcast():
    print("🧪 Testing SSE Broadcast...")

    from src.server.utils.sse_manager import sse_manager

    # 1. Subscribe a mock client
    sub_id, queue = await sse_manager.subscribe()

    # 2. Broadcast an update
    test_data = {"task_id": "123", "status": "done"}
    await sse_manager.broadcast("task_updated", test_data)

    # 3. Check queue
    message = await queue.get()
    print(f"Received message: {message.strip()}")

    assert "event: task_updated" in message
    assert '"task_id": "123"' in message

    # 4. Unsubscribe
    sse_manager.unsubscribe(sub_id)
    assert sub_id not in sse_manager.subscribers

    print("✅ SSE Broadcast Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_sse_broadcast())
