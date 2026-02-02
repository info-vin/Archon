
import base64
import json

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
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

async def _transcribe_with_gemini(
    audio_content: bytes,
    mime_type: str,
    api_key: str,
    model: str = "gemini-1.5-flash"
) -> tuple[str, str, list[str]]:
    """
    Helper to interact with Google Gemini Multimodal API for audio processing.
    Returns: (transcript, summary, tasks)
    """
    try:
        base64_audio = base64.b64encode(audio_content).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        prompt_text = (
            "You are an expert Sales Assistant. "
            "1. Transcribe the following sales visit audio accurately. "
            "2. Summarize the key points. "
            "3. Extract a list of follow-up tasks. "
            "Return JSON with keys: 'transcript', 'summary', 'tasks' (list of strings)."
        )

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt_text},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64_audio
                        }
                    }
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=60.0)

            if resp.status_code != 200:
                logger.error(f"Gemini API Error: {resp.text}")
                return f"[Error processing audio: {resp.status_code}]", "Processing failed.", []

            data = resp.json()
            try:
                # Gemini 1.5 returns text in candidates[0].content.parts[0].text
                raw_json = data["candidates"][0]["content"]["parts"][0]["text"]
                result = json.loads(raw_json)

                return (
                    result.get("transcript", ""),
                    result.get("summary", "Audio processed."),
                    result.get("tasks", [])
                )
            except (KeyError, IndexError, json.JSONDecodeError) as parse_error:
                logger.error(f"Failed to parse Gemini JSON: {parse_error}. Raw: {data}")
                return "[Error parsing AI response]", "Parsing failed.", []

    except Exception as e:
        logger.error(f"Gemini API Request exception: {e}")
        return f"[Error: {str(e)}]", "System error.", []

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
    logger.info(f"API: Creating visit log | user={current_user.get('email')} | has_audio={audio_file is not None}")

    try:
        supabase = get_supabase_client()
        transcript = ""
        summary = "No audio provided."
        tasks: list[str] = []

        # 1. Process Audio with Gemini 1.5 Flash (Multimodal)
        if audio_file:
            logger.info("Processing audio file with Gemini 1.5 Flash...")

            # Get Audio Model Config
            from ..services.credential_service import credential_service
            audio_model = "gemini-1.5-flash"

            try:
                settings = await credential_service.get_credentials_by_category("rag_strategy")
                db_model = settings.get("AUDIO_MODEL")
                if db_model:
                     audio_model = db_model
            except Exception as e:
                logger.warning(f"Failed to fetch AUDIO_MODEL from settings, using default: {e}")

            # Get Google API Key
            config = await credential_service.get_active_provider("llm")
            api_key = None
            if config and config.get("provider") == "google":
                api_key = config.get("api_key")

            if not api_key:
                import os
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

            if not api_key:
                 logger.warning("No Google/Gemini API key found for audio processing. Skipping.")
                 transcript = "[Error: No Gemini API Key found]"
            else:
                # Read and Process
                audio_content = await audio_file.read()
                mime_type = audio_file.content_type or "audio/webm"

                transcript, summary, tasks = await _transcribe_with_gemini(
                    audio_content, mime_type, api_key, audio_model
                )

        # 2. Save to DB
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

        # 3. GAP-009: Voice-to-Task Integration
        try:
            from ..services.projects.task_service import task_service

            # Find 'Field Ops' project
            field_ops_project_id = None
            proj_res = supabase.table("archon_projects").select("id").eq("title", "Field Ops").limit(1).execute()

            if proj_res.data:
                field_ops_project_id = proj_res.data[0]["id"]
            else:
                # Fallback
                fallback_res = supabase.table("archon_projects").select("id").limit(1).execute()
                if fallback_res.data:
                    field_ops_project_id = fallback_res.data[0]["id"]
                    logger.warning("GAP-009: 'Field Ops' project not found. Using fallback project.")

            if field_ops_project_id:
                # Resolve Entity Name for better Title
                entity_name = "Unknown Client"
                if customer_id:
                    c_res = supabase.table("vendors").select("name").eq("id", customer_id).limit(1).execute()
                    if c_res.data:
                        entity_name = c_res.data[0]["name"]
                elif lead_id:
                    l_res = supabase.table("leads").select("company_name").eq("id", lead_id).limit(1).execute()
                    if l_res.data:
                        entity_name = l_res.data[0]["company_name"]

                task_title = f"[Field Ops] 客戶: {entity_name} - {summary[:30]}..." if summary else f"[Field Ops] 筆記: {entity_name}"
                task_desc = f"**Transcript:**\n{transcript}\n\n**AI Summary:**\n{summary}\n\n**Location:** {location_address or f'{latitude}, {longitude}' if latitude else 'Unknown'}\n\n[System Generated from Voice Log]"

                await task_service.create_task(
                    project_id=field_ops_project_id,
                    title=task_title,
                    description=task_desc,
                    # status="todo", # Removed: TaskService defaults to 'todo' and doesn't accept this arg
                    assignee_id=user_id,
                )
                logger.info(f"GAP-009: Automatically created task for visit log {created_log['id']}")

        except Exception as task_err:
            logger.error(f"GAP-009: Voice-to-Task failed: {task_err}")

        return VisitLogResponse(
            id=created_log["id"],
            summary=created_log["summary"],
            voice_transcript=created_log["voice_transcript"],
            follow_up_tasks=created_log["follow_up_tasks"] or []
        )

    except Exception as e:
        logger.error(f"API: Visit log creation failed | error={str(e)}")
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
        logger.error(f"API: Fetch visit logs failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
