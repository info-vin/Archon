# python/src/server/core/health.py
from datetime import datetime
from typing import Any

from src.server.config.logfire_config import api_logger

from .app_state import app_state

# Cache schema check result to avoid repeated database queries
_schema_check_cache: dict[str, Any] = {"valid": None, "checked_at": 0.0}

async def _check_database_schema():
    """Check if the projects table exists to determine schema validity."""
    import time

    # If we've already confirmed schema is valid, don't check again
    if _schema_check_cache.get("valid") is True:
        return {"valid": True, "message": "Schema is up to date (cached)"}

    # If we recently failed, don't spam the database (wait at least 30 seconds)
    current_time = time.time()
    last_checked = float(_schema_check_cache.get("checked_at", 0.0))
    if _schema_check_cache.get("valid") is False and current_time - last_checked < 30:
        return _schema_check_cache.get("result", {"valid": False, "message": "Schema check recently failed."})

    try:
        from src.server.services.client_manager import get_supabase_client

        client = get_supabase_client()

        # Check if the 'archon_projects' table exists.
        client.table("archon_projects").select("id").limit(1).execute()

        # Cache successful result
        _schema_check_cache["valid"] = True
        _schema_check_cache["checked_at"] = current_time
        _schema_check_cache["result"] = {"valid": True, "message": "Schema is up to date"}

        return _schema_check_cache["result"]

    except Exception as e:
        error_msg = str(e).lower()
        api_logger.debug(f"Schema check error: {type(e).__name__}: {str(e)}")

        # Check if the error indicates the table does not exist.
        if 'relation "archon_projects" does not exist' in error_msg:
            result = {
                "valid": False,
                "message": "Projects table not detected. This is required for the projects feature.",
            }
            # Cache failed result
            _schema_check_cache["valid"] = False
            _schema_check_cache["checked_at"] = current_time
            _schema_check_cache["result"] = result
            return result

        # For other errors, consider the schema valid to not block other functionalities,
        # but log the error.
        api_logger.warning(f"Inconclusive schema check: {error_msg}")
        return {"valid": True, "message": f"Schema check inconclusive: {str(e)}"}

async def check_system_health():
    """Core health check logic shared between /health and /api/health."""
    # Check if initialization is complete
    if not app_state.initialization_complete:
        return {
            "status": "initializing",
            "service": "archon-backend",
            "timestamp": datetime.now().isoformat(),
            "message": "Backend is starting up, credentials loading...",
            "ready": False,
        }

    # Check for required database schema
    schema_status = await _check_database_schema()
    if not schema_status["valid"]:
        return {
            "status": "migration_required",
            "service": "archon-backend",
            "timestamp": datetime.now().isoformat(),
            "ready": False,
            "migration_required": True,
            "message": schema_status["message"],
            "migration_instructions": "Open Supabase Dashboard → SQL Editor → Run: migration/add_source_url_display_name.sql",
            "schema_valid": False,
        }

    return {
        "status": "healthy",
        "service": "archon-backend",
        "timestamp": datetime.now().isoformat(),
        "ready": True,
        "credentials_loaded": True,
        "schema_valid": True,
    }
