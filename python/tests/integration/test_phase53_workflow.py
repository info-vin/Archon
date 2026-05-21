import logging
import os

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
    Phase 5.3 & 5.0.2: Concept Verification for Supervisor/Worker Topology and Dynamic Prompt Governance.
    Simulates Charlie hosting a Marketing Data Deep Dive.
    """
    if os.environ.get("RUN_INTEGRATION_TESTS") != "true":
        pytest.skip("Skipping integration workflow test (set RUN_INTEGRATION_TESTS=true to run)")

    if not await is_server_running():
        pytest.skip("Agents server not running on localhost:8052")

    agents_url = "http://localhost:8052"
    prompt = "Please pull the latest conversion rates, calculate the WoW growth, and give me a marketing strategy."

    logger.info("🚀 Initiating Workflow as Charlie (Marketing Data Deep Dive)...")

    async with AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{agents_url}/agents/workflow/run",
            json={"prompt": prompt, "context": {"task_type": "Marketing Data Deep Dive"}},
            headers={"X-User-Role": "marketing"}
        )

        assert response.status_code == 200
        data = response.json()

        if not data.get("success"):
            err_msg = data.get("error", "")
            if any(msg in err_msg for msg in ["API Daily Limit Exceeded", "leaked", "PERMISSION_DENIED", "API key"]):
                logger.warning(f"⚠️ Google API Key or quota issue detected: {err_msg}. Workflow gracefully skipped.")
                pytest.skip(f"Skipping workflow integration test due to API key/quota issue: {err_msg}")

        assert data.get("success") is True, f"Workflow failed: {data.get('error')}"

        metadata = data.get("metadata", {})
        # Depending on PAI version, messages might be in metadata or data
        messages = data.get("messages") or metadata.get("messages", [])

        participants = {m.get("role") for m in messages}
        logger.info(f"👥 Participants in workflow: {participants}")

        # The new prompt should route to at least david or devbot or marketbot(bob)
        has_worker = any(role in participants for role in ["david", "devbot", "marketbot", "bob"])
        assert has_worker, f"No expected worker node executed. Participants: {participants}"

        assert metadata.get("step_count", 0) <= 8, "Workflow took too many steps, potential loop."

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_phase53_bob_to_charlie_workflow())
