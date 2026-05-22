"""
Business Monitoring Jobs for Scheduler
Handles leads, market reports, and token analysis.
"""

from datetime import UTC, datetime, timedelta

from src.server.config.logfire_config import get_logger
from src.server.services.shared_constants import AgentUUIDs
from src.server.utils import get_supabase_client

logger = get_logger(__name__)


async def run_auto_fetch_leads():
    """Clockwork task to trigger Alice's daily lead auto-fetch."""
    logger.info("📡 Clockwork: Triggering daily Alice job search...")
    try:
        from src.server.services.job_board_service import JobBoardService

        service = JobBoardService()
        new_leads = await service.auto_fetch_daily_leads()

        get_supabase_client().table("archon_logs").insert(
            {
                "source": "clockwork-scheduler",
                "level": "INFO",
                "message": f"Daily auto-fetch completed. {new_leads} new leads saved.",
                "details": {"new_leads_count": new_leads},
            }
        ).execute()
        logger.info(f"✅ Clockwork: Alice daily auto-fetch finished ({new_leads} leads).")
    except Exception as e:
        logger.error(f"💥 Clockwork: Alice auto-fetch failed: {e}")


async def run_prune_stale_leads():
    """Clockwork task to prune stale leads (Scenario D Pruning Loop)."""
    logger.info("🧹 Clockwork: Triggering hourly prune stale leads...")
    try:
        from src.server.services.enrichment_service import EnrichmentService

        pruned_count = await EnrichmentService.prune_stale_leads()

        if pruned_count > 0:
            get_supabase_client().table("archon_logs").insert(
                {
                    "source": "clockwork-scheduler",
                    "level": "INFO",
                    "message": f"Stale leads pruning completed. {pruned_count} leads archived.",
                    "details": {"pruned_count": pruned_count},
                }
            ).execute()
        logger.info(f"✅ Clockwork: Stale leads pruning finished ({pruned_count} leads archived).")
    except Exception as e:
        logger.error(f"💥 Clockwork: Pruning stale leads failed: {e}")


async def run_daily_market_report():
    """Triggering Bob (MarketingBot) to summarize today's leads."""
    logger.info("✍️ Clockwork: Triggering Bob's Daily Market Report...")
    try:
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service

        supabase = get_supabase_client()
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        res = supabase.table("leads").select("company_name, job_title, status").gt("created_at", one_day_ago).execute()
        leads = res.data or []
        if not leads:
            logger.info("✍️ Clockwork: No new leads today to report on. (Cycle logged)")
            return

        lead_summary = "\n".join([f"- {lead['company_name']} looking for {lead['job_title']}" for lead in leads])
        task_title = f"Daily Market Intelligence ({datetime.now().strftime('%Y-%m-%d')})"
        task_desc = f"""Please write an engaging 600-word daily blog post summarizing today's tech job market movements.

Data points ({len(leads)} leads):
{lead_summary}

Focus on industry trends and written in Traditional Chinese (繁體中文).
Use the tool to save this blog post as a DRAFT."""

        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if not p_res.data:
            logger.warning("Clockwork: No projects found to attach marketing task.")
            return

        success, tr = await task_service.create_task(
            project_id=p_res.data[0]["id"], title=task_title, description=task_desc, assignee_id=AgentUUIDs.MARKET_BOT
        )
        if success:
            logger.info(f"✍️ Clockwork: Created Market Report task {tr['task']['id']}. Dispatching Bob...")
            await agent_service.run_agent_task(task_id=tr["task"]["id"], agent_id=AgentUUIDs.MARKET_BOT)
    except Exception as e:
        logger.error(f"💥 Clockwork: Bob market report generation failed: {e}")


