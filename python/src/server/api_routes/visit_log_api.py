import asyncio
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from google import genai
from google.genai import types
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..utils import get_supabase_client
from ..utils.json_utils import safe_json_loads

logger = get_logger(__name__)

router = APIRouter(prefix="/api/visit-logs", tags=["visit-logs"])

class VisitLogResponse(BaseModel):
    id: str
    summary: str
    voice_transcript: str | None
    follow_up_tasks: list[str]

async def _transcribe_with_gemini(
    audio_content: bytes,
    mime_type: str,
    api_key: str,
    model: str = "gemini-2.5-flash"
) -> tuple[str, str, list[str]]:
    """Transcribes audio using the high-performance Gemini 2.5 model via official SDK."""
    # Model Name Calibration (Feb 2026 Resilience)
    safe_model = model.split("/")[-1]

    try:
        # REALITY CHECK (Feb 2026): Use official GenAI Client for Voice
        # This avoids unstable manual HTTP requests and URL-based API keys
        client = genai.Client(api_key=api_key)

        # 1. Upload using official SDK
        # The SDK handles the multipart encoding and status checking internally
        import io
        audio_io = io.BytesIO(audio_content)

        # Map MIME types for stability
        upload_mime = mime_type
        if "mpeg" in mime_type or "mp3" in mime_type:
            upload_mime = "audio/mpeg"
        elif "m4a" in mime_type or "x-m4a" in mime_type:
            upload_mime = "audio/mp4"

        uploaded_file = client.files.upload(
            file=audio_io,
            config={'mime_type': upload_mime}
        )

        # 2. Wait for processing (Polling state via SDK)
        # Use simple loop as SDK upload is sync by default but file status is async
        for _ in range(10):
            file_status = client.files.get(name=uploaded_file.name)
            if file_status.state.name == "ACTIVE":
                break
            await asyncio.sleep(2)

        # 3. Get Prompt from DB
        try:
            from ..services.prompt_service import prompt_service
            prompt = prompt_service.get_prompt("VOICE_TRANSCRIPTION_PROMPT")
            if not prompt:
                raise ValueError("Prompt not found")
        except Exception:
            prompt = (
                "你是一位專業的業務助理。請準確地將這段銷售拜訪錄音轉錄為繁體中文逐字稿，"
                "並總結關鍵點及提取具體任務。請嚴格以 JSON 格式回傳，"
                "包含鍵值：'transcript', 'summary', 'tasks' (字串清單)。"
            )

        # 4. Generate Content with Multi-modality
        response = client.models.generate_content(
            model=safe_model,
            contents=[
                prompt,
                uploaded_file
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0, # Precision is key for transcription
            )
        )

        raw_text = response.text or ""
        if not raw_text:
            raise ValueError("AI returned empty transcription")

        res_json = safe_json_loads(raw_text)
        return (
            res_json.get("transcript", ""),
            res_json.get("summary", ""),
            res_json.get("tasks", [])
        )

    except Exception as e:
        logger.error(f"Voice pipeline error: {e}")
        # BROADCAST TO CHARLIE (Manager Nexus)
        try:
            get_supabase_client().table("archon_logs").insert({
                "level": "ALERT",
                "source": "VoiceBot",
                "type": "system",
                "message": f"Voice Pipeline Exception: {str(e)[:100]}",
                "details": {"error": str(e), "model": safe_model}
            }).execute()
        except Exception:
            pass

        # CRITICAL: Raise exception to stop Agent retry loops
        raise HTTPException(
            status_code=503,
            detail=f"Voice AI Service Error: {str(e)[:100]}"
        ) from e

