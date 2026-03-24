"""
Marketing API Hardened - Entry point for Alice & Bob workflows.
Standardized RBAC Sealing with Full Test Compatibility.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.server.schemas.marketing import (
    ApprovalRequest,
    DraftBlogRequest,
    LeadCreateRequest,
    LeadUpdateRequest,
    LogoRequest,
    PitchRequest,
    PitchResponse,
    PromoteLeadRequest,
)
from src.server.services.marketing_service import MarketingService

from ..auth.dependencies import get_current_user, requires_permission
from ..auth.permissions import (
    AGENT_TRIGGER_MKT,
    BRAND_ASSET_MANAGE,
    CONTENT_PUBLISH,
    TASK_READ_TEAM,
)

router: APIRouter = APIRouter(prefix="/api/marketing", tags=["marketing"])

def get_marketing_service():
    """Export for test compatibility."""
    return MarketingService()

def _err(msg: str, code: int = 403):
    raise HTTPException(status_code=code, detail=msg)

@router.get("/jobs")
async def search_jobs(keyword: str = Query(...), limit: int = 10, current_user: dict = Depends(get_current_user)):
    service = MarketingService()
    return await service.search_jobs(keyword, limit)

@router.get("/leads")
async def list_leads(current_user: dict = Depends(get_current_user)):
    service = MarketingService()
    return await service.list_leads()

@router.post("/leads")
async def create_lead(req: LeadCreateRequest, current_user: dict = Depends(get_current_user)):
    service = MarketingService()
    success, res = await service.create_lead(req.model_dump(), creator_id=str(current_user.get("id")))
    if not success:
        _err(str(res), 400)
    return res

@router.post("/leads/reset")
async def reset_leads(current_user: dict = Depends(requires_permission(CONTENT_PUBLISH))):
    service = MarketingService()
    success = await service.reset_leads()
    return {"success": success}

@router.patch("/leads/{lead_id}")
async def update_lead(lead_id: str, req: LeadUpdateRequest, current_user: dict = Depends(get_current_user)):
    service = MarketingService()
    success, res = await service.update_lead(lead_id, req.model_dump(exclude_unset=True))
    if not success:
        _err(str(res), 400)
    return res

@router.post("/leads/{lead_id}/promote")
async def promote_lead(lead_id: str, req: PromoteLeadRequest, current_user: dict = Depends(get_current_user)):
    service = MarketingService()
    success, res = await service.promote_to_vendor(lead_id, **req.model_dump(), owner_id=str(current_user.get("id")))
    if not success:
        _err(str(res), 400)
    return res

@router.post("/generate-pitch", response_model=PitchResponse)
async def generate_pitch(req: PitchRequest, current_user: dict = Depends(requires_permission(AGENT_TRIGGER_MKT))):
    service = MarketingService()
    res = await service.generate_pitch(req.company, req.job_title)
    if isinstance(res, dict) and "error_code" in res:
        # Physical Alignment: Mapping service errors to HTTP Exceptions
        raise HTTPException(status_code=res["error_code"], detail=res["message"])
    return res

@router.post("/draft-blog")
async def draft_blog_post(req: DraftBlogRequest, current_user: dict = Depends(requires_permission(AGENT_TRIGGER_MKT))):
    service = MarketingService()
    success, res = await service.draft_blog(req.topic, req.industry, req.keywords)
    if not success:
        _err(res.get("message", "AI Draft failed"), res.get("error_code", 500))
    return res

@router.post("/blog/{post_id}/submit")
async def submit_blog(post_id: str, current_user: dict = Depends(get_current_user)):
    """Bob submits a draft for Charlie's review."""
    service = MarketingService()
    success, res = await service.submit_blog(post_id)
    if not success:
        _err(res.get("error", "Submission failed"), 400)
    return res

@router.post("/generate-logo")
async def generate_logo(req: LogoRequest, current_user: dict = Depends(requires_permission(BRAND_ASSET_MANAGE))):
    service = MarketingService()
    return await service.generate_visual_asset(req.style)

@router.get("/sources")
async def get_combined_sources(current_user: dict = Depends(get_current_user)):
    service = MarketingService()
    return await service.get_combined_sources(user_id=str(current_user.get("id")))

@router.get("/context/{source_id}")
async def get_content_context(source_id: str, source_type: str = Query("lead"), current_user: dict = Depends(get_current_user)):
    service = MarketingService()
    return await service.get_content_context(source_id, source_type)

@router.post("/manager/sentinel/run")
async def run_sentinel_manual(current_user: dict = Depends(requires_permission(AGENT_TRIGGER_MKT))):
    """Manually trigger the Business Sentinel."""
    service = MarketingService()
    return await service.run_sentinel()

@router.get("/stats")
async def get_marketing_stats(current_user: dict = Depends(get_current_user)):
    """Fetch marketing performance statistics."""
    service = MarketingService()
    return await service.get_marketing_stats()

@router.get("/trends")
async def get_marketing_trends(current_user: dict = Depends(get_current_user)):
    """Fetch marketing trends analysis."""
    service = MarketingService()
    return await service.get_marketing_trends()

@router.post("/knowledge/seed")
async def seed_knowledge_base(current_user: dict = Depends(requires_permission(CONTENT_PUBLISH))):
    """Admin triggers the physical knowledge seeding process."""
    service = MarketingService()
    return await service.seed_knowledge()

@router.get("/approvals")
async def get_pending_approvals(current_user: dict = Depends(requires_permission(TASK_READ_TEAM))):
    service = MarketingService()
    return await service.get_pending_approvals()

@router.post("/approvals/{item_type}/{item_id}/{action}")
async def process_approval(
    item_type: str, item_id: str, action: str,
    req: ApprovalRequest,
    current_user: dict = Depends(requires_permission(CONTENT_PUBLISH))
):
    service = MarketingService()
    success = await service.process_approval(item_type, item_id, action, req.notes)
    return {"success": success}
