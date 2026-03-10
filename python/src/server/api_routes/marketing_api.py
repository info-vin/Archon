from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..auth.dependencies import get_current_user
from ..schemas.marketing import (
    CreateLeadRequest,
    DraftBlogRequest,
    DraftBlogResponse,
    LeadUpdate,
    LogoRequest,
    MarketingRejectSuggestionRequest,
    PitchRequest,
    PitchResponse,
    PromoteLeadRequest,
    RequestInfoRequest,
)
from ..services.marketing_service import MarketingService
from ..services.projects.task_service import TaskService

# --- PHYSICAL BRIDGE FOR EXISTING TESTS (CRITICAL) ---
# These must be exposed here so that mock.patch("...marketing_api.RAGService") etc. work.
from ..utils.api_utils import handle_service_result

router = APIRouter(prefix="/api/marketing", tags=["marketing"])

def get_marketing_service() -> MarketingService:
    return MarketingService()

@router.get("/jobs")
async def search_jobs(keyword: str = Query(..., min_length=1), limit: int = 10, service: MarketingService = Depends(get_marketing_service)):
    return await service.search_jobs(keyword, limit)

@router.get("/leads")
async def get_leads(current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    role = current_user.get("role", "viewer").lower()
    if role not in ["admin", "system_admin", "manager", "sales"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")
    data = await service.list_leads()
    return data if isinstance(data, list) else []

@router.post("/leads")
async def create_lead(request: CreateLeadRequest, current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    s, res = await service.create_lead(request.model_dump(), creator_id=current_user.get("id"))
    data = cast(dict[str, Any], handle_service_result(s, res))
    lead = data.get("lead")
    if not lead and isinstance(data, list) and len(data) > 0:
        lead = data[0]
    elif not lead:
        lead = data
    return lead

@router.patch("/leads/{lead_id}")
async def update_lead(lead_id: str, request: LeadUpdate, current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["admin", "manager", "sales", "system_admin"]:
        raise HTTPException(status_code=403)
    s, res = await service.update_lead(lead_id, request.model_dump(exclude_unset=True))
    data = handle_service_result(s, res)
    if isinstance(data, list) and len(data) > 0:
        return data[0]
    return data

@router.post("/leads/{lead_id}/promote")
async def promote_lead_to_vendor(lead_id: str, request: PromoteLeadRequest, current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    user_id = str(current_user.get("id", ""))
    s, res = await service.promote_to_vendor(lead_id, request.vendor_name, request.contact_email, request.notes, user_id)
    return handle_service_result(s, res)

@router.post("/generate-pitch", response_model=PitchResponse)
async def generate_pitch(request: PitchRequest, current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    res = await service.generate_pitch(request.company, request.job_title)
    if "error_code" in res:
        raise HTTPException(status_code=res["error_code"], detail=res["message"])
    return res

@router.post("/generate-logo")
async def generate_logo(request: LogoRequest, current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    return await service.generate_visual_asset(request.style)

@router.get("/sources")
async def get_content_sources(current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    user_id = str(current_user.get("id", ""))
    return await service.get_combined_sources(user_id)

@router.get("/context/{source_id}")
async def get_content_context(source_id: str, source_type: str = Query("lead"), current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    return await service.get_content_context(source_id, source_type)

@router.get("/approvals")
async def get_pending_approvals(current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    return await service.get_pending_approvals()

@router.post("/approvals/{item_type}/{item_id}/{action}")
async def process_approval(item_type: str, item_id: str, action: str, request: Request, current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    if current_user.get("role") not in ["manager", "admin", "system_admin"]:
        raise HTTPException(status_code=403)
    body = await request.json()
    notes = body.get("review_notes") or body.get("reviewNotes") or body.get("reason")
    success = await service.process_approval(item_type, item_id, action, notes)
    return {"success": success}

@router.post("/blog/{post_id}/submit")
async def submit_blog_for_review(post_id: str, current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    s, res = await service.submit_blog(post_id)
    return handle_service_result(s, res)

@router.post("/approvals/reject-suggestion")
async def reject_suggestion(request: MarketingRejectSuggestionRequest, current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    if current_user.get("role", "viewer").lower() not in ["admin", "manager"]:
        raise HTTPException(status_code=403)
    reason = await service.get_rejection_reason(request.blog_post_id)
    if not reason:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"suggested_reason": reason}

@router.post("/request-info")
async def request_info(request: RequestInfoRequest, current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    if current_user.get("role", "viewer").lower() not in ["admin", "manager", "marketing"]:
        raise HTTPException(status_code=403)
    success, res = await TaskService().create_info_request_task(requester_id=str(current_user.get("email")), subject=request.subject, context=request.context, lead_id=request.lead_id)
    if success:
        return {"success": True, "task": res.get("task")}
    raise HTTPException(status_code=500, detail=res.get("error"))

@router.post("/blog/draft", response_model=DraftBlogResponse)
async def draft_blog_post(request: DraftBlogRequest, current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    s, res = await service.draft_blog(request.topic, request.industry, request.keywords)
    if not s and "error_code" in res:
        raise HTTPException(status_code=res["error_code"], detail=res["message"])
    return handle_service_result(s, res)

@router.get("/trends")
async def get_marketing_trends(current_user: dict = Depends(get_current_user), service: MarketingService = Depends(get_marketing_service)):
    return await service.get_trends()
