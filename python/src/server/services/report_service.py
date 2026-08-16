"""
Report Service (Phase 5.9.5: L2 Code Governance Refactoring)
Handles business data context gathering, Map-Reduce workflows, and periodic summaries.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from src.server.config.logfire_config import get_logger
from src.server.repositories.base_repository import BaseRepository
from src.server.services.shared_constants import AgentUUIDs

logger = get_logger(__name__)
CST = ZoneInfo("Asia/Taipei")


class ReportService(BaseRepository):
    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client)

    def _get_leads_context(self, cutoff_date: str) -> str:
        query = self.supabase_client.table("leads").select("company_name, job_title, status").gt("created_at", cutoff_date) # 合法
        success, leads_res = self.execute_query(query, "Failed to get leads")
        leads = leads_res.get("data", []) if success else []
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
        return leads_summary

    def _get_token_context(self, cutoff_date: str) -> str:
        query = self.supabase_client.table("token_usage").select("input_tokens, output_tokens, cost_usd").gt("created_at", cutoff_date) # 合法
        success, token_res = self.execute_query(query, "Failed to get token usage")
        token_data = token_res.get("data", []) if success else []
        total_input = sum(row.get("input_tokens", 0) or 0 for row in token_data)
        total_output = sum(row.get("output_tokens", 0) or 0 for row in token_data)
        total_cost = sum(float(row.get("cost_usd", 0.0) or 0.0) for row in token_data)
        return (
            f"API Request Count: {len(token_data)}\n"
            f"Input Tokens: {total_input}\n"
            f"Output Tokens: {total_output}\n"
            f"Total Cost: ${total_cost:.4f} USD"
        )

    def _get_logs_context(self, cutoff_date: str) -> str:
        query = self.supabase_client.table("archon_logs").select("level, message, source, created_at").gt("created_at", cutoff_date).in_("level", ["ALERT", "ERROR"]) # 合法
        success, logs_res = self.execute_query(query, "Failed to get alerts")
        logs = logs_res.get("data", []) if success else []
        logs_summary = f"Total Alerts/Errors: {len(logs)}\n"
        if logs:
            logs_summary += "Recent Alerts/Errors:\n" + "\n".join(
                f"- [{log['level']}] {log['source']}: {log['message']} ({log['created_at']})" for log in logs[:10]
            )
            if len(logs) > 10:
                logs_summary += f"\n... and {len(logs) - 10} more alerts."
        else:
            logs_summary += "No critical alerts/errors."
        return logs_summary

    def _get_tasks_context(self, cutoff_date: str) -> str:
        query = self.supabase_client.table("archon_tasks").select("title, status, assignee").gt("updated_at", cutoff_date) # 合法
        success, tasks_res = self.execute_query(query, "Failed to get tasks updated")
        tasks = tasks_res.get("data", []) if success else []
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
        return tasks_summary

    async def gather_report_context(self, days: int) -> str:
        """Gathers database metrics and events from the last N days to ground periodic summaries."""
        logger.info(f"📊 Gathering report context for the past {days} day(s)...")
        try:
            now = datetime.now(UTC)
            cutoff_date = (now - timedelta(days=days)).isoformat()

            leads_summary = self._get_leads_context(cutoff_date)
            token_summary = self._get_token_context(cutoff_date)
            logs_summary = self._get_logs_context(cutoff_date)
            tasks_summary = self._get_tasks_context(cutoff_date)

            from src.server.services.prompt_service import prompt_service

            prompt_template = prompt_service.get_prompt("REPORT_CONTEXT_PROMPT")
            return prompt_template.format(
                end_date_str=now.strftime('%Y-%m-%d'),
                start_date_str=(now - timedelta(days=days)).strftime('%Y-%m-%d'),
                days=days,
                leads_summary=leads_summary,
                token_summary=token_summary,
                logs_summary=logs_summary,
                tasks_summary=tasks_summary
            )
        except Exception as e:
            logger.error(f"Failed to gather report context: {e}", exc_info=True)
            from src.server.services.prompt_service import prompt_service
            return prompt_service.get_prompt("REPORT_CONTEXT_FALLBACK")

    async def _create_summary_task_and_log(
        self,
        days: int,
        title_prefix: str,
        task_desc: str,
        log_details: dict[str, Any],
        auto_complete: bool = False,
        dispatch_agent: bool = False,
        feature: str | None = None,
    ) -> None:
        import asyncio

        from src.server.schemas.settings import NetworkConfig
        from src.server.services.projects.task_service import task_service
        from src.server.services.system.telegram_service import telegram_service

        query = self.supabase_client.table("archon_projects").select("id").limit(1) # 合法
        success, p_res = self.execute_query(query, "Failed to get projects")
        if not success or not p_res.get("data"):
            logger.warning(f"ReportService: No projects found to attach {title_prefix} summary task.")
            return

        p_id = p_res["data"][0]["id"]

        assignee_id = AgentUUIDs.SUPERVISOR

        end_date = datetime.now(CST)
        start_date = end_date - timedelta(days=days)
        task_title = f"[{title_prefix}] Executive Summary ({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})"

        success, tr = await task_service.create_task(
            project_id=p_id, title=task_title, description=task_desc, assignee_id=assignee_id, feature=feature
        )
        if success:
            task_id = tr["task"]["id"]
            if auto_complete:
                await task_service.update_task(task_id, {"status": "done"})
                logger.info(f"✅ ReportService: Created and completed {title_prefix} Executive Summary task {task_id}.")
            else:
                logger.info(f"✅ ReportService: Created {title_prefix} Executive Summary task {task_id}.")

            if dispatch_agent:
                from src.server.services.agent_service import agent_service
                logger.info(f"Dispatching Group Chat for {task_id}...")
                asyncio.create_task(agent_service.run_agent_task(task_id=task_id, agent_id=assignee_id))

            insert_query = self.supabase_client.table("archon_logs").insert( # 合法
                {
                    "source": "report-service", "level": "INFO",
                    "message": f"{title_prefix} Executive Summary processed. Task: {task_id}",
                    "details": log_details,
                }
            )
            self.execute_query(insert_query, "Failed to record summary log")

            frontend_url = NetworkConfig().frontend_url
            telegram_msg = (
                f"🚨 **[Archon 系統通知] 星環 {title_prefix} 已產出**\n"
                f"* 日期區間: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}\n"
                f"* 狀態: 已指派給 Charlie\n"
                f"👉 請登入 Admin UI 查看詳細數據與表格：[點擊前往]({frontend_url}/#/dashboard?taskId={task_id})"
            )
            is_sent = await telegram_service.send_message(telegram_msg)
            if not is_sent:
                logger.warning(f"⚠️ ReportService: Failed to send Telegram notification (Task {task_id} was still created). Network timeout or invalid token.")
        else:
            error_msg = f"ReportService: Failed to create {title_prefix} summary task."
            logger.error(f"❌ {error_msg} Task service returned success=False.")
            raise Exception(error_msg)

    async def generate_daily_executive_summary(self) -> None:
        """Triggers Star-topology Group Chat for Daily Executive Summary."""
        logger.info("📊 ReportService: Triggering Daily Executive Summary (Group Chat)...")
        try:
            from src.server.services.prompt_service import prompt_service
            from src.server.services.shared_constants import TaskFeatureEnum

            context_md = await self.gather_report_context(1)
            prompt_template = prompt_service.get_prompt("DAILY_EXECUTIVE_SUMMARY_PROMPT")
            task_desc = prompt_template.format(context_md=context_md)

            await self._create_summary_task_and_log(
                days=1,
                title_prefix="Daily",
                task_desc=task_desc,
                log_details={"type": "daily_executive_summary", "status": "dispatched"},
                dispatch_agent=True,
                feature=TaskFeatureEnum.DAILY_EXECUTIVE_SUMMARY.value
            )
        except Exception as e:
            logger.error(f"💥 ReportService: Daily Executive Summary generation failed: {e}", exc_info=True)
            raise e

    async def _execute_map_reduce_summary(self, days: int, title_prefix: str, prompt_key: str) -> None:
        logger.info(f"📊 ReportService: Triggering {title_prefix} (Map-Reduce)...")
        try:
            from src.agents.workflow.engine_beta_graph import BetaState, beta_graph
            from src.agents.workflow.state import SharedState
            from src.server.services.prompt_service import prompt_service
            from src.server.services.report_enrichment_service import report_enrichment_service

            context_md = await self.gather_report_context(days)
            context_md = await report_enrichment_service.inject_nexus_oracle_insights(context_md)

            state = BetaState(shared=SharedState())
            prompt_template = prompt_service.get_prompt(prompt_key)
            prompt_content = prompt_template.replace("{context_md}", context_md)
            state.shared.messages = [{"role": "user", "content": prompt_content}]

            logger.info(f"📊 ReportService: Executing beta_graph Map-Reduce for {title_prefix} summary...")
            run_result: Any = await beta_graph.run(deps=None, state=state)
            output = run_result.output if hasattr(run_result, "output") else run_result

            task_desc = str(output)
            task_desc = await report_enrichment_service.attach_podcast_audio(task_desc)

            log_type = f"{title_prefix.lower().replace(' ', '_')}_executive_summary"
            log_details = {
                "type": log_type,
                "input_tokens": state.shared.input_tokens,
                "output_tokens": state.shared.output_tokens,
                "model": state.shared.model_used,
            }

            await self._create_summary_task_and_log(
                days=days,
                title_prefix=title_prefix,
                task_desc=task_desc,
                log_details=log_details,
                auto_complete=True
            )
        except Exception as e:
            logger.error(f"💥 ReportService: {title_prefix} Executive Summary generation failed: {e}", exc_info=True)
            raise e

    async def generate_weekly_executive_summary(self) -> None:
        await self._execute_map_reduce_summary(7, "Weekly", "WEEKLY_EXECUTIVE_SUMMARY")

    async def generate_monthly_executive_summary(self) -> None:
        await self._execute_map_reduce_summary(30, "Monthly", "MONTHLY_EXECUTIVE_SUMMARY")

report_service = ReportService()
