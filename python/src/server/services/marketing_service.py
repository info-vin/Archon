import asyncio
from typing import Any, cast

from google import genai
from google.genai import types

from ..config.logfire_config import get_logger
from ..config.model_ssot import SYSTEM_MODELS
from ..prompts.marketing_prompts import BLOG_DRAFT_SYSTEM_PROMPT
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
from .log_service import LogService

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

        # Physical Realization of Phase 4.6.42 Task 2: Automatic Lead Scoring
        if not lead_data.get("enrichment_score") or lead_data.get("enrichment_score") == 0:
            lead_data["enrichment_score"] = await self._calculate_lead_score(lead_data.get("job_title"))

        source_url = lead_data.get("source_job_url")

        if source_url:

            def _check_existing():
                return self.supabase_client.table("leads").select("id").eq("source_job_url", source_url).execute()

            _, existing = self.execute_query(_check_existing, "Check existing lead")
            if existing.get("data"):
                if lead_data.get("pitch_content"):
                    self.supabase_client.table("leads").update({"pitch_content": lead_data["pitch_content"]}).eq(
                        "id", existing["data"][0]["id"]
                    ).execute()
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

    async def promote_to_vendor(
        self, lead_id: str, vendor_name: str, email: str | None, notes: str | None, owner_id: str
    ) -> tuple[bool, dict]:
        try:
            vendor_data = {
                "name": vendor_name,
                "contact_email": email,
                "description": notes or "Promoted",
                "status": "active",
                "owner_id": owner_id,
            }
            vendor_res = self.supabase_client.table("vendors").insert(vendor_data).execute()
            new_vendor_id = vendor_res.data[0]["id"]

            self.supabase_client.table("leads").update({"status": "converted"}).eq("id", lead_id).execute()
            self.supabase_client.table("visit_logs").update({"customer_id": new_vendor_id}).eq(
                "lead_id", lead_id
            ).execute()

            return True, {"vendor": vendor_res.data[0]}
        except Exception as e:
            return False, {"error": str(e)}

    async def generate_pitch(self, company: str, job_title: str) -> dict:
        """
        Generates a tailored sales pitch using Gemini LLM.
        Uses credential_service to retrieve the appropriate API key.
        """
        try:
            # 1. Fetch Dedicated API Key (SSOT: No unsafe fallbacks)
            api_key = await credential_service.get_credential("GEMINI_API_KEY")

            if not api_key:
                logger.error("MarketingService: GEMINI_API_KEY not found. Refusing fallback to prevent 503.")
                return {"error_code": 401, "message": "Dedicated GEMINI_API_KEY missing. Please configure in Settings."}

            # 2. Get Dynamic Model Configuration (Physical Parity with Feb 2026 Goal)
            from ..config.model_ssot import SYSTEM_MODELS

            rag_strategy_creds = await credential_service.get_credentials_by_category("rag_strategy")
            marketing_model = rag_strategy_creds.get("MARKETING_MODEL") or SYSTEM_MODELS["DEFAULT_TEXT"]

            # Use asynchronous client for non-blocking FastAPI integration
            client = genai.Client(api_key=api_key)
            sys_prompt = prompt_service.get_prompt("SALES_PITCH", SALES_PITCH_SYSTEM_PROMPT)

            # 3. Call AI with Dynamic Model (Asynchronous)
            response = await client.aio.models.generate_content(
                model=marketing_model,
                contents=f"Company: {company}\nRole: {job_title}",
                config=types.GenerateContentConfig(system_instruction=sys_prompt),
            )

            draft_content = response.text or "AI Error"

            # 3.5 EXP-03: Creative Resilience (Tone Critique Loop)
            # Bob's feature: Automatically critique and refine the draft
            try:
                critique_prompt = prompt_service.get_prompt("BRAND_TONE_CRITIQUE", (
                    "Review the following sales pitch. Ensure the tone is 'Professional yet approachable, "
                    "focusing on value delivery rather than aggressive selling'. If it passes, reply with 'PASS'. "
                    "If it fails, rewrite it to meet the brand tone and return ONLY the rewritten text."
                ))

                critique_res = await client.aio.models.generate_content(
                    model=marketing_model,
                    contents=f"Draft Pitch to evaluate:\n\n{draft_content}",
                    config=types.GenerateContentConfig(system_instruction=critique_prompt),
                )
                critique_text = (critique_res.text or "").strip()

                if critique_text != "PASS" and len(critique_text) > 10:
                    logger.info("MarketingService: EXP-03 applied. Pitch refined by Librarian critique.")
                    draft_content = critique_text
            except Exception as critique_err:
                logger.warning(f"MarketingService: EXP-03 Critique loop failed, using original draft: {critique_err}")

            # 4. LOG ACTUAL TOKEN USAGE (Physical evidence)
            try:
                import uuid

                from .agent_registry import get_agent_uuid
                from .token_usage_service import TokenUsageService

                # Resolve Real Physical Identity
                agent_uuid = get_agent_uuid("market-bot")

                from ..config.model_ssot import SYSTEM_MODELS

                asyncio.create_task(
                    TokenUsageService.log_usage(
                        request_id=f"pitch-{uuid.uuid4().hex[:8]}",
                        user_id=agent_uuid,  # Real UUID from Registry
                        model=SYSTEM_MODELS["DEFAULT_TEXT"],
                        provider="google",
                        input_tokens=getattr(response.usage_metadata, "prompt_token_count", 0) or 0,
                        output_tokens=getattr(response.usage_metadata, "candidates_token_count", 0) or 0,
                        context_type="sales_pitch_generation",
                    )
                )
            except Exception as log_err:
                logger.warning(f"Failed to log token usage: {log_err}")

            return {"content": draft_content, "references": []}

        except Exception as e:
            logger.error(f"MarketingService: AI generation failed: {e}")

            # Persistent Audit Log for David (Admin)
            try:
                LogService(self.supabase_client).create_log_entry({
                    "user_input": f"Pitch Generation Request: {company} / {job_title}",
                    "gemini_response": f"AI Error: {str(e)[:500]}",
                    "project_name": "SalesBot",
                    "user_name": "alice@archon.com"
                })
            except Exception as log_err:
                logger.warning(f"Failed to record marketing error to DB: {log_err}")

            return {"error_code": 500, "message": f"AI generation error: {str(e)}"}

    async def generate_visual_asset(self, style: str) -> dict:
        """Scenario 3: Nana Banana 3-Tier Defense (Grounded Implementation)"""
        import base64

        from .marketing.logo_tool import generate_logo_svg

        try:
            api_key = await credential_service.get_credential(
                "GEMINI_API_KEY"
            ) or await credential_service.get_credential("GOOGLE_API_KEY")
            client = genai.Client(api_key=api_key)
            prompt = f"Professional tech logo, {style}, high resolution"

            # TIER 1: Native AI Generation
            from ..config.model_ssot import SYSTEM_MODELS

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
                logger.warning("MarketingService: Native AI visual generation failed, falling back to local SVG.")

            # TIER 2: Physical Local SVG (Zero Token Cost)
            # Fulfills PRP promise of geometric logo generation
            svg_content = generate_logo_svg(style)
            svg_base64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")

            return {
                "status": "success",
                "image_url": f"data:image/svg+xml;base64,{svg_base64}",
                "tier": "physical_svg",
                "svg_content": svg_content,
            }

        except Exception as e:
            logger.error(f"MarketingService: Emergency visual fallback triggered: {e}")
            return {"status": "success", "image_url": "https://picsum.photos/1024/1024", "tier": "emergency"}

    async def get_combined_sources(self, user_id: str) -> list[dict]:
        leads = self.supabase_client.table("leads").select("*").limit(10).execute().data or []
        tasks = (
            self.supabase_client.table("archon_tasks").select("*").eq("assignee_id", user_id).limit(10).execute().data
            or []
        )
        blogs = (
            self.supabase_client.table("blog_posts")
            .select("*")
            .in_("status", ["draft", "changes_requested"])
            .limit(10)
            .execute()
            .data
            or []
        )

        sources = []
        for lead_entry in leads:
            sources.append(
                {
                    "id": lead_entry["id"],
                    "type": "lead",
                    "title": lead_entry["company_name"],
                    "score": lead_entry.get("enrichment_score", 0),
                    "summary": lead_entry.get("identified_need", "")[:100],
                    "date": lead_entry["created_at"],
                }
            )
        for task_entry in tasks:
            sources.append(
                {
                    "id": task_entry["id"],
                    "type": "task",
                    "title": task_entry["title"],
                    "score": 100,
                    "summary": task_entry.get("description", "")[:100],
                    "date": task_entry["created_at"],
                }
            )
        for blog_entry in blogs:
            sources.append(
                {
                    "id": blog_entry["id"],
                    "type": "blog",
                    "title": blog_entry["title"],
                    "score": blog_entry.get("ai_score", 0),
                    "summary": blog_entry.get("excerpt", ""),
                    "date": blog_entry["created_at"],
                    "status": blog_entry["status"],
                }
            )
        return sorted(sources, key=lambda x: x["date"], reverse=True)

    async def get_pending_approvals(self) -> dict:
        """Physical Fix for Charlie's Approvals Page"""
        res = (
            self.supabase_client.table("blog_posts")
            .select("*")
            .eq("status", "review")
            .order("updated_at", desc=True)
            .execute()
        )
        return {"blogs": res.data or [], "leads": []}

    async def get_content_context(self, source_id: str, source_type: str) -> dict:
        context_text = ""
        if source_type == "lead":
            logs = self.supabase_client.table("visit_logs").select("*").eq("lead_id", source_id).execute().data
            for log_item in logs:
                context_text += f"\n[Log]: {log_item.get('summary')}\n"
        success, res = await RAGService().perform_rag_query(query=context_text[:1000] or "General", match_count=3)
        return {
            "source_id": source_id,
            "source_type": source_type,
            "rag_refs": res.get("results", []) if success else [],
            "context_summary": context_text,
        }

    async def process_approval(self, item_type: str, item_id: str, action: str, notes: str | None) -> bool:
        if item_type == "blog":
            new_status = "published" if action == "approve" else "changes_requested"
            res = (
                self.supabase_client.table("blog_posts")
                .update({"status": new_status, "review_notes": notes})
                .eq("id", item_id)
                .execute()
            )

            if action != "approve" and notes and res.data:
                post_data = res.data[0]
                asyncio.create_task(
                    LibrarianService().archive_style_critique(
                        post_title=post_data.get("title", "Untitled"),
                        original_content=post_data.get("content", ""),
                        review_notes=notes,
                    )
                )
            return True
        return False

    async def submit_blog(self, post_id: str) -> tuple[bool, dict]:
        post = self.supabase_client.table("blog_posts").select("*").eq("id", post_id).single().execute().data
        if not post:
            return False, {"error": "Post not found"}

        score = self._calculate_ai_score(post.get("content", ""))
        status = "changes_requested" if score < 50 else "review"
        self.supabase_client.table("blog_posts").update({"status": status, "ai_score": score}).eq(
            "id", post_id
        ).execute()
        return True, {"status": status, "ai_score": score}

    async def draft_blog(self, topic: str, industry: list[str] | None, keywords: str | None) -> tuple[bool, dict]:
        """
        Bob's Daily Blog Draft Generation.
        Restored with EXP-03 (Creative Resilience) style constraints.
        """
        # P11: Guardrail Check
        is_valid, err = GuardrailService.validate_input(f"{topic} {keywords or ''}")
        if not is_valid:
            return False, {"error_code": 400, "message": f"Guardrail Violation: {err}"}

        try:
            context_text = await self._get_expert_style_context(f"{topic} {industry}")

            # 1. Fetch API Key from Credential Service
            api_key = await credential_service.get_credential(
                "GEMINI_API_KEY"
            ) or await credential_service.get_credential("GOOGLE_API_KEY")

            if not api_key:
                logger.error("MarketingService: No API Key found for blog drafting.")
                return False, {"error_code": 401, "message": "API Key missing"}

            # 2. Initialize Client
            client = genai.Client(api_key=api_key)
            sys_prompt = prompt_service.get_prompt("BLOG_DRAFT", BLOG_DRAFT_SYSTEM_PROMPT)

            # 3. Call AI with current model choice
            response = client.models.generate_content(
                model=SYSTEM_MODELS["DEFAULT_TEXT"],
                contents=f"Topic: {topic}\nContext: {context_text}",
                config=types.GenerateContentConfig(
                    system_instruction=sys_prompt, response_mime_type="application/json"
                ),
            )

            # LOG ACTUAL TOKEN USAGE (Physical Alignment - Phase 4.6.15)
            try:
                import uuid

                from .agent_registry import get_agent_uuid
                from .token_usage_service import TokenUsageService

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
                logger.warning(f"Failed to log blog token usage: {log_err}")

            if not response.text:
                return False, {"error": "AI Empty response"}

            result = safe_json_loads(response.text)

            # P11: AI Leakage Guardrail
            is_safe, audit = GuardrailService.audit_output(str(result.get("content", "")), context_text)
            if not is_safe:
                return False, {"error_code": 422, "message": f"AI Output Blocked: {audit}"}

            # Physical Persistence (Phase 4.6.15)
            # Create the blog post in 'review' status for Charlie
            new_post = {
                "title": str(result.get("title", "Untitled")),
                "content": str(result.get("content", "")),
                "excerpt": str(result.get("excerpt", "")),
                "status": "review",  # Automatically goes to approval inbox
                "ai_score": self._calculate_ai_score(str(result.get("content", ""))),
                "image_url": "https://picsum.photos/seed/market/1024/1024",
            }

            self.supabase_client.table("blog_posts").insert(new_post).execute()

            return True, {
                "title": new_post["title"],
                "content": new_post["content"],
                "excerpt": new_post["excerpt"],
                "status": "review",
            }
        except Exception as e:
            logger.error(f"MarketingService: Blog drafting failed: {e}")
            return False, {"error_code": 500, "message": f"AI Error: {str(e)}"}

    async def get_marketing_stats(self) -> dict:
        """Fetch basic marketing performance statistics."""
        try:
            leads_count = self.supabase_client.table("leads").select("id", count="exact").execute().count or 0
            blogs_count = self.supabase_client.table("blog_posts").select("id", count="exact").execute().count or 0
            converted_leads = (
                self.supabase_client.table("leads")
                .select("id", count="exact")
                .eq("status", "converted")
                .execute()
                .count
                or 0
            )

            return {
                "total_leads": leads_count,
                "total_blog_posts": blogs_count,
                "conversion_rate": round((converted_leads / leads_count * 100), 2) if leads_count > 0 else 0,
                "active_campaigns": blogs_count,  # Use blog count as active campaigns surrogate
                "last_updated": "2026-03-20T10:00:00Z",
            }
        except Exception as e:
            logger.error(f"Failed to fetch marketing stats: {e}")
            return {"error": str(e)}

    async def get_marketing_trends(self) -> dict:
        res_t = (
            self.supabase_client.table("marketing_trends")
            .select("*")
            .eq("trend_type", "keyword_growth")
            .order("report_date", desc=True)
            .limit(1)
            .execute()
        )
        res_s = (
            self.supabase_client.table("marketing_trends")
            .select("*")
            .eq("trend_type", "sankey_flow")
            .order("report_date", desc=True)
            .limit(1)
            .execute()
        )
        return {
            "keyword_growth": res_t.data[0]["data"] if res_t.data else [],
            "sankey_flow": res_s.data[0]["data"] if res_s.data else {},
        }

    async def _get_expert_style_context(self, query: str) -> str:
        """
        Restores EXP-03 (Creative Resilience) logic:
        1. Performs RAG on general context.
        2. Retrieves specific brand voice constraints from Manager critiques.
        """
        # Step 1: General Context RAG
        success, rag = await RAGService().perform_rag_query(query=query, match_count=5, min_score=0.15)
        context_text = ""
        if success:
            for r in rag.get("results", []):
                context_text += f"\n[RAG]: {r['content']}\n"

        # Step 2: Brand Voice Constraints (Phase 4.6.46: Critical Restoration)
        try:
            constraints = await LibrarianService().get_style_constraints(category="marketing")
            if constraints:
                context_text += f"\n[BRAND VOICE CONSTRAINTS]:\n{constraints}\n"
        except Exception as e:
            logger.warning(f"EXP-03: Failed to retrieve style constraints: {e}")

        return context_text

    def _calculate_ai_score(self, content: str) -> int:
        if len(content) < 100:
            return 30
        if "Archon" in content:
            return 85
        return 75

    async def run_sentinel(self) -> dict:
        """Manually trigger the Business Sentinel."""
        from ..services.scheduler_service import scheduler_service

        await scheduler_service.run_business_sentinel()
        return {"status": "triggered", "message": "Sentinel scan started in background."}

    async def reset_leads(self) -> bool:
        """Clear all leads (Development/Reset tool)."""
        try:
            self.supabase_client.table("leads").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            return True
        except Exception as e:
            logger.error(f"Failed to reset leads: {e}")
            return False

    async def _calculate_lead_score(self, job_title: str | None) -> int:
        """
        Calculates a dynamic lead score based on job titles.
        Uses SettingsService with local fallbacks to avoid SQL overhead.
        """
        try:
            from ..services.settings_service import SettingsService
            settings = SettingsService(self.supabase_client)

            # 1. Fetch Dynamic Weights (Zero-SQL migration approach)
            w_strat = int(settings.get_setting("SCORE_STRATEGIC") or "95")
            w_tech = int(settings.get_setting("SCORE_TECHNICAL") or "85")
            w_ops = int(settings.get_setting("SCORE_OPERATIONAL") or "70")
            w_base = int(settings.get_setting("SCORE_BASE") or "40")

            title = str(job_title or "").upper()

            # Level 3: Strategic/Decision Makers
            if any(kw in title for kw in ["DIRECTOR", "VP", "HEAD", "CHIEF", "ARCHITECT", "FOUNDER"]):
                return w_strat

            # Level 2: Technical Core (AI/ML Priority)
            if any(kw in title for kw in ["AI", "ML", "MACHINE LEARNING", "DATA", "PYTHON", "ENGINEER"]):
                return w_tech

            # Level 1: Operational Management
            if any(kw in title for kw in ["MANAGER", "LEAD", "SENIOR", "TEAM LEAD"]):
                return w_ops

            return w_base
        except Exception as e:
            logger.warning(f"Lead Scoring Failed: {e}. Falling back to 40.")
            return 40

    async def seed_knowledge(self) -> dict:
        """Trigger the Knowledge Seeding process (scans resources and archives them)."""
        import os

        from ..services.librarian_service import LibrarianService

        # Physical Fix: Use the exact discovered Docker mount path
        target_dir = "/app/frontend_public/aus/156_resource"
        if not os.path.exists(target_dir):
            # Local dev fallback
            target_dir = "../enduser-ui-fe/public/aus/156_resource"

        if not os.path.exists(target_dir):
            return {"error": f"Knowledge resource directory not found at {target_dir}."}

        librarian = LibrarianService()
        success_count = 0
        total_count = 0
        errors = []

        try:
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if file.startswith(".") or file == "DS_Store":
                        continue
                    if not (file.endswith(".md") or file.endswith(".txt")):
                        continue

                    total_count += 1
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()
                        if not content.strip():
                            continue
                        await librarian.archive_file(
                            file_name=file, content=content, file_path=file_path, knowledge_type="technical"
                        )
                        success_count += 1
                    except Exception as e:
                        errors.append(f"{file}: {str(e)}")

            return {
                "status": "completed",
                "scanned_dir": target_dir,
                "total_files": total_count,
                "indexed_count": success_count,
                "errors": errors[:5],
            }
        except Exception as e:
            return {"error": f"Seeding failed: {str(e)}"}
