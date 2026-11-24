import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ...config.logfire_config import get_logger

logger = get_logger(__name__)


class CryptoUtils:
    """Utilities for Fernet encryption and key management."""

    @staticmethod
    def _derive_fernet_key(secret: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"static_salt_for_credentials",
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(secret.encode()))

    @staticmethod
    def get_encryption_key() -> bytes:
        """Generate primary encryption key, preferring dedicated CREDENTIAL_ENCRYPTION_KEY."""
        from src.server.config.config import get_config

        config = get_config()
        secret = (
            getattr(config, "credential_encryption_key", None)
            or config.supabase_service_key
            or "default-key-for-development"
        )
        return CryptoUtils._derive_fernet_key(secret)

    @staticmethod
    def get_decryption_keys() -> list[bytes]:
        """Return candidate Fernet keys in priority order for zero-downtime key rotation."""
        from src.server.config.config import get_config

        config = get_config()
        candidates: list[str] = []
        for secret in (
            getattr(config, "credential_encryption_key", None),
            config.supabase_service_key or "default-key-for-development",
            getattr(config, "previous_supabase_service_key", None),
        ):
            if secret and secret not in candidates:
                candidates.append(secret)
        return [CryptoUtils._derive_fernet_key(secret) for secret in candidates]

    @staticmethod
    def encrypt_value(value: str) -> str:
        """Encrypt a sensitive value using Fernet encryption."""
        if not value:
            return ""
        try:
            fernet = Fernet(CryptoUtils.get_encryption_key())
            encrypted_bytes = fernet.encrypt(value.encode("utf-8"))
            return base64.urlsafe_b64encode(encrypted_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"Error encrypting value: {e}")
            raise

    @staticmethod
    def decrypt_value(encrypted_value: str) -> str:
        """Decrypt a sensitive value using Fernet encryption with dual-key rotation fallback."""
        if not encrypted_value:
            return ""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode("utf-8"))
        except Exception as e:
            logger.error(f"Error decoding encrypted value: {e}")
            raise

        last_error: Exception | None = None
        for key in CryptoUtils.get_decryption_keys():
            try:
                decrypted_bytes = Fernet(key).decrypt(encrypted_bytes)
                return str(decrypted_bytes.decode("utf-8"))
            except InvalidToken as e:
                last_error = e
                continue
            except Exception as e:
                logger.error(f"Error decrypting value: {e}")
                raise

        logger.error(f"Error decrypting value with all candidate keys: {last_error}")
        assert last_error is not None
        raise last_error
