import asyncio
import logging
import uuid
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from ..auth.dependencies import get_current_user, verify_manager_role
from ..config.logfire_config import get_logger
from ..prompts.marketing_prompts import BLOG_DRAFT_SYSTEM_PROMPT, REJECTION_REASON_PROMPT
from ..prompts.sales_prompts import SALES_PITCH_SYSTEM_PROMPT
from ..services.credential_service import credential_service
from ..services.guardrail_service import GuardrailService
from ..services.job_board_service import JobBoardService, JobData
from ..services.librarian_service import LibrarianService
from ..services.llm_provider_service import get_llm_client
from ..services.log_service import LogService
from ..services.projects.task_service import TaskService
from ..services.prompt_service import prompt_service
from ..services.search.rag_service import RAGService
from ..utils import get_supabase_client
from ..utils.json_utils import safe_json_loads

logger: logging.Logger = get_logger(__name__)

router = APIRouter(prefix="/api/marketing", tags=["marketing"])

# --- MODELS ---

class PitchRequest(BaseModel):
    job_title: str
    company: str
    description: str

class PitchResponse(BaseModel):
    content: str
    references: list[str]

class DraftBlogRequest(BaseModel):
    topic: str
    keywords: str | None = None
    tone: str = "professional"
    context_source_id: str | None = None
    context_type: str | None = "lead"
    industry: list[str] | None = None
    style: list[str] | None = None
    length: str = "standard"
    charts: list[str] | None = None
    enable_web_research: bool = False

class DraftBlogResponse(BaseModel):
    title: str
    content: str
    excerpt: str
    references: list[str] = []
    used_prompt: str | None = None
    metadata: dict | None = None

class ApprovalActionRequest(BaseModel):
    review_notes: str | None = Field(None, alias='reviewNotes')
    model_config = {"populate_by_name": True}

class MarketingRejectSuggestionRequest(BaseModel):
    blog_post_id: str

class RequestInfoRequest(BaseModel):
    subject: str
    context: str
    lead_id: str | None = None

# --- ROUTES ---

