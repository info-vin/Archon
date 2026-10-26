"""
Report Service (Phase 5.9.5: L2 Code Governance Refactoring)
Handles business data context gathering, Map-Reduce workflows, and periodic summaries.
"""

from datetime import UTC, datetime, timedelta
from typing import Any, NotRequired, TypedDict, cast
from zoneinfo import ZoneInfo

from supabase import Client

from src.server.config.logfire_config import get_logger
from src.server.repositories.base_repository import BaseRepository
from src.server.services.shared_constants import AgentUUIDs, PromptNameEnum

logger = get_logger(__name__)
CST = ZoneInfo("Asia/Taipei")


class LeadRecordDTO(TypedDict):
    company_name: str
    job_title: str
    status: str
    enrichment_score: NotRequired[int | None]
    identified_need: NotRequired[str | None]

class BlogRecordDTO(TypedDict):
    title: str
    status: str
    ai_score: NotRequired[int | None]

class TokenRecordDTO(TypedDict):
    input_tokens: NotRequired[int | None]
    output_tokens: NotRequired[int | None]
    cost_usd: NotRequired[float | str | None]

class LogRecordDTO(TypedDict):
    level: str
    message: str
    source: str
    created_at: str

class TaskRecordDTO(TypedDict):
    title: str
    status: str
    assignee: str

class SummaryLogDetailsDTO(TypedDict):
    type: str
    status: NotRequired[str | None]
    input_tokens: NotRequired[int | None]
    output_tokens: NotRequired[int | None]
    model: NotRequired[str | None]


