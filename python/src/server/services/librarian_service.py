"""
Librarian Service

Encapsulates "Librarian" agent behaviors: Archiving and Indexing.
Handles the seamless transition from "Generated Content" to "Knowledge Base".
"""
import uuid
from datetime import datetime

from ..config.logfire_config import get_logger
from ..services.embeddings.embedding_service import create_embedding
from ..services.source_management_service import (
    SourceManagementService,
    extract_source_summary,
    update_source_info,
)
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

            logger.info(f"Librarian: Archiving pitch | source_id={source_id} | company={company}")

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

            # Generate embedding for the pitch content to enable RAG discovery
            try:
                embedding_vector = await create_embedding(content)
            except Exception as e:
                logger.error(f"Librarian: Failed to generate embedding for pitch {source_id} | error={str(e)}")
                embedding_vector = None

            page_data = {
                "source_id": source_id,
                "url": f"generated://pitch/{source_id}",
                "chunk_number": 0, # Required field
                "content": content,
                "embedding": embedding_vector,
                # WORKAROUND: We store the title in metadata to bypass the schema cache
                # and ensure it's available even if the 'title' column isn't fully synced yet.
                "metadata": {**metadata, "title": title} # Store title in metadata
            }

            self.supabase.table("archon_crawled_pages").insert(page_data).execute()

            # 5. Record version for audit trail (Admin Insight)
            try:
                self.supabase.table("archon_document_versions").insert({
                    "field_name": "sales_pitch",
                    "change_type": "create",
                    "change_summary": f"Archived generated pitch for {company}",
                    "content": {"source_id": source_id, "company": company, "job": job_title},
                    "created_by": "ai-librarian",
                    "version_number": 1
                }).execute()
            except Exception as v_err:
                logger.warning(f"Librarian: Failed to log document version: {v_err}")

            logger.info(f"Librarian: Pitch archived successfully | source_id={source_id}")
            return source_id

        except Exception as e:
            logger.error(f"Librarian: Failed to archive pitch | error={str(e)}")
            # For now, we return empty string to indicate failure but allow flow to continue.
            return ""

    async def archive_file(
        self,
        file_name: str,
        content: str,
        file_path: str,
        knowledge_type: str = "technical"
    ) -> str:
        """
        Archives a local file into the knowledge base.

        Args:
            file_name: Name of the file
            content: Text content of the file
            file_path: Original path (for metadata)
            knowledge_type: Classification of knowledge

        Returns:
            str: Source ID
        """
        try:
            # 1. Generate Source ID
            safe_name = "".join(c for c in file_name if c.isalnum()).lower()
            unique_suffix = str(uuid.uuid4())[:8]
            source_id = f"file-{safe_name}-{unique_suffix}"  # Use safe_name based on file_name

            # 2. Metadata
            title = file_name
            word_count = len(content.split())
            tags = ["file_upload", "seeded_knowledge"]

            # Detect type from extension
            if file_name.endswith(".md"):
                tags.append("markdown")
            elif file_name.endswith(".pdf"):
                tags.append("pdf")

            summary = await extract_source_summary(source_id, content)

            logger.info(f"Librarian: Archiving file | source_id={source_id} | file={file_name}")

            # 3. Source Info
            await update_source_info(
                client=self.supabase,
                source_id=source_id,
                summary=summary,
                word_count=word_count,
                content=content,
                knowledge_type=knowledge_type,
                tags=tags,
                source_display_name=title,
                original_url=f"file://{file_path}"
            )

            # 4. Content & Embedding
            # Chunking logic could go here, but for now we do single chunk for simplicity
            # or rely on RAG service's chunking if we used that.
            # To be safe with token limits, we should probably chunk larger files,
            # but for this specific request (seed data), single chunk or simple split is okay for MVP.

            # Simple chunking if too large (>8000 chars roughly)
            chunk_size = 4000
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

            for i, chunk in enumerate(chunks):
                try:
                    embedding_vector = await create_embedding(chunk)
                except Exception as e:
                    logger.error(f"Librarian: Embedding failed for chunk {i} of {source_id}: {e}")
                    embedding_vector = None

                page_data = {
                    "source_id": source_id,
                    "url": f"file://{file_path}#chunk={i}",
                    "chunk_number": i,
                    "content": chunk,
                    "embedding": embedding_vector,
                    "metadata": {
                        "knowledge_type": knowledge_type,
                        "tags": tags,
                        "file_path": file_path,
                        "title": f"{title} (Part {i+1})"
                    }
                }
                self.supabase.table("archon_crawled_pages").insert(page_data).execute()

            # 5. Record version for audit trail (Admin Insight)
            try:
                self.supabase.table("archon_document_versions").insert({
                    "field_name": "knowledge_file",
                    "change_type": "create",
                    "change_summary": f"Indexed local file: {file_name}",
                    "content": {"source_id": source_id, "file": file_name, "path": file_path},
                    "created_by": "ai-librarian",
                    "version_number": 1
                }).execute()
            except Exception as v_err:
                logger.warning(f"Librarian: Failed to log document version: {v_err}")

            logger.info(f"Librarian: File archived successfully | source_id={source_id}")
            return source_id

        except Exception as e:
            logger.error(f"Librarian: Failed to archive file {file_name} | error={str(e)}")
            return ""
