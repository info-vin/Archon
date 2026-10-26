import asyncio
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict, cast

if TYPE_CHECKING:
    from supabase import Client

from ..config.logfire_config import get_logger
from ..repositories.base_repository import BaseRepository
from ..services.crawling.clients.job104_client import JobData
from ..utils import get_supabase_client

logger = get_logger(__name__)


class LeadDataDict(TypedDict):
    id: NotRequired[str]
    company_name: NotRequired[str]
    job_title: NotRequired[str]
    status: NotRequired[str]
    identified_need: NotRequired[str]
    enrichment_score: NotRequired[int]
    source_job_url: NotRequired[str]
    pitch_content: NotRequired[str]
    created_from_user_id: NotRequired[str]
    lost_reason: NotRequired[str]
    assigned_sales_id: NotRequired[str | None]
    created_at: NotRequired[str]


class LeadResultDict(TypedDict):
    lead: LeadDataDict


class VendorDataDict(TypedDict):
    id: NotRequired[str]
    name: NotRequired[str]
    contact_email: NotRequired[str | None]
    description: NotRequired[str | None]
    status: NotRequired[str]
    owner_id: NotRequired[str]


class VendorResultDict(TypedDict):
    vendor: VendorDataDict


class PitchResultDict(TypedDict):
    content: NotRequired[str]
    references: NotRequired[list[str]]
    pitch: NotRequired[str]
    company: NotRequired[str]
    job_title: NotRequired[str]
    status: NotRequired[str]
    error: NotRequired[str]
    message: NotRequired[str]
    error_code: NotRequired[int]


class VisualAssetDict(TypedDict):
    status: NotRequired[str]
    image_url: NotRequired[str | None]
    tier: NotRequired[str | None]
    svg_content: NotRequired[str | None]
    error: NotRequired[str]


class BlogDraftResultDict(TypedDict):
    title: NotRequired[str]
    content: NotRequired[str]
    excerpt: NotRequired[str]
    ai_score: NotRequired[int]
    task_id: NotRequired[str]
    post_id: NotRequired[str]
    blog: NotRequired[dict[str, Any]]
    status: NotRequired[str]
    error: NotRequired[str]
    error_code: NotRequired[int]
    message: NotRequired[str]


class ManagerAlertDict(TypedDict):
    id: NotRequired[str]
    level: NotRequired[str]
    source: NotRequired[str]
    message: NotRequired[str]
    created_at: NotRequired[str]
    details: NotRequired[dict[str, Any]]


class PendingApprovalsDict(TypedDict):
    blogs: NotRequired[list[dict[str, Any]]]
    leads: NotRequired[list[dict[str, Any]]]


class MarketingStatsDict(TypedDict):
    total_leads: NotRequired[int]
    total_blog_posts: NotRequired[int]
    active_campaigns: NotRequired[int]
    conversion_rate: NotRequired[float]
    last_updated: NotRequired[str]
    error: NotRequired[str]


class MarketingTrendsDict(TypedDict):
    keyword_growth: NotRequired[list[dict[str, Any]]]
    sankey_flow: NotRequired[dict[str, Any]]


class CombinedSourceDict(TypedDict):
    id: NotRequired[str]
    type: NotRequired[str]
    title: NotRequired[str]
    score: NotRequired[int | float]
    summary: NotRequired[str]
    date: NotRequired[str]
    status: NotRequired[str]


class SentinelResultDict(TypedDict):
    status: NotRequired[str]
    message: NotRequired[str]


class KnowledgeSeedResultDict(TypedDict):
    status: NotRequired[str]
    scanned_dir: NotRequired[str]
    total_files: NotRequired[int]
    indexed_count: NotRequired[int]
    errors: NotRequired[list[str]]
    error: NotRequired[str]


class ErrorDict(TypedDict):
    error: NotRequired[str]
    message: NotRequired[str]
    error_code: NotRequired[int]


