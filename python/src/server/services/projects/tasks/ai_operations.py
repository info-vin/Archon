"""
AI Logic Submodule for Task Service (Phase 4.6.12 Hardening)

This module handles AI-powered task refinement (POBot) and
automated task generation from alerts (Smart Dispatch).
"""

import textwrap
from typing import Any

from src.server.config.logfire_config import get_logger
from src.server.services.log_service import LogService

logger = get_logger(__name__)


async def refine_task_description_logic(supabase_client, title: str, description: str) -> str:
    """
    Uses POBot (RAG-enhanced) to transform a raw description into
    a structured product spec with User Stories and Technical Requirements.
    """
    try:
        from google import genai
        from google.genai import types

        from src.server.services.credential_service import credential_service
        from src.server.services.search.rag_service import RAGService

        # 1. Fetch relevant context using RAG
        rag_service = RAGService(supabase_client)
        rag_success, rag_result = await rag_service.perform_rag_query(query=f"{title} {description}", match_count=3)

        context_str = ""
        if rag_success and "results" in rag_result:
            snippets = [res.get("content", "")[:300] for res in rag_result["results"]]
            context_str = "\n".join(snippets)
            logger.info(f"POBot RAG found {len(snippets)} context snippets")

        # 2. Construct Prompt with Context
        prompt = (
            textwrap.dedent(
                f"""
            You are POBot, an expert Product Owner.
            Refine the following task into a professional, structured specification.

            TASK TITLE: {title}
            RAW DESCRIPTION: {description}

            RELEVANT PROJECT CONTEXT (from RAG):
            {{context_str}}

            FORMAT:
            1. **Goal**: One sentence high-level goal.
            2. **User Stories**: At least 2-3 stories in "As a... I want to... so that..." format.
            3. **Acceptance Criteria**: Detailed bullet points.
            4. **Technical Considerations**: Constraints or hints (based on context if applicable).

            KEEP IT CONCISE AND ACTIONABLE.
        """
            )
            .format(context_str=context_str)
            .strip()
        )

        # 3. Generate Content using official SDK
        model_name = "gemini-2.5-flash-lite"

        # Key Decoupling: Prefer GEMINI_API_KEY
        charlie_api_key = await credential_service.get_credential(
            "GEMINI_API_KEY"
        ) or await credential_service.get_credential("GOOGLE_API_KEY")

        if not charlie_api_key:
            raise ValueError("No AI API Key available for PO Workflows")

        client = genai.Client(api_key=charlie_api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are POBot, a helpful Product Owner assistant. ALWAYS answer in Traditional Chinese (Taiwan繁體中文), regardless of the input language.",
                temperature=0.7,
            ),
        )

        content = response.text or ""
        if not content:
            raise ValueError("LLM returned empty content")
        return content

    except Exception as e:
        logger.error(f"POBot refinement failed: {e}", exc_info=True)

        # System Alert Logging
        try:
            LogService(supabase_client).create_log_entry(
                {
                    "user_input": f"SYSTEM_ALERT: POBot Failure [{type(e).__name__}]",
                    "gemini_response": f"Refinement Failed. Error: {str(e)}",
                    "project_name": "manager_bot",
                    "user_name": "system",
                }
            )
        except Exception:
            pass

        raise RuntimeError(f"POBot Refinement Unavailable: {str(e)[:100]}") from e


