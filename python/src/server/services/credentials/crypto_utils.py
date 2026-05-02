import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ...config.logfire_config import get_logger

logger = get_logger(__name__)


class CryptoUtils:
    """Utilities for Fernet encryption and key management."""

    @staticmethod
    def get_encryption_key() -> bytes:
        """Generate encryption key from environment variables."""
        service_key = os.getenv("SUPABASE_SERVICE_KEY", "default-key-for-development")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"static_salt_for_credentials",
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(service_key.encode()))

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
        """Decrypt a sensitive value using Fernet encryption."""
        if not encrypted_value:
            return ""
        try:
            fernet = Fernet(CryptoUtils.get_encryption_key())
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode("utf-8"))
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            return str(decrypted_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(f"Error decrypting value: {e}")
            raise
