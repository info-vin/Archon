import os
from datetime import datetime

import aiofiles

from ..config.logfire_config import get_logger
from .librarian_service import LibrarianService

logger = get_logger(__name__)


class ScoutIngestionService:
    """
    Service to ingest Digital Twin Scout reports into the Knowledge Base (Phase 4.6.15).
    Closes the loop between automated diagnostics and RAG awareness.
    """

    def __init__(self, diagnostics_dir: str = "./.twin/diagnostics") -> None:
        self.diagnostics_dir = diagnostics_dir
        self.librarian = LibrarianService()

    async def ingest_reports(self) -> dict:
        """
        Scans for report_*.md files and indexes them via Librarian.
        Avoids redundant indexing and filters out infrastructure noise (e.g. connection failures).
        """
        if not os.path.exists(self.diagnostics_dir):
            return {"status": "error", "message": f"Directory {self.diagnostics_dir} not found"}

        reports = [f for f in os.listdir(self.diagnostics_dir) if f.startswith("report_") and f.endswith(".md")]

        if not reports:
            return {"status": "success", "message": "No new reports found", "count": 0}

        ingested_count = 0
        errors = []

        for report_file in reports:
            file_path = os.path.join(self.diagnostics_dir, report_file)
            try:
                async with aiofiles.open(file_path, encoding="utf-8") as f:
                    content = await f.read()

                # Triage: Filter out reports that are just connection errors
                noise_keywords = ["Connection refused", "ECONNREFUSED", "TimeoutError", "net::ERR_CONNECTION_REFUSED"]
                if any(k in content for k in noise_keywords) and "✅" not in content:
                    logger.warning(f"[Scout Ingestion] Skipping noisy infrastructure report: {report_file}")
                    continue

                # Deduplication check: Has this file been indexed?
                from ..repositories.base_repository import BaseRepository
                from ..utils import get_supabase_client

                supabase = get_supabase_client()
                base_repo = BaseRepository(supabase)
                success, existing_dict = base_repo.execute_query(
                    supabase.table("archon_sources") # 合法
                    .select("source_id")
                    .eq("metadata->>knowledge_type", "scout_report")
                    .eq("source_display_name", report_file),
                    error_context="Failed to query archon_sources"
                )

                if success and existing_dict.get("data"):
                    continue

                async with aiofiles.open(file_path, encoding="utf-8") as f:
                    content = await f.read()

                # Check if content is substantial
                if len(content.strip()) < 50:
                    continue

                # Index as a 'system' type knowledge item
                # Librarian handles chunking and embedding
                await self.librarian.archive_file(
                    file_name=report_file,
                    content=content,
                    file_path=f"scout://{report_file}",  # Unique source URL for deduplication
                    knowledge_type="technical",
                )
                ingested_count += 1
                logger.info(f"[Scout Ingestion] Successfully indexed: {report_file}")

            except Exception as e:
                logger.error(f"[Scout Ingestion] Failed to index {report_file}: {e}")
                errors.append(f"{report_file}: {str(e)}")

        return {
            "status": "completed",
            "count": ingested_count,
            "errors": errors[:5],
            "timestamp": datetime.now().isoformat(),
        }


scout_ingestion_service = ScoutIngestionService()
