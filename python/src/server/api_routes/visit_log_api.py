import asyncio
import json
from typing import cast

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
    audio_path: str | None = None

class VisitLogResponse(BaseModel):
    id: str
    summary: str
    voice_transcript: str | None
    follow_up_tasks: list[str]

async def _upload_to_google_files_api(
    audio_content: bytes,
    mime_type: str,
    api_key: str,
    filename: str = "visit_audio.webm"
) -> str:
    """
    Uploads audio content to Google Generative AI Files API.
    Handles the metadata + binary multipart flow and waits for ACTIVE state.
    """
    upload_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}"

    metadata = {"file": {"display_name": filename}}
    boundary = "boundary_archon_voice"

    body = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode() + audio_content + f"\r\n--{boundary}--\r\n".encode()

    headers = {
        "X-Goog-Upload-Protocol": "multipart",
        "Content-Type": f"multipart/related; boundary={boundary}"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(upload_url, content=body, headers=headers, timeout=60.0)
        if resp.status_code != 200:
            logger.error(f"Google Files API Upload Error ({resp.status_code}): {resp.text}")
            raise Exception(f"Google API 上傳失敗: {resp.status_code}")

        data = resp.json()
        file_resource_name = data.get("file", {}).get("name")
        file_uri = data.get("file", {}).get("uri")

        if not file_resource_name or not file_uri:
            raise Exception("Google API 未回傳有效的檔案標識")

        # Polling for ACTIVE state
        check_url = f"https://generativelanguage.googleapis.com/v1beta/{file_resource_name}?key={api_key}"
        for _attempt in range(10):
            check_resp = await client.get(check_url)
            if check_resp.status_code == 200:
                state = check_resp.json().get("state")
                if state == "ACTIVE":
                    return cast(str, file_uri)
                elif state == "FAILED":
                    raise Exception("Google API 檔案處理失敗 (FAILED)")
            await asyncio.sleep(2)

        raise Exception("Google API 檔案處理逾時")

async def _transcribe_with_gemini(
    audio_content: bytes,
    mime_type: str,
    api_key: str,
    model: str = "gemini-2.0-flash-lite-preview-02-05"
) -> tuple[str, str, list[str]]:
    """
    Interact with Gemini Multimodal API for voice processing with robust error handling.
    """
    try:
        file_uri = await _upload_to_google_files_api(audio_content, mime_type, api_key)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        prompt_text = (
            "你是一位專業的業務助理。請執行以下任務：\n"
            "1. 準確地將這段銷售拜訪錄音轉錄為繁體中文逐字稿。\n"
            "2. 總結關鍵對話內容。\n"
            "3. 提取所有需要跟進的具體任務清單。\n"
            "請以 JSON 格式回傳，包含以下鍵值：'transcript', 'summary', 'tasks' (字串清單)。"
        )

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt_text},
                    {"file_data": {"mime_type": mime_type, "file_uri": file_uri}}
                ]
            }],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=120.0)

            if resp.status_code == 429:
                return "[系統提示：API 額度暫時不足]", "額度限制 (429)", []

            if resp.status_code != 200:
                logger.error(f"Gemini API Error ({resp.status_code}): {resp.text}")
                return f"[處理音訊錯誤: {resp.status_code}]", "AI 處理失敗", []

            data = resp.json()
            try:
                raw_json = data["candidates"][0]["content"]["parts"][0]["text"]
                result = json.loads(raw_json)
                return (
                    result.get("transcript", ""),
                    result.get("summary", "音訊處理完成。"),
                    result.get("tasks", [])
                )
            except (KeyError, IndexError, json.JSONDecodeError) as parse_error:
                logger.error(f"Failed to parse Gemini JSON: {parse_error}. Raw: {data}")
                return "[AI 回應解析失敗]", "解析失敗", []

    except Exception as e:
        logger.error(f"Gemini API 例外: {e}")
        error_msg = str(e)
        if "429" in error_msg:
            return "[系統提示：API 額度不足]", "額度限制", []
        return f"[系統錯誤: {error_msg}]", "系統異常", []

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
    """
    user_id = current_user.get("id")
    logger.info(f"API: Creating visit log | user={current_user.get('email')} | has_audio={audio_file is not None}")

    try:
        supabase = get_supabase_client()
        transcript = ""
        summary = "No audio provided."
        tasks: list[str] = []

        if audio_file:
            from ..services.credential_service import credential_service
            audio_model = "gemini-2.0-flash-lite-preview-02-05"

            try:
                settings = await credential_service.get_credentials_by_category("rag_strategy")
                db_model = settings.get("AUDIO_MODEL")
                if db_model:
                     audio_model = db_model
            except Exception as e:
                logger.warning(f"Failed to fetch AUDIO_MODEL from settings: {e}")

            config = await credential_service.get_active_provider("llm")
            api_key = None
            if config and config.get("provider") == "google":
                api_key = config.get("api_key")

            if not api_key:
                import os
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

            if not api_key:
                 logger.warning("No Gemini API key found.")
                 transcript = "[錯誤：未設定 Gemini API 金鑰]"
            else:
                audio_content = await audio_file.read()
                mime_type = audio_file.content_type or "audio/webm"
                transcript, summary, tasks = await _transcribe_with_gemini(
                    audio_content, mime_type, api_key, audio_model
                )

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

        # GAP-009: Voice-to-Task
        try:
            from ..services.projects.task_service import task_service
            field_ops_project_id = None
            proj_res = supabase.table("archon_projects").select("id").eq("title", "Field Ops").limit(1).execute()

            if proj_res.data:
                field_ops_project_id = proj_res.data[0]["id"]
            else:
                fallback_res = supabase.table("archon_projects").select("id").limit(1).execute()
                if fallback_res.data:
                    field_ops_project_id = fallback_res.data[0]["id"]

            if field_ops_project_id:
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
                task_desc = f"**逐字稿:**\n{transcript}\n\n**AI 摘要:**\n{summary}\n\n**位置:** {location_address or f'{latitude}, {longitude}' if latitude else '未知'}\n\n[系統自動生成語音日誌]"

                await task_service.create_task(
                    project_id=field_ops_project_id,
                    title=task_title,
                    description=task_desc,
                    assignee_id=user_id,
                )
        except Exception as task_err:
            logger.error(f"GAP-009 Error: {task_err}")

        return VisitLogResponse(
            id=created_log["id"],
            summary=created_log["summary"],
            voice_transcript=created_log["voice_transcript"],
            follow_up_tasks=created_log["follow_up_tasks"] or []
        )

    except Exception as e:
        logger.error(f"API Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/user/{user_id}", response_model=list[VisitLogResponse])
async def get_user_visit_logs(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and current_user.get("role") not in ["admin", "manager"]:
         raise HTTPException(status_code=403, detail="Forbidden")

    try:
        supabase = get_supabase_client()
        res = supabase.table("visit_logs").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return [VisitLogResponse(
            id=i["id"], summary=i.get("summary", ""),
            voice_transcript=i.get("voice_transcript", ""),
            follow_up_tasks=i.get("follow_up_tasks", [])
        ) for i in res.data]
    except Exception as e:
        logger.error(f"Fetch Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
