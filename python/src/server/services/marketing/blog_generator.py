import asyncio
import uuid
from typing import Any

from google import genai
from google.genai import types

from ...config.model_ssot import SYSTEM_MODELS
from ...repositories.base_repository import BaseRepository
from ...utils.json_utils import safe_json_loads
from ...utils.retry_utils import retry_with_backoff
from ..guardrail_service import GuardrailService
from ..librarian_service import LibrarianService
from ..prompt_service import prompt_service
from ..token_usage_service import TokenUsageService
from .content_handler import get_logger

logger = get_logger(__name__)




class BlogGenerator(BaseRepository):
    """Handles blog drafting and automated generation from leads using RAG."""

    def __init__(self, supabase_client: Any) -> None:
        super().__init__(supabase_client)

    async def draft_blog(self, topic: str, industry: list[str] | None, keywords: str | None) -> tuple[bool, dict]:
        is_valid, err = GuardrailService.validate_input(f"{topic} {keywords or ''}")
        if not is_valid:
            return False, {"error_code": 400, "message": f"Guardrail Violation: {err}"}

        try:
            context_text = await self._get_expert_style_context(f"{topic} {industry}")
            from ..credential_service import credential_service
            api_key = await credential_service.get_credential(
                "GEMINI_API_KEY"
            ) or await credential_service.get_credential("GOOGLE_API_KEY")
            if not api_key:
                return False, {"error_code": 401, "message": "API Key missing"}

            client = genai.Client(api_key=api_key)
            sys_prompt = prompt_service.get_prompt("BLOG_DRAFT")
            google_search_tool = types.Tool(google_search=types.GoogleSearch())

            @retry_with_backoff(max_retries=2)
            async def _call_gemini() -> Any:
                return await client.aio.models.generate_content(
                    model=SYSTEM_MODELS["DEFAULT_TEXT"],
                    contents=f"Topic: {topic}\nContext: {context_text}",
                    config=types.GenerateContentConfig(
                        system_instruction=sys_prompt, response_mime_type="application/json", tools=[google_search_tool]
                    ),
                )

            response = await _call_gemini()

            # Token Usage
            try:
                from ..agent_registry import get_agent_uuid

                agent_uuid = get_agent_uuid("market-bot")
                asyncio.create_task(
                    TokenUsageService.log_usage(
                        request_id=f"blog-{uuid.uuid4().hex[:8]}",
                        user_id=agent_uuid,
                        model=SYSTEM_MODELS["DEFAULT_TEXT"],
                        provider="google",
                        input_tokens=getattr(response.usage_metadata, "prompt_token_count", 0) or 0,
                        output_tokens=getattr(response.usage_metadata, "candidates_token_count", 0) or 0,
                        context_type="blog_generation",
                    )
                )
            except Exception as log_err:
                logger.warning(f"BlogGenerator: Failed to log blog tokens: {log_err}")

            if not response.text:
                return False, {"error": "AI Empty response"}

            result = safe_json_loads(response.text)
            is_safe, audit = GuardrailService.audit_output(str(result.get("content", "")), context_text)
            if not is_safe:
                return False, {"error_code": 422, "message": f"AI Output Blocked: {audit}"}

            new_post = {
                "title": str(result.get("title", "Untitled")),
                "content": str(result.get("content", "")),
                "excerpt": str(result.get("excerpt", "")),
                "status": "review",
                "ai_score": self.calculate_ai_score(str(result.get("content", ""))),
                "image_url": "https://picsum.photos/seed/market/1024/1024", # 合法
            }
            self.execute_query(self.supabase_client.table("blog_posts").insert(new_post), "Insert new post") # 合法
            return True, {
                "title": new_post["title"],
                "content": new_post["content"],
                "excerpt": new_post["excerpt"],
                "status": "review",
            }
        except Exception as e:
            logger.error(f"BlogGenerator: Blog drafting failed: {e}")
            return False, {"error_code": 500, "message": str(e)}

    async def draft_from_leads(self, lead_ids: list[str]) -> tuple[bool, dict]:
        """Creates a background task for Bob's 'Draft From Leads' action."""
        try:
            from ..projects.task_service import task_service
            from ..shared_constants import AgentNames, AgentUUIDs

            # 1. Fetch lead names for the task title
            success, leads_res = self.execute_query(self.supabase_client.table("leads").select("company_name").in_("id", lead_ids), "Fetch leads") # 合法
            lead_names = [L["company_name"] for L in (leads_res.get("data", []) if success else [])]
            title = f"AI Draft from Leads: {', '.join(lead_names[:2])}"
            if len(lead_names) > 2:
                title += f" (+{len(lead_names) - 2})"

            # 2. Create Task assigned to MarketBot
            success, res = await task_service.create_task(
                project_id="marketing_ops",
                title=title,
                description=f"AI is drafting blog posts for {len(lead_ids)} leads.",
                assignee=AgentNames.MARKET_BOT,
                assignee_id=AgentUUIDs.MARKET_BOT,
                priority="high",
                feature="blog_drafting",
            )

            if not success:
                return False, res

            task_id = res["task"]["id"]

            # 3. Store lead_ids in metadata (or fallback to description if column missing)
            try:
                self.execute_query(self.supabase_client.table("archon_tasks").update({"metadata": {"lead_ids": lead_ids}}).eq( # 合法
                    "id", task_id
                ), "Update task metadata")
            except Exception:
                # Fallback to description suffix if metadata column is not yet migrated
                self.execute_query(self.supabase_client.table("archon_tasks").update( # 合法
                    {"description": res["task"]["description"] + f"\n\n[PARAM:LEAD_IDS:{','.join(lead_ids)}]"}
                ).eq("id", task_id), "Update task description")

            return True, {"task_id": task_id, "status": "dispatched"}

        except Exception as e:
            logger.error(f"BlogGenerator: Async draft from leads failed: {e}")
            return False, {"error_code": 500, "message": str(e)}


    async def draft_daily_market_report_physical(self, task_id: str, task_data: dict) -> str:
        """Physical execution of the daily market report blog drafting."""
        try:
            from ..credential_service import credential_service
            api_key = await credential_service.get_credential(
                "GEMINI_API_KEY"
            ) or await credential_service.get_credential("GOOGLE_API_KEY")
            client = genai.Client(api_key=api_key)

            # Use BLOG_DRAFT prompt to enforce JSON
            sys_prompt = prompt_service.get_prompt("BLOG_DRAFT")

            task_desc = task_data.get("description", "")

            @retry_with_backoff(max_retries=2)
            async def _call_gemini() -> Any:
                return await client.aio.models.generate_content(
                    model=SYSTEM_MODELS["DEFAULT_TEXT"],
                    contents=f"Generate the daily market report based on this instruction:\n\n{task_desc}",
                    config=types.GenerateContentConfig(
                        system_instruction=sys_prompt, response_mime_type="application/json"
                    ),
                )

            response = await _call_gemini()
            if not response.text:
                return "Failed to generate market report."

            result = safe_json_loads(response.text)
            new_post = {
                "title": str(result.get("title", task_data.get("title", "Daily Market Intelligence"))),
                "content": str(result.get("content", "")),
                "excerpt": str(result.get("excerpt", "")),
                "status": "draft",
                "ai_score": self.calculate_ai_score(str(result.get("content", ""))),
            }

            self.execute_query(self.supabase_client.table("blog_posts").insert(new_post), "Insert daily market report") # 合法
            return "Successfully generated Daily Market Intelligence blog post."

        except Exception as e:
            logger.error(f"Error drafting daily market report physical: {e}", exc_info=True)
            return f"Failed to draft daily market report: {e}"

    async def draft_from_leads_physical(self, task_id: str, lead_ids: list[str]) -> str:
        """Physical execution of the blog drafting."""
        try:
            success, leads_res = self.execute_query(self.supabase_client.table("leads").select("*").in_("id", lead_ids), "Fetch leads physical") # 合法
            leads = leads_res.get("data", []) if success else []
            if not leads:
                return "No leads found for enrichment."

            from ..credential_service import credential_service
            api_key = await credential_service.get_credential(
                "GEMINI_API_KEY"
            ) or await credential_service.get_credential("GOOGLE_API_KEY")
            client = genai.Client(api_key=api_key)
            sys_prompt = prompt_service.get_prompt("BLOG_DRAFT")

            generated_count = 0
            new_posts = []
            for lead in leads:

                @retry_with_backoff(max_retries=2)
                async def _call_gemini(current_lead=lead) -> Any:
                    return await client.aio.models.generate_content(
                        model=SYSTEM_MODELS["DEFAULT_TEXT"],
                        contents=f"Generate a blog post. Target Company: {current_lead.get('company_name')}. Identified Need: {current_lead.get('identified_need')}. Job Title: {current_lead.get('job_title')}",
                        config=types.GenerateContentConfig(
                            system_instruction=sys_prompt, response_mime_type="application/json"
                        ),
                    )

                response = await _call_gemini()
                if not response.text:
                    continue

                result = safe_json_loads(response.text)
                new_post = {
                    "title": str(result.get("title", f"Draft for {lead.get('company_name')}")),
                    "content": str(result.get("content", "")),
                    "excerpt": str(result.get("excerpt", "")),
                    "status": "draft",
                    "ai_score": self.calculate_ai_score(str(result.get("content", ""))),
                    "lead_id": lead.get("id"),
                }
                new_posts.append(new_post)
                generated_count += 1

            if new_posts:
                self.execute_query(self.supabase_client.table("blog_posts").insert(new_posts), "Insert generated posts") # 合法

            return f"Successfully generated {generated_count} blog drafts from {len(lead_ids)} leads."

        except Exception as e:
            logger.error(f"BlogGenerator: Physical draft from leads failed: {e}")
            raise e

    async def submit_blog(self, post_id: str) -> tuple[bool, dict]:
        success, res = self.execute_query(self.supabase_client.table("blog_posts").select("*").eq("id", post_id), "Select post") # 合法
        post = res.get("data", [None])[0] if success and res.get("data") else None
        if not post:
            return False, {"error": "Post not found"}
        score = self.calculate_ai_score(post.get("content", ""))
        status = "changes_requested" if score < 50 else "review"
        self.execute_query(self.supabase_client.table("blog_posts").update({"status": status, "ai_score": score}).eq( # 合法
            "id", post_id
        ), "Update post status")
        return True, {"status": status, "ai_score": score}

    async def get_content_context(self, source_id: str, source_type: str) -> dict:
        context_text = ""
        if source_type == "lead":
            success, logs_res = self.execute_query(self.supabase_client.table("visit_logs").select("*").eq("lead_id", source_id), "Fetch visit logs") # 合法
            logs = logs_res.get("data", []) if success else []
            for log_item in logs or []:
                context_text += f"\n[Log]: {log_item.get('summary') or 'No summary'}\n"
        from ..search.rag_service import RAGService
        success, res = await RAGService().perform_rag_query(query=context_text[:1000] or "General", match_count=3)
        return {
            "source_id": source_id,
            "source_type": source_type,
            "rag_refs": res.get("results", []) if success else [],
            "context_summary": context_text,
        }

    async def _get_expert_style_context(self, query: str) -> str:
        from ..search.rag_service import RAGService
        success, rag = await RAGService().perform_rag_query(query=query, match_count=5, min_score=0.15)
        context_text = ""
        if success:
            for r in rag.get("results", []):
                context_text += f"\n[RAG]: {r['content']}\n"
        try:
            constraints = await LibrarianService().get_style_constraints(category="marketing")
            if constraints:
                context_text += f"\n[BRAND VOICE CONSTRAINTS]:\n{constraints}\n"
        except Exception as e:
            logger.warning(f"BlogGenerator: Failed to retrieve constraints: {e}")
        return context_text

    def calculate_ai_score(self, content: str) -> int:
        if len(content) < 100:
            return 30
        if "Archon" in content:
            return 85
        return 75
