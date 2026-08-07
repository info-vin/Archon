import json
import os
import tempfile
from typing import Any, cast

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
    Restored with Voice-to-Task (GAP-009) and aligned with 0413 SDK patterns.
    """

    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client or get_supabase_client())

    async def list_logs(self, lead_id: str | None = None) -> tuple[bool, Any]:
        q = self.supabase_client.table("visit_logs").select("*") # 合法
        if lead_id:
            q = q.eq("lead_id", lead_id)
        query = q.order("created_at", desc=True)

        return self.execute_query(query, "Failed to list logs")

    async def _process_voice_with_ai(self, audio_content: bytes, mime_type: str) -> tuple[str, str, list[str], Any]:
        """
        Processes audio using official google-genai SDK (Phase 4.6.39 pattern).
        Returns: (transcript, summary, tasks, parsed_ai_res)
        """
        try:
            # 1. Get Credentials
            api_key = await credential_service.get_credential("GEMINI_API_KEY")
            if not api_key:
                logger.error("VisitLogService: GEMINI_API_KEY missing.")
                from src.server.schemas.agent_outputs import VoiceProcessResult
                return "[Error: API Key Missing]", "AI processing failed.", [], VoiceProcessResult()

            rag_strategy = await credential_service.get_credentials_by_category("rag_strategy")
            model_name = (rag_strategy.get("AUDIO_MODEL") or SYSTEM_MODELS["DEFAULT_TEXT"]).split("/")[-1]

            client = genai.Client(api_key=api_key)

            # 2. Upload to Files API (Restored Phase 4.6.46: 40c92ce)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(audio_content)
                tmp_path = tmp.name

            try:
                uploaded_file = client.files.upload(file=tmp_path)

                sys_prompt = prompt_service.get_prompt(
                    "VOICE_TRANSCRIPTION",
                    (
                        "你是一位專業的業務助理。請準確地將拜訪錄音轉錄為繁體中文逐字稿，"
                        "總結關鍵對話內容，並提取跟進任務。此外，請分析是否有提及預約下次開會時間或下次預約的意圖。\n"
                        "回傳格式為 JSON:\n"
                        "{\n"
                        "  \"transcript\": \"逐字稿內容...\",\n"
                        "  \"summary\": \"AI摘要...\",\n"
                        "  \"tasks\": [\"任務1\"],\n"
                        "  \"scheduling_intent\": true/false,\n"
                        "  \"requested_date\": \"YYYY-MM-DD 或 null\",\n"
                        "  \"requested_duration_hours\": 1.0,\n"
                        "  \"meeting_topic\": \"會議主題或 null\"\n"
                        "}"
                    ),
                )

                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=cast(Any, [uploaded_file, sys_prompt]),
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            # Clean JSON markdown blocks if present (Fragile JSON Parsing Fix)
            clean_text = cast(str, response.text).strip()
            if clean_text.startswith("```"):
                lines = clean_text.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                clean_text = "\n".join(lines).strip()

            result = json.loads(clean_text)

            # Validate using VoiceProcessResult model (Dead Code / Hallucination Fix)
            from src.server.schemas.agent_outputs import VoiceProcessResult
            parsed_res = VoiceProcessResult.model_validate(result)

            return (
                parsed_res.transcript,
                parsed_res.summary,
                parsed_res.tasks,
                parsed_res
            )
        except Exception as e:
            logger.error(f"VisitLogService: AI processing crashed: {e}")
            from src.server.schemas.agent_outputs import VoiceProcessResult
            return f"[AI Error: {e}]", "System error during transcription.", [], VoiceProcessResult()

    async def create_log(self, data: dict, audio_file: Any = None) -> tuple[bool, Any]:
        """
        Creates a visit log and automatically triggers Task Generation (GAP-009).
        Supports Phase 5.4.6 PydanticAI voice scheduling loop.
        """
        from src.server.schemas.agent_outputs import VoiceProcessResult
        transcript = ""
        summary = data.get("summary", "No audio provided.")
        tasks: list[str] = []
        parsed_ai_res = VoiceProcessResult()

        if audio_file:
            logger.info("VisitLogService: Processing audio file...")
            audio_content = await audio_file.read()
            mime_type = audio_file.content_type or "audio/webm"
            transcript, summary, tasks, parsed_ai_res = await self._process_voice_with_ai(audio_content, mime_type)

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


        success, res = self.execute_query(self.supabase_client.table("visit_logs").insert(log_payload), "Failed to create visit log") # 合法
        if not success or not res:
            return False, res

        created_log = res[0] if isinstance(res, list) and len(res) > 0 else res
        visit_id = created_log.get("id")

        # 2. Automated Task Dispatch / Scheduling Recommendation (Phase 5.4.6)
        try:
            from datetime import datetime

            from src.server.services.agent_registry import get_agent_uuid
            from src.server.services.projects.task_service import task_service

            project_id = None
            proj_res = (
                self.supabase_client.table("archon_projects").select("id").ilike("title", "%Ops%").limit(1).execute() # 合法
            )
            if proj_res.data:
                project_id = proj_res.data[0]["id"]

            if not project_id:
                fallback = self.supabase_client.table("archon_projects").select("id").limit(1).execute() # 合法
                # Empty DB safety: Protect against IndexError (GAP-005 Fix)
                project_id = fallback.data[0]["id"] if fallback.data and len(fallback.data) > 0 else None

            if project_id and visit_id:
                entity_name = data.get("company_name") or "客戶"
                is_meeting = parsed_ai_res.scheduling_intent
                requested_date = parsed_ai_res.requested_date

                if is_meeting and requested_date:
                    # Retrieve Bob & Charlie agent UUIDs
                    bob_id = get_agent_uuid("market-bot")
                    charlie_id = get_agent_uuid("supervisor")

                    # Fallback check for missing Agents (GAP-005 Fix)
                    if not bob_id:
                        logger.warning("VisitLogService: Bob (market-bot) UUID not found in profiles, using default.")
                        bob_id = "00000000-0000-0000-0000-000000000002"
                    if not charlie_id:
                        logger.warning("VisitLogService: Charlie (supervisor) UUID not found in profiles, using default.")
                        charlie_id = "00000000-0000-0000-0000-000000000001"

                    # Invoke availability checker
                    from src.server.services.stats import stats_service
                    slots = await stats_service.get_team_availability([bob_id, charlie_id], requested_date)

                    slot_texts = []
                    for i, slot in enumerate(slots):
                        try:
                            st = datetime.fromisoformat(slot["start_time"])
                            et = datetime.fromisoformat(slot["end_time"])
                            slot_texts.append(f"選項 {chr(65+i)}: {st.strftime('%Y-%m-%d %H:%M')} ~ {et.strftime('%H:%M')} (GMT+8)")
                        except Exception:
                            slot_texts.append(f"選項 {chr(65+i)}: {slot['start_time']} ~ {slot['end_time']}")

                    conflict_summary = (
                        "已為 Bob (MarketBot) 與 Charlie (Supervisor) 排除行程衝突。建議開會時間選項如下：\n" +
                        "\n".join(slot_texts)
                    )

                    topic = parsed_ai_res.meeting_topic or "需求對接討論會"
                    task_title = f"[待確認會議] {entity_name} - {topic}"
                    task_desc = (
                        f"**由語音日誌自動分析排程**\n\n"
                        f"**會議主題:** {topic}\n"
                        f"**預計日期:** {requested_date}\n\n"
                        f"**{conflict_summary}**\n\n"
                        f"**逐字稿:**\n{transcript}\n\n"
                        f"**AI 摘要:**\n{summary}"
                    )

                    # Assign task to Bob, add Charlie as collaborator
                    collabs = [charlie_id]
                    if data.get("user_id"):
                        collabs.append(str(data.get("user_id")))

                    await task_service.create_task(
                        project_id=project_id,
                        title=task_title,
                        description=task_desc,
                        assignee="Archon MarketBot",
                        assignee_id=bob_id,
                        collaborator_agent_ids=collabs,
                        sources=[{"type": "visit_log", "id": str(visit_id)}],
                    )
                    # Expose recommendations in response so frontend can show them immediately
                    created_log["scheduling_recommendation"] = {
                        "meeting_topic": topic,
                        "suggested_slots": slots,
                        "conflict_summary": conflict_summary
                    }
                else:
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
                        sources=[{"type": "visit_log", "id": str(visit_id)}],
                    )
                logger.info(f"VisitLogService: Successfully dispatched task/schedule for log {visit_id}")
        except Exception as task_err:
            logger.error(f"VisitLogService: Auto-task dispatch failed: {task_err}")

        return True, created_log

    async def get_attendance_status(self, user_id: str) -> tuple[bool, Any]:
        """Fetches the current attendance status for a user."""

        query = (
            self.supabase_client.table("attendance_logs") # 合法
            .select("*")
            .eq("user_id", user_id)
            .order("clock_in_time", desc=True)
            .limit(1)
        )

        success, res = self.execute_query(query, "Failed to fetch attendance status")
        if not success or not res:
            return True, {"status": "OFF_WORK", "clock_in_time": None}

        data: list[Any] = res if isinstance(res, list) else []
        return True, data[0] if len(data) > 0 else {"status": "OFF_WORK", "clock_in_time": None}


# Singleton export
visit_log_service = VisitLogService()
