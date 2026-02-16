import asyncio
import logging
import uuid
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..prompts.marketing_prompts import BLOG_DRAFT_SYSTEM_PROMPT, REJECTION_REASON_PROMPT
from ..services.credential_service import credential_service
from ..services.guardrail_service import GuardrailService
from ..services.job_board_service import JobBoardService, JobData
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

class CreateLeadRequest(BaseModel):
    company_name: str
    job_title: str
    source: str = "manual"
    source_job_url: str | None = None
    identified_need: str | None = None
    status: str = "new"
    pitch_content: str | None = None

class PromoteLeadRequest(BaseModel):
    vendor_name: str
    contact_email: str | None = None
    notes: str | None = None

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

class LeadUpdate(BaseModel):
    status: str | None = None
    enrichment_score: int | None = None
    identified_need: str | None = None

class LogoRequest(BaseModel):
    style: str = "eciton"
    primary_color: str | None = None

class LogoResponse(BaseModel):
    svg_content: str
    style: str

# --- ROUTES ---

@router.get("/jobs", response_model=list[JobData])
async def search_jobs(keyword: str = Query(..., min_length=1), limit: int = 10):
    try:
        service = JobBoardService()
        jobs = await service.search_jobs(keyword, limit)
        asyncio.create_task(service.identify_leads_and_save(jobs))
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/leads")
async def get_leads():
    try:
        res = get_supabase_client().table("leads").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/leads")
