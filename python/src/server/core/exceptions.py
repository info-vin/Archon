# python/src/server/core/exceptions.py

import traceback

from fastapi import Request
from fastapi.responses import JSONResponse

from src.server.config.logfire_config import api_logger


async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to capture all unhandled exceptions
    and return a standardized JSON response.
    """
    api_logger.error(f"🔥 Global Crash on {request.url.path}: {str(exc)}")
    api_logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )
