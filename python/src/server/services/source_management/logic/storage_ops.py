"""
Database Operations for Source Management
Physically isolated to handle core persistence logic.
"""

import logging

from supabase import Client

from src.server.config.logfire_config import search_logger
from src.server.repositories.base_repository import BaseRepository
from src.server.services.source_management.logic.ai_metadata import generate_source_title_and_metadata

logger = logging.getLogger(__name__)


async def update_source_info(
    client: Client,
    source_id: str,
    summary: str,
    word_count: int,
    content: str = "",
    knowledge_type: str = "technical",
    tags: list[str] | None = None,
    update_frequency: int = 7,
    original_url: str | None = None,
    source_url: str | None = None,
    source_display_name: str | None = None,
):
    """Update or insert source information in the archon_sources table."""
    search_logger.info(f"Updating source {source_id} with knowledge_type={knowledge_type}")
    try:
        success, res = BaseRepository(client).execute_query(client.table("archon_sources").select("title").eq("source_id", source_id), "Fetch existing source title")
        existing_source = type("obj", (object,), {"data": res["data"] if success and isinstance(res, dict) and "data" in res else None})()

        if existing_source.data:
            existing_title = existing_source.data[0]["title"]
            search_logger.info(f"Preserving existing title for {source_id}: {existing_title}")
            search_logger.info(f"Updating existing source {source_id} metadata: knowledge_type={knowledge_type}")

            if source_url and source_url.startswith("file://"):
                source_type = "file"
            elif original_url and original_url.startswith("file://"):
                source_type = "file"
            else:
                source_type = "url"

            metadata = {
                "knowledge_type": knowledge_type,
                "tags": tags or [],
                "source_type": source_type,
                "auto_generated": False,
                "update_frequency": update_frequency,
            }
            if original_url:
                metadata["original_url"] = original_url

            update_data = {
                "summary": summary,
                "total_word_count": word_count,
                "metadata": metadata,
                "updated_at": "now()",
            }
            if source_url:
                update_data["source_url"] = source_url
            if source_display_name:
                update_data["source_display_name"] = source_display_name

            BaseRepository(client).execute_query(client.table("archon_sources").upsert(update_data).eq("source_id", source_id), "Update existing source metadata")
            search_logger.info(f"Updated source {source_id} while preserving title: {existing_title}")
        else:
            if source_display_name:
                title = source_display_name[:100].strip()
                if source_url and source_url.startswith("file://"):
                    source_type = "file"
                elif original_url and original_url.startswith("file://"):
                    source_type = "file"
                else:
                    source_type = "url"
                metadata = {
                    "knowledge_type": knowledge_type,
                    "tags": tags or [],
                    "source_type": source_type,
                    "auto_generated": False,
                }
            else:
                title, metadata = await generate_source_title_and_metadata(
                    source_id=source_id,
                    content=content,
                    knowledge_type=knowledge_type,
                    tags=tags,
                    original_url=original_url,
                    source_display_name=source_display_name,
                )
                if source_url and source_url.startswith("file://"):
                    metadata["source_type"] = "file"
                elif original_url and original_url.startswith("file://"):
                    metadata["source_type"] = "file"
                else:
                    metadata["source_type"] = "url"

            metadata["update_frequency"] = update_frequency
            if original_url:
                metadata["original_url"] = original_url

            search_logger.info(f"Creating new source {source_id} with knowledge_type={knowledge_type}")
            upsert_data = {
                "source_id": source_id,
                "title": title,
                "summary": summary,
                "total_word_count": word_count,
                "metadata": metadata,
            }
            if source_url:
                upsert_data["source_url"] = source_url
            if source_display_name:
                upsert_data["source_display_name"] = source_display_name

            BaseRepository(client).execute_query(client.table("archon_sources").upsert(upsert_data), "Upsert new source")
            search_logger.info(f"Created/updated source {source_id} with title: {title}")
    except Exception as e:
        search_logger.error(f"Error updating source {source_id}: {e}")
        raise


def create_source_from_upload_logic(
    client: Client,
    source_id: str,
    filename: str,
    knowledge_type: str,
    tags: list[str],
    chunks_stored: int,
    source_url: str | None = None,
) -> None:
    """Logic for creating source record from file upload."""
    search_logger.info(f"Creating source entry for uploaded file: {source_id}")
    metadata = {
        "knowledge_type": knowledge_type,
        "tags": tags or [],
        "source_type": "file",
        "file_name": filename,
        "status": "completed",
    }
    source_data = {
        "source_id": source_id,
        "title": filename,
        "source_display_name": filename,
        "summary": f"Content from uploaded file: {filename}",
        "total_word_count": 0,
        "metadata": metadata,
    }
    if source_url:
        source_data["source_url"] = source_url

    success, res_data = BaseRepository(client).execute_query(client.table("archon_sources").upsert(source_data), "Create source from upload")
    res = type("obj", (object,), {"error": not success})()
    if hasattr(res, "error") and res.error:
        search_logger.error(f"Supabase error creating source entry for {source_id}: {res.error}")
        raise Exception(f"Supabase error: {res.error}")
    search_logger.info(f"Successfully created source entry for {source_id}")
