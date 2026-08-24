import json
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from src.server.config.logfire_config import get_logger
from src.server.services.settings_service import SettingsService

logger = get_logger(__name__)

@asynccontextmanager
async def sync_notebooklm_session(settings: SettingsService, profile_name: str = "default") -> AsyncGenerator[str, None]:
    """
    Context manager for NotebookLM session state synchronization.

    Bi-directional Sync:
    - Pre-run: Synchronizes the token from SettingsService to the physical JSON file.
    - Post-run: Reads the potentially refreshed JSON file and writes it back to SettingsService.

    This respects the persistence mechanism of notebooklm-py while enforcing DB as SSOT.
    """
    base_dir = os.getenv("NOTEBOOKLM_DATA_DIR", os.path.join(os.path.expanduser("~"), ".notebooklm"))
    auth_json_path = os.path.join(base_dir, "profiles", profile_name, "storage_state.json")

    # Pre-run: DB -> File
    try:
        auth_json = settings.get_setting("notebooklm_auth_json", default=None)

        # We always want the DB to be the source of truth when we start.
        # But if the file exists and the DB is empty (rare edge case), we might keep the file.
        # Otherwise, write the DB json to the file.
        if auth_json:
            os.makedirs(os.path.dirname(auth_json_path), exist_ok=True)
            with open(auth_json_path, "w", encoding="utf-8") as f:
                f.write(auth_json)
        elif not os.path.exists(auth_json_path):
            logger.warning(f"No notebooklm_auth_json found in DB and no local file at {auth_json_path}")
    except Exception as e:
        logger.error(f"Error syncing NotebookLM DB to File: {e}")

    try:
        # Yield the base config directory. notebooklm-py defaults to reading `{base_dir}/profiles/default/storage_state.json`
        yield base_dir
    finally:
        # Post-run: File -> DB
        try:
            if os.path.exists(auth_json_path):
                with open(auth_json_path, encoding="utf-8") as f:
                    new_auth_json = f.read()

                # Basic validation that it's JSON
                try:
                    parsed = json.loads(new_auth_json)
                    if isinstance(parsed, dict) and new_auth_json != auth_json:
                        settings.set_setting("notebooklm_auth_json", json.dumps(parsed))
                        logger.info("Successfully synced refreshed NotebookLM session back to SettingsService.")
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in storage_state.json, skipping DB sync.")
        except Exception as e:
            logger.error(f"Error syncing NotebookLM File to DB: {e}")
