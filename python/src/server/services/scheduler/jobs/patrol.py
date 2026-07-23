"""
Patrol Jobs for Scheduler
Handles system health, log monitoring, and cleanup.
"""

import os
from datetime import UTC, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)


async def run_system_probe() -> None:
    """Triggering System Probe via HealthService."""
    logger.info("🤖 Clockwork: Triggering System Probe via HealthService...")
    try:
        from src.server.repositories.base_repository import BaseRepository
        from src.server.services.health_service import HealthService
        from src.server.utils import get_supabase_client

        supabase = get_supabase_client()
        repo = BaseRepository(supabase)
        repo = BaseRepository(supabase)

        health_service = HealthService()
        result = await health_service.check_rag_integrity()

        success = result.get("status") == "healthy"
        log_level = "INFO" if success else "ERROR"
        msg = "System Probe Passed" if success else "System Probe FAILED"

        if success:
            logger.info(f"✅ Clockwork: {msg}")
        else:
            logger.error(f"❌ Clockwork: {msg} | Details: {result.get('details', {})}")

        try:
            repo.execute_query(
                lambda: supabase.table("archon_logs").insert(
                    {"source": "clockwork-scheduler", "level": log_level, "message": msg, "details": result}
                ).execute(),
                "Log system probe"
            )
        except Exception as db_err:
            logger.error(f"❌ Clockwork: Failed to write to archon_logs: {db_err}")
    except Exception as outer_e:
        logger.error(f"💥 Clockwork: System Probe Crashed: {outer_e}")
        try:
            from src.server.utils import get_supabase_client

            error_message = f"System Probe Crashed: {str(outer_e)}"
            error_details = {"error": str(outer_e)}

            BaseRepository(get_supabase_client()).execute_query(
                lambda: get_supabase_client().table("archon_logs").insert(
                    {
                        "source": "clockwork-scheduler",
                        "level": "CRITICAL",
                        "message": error_message,
                        "details": error_details,
                    }
                ).execute(),
                "Log critical failure"
            )
        except Exception as inner_e:
            logger.error(f"Failed to log crash: {inner_e}")


async def run_log_patrol() -> None:
    """Scans logs for errors and dispatches DevBot."""
    logger.info("👮 Clockwork: Starting Log Patrol...")
    try:
        from src.server.repositories.base_repository import BaseRepository
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service
        from src.server.services.shared_constants import AI_AGENT_ROLES
        from src.server.utils import get_supabase_client

        supabase = get_supabase_client()
        repo = BaseRepository(supabase)
        one_hour_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        success, res = repo.execute_query(
            lambda: supabase.table("archon_logs")
            .select("*")
            .eq("level", "ERROR")
            .gt("created_at", one_hour_ago)
            .limit(5)
            .execute(),
            "Fetch error logs"
        )
        errors = res.get("data", []) if success else []
        if not errors:
            logger.info("👮 Clockwork: No recent errors found. All systems nominal.")
            return

        logger.info(f"👮 Clockwork: Detected {len(errors)} errors. Analyzing...")
        error_summary = "\n".join([f"- [{e['source']}] {e['message']}" for e in errors])
        cst = ZoneInfo("Asia/Taipei")
        task_title = f"Auto-Repair: System Errors Detected ({datetime.now(cst).strftime('%H:%M')})"
        fallback_str = (
            "Clockwork detected the following errors in the last hour:\n{error_summary}\n\nPlease analyze and fix."
        )

        from src.server.services.prompt_service import prompt_service
        prompt_template = prompt_service.get_prompt("SYS_ERROR_PATROL_PROMPT", default=fallback_str)
        task_desc = prompt_template.format(error_summary=error_summary)

        success, p_res = repo.execute_query(
            lambda: supabase.table("archon_projects").select("id").limit(1).execute(),
            "Get project ID"
        )
        p_data = p_res.get("data", []) if success else []
        if not p_data:
            logger.warning("Clockwork: No projects found to attach repair task.")
            return
        project_id = p_data[0]["id"]

        success, task_result = await task_service.create_task(
            project_id=project_id,
            title=task_title,
            description=task_desc,
            assignee_id=AI_AGENT_ROLES.get("DevBot (Engineering)") or "ai-dev-bot",
        )

        if success:
            logger.info(f"👮 Clockwork: Created repair task {task_result['task']['id']}. Dispatching DevBot...")

            # Phase 4.6.42: Trigger Cognitive Self-Tuning (Prompt Evolution)
            try:
                from ...system.self_tuning_service import self_tuning_service

                # Pick the first error to tune
                if errors:
                    res = await self_tuning_service.tune_prompt_from_error(str(errors[0]["id"]))
                    if res.get("success"):
                        logger.info(f"🧠 Clockwork: Prompt tuning proposal created: {res.get('proposal_id')}")
            except Exception as tune_err:
                logger.warning(f"🧠 Clockwork: Prompt tuning failed: {tune_err}")

            await agent_service.run_agent_task(
                task_id=task_result["task"]["id"], agent_id=task_result["task"]["assignee_id"]
            )
    except Exception as e:
        logger.error(f"💥 Clockwork: Log Patrol Failed: {e}")


