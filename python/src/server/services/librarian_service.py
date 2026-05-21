from ..config.logfire_config import get_logger
from ..repositories.knowledge_repository import KnowledgeRepository
from ..services.source_management_service import SourceManagementService
from ..utils import get_supabase_client
from .knowledge.chunking_service import KnowledgeChunkingService
from .librarian.business_archiver import BusinessArchiver
from .librarian.file_archiver import FileArchiver
from .librarian.web_archiver import WebArchiver

logger = get_logger(__name__)


class LibrarianService:
    """
    Facade for Librarian operations, delegating to specialized archivers.
    """

    def __init__(self):
        self.supabase = get_supabase_client()
        self.source_service = SourceManagementService(self.supabase)
        self.repo = KnowledgeRepository(self.supabase)
        self.chunker = KnowledgeChunkingService()

        self.file_archiver = FileArchiver(self.supabase, self.repo, self.chunker)
        self.web_archiver = WebArchiver(self.supabase, self.repo, self.file_archiver)
        self.business_archiver = BusinessArchiver(self.supabase, self.repo)

    async def archive_any_url(self, url: str, user_role: str = "member", depth: int = 0, max_depth: int = 1) -> str:
        return await self.web_archiver.archive_any_url(url, user_role, depth, max_depth)

    async def archive_web_research(self, query: str, content: str, references: list[str]) -> str:
        return await self.web_archiver.archive_web_research(query, content, references)

    async def archive_file(
        self,
        file_name: str,
        content: str,
        file_path: str,
        knowledge_type: str = "technical",
        authority_level: str = "normal",
    ) -> str:
        return await self.file_archiver.archive_file(file_name, content, file_path, knowledge_type, authority_level)

    async def archive_sales_pitch(self, company: str, job_title: str, content: str, references: list[str]) -> str:
        return await self.business_archiver.archive_sales_pitch(company, job_title, content, references)

    async def get_style_constraints(self, category: str = "marketing") -> str:
        return await self.business_archiver.get_style_constraints(category)

    async def archive_failure_case(
        self, content: str, reason: str, company: str, job_title: str, metadata: dict | None = None
    ) -> str:
        return await self.business_archiver.archive_failure_case(content, reason, company, job_title, metadata)

    async def archive_style_critique(self, post_title: str, original_content: str, review_notes: str) -> str:
        return await self.business_archiver.archive_style_critique(post_title, original_content, review_notes)