@router.post("/", response_model=VisitLogResponse)
async def create_visit_log(
    customer_id: str | None = Form(None), lead_id: str | None = Form(None),
    latitude: float | None = Form(None), longitude: float | None = Form(None),
    location_address: str | None = Form(None), visit_type: str = Form("Client Meeting"),
    audio_file: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id")
    try:
        supabase = get_supabase_client()
        transcript = ""
        summary = "無提供語音。"
        tasks: list[str] = []

        if audio_file:
            from ..services.credential_service import credential_service
            settings = await credential_service.get_credentials_by_category("rag_strategy")
            # Default to the high-performance 2.5 model
            audio_model = settings.get("AUDIO_MODEL", "gemini-2.5-flash")

            config = await credential_service.get_active_provider("llm")
            api_key = config.get("api_key") if config and config.get("provider") == "google" else os.getenv("GEMINI_API_KEY")

            if api_key:
                content = await audio_file.read()
                transcript, summary, tasks = await _transcribe_with_gemini(
                    content, audio_file.content_type or "audio/mpeg", api_key, audio_model
                )

        res = supabase.table("visit_logs").insert({
            "user_id": user_id, "customer_id": customer_id, "lead_id": lead_id,
            "latitude": latitude, "longitude": longitude, "location_address": location_address,
            "visit_type": visit_type,
            "voice_transcript": transcript, "summary": summary, "follow_up_tasks": tasks
        }).execute()
        created_log = res.data[0]

        # GAP-009: Voice-to-Task
        try:
            from ..services.projects.task_service import task_service
            proj = supabase.table("archon_projects").select("id").eq("title", "Field Ops").limit(1).execute()
            p_id = proj.data[0]["id"] if proj.data else None
            if p_id:
                await task_service.create_task(
                    project_id=p_id, title=f"[{visit_type}] 拜訪摘要: {summary[:30]}",
                    description=f"**類型:** {visit_type}\n**逐字稿:**\n{transcript}\n\n**摘要:**\n{summary}", assignee_id=user_id
                )
        except Exception as te:
            logger.warning(f"Task creation skipped: {te}")

        return VisitLogResponse(id=created_log["id"], summary=summary, voice_transcript=transcript, follow_up_tasks=tasks)
    except Exception as e:
        logger.error(f"API Failure: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/user/{user_id}", response_model=list[VisitLogResponse])
async def get_user_visit_logs(user_id: str, current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    res = supabase.table("visit_logs").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return [VisitLogResponse(id=i["id"], summary=i.get("summary", ""), voice_transcript=i.get("voice_transcript", ""), follow_up_tasks=i.get("follow_up_tasks", [])) for i in res.data]

# --- Attendance Endpoints ---

class ClockInRequest(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    location_name: str | None = None
    status: str = "PRESENT"

class AttendanceResponse(BaseModel):
    status: str
    clock_in_time: str | None
    location: str | None

@router.get("/attendance/status", response_model=AttendanceResponse)
async def get_attendance_status(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id")
    supabase = get_supabase_client()

    # Get latest log
    res = supabase.table("attendance_logs")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()

    if not res.data:
        return AttendanceResponse(status="OFF_WORK", clock_in_time=None, location=None)

    latest = res.data[0]
    # If clock_out_time is null, they are currently clocked in
    if latest.get("clock_out_time") is None:
        return AttendanceResponse(
            status=latest.get("status", "PRESENT"),
            clock_in_time=latest.get("clock_in_time"),
            location=latest.get("location_name")
        )

    return AttendanceResponse(status="OFF_WORK", clock_in_time=None, location=None)

@router.post("/attendance/clock-in")
async def clock_in(req: ClockInRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id")
    supabase = get_supabase_client()

    # Check if already clocked in
    existing = supabase.table("attendance_logs")\
        .select("id")\
        .eq("user_id", user_id)\
        .is_("clock_out_time", "null")\
        .execute()

    if existing.data:
        raise HTTPException(status_code=400, detail="Already clocked in")

    supabase.table("attendance_logs").insert({
        "user_id": user_id,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "location_name": req.location_name,
        "status": req.status
    }).execute()
    return {"message": "Clocked in successfully"}

@router.post("/attendance/clock-out")
async def clock_out(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id")
    supabase = get_supabase_client()

    # Find active session
    active = supabase.table("attendance_logs")\
        .select("id")\
        .eq("user_id", user_id)\
        .is_("clock_out_time", "null")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()

    if not active.data:
        raise HTTPException(status_code=400, detail="Not clocked in")

    from datetime import datetime
    now = datetime.now().isoformat()

    supabase.table("attendance_logs")\
        .update({"clock_out_time": now})\
        .eq("id", active.data[0]["id"])\
        .execute()

    return {"message": "Clocked out successfully"}
