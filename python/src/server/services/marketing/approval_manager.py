import asyncio
from typing import Any

from google import genai

from ...config.model_ssot import SYSTEM_MODELS
from ..librarian_service import LibrarianService
from ..prompt_service import prompt_service
from .content_handler import get_logger

logger = get_logger(__name__)


class ApprovalManager:
    """Handles content approval workflows and feedback suggestion generation."""

    def __init__(self, supabase_client: Any):
        self.supabase_client = supabase_client

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
                try:
                    post_data = res.data[0]
                    asyncio.create_task(
                        LibrarianService().archive_style_critique(
                            post_title=post_data.get("title", "Untitled"),
                            original_content=post_data.get("content", ""),
                            review_notes=notes,
                        )
                    )
                except Exception as e:
                    logger.error(f"ApprovalManager: Failed to archive style critique for blog {item_id}: {e}")
            return True
        return False

    async def get_pending_approvals(self) -> dict:
        res = (
            self.supabase_client.table("blog_posts")
            .select("*")
            .eq("status", "review")
            .order("updated_at", desc=True)
            .execute()
        )
        return {"blogs": res.data or [], "leads": []}

    async def generate_reject_suggestion(self, item_type: str, item_id: str) -> dict:
        if item_type != "blog":
            return {"notes": "Content type not supported for AI rejection."}

        res = self.supabase_client.table("blog_posts").select("*").eq("id", item_id).execute()
        post = res.data[0] if res.data else None
        if not post:
            return {"notes": "Item not found."}

        from ..credential_service import credential_service
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
            response = await client.aio.models.generate_content(model=SYSTEM_MODELS["DEFAULT_TEXT"], contents=prompt)
            return {"notes": response.text.strip() if response.text else "Failed to generate reason."}
        except Exception as e:
            return {"notes": f"AI Generation Failed: {str(e)}"}
