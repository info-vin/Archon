# python/src/server/services/system/seeding_service.py

import logging
import os
from typing import NotRequired, TypedDict

import aiofiles
from supabase import Client

from ...utils import get_supabase_client
from ..librarian_service import LibrarianService


class SeedingResultDTO(TypedDict):
    status: NotRequired[str]
    scanned_dir: NotRequired[str | None]
    total_files: NotRequired[int]
    indexed_count: NotRequired[int]
    errors: NotRequired[list[str]]
    error: NotRequired[str]

logger = logging.getLogger(__name__)


class SeedingService:
    """
    Service for bootstrapping knowledge bases and system data.
    Decoupled from Business Services for Phase 4.6.46 Hardening.
    """

    def __init__(self, supabase_client: Client | None = None) -> None:
        self.supabase = supabase_client or get_supabase_client()
        self.librarian = LibrarianService()

    async def seed_knowledge(self) -> SeedingResultDTO:
        """
        Trigger the Knowledge Seeding process with Cross-Env Path Resilience (SOP-14).
        David (Admin) uses this to rebuild the RAG index.
        """
        # SOP-14: Multi-Path Array Probing
        POSSIBLE_DIRS = [
            "/app/frontend_public/aus/156_resource",  # Docker Standard
            "../enduser-ui-fe/public/aus/156_resource",  # Local Dev (from src/server)
            "enduser-ui-fe/public/aus/156_resource",  # Root-relative
            "./enduser-ui-fe/public/aus/156_resource",  # Current-relative
        ]

        target_dir = next((d for d in POSSIBLE_DIRS if os.path.exists(d)), None)

        if not target_dir:
            logger.error(f"SeedingService: Resource directory not found. Scanned: {POSSIBLE_DIRS}")
            return {"error": "Knowledge resource directory not found. Check environment mounts."}

        logger.info(f"SeedingService: Starting indexing from {target_dir}")
        success_count = 0
        total_count = 0
        errors = []

        try:
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if file.startswith(".") or file == "DS_Store":
                        continue
                    if not (file.endswith(".md") or file.endswith(".txt")):
                        continue

                    total_count += 1
                    file_path = os.path.join(root, file)
                    try:
                        async with aiofiles.open(file_path, encoding="utf-8") as f:
                            content = await f.read()
                        if not content.strip():
                            continue

                        # Use Librarian for heavy RAG lifting
                        await self.librarian.archive_file(
                            file_name=file, content=content, file_path=file_path, knowledge_type="technical"
                        )
                        success_count += 1
                    except Exception as e:
                        errors.append(f"{file}: {str(e)}")

            return {
                "status": "completed",
                "scanned_dir": target_dir,
                "total_files": total_count,
                "indexed_count": success_count,
                "errors": errors[:5],
            }
        except Exception as e:
            logger.error(f"SeedingService: Global failure: {e}")
            return {"error": f"Seeding failed: {str(e)}"}
