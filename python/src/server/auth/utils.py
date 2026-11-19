from typing import Any

from fastapi import HTTPException, status
from supabase.client import Client

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_user_from_token(token: str) -> Any:
    """Verify the bearer token with the Supabase Auth server."""
    try:
        supabase: Client = get_supabase_client()
    except Exception as exc:
        logger.error("Token verification could not reach the auth client (%s)", type(exc).__name__)
        raise _unauthorized() from None

    try:
        user_response = supabase.auth.get_user(token)
    except Exception as exc:
        logger.warning("Supabase auth.get_user rejected the token (%s)", type(exc).__name__)
        raise _unauthorized() from None

    user = getattr(user_response, "user", None) if user_response else None
    if not user:
        logger.warning("Supabase auth.get_user returned no user")
        raise _unauthorized()

    return user
