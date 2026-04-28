import json
import os
import tempfile
from typing import Any

from google import genai
from google.genai import types

from src.server.config.logfire_config import get_logger
from src.server.config.model_ssot import SYSTEM_MODELS
from src.server.repositories.base_repository import BaseRepository
from src.server.services.credential_service import credential_service
from src.server.services.prompt_service import prompt_service
from src.server.utils import get_supabase_client

logger = get_logger(__name__)

class VisitLogService(BaseRepository):
    """
    Visit Log Service - Business logic for tracking customer interactions.
    Restored with Voice-to-Task (GAP-009) and aligned with 04-27 Hardening.
    """
    def __init__(self, supabase_client=None):
        super().__init__(supabase_client or get_supabase_client())

    async def list_logs(self, lead_id: str | None = None) -> tuple[bool, Any]:
        def _query():
            q = self.supabase_client.table("visit_logs").select("*")
            if lead_id:
                q = q.eq("lead_id", lead_id)
            return q.order("created_at", desc=True).execute()
        return self.execute_query(_query, "Failed to list logs")

    async def _process_voice_with_ai(self, audio_content: bytes, mime_type: str) -> tuple[str, str, list[str]]:
        """
        Processes audio using official google-genai SDK.
        Supports large files via polling (Physical Restoration of Apr 16 stability).
        """
        try:
            api_key = await credential_service.get_credential("GEMINI_API_KEY")
            if not api_key:
                logger.error("VisitLogService: GEMINI_API_KEY missing.")
                return "[Error: API Key Missing]", "AI processing failed.", []

            rag_strategy = await credential_service.get_credentials_by_category("rag_strategy")
            model_name = (rag_strategy.get("AUDIO_MODEL") or SYSTEM_MODELS["DEFAULT_TEXT"]).split("/")[-1]

            client = genai.Client(api_key=api_key)

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(audio_content)
                tmp_path = tmp.name

            try:
                # 1. Industrialized Upload (Supports Alice's 20MB+ field recordings)
                from ..utils.google_storage import GoogleStorageHandler
                file_info = await GoogleStorageHandler.upload_and_wait(
                    client=client,
                    path=tmp_path,
                    display_name="Visit Log Audio"
                )

                sys_prompt = prompt_service.get_prompt("VOICE_TRANSCRIPTION", (
                    "你是一位專業的業務助理。請準確地將拜訪錄音轉錄為繁體中文逐字稿，"
                    "總結關鍵對話內容，並提取跟進任務。回傳格式為 JSON: "
                    "{'transcript': '...', 'summary': '...', 'tasks': ['...']}"
                ))

                logger.info(f"VisitLogService: Realizing GAP-009 using model {model_name}...")
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=[file_info, sys_prompt],
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )

                result = json.loads(response.text)
                return (
                    result.get("transcript", ""),
                    result.get("summary", "音訊處理完成。"),
                    result.get("tasks", [])
                )
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            logger.error(f"VisitLogService: AI processing crashed: {e}")
            return f"[AI Error: {e}]", "System error during transcription.", []

    async def create_log(self, data: dict, audio_file: Any = None) -> tuple[bool, Any]:
        transcript = ""
        summary = data.get("summary", "No audio provided.")
        tasks: list[str] = []

        if audio_file:
            audio_content = await audio_file.read()
            mime_type = audio_file.content_type or "audio/webm"
            transcript, summary, tasks = await self._process_voice_with_ai(audio_content, mime_type)

        log_payload = {
            "user_id": data.get("user_id"),
            "customer_id": data.get("customer_id"),
            "lead_id": data.get("lead_id"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "location_address": data.get("location_address") or data.get("company_name"),
            "voice_transcript": transcript,
            "summary": summary,
            "follow_up_tasks": tasks,
        }

        def _query():
            return self.supabase_client.table("visit_logs").insert(log_payload).execute()

        success, res = self.execute_query(_query, "Failed to create visit log")
        if not success or not res:
            return False, res

        created_log = res[0] if isinstance(res, list) and len(res) > 0 else res

        # Automated Task Dispatch (Phase 4.6.46 Hardened)
        try:
            from src.server.services.projects.task_service import task_service
            proj_res = self.supabase_client.table("archon_projects").select("id").ilike("title", "%Ops%").limit(1).execute()
            project_id = proj_res.data[0]["id"] if proj_res.data else None

            if project_id and created_log.get("id"):
                entity_name = data.get("company_name") or "客戶"
                task_title = f"[Field Ops] 追蹤: {entity_name} - {summary[:30]}..."
                await task_service.create_task(
                    project_id=project_id,
                    title=task_title,
                    description=f"**逐字稿:**\n{transcript}\n\n**摘要:**\n{summary}",
                    assignee_id=data.get("user_id"),
                    sources=[{"type": "visit_log", "id": str(created_log['id'])}]
                )
        except Exception as task_err:
            logger.error(f"VisitLogService: Auto-task failed: {task_err}")

        return True, created_log

    async def get_attendance_status(self, user_id: str) -> tuple[bool, Any]:
        def _query():
            return self.supabase_client.table("attendance_logs").select("*").eq("user_id", user_id).order("clock_in_time", desc=True).limit(1).execute()
        success, res = self.execute_query(_query, "Failed to fetch status")
        data: list[Any] = res if isinstance(res, list) else []
        return True, data[0] if len(data) > 0 else {"status": "OFF_WORK", "clock_in_time": None}

visit_log_service = VisitLogService()
