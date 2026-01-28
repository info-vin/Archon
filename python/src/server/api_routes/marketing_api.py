import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger, logfire
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

logger = get_logger(__name__)

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
        logfire.info(f"API: Searching jobs | keyword={keyword}")
        jobs = await JobBoardService.search_jobs(keyword, limit)

        # Auto-save leads asynchronously
        new_leads = await JobBoardService.identify_leads_and_save(jobs)
        logfire.info(f"API: Auto-saved leads | count={new_leads}")

        return jobs
    except Exception as e:
        logfire.error(f"API: Job search failed | error={str(e)}")
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
        logfire.error(f"API: Failed to fetch leads | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

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
        logfire.warn(f"API: Access denied for promotion | user={current_user.get('email')} | role={user_role}")
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
        logfire.info(f"API: Promoting lead to vendor | lead_id={lead_id} | vendor={request.vendor_name} | user_role={user_role} | user_id={current_user.get('id')}")

        vendor_res = supabase.table("vendors").insert(vendor_data).execute()

        if not vendor_res.data:
            raise Exception("Failed to create vendor record - Database returned no data")

        # 2. Update Lead Status
        update_payload = {"status": "converted"}
        if request.contact_email:
             update_payload["contact_email"] = request.contact_email

        supabase.table("leads").update(update_payload).eq("id", lead_id).execute()

        # 3. Trigger Librarian (Fire-and-forget archiving)
        try:
            # Fetch lead details for better context (job_title, etc.)
            lead_res = supabase.table("leads").select("*").eq("id", lead_id).single().execute()
            lead_data = lead_res.data

            if lead_data:
                from ..services.librarian_service import LibrarianService
                librarian = LibrarianService()

                # Use notes as content or fallback to basic info
                content_to_archive = request.notes or f"Lead promoted: {lead_data.get('company_name')}"

                asyncio.create_task(librarian.archive_sales_pitch(
                    company=request.vendor_name,
                    job_title=lead_data.get("job_title", "General"),
                    content=content_to_archive,
                    references=[f"lead:{lead_id}", lead_data.get("source_job_url")]
                ))
                logfire.info(f"API: Librarian triggered for lead_id={lead_id}")
        except Exception as lib_err:
            logfire.warning(f"API: Librarian trigger failed | lead_id={lead_id} | error={lib_err}")

        return {"success": True, "vendor": vendor_res.data[0]}
    except Exception as e:
        logfire.error(f"API: Lead promotion failed | id={lead_id} | error={str(e)}", exc_info=True)
        # Return clearer error detail
        raise HTTPException(status_code=500, detail=f"Promotion failed: {str(e)}") from e

@router.post("/generate-pitch", response_model=PitchResponse)
async def generate_pitch(request: PitchRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate a tailored sales pitch using RAG to find relevant case studies.
    """
    try:
        logfire.info(f"API: Generating pitch | company={request.company} | user={current_user.get('email')}")

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

        if success and "results" in search_result:
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
            content = response.choices[0].message.content

        return PitchResponse(content=content, references=references)
    except Exception as e:
        logfire.error(f"API: Pitch generation failed | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e

@router.post("/logo", response_model=LogoResponse)
async def generate_logo(request: LogoRequest):
    """
    Triggers DevBot to generate a dynamic SVG logo asset.
    """
    try:
        logfire.info(f"API: Generating logo | style={request.style}")

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
        logfire.error(f"API: Logo generation failed | error={str(e)}")
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
        logfire.error(f"API: Market stats fetch failed | error={str(e)}")
        return {"error": str(e)}

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
        logfire.error(f"API: Blog status update failed | post_id={post_id} | error={str(e)}")
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
        logfire.error(f"API: Failed to fetch approvals | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/approvals/{item_type}/{item_id}/{action}")
async def process_approval(
    item_type: str,
    item_id: str,
    action: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Process approval action (approve/reject).
    """
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["system_admin", "admin", "manager"]:
        logfire.warn(f"API: Approval denied | user={current_user.get('email')} | role={user_role}")
        raise HTTPException(status_code=403, detail="Only Managers can approve items.")

    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    try:
        supabase = get_supabase_client()

        if item_type == "blog":
            new_status = "published" if action == "approve" else "draft"
            supabase.table("blog_posts").update({"status": new_status}).eq("id", item_id).execute()
            return {"success": True, "status": new_status}

        raise HTTPException(status_code=400, detail="Unknown item type")

    except Exception as e:
        logfire.error(f"API: Approval process failed | type={item_type} | id={item_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/blog/draft", response_model=DraftBlogResponse)
async def draft_blog_post(request: DraftBlogRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate a blog post draft using AI with RAG support.
    """
    try:
        logfire.info(f"API: Drafting blog | topic={request.topic} | user={current_user.get('email')}")

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
            match_count=5,
            metadata_filter={"knowledge_type": "sales_pitch"}
        )

        context_text = ""
        references = []

        if success and "results" in search_result:
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
        model_name = provider_config.get("chat_model") or "gpt-4o"

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
            result = json.loads(response.choices[0].message.content)

        # 3. Guardrail Output Audit
        generated_content = result.get("content", "")
        is_safe, audit_msg = GuardrailService.audit_output(generated_content, context_text)
        if not is_safe:
            logfire.error(f"API: Guardrail audit failed | reason={audit_msg}")
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
        logfire.error(f"API: Blog drafting failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
