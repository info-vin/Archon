# python/src/server/services/blog_service.py

from typing import Any

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

class BlogService:
    """Service for handling blog post operations."""

    def __init__(self):
        self.supabase = get_supabase_client()

    async def list_posts(self) -> tuple[bool, dict[str, Any]]:
        """Retrieve a list of all blog posts."""
        try:
            response = self.supabase.table("blog_posts").select("id, title, excerpt, author_name, publish_date, image_url").order("publish_date", desc=True).execute()
            if response.data is None:
                return False, {"error": "Failed to fetch blog posts."}
            return True, {"posts": response.data}
        except Exception as e:
            logger.error(f"Error listing blog posts: {e}", exc_info=True)
            return False, {"error": str(e)}

    async def get_post(self, post_id: str) -> tuple[bool, dict[str, Any]]:
        """Retrieve a single blog post by its ID."""
        try:
            response = self.supabase.table("blog_posts").select("*").eq("id", post_id).single().execute()
            if response.data is None:
                return False, {"error": "Post not found."}
            return True, {"post": response.data}
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {e}", exc_info=True)
            return False, {"error": str(e)}

    async def create_post(self, post_data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Create a new blog post."""
        try:
            response = self.supabase.table("blog_posts").insert(post_data).select().single().execute()
            if response.data is None:
                return False, {"error": "Failed to create post."}
            return True, {"post": response.data}
        except Exception as e:
            logger.error(f"Error creating post: {e}", exc_info=True)
            return False, {"error": str(e)}

    async def update_post(self, post_id: str, update_data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Update an existing blog post."""
        try:
            response = self.supabase.table("blog_posts").update(update_data).eq("id", post_id).select().single().execute()
            if response.data is None:
                return False, {"error": "Failed to update post or post not found."}
            return True, {"post": response.data}
        except Exception as e:
            logger.error(f"Error updating post {post_id}: {e}", exc_info=True)
            return False, {"error": str(e)}

    async def delete_post(self, post_id: str) -> tuple[bool, dict[str, Any]]:
        """Delete a blog post."""
        try:
            response = self.supabase.table("blog_posts").delete().eq("id", post_id).execute()
            # Delete doesn't return data, so we check for other indicators of success
            if getattr(response, 'error', None):
                 raise Exception(response.error.message)
            return True, {"message": "Post deleted successfully."}
        except Exception as e:
            logger.error(f"Error deleting post {post_id}: {e}", exc_info=True)
            return False, {"error": str(e)}
