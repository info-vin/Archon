import asyncio
import base64
import uuid
from typing import Any, cast

from google import genai
from google.genai import types

from ...config.logfire_config import get_logger
from ...config.model_ssot import SYSTEM_MODELS
from ...prompts.marketing_prompts import BLOG_DRAFT_SYSTEM_PROMPT
from ...prompts.sales_prompts import SALES_PITCH_SYSTEM_PROMPT
from ...utils.json_utils import safe_json_loads
from ...utils.retry_utils import retry_with_backoff
from ..credential_service import credential_service
from ..guardrail_service import GuardrailService
from ..librarian_service import LibrarianService
from ..log_service import LogService
from ..prompt_service import prompt_service
from ..search.rag_service import RAGService
from ..token_usage_service import TokenUsageService

logger = get_logger(__name__)

class ContentHandler:
    """
    Handles AI Content Generation, Visual Assets, and Approval Workflows.
    Physically decoupled from MarketingService for Phase 4.6.47.
    """

    def __init__(self, supabase_client: Any):
        self.supabase_client = supabase_client

    async def generate_pitch(self, company: str, job_title: str) -> dict:
        try:
            api_key = await credential_service.get_credential("GEMINI_API_KEY")
            if not api_key:
                return {"error_code": 401, "message": "GEMINI_API_KEY missing."}

            rag_strategy_creds = await credential_service.get_credentials_by_category("rag_strategy")
            marketing_model = rag_strategy_creds.get("MARKETING_MODEL") or SYSTEM_MODELS["DEFAULT_TEXT"]

            client = genai.Client(api_key=api_key)
            sys_prompt = prompt_service.get_prompt("SALES_PITCH", SALES_PITCH_SYSTEM_PROMPT)

            @retry_with_backoff(max_retries=2)
            async def _call_gemini():
                return await client.aio.models.generate_content(
                    model=marketing_model,
                    contents=f"Company: {company}\nRole: {job_title}",
                    config=types.GenerateContentConfig(system_instruction=sys_prompt),
                )

            response = await _call_gemini()

            # Token Logging
            try:
                from ..agent_registry import get_agent_uuid
                agent_uuid = get_agent_uuid("market-bot")
                asyncio.create_task(
                    TokenUsageService.log_usage(
                        request_id=f"pitch-{uuid.uuid4().hex[:8]}",
                        user_id=agent_uuid,
                        model=SYSTEM_MODELS["DEFAULT_TEXT"],
                        provider="google",
                        input_tokens=getattr(response.usage_metadata, "prompt_token_count", 0) or 0,
                        output_tokens=getattr(response.usage_metadata, "candidates_token_count", 0) or 0,
                        context_type="sales_pitch_generation",
                    )
                )
            except Exception as log_err:
                logger.warning(f"ContentHandler: Failed to log pitch tokens: {log_err}")

            return {"content": response.text or "AI Error", "references": []}

        except Exception as e:
            logger.error(f"ContentHandler: Pitch generation failed: {e}")
            try:
                LogService(self.supabase_client).create_log_entry({
                    "user_input": f"Pitch Request: {company} / {job_title}",
                    "gemini_response": f"AI Error: {str(e)[:500]}",
                    "project_name": "SalesBot",
                    "user_name": "alice@archon.com"
                })
            except Exception:
                pass
            return {"error_code": 500, "message": str(e)}

    async def generate_visual_asset(self, style: str) -> dict:
        from .logo_tool import generate_logo_svg
        try:
            api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
            client = genai.Client(api_key=api_key)
            prompt = f"Professional tech logo, {style}, high resolution"

            try:
                native_resp = client.models.generate_content(
                    model=SYSTEM_MODELS["IMAGE_GEN"],
                    contents=cast(Any, [prompt]),
                    config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
                )
                for part in native_resp.parts or []:
                    if part.inline_data and part.inline_data.data:
                        return {
                            "status": "success",
                            "image_url": f"data:{part.inline_data.mime_type};base64,{part.inline_data.data.decode('utf-8')}",
                            "tier": "native",
                            "svg_content": "",
                        }
            except Exception:
                logger.warning("ContentHandler: Native AI visual generation failed, using SVG.")

            svg_content = generate_logo_svg(style)
            svg_base64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
            return {
                "status": "success",
                "image_url": f"data:image/svg+xml;base64,{svg_base64}",
                "tier": "physical_svg",
                "svg_content": svg_content,
            }
        except Exception as e:
            logger.error(f"ContentHandler: Visual fallback: {e}")
            return {"status": "success", "image_url": "https://picsum.photos/1024/1024", "tier": "emergency"}

    async def draft_blog(self, topic: str, industry: list[str] | None, keywords: str | None) -> tuple[bool, dict]:
        is_valid, err = GuardrailService.validate_input(f"{topic} {keywords or ''}")
        if not is_valid:
            return False, {"error_code": 400, "message": f"Guardrail Violation: {err}"}

        try:
            context_text = await self._get_expert_style_context(f"{topic} {industry}")
            api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
            if not api_key:
                return False, {"error_code": 401, "message": "API Key missing"}

            client = genai.Client(api_key=api_key)
            sys_prompt = prompt_service.get_prompt("BLOG_DRAFT", BLOG_DRAFT_SYSTEM_PROMPT)
            google_search_tool = types.Tool(google_search=types.GoogleSearch())

            @retry_with_backoff(max_retries=2)
            async def _call_gemini():
                return await client.aio.models.generate_content(
                    model=SYSTEM_MODELS["DEFAULT_TEXT"],
                    contents=f"Topic: {topic}\nContext: {context_text}",
                    config=types.GenerateContentConfig(
                        system_instruction=sys_prompt,
                        response_mime_type="application/json",
                        tools=[google_search_tool]
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
                logger.warning(f"ContentHandler: Failed to log blog tokens: {log_err}")

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
                "image_url": "https://picsum.photos/seed/market/1024/1024",
            }
            self.supabase_client.table("blog_posts").insert(new_post).execute()
            return True, {"title": new_post["title"], "content": new_post["content"], "excerpt": new_post["excerpt"], "status": "review"}
        except Exception as e:
            logger.error(f"ContentHandler: Blog drafting failed: {e}")
            return False, {"error_code": 500, "message": str(e)}

    async def draft_from_leads(self, lead_ids: list[str]) -> tuple[bool, dict]:
        try:
            # 1. Fetch Leads
            leads_res = self.supabase_client.table("leads").select("*").in_("id", lead_ids).execute()
            leads = leads_res.data or []
            if not leads:
                return False, {"error_code": 404, "message": "No leads found for the provided IDs."}

            api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
            if not api_key:
                return False, {"error_code": 401, "message": "API Key missing"}

            client = genai.Client(api_key=api_key)
            sys_prompt = prompt_service.get_prompt("BLOG_DRAFT", BLOG_DRAFT_SYSTEM_PROMPT)

            generated_drafts = []

            for lead in leads:
                @retry_with_backoff(max_retries=2)
                async def _call_gemini(current_lead=lead):
                    return await client.aio.models.generate_content(
                        model=SYSTEM_MODELS["DEFAULT_TEXT"],
                        contents=f"Generate a blog post. Target Company: {current_lead.get('company_name')}. Identified Need: {current_lead.get('identified_need')}. Job Title: {current_lead.get('job_title')}",
                        config=types.GenerateContentConfig(
                            system_instruction=sys_prompt,
                            response_mime_type="application/json"
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
                    "image_url": "https://picsum.photos/seed/market/1024/1024",
                }

                insert_res = self.supabase_client.table("blog_posts").insert(new_post).execute()
                if insert_res.data:
                     generated_drafts.append(insert_res.data[0])

            return True, {"generated_count": len(generated_drafts), "drafts": generated_drafts}

        except Exception as e:
            logger.error(f"ContentHandler: Draft from leads failed: {e}")
            return False, {"error_code": 500, "message": str(e)}

    async def submit_blog(self, post_id: str) -> tuple[bool, dict]:
        post = self.supabase_client.table("blog_posts").select("*").eq("id", post_id).single().execute().data
        if not post:
            return False, {"error": "Post not found"}
        score = self.calculate_ai_score(post.get("content", ""))
        status = "changes_requested" if score < 50 else "review"
        self.supabase_client.table("blog_posts").update({"status": status, "ai_score": score}).eq("id", post_id).execute()
        return True, {"status": status, "ai_score": score}

    async def process_approval(self, item_type: str, item_id: str, action: str, notes: str | None) -> bool:
        if item_type == "blog":
            new_status = "published" if action == "approve" else "changes_requested"
            res = self.supabase_client.table("blog_posts").update({"status": new_status, "review_notes": notes}).eq("id", item_id).execute()
            if action != "approve" and notes and res.data:
                try:
                    post_data = res.data[0]
                    import asyncio

                    from ..librarian_service import LibrarianService
                    asyncio.create_task(
                        LibrarianService().archive_style_critique(
                            post_title=post_data.get("title", "Untitled"),
                            original_content=post_data.get("content", ""),
                            review_notes=notes,
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to archive style critique for blog {item_id}: {e}")
            return True
        return False

    async def get_pending_approvals(self) -> dict:
        res = self.supabase_client.table("blog_posts").select("*").eq("status", "review").order("updated_at", desc=True).execute()
        return {"blogs": res.data or [], "leads": []}

    async def generate_reject_suggestion(self, item_type: str, item_id: str) -> dict:
        if item_type != "blog":
            return {"notes": "Content type not supported for AI rejection."}

        post = self.supabase_client.table("blog_posts").select("*").eq("id", item_id).single().execute().data
        if not post:
            return {"notes": "Item not found."}

        from google import genai

        from ...config.model_ssot import SYSTEM_MODELS
        from ..credential_service import credential_service
        from ..prompt_service import prompt_service

        api_key = await credential_service.get_credential("GEMINI_API_KEY")
        if not api_key:
            return {"notes": "Cannot generate AI reason: AI provider missing."}

        client = genai.Client(api_key=api_key)

        default_prompt = (
            "You are a marketing director reviewing a blog post draft.\n"
            "The draft is slightly off-brand or has quality issues.\n"
            "Content:\n{content}\n\n"
            "Provide exactly ONE brief, constructive paragraph (max 50 words) explaining why this is rejected and what needs to be improved. Use Traditional Chinese."
        )
        prompt_template = prompt_service.get_prompt("REJECT_SUGGESTION", default=default_prompt)
        prompt = prompt_template.format(content=post.get("content", ""))

        try:
            response = await client.aio.models.generate_content(
                model=SYSTEM_MODELS["DEFAULT_TEXT"],
                contents=prompt
            )
            return {"notes": response.text.strip() if response.text else "Failed to generate reason."}
        except Exception as e:
            return {"notes": f"AI Generation Failed: {str(e)}"}

    async def get_content_context(self, source_id: str, source_type: str) -> dict:
        context_text = ""
        if source_type == "lead":
            logs = self.supabase_client.table("visit_logs").select("*").eq("lead_id", source_id).execute().data
            for log_item in (logs or []):
                context_text += f"\n[Log]: {log_item.get('summary') or 'No summary'}\n"
        success, res = await RAGService().perform_rag_query(query=context_text[:1000] or "General", match_count=3)
        return {
            "source_id": source_id,
            "source_type": source_type,
            "rag_refs": res.get("results", []) if success else [],
            "context_summary": context_text,
        }

    async def _get_expert_style_context(self, query: str) -> str:
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
            logger.warning(f"ContentHandler: Failed to retrieve constraints: {e}")
        return context_text

    def calculate_ai_score(self, content: str) -> int:
        if len(content) < 100:
            return 30
        if "Archon" in content:
            return 85
        return 75
