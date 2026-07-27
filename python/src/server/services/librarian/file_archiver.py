import uuid

from ...config.logfire_config import get_logger
from ...repositories.knowledge_repository import KnowledgeRepository
from ...services.source_management_service import extract_source_summary, update_source_info
from ...utils import get_supabase_client
from ..knowledge.chunking_service import KnowledgeChunkingService
from ..shared_constants import AgentUUIDs

logger = get_logger(__name__)


class FileArchiver:
    def __init__(self, supabase=None, repo=None, chunker=None) -> None:
        self.supabase = supabase or get_supabase_client()
        self.repo = repo or KnowledgeRepository(self.supabase)
        self.chunker = chunker or KnowledgeChunkingService()

    async def archive_file(
        self,
        file_name: str,
        content: str,
        file_path: str,
        knowledge_type: str = "technical",
        authority_level: str = "normal",
    ) -> str:
        """
        Archives a local file into the knowledge base.
        """
        try:
            # 1. Generate Source ID
            safe_name = "".join(c for c in file_name if c.isalnum()).lower()
            unique_suffix = str(uuid.uuid4())[:8]
            source_id = f"file-{safe_name}-{unique_suffix}"

            # 2. Metadata
            title = file_name
            word_count = len(content.split())
            tags = ["file_upload", "seeded_knowledge"]
            if authority_level == "high":
                tags.append("policy")

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
                original_url=f"file://{file_path}",
            )

            # 4. Content & Embedding
            page_data_list = await self.chunker.process_document_into_pages(
                source_id=source_id,
                content=content,
                base_url=f"file://{file_path}",
                metadata={
                    "knowledge_type": knowledge_type,
                    "tags": tags,
                    "file_path": file_path,
                },
                title_prefix=title,
            )

            if page_data_list:
                self.repo.insert_crawled_page(page_data_list)

            # 5. Record version
            self.repo.insert_document_version(
                document_id=source_id,
                field_name="knowledge_file",
                change_summary=f"Indexed local file: {file_name}",
                content={"source_id": source_id, "file": file_name, "path": file_path},
                created_by=AgentUUIDs.LIBRARIAN,
            )

            return source_id

        except Exception as e:
            logger.error(f"Librarian: Failed to archive file {file_name} | error={str(e)}")
            return ""
