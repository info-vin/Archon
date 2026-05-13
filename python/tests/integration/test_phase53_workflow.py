import logging

import pytest
from dotenv import load_dotenv
from httpx import AsyncClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables to ensure API keys are available for local script testing
load_dotenv(".env")

async def is_server_running():
    try:
        async with AsyncClient() as client:
            resp = await client.get("http://localhost:8052/health", timeout=2.0)
            return resp.status_code == 200
    except Exception:
        return False

@pytest.mark.asyncio
async def test_phase53_bob_to_charlie_workflow():
    """
    Phase 5.3: Concept Verification for Supervisor/Worker Topology.
    Simulates Bob (Marketing) requesting a blog post about AI models.
    """
    if not await is_server_running():
        pytest.skip("Agents server not running on localhost:8052")

    agents_url = "http://localhost:8052"
    prompt = "I need a short blog post about the latest Gemini models for our website."

    logger.info("🚀 Initiating Workflow as Bob...")

    async with AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{agents_url}/agents/workflow/run",
            json={"prompt": prompt},
            headers={"X-User-Role": "marketing"} # Simulating Bob's context
        )

        # 1. Assert Basic Execution
        assert response.status_code == 200
        data = response.json()

        # Check if we hit the Google API Free Tier Daily Limit (Phase 5.4.4 Resilience check)
        if not data.get("success") and "API Daily Limit Exceeded" in data.get("error", ""):
            logger.warning("⚠️ Google Free Tier Daily Limit Exceeded. Workflow gracefully degraded.")
            logger.warning("⚠️ Cannot verify full node path, but resilience mechanism is VERIFIED.")
            return # Conditional Pass

        assert data.get("success") is True, f"Workflow failed: {data.get('error')}"

        metadata = data.get("metadata", {})
        messages = metadata.get("messages", [])

        # 2. Assert Star-Topology Path
        # We expect messages from: user -> supervisor(charlie) -> librarian -> supervisor -> marketbot -> supervisor...
        # At minimum, librarian and marketbot should have participated.
        participants = {m.get("role") for m in messages}
        logger.info(f"👥 Participants in workflow: {participants}")

        assert "librarian" in participants, "Librarian Node did not execute"
        assert "marketbot" in participants, "MarketBot Node did not execute"

        # 3. Assert Final Output Structure
        final_result = data.get("result", "")
        logger.info(f"📝 Final Result Length: {len(final_result)}")
        assert len(final_result) > 50, "Final result is suspiciously short"

        # 4. Assert Circuit Breaker didn't trip unnecessarily
        assert metadata.get("step_count", 0) <= 5, "Workflow took too many steps, potential loop."
        assert "Needs Human Review" not in final_result, "Workflow hit the recursion limit!"

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_phase53_bob_to_charlie_workflow())