async def create_lead(request: CreateLeadRequest, current_user: dict = Depends(get_current_user)):
    try:
        supabase = get_supabase_client()
        lead_data = request.model_dump()
        lead_data["created_from_user_id"] = current_user.get("id")

        if request.source_job_url:
            existing = supabase.table("leads").select("id").eq("source_job_url", request.source_job_url).execute()
            if existing.data:
                if request.pitch_content:
                    supabase.table("leads").update({"pitch_content": request.pitch_content}).eq("id", existing.data[0]['id']).execute()
                return existing.data[0]

        res = supabase.table("leads").insert(lead_data).execute()
        if not res.data:
            raise Exception("Failed to insert lead")
        return res.data[0]
    except Exception as e:
        if "unique_violation" in str(e).lower():
            raise HTTPException(status_code=409, detail="Lead already exists.") from e
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.patch("/leads/{lead_id}")
async def update_lead(lead_id: str, request: LeadUpdate, current_user: dict = Depends(get_current_user)):
    try:
        user_role = current_user.get("role", "viewer").lower()
        if user_role not in ["admin", "manager", "sales", "system_admin"]:
            raise HTTPException(status_code=403)
        supabase = get_supabase_client()
        update_data = request.model_dump(exclude_unset=True)
        res = supabase.table("leads").update(update_data).eq("id", lead_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        return res.data[0]
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/leads/{lead_id}/promote")
async def promote_lead_to_vendor(lead_id: str, request: PromoteLeadRequest, current_user: dict = Depends(get_current_user)):
    user_role = current_user.get("role", "viewer").lower()
    if user_role in ["viewer", "guest"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions to promote leads.")

    try:
        supabase = get_supabase_client()
        vendor_data = {
            "name": request.vendor_name,
            "contact_email": request.contact_email,
            "description": request.notes or "Promoted from 104 Lead",
            "status": "active",
            "owner_id": current_user.get("id")
        }
        vendor_res = supabase.table("vendors").insert(vendor_data).execute()
        if not vendor_res.data:
            raise Exception("Failed to create vendor record")

        new_vendor_id = vendor_res.data[0]["id"]
        supabase.table("leads").update({"status": "converted", "contact_email": request.contact_email}).eq("id", lead_id).execute()
        supabase.table("visit_logs").update({"customer_id": new_vendor_id}).eq("lead_id", lead_id).execute()

        from ..services.librarian_service import LibrarianService
        lib = LibrarianService()
        asyncio.create_task(lib.archive_sales_pitch(
            company=request.vendor_name,
            job_title="Promoted Lead",
            content=f"Promoted Vendor Profile: {request.vendor_name}\nNotes: {request.notes}",
            references=[f"lead:{lead_id}"]
        ))

        return {"success": True, "vendor": vendor_res.data[0]}
    except Exception as e:
        logger.error(f"API: Promotion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/generate-pitch", response_model=PitchResponse)
async def generate_pitch(request: PitchRequest, current_user: dict = Depends(get_current_user)):
    try:
        user_role = current_user.get("role", "viewer").lower()
        if user_role not in ["admin", "manager", "sales", "marketing", "member"]:
            raise HTTPException(status_code=403, detail="Access restricted to employees.")

        rag_service = RAGService()
        search_query = f"{request.job_title} {request.description[:500]}"
        success, search_result = await rag_service.perform_rag_query(query=search_query, match_count=3)

        context_text = ""
        references = []
        if success and isinstance(search_result, dict) and "results" in search_result:
            for res in search_result["results"]:
                source = res.get("metadata", {}).get("source", "Unknown")
                context_text += f"\n[Context: {source}]\n{res.get('content', '')}\n"
                references.append(source)

        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        provider_config = await credential_service.get_active_provider("llm")
        model_id = provider_config.get("chat_model") or "gemini-2.0-flash"
        safe_model = model_id.split("/")[-1]

        from ..prompts.sales_prompts import SALES_PITCH_SYSTEM_PROMPT
        sys_prompt = prompt_service.get_prompt("SALES_PITCH", SALES_PITCH_SYSTEM_PROMPT)
        user_prompt = f"Company: {request.company}\nRole: {request.job_title}\nDescription: {request.description}\n\nContext:\n{context_text}"

        try:
            response = client.models.generate_content(
                model=safe_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(system_instruction=sys_prompt, temperature=0.7)
            )
            if not response.text:
                raise ValueError("Empty AI response")
            return PitchResponse(content=response.text, references=references)
        except Exception as ai_err:
            get_supabase_client().table("archon_logs").insert({
                "level": "ALERT", "source": "SalesBot", "message": f"Pitch Generation Failed: {str(ai_err)[:100]}"
            }).execute()
            raise HTTPException(status_code=503, detail=f"AI Service Temporarily Unavailable: {str(ai_err)[:50]}") from ai_err
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/logo", response_model=LogoResponse)
async def generate_logo(request: LogoRequest):
    mock_svg = f'<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="{request.primary_color or "#6366f1"}"/><text x="100" y="105" font-family="Arial" font-size="24" fill="white" text-anchor="middle">{request.style.upper()}</text></svg>'
    return LogoResponse(svg_content=mock_svg, style=request.style)

@router.get("/market-stats")
async def get_market_stats():
    try:
        supabase = get_supabase_client()
        response = supabase.table("leads").select("identified_need").execute()
        needs = [item.get("identified_need", "") for item in response.data]
        return {
            "AI/LLM": sum(1 for n in needs if "AI" in n or "LLM" in n),
            "Data/BI": sum(1 for n in needs if "Data" in n or "BI" in n),
            "Total Leads": len(needs)
        }
    except Exception as e:
        return {"error": str(e)}

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

@router.patch("/blog/{post_id}/status")
async def update_blog_status(post_id: str, status: str):
    try:
        res = get_supabase_client().table("blog_posts").update({"status": status}).eq("id", post_id).execute()
        return res.data
    except Exception as e:
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
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/approvals/{item_type}/{item_id}/{action}")
async def process_approval(item_type: str, item_id: str, action: str, request: Request, current_user: dict = Depends(get_current_user)):
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["manager", "admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Manager access required.")
    try:
        supabase = get_supabase_client()
        raw_body = {}
        try:
            raw_body = await request.json()
        except Exception:
            pass
        review_notes = raw_body.get("review_notes") or raw_body.get("reviewNotes") or raw_body.get("reason")
        if item_type == "blog":
            new_status = "published" if action == "approve" else "changes_requested"
            update_data = {"status": new_status}
            if review_notes:
                update_data["review_notes"] = str(review_notes)
            res = supabase.table("blog_posts").update(update_data).eq("id", item_id).execute()
            if res.data:
                meta = res.data[0].get("generation_metadata") or {}
                task_id = meta.get("task_id")
                if task_id:
                    try:
                        ts = TaskService()
                        await ts.update_task(task_id, {"status": "done" if action == "approve" else "doing"})
                    except Exception:
                        pass
        return {"success": True, "status": action}
    except Exception as e:
        logger.error(f"API: Approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/blog/{post_id}/submit")
async def submit_blog_for_review(post_id: str, current_user: dict = Depends(get_current_user)):
    try:
        supabase = get_supabase_client()
        res = supabase.table("blog_posts").select("*").eq("id", post_id).limit(1).execute()
        if not res.data:
            raise HTTPException(status_code=404)
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
            try:
                ts = TaskService()
                await ts.update_task(task_id, {"status": "review"})
            except Exception:
                pass
        return {"success": True, "status": new_status, "ai_score": final_score, "review_notes": final_notes}
    except Exception as e:
        logger.error(f"API: Submit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/approvals/reject-suggestion")
async def reject_suggestion(request: MarketingRejectSuggestionRequest, current_user: dict = Depends(get_current_user)):
    try:
        user_role = current_user.get("role", "viewer").lower()
        if user_role not in ["admin", "manager"]:
            raise HTTPException(status_code=403)
        supabase = get_supabase_client()
        post_res = supabase.table("blog_posts").select("title, content").eq("id", request.blog_post_id).single().execute()
        if not post_res.data:
            raise HTTPException(status_code=404)
        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        provider_config = await credential_service.get_active_provider("llm")
        model_id = provider_config.get("chat_model") or "gemini-2.0-flash"
        response = client.models.generate_content(model=model_id.replace("models/", ""), contents=REJECTION_REASON_PROMPT.format(title=post_res.data.get("title"), content=post_res.data.get("content")[:3000]))
        return {"suggested_reason": response.text}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/request-info")
async def request_info(request: RequestInfoRequest, current_user: dict = Depends(get_current_user)):
    try:
        user_role = current_user.get("role", "viewer").lower()
        if user_role not in ["admin", "manager", "marketing"]:
            raise HTTPException(status_code=403)
        ts = TaskService()
        success, result = await ts.create_info_request_task(requester_id=str(current_user.get("email")), subject=request.subject, context=request.context, lead_id=request.lead_id)
        if not success:
            raise Exception(result.get("error"))
        return {"success": True, "task": result.get("task")}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/blog/draft", response_model=DraftBlogResponse)
async def draft_blog_post(request: DraftBlogRequest, current_user: dict = Depends(get_current_user)):
    try:
        is_valid, error_msg = GuardrailService.validate_input(f"{request.topic} {request.keywords or ''}")
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Guardrail Violation: {error_msg}")

        rag_service = RAGService()
        search_query = f"{request.topic} {request.keywords or ''}"
        success, rag_res = await rag_service.perform_rag_query(query=search_query, match_count=5)
        context_text = ""
        if request.context_source_id:
            supabase = get_supabase_client()
            if request.context_type == "lead":
                log_res = supabase.table("visit_logs").select("summary, voice_transcript").eq("lead_id", request.context_source_id).execute()
                for log in log_res.data:
                    context_text += f"\n[Alice Signal]: {log['summary']}\n{log['voice_transcript']}\n"

        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        sys_prompt = prompt_service.get_prompt("BLOG_DRAFT", BLOG_DRAFT_SYSTEM_PROMPT)
        user_prompt = f"Topic: {request.topic}\nContext:\n{context_text}"

        try:
            response = client.models.generate_content(model="gemini-2.0-flash-lite", contents=cast(Any, [user_prompt]), config=types.GenerateContentConfig(system_instruction=sys_prompt, response_mime_type="application/json", temperature=0.7))
            result = safe_json_loads(response.text or "{}")
        except Exception:
            client_fb = genai.Client(api_key=api_key)
            response = client_fb.models.generate_content(model="gemini-1.5-pro", contents=cast(Any, [user_prompt]), config=types.GenerateContentConfig(system_instruction=sys_prompt, response_mime_type="application/json", temperature=0.7))
            result = safe_json_loads(response.text or "{}")

        content = str(result.get("content", ""))
        is_safe, audit_msg = GuardrailService.audit_output(content, context_text)
        if not is_safe:
            raise HTTPException(status_code=422, detail=f"AI Output Blocked: {audit_msg}")

        metadata = {"task_id": request.context_source_id if request.context_type == "task" else None, "context_source_id": request.context_source_id, "context_type": request.context_type}
        return DraftBlogResponse(title=str(result.get("title", "Untitled")), content=content, excerpt=str(result.get("excerpt", "")), metadata=metadata)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
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
    except Exception:
        return {"keyword_growth": [], "sankey_flow": {}}

@router.post("/enrichment/trigger")
async def trigger_enrichment_loop(current_user: dict = Depends(get_current_user)):
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["admin", "system_admin", "marketing"]:
        raise HTTPException(status_code=403)
    from ..services.enrichment_service import EnrichmentService
    pruned = await EnrichmentService.prune_stale_leads()
    return {"success": True, "pruned": pruned}

@router.delete("/leads/reset")
async def reset_leads(current_user: dict = Depends(get_current_user)):
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["admin", "system_admin"]:
        raise HTTPException(status_code=403)
    res = get_supabase_client().table("leads").delete().neq("id", str(uuid.uuid4())).execute()
    return {"success": True, "deleted": len(res.data) if res.data else 0}

@router.get("/manager/alerts")
async def get_manager_alerts(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["manager", "admin"]:
        raise HTTPException(status_code=403)
    res = get_supabase_client().table("archon_logs").select("*").eq("level", "ALERT").in_("source", ["sentinel", "LeadScoring", "BusinessGuard"]).order("created_at", desc=True).limit(50).execute()
    return res.data or []

@router.post("/manager/sentinel/run")
async def trigger_sentinel(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["manager", "admin"]:
        raise HTTPException(status_code=403)
    from ..services.scheduler_service import scheduler_service
    await scheduler_service.run_business_sentinel()
    return {"status": "triggered"}

@router.post("/manager/alerts/{alert_id}/dispatch")
async def dispatch_alert_task(alert_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["manager", "admin"]:
        raise HTTPException(status_code=403)
    from ..services.projects.task_service import TaskService
    ts = TaskService()
    success, result = await ts.generate_task_from_alert(alert_id=alert_id, triggered_by=current_user.get("id"))
    if not success:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result

@router.post("/manager/knowledge/seed")
async def seed_knowledge_base(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["manager", "admin"]:
        raise HTTPException(status_code=403)
    return {"status": "completed", "message": "Manual seeding process finished."}