async def gather_report_context(days: int) -> str:
    """Gathers database metrics and events from the last N days to ground periodic summaries."""
    logger.info(f"📊 Gathering report context for the past {days} day(s)...")
    try:
        supabase = get_supabase_client()
        cutoff_date = (datetime.now(UTC) - timedelta(days=days)).isoformat()

        # 1. Leads
        leads_res = (
            supabase.table("leads").select("company_name, job_title, status").gt("created_at", cutoff_date).execute()
        )
        leads = leads_res.data or []
        leads_summary = f"Total New Leads: {len(leads)}\n"
        if leads:
            lead_status_counts: dict[str, int] = {}
            for lead in leads:
                lead_status_counts[lead["status"]] = lead_status_counts.get(lead["status"], 0) + 1
            leads_summary += "Status Breakdown: " + ", ".join(f"{k}: {v}" for k, v in lead_status_counts.items()) + "\n"
            leads_summary += "Recent Leads Sample:\n" + "\n".join(
                f"- {lead['company_name']} ({lead['job_title']}) -> {lead['status']}" for lead in leads[:10]
            )
            if len(leads) > 10:
                leads_summary += f"\n... and {len(leads) - 10} more leads."
        else:
            leads_summary += "No new leads found."

        # 2. Token Usage
        token_res = (
            supabase.table("token_usage")
            .select("input_tokens, output_tokens, cost_usd")
            .gt("created_at", cutoff_date)
            .execute()
        )
        token_data = token_res.data or []
        total_input = sum(row.get("input_tokens", 0) or 0 for row in token_data)
        total_output = sum(row.get("output_tokens", 0) or 0 for row in token_data)
        total_cost = sum(float(row.get("cost_usd", 0.0) or 0.0) for row in token_data)
        token_summary = (
            f"API Request Count: {len(token_data)}\n"
            f"Input Tokens: {total_input}\n"
            f"Output Tokens: {total_output}\n"
            f"Total Cost: ${total_cost:.4f} USD"
        )

        # 3. System Alerts / Errors
        logs_res = (
            supabase.table("archon_logs")
            .select("level, message, source, created_at")
            .gt("created_at", cutoff_date)
            .in_("level", ["ALERT", "ERROR"])
            .execute()
        )
        logs = logs_res.data or []
        logs_summary = f"Total Alerts/Errors: {len(logs)}\n"
        if logs:
            logs_summary += "Recent Alerts/Errors:\n" + "\n".join(
                f"- [{log['level']}] {log['source']}: {log['message']} ({log['created_at']})" for log in logs[:10]
            )
            if len(logs) > 10:
                logs_summary += f"\n... and {len(logs) - 10} more alerts."
        else:
            logs_summary += "No critical alerts/errors."

        # 4. Tasks Updated
        tasks_res = (
            supabase.table("archon_tasks").select("title, status, assignee").gt("updated_at", cutoff_date).execute()
        )
        tasks = tasks_res.data or []
        tasks_summary = f"Total Tasks Active/Updated: {len(tasks)}\n"
        if tasks:
            task_status_counts: dict[str, int] = {}
            for t in tasks:
                task_status_counts[t["status"]] = task_status_counts.get(t["status"], 0) + 1
            status_desc = ", ".join(f"{k}: {v}" for k, v in task_status_counts.items())
            tasks_summary += f"Status Breakdown: {status_desc}\n"
            tasks_summary += "Tasks List:\n" + "\n".join(
                f"- {t['title']} ({t['assignee']}) -> status: {t['status']}" for t in tasks[:10]
            )
            if len(tasks) > 10:
                tasks_summary += f"\n... and {len(tasks) - 10} more tasks."
        else:
            tasks_summary += "No task status updates."

        context_md = f"""### 系統運行上下文數據 (過去 {days} 天)

#### 1. 商業開發線告 (Leads)
{leads_summary}

#### 2. AI 運算用量與成本 (Token Usage)
{token_summary}

#### 3. 系統警示與異常紀錄 (Archon Logs)
{logs_summary}

#### 4. 專案任務狀態異動 (Archon Tasks)
{tasks_summary}
"""
        return context_md
    except Exception as e:
        logger.error(f"Failed to gather report context: {e}", exc_info=True)
        return "無法取得系統運行數據，請以無上下文模式進行總結。"


