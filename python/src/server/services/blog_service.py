# python/src/server/services/blog_service.py

from typing import Any

from src.server.repositories.base_repository import BaseRepository

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


class BlogService(BaseRepository):
    """Service for handling blog post operations."""

    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client or get_supabase_client())

    async def list_posts(self) -> tuple[bool, dict[str, Any]]:
        """Retrieve a list of all blog posts."""


        success, res = self.execute_query(self.supabase_client.table("blog_posts").select("*").order("publish_date", desc=True), "Failed to fetch blog posts") # 合法
        if success:
            return True, {"posts": res.get("data", [])}
        return False, res

    async def get_post(self, post_id: str) -> tuple[bool, dict[str, Any]]:
        """Retrieve a single blog post by its ID."""

        query = self.supabase_client.table("blog_posts").select("*").eq("id", post_id) # 合法
        success, res = self.execute_query(query, f"Error getting post {post_id}", require_data=True)
        if success:
            data = res.get("data", [])
            post_data = data[0] if isinstance(data, list) and data else (data if data else {})
            return True, {"post": post_data}
        return False, res

    async def create_post(self, post_data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Create a new blog post with AI-generated visual asset."""
        # P6: Smart Polish - Extract image and clean content
        post_data = self._clean_content_images(post_data)

        # Task 40.4: Automated Visual Generation (Nana Banana Integration)
        if not post_data.get("cover_image"):
            try:
                from src.server.services.marketing_service import MarketingService

                marketing_svc = MarketingService(self.supabase_client)
                title = post_data.get("title", "Modern Tech")
                # Request a visual asset matching the blog title style
                visual = await marketing_svc.generate_visual_asset(style=f"Cyberpunk Tech Logo for {title}")
                if visual.get("status") == "success":
                    post_data["cover_image"] = visual.get("image_url")
                    logger.info(f"BlogService: Automatically attached cover image (Tier: {visual.get('tier')})")
            except Exception as e:
                logger.warning(f"BlogService: Visual generation skipped due to error: {e}")


        success, res = self.execute_query(self.supabase_client.table("blog_posts").insert(post_data), "Error creating post") # 合法
        if success:
            data = res.get("data", [])
            return True, {"post": data[0] if isinstance(data, list) and data else data}
        return False, res

    async def update_post(self, post_id: str, update_data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Update an existing blog post."""
        # Phase 4.6.57: AI Correction Tracking
        if "content" in update_data:
            # Fetch old post to compare content
            old_post_success, old_post_res = await self.get_post(post_id)
            if old_post_success and "post" in old_post_res:
                old_content = old_post_res["post"].get("content", "")
                new_content = update_data["content"]

                # Calculate diff if content changed
                if old_content and old_content != new_content:
                    import difflib

                    s = difflib.SequenceMatcher(None, old_content, new_content)
                    correction_rate = round((1.0 - s.ratio()) * 100, 2)

                    # Log AI_CORRECTION to archon_logs
                    log_data = {
                        "source": "blog_editor",
                        "level": "INFO",
                        "message": f"AI Content Correction: {correction_rate}% changed",
                        "type": "AI_CORRECTION",
                        "details": {
                            "post_id": post_id,
                            "correction_rate": correction_rate,
                            "old_length": len(old_content),
                            "new_length": len(new_content),
                        },
                    }
                    try:
                        self.execute_query(
                            self.supabase_client.table("archon_logs").insert(log_data),
                            "Log AI_CORRECTION"
                        )
                        logger.info(f"Logged AI_CORRECTION for post {post_id} with rate {correction_rate}%")
                    except Exception as e:
                        logger.error(f"Failed to log AI_CORRECTION: {e}")

            # P6: Smart Polish - Extract image and clean content
            update_data = self._clean_content_images(update_data)


        success, res = self.execute_query(self.supabase_client.table("blog_posts").update(update_data).eq("id", post_id), f"Error updating post {post_id}") # 合法
        if success:
            data = res.get("data", [])
            return True, {"post": data[0] if isinstance(data, list) and data else data}
        return False, res

    def _clean_content_images(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        P6 Implementation: Extracts image URL from Markdown syntax and strips it from content.
        Moves url to metadata 'image_url' field.
        """
        import re

        content = data.get("content", "")
        if not content:
            return data

        # Pattern: ![alt](url)
        match = re.search(r"!\[.*?\]\((.*?)\)", content)
        if match:
            # Move to image_url if not already explicitly set
            if not data.get("image_url"):
                data["image_url"] = match.group(1)
            # Remove from content
            data["content"] = re.sub(r"!\[.*?\]\((.*?)\)", "", content).strip()

        return data

    async def delete_post(self, post_id: str) -> tuple[bool, dict[str, Any]]:
        """Delete a blog post."""


        # execute_query with require_data=False for delete
        success, res = self.execute_query(self.supabase_client.table("blog_posts").delete().eq("id", post_id), f"Error deleting post {post_id}", require_data=False) # 合法
        if success:
            return True, {"message": "Post deleted successfully."}
        return False, res
