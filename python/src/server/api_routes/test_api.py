# python/src/server/api_routes/test_api.py
import os
from fastapi import APIRouter, HTTPException, status
from supabase import Client # Needed for type hinting for get_supabase_client
from ..services.client_manager import get_supabase_client # Found this definition

# This router should only be included if the environment allows it.
# This ensures test-specific endpoints are not exposed in production.
if os.getenv("ENABLE_TEST_ENDPOINTS") != "true":
    # If the env var is not set, we create a dummy router that does nothing.
    router = APIRouter()
else:
    # If the env var is set, we create the actual router with the endpoint.
    router = APIRouter(
        prefix="/api/test",
        tags=["Test"],
    )

    @router.post("/reset-database", status_code=status.HTTP_200_OK)
    async def reset_database():
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
            await supabase_client.rpc('reset_test_database').execute()
            await supabase_client.rpc('seed_test_database').execute()
            
            return {"message": "Database reset and seeded successfully via API."}
        except Exception as e:
            # Log the error for debugging purposes
            print(f"ERROR: Database reset via API failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database setup failed via API: {str(e)}",
            )