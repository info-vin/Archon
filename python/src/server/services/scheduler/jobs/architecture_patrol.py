"""
Architecture Patrol for Scheduler
Handles weekly scans of backend architecture health and type coverage.
"""

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)

async def run_architecture_health_audit() -> None:
    """Scans the backend codebase for type coverage and monolith files, generating a markdown task."""
    logger.info("🏛️ Clockwork: Starting Architecture Health Audit...")
    try:
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service
        from src.server.services.shared_constants import AI_AGENT_ROLES
        from src.server.utils import get_supabase_client

        # Multi-path detection (Host vs Docker)
        possible_roots = [
            Path("/app"),  # Docker
            Path.cwd(),    # Host (Archon root)
            Path.cwd().parent, # Host (Archon/python root)
        ]

        project_root = Path("/app")
        for root in possible_roots:
            if (root / "scripts" / "backend_type_health.py").exists():
                project_root = root
                break

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

        from src.server.repositories.base_repository import BaseRepository
        base_repo = BaseRepository(supabase)
        success, p_res_dict = base_repo.execute_query(
            supabase.table("archon_projects").select("id").limit(1),
            "Failed to find project for architecture health task"
        )
        if not success or not p_res_dict.get("data"):
            logger.warning("Clockwork: No projects found to attach architecture health task.")
            return

        project_id = p_res_dict["data"][0]["id"]

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
