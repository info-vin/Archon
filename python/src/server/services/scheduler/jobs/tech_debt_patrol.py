"""
Tech Debt Patrol for Scheduler
Handles scanning for stale PRPs, scripts, and other technical debt.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)

async def run_tech_debt_audit() -> None:
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

        from src.server.services.prompt_service import prompt_service
        prompt_template = prompt_service.get_prompt("TECH_DEBT_CLEANUP_PROMPT")
        task_desc = prompt_template.format(warnings_str="\n\n".join(warnings))

        supabase = get_supabase_client()
        from src.server.repositories.base_repository import BaseRepository
        repo = BaseRepository(supabase)
        suc_p, p_res = repo.execute_query(
            supabase.table("archon_projects").select("id").limit(1),
            "Fetch project for tech debt task"
        )
        if not suc_p or not p_res.get("data"):
            logger.warning("Clockwork: No projects found to attach tech debt task.")
            return

        project_id = p_res["data"][0]["id"]

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

async def run_ssot_audit() -> None:
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
            scan_dir = project_root / "src"  # Fallback for Docker environment
            if not scan_dir.exists():
                logger.warning("SSOT Audit skipped: Both python/src and src directories not found.")
                return

        for root_dir, _, files in os.walk(scan_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                if file == "model_ssot.py" or file == "config.py":
                    continue

                filepath = Path(root_dir) / file
                if not os.path.isfile(filepath):
                    continue
                if "visit_log_service.py" in str(filepath):
                    continue
                rel_path = filepath.relative_to(project_root)

                with open(filepath, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        # 1. Hostnames
                        if "archon-mcp" in line or "127.0.0.1" in line: # 合法
                            if "http" in line or "://" in line:
                                warnings.append(f"Hardcoded Network Host at `{rel_path}:{i}` -> {line.strip()[:50]}")
                        # 2. Models removed due to dynamic discovery
                        # 3. Prompts
                        if ("task_desc =" in line or "task_desc=" in line) and not any(x in line for x in ["prompt_template", "str(output)", "get(", 'f"**', "await "]):
                            if '"""' in line or "'''" in line or "(" in line:
                                warnings.append(f"Possible Hardcoded Prompt at `{rel_path}:{i}` -> {line.strip()[:50]}")

        if not warnings:
            logger.info("✅ Clockwork: SSOT Audit found no hardcoding violations.")
            return

        logger.info("⚠️ Clockwork: Detected Hardcoded Tech Debt. Creating task for DevBot...")
        cst = ZoneInfo("Asia/Taipei")
        task_title = f"Auto-Cleanup: SSOT Hardcoding Audit ({datetime.now(cst).strftime('%Y-%m-%d')})"

        from src.server.services.prompt_service import prompt_service
        prompt_template2 = prompt_service.get_prompt("TECH_DEBT_SSOT_AUDIT_PROMPT")
        task_desc = prompt_template2.format(warnings_str="\n".join(f"- {w}" for w in warnings))

        supabase = get_supabase_client()
        from src.server.repositories.base_repository import BaseRepository
        repo = BaseRepository(supabase)
        suc_p, p_res = repo.execute_query(
            supabase.table("archon_projects").select("id").limit(1),
            "Fetch project for SSOT audit task"
        )
        if not suc_p or not p_res.get("data"):
            return

        project_id = p_res["data"][0]["id"]
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

async def run_engineering_retrospective() -> None:
    """Executes a Map-Reduce Weekly Engineering Retro using git log and GEMINI.md context."""
    logger.info("🛠️ Clockwork: Starting Weekly Engineering Retrospective...")
    try:
        import subprocess
        from pathlib import Path

        from src.agents.workflow.engine_beta_graph import BetaState, beta_graph
        from src.agents.workflow.state import SharedState
        from src.server.config.config import get_config
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service
        from src.server.services.shared_constants import AgentUUIDs, PromptNameEnum
        from src.server.utils import get_supabase_client

        config = get_config()
        days = getattr(config, "weekly_engineering_retro_lookback_days", 7)

        project_root = Path("/app")
        if not project_root.exists():
            project_root = Path.cwd()

        # 1. Fetch git logs
        try:
            git_logs = subprocess.check_output(
                ["git", "log", f"--since={days} days ago", "--oneline", "--stat"],
                cwd=str(project_root),
                stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="ignore")
        except Exception:
            git_logs = "無法取得 git 歷史紀錄 (Not a git repository or no recent logs)."

        # 2. Fetch GEMINI.md logs
        gemini_md_path = project_root / "GEMINI.md"
        journal_logs = ""
        if gemini_md_path.exists():
            try:
                with open(gemini_md_path, encoding="utf-8") as f:
                    lines = f.readlines()
                    journal_logs = "".join(lines[-200:])
            except Exception:
                journal_logs = "無法讀取 GEMINI.md"

        from src.server.prompts.pm_prompts import ENGINEERING_RETRO_DEFAULT
        from src.server.services.prompt_service import prompt_service

        prompt_template = prompt_service.get_prompt("ENGINEERING_RETRO_DEFAULT", default=ENGINEERING_RETRO_DEFAULT)
        prompt_content = prompt_template.format(
            days=days,
            git_logs=git_logs[:3000],  # truncate if too large
            journal_logs=journal_logs
        )

        state = BetaState(shared=SharedState())
        state.worker_targets = ["product", "business"]
        state.worker_prompts = {
            "product": PromptNameEnum.MAP_REDUCE_POBOT_PROMPT,
            "business": PromptNameEnum.MAP_REDUCE_BUSINESS_PROMPT,
        }
        state.reducer_prompt_name = PromptNameEnum.MAP_REDUCE_ENGINEERING_REDUCER_PROMPT
        state.shared.messages = [{"role": "user", "content": prompt_content}]

        logger.info("🛠️ Clockwork: Executing beta_graph Map-Reduce for Engineering Retro...")
        run_result = await beta_graph.run(deps=None, state=state)
        import typing
        output = typing.cast(typing.Any, run_result).output if hasattr(run_result, "output") else run_result

        task_desc = str(output)

        cst = ZoneInfo("Asia/Taipei")
        task_title = f"[Weekly Retro] Engineering Reflection ({datetime.now(cst).strftime('%Y-%m-%d')})"

        supabase = get_supabase_client()
        from src.server.repositories.base_repository import BaseRepository
        repo = BaseRepository(supabase)
        suc_p, p_res = repo.execute_query(
            supabase.table("archon_projects").select("id").limit(1),
            "Fetch project for Engineering Retro"
        )
        if not suc_p or not p_res.get("data"):
            logger.warning("Clockwork: No projects found to attach Engineering Retro task.")
            return

        project_id = p_res["data"][0]["id"]

        success, task_result = await task_service.create_task(
            project_id=project_id,
            title=task_title,
            description=task_desc,
            assignee_id=AgentUUIDs.DEV_BOT,
        )

        if success:
            task_id = task_result["task"]["id"]
            logger.info(f"✅ Clockwork: Created Engineering Retro task {task_id}. Dispatching DevBot Group Chat...")
            await agent_service.run_agent_task(task_id=task_id, agent_id=AgentUUIDs.DEV_BOT)

    except Exception as e:
        logger.error(f"💥 Clockwork: Engineering Retrospective Failed: {e}", exc_info=True)