@router.get("/jobs", response_model=list[JobData])
async def search_jobs(keyword: str = Query(..., min_length=1), limit: int = 10):
    try:
        service = JobBoardService()
        return await service.search_jobs(keyword, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/leads")
async def get_leads():
    try:
        res = get_supabase_client().table("leads").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/sources")
async def get_content_sources(current_user: dict = Depends(get_current_user)):
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        lead_res = supabase.table("leads").select("id, company_name, enrichment_score, identified_need, created_at")\
            .or_("status.eq.WON,enrichment_score.gte.80")\
            .order("created_at", desc=True).limit(20).execute()
        sources = []
        for lead in lead_res.data:
            sources.append({"id": lead["id"], "type": "lead", "title": lead["company_name"], "score": lead["enrichment_score"], "summary": lead["identified_need"][:100] if lead["identified_need"] else "", "date": lead["created_at"]})
        task_res = supabase.table("archon_tasks").select("id, title, description, created_at")\
            .eq("assignee_id", user_id).neq("status", "done")\
            .order("created_at", desc=True).limit(10).execute()
        for task in task_res.data:
            sources.append({"id": task["id"], "type": "task", "title": task["title"], "score": 100, "summary": task["description"][:100] if task["description"] else "", "date": task["created_at"]})
        blog_res = supabase.table("blog_posts").select("id, title, excerpt, ai_score, review_notes, status, created_at")\
            .in_("status", ["draft", "changes_requested"])\
            .order("created_at", desc=True).limit(15).execute()
        for blog in blog_res.data:
            status = blog.get("status")
            review_notes = blog.get("review_notes")
            summary = review_notes if (status == "changes_requested" and review_notes) else (blog.get("excerpt") or "")
            sources.append({
                "id": blog["id"], "type": "blog", "title": blog["title"], "score": blog.get("ai_score", 0),
                "summary": summary, "date": blog["created_at"], "review_notes": review_notes, "ai_score": blog.get("ai_score"), "status": status
            })
        return sorted(sources, key=lambda x: x["date"], reverse=True)
    except Exception as e:
        logger.error(f"API: Sources fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/context/{source_id}")
async def get_content_context(source_id: str, source_type: str = Query("lead"), current_user: dict = Depends(get_current_user)):
    try:
        supabase = get_supabase_client()
        context_text = ""
        logs = []
        target_id, target_type = source_id, source_type
        if source_type == "blog":
            res = supabase.table("blog_posts").select("generation_metadata").eq("id", source_id).limit(1).execute()
            if res.data and len(res.data) > 0:
                meta = res.data[0].get("generation_metadata") or {}
                origin_id = meta.get("context_source_id") or meta.get("task_id")
                if origin_id:
                    target_id = origin_id
                    target_type = meta.get("context_type") or ("task" if meta.get("task_id") else "lead")
        if target_type == "lead":
            log_res = supabase.table("visit_logs").select("*").eq("lead_id", target_id).execute()
            logs = log_res.data
            for log in logs:
                context_text += f"\n[Visit Log]: {log.get('summary')}\n[Transcript]: {log.get('voice_transcript')}\n"
            lead_res = supabase.table("leads").select("identified_need").eq("id", target_id).limit(1).execute()
            if lead_res.data:
                context_text += f"\n[Lead Need]: {lead_res.data[0].get('identified_need')}\n"
        elif target_type == "task":
            task_res = supabase.table("archon_tasks").select("*").eq("id", target_id).limit(1).execute()
            if task_res.data:
                task_data = task_res.data[0]
                context_text += f"\n[Task]: {task_data.get('title')}\n{task_data.get('description')}\n"
                lead_id = task_data.get("lead_id")
                if lead_id:
                    l_res = supabase.table("visit_logs").select("*").eq("lead_id", lead_id).execute()
                    for log_entry in l_res.data:
                        context_text += f"\n[Linked Log]: {log_entry.get('summary')}\n{log_entry.get('voice_transcript')}\n"
        rag_refs = []
        if context_text.strip():
            rag_service = RAGService()
            success, result = await rag_service.perform_rag_query(query=context_text[:1000], match_count=3)
            if success and isinstance(result, dict):
                rag_refs = result.get("results", [])
        return {"source_id": source_id, "source_type": source_type, "logs": logs, "rag_refs": rag_refs, "context_summary": context_text or "No original victory signals available."}
    except Exception as e:
        logger.error(f"API: Context fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/approvals")
async def get_pending_approvals(current_user: dict = Depends(get_current_user)):
    try:
        user_role = current_user.get("role", "viewer").lower()
        if user_role not in ["manager", "admin", "system_admin"]:
            raise HTTPException(status_code=403)
        res = get_supabase_client().table("blog_posts").select("*").eq("status", "review").order("updated_at", desc=True).execute()
        return {"blogs": res.data or [], "leads": []}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/approvals/{item_type}/{item_id}/{action}")
async def process_approval(item_type: str, item_id: str, action: str, request: Request, current_user: dict = Depends(get_current_user)):
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["manager", "admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Manager access required.")
    try:
        supabase = get_supabase_client()
        raw_body = {}
        try: raw_body = await request.json()
        except Exception: pass
        review_notes = raw_body.get("review_notes") or raw_body.get("reviewNotes") or raw_body.get("reason")
        if item_type == "blog":
            new_status = "published" if action == "approve" else "changes_requested"
            update_data = {"status": new_status}
            if review_notes: update_data["review_notes"] = str(review_notes)
            res = supabase.table("blog_posts").update(update_data).eq("id", item_id).execute()
            if res.data:
                meta = res.data[0].get("generation_metadata") or {}
                task_id = meta.get("task_id")
                if task_id:
                    try:
                        ts = TaskService(supabase)
                        await ts.update_task(task_id, {"status": "done" if action == "approve" else "doing"})
                    except Exception: pass
        return {"success": True, "status": action}
    except Exception as e:
        logger.error(f"API: Approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/blog/{post_id}/submit")
async def submit_blog_for_review(post_id: str, current_user: dict = Depends(get_current_user)):
    try:
        supabase = get_supabase_client()
        res = supabase.table("blog_posts").select("*").eq("id", post_id).limit(1).execute()
        if not res.data: raise HTTPException(status_code=404)
        post = res.data[0]
        from .stats_api import calculate_ai_score
        new_score = calculate_ai_score(post.get("content", ""))
        existing_notes = post.get("review_notes")
        auto_reject = new_score < 50
        final_notes = f"AI Review failure ({new_score}/100)" if auto_reject else existing_notes
        final_score = max(post.get("ai_score") or 0, new_score)
        new_status = "changes_requested" if auto_reject else "review"
        supabase.table("blog_posts").update({"status": new_status, "ai_score": final_score, "review_notes": final_notes}).eq("id", post_id).execute()
        task_id = (post.get("generation_metadata") or {}).get("task_id")
        if task_id and not auto_reject:
            try: await TaskService(supabase).update_task(task_id, {"status": "review"})
            except Exception: pass
        return {"success": True, "status": new_status, "ai_score": final_score, "review_notes": final_notes}
    except Exception as e:
        logger.error(f"API: Submit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/approvals/reject-suggestion")
async def reject_suggestion(request: MarketingRejectSuggestionRequest, current_user: dict = Depends(get_current_user)):
    try:
        user_role = current_user.get("role", "viewer").lower()
        if user_role not in ["admin", "manager"]: raise HTTPException(status_code=403)
        supabase = get_supabase_client()
        post_res = supabase.table("blog_posts").select("title, content").eq("id", request.blog_post_id).single().execute()
        if not post_res.data: raise HTTPException(status_code=404)
        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        provider_config = await credential_service.get_active_provider("llm")
        model_id = provider_config.get("chat_model") or "gemini-2.0-flash"
        response = client.models.generate_content(model=model_id.replace("models/", ""), contents=REJECTION_REASON_PROMPT.format(title=post_res.data.get("title"), content=post_res.data.get("content")[:3000]))
        return {"suggested_reason": response.text}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/request-info")
async def request_info(request: RequestInfoRequest, current_user: dict = Depends(get_current_user)):
    try:
        user_role = current_user.get("role", "viewer").lower()
        if user_role not in ["admin", "manager", "marketing"]: raise HTTPException(status_code=403)
        ts = TaskService(get_supabase_client())
        success, result = await ts.create_info_request_task(requester_id=str(current_user.get("email")), subject=request.subject, context=request.context, lead_id=request.lead_id)
        if not success: raise Exception(result.get("error"))
        return {"success": True, "task": result.get("task")}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/blog/draft", response_model=DraftBlogResponse)
async def draft_blog_post(request: DraftBlogRequest, current_user: dict = Depends(get_current_user)):
    try:
        rag_service = RAGService()
        search_query = f"{request.topic} {request.keywords or ''}"
        success, rag_res = await rag_service.perform_rag_query(query=search_query, match_count=5)
        context_text = ""
        if request.context_source_id:
            supabase = get_supabase_client()
            if request.context_type == "lead":
                logs = supabase.table("visit_logs").select("summary, voice_transcript").eq("lead_id", request.context_source_id).execute()
                for log in logs.data: context_text += f"\n[Signal]: {log['summary']}\n{log['voice_transcript']}\n"
        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        sys_prompt = prompt_service.get_prompt("BLOG_DRAFT", BLOG_DRAFT_SYSTEM_PROMPT)
        user_prompt = f"Topic: {request.topic}\nContext:\n{context_text}"
        
        try:
            response = client.models.generate_content(model="gemini-2.0-flash-lite", contents=cast(Any, [user_prompt]), config=types.GenerateContentConfig(system_instruction=sys_prompt, response_mime_type="application/json", temperature=0.7))
            result = safe_json_loads(response.text or "{}")
        except Exception as llm_err:
            # Fallback to 1.5-pro logic for tests
            client_fb = genai.Client(api_key=api_key)
            response = client_fb.models.generate_content(model="gemini-1.5-pro", contents=cast(Any, [user_prompt]), config=types.GenerateContentConfig(system_instruction=sys_prompt, response_mime_type="application/json", temperature=0.7))
            result = safe_json_loads(response.text or "{}")

        metadata = {"task_id": request.context_source_id if request.context_type == "task" else None, "context_source_id": request.context_source_id, "context_type": request.context_type}
        return DraftBlogResponse(title=str(result.get("title", "Untitled")), content=str(result.get("content", "")), excerpt=str(result.get("excerpt", "")), metadata=metadata)
    except Exception as e:
        logger.error(f"API: Draft failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/nana-banana")
async def nana_banana_proxy(request: dict, current_user: dict = Depends(get_current_user)):
    try:
        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.0-flash-exp", contents=cast(Any, [request.get("prompt", "artwork")]), config=types.GenerateContentConfig(response_modalities=['IMAGE']))
        for part in (response.parts or []):
            if part.inline_data:
                return {"status": "success", "image_url": f"data:{part.inline_data.mime_type or 'image/png'};base64,{part.inline_data.data.decode('utf-8')}"}
        raise Exception("No image data")
    except Exception as e:
        LogService(get_supabase_client()).create_log_entry({"user_input": "Nana Banana Failure", "gemini_response": str(e), "project_name": "marketing", "user_name": "system"})
        return {"status": "fallback_mock", "image_url": "https://picsum.photos/seed/fallback/800/600?text=Nana+Banana+Fallback"}

@router.get("/trends")
async def get_marketing_trends(current_user: dict = Depends(get_current_user)):
    try:
        supabase = get_supabase_client()
        res_t = supabase.table("marketing_trends").select("*").eq("trend_type", "keyword_growth").order("report_date", desc=True).limit(1).execute()
        res_s = supabase.table("marketing_trends").select("*").eq("trend_type", "sankey_flow").order("report_date", desc=True).limit(1).execute()
        return {"keyword_growth": res_t.data[0]["data"] if res_t.data else [], "sankey_flow": res_s.data[0]["data"] if res_s.data else {}}
    except Exception: return {"keyword_growth": [], "sankey_flow": {}}

@router.get("/manager/alerts")
async def get_manager_alerts(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["manager", "admin"]: raise HTTPException(status_code=403)
    res = get_supabase_client().table("archon_logs").select("*").eq("level", "ALERT").in_("source", ["sentinel", "LeadScoring"]).order("created_at", desc=True).limit(50).execute()
    return res.data or []