class MarketingService(BaseRepository):
    """
    Marketing Service - Slim Facade for Alice/Bob workflows.
    Physically delegates logic to specialized handlers for Phase 4.6.47 Hardening.
    """

    def __init__(self, supabase_client: "Client | None" = None) -> None:
        super().__init__(supabase_client or get_supabase_client())

    # --- 1. Leads & Jobs (LeadHandler) ---

    async def search_jobs(self, keyword: str, limit: int = 10, page: int = 1) -> list[JobData]:
        from ..services.job_board_service import JobBoardService

        service = JobBoardService()
        jobs = await service.search_jobs(keyword, limit, page=page)
        asyncio.create_task(service.identify_leads_and_save(jobs))
        return jobs

    async def list_leads(self, user_id: str | None = None, role: str | None = None) -> list[LeadDataDict | dict[str, Any]]:
        from .marketing.lead_handler import LeadHandler

        return cast(list[LeadDataDict | dict[str, Any]], await LeadHandler(self.supabase_client).list_leads(user_id, role))

    async def create_lead(
        self, lead_data: LeadDataDict | dict[str, Any], creator_id: str | None = None
    ) -> tuple[bool, LeadResultDict | ErrorDict | dict[str, Any]]:
        from .marketing.lead_handler import LeadHandler

        return await LeadHandler(self.supabase_client).create_lead(lead_data, creator_id)

    async def update_lead(
        self, lead_id: str, update_data: LeadDataDict | dict[str, Any]
    ) -> tuple[bool, LeadResultDict | ErrorDict | dict[str, Any]]:
        from .marketing.lead_handler import LeadHandler

        return await LeadHandler(self.supabase_client).update_lead(lead_id, update_data)

    async def promote_to_vendor(
        self, lead_id: str, vendor_name: str, email: str | None, notes: str | None, owner_id: str
    ) -> tuple[bool, VendorResultDict | ErrorDict | dict[str, Any]]:
        from .marketing.lead_handler import LeadHandler

        return await LeadHandler(self.supabase_client).promote_to_vendor(lead_id, vendor_name, email, notes, owner_id)

    async def reset_leads(self) -> bool:
        from .marketing.lead_handler import LeadHandler

        return await LeadHandler(self.supabase_client).reset_leads()

    # --- 2. AI Content & Approvals (ContentHandler) ---

    async def generate_pitch(self, company: str, job_title: str) -> PitchResultDict | dict[str, Any]:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).generate_pitch(company, job_title)

    async def generate_visual_asset(self, style: str) -> VisualAssetDict | dict[str, Any]:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).generate_visual_asset(style)

    async def draft_blog(
        self, topic: str, industry: list[str] | None, keywords: str | None
    ) -> tuple[bool, BlogDraftResultDict | ErrorDict | dict[str, Any]]:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).draft_blog(topic, industry, keywords)

    async def draft_from_leads(
        self, lead_ids: list[str]
    ) -> tuple[bool, BlogDraftResultDict | ErrorDict | dict[str, Any]]:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).draft_from_leads(lead_ids)

    async def submit_blog(self, post_id: str) -> tuple[bool, BlogDraftResultDict | ErrorDict | dict[str, Any]]:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).submit_blog(post_id)

    async def get_manager_alerts(self, limit: int = 50) -> list[ManagerAlertDict | dict[str, Any]]:
        query = self.supabase_client.table("archon_logs").select("*").eq("level", "ALERT").in_("source", ["sentinel", "twin_scout", "LeadScoring"]).order("created_at", desc=True).limit(limit)  # 合法
        success, res = self.execute_query(query, "Failed to get manager alerts")
        return res.get("data", []) if success else []

    async def process_approval(self, item_type: str, item_id: str, action: str, notes: str | None) -> bool:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).process_approval(item_type, item_id, action, notes)

    async def generate_reject_suggestion(self, item_type: str, item_id: str) -> dict[str, Any]:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).generate_reject_suggestion(item_type, item_id)

    async def get_pending_approvals(self) -> PendingApprovalsDict | dict[str, Any]:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).get_pending_approvals()

    async def get_content_context(self, source_id: str, source_type: str) -> dict[str, Any]:
        from .marketing.content_handler import ContentHandler

        return await ContentHandler(self.supabase_client).get_content_context(source_id, source_type)

    # --- 3. Analytics, Seeding & Background (AnalyticsHandler) ---

    async def get_marketing_stats(self) -> MarketingStatsDict | dict[str, Any]:
        from .marketing.analytics_handler import AnalyticsHandler

        return await AnalyticsHandler(self.supabase_client).get_marketing_stats()

    async def get_marketing_trends(self) -> MarketingTrendsDict | dict[str, Any]:
        from .marketing.analytics_handler import AnalyticsHandler

        return await AnalyticsHandler(self.supabase_client).get_marketing_trends()

    async def get_combined_sources(self, user_id: str) -> list[CombinedSourceDict | dict[str, Any]]:
        from .marketing.analytics_handler import AnalyticsHandler

        return cast(list[CombinedSourceDict | dict[str, Any]], await AnalyticsHandler(self.supabase_client).get_combined_sources(user_id))

    async def run_sentinel(self) -> SentinelResultDict | dict[str, Any]:
        from .marketing.analytics_handler import AnalyticsHandler

        return await AnalyticsHandler(self.supabase_client).run_sentinel()

    async def seed_knowledge(self) -> KnowledgeSeedResultDict | dict[str, Any]:
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
