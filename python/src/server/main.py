"""
FastAPI Backend for Archon Knowledge Engine

This is the main entry point for the Archon backend API.
It uses a modular approach with separate API modules for different functionality.

Modules:
- settings_api: Settings and credentials management
- mcp_api: MCP server management and tool execution
- knowledge_api: Knowledge base, crawling, and RAG operations
- projects_api: Project and task management with streaming
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_routes.admin_api import router as admin_router  # NEW IMPORT
from .api_routes.agent_chat_api import router as agent_chat_router
from .api_routes.agents_api import router as agents_router
from .api_routes.auth_api import router as auth_router  # NEW IMPORT
from .api_routes.blog_api import router as blog_router
from .api_routes.bug_report_api import router as bug_report_router
from .api_routes.changes_api import router as changes_router  # NEW IMPORT
from .api_routes.ethics_api import router as ethics_router  # NEW IMPORT
from .api_routes.extraction_api import router as extraction_router  # NEW IMPORT (GAP-018)
from .api_routes.files_api import router as files_router
from .api_routes.internal_api import router as internal_router
from .api_routes.knowledge_api import router as knowledge_router
from .api_routes.log_api import router as log_router
from .api_routes.marketing_api import router as marketing_router  # NEW IMPORT
from .api_routes.migration_api import router as migration_router
from .api_routes.ollama import router as ollama_router
from .api_routes.progress_api import router as progress_router
from .api_routes.projects_api import router as projects_router
from .api_routes.prompts_api import router as prompts_router
from .api_routes.providers_api import router as providers_router
from .api_routes.settings_api import router as settings_router
from .api_routes.stats_api import router as stats_router
from .api_routes.system_api import router as system_router  # NEW IMPORT
from .api_routes.test_api import router as test_api_router  # NEW IMPORT
from .api_routes.version_api import router as version_router
from .api_routes.visit_log_api import router as visit_log_router  # NEW IMPORT

# Import Logfire configuration
from .config.logfire_config import api_logger, setup_logfire
from .services.background_task_manager import cleanup_task_manager
from .services.crawler_manager import cleanup_crawler

# Import utilities and core classes
from .services.credential_service import initialize_credentials
from .services.scheduler_service import SchedulerService

# Import missing dependencies that the modular APIs need
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig
except ImportError:
    # These are optional dependencies for full functionality
    AsyncWebCrawler = None
    BrowserConfig = None

# Logger will be initialized after credentials are loaded
logger = logging.getLogger(__name__)

# Set up logging configuration to reduce noise

# Override uvicorn's access log format to be less verbose
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.setLevel(logging.INFO)  # Enable all logs

# CrawlingContext has been replaced by CrawlerManager in services/crawler_manager.py

# Global flag to track if initialization is complete
_initialization_complete = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown tasks."""
    global _initialization_complete
    _initialization_complete = False

    # Startup
    logger.info("🚀 Starting Archon backend...")

    try:
        # Validate configuration FIRST - check for anon vs service key
        from .config.config import get_config

        get_config()  # This will raise ConfigurationError if anon key detected

        # Initialize credentials from database FIRST - this is the foundation for everything else
        await initialize_credentials()

        # Now that credentials are loaded, we can properly initialize logging
        # This must happen AFTER credentials so LOGFIRE_ENABLED is set from database
        setup_logfire(service_name="archon-backend")

        # Now we can safely use the logger
        logger.info("✅ Credentials initialized")
        api_logger.info("🔥 Logfire initialized for backend")

        # Initialize crawling context
        # try:
        #     await initialize_crawler()
        # except Exception as e:
        #     api_logger.warning(f"Could not fully initialize crawling context: {str(e)}")

        # Make crawling context available to modules
        # Crawler is now managed by CrawlerManager

        api_logger.info("✅ Using polling for real-time updates")

        # Initialize Prompt Service
        try:
            from .services.prompt_service import prompt_service

            await prompt_service.load_prompts()
            api_logger.info("✅ Prompt service initialized")
        except Exception as e:
            api_logger.warning(f"Could not initialize prompt service: {e}")



        # Initialize Agent Neural Wiring (MCP Client Injection)
        try:
            from ..agents.mcp_client import get_mcp_client
            from .services.agent_service import agent_service

            # Initialize the global MCP client bridge
            mcp_bridge = await get_mcp_client()

            # Inject into Agent Service (Neural Wiring)
            agent_service.mcp_client = mcp_bridge
            api_logger.info("🧠 Agent Neural Wiring Complete: MCP Client injected into AgentService")
        except Exception as e:
            api_logger.warning(f"⚠️ Failed to wire Agent to MCP (Skills disabled): {e}")

        # Set the main event loop for background tasks
        try:
            from .services.background_task_manager import get_task_manager

            task_manager = get_task_manager()
            current_loop = asyncio.get_running_loop()
            task_manager.set_main_loop(current_loop)
            api_logger.info("✅ Main event loop set for background tasks")
        except Exception as e:
            api_logger.warning(f"Could not set main event loop: {e}")

        # Re-enable Internal Scheduler
        try:
            await SchedulerService().start()
            api_logger.info("🕒 Internal Scheduler started")
        except Exception as e:
            api_logger.warning(f"Could not start internal scheduler: {e}")

        # MCP Client functionality removed from architecture
        # Agents now use MCP tools directly

        # Mark initialization as complete
        _initialization_complete = True
        api_logger.info("🎉 Archon backend started successfully!")

    except Exception as e:
        api_logger.error(f"❌ Failed to start backend: {str(e)}")
        raise

    yield

    # Shutdown
    _initialization_complete = False
    api_logger.info("🛑 Shutting down Archon backend...")

    try:


        # MCP Client cleanup not needed

        # Cleanup crawling context
        try:
            await cleanup_crawler()
        except Exception as e:
            api_logger.warning(f"Could not cleanup crawling context: {str(e)}")

        # Cleanup background task manager
        try:
            await cleanup_task_manager()
            api_logger.info("Background task manager cleaned up")
        except Exception as e:
            api_logger.warning(f"Could not cleanup background task manager: {str(e)}")

        # Stop Internal Scheduler
        try:
            SchedulerService().shutdown()
        except Exception:
            pass

        api_logger.info("✅ Cleanup completed")

    except Exception as e:
        api_logger.error(f"❌ Error during shutdown: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title="Archon Knowledge Engine API",
    description="Backend API for the Archon knowledge management and project automation platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
origins = [
    "https://archon-ui-wiwy.onrender.com",
    "https://enduser-ui-fe.onrender.com",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:3737",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(test_api_router) # NEW ROUTER
# Add middleware to skip logging for health checks
@app.middleware("http")
async def skip_health_check_logs(request, call_next):
    # Skip logging for health check endpoints
    if request.url.path in ["/health", "/api/health"]:
        # Temporarily suppress the log
        import logging

        logger = logging.getLogger("uvicorn.access")
        old_level = logger.level
        logger.setLevel(logging.ERROR)
        response = await call_next(request)
        logger.setLevel(old_level)
        return response
    return await call_next(request)


# Include API routers
app.include_router(settings_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

# app.include_router(mcp_client_router)  # Removed - not part of new architecture
app.include_router(knowledge_router)
app.include_router(projects_router)
app.include_router(progress_router)
app.include_router(agent_chat_router)
app.include_router(internal_router)
app.include_router(agents_router)
app.include_router(admin_router)  # NEW ROUTER
app.include_router(auth_router)
app.include_router(blog_router)
app.include_router(bug_report_router)
app.include_router(changes_router, prefix="/api")
app.include_router(log_router)
app.include_router(ethics_router)
app.include_router(files_router)
app.include_router(version_router)
app.include_router(providers_router)
app.include_router(ollama_router)
app.include_router(migration_router)
app.include_router(agents_router)
app.include_router(stats_router)
app.include_router(marketing_router)
app.include_router(system_router)
app.include_router(prompts_router)
app.include_router(visit_log_router)
app.include_router(extraction_router) # NEW ROUTER (GAP-018)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Archon Knowledge Engine API",
        "version": "1.0.0",
        "description": "Backend API for knowledge management and project automation",
        "status": "healthy",
        "modules": ["settings", "mcp", "mcp-clients", "knowledge", "projects"],
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint that indicates true readiness including credential loading."""
    from datetime import datetime

    # Check if initialization is complete
    if not _initialization_complete:
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
            "schema_valid": False
        }

    return {
        "status": "healthy",
        "service": "archon-backend",
        "timestamp": datetime.now().isoformat(),
        "ready": True,
        "credentials_loaded": True,
        "schema_valid": True,
    }


# API health check endpoint (alias for /health at /api/health)
@app.get("/api/health")
async def api_health_check():
    """API health check endpoint - alias for /health."""
    return await health_check()


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
    if (_schema_check_cache.get("valid") is False and
        current_time - last_checked < 30):
        return _schema_check_cache.get("result", {"valid": False, "message": "Schema check recently failed."})

    try:
        from .services.client_manager import get_supabase_client
        client = get_supabase_client()

        # Check if the 'archon_projects' table exists.
        client.table('archon_projects').select('id').limit(1).execute()

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
                "message": "Projects table not detected. This is required for the projects feature."
            }
            # Cache failed result
            _schema_check_cache["valid"] = False
            _schema_check_cache["checked_at"] = current_time
            _schema_check_cache["result"] = result
            return result

        # For other errors, consider the schema valid to not block other functionalities,
        # but log the error.
        api_logger.warning(f"Inconclusive schema check: {error_msg}")
        # To be safe, let's not block the app for other errors.
        # The original code returned true for inconclusive results.
        return {"valid": True, "message": f"Schema check inconclusive: {str(e)}"}


# Export the app directly for uvicorn to use


def main():
    """Main entry point for running the server."""
    import uvicorn

    # Require ARCHON_SERVER_PORT to be set
    server_port = os.getenv("ARCHON_SERVER_PORT")
    if not server_port:
        raise ValueError(
            "ARCHON_SERVER_PORT environment variable is required. "
            "Please set it in your .env file or environment. "
            "Default value: 8181"
        )

    uvicorn.run(
        "src.server.main:app",
        host="0.0.0.0",
        port=int(server_port),
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
