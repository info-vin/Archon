# python/src/server/auth/utils.py

from supabase.client import Client

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

async def get_user_from_token(token: str) -> dict | None:
    """
    Verifies the JWT token by calling Supabase Auth API.
    Returns the user object if valid, None otherwise.

    Args:
        token: The Bearer token string (without 'Bearer ' prefix)
    """
    try:
        supabase: Client = get_supabase_client()

        # Verify token via Supabase GoTrue API
        # This ensures the token is valid, not expired, and not revoked
        user_response = supabase.auth.get_user(token)

        if not user_response.user:
            logger.warning("Token verification failed: No user returned")
            return None

        return user_response.user

    except Exception as e:
        # Log warning but don't crash - invalid tokens happen
        logger.warning(f"Token verification failed: {str(e)}")
        return None
