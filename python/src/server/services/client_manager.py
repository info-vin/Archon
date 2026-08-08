"""
Client Manager Service

Manages database and API client connections.
"""

import re
import time
from functools import wraps

from postgrest._sync.request_builder import SyncQueryRequestBuilder
from supabase import Client, create_client

from ..config.logfire_config import search_logger

# --- Monkey Patch: Supabase Anti-Drop Resilience ---
# Intercepts all synchronous execute() calls to handle HTTP/2 ConnectionTerminated
# errors caused by Hugging Face proxy idle timeouts.
_original_execute = SyncQueryRequestBuilder.execute

@wraps(_original_execute)
def _robust_execute(self, *args, **kwargs):
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            return _original_execute(self, *args, **kwargs)
        except Exception as e:
            err_str = str(e).lower()
            if "connectionterminated" in err_str or "connection dropped" in err_str or "remote protocol error" in err_str or "eof occurred" in err_str:
                if attempt < max_retries:
                    search_logger.warning(f"⚠️ Supabase Connection dropped (attempt {attempt + 1}). Retrying...")
                    time.sleep(0.5 * (2 ** attempt))
                    continue
            raise e
    raise Exception("Max retries exceeded") # Fallback

SyncQueryRequestBuilder.execute = _robust_execute  # type: ignore
# --------------------------------------------------

# ...


def get_supabase_client() -> Client:
    """
    Get a Supabase client instance.

    Returns:
        Supabase client instance
    """
    from ..config.config import get_config

    config = get_config()
    url = config.supabase_url
    key = config.supabase_service_key

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")

    try:
        # Let Supabase handle connection pooling internally
        client = create_client(url, key)

        # Extract project ID from URL for logging purposes only
        match = re.match(r"https://([^.]+)\.supabase\.co", url)
        if match:
            project_id = match.group(1)
            search_logger.debug(f"Supabase client initialized - project_id={project_id}")

        return client
    except Exception as e:
        import logging
        logging.error(f"Failed to create Supabase client: {e}", exc_info=True)
        raise