def is_hf_awake() -> bool:
    """
    判斷當前時間是否在 HF 的上線視窗內。
    睡眠區間預設為台灣 20:18 ~ 05:32 (CST)。
    """
    # 取得 CST (UTC+8) 時間
    cst_now = datetime.now(UTC).astimezone(timezone(timedelta(hours=8)))
    current_time = cst_now.time()

    # 從環境變數讀取 (CST HH:MM 格式)
    start_str = os.getenv("HF_SLEEP_START", "20:18")
    end_str = os.getenv("HF_SLEEP_END", "05:32")

    try:
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        sleep_start = time(sh, sm)
        sleep_end = time(eh, em)
    except Exception:
        sleep_start = time(20, 18)
        sleep_end = time(5, 32)

    if sleep_start <= sleep_end:
        if sleep_start <= current_time <= sleep_end:
            return False
    else:
        # Crosses midnight
        if current_time >= sleep_start or current_time <= sleep_end:
            return False

    return True


async def run_model_verification() -> None:
    """Verifies that the system is using the safe Lite model to prevent 429 errors."""
    logger.info("🤖 Clockwork: Running Model Verification...")
    try:
        from src.server.utils import get_supabase_client

        supabase = get_supabase_client()

        if not is_hf_awake():
            logger.info("🤖 Clockwork: HF Sleep Mode active. Skipping verification probe.")
            try:
                from src.server.repositories.base_repository import BaseRepository
                BaseRepository(supabase).execute_query(
                    lambda: supabase.table("archon_logs").insert(
                        {
                            "source": "clockwork-scheduler",
                            "level": "INFO",
                            "message": "Model Verification [Sleep Mode]",
                            "details": {"status": "skipped_due_to_sleep_mode"},
                        }
                    ).execute(),
                    "Log model verification sleep"
                )
            except Exception as db_err:
                logger.error(f"❌ Clockwork: Failed to write to archon_logs: {db_err}")
            return

        from src.server.config.model_ssot import SYSTEM_MODELS

        default_pro = SYSTEM_MODELS.get("DEFAULT_PRO", "")
        default_text = SYSTEM_MODELS.get("DEFAULT_TEXT", "")

        # Check if the models are set to lite versions to bypass 20 RPD limit
        is_safe = "lite" in default_pro and "lite" in default_text
        msg = (
            "Model Verification Passed (Using Lite models)"
            if is_safe
            else "Model Verification WARNING: Potentially using high-quota models"
        )
        log_level = "INFO" if is_safe else "WARNING"

        logger.info(f"{'✅' if is_safe else '⚠️'} Clockwork: {msg}")

        try:
            from src.server.repositories.base_repository import BaseRepository
            BaseRepository(supabase).execute_query(
                lambda: supabase.table("archon_logs").insert(
                    {
                        "source": "clockwork-scheduler",
                        "level": log_level,
                        "message": msg,
                        "details": {"DEFAULT_PRO": default_pro, "DEFAULT_TEXT": default_text},
                    }
                ).execute(),
                "Log model verification result"
            )
        except Exception as db_err:
            logger.error(f"❌ Clockwork: Failed to write to archon_logs: {db_err}")

    except Exception as e:
        logger.error(f"💥 Clockwork: Model Verification Crashed: {e}")
