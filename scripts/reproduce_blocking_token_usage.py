import sys
import os
import asyncio
import time
from unittest.mock import MagicMock, patch

# Adjust path to find server package from scripts/ directory
# Assuming script is in scripts/, server is in python/src/server
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "python", "src"))

from server.services.token_usage_service import TokenUsageService

# Mock Supabase client to simulate blocking IO
mock_client = MagicMock()
mock_table = MagicMock()
mock_insert = MagicMock()
mock_select = MagicMock()

def blocking_execute():
    print("  [DB] Starting blocking DB call (1s)...")
    time.sleep(1.0) # Simulate blocking IO
    print("  [DB] Finished blocking DB call")
    return MagicMock()

mock_insert.execute.side_effect = blocking_execute
mock_table.insert.return_value = mock_insert

# Mock select chain for get_daily_cost
mock_chain = MagicMock()
mock_chain.gt.return_value.order.return_value.limit.return_value.execute.side_effect = blocking_execute
mock_table.select.return_value = mock_chain

mock_client.table.return_value = mock_table

async def heartbeat():
    print("  [Heartbeat] Started")
    last_time = time.time()
    try:
        while True:
            await asyncio.sleep(0.1)
            now = time.time()
            diff = now - last_time
            if diff > 0.15: # Allow some margin
                print(f"  [Heartbeat] BLOCKED! Gap: {diff:.3f}s")
            else:
                print(f"  [Heartbeat] Tick")
            last_time = now
    except asyncio.CancelledError:
        pass

async def main():
    print("Starting Archon Token Usage Performance Test...")

    with patch("server.services.token_usage_service.get_supabase_client", return_value=mock_client):
        service = TokenUsageService()

        # Start heartbeat
        heartbeat_task = asyncio.create_task(heartbeat())

        # Wait a bit
        await asyncio.sleep(0.2)

        # Call log_usage
        print("
=== Testing log_usage (Fire-and-forget check) ===")
        print("Calling log_usage...")
        # Start time
        start = time.time()
        await service.log_usage(
            request_id="test",
            model="gpt-4o",
            provider="openai",
            input_tokens=100,
            output_tokens=100
        )
        end = time.time()
        print(f"log_usage returned in {end - start:.3f}s")

        await asyncio.sleep(0.5)

        # Call get_daily_cost
        print("
=== Testing get_daily_cost (Blocking check) ===")
        print("Calling get_daily_cost...")
        start = time.time()
        await service.get_daily_cost(days=7)
        end = time.time()
        print(f"get_daily_cost returned in {end - start:.3f}s")

        # Give time for heartbeat to report blockage
        await asyncio.sleep(0.5)

        heartbeat_task.cancel()
        await heartbeat_task

if __name__ == "__main__":
    asyncio.run(main())
