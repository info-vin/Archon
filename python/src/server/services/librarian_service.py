"""
Librarian Service

Encapsulates "Librarian" agent behaviors: Archiving and Indexing.
Handles the seamless transition from "Generated Content" to "Knowledge Base".
"""
import uuid
from datetime import datetime

from ..config.logfire_config import get_logger, logfire
from ..services.source_management_service import SourceManagementService, update_source_info
from ..utils import get_supabase_client

logger = get_logger(__name__)

class LibrarianService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.source_service = SourceManagementService(self.supabase)

    async def archive_sales_pitch(
        self,
        company: str,
        job_title: str,
        content: str,
        references: list[str]
    ) -> str:
        """
        Archives a generated sales pitch into the knowledge base.

        Args:
            company: Target company name
            job_title: Target job title
            content: The email content generated
            references: List of source IDs or titles referenced (for metadata)

        Returns:
            str: The source_id of the archived item
        """
        try:
            # 1. Generate unique Source ID
            # Format: pitch-{company}-{uuid_short}
            safe_company = "".join(c for c in company if c.isalnum()).lower()
            unique_suffix = str(uuid.uuid4())[:8]
            source_id = f"pitch-{safe_company}-{unique_suffix}"

            # 2. Prepare Metadata
            title = f"Pitch: {company} - {job_title}"
            summary = f"Auto-generated sales pitch for {job_title} at {company}."
            word_count = len(content.split())
            tags = ["sales_pitch", "outbound", "email"]
            if references:
                tags.append("has_references")

            metadata = {
                "knowledge_type": "sales_pitch",
                "tags": tags,
                "references": references,
                "target_company": company,
                "target_job": job_title,
                "source_type": "generated",
                "auto_generated": True,
                "created_at": datetime.now().isoformat()
            }

            logfire.info(f"Librarian: Archiving pitch | source_id={source_id} | company={company}")

            # 3. Create Source Info (archon_sources)
            # We use the lower-level update_source_info to manually set metadata
            await update_source_info(
                client=self.supabase,
                source_id=source_id,
                summary=summary,
                word_count=word_count,
                content=content,
                knowledge_type="sales_pitch",
                tags=tags,
                source_display_name=title
            )

            # 4. Insert Content (archon_crawled_pages)
            # This makes it searchable by RAG.
            # We treat the pitch as a single "page".
            page_data = {
                "source_id": source_id,
                "url": f"generated://pitch/{source_id}",
                "title": title,
                "content": content,
                "metadata": metadata
            }

            self.supabase.table("archon_crawled_pages").insert(page_data).execute()

            logfire.info(f"Librarian: Pitch archived successfully | source_id={source_id}")
            return source_id

        except Exception as e:
            logfire.error(f"Librarian: Failed to archive pitch | error={str(e)}")
            # We don't want to break the user flow if archiving fails, but we should log it.
            # In a critical system, we might retry or raise.
            # For now, we return empty string to indicate failure but allow flow to continue.
            return ""
