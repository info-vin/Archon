# python/src/server/api_routes/test_api.py
import os
from typing import Any

from fastapi import APIRouter, HTTPException, status
from supabase import Client  # Needed for type hinting for get_supabase_client

from ..services.client_manager import get_supabase_client  # Found this definition

# This router should only be included if the environment allows it.
# This ensures test-specific endpoints are not exposed in production.
from src.server.services.settings_service import SettingsService
if SettingsService().get_setting("ENABLE_TEST_ENDPOINTS") != "true":
    # If the env var is not set, we create a dummy router that does nothing.
    router = APIRouter()
else:
    # If the env var is set, we create the actual router with the endpoint.
    router = APIRouter(
        prefix="/api/test",
        tags=["Test"],
    )

    @router.post("/reset-database", status_code=status.HTTP_200_OK)
    async def reset_database() -> Any:
        """
        Resets and seeds the database using pre-defined database functions.
        THIS IS FOR TESTING ONLY AND SHOULD NOT BE ENABLED IN PRODUCTION.
        It requires ENABLE_TEST_ENDPOINTS=true in the environment.
        """
        try:
            # Get the Supabase client using the project's standard method
            supabase_client: Client = get_supabase_client()

            # Call the database functions via RPC
            # These functions are defined in migration/004_create_test_utility_functions.sql
            supabase_client.rpc("reset_test_database").execute()
            supabase_client.rpc("seed_test_database").execute()

            return {"message": "Database reset and seeded successfully via API."}
        except Exception as e:
            # Log the error for debugging purposes
            print(f"ERROR: Database reset via API failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database setup failed via API: {str(e)}",
            ) from e

    @router.post("/trigger-agent-task", status_code=status.HTTP_200_OK)
    async def trigger_agent_task(payload: dict):
        """
        Manually triggers an AI Agent task execution for testing self-healing.
        Required fields: task_id, agent_id, command
        """
        from ..services.agent_service import agent_service
        from ..services.projects.task_service import task_service

        task_id = payload.get("task_id")
        agent_id = payload.get("agent_id")
        command = payload.get("command")

        if not task_id or not agent_id:
            raise HTTPException(status_code=400, detail="Missing task_id or agent_id")

        # Grounded Reasoning Transition: If command is provided, update task description
        # This forces the agent to read and reason instead of being magically injected.
        if command:
            success, task_data = await task_service.get_task(task_id)
            if success and task_data:
                old_desc = task_data["task"].get("description", "")
                new_desc = f"{old_desc}\n\n[Instruction]: Please use appropriate tools to execute and verify: {command}"
                await task_service.update_task(task_id, {"description": new_desc})

        # Run the task in the background
        import asyncio

        asyncio.create_task(agent_service.run_agent_task(task_id, agent_id))

        return {"message": f"Task {task_id} triggered for agent {agent_id}", "command": command}
