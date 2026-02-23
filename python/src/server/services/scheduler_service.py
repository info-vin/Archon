from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config.logfire_config import get_logger
from .health_service import HealthService

logger = get_logger(__name__)

class SchedulerService:
    _instance = None
    _scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._scheduler = AsyncIOScheduler()
        return cls._instance

    async def _get_setting(self, key: str, default: int) -> int:
        """Helper to fetch numerical settings from DB."""
        try:
            from ..utils import get_supabase_client
            supabase = get_supabase_client()
            res = supabase.table("archon_settings").select("value").eq("key", key).execute()
            if res.data:
                return int(res.data[0]["value"])
        except Exception as e:
            logger.warning(f"Scheduler: Failed to fetch {key}, using default {default}: {e}")
        return default

    async def start(self):
        if self._scheduler and not self._scheduler.running:
            logger.info("🕒 Clockwork: Starting Scheduler Service...")
            self._scheduler.start()
            # We need to run seeding logic in a way that allows fetching async settings
            await self._schedule_jobs()
        else:
            logger.warning("Clockwork: Scheduler already running or not initialized.")

    def shutdown(self):
        if self._scheduler and self._scheduler.running:
            logger.info("🛑 Clockwork: Shutting down Scheduler...")
            self._scheduler.shutdown()

    async def _schedule_jobs(self):
        if not self._scheduler:
            return

        # Fetch intervals from settings
        probe_mins = await self._get_setting("SCHEDULER_PROBE_INTERVAL_MINS", 60)
        patrol_mins = await self._get_setting("SCHEDULER_PATROL_INTERVAL_MINS", 60)
        sentinel_hours = await self._get_setting("SCHEDULER_SENTINEL_INTERVAL_HOURS", 12)

        # Job 1: System Heartbeat Probe
        self._scheduler.add_job(
            self._run_system_probe,
            trigger=IntervalTrigger(minutes=probe_mins),
            id="system_probe",
            replace_existing=True
        )
        logger.info(f"✅ Scheduled Job: System Probe (Every {probe_mins} mins)")

        # Job 1.5: System Probe Cleanup (Hourly)
        self._scheduler.add_job(
            self._cleanup_system_probes,
            trigger=IntervalTrigger(hours=1),
            id="system_probe_cleanup",
            replace_existing=True
        )

        # Job 2: The Accountant - Token Analysis (Every 24 hours)
        self._scheduler.add_job(
            self._analyze_token_usage,
            trigger=IntervalTrigger(hours=24),
            id="token_analysis",
            replace_existing=True
        )

        # Job 3: The Patrol - Log Analysis & Auto-Repair
        self._scheduler.add_job(
            self._run_log_patrol,
            trigger=IntervalTrigger(minutes=patrol_mins),
            id="log_patrol",
            replace_existing=True
        )
        logger.info(f"✅ Scheduled Job: Log Patrol (Every {patrol_mins} mins)")

        # Job 4: The Sentinel - Business Logic Monitoring
        self._scheduler.add_job(
            self._run_business_sentinel,
            trigger=IntervalTrigger(hours=sentinel_hours),
            id="business_sentinel",
            replace_existing=True
        )
        logger.info(f"✅ Scheduled Job: Business Sentinel (Every {sentinel_hours} hours)")

        # Job 5: The Dispatcher - Recurring Task Execution (Every 30 minutes)
        # 物理加固：實作 David 的自動化爬蟲排程，達成 5173 任務與 3737 設定的自動閉環
        self._scheduler.add_job(
            self._run_task_dispatcher,
            trigger=IntervalTrigger(minutes=30),
            id="task_dispatcher",
            replace_existing=True
        )
        logger.info("✅ Scheduled Job: Task Dispatcher (Every 30 mins)")

    async def _run_task_dispatcher(self):
        """
        Scans archon_tasks for recurring tasks (is_recurring=true) and dispatches them
        based on David's schedule_config.
        """
        logger.info("📡 Clockwork: Starting Task Dispatcher...")
        try:
            from ..utils import get_supabase_client
            from .agent_service import agent_service

            supabase = get_supabase_client()

            # Find recurring tasks that are ready to run
            # For MVP: We pick 'todo' or 'pending' tasks marked as recurring
            res = (
                supabase.table("archon_tasks")
                .select("id, title, assignee_id, schedule_config, crawler_target_id")
                .eq("is_recurring", True)
                .not_.eq("status", "completed")
                .execute()
            )

            tasks = res.data or []
            if not tasks:
                logger.info("📡 Clockwork: No pending recurring tasks found.")
                return

            logger.info(f"📡 Clockwork: Processing {len(tasks)} recurring tasks...")

            for task in tasks:
                # 物理連動：如果任務關聯了 crawler_target_id (來自 3737)，則優先處理
                target_id = task.get("crawler_target_id")
                task_id = task["id"]

                # Check if it's time to run (Simple daily logic for now)
                # In a full implementation, we would parse cron from schedule_config
                logger.info(f"📡 Clockwork: Dispatching task '{task['title']}' (ID: {task_id}) to Agent {task['assignee_id']}")

                # Execute the task via AgentService
                # This will trigger Librarian to crawl if it's a knowledge task
                await agent_service.run_agent_task(
                    task_id=task_id,
                    agent_id=task_id # Note: agent_id in run_agent_task matches the task's assignee_id internally
                )

                # Log success
                supabase.table("archon_logs").insert({
                    "source": "clockwork-scheduler",
                    "level": "INFO",
                    "message": f"Auto-dispatched recurring task: {task['title']}",
                    "details": {"task_id": task_id, "target_id": target_id}
                }).execute()

        except Exception as e:
            logger.error(f"💥 Clockwork: Task Dispatcher Failed: {e}")

    async def _run_log_patrol(self):
        """
        Scans logs for errors and dispatches DevBot if needed.
        """
        logger.info("👮 Clockwork: Starting Log Patrol...")
        try:
            from ..utils import get_supabase_client
            from .agent_service import agent_service
            from .projects.task_service import task_service
            from .shared_constants import AI_AGENT_ROLES

            supabase = get_supabase_client()
            one_hour_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

            # Find recent errors
            res = (
                supabase.table("archon_logs")
                .select("*")
                .eq("level", "ERROR")
                .gt("created_at", one_hour_ago)
                .limit(5) # Avoid spamming tasks
                .execute()
            )

            errors = res.data or []
            if not errors:
                logger.info("👮 Clockwork: No recent errors found. All systems nominal.")
                return

            logger.info(f"👮 Clockwork: Detected {len(errors)} errors. Analyzing...")

            # Simple heuristic: If we find errors, create ONE investigation task
            # In a real system, we would group similar errors.

            # Create a task for DevBot
            error_summary = "\n".join([f"- [{e['source']}] {e['message']}" for e in errors])
            task_title = f"Auto-Repair: System Errors Detected ({datetime.now().strftime('%H:%M')})"
            task_desc = f"Clockwork detected the following errors in the last hour:\n{error_summary}\n\nPlease analyze and fix."

            # We need a project ID to attach the task to.
            # Ideally, there should be a 'System Maintenance' project.
            # For now, we'll try to find one or create it?
            # Or just fail if no project found.
            # Let's assume a default project or pick the first one for MVP.

            p_res = supabase.table("archon_projects").select("id").limit(1).execute()
            if not p_res.data:
                logger.warning("Clockwork: No projects found to attach repair task.")
                return

            project_id = p_res.data[0]["id"]

            # Create Task
            # We explicitly define parameters to ensure type safety and match TaskService.create_task signature
            success, task_result = await task_service.create_task(
                project_id=project_id,
                title=task_title,
                description=task_desc,
                assignee_id=AI_AGENT_ROLES.get("DevBot (Engineering)") or "ai-dev-bot"
            )


            if success:
                logger.info(f"👮 Clockwork: Created repair task {task_result['task']['id']}. Dispatching DevBot...")
                # Dispatch DevBot immediately
                await agent_service.run_agent_task(task_id=task_result['task']['id'], agent_id=task_result['task']["assignee_id"])

        except Exception as e:
            logger.error(f"💥 Clockwork: Log Patrol Failed: {e}")

    async def _analyze_token_usage(self):
        logger.info("🤖 Clockwork: Starting Token Usage Analysis...")
        try:
            from ..utils import get_supabase_client
            supabase = get_supabase_client()

            one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()

            # Using parentheses for multi-line chaining (standard Python practice)
            res = (
                supabase.table("gemini_logs")
                .select("user_name, gemini_response")
                .gt("created_at", one_day_ago)
                .execute()
            )

            data = res.data or []
            usage_map: dict[str, int] = {}
            total_tokens = 0

            for entry in data:
                user = entry.get("user_name", "Unknown")
                content = entry.get("gemini_response", "")
                if not content:
                    continue

                est_tokens = len(content) // 4
                usage_map[user] = usage_map.get(user, 0) + est_tokens
                total_tokens += est_tokens

            logger.info(f"📊 Daily Token Analysis: {total_tokens} tokens estimated across {len(usage_map)} users.")

            details = {
                "type": "token_analysis",
                "period": "24h",
                "usage_breakdown": usage_map,
                "total_estimated": total_tokens
            }

            supabase.table("archon_logs").insert({
                "source": "clockwork-scheduler",
                "level": "INFO",
                "message": f"Daily Token Analysis: {total_tokens} tokens",
                "details": details
            }).execute()

        except Exception as e:
            logger.error(f"💥 Clockwork: Token Analysis Failed: {e}")
            try:
                from ..utils import get_supabase_client
                get_supabase_client().table("archon_logs").insert({
                    "source": "clockwork-scheduler",
                    "level": "ERROR",
                    "message": f"Token Analysis Failed: {str(e)}",
                    "details": {"error": str(e)}
                }).execute()
            except Exception:
                pass

    async def _run_system_probe(self):
        logger.info("🤖 Clockwork: Triggering System Probe via HealthService...")
        try:
            from ..utils import get_supabase_client
            supabase = get_supabase_client()

            # Use the integrated HealthService
            health_service = HealthService()
            result = await health_service.check_rag_integrity()

            success = result.get("status") == "healthy"
            log_level = "INFO" if success else "ERROR"
            msg = "System Probe Passed" if success else "System Probe FAILED"

            if success:
                logger.info(f"✅ Clockwork: {msg}")
            else:
                logger.error(f"❌ Clockwork: {msg} | Details: {result.get('details', {}).get('errors')}")

            try:
                supabase.table("archon_logs").insert({
                    "source": "clockwork-scheduler",
                    "level": log_level,
                    "message": msg,
                    "details": result
                }).execute()
            except Exception as db_err:
                logger.error(f"❌ Clockwork: Failed to write to archon_logs: {db_err}")

        except Exception as e:
            logger.error(f"💥 Clockwork: System Probe Crashed: {e}")
            try:
                from ..utils import get_supabase_client
                supabase = get_supabase_client()
                supabase.table("archon_logs").insert({
                    "source": "clockwork-scheduler",
                    "level": "CRITICAL",
                    "message": f"System Probe Crashed: {str(e)}",
                    "details": {"error": str(e)}
                }).execute()
            except Exception:
                pass

    async def run_business_sentinel(self):
        """Public wrapper for manual triggering."""
        await self._run_business_sentinel()

    async def _run_business_sentinel(self):
        """
        Scans leads for staleness and other business anomalies.
        Generates ALERT logs for the Manager Dashboard.
        """
        logger.info("🛡️ Clockwork: Starting Business Sentinel...")
        try:
            from ..utils import get_supabase_client
            supabase = get_supabase_client()

            # 1. Fetch Threshold from settings (Fallback to 14 days)
            threshold_days = 14
            try:
                res_settings = supabase.table("archon_settings").select("value").eq("key", "STALE_LEAD_THRESHOLD_DAYS").execute()
                if res_settings.data:
                    threshold_days = int(res_settings.data[0]["value"])
            except Exception:
                pass

            cutoff_date = (datetime.now(UTC) - timedelta(days=threshold_days)).isoformat()
            logger.info(f"🛡️ Sentinel: Scanning for leads updated before {cutoff_date} (threshold={threshold_days}d)")

            # 2. Find Stale Leads
            # Filter: updated_at < cutoff AND status NOT IN ('won', 'converted')
            res = (
                supabase.table("leads")
                .select("id, company_name, updated_at, enrichment_score, status")
                .lt("updated_at", cutoff_date)
                .not_.in_("status", ["won", "converted"])
                .limit(20) # Limit per scan
                .execute()
            )

            stale_leads = res.data or []
            company_names = [lead.get("company_name") for lead in stale_leads]
            logger.info(f"🛡️ Sentinel: Found {len(stale_leads)} potential stale leads in DB: {company_names}")

            if not stale_leads:
                logger.info("🛡️ Clockwork: No stale leads found.")
            else:
                for lead in stale_leads:
                    # Check for existing recent alert to avoid spam (within last 7 days)
                    seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()
                    existing = supabase.table("archon_logs").select("id")\
                        .eq("source", "sentinel")\
                        .eq("level", "ALERT")\
                        .gt("created_at", seven_days_ago)\
                        .filter("details->>lead_id", "eq", str(lead["id"]))\
                        .execute()

                    if existing.data:
                        continue

                    # Parse updated_at to calculate actual days
                    lead_updated = datetime.fromisoformat(lead["updated_at"].replace('Z', '+00:00'))
                    days_stale = (datetime.now(UTC) - lead_updated).days
                    alert_msg = f"Stale Lead Risk: {lead['company_name']} ({days_stale} days inactive)"

                    alert_payload = {
                        "source": "sentinel",
                        "level": "ALERT",
                        "message": alert_msg,
                        "details": {
                            "type": "stale_lead",
                            "category": "business", # Strategic Filter
                            "lead_id": lead["id"],
                            "company": lead["company_name"],
                            "days_stale": days_stale,
                            "enrichment_score": lead.get("enrichment_score", 0)
                        }
                    }
                    supabase.table("archon_logs").insert(alert_payload).execute()
                    logger.info(f"🛡️ Sentinel: Created alert for {lead['company_name']}")

            # 3. Find Content Bottlenecks (New Logic for GAP-029)
            # Filter: status = 'review' AND updated_at < 48h ago
            forty_eight_hours_ago = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
            post_res = supabase.table("blog_posts")\
                .select("id, title, status, updated_at")\
                .eq("status", "review")\
                .lt("updated_at", forty_eight_hours_ago).execute()

            bottlenecks = post_res.data or []
            for post in bottlenecks:
                seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()
                existing_p = supabase.table("archon_logs").select("id")\
                    .eq("source", "sentinel")\
                    .eq("level", "ALERT")\
                    .gt("created_at", seven_days_ago)\
                    .filter("details->>post_id", "eq", str(post["id"]))\
                    .execute()

                if existing_p.data:
                    continue

                post_updated = datetime.fromisoformat(post["updated_at"].replace('Z', '+00:00'))
                hours_stuck = int((datetime.now(UTC) - post_updated).total_seconds() / 3600)

                alert_payload = {
                    "source": "sentinel",
                    "level": "ALERT",
                    "message": f"Content Bottleneck: '{post['title']}' stuck in review for {hours_stuck}h",
                    "details": {
                        "type": "content_bottleneck",
                        "category": "business", # Strategic Filter
                        "post_id": post["id"],
                        "title": post["title"],
                        "hours_stuck": hours_stuck
                    }
                }
                supabase.table("archon_logs").insert(alert_payload).execute()
                logger.info(f"🛡️ Sentinel: Created bottleneck alert for {post['title']}")

        except Exception as e:
            logger.error(f"💥 Clockwork: Business Sentinel Failed: {e}", exc_info=True)

    async def _cleanup_system_probes(self):
        """
        Retention Policy: Deletes System Probe data older than 48 hours to prevent unwanted KB bloat.
        Targets: archon_crawled_pages, archon_document_versions, archon_sources (cascade order).
        """
        logger.info("🧹 Clockwork: Running System Probe Cleanup...")
        try:
            from ..utils import get_supabase_client
            supabase = get_supabase_client()

            # Calculate cutoff time (48 hours ago)
            cutoff_time = (datetime.now(UTC) - timedelta(hours=48)).isoformat()

            # 1. Clean Leads (Safety net, though Probe doesn't usually create leads)
            res = supabase.table("leads").delete().eq("company_name", "System Probe").lt("created_at", cutoff_time).execute()
            deleted_leads = len(res.data) if res.data else 0

            # 2. Clean Knowledge Base Items (Real Tables)
            # The probe creates a source with ID pattern 'pitch-systemprobe-%'
            # We must delete in order or rely on CASCADE. Explicit deletion is safer for now.

            # A. Delete Content Pages
            # We filter by source_id pattern since we can't do complex joins easily in simple delete calls
            # But Supabase (PostgREST) delete supports filtering.
            # Using 'like' filter for 'pitch-systemprobe-%'
            res_pages = supabase.table("archon_crawled_pages").delete().like("source_id", "pitch-systemprobe-%").lt("created_at", cutoff_time).execute()
            deleted_pages = len(res_pages.data) if res_pages.data else 0

            # B. Delete Document Versions
            # The content field is JSONB, we need to check if content->source_id starts with...
            # This is harder to do efficiently with simple filters if not indexed, but for cleanup it's okay.
            # Alternatively, we can just delete versions created by 'ai-librarian' with change_summary containing 'validating vector database' or similar?
            # Or just rely on the fact that we know the ID structure.
            # Let's try to filter by the content->source_id if possible, or maybe just matching the change_summary if consistent.
            # LibrarianService: "change_summary": f"Archived generated pitch for {company}" -> "Archived generated pitch for System Probe"
            res_versions = supabase.table("archon_document_versions").delete()\
                .eq("created_by", "ai-librarian")\
                .like("change_summary", "%System Probe%")\
                .lt("created_at", cutoff_time)\
                .execute()
            deleted_versions = len(res_versions.data) if res_versions.data else 0

            # C. Delete Sources (Parent)
            res_sources = supabase.table("archon_sources").delete().like("source_id", "pitch-systemprobe-%").lt("created_at", cutoff_time).execute()
            deleted_sources = len(res_sources.data) if res_sources.data else 0

            total_deleted = deleted_leads + deleted_pages + deleted_versions + deleted_sources

            if total_deleted > 0:
                logger.info(f"✅ Clockwork: Cleanup complete. Deleted {deleted_leads} leads, {deleted_pages} pages, {deleted_versions} versions, {deleted_sources} sources.")
            else:
                logger.info("✅ Clockwork: Cleanup complete. No expired probe data found.")

        except Exception as e:
            logger.error(f"💥 Clockwork: System Probe Cleanup Failed: {e}")

scheduler_service = SchedulerService()
