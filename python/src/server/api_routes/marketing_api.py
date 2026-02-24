import asyncio
import logging
import re
import uuid
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..prompts.marketing_prompts import BLOG_DRAFT_SYSTEM_PROMPT, REJECTION_REASON_PROMPT
from ..prompts.sales_prompts import SALES_PITCH_SYSTEM_PROMPT
from ..services.credential_service import credential_service
from ..services.guardrail_service import GuardrailService
from ..services.job_board_service import JobBoardService, JobData
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
    lost_reason: str | None = None
    lost_competitor: str | None = None

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
        current_res = supabase.table("leads").select("*").eq("id", lead_id).single().execute()
        if not current_res.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        old_lead = current_res.data
        update_data = request.model_dump(exclude_unset=True)
        res = supabase.table("leads").update(update_data).eq("id", lead_id).execute()
        new_lead = res.data[0]
        if (request.status or "").upper() == "LOST":
            from ..services.librarian_service import LibrarianService
            lib = LibrarianService()
            content_context = f"Company: {old_lead.get('company_name')}\nNeed: {old_lead.get('identified_need')}\nCompetitor: {request.lost_competitor}"
            asyncio.create_task(lib.archive_failure_case(
                content=content_context,
                reason=request.lost_reason or "Unknown",
                company=old_lead.get("company_name", "Unknown"),
                job_title=old_lead.get("job_title", "Lead")
            ))
        return new_lead
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/leads/{lead_id}/promote")
async def promote_lead_to_vendor(lead_id: str, request: PromoteLeadRequest, current_user: dict = Depends(get_current_user)):
    user_role = current_user.get("role", "viewer").lower()
    if user_role in ["viewer", "guest"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")
    try:
        supabase = get_supabase_client()
        vendor_data = {
            "name": request.vendor_name,
            "contact_email": request.contact_email,
            "description": request.notes or "Promoted from Lead",
            "status": "active",
            "owner_id": current_user.get("id")
        }
        vendor_res = supabase.table("vendors").insert(vendor_data).execute()
        new_vendor_id = vendor_res.data[0]["id"]
        supabase.table("leads").update({"status": "converted", "contact_email": request.contact_email}).eq("id", lead_id).execute()
        supabase.table("visit_logs").update({"customer_id": new_vendor_id}).eq("lead_id", lead_id).execute()
        from ..services.librarian_service import LibrarianService
        lead_data = supabase.table("leads").select("*").eq("id", lead_id).single().execute().data
        content_to_archive = f"# Vendor: {request.vendor_name}\n## Need\n{lead_data.get('identified_need')}\n## Notes\n{request.notes}"
        asyncio.create_task(LibrarianService().archive_sales_pitch(
            company=request.vendor_name,
            job_title=lead_data.get("job_title", "General"),
            content=content_to_archive,
            references=[f"lead:{lead_id}"]
        ))
        return {"success": True, "vendor": vendor_res.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/generate-pitch", response_model=PitchResponse)
async def generate_pitch(request: PitchRequest, current_user: dict = Depends(get_current_user)):
    """
    Alice's Sales Pitch Generator.
    Uses RAG context (Librarian) and Alice's core persona to craft a personalized pitch.
    """
    try:
        context_text = ""
        references = []

        # 1. Expertise & Style Context
        search_result = await RAGService().search_documents(f"Sales Pitch: {request.job_title} {request.company}")
        if search_result:
            for res in search_result:
                source = res.get("metadata", {}).get("source", "Unknown")
                context_text += f"\n[Context: {source}]\n{res.get('content', '')}\n"
                references.append(str(source))

        # 2. LLM Generation via Google GenAI SDK (Bob/Alice Standard)
        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=401, detail="AI API Key not configured. Please check Admin Settings.")

        model_id = (await credential_service.get_active_provider("llm")).get("chat_model") or "gemini-2.0-flash"
        sys_prompt = prompt_service.get_prompt("SALES_PITCH", SALES_PITCH_SYSTEM_PROMPT)

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_id.split("/")[-1],
            contents=f"Company: {request.company}\nRole: {request.job_title}\n\nContext:\n{context_text}",
            config=types.GenerateContentConfig(system_instruction=sys_prompt, temperature=0.7)
        )

        if not response.text:
            raise Exception("AI returned empty response")

        return PitchResponse(content=response.text, references=references)

    except Exception as e:
        if isinstance(e, errors.ClientError) and "429" in str(e):
            logger.warning(f"API: Google API Quota Exhausted (429) during pitch generation: {e}")
            raise HTTPException(status_code=429, detail={"error": "AI Quota Exhausted. Please wait a minute before retrying."}) from e

        if isinstance(e, HTTPException):
            raise e

        logger.error(f"API: Pitch generation failed | error={str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail={"error": f"AI Service Error: {str(e)}"}) from e

@router.post("/logo", response_model=LogoResponse)
async def generate_logo(request: LogoRequest):
    mock_svg = f'<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="{request.primary_color or "#6366f1"}"/><text x="100" y="105" font-family="Arial" font-size="24" fill="white" text-anchor="middle">{request.style.upper()}</text></svg>'
    return LogoResponse(svg_content=mock_svg, style=request.style)

@router.get("/market-stats")
async def get_market_stats():
    try:
        needs_data = get_supabase_client().table("leads").select("identified_need").execute().data
        needs = [i.get("identified_need", "") for i in needs_data]
        return {"AI/LLM": sum(1 for n in needs if "AI" in n), "Total": len(needs)}
    except Exception:
        return {"error": "Stats unavailable"}

@router.get("/sources")
async def get_content_sources(current_user: dict = Depends(get_current_user)):
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        lead_res = supabase.table("leads").select("id, company_name, enrichment_score, identified_need, created_at").or_("status.eq.WON,enrichment_score.gte.80").limit(20).execute()
        sources = []
        for log_entry in lead_res.data:
            sources.append({
                "id": log_entry["id"],
                "type": "lead",
                "title": log_entry["company_name"],
                "score": log_entry["enrichment_score"],
                "summary": log_entry["identified_need"][:100] if log_entry["identified_need"] else "",
                "date": log_entry["created_at"]
            })
        task_res = supabase.table("archon_tasks").select("id, title, description, created_at").eq("assignee_id", user_id).neq("status", "done").limit(10).execute()
        for t in task_res.data:
            sources.append({
                "id": t["id"],
                "type": "task",
                "title": t["title"],
                "score": 100,
                "summary": t["description"][:100] if t["description"] else "",
                "date": t["created_at"]
            })
        blog_res = supabase.table("blog_posts").select("id, title, excerpt, ai_score, status, created_at").in_("status", ["draft", "changes_requested"]).limit(15).execute()
        for b in blog_res.data:
            sources.append({
                "id": b["id"],
                "type": "blog",
                "title": b["title"],
                "score": b.get("ai_score", 0),
                "summary": b.get("excerpt", ""),
                "date": b["created_at"],
                "status": b["status"]
            })
        return sorted(sources, key=lambda x: x["date"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/context/{source_id}")
async def get_content_context(source_id: str, source_type: str = Query("lead"), current_user: dict = Depends(get_current_user)):
    try:
        context_text = ""
        if source_type == "lead":
            logs = get_supabase_client().table("visit_logs").select("*").eq("lead_id", source_id).execute().data
            for l_item in logs:
                context_text += f"\n[Log]: {l_item.get('summary')}\n{l_item.get('voice_transcript')}\n"
        rag_refs = []
        if context_text:
            success, res = await RAGService().perform_rag_query(query=context_text[:1000], match_count=3)
            if success:
                rag_refs = res.get("results", [])
        return {"source_id": source_id, "source_type": source_type, "rag_refs": rag_refs, "context_summary": context_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/approvals")
async def get_pending_approvals(current_user: dict = Depends(get_current_user)):
    res = get_supabase_client().table("blog_posts").select("*").eq("status", "review").order("updated_at", desc=True).execute()
    return {"blogs": res.data or [], "leads": []}

@router.post("/approvals/{item_type}/{item_id}/{action}")
async def process_approval(item_type: str, item_id: str, action: str, request: Request, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["manager", "admin", "system_admin"]:
        raise HTTPException(status_code=403)
    supabase = get_supabase_client()
    raw_body = await request.json() if request.method == "POST" else {}
    notes = raw_body.get("review_notes") or raw_body.get("reason")
    if item_type == "blog":
        new_status = "published" if action == "approve" else "changes_requested"
        res = supabase.table("blog_posts").update({"status": new_status, "review_notes": notes}).eq("id", item_id).execute()
        if res.data:
            post_data = res.data[0]
            # EXP-02: Bob's Feedback Reinforcement Loop
            if action != "approve" and notes:
                from ..services.librarian_service import LibrarianService
                asyncio.create_task(LibrarianService().archive_style_critique(
                    post_title=post_data.get("title", "Untitled"),
                    original_content=post_data.get("content", ""),
                    review_notes=notes
                ))

            task_id = (post_data.get("generation_metadata") or {}).get("task_id")
            if task_id:
                await TaskService().update_task(task_id, {"status": "done" if action == "approve" else "doing"})
    return {"success": True}

@router.post("/blog/{post_id}/submit")
async def submit_blog_for_review(post_id: str, current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    post = supabase.table("blog_posts").select("*").eq("id", post_id).single().execute().data
    from .stats_api import calculate_ai_score
    score = calculate_ai_score(post.get("content", ""))
    new_status = "changes_requested" if score < 50 else "review"
    supabase.table("blog_posts").update({"status": new_status, "ai_score": score}).eq("id", post_id).execute()
    task_id = (post.get("generation_metadata") or {}).get("task_id")
    if task_id and new_status == "review":
        await TaskService().update_task(task_id, {"status": "review"})
    return {"success": True, "status": new_status, "ai_score": score}

@router.post("/approvals/reject-suggestion")
async def reject_suggestion(request: MarketingRejectSuggestionRequest, current_user: dict = Depends(get_current_user)):
    if current_user.get("role", "viewer").lower() not in ["admin", "manager"]:
        raise HTTPException(status_code=403)
    post = get_supabase_client().table("blog_posts").select("title, content").eq("id", request.blog_post_id).single().execute().data
    if not post:
        raise HTTPException(status_code=404)
    api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
    model_id = (await credential_service.get_active_provider("llm")).get("chat_model") or "gemini-2.0-flash"
    response = genai.Client(api_key=api_key).models.generate_content(model=model_id.split("/")[-1], contents=REJECTION_REASON_PROMPT.format(title=post.get("title"), content=post.get("content")[:3000]))
    return {"suggested_reason": response.text}

@router.post("/request-info")
async def request_info(request: RequestInfoRequest, current_user: dict = Depends(get_current_user)):
    if current_user.get("role", "viewer").lower() not in ["admin", "manager", "marketing"]:
        raise HTTPException(status_code=403)
    success, res = await TaskService().create_info_request_task(requester_id=str(current_user.get("email")), subject=request.subject, context=request.context, lead_id=request.lead_id)
    if not success:
        raise HTTPException(status_code=500, detail=res.get("error"))
    return {"success": True, "task": res.get("task")}

async def _get_expert_style_context(query: str) -> str:
    """
    Unified Bob Expertise Retrieval (1.4 - Live Knowledge Injection).
    Prioritizes technical and market_intel tags during retrieval.
    """
    context_text = ""
    # 1. First attempt: High priority knowledge with strict score (1.4 - Live Knowledge Injection)
    success, rag = await RAGService().perform_rag_query(
        query=query,
        match_count=5,
        filter_metadata={"tags": ["technical", "market_intel", "style_lesson"]},
        min_score=0.25
    )

    # 2. Fallback: Generic RAG if prioritized search returns low results
    if not success or not rag.get("results"):
        success, rag = await RAGService().perform_rag_query(query=query, match_count=5, min_score=0.15)

    if success:
        for r_item in rag.get("results", []):
            metadata = r_item.get("metadata", {})
            # Explicit weighting for critical feedback
            if metadata.get("knowledge_type") == "brand_voice" or "style_lesson" in metadata.get("tags", []):
                context_text += f"\n[PAST STYLE FEEDBACK - CRITICAL]:\n{r_item['content']}\n"
            else:
                context_text += f"\n[RAG]: {r_item['content']}\n"
    return context_text

@router.post("/blog/draft", response_model=DraftBlogResponse)
async def draft_blog_post(request: DraftBlogRequest, current_user: dict = Depends(get_current_user)):
    try:
        is_valid, err = GuardrailService.validate_input(f"{request.topic} {request.keywords or ''}")
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Guardrail Violation: {err}")

        # 1. Base Alice Signals
        context_text = ""
        if request.context_source_id and request.context_type == "lead":
            logs = get_supabase_client().table("visit_logs").select("summary, voice_transcript").eq("lead_id", request.context_source_id).execute().data
            for l_entry in logs:
                context_text += f"\n[Alice Signal]: {l_entry['summary']}\n{l_entry['voice_transcript']}\n"

        # 2. Reusable Expertise Retrieval (Bob's Memory)
        context_text += await _get_expert_style_context(f"{request.topic} {request.keywords or ''}")

        is_tc = bool(re.search(r'[\u4e00-\u9fff]', request.topic))
        lang_instr = "You MUST use Traditional Chinese (Taiwan, zh-TW)." if is_tc else ""
        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")

        provider_config = await credential_service.get_active_provider("llm")
        model_id = provider_config.get("chat_model") or "gemini-2.0-flash"

        sys_prompt = prompt_service.get_prompt("BLOG_DRAFT", BLOG_DRAFT_SYSTEM_PROMPT)

        # Physical Fix: Use a dedicated client instance for this request to avoid "closed client" issues
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_id.split("/")[-1],
            contents=f"Topic: {request.topic}\nIndustry: {request.industry}\nStyle: {request.style}\nContext: {context_text}\n{lang_instr}",
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                response_mime_type="application/json",
                temperature=0.7
            )
        )

        if not response.text:
            raise Exception("AI returned empty content")

        result = safe_json_loads(response.text)
        is_safe, audit = GuardrailService.audit_output(str(result.get("content", "")), context_text)
        if not is_safe:
            raise HTTPException(status_code=422, detail=f"AI Output Blocked: {audit}")
        from ..services.token_usage_service import TokenUsageService
        if response.usage_metadata:
            asyncio.create_task(TokenUsageService.log_usage(request_id=f"blog-{uuid.uuid4().hex[:8]}", user_id=current_user.get("id"), model=model_id.split("/")[-1], provider="google", input_tokens=response.usage_metadata.prompt_token_count, output_tokens=response.usage_metadata.candidates_token_count, context_type="blog_draft"))
        return DraftBlogResponse(
            title=str(result.get("title", "")),
            content=str(result.get("content", "")),
            excerpt=str(result.get("excerpt", "")),
            used_prompt=request.topic
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/nana-banana")
async def nana_banana_proxy(request: dict, current_user: dict = Depends(get_current_user)):
    """
    Bob's Creative Studio.
    Stage 1: LLM-based Prompt Engineering (with style constraints).
    Stage 2: Tier-aware Rendering (Native Imagen vs Bob's Fallback).
    """
    try:
        user_prompt = request.get("prompt", "a professional marketing graphic")
        style = request.get("style", "professional")

        # 1. Expertise Retrieval (Bob's Memory)
        context_text = await _get_expert_style_context(f"image style {style} {user_prompt}")

        # 2. Bob's Prompt Engineering (Safe for Free Tier)
        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)

        enrichment_prompt = (
            "You are Bob, a Senior Marketing Designer. Craft a highly detailed visual prompt "
            "for an AI image generator based on the user's idea and brand constraints.\n\n"
            f"User Idea: {user_prompt}\n"
            f"Constraints: {context_text}\n\n"
            "Return ONLY the enhanced prompt in English."
        )

        enrich_resp = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=enrichment_prompt
        )
        enhanced_prompt = enrich_resp.text.strip()

        # 3. Tier-aware Rendering
        try:
            # Native attempt (Paid/Pro Tier)
            native_resp = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=cast(Any, [enhanced_prompt]),
                config=types.GenerateContentConfig(response_modalities=['IMAGE'])
            )
            for part in (native_resp.parts or []):
                if part.inline_data:
                    return {
                        "status": "success",
                        "image_url": f"data:{part.inline_data.mime_type};base64,{part.inline_data.data.decode('utf-8')}",
                        "enhanced_prompt": enhanced_prompt,
                        "tier": "native"
                    }
        except Exception as e:
            logger.info(f"NanaBanana: Native rendering unavailable ({e}). Using Bob's Fallback.")

        # 4. Bob's Fallback (Tier 2: Community AI - No Token Required)
        # Use a simplified URL structure to improve Pollinations stability
        # We replace spaces with hyphens and remove special chars for better parsing
        safe_keywords = re.sub(r'[^a-zA-Z0-9\s]', '', enhanced_prompt).strip().replace(" ", "-")
        fallback_url = f"https://image.pollinations.ai/prompt/{safe_keywords}?width=1024&height=1024&nologo=true"

        return {
            "status": "success",
            "image_url": fallback_url,
            "enhanced_prompt": enhanced_prompt,
            "tier": "fallback_pollinations",
            "note": "Generated via community AI cluster."
        }

    except Exception as e:
        logger.error(f"NanaBanana: Primary and AI Fallback failed: {e}")
        # Final Safety Net: Tier 3 (Stable Visual Asset - No AI)
        # Use a seed based on the prompt hash to keep it consistent
        import hashlib
        prompt_hash = hashlib.md5(request.get("prompt", "marketing").encode()).hexdigest()[:8]
        return {
            "status": "success",
            "image_url": f"https://picsum.photos/seed/{prompt_hash}/1024/1024",
            "enhanced_prompt": request.get("prompt"),
            "tier": "emergency_picsum",
            "note": "Fallback to stable visual placeholder."
        }

@router.get("/trends")
async def get_marketing_trends(current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    res_t = supabase.table("marketing_trends").select("*").eq("trend_type", "keyword_growth").order("report_date", desc=True).limit(1).execute()
    res_s = supabase.table("marketing_trends").select("*").eq("trend_type", "sankey_flow").order("report_date", desc=True).limit(1).execute()
    return {"keyword_growth": res_t.data[0]["data"] if res_t.data else [], "sankey_flow": res_s.data[0]["data"] if res_s.data else {}}

@router.post("/enrichment/trigger")
async def trigger_enrichment_loop(current_user: dict = Depends(get_current_user)):
    from ..services.enrichment_service import EnrichmentService
    return {"success": True, "pruned": await EnrichmentService.prune_stale_leads()}

@router.delete("/leads/reset")
async def reset_leads(current_user: dict = Depends(get_current_user)):
    if current_user.get("role", "viewer").lower() not in ["admin", "system_admin"]:
        raise HTTPException(status_code=403)
    res = get_supabase_client().table("leads").delete().neq("id", str(uuid.uuid4())).execute()
    return {"success": True, "count": len(res.data) if res.data else 0}

@router.get("/manager/alerts")
async def get_manager_alerts(current_user: dict = Depends(get_current_user)):
    if current_user.get("role", "viewer").lower() not in ["manager", "admin"]:
        raise HTTPException(status_code=403)
    res = get_supabase_client().table("archon_logs").select("*").eq("level", "ALERT").in_("source", ["sentinel", "LeadScoring"]).order("created_at", desc=True).limit(50).execute()
    return res.data or []

@router.post("/manager/sentinel/run")
async def trigger_sentinel(current_user: dict = Depends(get_current_user)):
    if current_user.get("role", "viewer").lower() not in ["manager", "admin"]:
        raise HTTPException(status_code=403)
    from ..services.scheduler_service import scheduler_service
    await scheduler_service.run_business_sentinel()
    return {"status": "triggered"}

@router.post("/manager/leads/auto-fetch")
async def trigger_daily_fetch(current_user: dict = Depends(get_current_user)):
    """Manually trigger Alice's daily lead auto-fetch."""
    if current_user.get("role", "viewer").lower() not in ["manager", "admin", "sales"]:
        raise HTTPException(status_code=403)
    from ..services.job_board_service import JobBoardService
    service = JobBoardService()
    new_leads = await service.auto_fetch_daily_leads()
    return {"success": True, "new_leads_count": new_leads}

@router.post("/manager/alerts/{alert_id}/dispatch")
async def dispatch_alert_task(alert_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role", "viewer").lower() not in ["manager", "admin"]:
        raise HTTPException(status_code=403)
    success, result = await TaskService().generate_task_from_alert(alert_id=alert_id, triggered_by=current_user.get("id"))
    if not success:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result

@router.post("/manager/knowledge/seed")
async def seed_knowledge_base(current_user: dict = Depends(get_current_user)):
    if current_user.get("role", "viewer").lower() not in ["manager", "admin"]:
        raise HTTPException(status_code=403)

    try:
        from ..services.librarian_service import LibrarianService
        lib = LibrarianService()

        # Physical Seeding: Archive a set of foundational documents
        # This resolves the 'total_sources: 0' issue in HealthService
        foundation_docs = [
            {"title": "Archon Core Vision", "content": "Archon is an AI-human collaboration framework focused on physical realization and grounded logic.", "company": "Archon Internal"},
            {"title": "Alice Persona Protocol", "content": "Alice handles sales outreach and voice-to-task automation with real-time GPS grounding.", "company": "Archon Sales"},
            {"title": "Bob Persona Protocol", "content": "Bob manages marketing assets, logo generation, and brand consistency.", "company": "Archon Marketing"}
        ]

        for doc in foundation_docs:
            await lib.archive_sales_pitch(
                company=doc["company"],
                job_title=doc["title"],
                content=doc["content"],
                references=["system:seed"]
            )

        return {"status": "completed", "documents_seeded": len(foundation_docs)}
    except Exception as e:
        logger.error(f"API: Knowledge seeding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