async def generate_task_from_alert_logic(
    task_service_instance, alert_id: str, assignee_id: str | None = None
) -> tuple[bool, dict[str, Any]]:
    """
    AI-powered task generation from a Sentinel alert.
    Enriches the task with business context from the lead and RAG.
    """
    try:
        from src.server.services.credential_service import credential_service
        from src.server.services.search.rag_service import RAGService

        # 1. Fetch Alert
        context_msg = "Automated Alert"
        details = {}
        source_table = "archon_logs"

        res_alert = task_service_instance.supabase_client.table("archon_logs").select("*").eq("id", alert_id).execute()
        alert_data = res_alert.data[0] if (res_alert.data and len(res_alert.data) > 0) else None

        if alert_data:
            details = alert_data.get("details", {})
            context_msg = alert_data.get("message", "System Alert")
        else:
            res_ethics = (
                task_service_instance.supabase_client.table("archon_ethics_events")
                .select("*")
                .eq("id", alert_id)
                .execute()
            )
            if res_ethics.data and len(res_ethics.data) > 0:
                eth = res_ethics.data[0]
                context_msg = f"Ethics Violation: {eth.get('event_type')} - {eth.get('description')}"
                details = {
                    "type": "ethics_violation",
                    "category": "business",
                    "raw_input": eth.get("raw_input"),
                    "company": "Safety Compliance",
                }
                source_table = "archon_ethics_events"
            else:
                return False, {"error": f"Alert or Ethics Event {alert_id} not found"}

        lead_id = details.get("lead_id")
        post_id = details.get("post_id")

        # 2. Gather Context
        context_str = f"ALERT: {context_msg}\n"

        if lead_id:
            res_lead = task_service_instance.supabase_client.table("leads").select("*").eq("id", lead_id).execute()
            if res_lead.data and len(res_lead.data) > 0:
                lead_data_local = res_lead.data[0]
                context_str += f"COMPANY: {lead_data_local['company_name']}\n"
                context_str += f"IDENTIFIED NEED: {lead_data_local.get('identified_need', 'None')}\n"
                res_logs = (
                    task_service_instance.supabase_client.table("visit_logs")
                    .select("summary")
                    .eq("lead_id", lead_id)
                    .limit(3)
                    .execute()
                )
                if res_logs.data:
                    context_str += "\nPAST VISIT SUMMARIES:\n"
                    for _log in res_logs.data:
                        context_str += f"- {_log['summary']}\n"

        elif post_id:
            res_post = task_service_instance.supabase_client.table("blog_posts").select("*").eq("id", post_id).execute()
            if res_post.data and len(res_post.data) > 0:
                post_data_local = res_post.data[0]
                context_str += f"CONTEXT: Content Bottleneck\nTITLE: {post_data_local['title']}\nSTATUS: {post_data_local['status']}\n"

        # 3. RAG Search
        rag_service = RAGService(task_service_instance.supabase_client)
        rag_success, rag_result = await rag_service.perform_rag_query(
            query=f"{details.get('company', 'Compliance')} {details.get('type', '')}",
            match_count=2,
        )
        if rag_success and "results" in rag_result:
            context_str += "\nINTERNAL KNOWLEDGE BASE SNIPPETS:\n"
            context_str += "\n".join([res.get("content", "")[:300] for res in rag_result["results"]])

        # 4. Call AI using Official SDK
        model_name = "gemini-1.5-pro"
        charlie_api_key = await credential_service.get_credential(
            "GEMINI_API_KEY"
        ) or await credential_service.get_credential("GOOGLE_API_KEY")

        if not charlie_api_key:
            raise ValueError("No AI API Key available for Alert Dispatch")

        prompt = (
            textwrap.dedent(
                f"""
            Convert the following Alert into a high-value task for the team.
            ALERT: {context_msg}
            CONTEXT: {context_str}
            FORMAT: TITLE: [Title] | DESCRIPTION: [Detailed strategy]
        """
            )
            .format(context_msg=context_msg, context_str=context_str)
            .strip()
        )

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=charlie_api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are Charlie's Assistant. Answer in Traditional Chinese (Taiwan).",
                temperature=0.7,
            ),
        )
        ai_output = response.text or ""
        if not ai_output:
            raise ValueError("LLM returned empty dispatch content")

        # Parse AI Output
        title = f"Follow-up: {details.get('company', 'Safety Case')}"
        description = ai_output
        if "TITLE:" in ai_output:
            try:
                title = ai_output.split("TITLE:")[1].split("DESCRIPTION:")[0].strip()
                description = ai_output.split("DESCRIPTION:")[1].strip()
            except Exception:
                pass

        # 5. Get Project (Field Ops preferred)
        p_res = (
            task_service_instance.supabase_client.table("archon_projects")
            .select("id")
            .ilike("title", "%Field%")
            .execute()
        )
        if not (p_res.data and len(p_res.data) > 0):
            p_res = task_service_instance.supabase_client.table("archon_projects").select("id").limit(1).execute()

        if not (p_res.data and len(p_res.data) > 0):
            return False, {"error": "Critical: No project found in database to attach task."}

        project_id = p_res.data[0]["id"]

        sources = [{"type": "sentinel_alert", "source_id": alert_id, "title": context_msg}]

        # Create Task via passed-in instance to avoid circular imports and maintain state
        success, result = await task_service_instance.create_task(
            project_id=project_id,
            title=title,
            description=description,
            assignee_id=assignee_id,
            priority="high",
            sources=sources,
        )

        if success:
            logger.info(f"Smart Dispatch Success: {source_table} {alert_id}")
            if source_table == "archon_logs":
                updated_details = {
                    **details,
                    "status": "dispatched",
                    "dispatched_task_id": result["task"]["id"],
                }
                task_service_instance.supabase_client.table("archon_logs").update(
                    {"details": updated_details, "level": "INFO"}
                ).eq("id", alert_id).execute()
            else:
                task_service_instance.supabase_client.table("archon_ethics_events").update(
                    {
                        "resolved": True,
                        "resolution_notes": f"Dispatched: {result['task']['id']}",
                    }
                ).eq("id", alert_id).execute()

        return success, result

    except Exception as e:
        logger.error(f"Critical Dispatch Error: {e}", exc_info=True)
        return False, {"error": str(e)}
