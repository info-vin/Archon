
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..config.logfire_config import get_logger, logfire
from ..services.credential_service import credential_service
from ..services.job_board_service import JobBoardService, JobData
from ..services.llm_provider_service import get_llm_client
from ..services.search.rag_service import RAGService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/marketing", tags=["marketing"])

class PitchRequest(BaseModel):
    job_title: str
    company: str
    description: str

class PitchResponse(BaseModel):
    content: str
    references: list[str]

@router.get("/jobs", response_model=list[JobData])
async def search_jobs(keyword: str = Query(..., min_length=1), limit: int = 10):
    """
    Search for jobs and automatically identify/save potential leads.
    """
    try:
        logfire.info(f"API: Searching jobs | keyword={keyword}")
        jobs = await JobBoardService.search_jobs(keyword, limit)

        # Auto-save leads asynchronously (fire and forget logic could be used, but await is safer for now)
        new_leads = await JobBoardService.identify_leads_and_save(jobs)
        logfire.info(f"API: Auto-saved leads | count={new_leads}")

        return jobs
    except Exception as e:
        logfire.error(f"API: Job search failed | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e

@router.post("/generate-pitch", response_model=PitchResponse)
async def generate_pitch(request: PitchRequest):
    """
    Generate a tailored sales pitch using RAG to find relevant case studies.
    """
    try:
        logfire.info(f"API: Generating pitch | company={request.company} | title={request.job_title}")

        # 1. RAG Search: Find relevant case studies or capabilities based on the job description
        # We combine title and description for better context
        search_query = f"{request.job_title} {request.description[:500]}"
        rag_service = RAGService()

        # Search specifically in 'case_studies' or generic documents
        # For now, we search everything as 'source' filtering might be too restrictive if data isn't tagged perfectly
        success, search_result = await rag_service.perform_rag_query(query=search_query, match_count=3)

        context_text = ""
        references = []

        if success and "results" in search_result:
            for res in search_result["results"]:
                # Safely access metadata
                meta = res.get("metadata", {})
                source = meta.get("source", "Unknown Source")
                content = res.get("content", "").strip()

                context_text += f"\n[Source: {source}]\n{content}\n"
                references.append(source)

        if not context_text:
            context_text = "No specific case studies found. Use general Archon capabilities: AI automation, data analytics, and efficiency improvement."

        # 2. LLM Generation
        # Get active provider configuration to respect system settings (e.g. Gemini)
        provider_config = await credential_service.get_active_provider("llm")
        model_name = provider_config.get("chat_model") or "gpt-4o" # Fallback if not set

        system_prompt = """You are a top-tier Sales Representative for Archon, an AI & Data consultancy.
Your goal is to write a personalized, professional, and compelling email pitch to a hiring manager.
Use the provided Context (Case Studies/Capabilities) to prove we can solve their likely problems.

Structure:
1. Hook: Mention their hiring need (Job Title) and infer a challenge they might be facing.
2. Value Proposition: Briefly explain how Archon solves this, referencing a specific Case Study from the context if relevant.
3. Call to Action: Suggest a brief chat.

Tone: Professional, confident, yet helpful. NOT salesy or aggressive. Keep it under 200 words."""

        user_prompt = f"""
Target Company: {request.company}
Hiring For: {request.job_title}
Job Snippet: {request.description[:300]}...

Context / Relevant Case Studies:
{context_text}

Draft the email content (Subject line included).
"""

        async with get_llm_client() as client:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )

            content = response.choices[0].message.content

        return PitchResponse(content=content, references=references)

    except Exception as e:
        logfire.error(f"API: Pitch generation failed | error={str(e)}")
        # Fallback for demo purposes if LLM fails (e.g. no API key)
        if "API key" in str(e) or "not found" in str(e):
             return PitchResponse(
                 content=f"Subject: Collaboration regarding {request.job_title}\n\n(System Note: Real LLM generation failed due to missing configuration. Please check Admin Settings.)\n\nDear Hiring Manager at {request.company}...",
                 references=["System Fallback"]
             )
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e
