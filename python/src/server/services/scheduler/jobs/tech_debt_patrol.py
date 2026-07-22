"""
Tech Debt Patrol for Scheduler
Handles scanning for stale PRPs, scripts, and other technical debt.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)

async def run_tech_debt_audit():
    """Scans PRPs and scripts for technical debt, and dispatches DevBot if needed."""
    logger.info("🧹 Clockwork: Starting Tech Debt Patrol...")
    try:
        import glob
        import os
        import time
        from pathlib import Path

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
            if (root / "PRPs").exists():
                project_root = root
                break

        warnings = []

        # 1. Check unarchived PRPs
        prp_dir = project_root / "PRPs"
        prp_files = list(prp_dir.glob("Phase_*.md")) if prp_dir.exists() else []
        if len(prp_files) >= 5:
            warnings.append(
                f"PRPs directory is cluttered ({len(prp_files)} unarchived files). Please archive completed phases."
            )

        # 2. Check stale scripts (older than 14 days)
        fourteen_days_ago = time.time() - (14 * 24 * 3600)
        stale_scripts = []

        script_patterns = [
            str(project_root / "scripts" / "*.py"),
            str(project_root / "scripts" / "*.sh"),
            str(project_root / "python" / "scripts" / "*.py")
        ]

        for pattern in script_patterns:
            for filepath in glob.glob(pattern):
                if os.path.isfile(filepath):
                    mtime = os.path.getmtime(filepath)
                    if mtime < fourteen_days_ago:
                        stale_scripts.append(os.path.relpath(filepath, str(project_root)))

        if stale_scripts:
            stale_msg = f"Found {len(stale_scripts)} stale script(s) (no modifications in > 14 days):\n"
            stale_msg += "\n".join([f"- {s}" for s in stale_scripts[:5]])
            if len(stale_scripts) > 5:
                stale_msg += "\n..."
            warnings.append(stale_msg)

        if not warnings:
            logger.info("✅ Clockwork: Tech Debt Patrol found no issues.")
            return

        logger.info("⚠️ Clockwork: Detected Tech Debt. Creating task for DevBot...")

        cst = ZoneInfo("Asia/Taipei")
        task_title = f"Auto-Cleanup: Technical Debt Audit ({datetime.now(cst).strftime('%Y-%m-%d')})"
        task_desc = (
            "Clockwork detected the following technical debt that needs archiving or cleanup:\n\n"
            + "\n\n".join(warnings)
            + "\n\nPlease review and clean up the workspace."
        )

        supabase = get_supabase_client()
        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if not p_res.data:
            logger.warning("Clockwork: No projects found to attach tech debt task.")
            return

        project_id = p_res.data[0]["id"]

        success, task_result = await task_service.create_task(
            project_id=project_id,
            title=task_title,
            description=task_desc,
            assignee_id=AI_AGENT_ROLES.get("DevBot (Engineering)") or "ai-dev-bot",
        )

        if success:
            logger.info(f"🧹 Clockwork: Created tech debt task {task_result['task']['id']}. Dispatching DevBot...")
            await agent_service.run_agent_task(
                task_id=task_result["task"]["id"], agent_id=task_result["task"]["assignee_id"]
            )

    except Exception as e:
        logger.error(f"💥 Clockwork: Tech Debt Patrol Failed: {e}")

async def run_ssot_audit():
    """Scans for hardcoded technical debt based on historical pain points (Network, Models, Paths, Prompts)."""
    logger.info("🔎 Clockwork: Starting SSOT Audit...")
    try:
        import os
        from pathlib import Path

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
            if (root / "python" / "src").exists():
                project_root = root
                break

        warnings = []

        # We will scan python files in src/
        scan_dir = project_root / "python" / "src"
        if not scan_dir.exists():
            logger.warning("SSOT Audit skipped: python/src directory not found.")
            return

        for root_dir, _, files in os.walk(scan_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                if file == "model_ssot.py" or file == "config.py":
                    continue

                filepath = Path(root_dir) / file
                rel_path = filepath.relative_to(project_root)

                with open(filepath, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        # 1. Hostnames
                        if "archon-mcp" in line or "127.0.0.1" in line:
                            if "http" in line or "://" in line:
                                warnings.append(f"Hardcoded Network Host at `{rel_path}:{i}` -> {line.strip()[:50]}")
                        # 2. Models
                        if "gemini-" in line and "gemini-3" in line:
                            warnings.append(f"Hardcoded Model Name at `{rel_path}:{i}` -> {line.strip()[:50]}")
                        # 3. Prompts
                        if "task_desc =" in line or "task_desc=" in line:
                            if '"""' in line or "'''" in line or "(" in line:
                                warnings.append(f"Possible Hardcoded Prompt at `{rel_path}:{i}` -> {line.strip()[:50]}")

        if not warnings:
            logger.info("✅ Clockwork: SSOT Audit found no hardcoding violations.")
            return

        logger.info("⚠️ Clockwork: Detected Hardcoded Tech Debt. Creating task for DevBot...")
        cst = ZoneInfo("Asia/Taipei")
        task_title = f"Auto-Cleanup: SSOT Hardcoding Audit ({datetime.now(cst).strftime('%Y-%m-%d')})"
        task_desc = (
            "Clockwork detected the following hardcoded values (Network/Models/Prompts) that violate SSOT rules:\n\n"
            + "\n".join(f"- {w}" for w in warnings)
            + "\n\nPlease extract these to config variables, model_ssot.py, or PromptService."
        )

        supabase = get_supabase_client()
        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if not p_res.data:
            return

        project_id = p_res.data[0]["id"]
        success, task_result = await task_service.create_task(
            project_id=project_id,
            title=task_title,
            description=task_desc,
            assignee_id=AI_AGENT_ROLES.get("DevBot (Engineering)") or "ai-dev-bot",
        )

        if success:
            logger.info(f"🔎 Clockwork: Created SSOT audit task {task_result['task']['id']}.")
            await agent_service.run_agent_task(
                task_id=task_result["task"]["id"], agent_id=task_result["task"]["assignee_id"]
            )

    except Exception as e:
        logger.error(f"💥 Clockwork: SSOT Audit Failed: {e}")