async def run_daily_executive_summary():
    """Clockwork task to trigger Star-topology Group Chat for Daily Executive Summary."""
    logger.info("📊 Clockwork: Triggering Daily Executive Summary (Group Chat)...")
    try:
        import asyncio

        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service
        from src.server.services.shared_constants import AgentUUIDs

        # 1. Gather 1-day context
        context_md = await gather_report_context(1)

        # 2. Save to DB as Task assigned to Supervisor
        supabase = get_supabase_client()
        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if not p_res.data:
            logger.warning("Clockwork: No projects found to attach summary task.")
            return

        task_title = f"[Daily Report] Executive Summary ({datetime.now().strftime('%Y-%m-%d')})"
        task_desc = (
            f"昨日系統運行數據如下：\n\n{context_md}\n\n"
            "請啟動星環群聊，協調 Alice, Bob, DevBot 進行討論，最後由 Supervisor (Charlie) 彙整並提供每日執行摘要報告。"
        )

        success, tr = await task_service.create_task(
            project_id=p_res.data[0]["id"], title=task_title, description=task_desc, assignee_id=AgentUUIDs.SUPERVISOR
        )
        if success:
            logger.info(
                f"✅ Clockwork: Created Daily Executive Summary task {tr['task']['id']}. Dispatching Star-topology Group Chat..."
            )
            # 3. Asynchronously trigger the Star-topology Group Chat workflow
            asyncio.create_task(agent_service.run_agent_task(task_id=tr["task"]["id"], agent_id=AgentUUIDs.SUPERVISOR))

            # Record initial log
            supabase.table("archon_logs").insert(
                {
                    "source": "clockwork-scheduler",
                    "level": "INFO",
                    "message": f"Daily Executive Summary group chat dispatched. Task created: {tr['task']['id']}",
                    "details": {
                        "type": "daily_executive_summary",
                        "status": "dispatched",
                    },
                }
            ).execute()

    except Exception as e:
        logger.error(f"💥 Clockwork: Daily Executive Summary generation failed: {e}", exc_info=True)


async def run_weekly_executive_summary():
    """Clockwork task to trigger Map-Reduce for Weekly Executive Summary."""
    logger.info("📊 Clockwork: Triggering Weekly Executive Summary (Map-Reduce)...")
    try:
        from src.agents.workflow.engine_beta_graph import BetaState, beta_graph
        from src.agents.workflow.state import SharedState
        from src.server.services.projects.task_service import task_service
        from src.server.services.shared_constants import AgentUUIDs

        # 1. Gather 7-day context
        context_md = await gather_report_context(7)

        # 2. Initialize State with context as first message
        state = BetaState(shared=SharedState())
        state.shared.messages = [
            {
                "role": "user",
                "content": f"這是過去 7 天的系統運行上下文數據：\n\n{context_md}\n\n請對每個專屬領域（Sales, Marketing, System）進行分析提煉，最後由 Supervisor 彙整並提供高知識品質、具體行動建議的執行摘要。",
            }
        ]

        logger.info("📊 Clockwork: Executing beta_graph Map-Reduce for Weekly summary...")
        from typing import Any

        run_result: Any = await beta_graph.run(deps=None, state=state)
        output = run_result.output if hasattr(run_result, "output") else run_result

        # 3. Save to DB as a completed Task
        supabase = get_supabase_client()
        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if not p_res.data:
            logger.warning("Clockwork: No projects found to attach weekly summary task.")
            return

        task_title = f"[Weekly Report] Executive Summary ({datetime.now().strftime('%Y-%m-%d')})"
        task_desc = str(output)

        # Get Charlie's ID for assignment
        charlie_res = supabase.table("profiles").select("id").eq("email", "charlie@archon.com").execute()
        assignee_id = charlie_res.data[0]["id"] if charlie_res.data else AgentUUIDs.SUPERVISOR

        success, tr = await task_service.create_task(
            project_id=p_res.data[0]["id"], title=task_title, description=task_desc, assignee_id=assignee_id
        )
        if success:
            await task_service.update_task(tr["task"]["id"], {"status": "done"})
            logger.info(f"✅ Clockwork: Created and completed Weekly Executive Summary task {tr['task']['id']}.")

            # Record ROI info to logs
            supabase.table("archon_logs").insert(
                {
                    "source": "clockwork-scheduler",
                    "level": "INFO",
                    "message": f"Weekly Executive Summary completed. Task created: {tr['task']['id']}",
                    "details": {
                        "type": "weekly_executive_summary",
                        "input_tokens": state.shared.input_tokens,
                        "output_tokens": state.shared.output_tokens,
                        "model": state.shared.model_used,
                    },
                }
            ).execute()
    except Exception as e:
        logger.error(f"💥 Clockwork: Weekly Executive Summary generation failed: {e}", exc_info=True)


