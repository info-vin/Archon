import logging
import os

import httpx

logger = logging.getLogger(__name__)

# --- David's Developer Tools (Phase 5.1.3) ---
async def propose_code_fix(file_path: str, new_content: str, summary: str) -> str:
    """
    Submits a code change proposal to the Archon Server for human approval.
    Use this when you have identified a fix for a bug or a way to implement a feature.
    """
    server_port = os.getenv("ARCHON_SERVER_PORT", "8181")
    is_docker = os.getenv("DOCKER_CONTAINER") == "true" or os.path.exists("/.dockerenv")
    server_host = "archon-server" if is_docker else "localhost"
    url = f"http://{server_host}:{server_port}/internal/david/propose"

    payload = {
        "file_path": file_path,
        "new_content": new_content,
        "summary": summary
    }

    try:
        async with httpx.AsyncClient() as client:
            # Note: In a production scenario, we'd add auth headers here.
            # For now, we rely on the internal Docker network security.
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return f"✅ Proposal created successfully! ID: {data.get('id')}. Waiting for human approval."
    except Exception as e:
        logger.error(f"Failed to submit proposal: {e}")
        return f"❌ Failed to submit proposal: {str(e)}"

async def read_code_file(file_path: str) -> str:
    """
    Reads the content of a file from the codebase.
    """
    server_port = os.getenv("ARCHON_SERVER_PORT", "8181")
    is_docker = os.getenv("DOCKER_CONTAINER") == "true" or os.path.exists("/.dockerenv")
    server_host = "archon-server" if is_docker else "localhost"
    # Reusing the existing internal proxy endpoint
    url = f"http://{server_host}:{server_port}/internal/david/read?path={file_path}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            return response.text
    except Exception as e:
        return f"❌ Failed to read file: {str(e)}"
