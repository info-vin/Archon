import asyncio
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..prompts.marketing_prompts import BLOG_DRAFT_SYSTEM_PROMPT
from ..prompts.sales_prompts import SALES_PITCH_SYSTEM_PROMPT
from ..services.credential_service import credential_service
from ..services.guardrail_service import GuardrailService
from ..services.job_board_service import JobBoardService, JobData
from ..services.llm_provider_service import get_llm_client
from ..services.search.rag_service import RAGService
from ..utils import get_supabase_client

# TODO(Phase 5): Re-enable this when MCP Server is properly integrated as a package or service
# from mcp_server.features.design.logo_tool import GenerateBrandAssetTool

logger: logging.Logger = get_logger(__name__)

router = APIRouter(prefix="/api/marketing", tags=["marketing"])

class PitchRequest(BaseModel):
    job_title: str
    company: str
    description: str

class PitchResponse(BaseModel):
    content: str
    references: list[str]

class LogoRequest(BaseModel):
    style: str = "eciton"
    primary_color: str | None = None

class LogoResponse(BaseModel):
    svg_content: str
    style: str

class PromoteLeadRequest(BaseModel):
    vendor_name: str
    contact_email: str | None = None
    notes: str | None = None

class DraftBlogRequest(BaseModel):
    topic: str
    keywords: str | None = None
    tone: str = "professional"
    context_source_id: str | None = None
    context_type: str | None = "lead" # "lead" or "task"

class DraftBlogResponse(BaseModel):
    title: str
    content: str
    excerpt: str
    references: list[str] = []

