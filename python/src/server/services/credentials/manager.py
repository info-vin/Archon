import os
import re
import time
from dataclasses import dataclass
from typing import Any, cast

from supabase import Client, create_client

from ...config.logfire_config import get_logger
from .encryption_util import EncryptionUtil

logger = get_logger(__name__)


@dataclass
class CredentialItem:
    """
    Represents a credential/setting item.

    This is used primarily for the Settings UI to represent the state
    of a specific configuration key.
    """

    key: str
    value: str | None = None
    encrypted_value: str | None = None
    is_encrypted: bool = False
    category: str | None = None
    description: str | None = None


class CredentialManager:
    """
    Service for managing application credentials and configuration.

    Handles loading, storing, and accessing credentials with encryption
    for sensitive values. Credentials include API keys, service credentials,
    and application configuration stored in the archon_settings table.
    """

    def __init__(self):
        self._supabase: Client | None = None
        self._cache: dict[str, Any] = {}
        self._cache_initialized = False
        self._rag_settings_cache: dict[str, Any] | None = None
        self._rag_cache_timestamp: float | None = None
        self._rag_cache_ttl = 300  # 5 minutes TTL for RAG settings cache

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
            supabase = self._get_supabase_client()

            # Fetch all credentials from archon_settings
            result = supabase.table("archon_settings").select("*").execute()

            credentials = {}
            for item in result.data:
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
                    # SELF-DELEGATION: Use internal method to allow object-level mocking in tests
                    return self._decrypt_value(encrypted_value)
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
            supabase = self._get_supabase_client()

            data: dict[str, Any] = {
                "key": key,
                "is_encrypted": is_encrypted,
                "category": category,
                "description": description,
            }

            if is_encrypted:
                # SELF-DELEGATION: Use internal method to allow object-level mocking in tests
                data["encrypted_value"] = self._encrypt_value(value)
                data["value"] = None
            else:
                data["value"] = value
                data["encrypted_value"] = None

            # Upsert to database with proper conflict handling
            supabase.table("archon_settings").upsert(
                data,
                on_conflict="key",
            ).execute()

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
            supabase = self._get_supabase_client()

            # Execute delete on Supabase
            supabase.table("archon_settings").delete().eq("key", key).execute()

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
            supabase = self._get_supabase_client()
            result = supabase.table("archon_settings").select("*").eq("category", category).execute()

            credentials = {}
            for item in result.data:
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
            supabase = self._get_supabase_client()
            result = supabase.table("archon_settings").select("*").execute()

            credentials = []
            for item in result.data:
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

    async def check_credentials_exist(self, keys: list[str]) -> dict[str, dict[str, Any]]:
        """
        Check if a list of credentials exist and have a value.
        Returns a dictionary with the status for each key.
        """
        if not self._cache_initialized:
            await self.load_all_credentials()

        statuses = {}
        for key in keys:
            value = self._cache.get(key)
            has_value = False
            if value:
                if isinstance(value, dict) and value.get("is_encrypted"):
                    if value.get("encrypted_value"):
                        has_value = True
                elif isinstance(value, str) and value:
                    has_value = True

            # Step 2: Environment variable fallback (Physical Hardening)
            if not has_value:
                env_value = os.getenv(key) or os.getenv(key.upper())
                if not env_value and key == "GOOGLE_API_KEY":
                    env_value = os.getenv("GEMINI_API_KEY")
                if env_value and env_value.strip():
                    has_value = True

            statuses[key] = {"key": key, "has_value": has_value}

        return statuses

    def get_config_as_env_dict(self) -> dict[str, str]:
        """
        Get configuration as environment variable style dict.
        Note: This returns plain text values only.
        """
        if not self._cache_initialized:
            logger.warning("Credentials not loaded, returning empty config")
            return {}

        env_dict = {}
        for key, value in self._cache.items():
            if isinstance(value, dict) and value.get("is_encrypted"):
                continue
            else:
                env_dict[key] = str(value) if value is not None else ""

        return env_dict

    async def get_active_provider(self, service_type: str = "llm") -> dict[str, Any]:
        """
        Get the currently active provider configuration.
        Searches across critical categories with deep fallback to OS environment.
        """
        try:
            ai_settings = await self.get_credentials_by_category("ai")
            marketing_settings = await self.get_credentials_by_category("marketing")
            rag_settings = await self.get_credentials_by_category("rag_strategy")

            all_settings = {**ai_settings, **marketing_settings, **rag_settings}

            provider_key = "LLM_PROVIDER" if service_type == "llm" else "EMBEDDING_PROVIDER"
            provider = all_settings.get(provider_key)

            if not provider:
                provider = os.getenv(provider_key, "openai").lower()

            api_key = await self._get_provider_api_key(provider)
            base_url = self._get_provider_base_url(provider, all_settings)

            chat_model = all_settings.get("MODEL_CHOICE") or all_settings.get("MARKETING_MODEL") or ""
            embedding_model = all_settings.get("EMBEDDING_MODEL", "")

            return {
                "provider": provider,
                "api_key": api_key,
                "base_url": base_url,
                "chat_model": chat_model,
                "embedding_model": embedding_model,
            }

        except Exception as e:
            logger.error(f"Error getting active provider for {service_type}: {e}")
            provider = os.getenv("LLM_PROVIDER", "openai")
            return {
                "provider": provider,
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": None,
                "chat_model": "",
                "embedding_model": "",
            }

    async def get_embedding_provider_configs(self) -> list[dict[str, Any]]:
        """
        Get the currently active primary and fallback embedding provider configurations.
        Designed for failover and separate from the main LLM provider logic.
        """
        configs = []
        try:
            rag_settings = await self.get_credentials_by_category("rag_strategy")

            provider_types = [
                {"type": "primary", "suffix": ""},
                {"type": "fallback", "suffix": "_FALLBACK"},
            ]

            for pt in provider_types:
                provider_key = f"EMBEDDING_PROVIDER{pt['suffix']}"
                model_key = f"EMBEDDING_MODEL{pt['suffix']}"
                api_key_override_key = f"EMBEDDING_API_KEY{pt['suffix']}"

                provider = rag_settings.get(provider_key)
                if not provider:
                    if pt["type"] == "primary":
                        provider = rag_settings.get("LLM_PROVIDER", "openai")
                    else:
                        continue

                embedding_model = rag_settings.get(model_key)
                if not embedding_model and pt["type"] == "primary":
                    embedding_model = rag_settings.get("EMBEDDING_MODEL")

                if not provider or not embedding_model:
                    continue

                api_key = await self.get_credential(api_key_override_key)
                if not api_key:
                    api_key = await self._get_provider_api_key(provider)

                base_url = self._get_provider_base_url(provider, rag_settings)

                if api_key:
                    configs.append(
                        {
                            "provider": provider,
                            "api_key": api_key,
                            "base_url": base_url,
                            "embedding_model": embedding_model,
                        }
                    )

            return configs

        except Exception as e:
            logger.error(f"Error getting embedding provider configs: {e}")
            return []

    async def _get_provider_api_key(self, provider: str) -> str | None:
        """Get API key for a specific provider."""
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "ollama": None,
        }

        key_name = key_mapping.get(provider)
        if key_name:
            return cast(str | None, await self.get_credential(key_name))
        return "ollama" if provider == "ollama" else None

    def _get_provider_base_url(self, provider: str, rag_settings: dict) -> str | None:
        """Get base URL for provider."""
        if provider == "ollama":
            return cast(str | None, rag_settings.get("LLM_BASE_URL", "http://localhost:11434/v1"))
        elif provider == "google":
            return "https://generativelanguage.googleapis.com/v1beta/openai/"
        return None

    async def set_active_provider(self, provider: str, service_type: str = "llm") -> bool:
        """Set the active provider for a service type."""
        try:
            return await self.set_credential(
                "llm_provider",
                provider,
                category="rag_strategy",
                description=f"Active {service_type} provider",
            )
        except Exception as e:
            logger.error(f"Error setting active provider {provider} for {service_type}: {e}")
            return False

    # BACKWARD COMPATIBILITY ALIASES (Physical Alignment with Phase 4.6 Legacy)
    def _encrypt_value(self, value: str) -> str:
        return EncryptionUtil.encrypt_value(value)

    def _decrypt_value(self, encrypted_value: str) -> str:
        return EncryptionUtil.decrypt_value(encrypted_value)

    def _get_encryption_key(self) -> bytes:
        return EncryptionUtil.get_encryption_key()
