import asyncio
import json
import os
from typing import cast

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
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

async def _list_available_models(api_key: str):
    """Diagnostic tool to stop guessing and see what models are actually available."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                logger.info(f"Available Google Models for this key: {models}")
                return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
    return []

async def _upload_to_google_files_api(
    audio_content: bytes,
    mime_type: str,
    api_key: str,
    filename: str = "visit_audio.mp3"
) -> str:
    """Uploads audio to Google Files API and ensures it is ACTIVE."""
    # Map common mobile audio formats to Google-compatible MIME types
    if "mpeg" in mime_type or "mp3" in mime_type:
        mime_type = "audio/mpeg"
    elif "m4a" in mime_type or "x-m4a" in mime_type:
        mime_type = "audio/mp4"
    elif "wav" in mime_type:
        mime_type = "audio/wav"

    upload_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}"
    boundary = "boundary_archon_voice"
    metadata = {"file": {"display_name": filename}}

    body = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\nContent-Type: {mime_type}\r\n\r\n"
    ).encode() + audio_content + f"\r\n--{boundary}--\r\n".encode()

    headers = {
        "X-Goog-Upload-Protocol": "multipart",
        "Content-Type": f"multipart/related; boundary={boundary}"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(upload_url, content=body, headers=headers, timeout=60.0)
        if resp.status_code != 200:
            raise Exception(f"Upload Failed: {resp.status_code}")

        data = resp.json()
        file_name = data.get("file", {}).get("name")
        file_uri = data.get("file", {}).get("uri")

        check_url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={api_key}"
        for _ in range(10):
            await asyncio.sleep(2)
            chk = await client.get(check_url)
            if chk.status_code == 200 and chk.json().get("state") == "ACTIVE":
                return cast(str, file_uri)
        return cast(str, file_uri)

async def _transcribe_with_gemini(
    audio_content: bytes,
    mime_type: str,
    api_key: str,
    model: str = "gemini-2.5-flash"
) -> tuple[str, str, list[str]]:
    """Transcribes audio using the high-performance Gemini 2.5 model."""
    # Model Name Calibration (Feb 2026 Resilience)
    # Use split()[-1] to ensure we only have the final model ID
    # This is critical for Google REST API paths like /v1beta/models/{safe_model}:generateContent
    safe_model = model.split("/")[-1]

    try:
        file_uri = await _upload_to_google_files_api(audio_content, mime_type, api_key)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{safe_model}:generateContent?key={api_key}"

        # Get Prompt from DB (via PromptService) or fallback
        try:
            from ..services.prompt_service import prompt_service
            prompt_data = prompt_service.get_prompt("VOICE_TRANSCRIPTION_PROMPT")
            prompt = prompt_data if prompt_data else (
                "你是一位專業的業務助理。請準確地將這段銷售拜訪錄音轉錄為繁體中文逐字稿，"
                "並總結關鍵點及提取具體任務。請嚴格以 JSON 格式回傳，"
                "包含鍵值：'transcript', 'summary', 'tasks' (字串清單)。"
            )
        except Exception:
            prompt = (
                "你是一位專業的業務助理。請準確地將這段銷售拜訪錄音轉錄為繁體中文逐字稿，"
                "並總結關鍵點及提取具體任務。請嚴格以 JSON 格式回傳，"
                "包含鍵值：'transcript', 'summary', 'tasks' (字串清單)。"
            )

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"file_data": {"mime_type": "audio/mpeg" if "mp3" in mime_type else mime_type, "file_uri": file_uri}}
                ]
            }],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=120.0)

            if resp.status_code == 404:
                available = await _list_available_models(api_key)
                # BROADCAST TO CHARLIE
                try:
                    get_supabase_client().table("archon_logs").insert({
                        "level": "ALERT", "source": "VoiceBot", "type": "system",
                        "message": f"Voice Model Not Found (404): {safe_model}",
                        "details": {"model": safe_model, "available": available[:5]}
                    }).execute()
                except Exception:
                    pass
                return f"[錯誤 404: 可用模型: {available[:3]}]", "模型配置錯誤", []

            if resp.status_code == 429:
                # BROADCAST TO CHARLIE
                try:
                    get_supabase_client().table("archon_logs").insert({
                        "level": "ALERT", "source": "VoiceBot", "type": "system",
                        "message": "Voice API Rate Limit (429)",
                        "details": {"model": safe_model}
                    }).execute()
                except Exception:
                    pass
                return "[系統提示：API 額度暫時不足]", "額度限制 (429)", []

            if resp.status_code != 200:
                return f"[處理錯誤 {resp.status_code}]", "AI 處理失敗", []

            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            res_json = safe_json_loads(raw_text)
            return res_json.get("transcript", ""), res_json.get("summary", ""), res_json.get("tasks", [])

    except Exception as e:
        logger.error(f"Voice pipeline error: {e}")
        # BROADCAST TO CHARLIE
        try:
            get_supabase_client().table("archon_logs").insert({
                "level": "ALERT", "source": "VoiceBot", "type": "system",
                "message": f"Voice Pipeline Exception: {str(e)[:100]}",
                "details": {"error": str(e), "model": safe_model}
            }).execute()
        except Exception:
            pass
        return str(e), "發生異常", []

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
