
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger, logfire
from ..services.llm_provider_service import get_llm_client
from ..utils import get_supabase_client

logger = get_logger(__name__)

router = APIRouter(prefix="/api/visit-logs", tags=["visit-logs"])

class VisitLogCreate(BaseModel):
    customer_id: str | None = None
    lead_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_address: str | None = None
    audio_path: str | None = None # Path if uploaded beforehand, or handle file upload directly

class VisitLogResponse(BaseModel):
    id: str
    summary: str
    voice_transcript: str | None
    follow_up_tasks: list[str]

@router.post("/", response_model=VisitLogResponse)
async def create_visit_log(
    customer_id: str | None = Form(None),
    lead_id: str | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    location_address: str | None = Form(None),
    audio_file: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a visit log from a voice recording (Mobile Ops).
    Uses Gemini Multimodal to transcribe and summarize.
    """
    user_id = current_user.get("id")
    logfire.info(f"API: Creating visit log | user={current_user.get('email')} | has_audio={audio_file is not None}")

    try:
        supabase = get_supabase_client()
        transcript = ""
        summary = "No audio provided."
        tasks = []

        # 1. Process Audio with Gemini (Mock for now or Real if Key exists)
        if audio_file:
            # TODO(Phase 4.6): Implement actual Gemini 1.5 Flash Audio Processing
            # For now, we simulate a transcript based on file name or dummy content
            transcript = "Customer confirmed interest in the Enterprise plan but wants a 10% discount. Follow up with a quote next Tuesday."

            # 2. Extract Tasks & Summary using LLM
            # (In real impl, we would send audio directly to Gemini 1.5 Flash)
            async with get_llm_client() as client:
                # Simple text extraction for now
                response = await client.chat.completions.create(
                    model="gpt-4o", # Or Gemini-1.5-flash
                    messages=[
                        {"role": "system", "content": "You are a Sales Assistant. Extract a summary and checklist of follow-up tasks from this sales visit transcript. Return JSON: {summary: str, tasks: str[]}"},
                        {"role": "user", "content": transcript}
                    ],
                    response_format={ "type": "json_object" }
                )
                import json
                result = json.loads(response.choices[0].message.content)
                summary = result.get("summary", "Processed visit log.")
                tasks = result.get("tasks", [])

        # 3. Save to DB
        log_data = {
            "user_id": user_id,
            "customer_id": customer_id if customer_id else None,
            "lead_id": lead_id if lead_id else None,
            "latitude": latitude,
            "longitude": longitude,
            "location_address": location_address,
            "voice_transcript": transcript,
            "summary": summary,
            "follow_up_tasks": tasks,
            "created_at": "now()",
            "updated_at": "now()"
        }

        res = supabase.table("visit_logs").insert(log_data).execute()

        if not res.data:
            raise Exception("Database insertion failed")

        created_log = res.data[0]

        return VisitLogResponse(
            id=created_log["id"],
            summary=created_log["summary"],
            voice_transcript=created_log["voice_transcript"],
            follow_up_tasks=created_log["follow_up_tasks"] or []
        )

    except Exception as e:
        logfire.error(f"API: Visit log creation failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/user/{user_id}", response_model=list[VisitLogResponse])
async def get_user_visit_logs(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get visit logs for a specific user.
    """
    # RLS should handle permission, but we add an extra check
    if current_user["id"] != user_id and current_user.get("role") not in ["admin", "manager"]:
         raise HTTPException(status_code=403, detail="Cannot view other users' logs.")

    try:
        supabase = get_supabase_client()
        res = supabase.table("visit_logs").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()

        logs = []
        for item in res.data:
            logs.append(VisitLogResponse(
                id=item["id"],
                summary=item.get("summary", ""),
                voice_transcript=item.get("voice_transcript", ""),
                follow_up_tasks=item.get("follow_up_tasks", [])
            ))
        return logs
    except Exception as e:
        logfire.error(f"API: Fetch visit logs failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
