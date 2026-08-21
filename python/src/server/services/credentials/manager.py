import os
import re
import time
from typing import TYPE_CHECKING, Any, TypeVar

from supabase import Client, create_client

from ...config.logfire_config import get_logger
from .crypto_utils import CryptoUtils
from .models import CredentialItem

if TYPE_CHECKING:
    from .repository import CredentialRepository

T = TypeVar("T")

logger = get_logger(__name__)


class CredentialManager:
    """
    Service for managing application credentials and configuration.

    Handles loading, storing, and accessing credentials with encryption
    for sensitive values. Credentials include API keys, service credentials,
    and application configuration stored in the archon_settings table.
    """

    def __init__(self) -> None:
        self._supabase: Client | None = None
        self._repository: Any | None = None
        self._cache: dict[str, Any] = {}
        self._cache_initialized = False
        self._rag_settings_cache: dict[str, Any] | None = None
        self._rag_cache_timestamp: float | None = None
        self._rag_cache_ttl = 300  # 5 minutes TTL for RAG settings cache
        self._active_tier = 1

    def get_active_tier(self) -> int:
        """Get the currently active model tier (1, 2, or 3)."""
        return getattr(self, "_active_tier", 1)

    def set_active_tier(self, tier: int) -> None:
        """Set the active model tier (1, 2, or 3)."""
        self._active_tier = tier

    def _get_repository(self) -> "CredentialRepository":
        """Get or create the CredentialRepository."""
        if self._repository is None:
            from .repository import CredentialRepository
            self._repository = CredentialRepository(self._get_supabase_client())
        return self._repository

    def _get_supabase_client(self) -> Client:
        """
        Get or create a properly configured Supabase client using environment variables.
        Uses the standard Supabase client initialization.

        Returns:
            A configured Supabase Client instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        if self._supabase is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")

            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")

            try:
                # Initialize with standard Supabase client - no need for custom headers
                self._supabase = create_client(url, key)

                # Extract project ID from URL for logging purposes only
                match = re.match(r"https://([^.]+)\.supabase\.co", url)
                if match:
                    project_id = match.group(1)
                    logger.debug(f"Supabase client initialized for project: {project_id}")
                else:
                    logger.debug("Supabase client initialized successfully")

            except Exception as e:
                logger.error(f"Error initializing Supabase client: {e}")
                raise

        return self._supabase

    async def load_all_credentials(self) -> dict[str, Any]:
        """
        Load all credentials from database and cache them.
        This is typically called at system startup via initialize_credentials.

        Returns:
            A dictionary of all loaded credentials.
        """
        try:
            repository = self._get_repository()
            data = repository.fetch_all()

            credentials = {}
            for item in data:
                key = item["key"]
                if item["is_encrypted"] and item["encrypted_value"]:
                    # For encrypted values, we store the encrypted version
                    # Decryption happens when the value is actually needed via get_credential
                    credentials[key] = {
                        "encrypted_value": item["encrypted_value"],
                        "is_encrypted": True,
                        "category": item["category"],
                        "description": item["description"],
                    }
                else:
                    # Plain text values are stored directly
                    credentials[key] = item["value"]

            self._cache = credentials
            self._cache_initialized = True
            logger.info(f"Loaded {len(credentials)} credentials from database")

            return credentials

        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            raise

    async def get_credential(self, key: str, default: Any = None, decrypt: bool = True) -> Any:
        """
        Get a credential value by key.

        This method checks the internal cache first, and falls back to OS
        environment variables if the key is not found or empty in the database.

        Args:
            key: The configuration key to look up.
            default: Value to return if the key is not found.
            decrypt: Whether to automatically decrypt encrypted values.

        Returns:
            The credential value, or the default value if not found.
        """
        if not self._cache_initialized:
            await self.load_all_credentials()

        value = self._cache.get(key, default)

        # If it's an encrypted value and we want to decrypt it
        if isinstance(value, dict) and value.get("is_encrypted") and decrypt:
            encrypted_value = value.get("encrypted_value")
            if encrypted_value:
                try:
                    return CryptoUtils.decrypt_value(encrypted_value)
                except Exception as e:
                    logger.error(f"Failed to decrypt credential {key}: {e}")
                    return default

        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped

        # PHYSICAL FALLBACK: If not in cache or is empty string, check OS environment
        # This allows environment variables to override or provide defaults for missing settings
        env_value = os.getenv(key) or os.getenv(key.upper())
        if env_value:
            return env_value

        return value

    async def get_encrypted_credential_raw(self, key: str) -> str | None:
        """
        Get the raw encrypted value for a credential (without decryption).

        Args:
            key: The configuration key.

        Returns:
            The raw encrypted string or None.
        """
        if not self._cache_initialized:
            await self.load_all_credentials()

        value = self._cache.get(key)
        if isinstance(value, dict) and value.get("is_encrypted"):
            return value.get("encrypted_value")

        return None

    async def set_credential(
        self,
        key: str,
        value: str,
        is_encrypted: bool = False,
        category: str | None = None,
        description: str | None = None,
    ) -> bool:
        """
        Set a credential/setting in the database.

        Args:
            key: Setting key
            value: Plain text value
            is_encrypted: Whether to encrypt the value before storing
            category: Optional category for grouping
            description: Optional description

        Returns:
            True if successful, False otherwise
        """
        try:
            data: dict[str, Any] = {
                "key": key,
                "is_encrypted": is_encrypted,
                "category": category,
                "description": description,
            }

            if is_encrypted:
                data["encrypted_value"] = CryptoUtils.encrypt_value(value)
                data["value"] = None
            else:
                data["value"] = value
                data["encrypted_value"] = None

            # Upsert to database via repository
            repository = self._get_repository()
            repository.upsert(data)

            # Invalidate RAG settings cache if this is a rag_strategy setting
            if category == "rag_strategy":
                self._rag_settings_cache = None
                self._rag_cache_timestamp = None
                logger.debug(f"Invalidated RAG settings cache due to update of {key}")

            logger.info(f"Successfully {'encrypted and ' if is_encrypted else ''}stored credential: {key}")
            return True

        except Exception as e:
            logger.error(f"Error setting credential {key}: {e}")
            return False

    async def delete_credential(self, key: str) -> bool:
        """
        Delete a credential from database and cache.

        Args:
            key: The key to delete.

        Returns:
            True if successful.
        """
        try:
            # Execute delete via repository
            repository = self._get_repository()
            repository.delete(key)

            # Remove from local cache
            if key in self._cache:
                del self._cache[key]

            # Invalidate RAG settings cache if needed
            if self._rag_settings_cache is not None and key in self._rag_settings_cache:
                self._rag_settings_cache = None
                self._rag_cache_timestamp = None
                logger.debug(f"Invalidated RAG settings cache due to deletion of {key}")

            logger.info(f"Successfully deleted credential: {key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting credential {key}: {e}")
            return False

    async def get_credentials_by_category(self, category: str) -> dict[str, Any]:
        """
        Get all credentials for a specific category.

        Special caching is applied for the 'rag_strategy' category to
        reduce redundant database calls during high-frequency RAG operations.
        """
        if not self._cache_initialized:
            await self.load_all_credentials()

        # Special caching for rag_strategy category
        if category == "rag_strategy":
            current_time = time.time()
            if (
                self._rag_settings_cache is not None
                and self._rag_cache_timestamp is not None
                and current_time - self._rag_cache_timestamp < self._rag_cache_ttl
            ):
                logger.debug("Using cached RAG settings")
                return self._rag_settings_cache

        try:
            repository = self._get_repository()
            data = repository.fetch_by_category(category)

            credentials = {}
            for item in data:
                key = item["key"]
                if item["is_encrypted"]:
                    credentials[key] = {
                        "value": "[ENCRYPTED]",
                        "is_encrypted": True,
                        "category": item["category"],
                        "description": item["description"],
                    }
                else:
                    credentials[key] = item["value"]

            # Cache rag_strategy results
            if category == "rag_strategy":
                self._rag_settings_cache = credentials
                self._rag_cache_timestamp = time.time()
                logger.debug(f"Cached RAG settings with {len(credentials)} items")

            return credentials

        except Exception as e:
            logger.error(f"Error getting credentials for category {category}: {e}")
            return {}

    async def list_all_credentials(self) -> list[CredentialItem]:
        """Get all credentials as a list of CredentialItem objects (for Settings UI)."""
        try:
            repository = self._get_repository()
            data = repository.fetch_non_system_protected()

            credentials = []
            for item in data:
                if item["is_encrypted"] and item["encrypted_value"]:
                    cred = CredentialItem(
                        key=item["key"],
                        value="[ENCRYPTED]",
                        encrypted_value=None,
                        is_encrypted=item["is_encrypted"],
                        category=item["category"],
                        description=item["description"],
                    )
                else:
                    cred = CredentialItem(
                        key=item["key"],
                        value=item["value"],
                        encrypted_value=None,
                        is_encrypted=item["is_encrypted"],
                        category=item["category"],
                        description=item["description"],
                    )
                credentials.append(cred)

            return credentials

        except Exception as e:
            logger.error(f"Error listing credentials: {e}")
            return []

    # --- Backward Compatibility / Proxy Wrappers ---
    # To satisfy tests and existing mocks without breaking physical mock integrity (Rule 13).

    async def check_credentials_exist(self, keys: list[str]) -> dict[str, dict[str, Any]]:
        from .helpers import check_credentials_exist
        return await check_credentials_exist(self, keys)


