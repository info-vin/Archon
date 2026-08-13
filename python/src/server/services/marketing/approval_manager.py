import asyncio
from typing import Any

from google import genai

from ...config.model_ssot import SYSTEM_MODELS
from ...repositories.base_repository import BaseRepository
from ..librarian_service import LibrarianService
from ..prompt_service import prompt_service
from .content_handler import get_logger

logger = get_logger(__name__)




class ApprovalManager(BaseRepository):
    """Handles content approval workflows and feedback suggestion generation."""

    def __init__(self, supabase_client: Any) -> None:
        super().__init__(supabase_client)

    async def process_approval(self, item_type: str, item_id: str, action: str, notes: str | None) -> bool:
        if item_type == "blog":
            new_status = "published" if action == "approve" else "changes_requested"
            success, res = self.execute_query(
                self.supabase_client.table("blog_posts") # 合法
                .update({"status": new_status, "review_notes": notes})
                .eq("id", item_id),
                "Update blog status"
            )
            if action != "approve" and notes and success and res.get("data"):
                try:
                    post_data = res["data"][0]
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
        success, res = self.execute_query(
            self.supabase_client.table("blog_posts") # 合法
            .select("*")
            .eq("status", "review")
            .order("updated_at", desc=True),
            "Get pending approvals"
        )
        return {"blogs": res.get("data", []) if success else [], "leads": []}

    async def generate_reject_suggestion(self, item_type: str, item_id: str) -> dict:
        if item_type != "blog":
            return {"notes": "Content type not supported for AI rejection."}

        success, res = self.execute_query(self.supabase_client.table("blog_posts").select("*").eq("id", item_id), "Get blog post") # 合法
        post = res.get("data", [None])[0] if success and res.get("data") else None
        if not post:
            return {"notes": "Item not found."}

        from ..credential_service import credential_service
        api_key = await credential_service.get_credential("GEMINI_API_KEY")
        if not api_key:
            return {"notes": "Cannot generate AI reason: AI provider missing."}

        client = genai.Client(api_key=api_key)

        prompt_template = prompt_service.get_prompt("REJECT_SUGGESTION")
        prompt = prompt_template.format(content=post.get("content", ""))

        try:
            response = await client.aio.models.generate_content(model=SYSTEM_MODELS["DEFAULT_TEXT"], contents=prompt)
            return {"notes": response.text.strip() if response.text else "Failed to generate reason."}
        except Exception as e:
            return {"notes": f"AI Generation Failed: {str(e)}"}
