from typing import Any

from ...config.logfire_config import get_logger

logger = get_logger(__name__)


class ContentHandler:
    """
    Handles AI Content Generation, Visual Assets, and Approval Workflows.
    Facade delegating specialized tasks to domain sub-generators.
    """

    def __init__(self, supabase_client: Any):
        self.supabase_client = supabase_client

        # Dynamic import to avoid module-level circular dependencies
        from .approval_manager import ApprovalManager
        from .blog_generator import BlogGenerator
        from .sales_pitch import SalesPitchGenerator
        from .visual_generator import VisualAssetGenerator

        self.sales_pitch = SalesPitchGenerator(supabase_client)
        self.visual_generator = VisualAssetGenerator(supabase_client)
        self.blog_generator = BlogGenerator(supabase_client)
        self.approval_manager = ApprovalManager(supabase_client)

    async def generate_pitch(self, company: str, job_title: str) -> dict:
        return await self.sales_pitch.generate_pitch(company, job_title)

    async def generate_visual_asset(self, style: str) -> dict:
        return await self.visual_generator.generate_visual_asset(style)

    async def draft_blog(self, topic: str, industry: list[str] | None, keywords: str | None) -> tuple[bool, dict]:
        return await self.blog_generator.draft_blog(topic, industry, keywords)

    async def draft_from_leads(self, lead_ids: list[str]) -> tuple[bool, dict]:
        return await self.blog_generator.draft_from_leads(lead_ids)

    async def draft_from_leads_physical(self, task_id: str, lead_ids: list[str]) -> str:
        return await self.blog_generator.draft_from_leads_physical(task_id, lead_ids)

    async def submit_blog(self, post_id: str) -> tuple[bool, dict]:
        return await self.blog_generator.submit_blog(post_id)

    async def process_approval(self, item_type: str, item_id: str, action: str, notes: str | None) -> bool:
        return await self.approval_manager.process_approval(item_type, item_id, action, notes)

    async def get_pending_approvals(self) -> dict:
        return await self.approval_manager.get_pending_approvals()

    async def generate_reject_suggestion(self, item_type: str, item_id: str) -> dict:
        return await self.approval_manager.generate_reject_suggestion(item_type, item_id)

    async def get_content_context(self, source_id: str, source_type: str) -> dict:
        return await self.blog_generator.get_content_context(source_id, source_type)

    def calculate_ai_score(self, content: str) -> int:
        return self.blog_generator.calculate_ai_score(content)
