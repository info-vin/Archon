import asyncio
from typing import Any, cast

from google import genai
from google.genai import types

from ..config.logfire_config import get_logger
from ..prompts.marketing_prompts import BLOG_DRAFT_SYSTEM_PROMPT, REJECTION_REASON_PROMPT
from ..prompts.sales_prompts import SALES_PITCH_SYSTEM_PROMPT
from ..repositories.base_repository import BaseRepository
from ..services.credential_service import credential_service
from ..services.guardrail_service import GuardrailService
from ..services.job_board_service import JobBoardService, JobData
from ..services.librarian_service import LibrarianService
from ..services.prompt_service import prompt_service
from ..services.search.rag_service import RAGService
from ..utils import get_supabase_client
from ..utils.json_utils import safe_json_loads

logger = get_logger(__name__)

class MarketingService(BaseRepository):
    """
    Marketing Service - Encapsulates all Alice/Bob workflows and 3-Agent collaboration logic.
    Follows Phase 4.6.12 Architectural Hardening Standards.
    """

    def __init__(self, supabase_client=None):
        super().__init__(supabase_client or get_supabase_client())

    async def search_jobs(self, keyword: str, limit: int = 10) -> list[JobData]:
        service = JobBoardService()
        jobs = await service.search_jobs(keyword, limit)
        asyncio.create_task(service.identify_leads_and_save(jobs))
        return jobs

    async def list_leads(self) -> list[dict]:
        def _query():
            return self.supabase_client.table("leads").select("*").order("created_at", desc=True).execute()
        success, res = self.execute_query(_query, "Failed to fetch leads")
        return res.get("data", []) if success else []

    async def create_lead(self, lead_data: dict, creator_id: str | None = None) -> tuple[bool, dict]:
        lead_data["created_from_user_id"] = creator_id
        source_url = lead_data.get("source_job_url")

        if source_url:
            def _check_existing():
                return self.supabase_client.table("leads").select("id").eq("source_job_url", source_url).execute()
            _, existing = self.execute_query(_check_existing, "Check existing lead")
            if existing.get("data"):
                if lead_data.get("pitch_content"):
                    self.supabase_client.table("leads").update({"pitch_content": lead_data["pitch_content"]}).eq("id", existing["data"][0]['id']).execute()
                return True, {"lead": existing["data"][0]}

        def _insert():
            return self.supabase_client.table("leads").insert(lead_data).execute()

        success, res = self.execute_query(_insert, "Failed to create lead")
        if success and res.get("data"):
            return True, {"lead": res["data"][0]}
        return False, res

    async def update_lead(self, lead_id: str, update_data: dict) -> tuple[bool, dict]:
        def _query():
            return self.supabase_client.table("leads").update(update_data).eq("id", lead_id).execute()

        success, res = self.execute_query(_query, f"Failed to update lead {lead_id}")
        if success and res.get("data"):
            return True, {"lead": res["data"][0]}
        return False, res

    async def promote_to_vendor(self, lead_id: str, vendor_name: str, email: str | None, notes: str | None, owner_id: str) -> tuple[bool, dict]:
        try:
            vendor_data = {
                "name": vendor_name,
                "contact_email": email,
                "description": notes or "Promoted",
                "status": "active",
                "owner_id": owner_id
            }
            vendor_res = self.supabase_client.table("vendors").insert(vendor_data).execute()
            new_vendor_id = vendor_res.data[0]["id"]

            self.supabase_client.table("leads").update({"status": "converted"}).eq("id", lead_id).execute()
            self.supabase_client.table("visit_logs").update({"customer_id": new_vendor_id}).eq("lead_id", lead_id).execute()

            return True, {"vendor": vendor_res.data[0]}
        except Exception as e:
            return False, {"error": str(e)}

    async def generate_pitch(self, company: str, job_title: str) -> dict:
        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
        if not api_key:
            return {"error_code": 401, "message": "AI API Key not configured."}

        client = genai.Client(api_key=api_key)
        sys_prompt = prompt_service.get_prompt("SALES_PITCH", SALES_PITCH_SYSTEM_PROMPT)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Company: {company}\nRole: {job_title}",
            config=types.GenerateContentConfig(system_instruction=sys_prompt)
        )
        return {"content": response.text or "AI Error", "references": []}

    async def generate_visual_asset(self, style: str) -> dict:
        """Scenario 3: Nana Banana 3-Tier Defense"""
        try:
            api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
            client = genai.Client(api_key=api_key)
            prompt = f"Professional tech logo, {style}, high resolution"
            try:
                native_resp = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=cast(Any, [prompt]),
                    config=types.GenerateContentConfig(response_modalities=['IMAGE'])
                )
                for part in (native_resp.parts or []):
                    if part.inline_data:
                        return {
                            "status": "success",
                            "image_url": f"data:{part.inline_data.mime_type};base64,{part.inline_data.data.decode('utf-8')}",
                            "tier": "native",
                            "svg_content": ""
                        }
            except Exception:
                pass

            import urllib.parse
            fallback_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true"
            return {"status": "success", "image_url": fallback_url, "tier": "fallback_pollinations", "svg_content": "<svg></svg>"}
        except Exception:
            return {"status": "success", "image_url": "https://picsum.photos/1024/1024", "tier": "emergency"}

    async def get_combined_sources(self, user_id: str) -> list[dict]:
        leads = self.supabase_client.table("leads").select("*").limit(10).execute().data or []
        tasks = self.supabase_client.table("archon_tasks").select("*").eq("assignee_id", user_id).limit(10).execute().data or []
        blogs = self.supabase_client.table("blog_posts").select("*").in_("status", ["draft", "changes_requested"]).limit(10).execute().data or []

        sources = []
        for lead_entry in leads:
            sources.append({
                "id": lead_entry["id"], "type": "lead", "title": lead_entry["company_name"],
                "score": lead_entry.get("enrichment_score", 0),
                "summary": lead_entry.get("identified_need", "")[:100], "date": lead_entry["created_at"]
            })
        for task_entry in tasks:
            sources.append({
                "id": task_entry["id"], "type": "task", "title": task_entry["title"],
                "score": 100, "summary": task_entry.get("description", "")[:100], "date": task_entry["created_at"]
            })
        for blog_entry in blogs:
            sources.append({
                "id": blog_entry["id"], "type": "blog", "title": blog_entry["title"],
                "score": blog_entry.get("ai_score", 0), "summary": blog_entry.get("excerpt", ""),
                "date": blog_entry["created_at"], "status": blog_entry["status"]
            })
        return sorted(sources, key=lambda x: x["date"], reverse=True)

    async def get_pending_approvals(self) -> dict:
        """Physical Fix for Charlie's Approvals Page"""
        res = self.supabase_client.table("blog_posts").select("*").eq("status", "review").order("updated_at", desc=True).execute()
        return {"blogs": res.data or [], "leads": []}

    async def get_content_context(self, source_id: str, source_type: str) -> dict:
        context_text = ""
        if source_type == "lead":
            logs = self.supabase_client.table("visit_logs").select("*").eq("lead_id", source_id).execute().data
            for log_item in logs:
                context_text += f"\n[Log]: {log_item.get('summary')}\n"
        success, res = await RAGService().perform_rag_query(query=context_text[:1000] or "General", match_count=3)
        return {"source_id": source_id, "source_type": source_type, "rag_refs": res.get("results", []) if success else [], "context_summary": context_text}

    async def process_approval(self, item_type: str, item_id: str, action: str, notes: str | None) -> bool:
        if item_type == "blog":
            new_status = "published" if action == "approve" else "changes_requested"
            res = self.supabase_client.table("blog_posts").update({"status": new_status, "review_notes": notes}).eq("id", item_id).execute()

            if action != "approve" and notes and res.data:
                post_data = res.data[0]
                asyncio.create_task(LibrarianService().archive_style_critique(
                    post_title=post_data.get("title", "Untitled"),
                    original_content=post_data.get("content", ""),
                    review_notes=notes
                ))
            return True
        return False

    async def submit_blog(self, post_id: str) -> tuple[bool, dict]:
        post = self.supabase_client.table("blog_posts").select("*").eq("id", post_id).single().execute().data
        if not post:
            return False, {"error": "Post not found"}

        score = self._calculate_ai_score(post.get("content", ""))
        status = "changes_requested" if score < 50 else "review"
        self.supabase_client.table("blog_posts").update({"status": status, "ai_score": score}).eq("id", post_id).execute()
        return True, {"status": status, "ai_score": score}

    async def get_rejection_reason(self, blog_post_id: str) -> str | None:
        """Bob's Smart Polish: Get AI suggested rejection reason"""
        from ..services.blog_service import BlogService
        s, blog = await BlogService().get_post(blog_post_id)
        if not s or not blog or not blog.get('post'):
            return None

        api_key = await credential_service.get_credential("GEMINI_API_KEY")
        if not api_key:
            return "API Key Missing"

        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=REJECTION_REASON_PROMPT.format(title=blog['post']['title'], content=blog['post']['content'][:1000])
        )
        return str(resp.text) if resp.text else None
    async def draft_blog(self, topic: str, industry: list[str] | None, keywords: str | None) -> tuple[bool, dict]:
        # P11: Guardrail Check
        is_valid, err = GuardrailService.validate_input(f"{topic} {keywords or ''}")
        if not is_valid:
            return False, {"error_code": 400, "message": f"Guardrail Violation: {err}"}

        context_text = await self._get_expert_style_context(f"{topic} {industry}")
        api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
        if not api_key:
            return False, {"error_code": 401, "message": "API Key missing"}

        client = genai.Client(api_key=api_key)
        sys_prompt = prompt_service.get_prompt("BLOG_DRAFT", BLOG_DRAFT_SYSTEM_PROMPT)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Topic: {topic}\nContext: {context_text}",
            config=types.GenerateContentConfig(system_instruction=sys_prompt, response_mime_type="application/json")
        )

        if not response.text:
            return False, {"error": "AI Empty response"}
        result = safe_json_loads(response.text)

        # P11: AI Leakage Guardrail
        is_safe, audit = GuardrailService.audit_output(str(result.get("content", "")), context_text)
        if not is_safe:
            return False, {"error_code": 422, "message": f"AI Output Blocked: {audit}"}

        return True, {
            "title": str(result.get("title", "Untitled")),
            "content": str(result.get("content", "")),
            "excerpt": str(result.get("excerpt", "")),
            "used_prompt": topic
        }

    async def get_trends(self) -> dict:
        res_t = self.supabase_client.table("marketing_trends").select("*").eq("trend_type", "keyword_growth").order("report_date", desc=True).limit(1).execute()
        res_s = self.supabase_client.table("marketing_trends").select("*").eq("trend_type", "sankey_flow").order("report_date", desc=True).limit(1).execute()
        return {
            "keyword_growth": res_t.data[0]["data"] if res_t.data else [],
            "sankey_flow": res_s.data[0]["data"] if res_s.data else {}
        }

    async def _get_expert_style_context(self, query: str) -> str:
        success, rag = await RAGService().perform_rag_query(query=query, match_count=5, min_score=0.15)
        context_text = ""
        if success:
            for r in rag.get("results", []):
                context_text += f"\n[RAG]: {r['content']}\n"
        return context_text

    def _calculate_ai_score(self, content: str) -> int:
        if len(content) < 100:
            return 30
        if "Archon" in content:
            return 85
        return 75