async def run_monthly_executive_summary():
    """Clockwork task to trigger Map-Reduce for Monthly Executive Summary."""
    logger.info("📊 Clockwork: Triggering Monthly Executive Summary (Map-Reduce)...")
    try:
        from src.agents.workflow.engine_beta_graph import BetaState, beta_graph
        from src.agents.workflow.state import SharedState
        from src.server.services.projects.task_service import task_service
        from src.server.services.shared_constants import AgentUUIDs

        # 1. Gather 30-day context
        context_md = await gather_report_context(30)

        # 2. Initialize State with context as first message
        state = BetaState(shared=SharedState())
        state.shared.messages = [
            {
                "role": "user",
                "content": f"這是過去 30 天的系統運行上下文數據：\n\n{context_md}\n\n請對每個專屬領域（Sales, Marketing, System）進行分析提煉，最後由 Supervisor 彙整並提供高知識品質、具體行動建議的執行摘要。",
            }
        ]

        logger.info("📊 Clockwork: Executing beta_graph Map-Reduce for Monthly summary...")
        from typing import Any

        run_result: Any = await beta_graph.run(deps=None, state=state)
        output = run_result.output if hasattr(run_result, "output") else run_result

        # 3. Save to DB as a completed Task
        supabase = get_supabase_client()
        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if not p_res.data:
            logger.warning("Clockwork: No projects found to attach monthly summary task.")
            return

        task_title = f"[Monthly Report] Executive Summary ({datetime.now().strftime('%Y-%m-%d')})"
        task_desc = str(output)

        # Get Charlie's ID for assignment
        charlie_res = supabase.table("profiles").select("id").eq("email", "charlie@archon.com").execute()
        assignee_id = charlie_res.data[0]["id"] if charlie_res.data else AgentUUIDs.SUPERVISOR

        success, tr = await task_service.create_task(
            project_id=p_res.data[0]["id"], title=task_title, description=task_desc, assignee_id=assignee_id
        )
        if success:
            await task_service.update_task(tr["task"]["id"], {"status": "done"})
            logger.info(f"✅ Clockwork: Created and completed Monthly Executive Summary task {tr['task']['id']}.")

            # Record ROI info to logs
            supabase.table("archon_logs").insert(
                {
                    "source": "clockwork-scheduler",
                    "level": "INFO",
                    "message": f"Monthly Executive Summary completed. Task created: {tr['task']['id']}",
                    "details": {
                        "type": "monthly_executive_summary",
                        "input_tokens": state.shared.input_tokens,
                        "output_tokens": state.shared.output_tokens,
                        "model": state.shared.model_used,
                    },
                }
            ).execute()
    except Exception as e:
        logger.error(f"💥 Clockwork: Monthly Executive Summary generation failed: {e}", exc_info=True)