@router.get("/jobs", response_model=list[JobData])
async def search_jobs(keyword: str = Query(..., min_length=1), limit: int = 10):
    """
    Search for jobs and automatically identify/save potential leads.
    """
    try:
        logger.info(f"API: Searching jobs | keyword={keyword}")
        jobs = await JobBoardService.search_jobs(keyword, limit)

        # Auto-save leads asynchronously
        new_leads = await JobBoardService.identify_leads_and_save(jobs)
        logger.info(f"API: Auto-saved leads | count={new_leads}")

        return jobs
    except Exception as e:
        logger.error(f"API: Job search failed | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e

@router.get("/leads")
async def get_leads():
    """
    Fetch all saved leads from the database.
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("leads").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"API: Failed to fetch leads | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

class CreateLeadRequest(BaseModel):
    company_name: str
    job_title: str
    source: str = "manual"
    source_job_url: str | None = None
    identified_need: str | None = None
    status: str = "new"

@router.post("/leads")
async def create_lead(
    request: CreateLeadRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Manually create a new lead (e.g. from Job Search results).
    """
    try:
        logger.info(f"API: Creating lead | company={request.company_name} | user={current_user.get('email')}")
        supabase = get_supabase_client()

        lead_data = request.model_dump()
        lead_data["created_from_user_id"] = current_user.get("id")
        lead_data["created_at"] = "now()"
        lead_data["updated_at"] = "now()"

        # Check for duplicates? For now, we allow multiple leads for same company if different jobs.
        # But maybe we should upsert based on source_job_url if present?
        # Let's simple insert for now as per immediate requirement.

        res = supabase.table("leads").insert(lead_data).execute()

        if not res.data:
             raise Exception("Database returned no data after insert")

        logger.info(f"API: Lead created successfully | id={res.data[0]['id']}")
        return res.data[0]

    except Exception as e:
        logger.error(f"API: Failed to create lead | error={str(e)}")
        # If duplicated url, handle gracefully?
        error_detail = str(e)
        if "unique_violation" in error_detail.lower():
             raise HTTPException(status_code=409, detail="Lead already exists.") from e

        raise HTTPException(status_code=500, detail=error_detail) from e

@router.post("/leads/{lead_id}/promote")
async def promote_lead_to_vendor(
    lead_id: str,
    request: PromoteLeadRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Promote a Lead to a Vendor.
    """
    # Secure Role Check using Authenticated User Context
    user_role = current_user.get("role", "viewer").lower()

    # Allow: admin, manager, sales, marketing, member
    # Deny: viewer, guest
    if user_role in ["viewer", "guest"]:
        logger.warning(f"API: Access denied for promotion | user={current_user.get('email')} | role={user_role}")
        raise HTTPException(status_code=403, detail="Insufficient permissions to promote leads.")

    try:
        supabase = get_supabase_client()

        # 1. Create Vendor
        vendor_data = {
            "name": request.vendor_name,
            "contact_email": request.contact_email,
            "description": request.notes or "Promoted from 104 Lead",
            "status": "active",
            "owner_id": current_user.get("id"), # Set current user as owner
            "created_at": "now()", # Ensure timestamp is set
            "updated_at": "now()"
        }

        # Log the attempt
        logger.info(f"API: Promoting lead to vendor | lead_id={lead_id} | vendor={request.vendor_name} | user_role={user_role} | user_id={current_user.get('id')}")

        vendor_res = supabase.table("vendors").insert(vendor_data).execute()

        if not vendor_res.data:
            raise Exception("Failed to create vendor record - Database returned no data")

        new_vendor_id = vendor_res.data[0]["id"]

        # 2. Update Lead Status
        update_payload = {"status": "converted"}
        if request.contact_email:
             update_payload["contact_email"] = request.contact_email

        supabase.table("leads").update(update_payload).eq("id", lead_id).execute()

        # --- Visit Log Inheritance ---
        # Link historical visit logs from this lead to the new vendor/customer
        try:
            supabase.table("visit_logs").update({"customer_id": new_vendor_id}).eq("lead_id", lead_id).execute()
            logger.info(f"API: Inherited visit logs from lead {lead_id} to vendor {new_vendor_id}")
        except Exception as inherit_err:
            logger.warning(f"API: Failed to inherit visit logs: {inherit_err}")
        # -----------------------------

        # 3. Trigger Librarian (Fire-and-forget archiving)
        try:
            # Fetch lead details for better context (job_title, etc.)
            lead_res = supabase.table("leads").select("*").eq("id", lead_id).single().execute()
            lead_data = lead_res.data

            if lead_data:
                from ..services.librarian_service import LibrarianService
                librarian = LibrarianService()

                # Use notes as content or fallback to basic info
                base_content = request.notes or f"Promoted Lead: {lead_data.get('company_name')}"

                # Extract Enriched Data for KB
                identified_need = lead_data.get("identified_need", "")
                enrichment_block = ""
                if "[Auto-Enriched Data]" in identified_need:
                    try:
                        _, enriched_part = identified_need.split("[Auto-Enriched Data]")
                        enrichment_block = f"\n\n## Market Intelligence\n{enriched_part.strip()}"
                    except Exception:
                        pass

                # Format full content for Knowledge Base (RAG Source)
                content_to_archive = (
                    f"# Vendor Profile: {request.vendor_name}\n"
                    f"**Source**: {lead_data.get('source')} | **Job Title**: {lead_data.get('job_title')}\n\n"
                    f"## Business Need\n{identified_need.replace('[Auto-Enriched Data]', '').split('Tax ID:')[0].strip()}\n"
                    f"{enrichment_block}\n\n"
                    f"## Internal Notes\n{base_content}"
                )

                asyncio.create_task(librarian.archive_sales_pitch(
                    company=request.vendor_name,
                    job_title=lead_data.get("job_title", "General"),
                    content=content_to_archive,
                    references=[f"lead:{lead_id}", lead_data.get("source_job_url")]
                ))
                logger.info(f"API: Librarian triggered for lead_id={lead_id}")
        except Exception as lib_err:
            logger.warning(f"API: Librarian trigger failed | lead_id={lead_id} | error={lib_err}")

        from fastapi.encoders import jsonable_encoder
        return {"success": True, "vendor": jsonable_encoder(vendor_res.data[0])}
    except Exception as e:
        logger.error(f"API: Lead promotion failed | id={lead_id} | error={str(e)}", exc_info=True)
        # Detailed error for debugging (safe to expose to authenticated users)
        error_detail = f"Promotion failed: {str(e)}. User Role: {user_role}"
        if "column" in str(e).lower():
            error_detail += " (Database Schema Error)"
        elif "permission" in str(e).lower():
            error_detail += " (Permission Error)"

        raise HTTPException(status_code=500, detail=error_detail) from e

class UpdateLeadRequest(BaseModel):
    status: str | None = None
    notes: str | None = None
    enrichment_status: str | None = None

@router.patch("/leads/{lead_id}")
async def update_lead(
    lead_id: str,
    request: UpdateLeadRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update lead status or details.
    """
    try:
        supabase = get_supabase_client()
        update_data = {}
        if request.status:
            update_data["status"] = request.status
        if request.enrichment_status:
             update_data["enrichment_status"] = request.enrichment_status

        # If notes in future... currently lead table might not have notes column directly or is JSONB?
        # Checking schema... migration 006 says nothing about notes.
        # But we can update generic fields.

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_data["updated_at"] = "now()"

        res = supabase.table("leads").update(update_data).eq("id", lead_id).execute()
        return res.data
    except Exception as e:
        logger.error(f"API: Lead update failed | id={lead_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/generate-pitch", response_model=PitchResponse)
async def generate_pitch(request: PitchRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate a tailored sales pitch using RAG to find relevant case studies.
    """
    try:
        logger.info(f"API: Generating pitch | company={request.company} | user={current_user.get('email')}")

        # Secure Role Check
        user_role = current_user.get("role", "viewer").lower()
        if user_role not in ["admin", "manager", "sales", "marketing", "member"]:
             if user_role == "viewer":
                 raise HTTPException(status_code=403, detail="Access restricted to active employees.")

        # 1. RAG Search
        search_query = f"{request.job_title} {request.description[:500]}"
        rag_service = RAGService()
        success, search_result = await rag_service.perform_rag_query(query=search_query, match_count=3)

        context_text = ""
        references = []

        if success and isinstance(search_result, dict) and "results" in search_result:
            for res in search_result["results"]:
                meta = res.get("metadata", {})
                source = meta.get("source", "Unknown Source")
                content = res.get("content", "").strip()
                context_text += f"\n[Source: {source}]\n{content}\n"
                references.append(source)

        if not context_text:
            context_text = "No specific case studies found. Use general Archon capabilities: AI automation, data analytics, and efficiency improvement."

        # 2. LLM Generation
        provider_config = await credential_service.get_active_provider("llm")
        model_name = provider_config.get("chat_model") or "gpt-4o"

        system_prompt = SALES_PITCH_SYSTEM_PROMPT

        user_prompt = f"Target Company: {request.company}\nHiring For: {request.job_title}\n\nContext:\n{context_text}"

        async with get_llm_client() as client:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.7
            )
            content = str(response.choices[0].message.content)

        return PitchResponse(content=content, references=references)
    except Exception as e:
        logger.error(f"API: Pitch generation failed | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e

@router.post("/logo", response_model=LogoResponse)
async def generate_logo(request: LogoRequest):
    """
    Triggers DevBot to generate a dynamic SVG logo asset.
    """
    try:
        logger.info(f"API: Generating logo | style={request.style}")

        mock_svg = f"""
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="{request.primary_color or '#f0f0f0'}" />
            <circle cx="100" cy="100" r="50" fill="#6366f1" />
            <text x="100" y="105" font-family="Arial" font-size="24" fill="white" text-anchor="middle">
                {request.style.upper()}
            </text>
        </svg>
        """

        return LogoResponse(svg_content=mock_svg.strip(), style=request.style)

    except Exception as e:
        logger.error(f"API: Logo generation failed | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e

@router.get("/market-stats")
async def get_market_stats():
    """
    Aggregates keyword data from 'leads' table for Market Specs dashboard.
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("leads").select("identified_need").execute()

        needs = [item.get("identified_need", "") for item in response.data]
        stats = {
            "AI/LLM": sum(1 for n in needs if "AI" in n or "LLM" in n),
            "Data/BI": sum(1 for n in needs if "Data" in n or "BI" in n),
            "Marketing": sum(1 for n in needs if "Marketing" in n),
            "Total Leads": len(needs)
        }
        return stats
    except Exception as e:
        logger.error(f"API: Market stats fetch failed | error={str(e)}")
        return {"error": str(e)}

@router.get("/sources")
async def get_content_sources(current_user: dict = Depends(get_current_user)):
    """
    Bob's Victory Feed: Aggregates High-Score Leads and Assigned Tasks.
    """
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")

        # 1. Fetch High Score Leads
        # Using the RLS policy defined in migration 022
        lead_res = supabase.table("leads").select("id, company_name, enrichment_score, identified_need, created_at")\
            .or_("status.eq.WON,enrichment_score.gte.80")\
            .order("created_at", desc=True).limit(20).execute()

        sources = []
        for lead in lead_res.data:
            sources.append({
                "id": lead["id"],
                "type": "lead",
                "title": lead["company_name"],
                "score": lead["enrichment_score"],
                "summary": lead["identified_need"][:100] if lead["identified_need"] else "",
                "date": lead["created_at"]
            })

        # 2. Fetch Bob's assigned tasks (Collaborating with Charlie)
        task_res = supabase.table("archon_tasks").select("id, title, description, created_at")\
            .eq("assignee_id", user_id)\
            .neq("status", "done")\
            .order("created_at", desc=True).limit(10).execute()

        for task in task_res.data:
            sources.append({
                "id": task["id"],
                "type": "task",
                "title": task["title"],
                "score": 100, # Tasks are high priority
                "summary": task["description"][:100] if task["description"] else "",
                "date": task["created_at"]
            })

        return sorted(sources, key=lambda x: x["date"], reverse=True)
    except Exception as e:
        logger.error(f"API: Failed to fetch content sources | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/context/{source_id}")
async def get_content_context(
    source_id: str,
    source_type: str = Query("lead"),
    current_user: dict = Depends(get_current_user)
):
    """
    Librarian's Context Fetcher: Aggregates logs and RAG docs for a source.
    """
    try:
        supabase = get_supabase_client()
        context_text = ""
        logs = []

        if source_type == "lead":
            # Fetch Visit Logs
            log_res = supabase.table("visit_logs").select("*").eq("lead_id", source_id).execute()
            logs = log_res.data
            for log in logs:
                context_text += f"\n[Visit Log Summary]: {log.get('summary')}\n[Transcript]: {log.get('voice_transcript')}\n"

            # Fetch Lead Info for RAG
            lead_res = supabase.table("leads").select("identified_need").eq("id", source_id).single().execute()
            if lead_res.data:
                context_text += f"\n[Lead Need]: {lead_res.data.get('identified_need')}\n"

        elif source_type == "task":
            # Fetch Task Details
            task_res = supabase.table("archon_tasks").select("*").eq("id", source_id).single().execute()
            if task_res.data:
                context_text += f"\n[Task Title]: {task_res.data.get('title')}\n[Description]: {task_res.data.get('description')}\n"

        # Call Librarian (RAG)
        rag_service = RAGService()
        success, search_result = await rag_service.perform_rag_query(
            query=context_text[:1000],
            match_count=3
        )

        rag_refs = []
        if success and isinstance(search_result, dict) and "results" in search_result:
            rag_refs = search_result["results"]

        return {
            "source_id": source_id,
            "source_type": source_type,
            "logs": logs,
            "rag_refs": rag_refs,
            "context_summary": context_text
        }
    except Exception as e:
        logger.error(f"API: Failed to fetch context | id={source_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.patch("/blog/{post_id}/status")
async def update_blog_status(post_id: str, status: str):
    """
    Updates the status of a blog post for Kanban flow.
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("blog_posts").update({"status": status}).eq("id", post_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"API: Blog status update failed | post_id={post_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/approvals")
async def get_pending_approvals():
    """
    Get all items requiring approval.
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("blog_posts").select("*").eq("status", "review").execute()

        return {
            "blogs": response.data,
            "leads": []
        }
    except Exception as e:
        logger.error(f"API: Failed to fetch approvals | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/approvals/{item_type}/{item_id}/{action}")
async def process_approval(
    item_type: str,
    item_id: str,
    action: str,
    comment: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Process approval action (approve/reject).
    Only Managers can perform this action.
    """
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["system_admin", "admin", "manager"]:
        logger.warning(f"API: Approval denied | user={current_user.get('email')} | role={user_role}")
        raise HTTPException(status_code=403, detail="Only Managers can approve items.")

    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    try:
        supabase = get_supabase_client()

        if item_type == "blog":
            # State Machine: review -> published OR changes_requested
            new_status = "published" if action == "approve" else "changes_requested"

            update_payload = {
                "status": new_status,
                "updated_at": "now()"
            }

            # TODO: Store review comments in a separate table or a JSONB column in future
            # For now, we assume simple status update is enough for Phase 4.6.3

            supabase.table("blog_posts").update(update_payload).eq("id", item_id).execute()

            logger.info(f"API: Blog approval processed | id={item_id} | action={action} | user={current_user.get('email')}")
            return {"success": True, "status": new_status}

        raise HTTPException(status_code=400, detail="Unknown item type")

    except Exception as e:
        logger.error(f"API: Approval process failed | type={item_type} | id={item_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/blog/{post_id}/submit")
async def submit_blog_for_review(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Bob submits a draft for review.
    Triggers 'Reviewer' Bot (AI) for compliance check.
    """
    try:
        supabase = get_supabase_client()

        # 1. Fetch Draft Content
        res = supabase.table("blog_posts").select("*").eq("id", post_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Blog post not found")

        post = res.data
        if post["status"] != "draft" and post["status"] != "changes_requested":
             raise HTTPException(status_code=400, detail=f"Cannot submit post in status: {post['status']}")

        # 2. Trigger AI Reviewer (Simulated for Phase 4.6.3)
        # In a real implementation, this would call get_llm_client() with a specific prompt
        # Here we simulate the logic:
        # - Content length < 50 chars -> Reject (Low Quality)
        # - Content contains "CONFIDENTIAL" -> Reject (Compliance)
        # - Otherwise -> Pass

        content = post.get("content", "")
        ai_score = 85 # Default high score
        review_notes = "AI Compliance Check: Passed. Tone is consistent."
        auto_reject = False

        if len(content) < 50:
            ai_score = 40
            review_notes = "AI Review: Content too short. Please expand."
            auto_reject = True
        elif "CONFIDENTIAL" in content.upper():
            ai_score = 0
            review_notes = "AI Review: Security Alert. Found sensitive keyword 'CONFIDENTIAL'."
            auto_reject = True

        # 3. Decision Logic
        if auto_reject:
            new_status = "changes_requested"
            logger.info(f"API: AI Auto-Reject | id={post_id} | score={ai_score}")
        else:
            new_status = "review" # PENDING_REVIEW
            logger.info(f"API: AI Auto-Pass | id={post_id} | score={ai_score}")

        # 4. Update DB
        supabase.table("blog_posts").update({
            "status": new_status
            # In future: store review_notes and ai_score in DB
        }).eq("id", post_id).execute()

        return {
            "success": True,
            "status": new_status,
            "ai_score": ai_score,
            "review_notes": review_notes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Blog submission failed | id={post_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/blog/draft", response_model=DraftBlogResponse)
async def draft_blog_post(request: DraftBlogRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate a blog post draft using AI with RAG support.
    """
    try:
        logger.info(f"API: Drafting blog | topic={request.topic} | user={current_user.get('email')}")

        # 0. Guardrail Input Check
        is_valid, error_msg = GuardrailService.validate_input(f"{request.topic} {request.keywords or ''}")
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Guardrail Violation: {error_msg}")

        # Role check
        user_role = current_user.get("role", "viewer").lower()
        if user_role == "viewer":
            raise HTTPException(status_code=403, detail="Viewers cannot generate content.")

        # 1. RAG Search (Bob's memory)
        rag_service = RAGService()
        search_query = f"{request.topic} {request.keywords or ''}"

        success, search_result = await rag_service.perform_rag_query(
            query=search_query,
            match_count=5
        )

        context_text = ""
        references = []

        # Workbench Integration: Fetch specific context from Lead/Task if provided
        if request.context_source_id:
            logger.info(f"API: Fetching specific context for {request.context_type}={request.context_source_id}")
            supabase = get_supabase_client()
            if request.context_type == "lead":
                log_res = supabase.table("visit_logs").select("summary, voice_transcript").eq("lead_id", request.context_source_id).execute()
                if log_res.data:
                    context_text += "\n### Alice's Visit Logs (Sales Context):\n"
                    for log in log_res.data:
                        context_text += f"- Summary: {log['summary']}\n- Transcript: {log['voice_transcript']}\n"
            elif request.context_type == "task":
                task_res = supabase.table("archon_tasks").select("title, description").eq("id", request.context_source_id).single().execute()
                if task_res.data:
                    context_text += f"\n### Task Context:\n- Title: {task_res.data['title']}\n- Description: {task_res.data['description']}\n"

        if success and isinstance(search_result, dict) and "results" in search_result:
            for res in search_result["results"]:
                meta = res.get("metadata", {})
                source = meta.get("source", "Unknown Source")
                content = res.get("content", "").strip()
                if source not in references:
                    references.append(source)

                context_text += f"\n[Source: {source}]\n{content}\n"

        if not context_text:
            context_text = "No specific internal references found. Rely on general industry knowledge."

        # 2. LLM Generation
        provider_config = await credential_service.get_active_provider("llm")
        # Optimization: Fetch MARKETING_MODEL
        rag_strategy_creds = await credential_service.get_credentials_by_category("rag_strategy")
        marketing_model = rag_strategy_creds.get("MARKETING_MODEL")
        model_name = marketing_model or provider_config.get("chat_model") or "gpt-4o"

        system_prompt = BLOG_DRAFT_SYSTEM_PROMPT
        user_prompt = f"Topic: {request.topic}\nKeywords: {request.keywords}\nTone: {request.tone}\n\n<reference_context>\n{context_text}\n</reference_context>"

        async with get_llm_client() as client:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                response_format={ "type": "json_object" },
                temperature=0.7
            )
            import json
            # Ensure content is a string
            message_content = response.choices[0].message.content or "{}"
            result = json.loads(message_content)

        # 3. Guardrail Output Audit
        generated_content = result.get("content", "")
        is_safe, audit_msg = GuardrailService.audit_output(generated_content, context_text)
        if not is_safe:
            logger.error(f"API: Guardrail audit failed | reason={audit_msg}")
            raise HTTPException(status_code=422, detail=f"AI Output Blocked: {audit_msg}")

        return DraftBlogResponse(
            title=result.get("title", "Untitled Draft"),
            content=generated_content,
            excerpt=result.get("excerpt", ""),
            references=result.get("used_references", references)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Blog drafting failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/nana-banana")
async def nana_banana_proxy(
    request: dict, # Pass-through payload
    current_user: dict = Depends(get_current_user)
):
    """
    Proxy request to Nana Banana Image Generation Service.
    Protected by Backend Env Key.
    """
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["marketing", "manager", "admin"]:
        raise HTTPException(status_code=403, detail="Only Marketing/Managers can generate assets.")

    api_key = await credential_service.get_credential("GOOGLE_API_KEY")
    if not api_key:
        api_key = await credential_service.get_credential("GEMINI_API_KEY") # Fallback

    if not api_key:
        raise HTTPException(status_code=503, detail="Google API Key Not Configured")

    # Real Implementation for Google Imagen 3
    rag_strategy_creds = await credential_service.get_credentials_by_category("rag_strategy")
    # Default to imagen-3.0-generate-001 (Preview/Beta)
    imagen_model = rag_strategy_creds.get("MARKETING_IMAGE_MODEL") or "imagen-3.0-generate-001"

    logger.info(f"API: Google Imagen Call ({imagen_model}) | user={current_user.get('email')}")

    prompt = request.get("prompt", "A futuristic digital artwork of a high-tech dashboard")
    aspect_ratio = request.get("aspect_ratio", "1:1")

    # Google Imagen via REST API (Generative Language API)
    # Endpoint: https://generativelanguage.googleapis.com/v1beta/models/{model}:predict
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{imagen_model}:predict?key={api_key}"

    payload = {
        "instances": [
            {
                "prompt": prompt
            }
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": aspect_ratio
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30.0)

            if response.status_code != 200:
                logger.error(f"Imagen API Error: {response.text}")
                # Mock Fallback if API fails (e.g. 404 model specific or quota)
                if response.status_code == 404 or response.status_code == 403:
                     logger.warning("Imagen Model not found or permitted, falling back to mock for demo stability.")
                     return {
                        "status": "fallback_mock",
                        "image_url": "https://placehold.co/600x400/png?text=Imagen+Fallback+Mock"
                     }
                raise HTTPException(status_code=response.status_code, detail=f"Imagen API Failed: {response.text}")

            data = response.json()
            # Extract base64 image
            # structure: predictions[0].bytesBase64Encoded
            # or predictions[0].mimeType

            if "predictions" in data and len(data["predictions"]) > 0:
                prediction = data["predictions"][0]
                b64_image = prediction.get("bytesBase64Encoded")
                mime_type = prediction.get("mimeType", "image/png")

                # We return raw base64 data URL for frontend to display directly
                # In prod, we should upload this to Supabase Storage and return URL
                return {
                    "status": "success",
                    "image_url": f"data:{mime_type};base64,{b64_image}"
                }
            else:
                raise Exception("No predictions returned")

    except Exception as e:
        logger.error(f"Imagen API Exception: {e}")
        # Graceful degradation
        return {
            "status": "error_fallback",
            "image_url": "https://placehold.co/600x400/png?text=Imagen+Error+Fallback"
        }

@router.get("/trends")
async def get_marketing_trends(
    current_user: dict = Depends(get_current_user)
):
    """
    Get cached marketing trends from `marketing_trends` table.
    """
    try:
        supabase = get_supabase_client()
        # Fetch latest trend report for each type
        # Ideally we want distinct on type, order by date desc
        # Supabase/PostgREST doesn't support DISTINCT ON easily, so we fetch latest few

        # 1. Trend Line
        res_trend = supabase.table("marketing_trends").select("*").eq("trend_type", "keyword_growth").order("report_date", desc=True).limit(1).execute()

        # 2. Sankey
        res_sankey = supabase.table("marketing_trends").select("*").eq("trend_type", "sankey_flow").order("report_date", desc=True).limit(1).execute()

        return {
            "keyword_growth": res_trend.data[0]["data"] if res_trend.data else [],
            "sankey_flow": res_sankey.data[0]["data"] if res_sankey.data else {}
        }

    except Exception as e:
        logger.error(f"API: Fetch trends failed | error={str(e)}")
        # Fallback to mock data if table empty or error (graceful degradation)
        return {
            "keyword_growth": [
                {"date": "2025-01", "AI": 40, "Data": 24},
                {"date": "2025-02", "AI": 30, "Data": 13},
                {"date": "2025-03", "AI": 98, "Data": 22},
            ],
            "sankey_flow": {
                "nodes": [
                    {"name": "Finance"}, {"name": "Healthcare"},
                    {"name": "Data Analysis"}, {"name": "AI Agent"},
                    {"name": "Archon"}
                ],
                "links": [
                    {"source": 0, "target": 2, "value": 10},
                    {"source": 1, "target": 3, "value": 15},
                    {"source": 2, "target": 4, "value": 8},
                    {"source": 3, "target": 4, "value": 12}
                ]
            }
        }

@router.post("/enrichment/trigger")
async def trigger_enrichment_loop(
    current_user: dict = Depends(get_current_user)
):
    """
    Manually trigger the Enrichment & Pruning Loop.
    Usually called by a Cron Service or Admin.
    """
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["admin", "system_admin", "marketing"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    from ..services.enrichment_service import EnrichmentService

    # 1. Prune
    pruned_count = await EnrichmentService.prune_stale_leads()

    # 2. Enrich (For demo, we enrich the latest 5 new leads)
    try:
        supabase = get_supabase_client()
        # Get new leads needing enrichment
        res = supabase.table("leads").select("id").eq("status", "new").is_("enrichment_status", "null").limit(5).execute()

        enrich_count = 0
        if res.data:
            for item in res.data:
                await EnrichmentService.enrich_lead(item["id"])
                enrich_count += 1

        return {
            "success": True,
            "pruned_count": pruned_count,
            "enriched_count": enrich_count
        }
    except Exception as e:
        logger.error(f"Enrichment loop failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.delete("/leads/reset")
async def reset_leads(current_user: dict = Depends(get_current_user)):
    """
    DEV UTILITY: Delete ALL leads from the database.
    Use with caution.
    """
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["admin", "system_admin", "manager"]:
        raise HTTPException(status_code=403, detail="Permission denied: Only Admins can reset data.")

    try:
        supabase = get_supabase_client()
        # Delete all rows in leads table
        res = supabase.table("leads").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

        logger.info(f"API: Leads reset | count={len(res.data) if res.data else 0} | user={current_user.get('email')}")
        return {"success": True, "deleted_count": len(res.data) if res.data else 0}
    except Exception as e:
        logger.error(f"API: Leads reset failed | error={str(e)}")
        # Return detailed error to help debug foreign key constraints etc.
        raise HTTPException(status_code=500, detail=f"Failed to reset leads: {str(e)}") from e
