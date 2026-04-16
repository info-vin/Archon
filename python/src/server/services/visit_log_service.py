import json
from typing import Any

from src.server.config.logfire_config import get_logger
from src.server.repositories.base_repository import BaseRepository
from src.server.utils import get_supabase_client

logger = get_logger(__name__)

class VisitLogService(BaseRepository):
    """
    Visit Log Service - Business logic for tracking customer interactions.
    Restored with Voice-to-Task (GAP-009) and aligned with 0413 SDK patterns.
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
        Processes audio using official google-genai SDK (Phase 4.6.39 pattern).
        Returns: (transcript, summary, tasks)
        """
        try:
            from google import genai
            from google.genai import types

            from src.server.services.credential_service import credential_service
            from src.server.services.prompt_service import prompt_service

            # 1. Get Credentials
            api_key = await credential_service.get_credential("GEMINI_API_KEY")
            if not api_key:
                logger.error("VisitLogService: GEMINI_API_KEY missing.")
                return "[Error: API Key Missing]", "AI processing failed.", []

            rag_strategy = await credential_service.get_credentials_by_category("rag_strategy")
            model_name = (rag_strategy.get("AUDIO_MODEL") or "gemini-2.0-flash").split("/")[-1]

            client = genai.Client(api_key=api_key)

            # 2. Upload to Files API
            # Note: For small field audio, we can pass bytes directly or use the Files API.
            # Aligned with 7a92a7d preference for stable Files API handling.

            # Using a simplified Bytes upload for faster execution if supported,
            # otherwise fallback to Files API pattern if latency allows.
            sys_prompt = prompt_service.get_prompt("VOICE_TRANSCRIPTION", (
                "你是一位專業的業務助理。請準確地將拜訪錄音轉錄為繁體中文逐字稿，"
                "總結關鍵對話內容，並提取跟進任務。回傳格式為 JSON: "
                "{'transcript': '...', 'summary': '...', 'tasks': ['...']}"
            ))

            contents = [
                sys_prompt,
                types.Part.from_bytes(data=audio_content, mime_type=mime_type)
            ]

            response = await client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )

            result = json.loads(response.text)
            return (
                result.get("transcript", ""),
                result.get("summary", "音訊處理完成。"),
                result.get("tasks", [])
            )
        except Exception as e:
            logger.error(f"VisitLogService: AI processing crashed: {e}")
            return f"[AI Error: {e}]", "System error during transcription.", []

    async def create_log(self, data: dict, audio_file: Any = None) -> tuple[bool, Any]:
        """
        Creates a visit log and automatically triggers Task Generation (GAP-009).
        """
        transcript = ""
        summary = data.get("summary", "No audio provided.")
        tasks: list[str] = []

        if audio_file:
            logger.info("VisitLogService: Processing audio file...")
            audio_content = await audio_file.read()
            mime_type = audio_file.content_type or "audio/webm"
            transcript, summary, tasks = await self._process_voice_with_ai(audio_content, mime_type)

        # 1. Insert Visit Log
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

        # res is typically a list from Supabase PostgREST
        created_log = res[0] if isinstance(res, list) and len(res) > 0 else res
        visit_id = created_log.get("id")

        # 2. Automated Task Dispatch (The "Lost" Logic from 7a92a7d)
        try:
            from src.server.services.projects.task_service import task_service

            # Find Field Ops project
            proj_res = self.supabase_client.table("archon_projects").select("id").eq("title", "Field Ops").limit(1).execute()
            project_id = proj_res.data[0]["id"] if proj_res.data else None

            if not project_id:
                # Fallback to any active project
                fallback = self.supabase_client.table("archon_projects").select("id").limit(1).execute()
                project_id = fallback.data[0]["id"] if fallback.data else None

            if project_id and visit_id:
                entity_name = data.get("company_name") or "客戶"
                task_title = f"[Field Ops] 追蹤: {entity_name} - {summary[:30]}..."
                task_desc = (
                    f"**由語音日誌自動產生**\n\n"
                    f"**逐字稿:**\n{transcript}\n\n"
                    f"**AI 摘要:**\n{summary}\n\n"
                    f"**拜訪地點:** {log_payload['location_address'] or '未提供'}"
                )

                await task_service.create_task(
                    project_id=project_id,
                    title=task_title,
                    description=task_desc,
                    assignee_id=data.get("user_id"),
                    sources=[{"type": "visit_log", "id": str(visit_id)}]
                )
                logger.info(f"VisitLogService: Successfully dispatched auto-task for log {visit_id}")
        except Exception as task_err:
            logger.error(f"VisitLogService: Auto-task dispatch failed: {task_err}")

        return True, created_log

    async def get_attendance_status(self, user_id: str) -> tuple[bool, Any]:
        """Fetches the current attendance status for a user."""
        def _query():
            return (
                self.supabase_client.table("attendance_logs")
                .select("*")
                .eq("user_id", user_id)
                .order("clock_in_time", desc=True)
                .limit(1)
                .execute()
            )

        success, res = self.execute_query(_query, "Failed to fetch attendance status")
        if not success or not res:
            return True, {"status": "OFF_WORK", "clock_in_time": None}

        data: list[Any] = res if isinstance(res, list) else []
        return True, data[0] if len(data) > 0 else {"status": "OFF_WORK", "clock_in_time": None}

# Singleton export
visit_log_service = VisitLogService()
