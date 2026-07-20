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
# ruff: noqa: E402

import os
import warnings

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

# Suppress the noisy transformers LambdaRuntimeClient deprecation warnings
warnings.filterwarnings("ignore", message=".*LambdaRuntimeClient.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="transformers")
# Suppress FastAPIDeprecationWarning from fastapi package
warnings.filterwarnings("ignore", category=DeprecationWarning, module="fastapi")
warnings.filterwarnings("ignore", message=".*regex.*")

import logging

try:
    import transformers.utils.logging as transformers_logging
    transformers_logging.set_verbosity_error()
except ImportError:
    pass
logging.getLogger("transformers").setLevel(logging.ERROR)

class UvicornBotFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.args and isinstance(record.args, tuple) and len(record.args) >= 3:
            try:
                status = record.args[4] if len(record.args) >= 5 else None
                path = record.args[2] if len(record.args) >= 3 else ""

                # Hide noisy health checks
                if path in ["/health", "/api/health", "/"] and status == 200:
                    return False

                # Best practice: Suppress all 404 and 401 responses in the access log
                # to completely silence vulnerability scanners and bots.
                if status in (404, 401):
                    return False
            except Exception:
                pass
        return True

logging.getLogger("uvicorn.access").addFilter(UvicornBotFilter())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.server.core import (
    check_system_health,
    global_exception_handler,
    lifespan,
)

from .api_routes.admin_api import router as admin_router  # NEW IMPORT
from .api_routes.agent_chat_api import router as agent_chat_router
from .api_routes.agents_api import router as agents_router  # MISSING
from .api_routes.audio_api import router as audio_router
from .api_routes.auth_api import router as auth_router  # NEW IMPORT
from .api_routes.blog_api import router as blog_router
from .api_routes.bug_report_api import router as bug_report_router
from .api_routes.changes_api import router as changes_router  # NEW IMPORT
from .api_routes.ethics_api import router as ethics_router  # NEW IMPORT
from .api_routes.extraction_api import router as extraction_router  # NEW IMPORT (GAP-018)
from .api_routes.game_api import router as game_router
from .api_routes.internal_api import router as internal_router
from .api_routes.internal_llm_api import router as internal_llm_router  # NEW IMPORT
from .api_routes.knowledge_api import router as knowledge_router
from .api_routes.log_api import router as log_router
from .api_routes.marketing_api import router as marketing_router  # NEW IMPORT
from .api_routes.mcp_api import router as mcp_api_router  # NEW IMPORT
from .api_routes.migration_api import router as migration_router
from .api_routes.progress_api import router as progress_router
from .api_routes.projects_api import router as projects_router
from .api_routes.prompts_api import router as prompts_router  # MISSING
from .api_routes.providers_api import router as providers_router
from .api_routes.rag_api import router as rag_router  # NEW IMPORT
from .api_routes.settings_api import router as settings_router
from .api_routes.sse_api import router as sse_router  # NEW IMPORT
from .api_routes.stats_api import router as stats_router
from .api_routes.system_api import router as system_router  # NEW IMPORT
from .api_routes.test_api import router as test_api_router  # NEW IMPORT
from .api_routes.version_api import router as version_router
from .api_routes.visit_log_api import router as visit_log_router  # NEW IMPORT
from .middleware.budget_guard import BudgetGuardMiddleware

# Import Logfire configuration

# Create FastAPI application
app = FastAPI(
    title="Archon Knowledge Engine API",
    description="Backend API for the Archon knowledge management and project automation platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_exception_handler(Exception, global_exception_handler)

# Configure CORS
origins = [
    "https://archon-ui-wiwy.onrender.com",
    "https://enduser-ui-fe.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:3737",
    "http://enduser-ui:5173",
    "http://archon-ui:3737",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BudgetGuardMiddleware)


app.include_router(test_api_router)  # NEW ROUTER
app.include_router(internal_llm_router)


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


# --- API Routing Standardized (Phase 4.6.34) ---
# Group 1: Routers that ALREADY define "/api" in their internal prefix (No extra prefix needed)
app.include_router(projects_router)
app.include_router(marketing_router)
app.include_router(admin_router)
app.include_router(blog_router)
app.include_router(stats_router)
app.include_router(mcp_api_router)
app.include_router(visit_log_router)
app.include_router(version_router)
app.include_router(log_router)
app.include_router(bug_report_router)
app.include_router(changes_router)
app.include_router(extraction_router)
app.include_router(ethics_router)
app.include_router(providers_router)
app.include_router(migration_router)
app.include_router(system_router)
app.include_router(sse_router)
app.include_router(agent_chat_router)
app.include_router(audio_router)
app.include_router(progress_router)
app.include_router(knowledge_router)
app.include_router(agents_router)
app.include_router(prompts_router)

# Group 2: Routers that NEED an "/api" prefix (defined without prefix internally)
app.include_router(auth_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(game_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(internal_router)  # Already defines /internal

app.include_router(test_api_router)

@app.get("/api/mcp-logs")
async def get_mcp_logs():
    import os

    from fastapi.responses import FileResponse
    log_path = os.getenv("ARCHON_MCP_LOG_PATH", "/tmp/mcp_server.log")
    if os.path.exists(log_path):
        return FileResponse(log_path)
    return {"error": "Log file not found"}


# Root endpoint
@app.get("/")
@app.head("/")
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
@app.head("/health")
async def health_check_route():
    """Health check endpoint that indicates true readiness including credential loading."""
    return await check_system_health()


# API health check endpoint (alias for /health at /api/health)
@app.get("/api/health")
async def api_health_check_route():
    """API health check endpoint - alias for /health."""
    return await check_system_health()


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