class ReportService(BaseRepository):
    def __init__(self, supabase_client: Client | None = None) -> None:
        super().__init__(supabase_client)

    def _format_lead_line(self, lead: LeadRecordDTO) -> str:
        base = f"- {lead.get('company_name', 'N/A')} ({lead.get('job_title', 'N/A')}) -> {lead.get('status', 'N/A')}"
        score = lead.get("enrichment_score")
        need = str(lead.get("identified_need") or "").replace("\n", " ").strip()
        if score:
            base += f" [Score: {score}]"
        if need:
            base += f" | 痛點: {need[:100]}"
        return base

    def _get_leads_context(self, cutoff_date: str) -> str:
        query = self.supabase_client.table("leads").select("company_name, job_title, status, enrichment_score, identified_need").gt("created_at", cutoff_date) # 合法
        success, leads_res = self.execute_query(query, "Failed to get leads")
        raw_leads = leads_res.get("data") if success and isinstance(leads_res, dict) else None
        leads: list[LeadRecordDTO] = cast(list[LeadRecordDTO], raw_leads) if isinstance(raw_leads, list) else []
        leads_summary = f"Total New Leads: {len(leads)}\n"
        if leads:
            lead_status_counts: dict[str, int] = {}
            for lead in leads:
                status_key = lead.get("status", "unknown")
                lead_status_counts[status_key] = lead_status_counts.get(status_key, 0) + 1
            leads_summary += "Status Breakdown: " + ", ".join(f"{k}: {v}" for k, v in lead_status_counts.items()) + "\n"
            leads_summary += "Recent Leads Sample:\n" + "\n".join(self._format_lead_line(lead) for lead in leads[:10])
            if len(leads) > 10:
                leads_summary += f"\n... and {len(leads) - 10} more leads."
        else:
            leads_summary += "No new leads found."

        # Enrich with active Qualified Leads pool so daily summary sees actionable pipeline even on 0-new-lead days
        q_query = self.supabase_client.table("leads").select("company_name, job_title, status, enrichment_score, identified_need").eq("status", "qualified").order("enrichment_score", desc=True).limit(5) # 合法
        q_ok, q_res = self.execute_query(q_query, "Failed to get qualified leads pool")
        raw_q = q_res.get("data") if q_ok and isinstance(q_res, dict) else None
        q_leads: list[LeadRecordDTO] = cast(list[LeadRecordDTO], raw_q) if isinstance(raw_q, list) else []
        if q_leads:
            leads_summary += f"\n\nActive Qualified Leads Pool (待跟進高意向潛客庫存, Top {len(q_leads)}):\n"
            leads_summary += "\n".join(self._format_lead_line(ql) for ql in q_leads)

        # Enrich with Bob's Marketing Blog Pipeline
        b_query = self.supabase_client.table("blog_posts").select("title, status, ai_score").order("created_at", desc=True).limit(20) # 合法
        b_ok, b_res = self.execute_query(b_query, "Failed to get blog posts context")
        raw_b = b_res.get("data") if b_ok and isinstance(b_res, dict) else None
        blogs: list[BlogRecordDTO] = cast(list[BlogRecordDTO], raw_b) if isinstance(raw_b, list) else []
        if blogs:
            blog_counts: dict[str, int] = {}
            for b in blogs:
                b_status = str(b.get("status", "unknown"))
                blog_counts[b_status] = blog_counts.get(b_status, 0) + 1
            b_breakdown = ", ".join(f"{k}: {v}" for k, v in blog_counts.items())
            leads_summary += f"\n\nMarketing Content Pipeline (Bob 部落格內容資產): Total Sampled: {len(blogs)} ({b_breakdown})\n"
            leads_summary += "Recent Blog Posts:\n" + "\n".join(
                f"- {b.get('title', 'Untitled')} -> status: {b.get('status', 'N/A')} [AI Score: {b.get('ai_score', 'N/A')}]" for b in blogs[:4]
            )
        return leads_summary

    def _get_token_context(self, cutoff_date: str) -> str:
        query = self.supabase_client.table("token_usage").select("input_tokens, output_tokens, cost_usd").gt("created_at", cutoff_date) # 合法
        success, token_res = self.execute_query(query, "Failed to get token usage")
        token_data: list[TokenRecordDTO] = cast(list[TokenRecordDTO], token_res.get("data", [])) if success and isinstance(token_res, dict) and token_res.get("data") else []
        total_input = sum(row.get("input_tokens", 0) or 0 for row in token_data)
        total_output = sum(row.get("output_tokens", 0) or 0 for row in token_data)
        total_cost = sum(float(row.get("cost_usd", 0.0) or 0.0) for row in token_data)
        return f"API Request Count: {len(token_data)}\nInput Tokens: {total_input}\nOutput Tokens: {total_output}\nTotal Cost: ${total_cost:.4f} USD"

    def _get_logs_context(self, cutoff_date: str) -> str:
        from collections import Counter

        query = self.supabase_client.table("archon_logs").select("level, message, source, created_at").gt("created_at", cutoff_date).in_("level", ["ALERT", "ERROR"]) # 合法
        success, logs_res = self.execute_query(query, "Failed to get alerts")
        logs: list[LogRecordDTO] = cast(list[LogRecordDTO], logs_res.get("data", [])) if success and isinstance(logs_res, dict) and logs_res.get("data") else []
        logs_summary = f"Total Alerts/Errors: {len(logs)}\n"
        if logs:
            counts: Counter[tuple[str, str, str]] = Counter()
            latest_time: dict[tuple[str, str, str], str] = {}
            for log in logs:
                level, source, msg = str(log.get("level", "N/A")), str(log.get("source", "N/A")), str(log.get("message", "N/A"))
                first_line = msg.split("\n")[0].strip()
                if len(first_line) > 120:
                    first_line = first_line[:117] + "..."
                sig = (level, source, first_line)
                counts[sig] += 1
                if sig not in latest_time:
                    latest_time[sig] = str(log.get("created_at", "N/A"))
            logs_summary += "Recent Alerts/Errors (Aggregated):\n"
            for (level, source, first_line), count in counts.most_common(8):
                clean_msg = first_line.replace("`", "'")
                repeat_suffix = f" (x{count})" if count > 1 else ""
                logs_summary += f"- [{level}] {source}: `{clean_msg}`{repeat_suffix} ({latest_time[(level, source, first_line)]})\n"
            if len(counts) > 8:
                logs_summary += f"... and {len(counts) - 8} more alert signatures.\n"
        else:
            logs_summary += "No critical alerts/errors."
        return logs_summary.strip()

    def _get_tasks_context(self, cutoff_date: str) -> str:
        query = self.supabase_client.table("archon_tasks").select("title, status, assignee").gt("updated_at", cutoff_date) # 合法
        success, tasks_res = self.execute_query(query, "Failed to get tasks updated")
        tasks: list[TaskRecordDTO] = cast(list[TaskRecordDTO], tasks_res.get("data", [])) if success and isinstance(tasks_res, dict) and tasks_res.get("data") else []
        tasks_summary = f"Total Tasks Active/Updated: {len(tasks)}\n"
        if tasks:
            task_status_counts: dict[str, int] = {}
            for t in tasks:
                status_key = t.get("status", "unknown")
                task_status_counts[status_key] = task_status_counts.get(status_key, 0) + 1
            tasks_summary += "Status Breakdown: " + ", ".join(f"{k}: {v}" for k, v in task_status_counts.items()) + "\n"
            tasks_summary += "Tasks List:\n" + "\n".join(f"- {t.get('title', 'N/A')} ({t.get('assignee', 'N/A')}) -> status: {t.get('status', 'N/A')}" for t in tasks[:10])
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
                end_date_str=now.strftime('%Y-%m-%d'), start_date_str=(now - timedelta(days=days)).strftime('%Y-%m-%d'),
                days=days, leads_summary=leads_summary, token_summary=token_summary,
                logs_summary=logs_summary, tasks_summary=tasks_summary,
            )
        except Exception as e:
            logger.error(f"Failed to gather report context: {e}", exc_info=True)
            from src.server.services.prompt_service import prompt_service
            return prompt_service.get_prompt("REPORT_CONTEXT_FALLBACK")

    async def _create_summary_task_and_log(
        self, days: int, title_prefix: str, task_desc: str,
        log_details: SummaryLogDetailsDTO | dict[str, Any],
        auto_complete: bool = False, dispatch_agent: bool = False, feature: str | None = None,
    ) -> None:
        import asyncio

        from src.server.services.projects.task_service import task_service

        query = self.supabase_client.table("archon_projects").select("id").limit(1) # 合法
        success, p_res = self.execute_query(query, "Failed to get projects")
        if not success or not isinstance(p_res, dict) or not p_res.get("data"):
            logger.warning(f"ReportService: No projects found to attach {title_prefix} summary task.")
            return
        p_id, assignee_id = p_res["data"][0]["id"], AgentUUIDs.SUPERVISOR
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
            logger.info(f"✅ ReportService: Created {title_prefix} Executive Summary task {task_id}.")
            if dispatch_agent:
                from src.server.services.agent_service import agent_service
                asyncio.create_task(agent_service.run_agent_task(task_id=task_id, agent_id=assignee_id))
            insert_query = self.supabase_client.table("archon_logs").insert( # 合法
                {
                    "source": "report-service", "level": "INFO",
                    "message": f"{title_prefix} Executive Summary processed. Task: {task_id}",
                    "details": cast(dict[str, Any], log_details),
                }
            )
            self.execute_query(insert_query, "Failed to record summary log")
            if not dispatch_agent:
                await self.send_summary_telegram(
                    title_prefix=title_prefix, content=task_desc, task_id=task_id, start_date=start_date, end_date=end_date
                )
        else:
            error_msg = f"ReportService: Failed to create {title_prefix} summary task."
            logger.error(f"❌ {error_msg} Task service returned success=False.")
            raise Exception(error_msg)

    async def send_summary_telegram(
        self, title_prefix: str, content: str, task_id: str,
        start_date: datetime | None = None, end_date: datetime | None = None,
    ) -> bool:
        """Dispatches finished executive summary content to Telegram with Admin UI deep link and Dual-Voice Briefings."""
        from src.server.schemas.settings import NetworkConfig
        from src.server.services.report_enrichment_service import report_enrichment_service
        from src.server.services.system.telegram_service import telegram_service

        frontend_url = NetworkConfig().frontend_url
        date_str = f"📅 區間: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}\n\n" if start_date and end_date else ""
        telegram_msg = (
            f"🚨 **[Archon 系統通知] 星環 {title_prefix} 已產出**\n{date_str}{content.strip()}\n\n"
            f"👉 完整數據與儀表板請至 Admin UI 查看：[點擊前往]({frontend_url}/#/dashboard?taskId={task_id})"
        )
        is_sent = await telegram_service.send_message(telegram_msg)
        if title_prefix == "Daily":
            await report_enrichment_service.dispatch_dual_voice_briefings(content)
        elif "Fallback" in title_prefix:
            await report_enrichment_service.trigger_emergency_voice_alert(content)
        return is_sent

    def _inject_steering_focus(self, context_md: str) -> str:
        """Appends Management Steering Focus from settings if configured."""
        from src.server.schemas.settings import SchedulerConfig
        from src.server.services.settings_service import SettingsService

        steering_focus: str | None = None
        try:
            all_settings = SettingsService(self.supabase_client).get_all_settings()
            if isinstance(all_settings, dict):
                raw_focus = all_settings.get("MANAGEMENT_STEERING_FOCUS")
                if raw_focus and isinstance(raw_focus, str) and raw_focus.strip():
                    steering_focus = raw_focus.strip()
                else:
                    steering_focus = SchedulerConfig.model_validate(all_settings).management_steering_focus
        except Exception as conf_err:
            logger.warning(f"ReportService: Failed to parse SchedulerConfig for steering focus: {conf_err}")

        if steering_focus and steering_focus.strip():
            context_md += f"\n\n### 🎯 管理者戰略關注焦點 (Management Steering Focus)\n{steering_focus.strip()}\n"
        return context_md

    async def generate_daily_executive_summary(self) -> None:
        """Triggers Star-topology Group Chat for Daily Executive Summary."""
        logger.info("📊 ReportService: Triggering Daily Executive Summary (Group Chat)...")
        try:
            from src.server.services.prompt_service import prompt_service
            from src.server.services.shared_constants import TaskFeatureEnum

            context_md = self._inject_steering_focus(await self.gather_report_context(1))
            task_desc = prompt_service.get_prompt("DAILY_EXECUTIVE_SUMMARY_PROMPT").format(context_md=context_md)
            await self._create_summary_task_and_log(
                days=1, title_prefix="Daily", task_desc=task_desc,
                log_details={"type": "daily_executive_summary", "status": "dispatched"},
                dispatch_agent=True, feature=TaskFeatureEnum.DAILY_EXECUTIVE_SUMMARY.value,
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

            context_md = self._inject_steering_focus(await report_enrichment_service.inject_nexus_oracle_insights(await self.gather_report_context(days)))

            state = BetaState(shared=SharedState())
            state.worker_targets = ["sales", "marketing", "system"] # 合法
            state.worker_prompts = {
                "sales": PromptNameEnum.MAP_REDUCE_ALICE_PROMPT,
                "marketing": PromptNameEnum.MAP_REDUCE_BOB_PROMPT,
                "system": PromptNameEnum.MAP_REDUCE_SYSTEM_PROMPT,
            }
            state.reducer_prompt_name = PromptNameEnum.MAP_REDUCE_SUPERVISOR_PROMPT
            state.shared.messages = [{"role": "user", "content": prompt_service.get_prompt(prompt_key).replace("{context_md}", context_md)}]

            logger.info(f"📊 ReportService: Executing beta_graph Map-Reduce for {title_prefix} summary...")
            run_result: Any = await beta_graph.run(deps=None, state=state)
            output = run_result.output if hasattr(run_result, "output") else run_result
            task_desc = await report_enrichment_service.attach_podcast_audio(str(output))

            log_type = f"{title_prefix.lower().replace(' ', '_')}_executive_summary"
            log_details: SummaryLogDetailsDTO = {
                "type": log_type, "input_tokens": state.shared.input_tokens,
                "output_tokens": state.shared.output_tokens, "model": state.shared.model_used,
            }
            await self._create_summary_task_and_log(
                days=days, title_prefix=title_prefix, task_desc=task_desc, log_details=log_details, auto_complete=True
            )
        except Exception as e:
            logger.error(f"💥 ReportService: {title_prefix} Executive Summary generation failed: {e}", exc_info=True)
            raise e

    async def generate_weekly_executive_summary(self) -> None:
        await self._execute_map_reduce_summary(7, "Weekly", "WEEKLY_EXECUTIVE_SUMMARY")

    async def generate_monthly_executive_summary(self) -> None:
        await self._execute_map_reduce_summary(30, "Monthly", "MONTHLY_EXECUTIVE_SUMMARY")


report_service = ReportService()
