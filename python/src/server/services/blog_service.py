# python/src/server/services/blog_service.py

from typing import Any

from src.server.repositories.base_repository import BaseRepository

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

class BlogService(BaseRepository):
    """Service for handling blog post operations."""

    def __init__(self, supabase_client=None):
        super().__init__(supabase_client or get_supabase_client())

    async def list_posts(self) -> tuple[bool, dict[str, Any]]:
        """Retrieve a list of all blog posts."""
        def _query():
            return self.supabase_client.table("blog_posts").select("*").order("publish_date", desc=True).execute()

        success, res = self.execute_query(_query, "Failed to fetch blog posts")
        if success:
            return True, {"posts": res.get("data", [])}
        return False, res

    async def get_post(self, post_id: str) -> tuple[bool, dict[str, Any]]:
        """Retrieve a single blog post by its ID."""
        def _query():
            return self.supabase_client.table("blog_posts").select("*").eq("id", post_id).single().execute()

        success, res = self.execute_query(_query, f"Error getting post {post_id}", require_data=True)
        if success:
            return True, {"post": res.get("data")}
        return False, res

    async def create_post(self, post_data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Create a new blog post."""
        def _query():
            return self.supabase_client.table("blog_posts").insert(post_data).execute()

        success, res = self.execute_query(_query, "Error creating post")
        if success:
            data = res.get("data", [])
            return True, {"post": data[0] if isinstance(data, list) and data else data}
        return False, res

    async def update_post(self, post_id: str, update_data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Update an existing blog post."""
        def _query():
            return self.supabase_client.table("blog_posts").update(update_data).eq("id", post_id).execute()

        success, res = self.execute_query(_query, f"Error updating post {post_id}")
        if success:
            data = res.get("data", [])
            return True, {"post": data[0] if isinstance(data, list) and data else data}
        return False, res

    async def delete_post(self, post_id: str) -> tuple[bool, dict[str, Any]]:
        """Delete a blog post."""
        def _query():
            return self.supabase_client.table("blog_posts").delete().eq("id", post_id).execute()

        # execute_query with require_data=False for delete
        success, res = self.execute_query(_query, f"Error deleting post {post_id}", require_data=False)
        if success:
            return True, {"message": "Post deleted successfully."}
        return False, res
