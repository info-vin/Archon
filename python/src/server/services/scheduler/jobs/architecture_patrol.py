"""
Architecture Patrol for Scheduler
Handles weekly scans of backend architecture health and type coverage.
"""

import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)

async def run_architecture_health_audit() -> None:
    """Scans the backend codebase for type coverage and monolith files, generating a markdown task."""
    logger.info("🏛️ Clockwork: Starting Architecture Health Audit...")
    try:
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service
        from src.server.services.scheduler.utils import get_default_project_id, resolve_project_root
        from src.server.services.shared_constants import AI_AGENT_ROLES
        from src.server.utils import get_supabase_client

        project_root = resolve_project_root("scripts/backend_type_health.py")

        scripts_dir = str(project_root / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        try:
            from backend_type_health import generate_health_report_markdown
            markdown_content = generate_health_report_markdown()
        except ImportError as e:
            logger.error(f"Could not import backend_type_health: {e}")
            return

        cst = ZoneInfo("Asia/Taipei")
        task_title = f"[Weekly] Architecture Health Audit ({datetime.now(cst).strftime('%Y-%m-%d')})"
        task_desc = (
            "本週後端架構健康度與型別覆蓋率掃描報告已出爐，請審閱：\n\n"
            f"{markdown_content}"
        )

        supabase = get_supabase_client()
        project_id = get_default_project_id(supabase, "Failed to find project for architecture health task")
        if not project_id:
            logger.warning("Clockwork: No projects found to attach architecture health task.")
            return

        success, task_result = await task_service.create_task(
            project_id=project_id,
            title=task_title,
            description=task_desc,
            assignee_id=AI_AGENT_ROLES.get("DevBot (Engineering)") or "ai-dev-bot",
        )

        if success:
            logger.info(f"🏛️ Clockwork: Created Architecture Health task {task_result['task']['id']}.")
            await agent_service.run_agent_task(
                task_id=task_result["task"]["id"], agent_id=task_result["task"]["assignee_id"]
            )

    except Exception as e:
        logger.error(f"💥 Clockwork: Architecture Health Audit Failed: {e}", exc_info=True)
