
"""
Credential management service for Archon backend (Facade Pattern)
Maintains backward compatibility while delegating logic to the credentials package.
"""
import os
import logging
from typing import Any
from .credentials.manager import CredentialManager, CredentialItem
from .credentials.encryption_util import EncryptionUtil
from ..config.logfire_config import get_logger

logger = get_logger(__name__)

# Re-export for backward compatibility
CredentialItem = CredentialItem

class CredentialService(CredentialManager):
    """Facade for CredentialManager to maintain backward compatibility."""
    pass

# Global instance maintained for the entire application
credential_service = CredentialService()

async def get_credential(key: str, default: Any = None) -> Any:
    """Convenience function to get a credential."""
    return await credential_service.get_credential(key, default)

async def set_credential(
    key: str, value: str, is_encrypted: bool = False, category: str | None = None, description: str | None = None
) -> bool:
    """Convenience function to set a credential."""
    return await credential_service.set_credential(key, value, is_encrypted, category, description)

async def initialize_credentials() -> None:
    """
    Initialize the credential service by loading all credentials 
    and setting environment variables (Full Functional Parity).
    """
    await credential_service.load_all_credentials()

    # Only set infrastructure/startup credentials as environment variables
    infrastructure_credentials = [
        "OPENAI_API_KEY", "HOST", "PORT", "MCP_TRANSPORT", 
        "LOGFIRE_ENABLED", "PROJECTS_ENABLED"
    ]

    # LLM provider credentials (for sync client support)
    provider_credentials = [
        "GOOGLE_API_KEY", "GEMINI_API_KEY", "LLM_PROVIDER", 
        "LLM_BASE_URL", "EMBEDDING_MODEL", "MODEL_CHOICE"
    ]

    # Note: RAG and Code Extraction settings are Looked up on-demand 
    # and NOT set as env vars to prevent environment pollution.

    # Set infrastructure credentials
    for key in infrastructure_credentials:
        try:
            value = await credential_service.get_credential(key, decrypt=True)
            if value:
                os.environ[key] = str(value)
                logger.debug(f"Mapped infra env: {key}")
        except Exception as e:
            logger.warning(f"Failed to set infrastructure env {key}: {e}")

    # Set provider credentials with proper environment variable names (UPPERCASE)
    for key in provider_credentials:
        try:
            value = await credential_service.get_credential(key, decrypt=True)
            if value:
                env_key = key.upper()
                os.environ[env_key] = str(value)
                logger.debug(f"Mapped provider env: {env_key}")
        except Exception:
            pass

    logger.info("✅ Credentials initialized and physical environment mapped")
