
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from mcp_server.features.design.logo_tool import GenerateBrandAssetTool

from ..config.logfire_config import get_logger, logfire
from ..services.credential_service import credential_service
from ..services.job_board_service import JobBoardService, JobData
from ..services.llm_provider_service import get_llm_client
from ..services.search.rag_service import RAGService
from ..utils import get_supabase_client

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
async def promote_lead_to_vendor(lead_id: str, request: PromoteLeadRequest):
    """
    Promote a Lead to a Vendor.
    """
    try:
        supabase = get_supabase_client()

        # 1. Create Vendor
        vendor_data = {
            "name": request.vendor_name,
            "contact_email": request.contact_email,
            "description": request.notes or "Promoted from 104 Lead",
            "status": "active"
        }
        vendor_res = supabase.table("vendors").insert(vendor_data).execute()

        if not vendor_res.data:
            raise Exception("Failed to create vendor record")

        # 2. Update Lead Status
        supabase.table("leads").update({
            "status": "converted",
            "contact_email": request.contact_email
        }).eq("id", lead_id).execute()

        return {"success": True, "vendor": vendor_res.data[0]}
    except Exception as e:
        logfire.error(f"API: Lead promotion failed | id={lead_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/generate-pitch", response_model=PitchResponse)
async def generate_pitch(request: PitchRequest):
    """
    Generate a tailored sales pitch using RAG to find relevant case studies.
    """
    try:
        logfire.info(f"API: Generating pitch | company={request.company} | title={request.job_title}")

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

        system_prompt = """You are a top-tier Sales Representative for Archon, an AI & Data consultancy.
Your goal is to write a personalized, professional, and compelling email pitch to a hiring manager.
Structure: 1. Hook, 2. Value Prop (reference case study), 3. CTA."""

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
        # Initialize the existing tool logic
        tool = GenerateBrandAssetTool(style=request.style)
        svg_content = await tool.execute()

        return LogoResponse(svg_content=svg_content, style=request.style)
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
        # Fetch needs to analyze common keywords
        response = supabase.table("leads").select("identified_need").execute()

        needs = [item.get("identified_need", "") for item in response.data]
        # Simple frequency count (In real app, we might use a dedicated stats table)
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
    Note: Requires 'status' column in 'blog_posts' table.
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
    Get all items requiring approval (currently Blog Posts in 'review').
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("blog_posts").select("*").eq("status", "review").execute()

        # In the future, we can merge with Leads requiring approval
        return {
            "blogs": response.data,
            "leads": []
        }
    except Exception as e:
        logfire.error(f"API: Failed to fetch approvals | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/approvals/{item_type}/{item_id}/{action}")
async def process_approval(item_type: str, item_id: str, action: str):
    """
    Process approval action (approve/reject).
    """
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
