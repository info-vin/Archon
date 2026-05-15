# python/src/server/core/lifespan.py

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.server.config.logfire_config import api_logger

from .app_state import app_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events cleanly.
    """
    api_logger.info("Starting Archon Backend application...")

    # Imports moved inside the lifespan function to prevent circular dependencies
    from src.agents.mcp_client import get_mcp_client
    from src.server.config.config import get_config
    from src.server.services.agent_service import agent_service
    from src.server.services.background_task_manager import cleanup_task_manager, get_task_manager
    from src.server.services.crawler_manager import cleanup_crawler
    from src.server.services.credential_service import initialize_credentials
    from src.server.services.log_service import log_service
    from src.server.services.prompt_service import prompt_service
    from src.server.services.scheduler_service import SchedulerService
    from src.server.services.search.reranking_strategy import reranking_strategy
    from src.server.services.system.worker_service import worker_service

    # Keep track of initialized components for cleanup
    initialized_components = set()

    try:
        # Load configuration
        get_config()

        # Phase 4.6.48: Physical SSOT Parity - Ensure credential table matches system specs
        api_logger.info("Aligning dynamic credentials from settings...")
        await initialize_credentials()
        initialized_components.add("credentials")

        # Set up logfire now that credentials are loaded
        from src.server.config.logfire_config import setup_logfire
        setup_logfire(service_name="archon-backend")
        api_logger.info("🔥 Logfire initialized for backend")

        # Phase 4.6.25: Pre-load Reranking model to eliminate cold-start latency
        if reranking_strategy.is_available():
            api_logger.info("Reranking model pre-loaded successfully.")
        else:
            api_logger.warning("Reranking model failed to pre-load.")
        initialized_components.add("models")

        # Initialize Prompt Service
        try:
            await prompt_service.load_prompts()
            api_logger.info("✅ Prompt service initialized")
        except Exception as e:
            api_logger.warning(f"Could not initialize prompt service: {e}")

        # Initialize MCP Client
        api_logger.info("Initializing MCP Client...")
        mcp_client = await get_mcp_client()

        # Initialize tool list to verify connection
        tools = await mcp_client.list_tools()
        if not tools:
            log_service.create_log_entry({
                "project_name": "mcp-neural-wiring",
                "gemini_response": "🧠 Agent Neural Wiring FAILED: MCP Client connected but returned 0 tools. Check volumes/permissions.",
                "user_input": f"mcp_url: {mcp_client.mcp_url}"
            })
        else:
            # Dependency Injection (Architectural Bridge)
            agent_service.mcp_client = mcp_client
            initialized_components.add("mcp_client")
            api_logger.info(f"🧠 Agent Neural Wiring Complete: MCP Client injected with {len(tools)} tools.")

        # Initialize Background Task Manager
        api_logger.info("Initializing Background Task Manager...")
        get_task_manager()

        # Initialize Sentinel / Scheduler
        api_logger.info("Waking up Sentinels (Scheduler Service)...")
        scheduler = SchedulerService()
        await scheduler.start()
        initialized_components.add("scheduler")
        # Initialize DB-based Worker Queue
        api_logger.info("Starting Worker Service Queue...")
        await worker_service.start()
        initialized_components.add("worker")

        # Signal that all initialization steps are complete
        app_state.initialization_complete = True
        api_logger.info("Archon Backend initialization completed successfully. Ready for requests.")

        yield

    except Exception as e:
        api_logger.error(f"Critical failure during startup: {str(e)}")
        # Propagate the error so the server fails to start
        raise

    finally:
        api_logger.info("Shutting down Archon Backend application...")
        app_state.initialization_complete = False

        # Clean up Background Task Manager FIRST
        try:
            api_logger.info("Cleaning up background task manager...")
            await cleanup_task_manager()
        except Exception as e:
            api_logger.error(f"Error cleaning up task manager: {e}")

        # Stop Scheduler
        if "scheduler" in initialized_components:
            try:
                scheduler = SchedulerService()
                scheduler.shutdown()
            except Exception as e:
                api_logger.error(f"Error stopping scheduler: {e}")

        # Stop Worker
        if "worker" in initialized_components:
            try:
                await worker_service.stop()
            except Exception as e:
                api_logger.error(f"Error stopping worker: {e}")

        # MCP Client cleanup not needed

        # Close specific browser instances
        try:
            await cleanup_crawler()
        except Exception as e:
            api_logger.error(f"Error during browser cleanup: {e}")

        # Close LLM clients (not needed)

        api_logger.info("Archon Backend shutdown complete.")
