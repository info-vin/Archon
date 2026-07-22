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
    def __init__(self, supabase_client=None):
        super().__init__(supabase_client)

    def _get_leads_context(self, cutoff_date: str) -> str:
        success, leads_res = self.execute_query(
            lambda: self.supabase_client.table("leads").select("company_name, job_title, status").gt("created_at", cutoff_date).execute(),
            "Failed to get leads"
        )
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
        success, token_res = self.execute_query(
            lambda: self.supabase_client.table("token_usage").select("input_tokens, output_tokens, cost_usd").gt("created_at", cutoff_date).execute(),
            "Failed to get token usage"
        )
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
        success, logs_res = self.execute_query(
            lambda: self.supabase_client.table("archon_logs").select("level, message, source, created_at").gt("created_at", cutoff_date).in_("level", ["ALERT", "ERROR"]).execute(),
            "Failed to get alerts"
        )
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
        success, tasks_res = self.execute_query(
            lambda: self.supabase_client.table("archon_tasks").select("title, status, assignee").gt("updated_at", cutoff_date).execute(),
            "Failed to get tasks updated"
        )
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

            return f"""### 系統運行上下文數據

**資料區間**：{now.strftime('%Y-%m-%d')} 前推 {days} 天 (從 {(now - timedelta(days=days)).strftime('%Y-%m-%d')} 至 {now.strftime('%Y-%m-%d')})
**報告產出日期**：{now.strftime('%Y-%m-%d')}

#### 1. 商業開發線告 (Leads)
{leads_summary}

#### 2. AI 運算用量與成本 (Token Usage)
{token_summary}

#### 3. 系統警示與異常紀錄 (Archon Logs)
{logs_summary}

#### 4. 專案任務狀態異動 (Archon Tasks)
{tasks_summary}
"""
        except Exception as e:
            logger.error(f"Failed to gather report context: {e}", exc_info=True)
            return "無法取得系統運行數據，請以無上下文模式進行總結。"

    async def generate_daily_executive_summary(self) -> None:
        """Triggers Star-topology Group Chat for Daily Executive Summary."""
        logger.info("📊 ReportService: Triggering Daily Executive Summary (Group Chat)...")
        try:
            import asyncio

            from src.server.services.agent_service import agent_service
            from src.server.services.projects.task_service import task_service

            context_md = await self.gather_report_context(1)
            supabase = self.supabase_client

            success, p_res = self.execute_query(
                lambda: supabase.table("archon_projects").select("id").limit(1).execute(),
                "Failed to get projects"
            )
            if not success or not p_res.get("data"):
                logger.warning("ReportService: No projects found to attach summary task.")
                return

            end_date = datetime.now(CST)
            start_date = end_date - timedelta(days=1)
            task_title = f"[Daily] Executive Summary ({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})"
            fallback_str = (
                "昨日系統運行數據如下：\n\n{context_md}\n\n"
                "請啟動星環群聊，協調 Alice, Bob, DevBot 進行討論，最後由 Supervisor (Charlie) 彙整並提供每日執行摘要報告。"
            )

            from src.server.services.prompt_service import prompt_service
            prompt_template = prompt_service.get_prompt("DAILY_EXECUTIVE_SUMMARY_PROMPT", default=fallback_str)
            task_desc = prompt_template.format(context_md=context_md)

            success, charlie_res = self.execute_query(
                lambda: supabase.table("profiles").select("id").eq("email", "charlie@archon.com").execute(),
                "Failed to get charlie's id"
            )
            charlie_data = charlie_res.get("data", []) if success else []
            assignee_id = charlie_data[0]["id"] if charlie_data else AgentUUIDs.SUPERVISOR
            p_id = p_res.get("data", [])[0]["id"] if p_res.get("data") else ""

            success, tr = await task_service.create_task(
                project_id=p_id, title=task_title, description=task_desc, assignee_id=assignee_id
            )
            if success:
                logger.info(f"✅ ReportService: Created Daily Executive Summary task {tr['task']['id']}. Dispatching Group Chat...")
                asyncio.create_task(agent_service.run_agent_task(task_id=tr["task"]["id"], agent_id=AgentUUIDs.SUPERVISOR))
                self.execute_query(
                    lambda: supabase.table("archon_logs").insert(
                        {
                            "source": "report-service", "level": "INFO",
                            "message": f"Daily Executive Summary group chat dispatched. Task created: {tr['task']['id']}",
                            "details": {"type": "daily_executive_summary", "status": "dispatched"},
                        }
                    ).execute(),
                    "Failed to record daily summary log"
                )
        except Exception as e:
            logger.error(f"💥 ReportService: Daily Executive Summary generation failed: {e}", exc_info=True)

    async def _execute_map_reduce_summary(self, days: int, title_prefix: str, prompt_key: str, default_prompt: str) -> None:
        logger.info(f"📊 ReportService: Triggering {title_prefix} (Map-Reduce)...")
        try:
            from src.agents.workflow.engine_beta_graph import BetaState, beta_graph
            from src.agents.workflow.state import SharedState
            from src.server.services.projects.task_service import task_service
            from src.server.services.prompt_service import prompt_service
            from src.server.services.report_enrichment_service import report_enrichment_service

            context_md = await self.gather_report_context(days)
            context_md = await report_enrichment_service.inject_nexus_oracle_insights(context_md)

            state = BetaState(shared=SharedState())
            prompt_template = prompt_service.get_prompt(prompt_key, default=default_prompt)
            prompt_content = prompt_template.replace("{context_md}", context_md)
            state.shared.messages = [{"role": "user", "content": prompt_content}]

            logger.info(f"📊 ReportService: Executing beta_graph Map-Reduce for {title_prefix} summary...")
            run_result: Any = await beta_graph.run(deps=None, state=state)
            output = run_result.output if hasattr(run_result, "output") else run_result

            success, p_res = self.execute_query(
                lambda: self.supabase_client.table("projects").select("id").limit(1).execute(),
                "Failed to get internal project", require_data=True
            )
            # fallback to archon_projects if projects doesn't exist
            if not success or not p_res.get("data"):
                success, p_res = self.execute_query(
                    lambda: self.supabase_client.table("archon_projects").select("id").limit(1).execute(),
                    "Failed to get projects fallback", require_data=True
                )
                if not success or not p_res.get("data"):
                    logger.warning(f"ReportService: No internal project found to attach {title_prefix} summary task.")
                    return

            end_date = datetime.now(CST)
            start_date = end_date - timedelta(days=days)
            task_title = f"[{title_prefix}] Executive Summary ({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})"
            task_desc = str(output)
            task_desc = await report_enrichment_service.attach_podcast_audio(task_desc)

            success, charlie_res = self.execute_query(
                lambda: self.supabase_client.table("profiles").select("id").eq("email", "charlie@archon.com").execute(),
                "Failed to get charlie's id"
            )
            assignee_id = charlie_res.get("data", [])[0]["id"] if (success and charlie_res.get("data")) else AgentUUIDs.SUPERVISOR
            p_id = p_res.get("data", [])[0]["id"] if p_res.get("data") else ""

            success, tr = await task_service.create_task(
                project_id=p_id, title=task_title, description=task_desc, assignee_id=assignee_id
            )
            if success:
                await task_service.update_task(tr["task"]["id"], {"status": "done"})
                logger.info(f"✅ ReportService: Created and completed {title_prefix} Executive Summary task {tr['task']['id']}.")
                log_type = f"{title_prefix.lower().replace(' ', '_')}_executive_summary"
                self.execute_query(
                    lambda: self.supabase_client.table("archon_logs").insert(
                        {
                            "source": "report-service", "level": "INFO",
                            "message": f"{title_prefix} Executive Summary completed. Task created: {tr['task']['id']}",
                            "details": {
                                "type": log_type,
                                "input_tokens": state.shared.input_tokens,
                                "output_tokens": state.shared.output_tokens,
                                "model": state.shared.model_used,
                            },
                        }
                    ).execute(),
                    "Failed to record summary log"
                )
        except Exception as e:
            logger.error(f"💥 ReportService: {title_prefix} Executive Summary generation failed: {e}", exc_info=True)

    async def generate_weekly_executive_summary(self) -> None:
        default_prompt = "這是過去 7 天的系統運行上下文數據：\n\n{context_md}\n\n請對每個專屬領域（Sales, Marketing, System, **Engineering/DevBot**）進行分析提煉，最後由 Supervisor 彙整並提供高知識品質、具體行動建議的執行摘要。"
        await self._execute_map_reduce_summary(7, "Weekly Report", "WEEKLY_EXECUTIVE_SUMMARY", default_prompt)

    async def generate_monthly_executive_summary(self) -> None:
        default_prompt = "這是過去 30 天的系統運行上下文數據：\n\n{context_md}\n\n請對每個專屬領域（Sales, Marketing, System, **Engineering/DevBot**）進行分析提煉，最後由 Supervisor 彙整並提供高知識品質、具體行動建議的執行摘要。"
        await self._execute_map_reduce_summary(30, "Monthly Report", "MONTHLY_EXECUTIVE_SUMMARY", default_prompt)

report_service = ReportService()
