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

        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service
        from src.server.services.scheduler.utils import get_default_project_id, resolve_project_root
        from src.server.services.shared_constants import AI_AGENT_ROLES
        from src.server.utils import get_supabase_client

        project_root = resolve_project_root("PRPs")

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
        project_id = get_default_project_id(supabase, "Fetch project for tech debt task")
        if not project_id:
            logger.warning("Clockwork: No projects found to attach tech debt task.")
            return

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
        from src.server.services.scheduler.utils import get_default_project_id, resolve_project_root
        from src.server.services.shared_constants import AI_AGENT_ROLES
        from src.server.utils import get_supabase_client

        project_root = resolve_project_root("python/src")

        warnings = []

        # We will scan python files in src/
        scan_dir = project_root / "python" / "src"
        if not scan_dir.exists():
            scan_dir = project_root / "src"  # Fallback for Docker environment
            if not scan_dir.exists():
                logger.warning("SSOT Audit skipped: Both python/src and src directories not found.")
                return

        allowed_ssot_files = {
            "model_ssot.py",
            "config.py",
            "settings.py",
            "service_discovery.py",
            "logfire_config.py",
            "client_manager.py",
            "credential_service.py",
            "main.py",
            "lifespan.py",
            "mcp_client.py",
            "endpoints.py",
            "reranking_strategy.py",
            "visit_log_service.py",
        }

        for root_dir, _, files in os.walk(scan_dir):
            for file in files:
                if not file.endswith(".py") or file in allowed_ssot_files:
                    continue

                filepath = Path(root_dir) / file
                if not os.path.isfile(filepath):
                    continue
                rel_path = filepath.relative_to(project_root)

                with open(filepath, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if "# 合法" in line or line.strip().startswith("#"):
                            continue
                        # 1. Hostnames
                        if "archon-mcp" in line or "127.0.0.1" in line:  # 合法
                            if "http" in line or "://" in line:
                                warnings.append(f"Hardcoded Network Host at `{rel_path}:{i}` -> {line.strip()[:50]}")
                        # 2. Prompts
                        if ("task_desc =" in line or "task_desc=" in line) and not any(
                            x in line for x in ["prompt_template", "prompt_service", "str(output)", "get(", 'f"**', "await "]
                        ):
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
        project_id = get_default_project_id(supabase, "Fetch project for SSOT audit task")
        if not project_id:
            return

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
    """Executes a Map-Reduce Weekly Engineering Retro using git log, GEMINI.md, and DB telemetry fallback."""
    logger.info("🛠️ Clockwork: Starting Weekly Engineering Retrospective...")
    try:
        import subprocess
        from datetime import UTC, timedelta

        from src.agents.workflow.engine_beta_graph import BetaState, beta_graph
        from src.agents.workflow.state import SharedState
        from src.server.config.config import get_config
        from src.server.repositories.base_repository import BaseRepository
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service
        from src.server.services.scheduler.utils import get_default_project_id, resolve_project_root
        from src.server.services.shared_constants import AgentUUIDs, PromptNameEnum
        from src.server.utils import get_supabase_client

        config = get_config()
        days = getattr(config, "weekly_engineering_retro_lookback_days", 7)
        supabase = get_supabase_client()
        repo = BaseRepository(supabase)

        project_root = resolve_project_root("GEMINI.md")

        # 1. Fetch git logs with Cloud/Docker DB fallback
        git_logs = ""
        try:
            git_logs = subprocess.check_output(
                ["git", "log", f"--since={days} days ago", "--oneline", "--stat"],
                cwd=str(project_root),
                stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="ignore").strip()
        except Exception:
            git_logs = ""

        if not git_logs:
            cutoff_iso = (datetime.now(UTC) - timedelta(days=days)).isoformat()
            suc_t, res_t = repo.execute_query(
                supabase.table("archon_tasks")  # 合法
                .select("title, status, assignee, updated_at")
                .gte("updated_at", cutoff_iso)
                .order("updated_at", desc=True)
                .limit(30),
                "Fetch recent engineering tasks for retro fallback",
            )
            recent_tasks = res_t.get("data", []) if suc_t and isinstance(res_t.get("data"), list) else []
            if recent_tasks:
                git_logs = "【雲端容器模式：由 Supabase archon_tasks 實體工單紀錄提供近 7 日工程進度】\n" + "\n".join(
                    f"- [{t.get('updated_at', '')[:10]}] ({t.get('status')}) {t.get('title')} (Assignee: {t.get('assignee')})"
                    for t in recent_tasks
                )
            else:
                git_logs = "近 7 日無新增 Git 提交或工程工單紀錄。"

        # 2. Fetch GEMINI.md logs with Cloud/Docker DB fallback
        gemini_md_path = project_root / "GEMINI.md"
        journal_logs = ""
        if gemini_md_path.exists():
            try:
                with open(gemini_md_path, encoding="utf-8") as f:
                    lines = f.readlines()
                    journal_logs = "".join(lines[-200:]).strip()
            except Exception:
                journal_logs = ""

        if not journal_logs:
            cutoff_iso = (datetime.now(UTC) - timedelta(days=days)).isoformat()
            suc_l, res_l = repo.execute_query(
                supabase.table("archon_logs")  # 合法
                .select("created_at, source, level, message")
                .gte("created_at", cutoff_iso)
                .order("created_at", desc=True)
                .limit(40),
                "Fetch recent system logs for retro fallback",
            )
            recent_logs = res_l.get("data", []) if suc_l and isinstance(res_l.get("data"), list) else []
            if recent_logs:
                journal_logs = "【雲端容器模式：由 Supabase archon_logs 實體系統日誌提供近 7 日架構遙測】\n" + "\n".join(
                    f"- [{lg.get('created_at', '')[:16]}] [{lg.get('level')}] {lg.get('source')}: {lg.get('message')}"
                    for lg in recent_logs
                )
            else:
                journal_logs = "近 7 日無系統異常日誌。"

        from src.server.prompts.pm_prompts import ENGINEERING_RETRO_DEFAULT
        from src.server.services.prompt_service import prompt_service

        prompt_template = prompt_service.get_prompt("ENGINEERING_RETRO_DEFAULT", default=ENGINEERING_RETRO_DEFAULT)
        prompt_content = prompt_template.format(
            days=days,
            git_logs=git_logs[:3000],  # truncate if too large
            journal_logs=journal_logs[:4000]
        )

        state = BetaState(shared=SharedState())
        state.worker_targets = ["product", "business"] # 合法
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

        project_id = get_default_project_id(supabase, "Fetch project for Engineering Retro")
        if not project_id:
            logger.warning("Clockwork: No projects found to attach Engineering Retro task.")
            return

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
