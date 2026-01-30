
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

        # 1. Process Audio with Gemini 1.5 Flash (Multimodal)
        if audio_file:
            logfire.info("Processing audio file with Gemini 1.5 Flash...")
            
            # Read and encode audio
            audio_content = await audio_file.read()
            import base64
            # Function to determine mime type from filename or header
            mime_type = audio_file.content_type or "audio/webm"
            base64_audio = base64.b64encode(audio_content).decode("utf-8")
            
            # Get Google API Key
            # We bypass llm_provider_service for this specific raw multimodal call because
            # standard OpenAI client wrapper doesn't support 'inline_data' for audio easily.
            from ..services.credential_service import credential_service
            
            # Try to get 'google' provider key first, or fallback to 'rag_strategy' key
            config = await credential_service.get_active_provider("llm")
            api_key = None
            if config and config.get("provider") == "google":
                api_key = config.get("api_key")
            
            if not api_key:
                # Fallback: check if we have a specific Google key in env or settings
                creds = await credential_service.get_credentials_by_category("llm_providers")
                # This is a bit heuristic, assuming 'google' might be there even if not active
                # But let's assume if it's not active, we might fail or use a default env var
                import os
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

            if not api_key:
                 # Last resort: check if 'openai' provider is actually Google (e.g. valid key)
                 # But safer to just warn and skip if no key found.
                 logfire.warning("No Google/Gemini API key found for audio processing. Skipping.")
                 transcript = "[Error: No Gemini API Key found]"
            else:
                try:
                    import httpx
                    
                    # Gemini 1.5 Flash Endpoint
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    
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
                            logfire.error(f"Gemini API Error: {resp.text}")
                            transcript = f"[Error processing audio: {resp.status_code}]"
                        else:
                            data = resp.json()
                            # Parse Gemini Response
                            try:
                                raw_json = data["candidates"][0]["content"]["parts"][0]["text"]
                                import json
                                result = json.loads(raw_json)
                                transcript = result.get("transcript", "")
                                summary = result.get("summary", "Audio processed.")
                                tasks = result.get("tasks", [])
                            except Exception as parse_error:
                                logfire.error(f"Failed to parse Gemini JSON: {parse_error}")
                                transcript = "[Error parsing AI response]"

                except Exception as api_err:
                    logfire.error(f"Gemini API Request failed: {api_err}")
                    transcript = f"[Error: {str(api_err)}]"

        # 3. Save to DB (Combined logic)
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