async def analyze_token_usage():
    """Token Usage Analysis & Proactive Alerting (Phase 4.6.46: Proactive)"""
    logger.info("🤖 Clockwork: Starting Token Usage Analysis...")
    try:
        supabase = get_supabase_client()
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        # Physical Fix: table is token_usage
        res = (
            supabase.table("token_usage")
            .select("input_tokens, output_tokens, cost_usd")
            .gt("created_at", one_day_ago)
            .execute()
        )
        data = res.data or []

        total_tokens = sum((row.get("input_tokens", 0) + row.get("output_tokens", 0)) for row in data)
        total_cost = sum(float(row.get("cost_usd", 0)) for row in data)

        # 1. INFO Log
        logger.info(f"📊 Daily Token Analysis: {total_tokens} physical tokens, ${total_cost:.4f} USD.")

        # 2. PROACTIVE ALERT (Restored Milestone)
        # Alert if cost exceeds threshold (Default $1.0)
        cost_threshold = 1.0
        if total_cost > cost_threshold:
            supabase.table("archon_logs").insert(
                {
                    "source": "sentinel-cost",
                    "level": "ALERT",
                    "message": f"💰 Cost Spike Detected: 24h spend ${total_cost:.2f} > threshold ${cost_threshold:.2f}",
                    "details": {"total_cost": total_cost, "total_tokens": total_tokens, "request_count": len(data)},
                }
            ).execute()

        supabase.table("archon_logs").insert(
            {
                "source": "clockwork-scheduler",
                "level": "INFO",
                "message": f"Daily Token Analysis: {total_tokens} physical tokens",
                "details": {
                    "type": "token_analysis",
                    "period": "24h",
                    "total_tokens": total_tokens,
                    "total_cost": total_cost,
                    "request_count": len(data),
                },
            }
        ).execute()
    except Exception as e:
        logger.error(f"💥 Clockwork: Token Analysis Failed: {e}")


async def run_business_sentinel():
    """Scans leads for staleness with Proactive State Intervention (Restored Phase 4.6.46)."""
    logger.info("🛡️ Clockwork: Starting Business Sentinel...")
    try:
        supabase = get_supabase_client()
        threshold_days = 14
        # Physical Fix: Column name is 'key', not 'setting_key'
        res_settings = (
            supabase.table("archon_settings").select("value").eq("key", "STALE_LEAD_THRESHOLD_DAYS").execute()
        )
        if res_settings.data:
            threshold_days = int(res_settings.data[0]["value"])

        cutoff_date = (datetime.now(UTC) - timedelta(days=threshold_days)).isoformat()
        logger.info(f"🛡️ Sentinel: Scanning for leads updated before {cutoff_date} (threshold={threshold_days}d)")

        seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()

        # 1. Stale Leads with Proactive Intervention
        res = (
            supabase.table("leads")
            .select("id, company_name, updated_at")
            .lt("updated_at", cutoff_date)
            .not_.in_("status", ["won", "converted", "dormant"])
            .limit(20)
            .execute()
        )
        stale_leads = res.data or []
        if not stale_leads:
            logger.info("🛡️ Clockwork: No stale leads found.")
        else:
            log_payloads = []
            for lead in stale_leads:
                # Proactive Action: Mark as dormant to auto-clean Alice's workbench
                supabase.table("leads").update({"status": "dormant"}).eq("id", lead["id"]).execute()

                # Anti-spam: Check if already alerted
                existing = (
                    supabase.table("archon_logs")
                    .select("id")
                    .eq("source", "sentinel")
                    .eq("level", "ALERT")
                    .gt("created_at", seven_days_ago)
                    .filter("details->>lead_id", "eq", str(lead["id"]))
                    .execute()
                )
                if existing.data:
                    continue

                log_payloads.append(
                    {
                        "source": "sentinel",
                        "level": "ALERT",
                        "message": f"Stale Lead Auto-Dormant: {lead['company_name']}",
                        "details": {
                            "type": "stale_lead",
                            "category": "business",
                            "lead_id": lead["id"],
                            "company": lead["company_name"],
                            "action": "status_changed_to_dormant",
                        },
                    }
                )
                logger.info(f"🛡️ Sentinel: Prepared proactive alert for {lead['company_name']}")

            if log_payloads:
                log_res = supabase.table("archon_logs").insert(log_payloads).execute()
                if log_res.data:
                    try:
                        import asyncio

                        from src.server.services.projects.task_service import task_service

                        for log_record in log_res.data:
                            log_id = log_record["id"]
                            asyncio.create_task(
                                task_service.generate_task_from_alert(alert_id=str(log_id), assignee_id=None)
                            )
                    except Exception as task_err:
                        logger.error(f"🛡️ Sentinel: Failed to auto-generate tasks from alerts: {task_err}")

        # 2. Content Bottlenecks (GAP-029)
        forty_eight_hours_ago = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
        post_res = (
            supabase.table("blog_posts")
            .select("id, title, updated_at")
            .eq("status", "review")
            .lt("updated_at", forty_eight_hours_ago)
            .execute()
        )
        posts = post_res.data or []
        log_payloads = []
        for post in posts:
            # Anti-spam
            existing_p = (
                supabase.table("archon_logs")
                .select("id")
                .eq("source", "sentinel")
                .eq("level", "ALERT")
                .gt("created_at", seven_days_ago)
                .filter("details->>post_id", "eq", str(post["id"]))
                .execute()
            )
            if existing_p.data:
                continue

            log_payloads.append(
                {
                    "source": "sentinel",
                    "level": "ALERT",
                    "message": f"Content Bottleneck: '{post['title']}' stuck in review",
                    "details": {
                        "type": "content_bottleneck",
                        "category": "business",
                        "post_id": post["id"],
                        "title": post["title"],
                    },
                }
            )
            logger.info(f"🛡️ Sentinel: Prepared bottleneck alert for {post['title']}")

        if log_payloads:
            supabase.table("archon_logs").insert(log_payloads).execute()
    except Exception as e:
        logger.error(f"💥 Clockwork: Business Sentinel Failed: {e}", exc_info=True)


