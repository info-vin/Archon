"""
Main FastAPI application for Archon.

This application serves as the central hub for all Archon services,
including project management, real-time collaboration, and AI agent interactions.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Unified logging configuration
from .config.logfire_config import configure_logfire, get_logger
from .utils import get_supabase_client

# Import API routers
from .api_routes import (
    auth_api,
    files_api,
    log_api,
    mcp_api,
    progress_api,
    projects_api,
    settings_api,
)
from .services.client_manager import close_all_clients
from .services.health_service import HealthService
from .services.projects.background_crawler import BackgroundCrawler
from .services.projects.task_manager import TaskManager

# Configure Logfire for structured, observable logging
configure_logfire()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Initializes and closes resources like Supabase clients and background tasks.
    """
    logger.info("Application starting up...")

    # Initialize Supabase client on startup
    try:
        get_supabase_client()
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")

    # Initialize and start background crawler
    try:
        crawler = BackgroundCrawler()
        asyncio.create_task(crawler.start())
        app.state.crawler = crawler
        logger.info("Background crawler started.")
    except Exception as e:
        logger.error(f"Failed to start background crawler: {e}")

    # Initialize task manager
    try:
        task_manager = TaskManager()
        app.state.task_manager = task_manager
        logger.info("Task manager initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize task manager: {e}")

    yield  # Application is now running

    # Shutdown logic
    logger.info("Application shutting down...")
    if hasattr(app.state, "crawler") and app.state.crawler:
        await app.state.crawler.stop()
        logger.info("Background crawler stopped.")

    # Close any open HTTPX clients
    await close_all_clients()
    logger.info("All HTTPX clients closed.")


app = FastAPI(
    title="Archon API",
    description="Powering the Archon knowledge and task management engine.",
    version="1.2.0",
    lifespan=lifespan,
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3737",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_api.router)
app.include_router(files_api.router)
app.include_router(log_api.router)
app.include_router(mcp_api.router)
app.include_router(progress_api.router)
app.include_router(projects_api.router)
app.include_router(settings_api.router)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Performs a comprehensive health check of the application and its dependencies.
    """
    try:
        health_service = HealthService()
        health_status = health_service.get_system_health()
        
        if health_status["status"] == "healthy":
            logger.info("Health check successful.")
            return health_status
        else:
            logger.warning(f"Health check indicates a degraded state: {health_status}")
            return JSONResponse(
                status_code=503,
                content=health_status,
            )

    except Exception as e:
        logger.error(f"Health check failed with an unexpected exception: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": "An unexpected error occurred during health check.",
                "error": str(e)
            },
        )


@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing basic information about the API.
    """
    return {
        "message": "Welcome to the Archon API. See /docs for documentation.",
        "version": app.version,
        "status": "running",
    }


# Optional: Add a custom exception handler for better error formatting
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Generic exception handler to catch unhandled errors and return a
    standardized JSON response.
    """
    logger.error(f"Unhandled exception for request {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": str(exc)},
    )
