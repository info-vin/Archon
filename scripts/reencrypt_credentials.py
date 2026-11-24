"""
One-time credential re-encryption script for zero-downtime SUPABASE_SERVICE_KEY rotation.

Usage:
    CREDENTIAL_ENCRYPTION_KEY=<new-secret> uv run python scripts/reencrypt_credentials.py --dry-run
    CREDENTIAL_ENCRYPTION_KEY=<new-secret> uv run python scripts/reencrypt_credentials.py
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

from src.server.config.logfire_config import get_logger, setup_logfire  # noqa: E402
from src.server.services.credentials.crypto_utils import CryptoUtils  # noqa: E402
from src.server.utils import get_supabase_client  # noqa: E402

setup_logfire()
logger = get_logger(__name__)


def reencrypt_all_credentials(dry_run: bool = False) -> tuple[int, int]:
    """Decrypt all encrypted archon_settings rows with candidate keys and re-encrypt with CREDENTIAL_ENCRYPTION_KEY."""
    if not os.getenv("CREDENTIAL_ENCRYPTION_KEY"):
        raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY must be set before running re-encryption.")

    supabase = get_supabase_client()
    response = (
        supabase.table("archon_settings")
        .select("id, key, encrypted_value, is_encrypted")
        .eq("is_encrypted", True)
        .execute()
    )
    rows = response.data or []
    updated = 0
    failed = 0

    for row in rows:
        key_name = row.get("key")
        encrypted_val = row.get("encrypted_value")
        if not encrypted_val:
            continue
        try:
            plaintext = CryptoUtils.decrypt_value(encrypted_val)
            new_ciphertext = CryptoUtils.encrypt_value(plaintext)
            if dry_run:
                logger.info(f"[DRY-RUN] Would re-encrypt setting '{key_name}' (id={row.get('id')})")
            else:
                supabase.table("archon_settings").update({"encrypted_value": new_ciphertext}).eq(
                    "id", row["id"]
                ).execute()
                logger.info(f"Re-encrypted setting '{key_name}' (id={row.get('id')})")
            updated += 1
        except Exception as e:
            logger.error(f"Failed to re-encrypt setting '{key_name}': {e}")
            failed += 1

    return updated, failed


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    parser = argparse.ArgumentParser(description="Re-encrypt archon_settings credentials using CREDENTIAL_ENCRYPTION_KEY")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to database")
    args = parser.parse_args()

    updated, failed = reencrypt_all_credentials(dry_run=args.dry_run)
    print(f"Re-encryption finished: updated={updated}, failed={failed}, dry_run={args.dry_run}")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
