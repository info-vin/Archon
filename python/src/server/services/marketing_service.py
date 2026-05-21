import asyncio

from ..config.logfire_config import get_logger
from ..repositories.base_repository import BaseRepository
from ..services.job_board_service import JobData
from ..utils import get_supabase_client

logger = get_logger(__name__)


class MarketingService(BaseRepository):
    """
    Marketing Service - Slim Facade for Alice/Bob workflows.
    Physically delegates logic to specialized handlers for Phase 4.6.47 Hardening.
    """

    def __init__(self, supabase_client=None):
        super().__init__(supabase_client or get_supabase_client())

    # --- 1. Leads & Jobs (LeadHandler) ---

    async def search_jobs(self, keyword: str, limit: int = 10) -> list[JobData]:
        from ..services.job_board_service import JobBoardService

        service = JobBoardService()
        jobs = await service.search_jobs(keyword, limit)
        asyncio.create_task(service.identify_leads_and_save(jobs))
        return jobs

    async def list_leads(self, user_id: str | None = None, role: str | None = None) -> list[dict]:
        from .marketing.lead_handler import LeadHandler

        return await LeadHandler(self.supabase_client).list_leads(user_id, role)

    async def create_lead(self, lead_data: dict, creator_id: str | None = None) -> tuple[bool, dict]:
        from .marketing.lead_handler import LeadHandler

        return await LeadHandler(self.supabase_client).create_lead(lead_data, creator_id)

    async def update_lead(self, lead_id: str, update_data: dict) -> tuple[bool, dict]:
        from .marketing.lead_handler import LeadHandler

        return await LeadHandler(self.supabase_client).update_lead(lead_id, update_data)

    async def promote_to_vendor(
        self, lead_id: str, vendor_name: str, email: str | None, notes: str | None, owner_id: str
    ) -> tuple[bool, dict]:
        from .marketing.lead_handler import LeadHandler

        return await LeadHandler(self.supabase_client).promote_to_vendor(lead_id, vendor_name, email, notes, owner_id)

    async def reset_leads(self) -> bool:
        from .marketing.lead_handler import LeadHandler

        return await LeadHandler(self.supabase_client).reset_leads()

    # --- 2. AI Content & Approvals (ContentHandler) ---

    async def generate_pitch(self, company: str, job_title: str) -> dict:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).generate_pitch(company, job_title)

    async def generate_visual_asset(self, style: str) -> dict:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).generate_visual_asset(style)

    async def draft_blog(self, topic: str, industry: list[str] | None, keywords: str | None) -> tuple[bool, dict]:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).draft_blog(topic, industry, keywords)

    async def draft_from_leads(self, lead_ids: list[str]) -> tuple[bool, dict]:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).draft_from_leads(lead_ids)

    async def submit_blog(self, post_id: str) -> tuple[bool, dict]:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).submit_blog(post_id)

    async def process_approval(self, item_type: str, item_id: str, action: str, notes: str | None) -> bool:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).process_approval(item_type, item_id, action, notes)

    async def generate_reject_suggestion(self, item_type: str, item_id: str) -> dict:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).generate_reject_suggestion(item_type, item_id)

    async def get_pending_approvals(self) -> dict:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).get_pending_approvals()

    async def get_content_context(self, source_id: str, source_type: str) -> dict:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).get_content_context(source_id, source_type)

    # --- 3. Analytics, Seeding & Background (AnalyticsHandler) ---

    async def get_marketing_stats(self) -> dict:
        from .marketing.analytics_handler import AnalyticsHandler

        return await AnalyticsHandler(self.supabase_client).get_marketing_stats()

    async def get_marketing_trends(self) -> dict:
        from .marketing.analytics_handler import AnalyticsHandler

        return await AnalyticsHandler(self.supabase_client).get_marketing_trends()

    async def get_combined_sources(self, user_id: str) -> list[dict]:
        from .marketing.analytics_handler import AnalyticsHandler

        return await AnalyticsHandler(self.supabase_client).get_combined_sources(user_id)

    async def run_sentinel(self) -> dict:
        from .marketing.analytics_handler import AnalyticsHandler

        return await AnalyticsHandler(self.supabase_client).run_sentinel()

    async def seed_knowledge(self) -> dict:
        from .marketing.analytics_handler import AnalyticsHandler

        # Type safety: seed_knowledge in handler returns dict
        res = await AnalyticsHandler(self.supabase_client).seed_knowledge()
        return res

    # --- Private Method Facades (For backward compatibility / internal calls) ---

    async def _calculate_lead_score(self, job_title: str | None) -> int:
        from .marketing.lead_handler import LeadHandler

        return await LeadHandler(self.supabase_client).calculate_lead_score(job_title)

    def _calculate_ai_score(self, content: str) -> int:
        from .marketing.content_handler import ContentHandler

        return ContentHandler(self.supabase_client).calculate_ai_score(content)