async def run_api_deprecation_scan():
    """Bi-weekly scan of Google's Gemini API Docs to check for deprecations and limit changes."""
    logger.info("🔍 Clockwork: Starting API Deprecation & Limit Scan...")
    try:
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service
        from src.server.services.shared_constants import AI_AGENT_ROLES

        supabase = get_supabase_client()

        task_title = f"Auto-Scan: Gemini API Deprecations & Quotas ({datetime.now(UTC).strftime('%Y-%m-%d')})"
        task_desc = (
            "Clockwork has initiated the bi-weekly scan of Google's Gemini API documentation.\n\n"
            "Please use your RAG and Web capabilities to extract the latest information regarding:\n"
            "1. Model Deprecations (e.g., gemini-3.1-flash-lite, gemini-3-flash-preview).\n"
            "2. Free Tier API Rate Limits (RPD, RPM) for the Gemini 3/3.1 series.\n\n"
            "Provide a summary of any changes that might affect our system stability."
        )

        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if not p_res.data:
            logger.warning("Clockwork: No projects found to attach API scan task.")
            return

        project_id = p_res.data[0]["id"]

        success, task_result = await task_service.create_task(
            project_id=project_id,
            title=task_title,
            description=task_desc,
            assignee_id=AI_AGENT_ROLES.get("Librarian (Research)") or "ai-librarian",
        )

        if success:
            logger.info(f"🔍 Clockwork: Created API scan task {task_result['task']['id']}. Dispatching Librarian...")
            await agent_service.run_agent_task(
                task_id=task_result["task"]["id"], agent_id=task_result["task"]["assignee_id"]
            )

            supabase.table("archon_logs").insert(
                {
                    "source": "clockwork-scheduler",
                    "level": "INFO",
                    "message": "Dispatched Bi-Weekly API Limit & Deprecation Scan to Librarian",
                }
            ).execute()

    except Exception as e:
        logger.error(f"💥 Clockwork: API Scan Failed: {e}", exc_info=True)
