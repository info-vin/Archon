from typing import Any, cast

from ..repositories.base_repository import BaseRepository


class PagesService(BaseRepository):
    def __init__(self) -> None:
        super().__init__()

    async def list_pages(self, source_id: str, section: str | None = None) -> list[dict[str, Any]]:
        query = self.supabase_client.table("archon_crawled_pages").select("id, url, section_title, section_order, word_count, char_count, chunk_count").eq("source_id", source_id)
        if section:
            query = query.eq("section_title", section)
        query = query.order("section_order").order("created_at")

        success, res = self.execute_query(query, f"Failed to list pages for source_id={source_id}", require_data=False)
        return cast(list[dict[str, Any]], res.get("data", []) if success else [])

    async def get_page_by_url(self, url: str) -> dict[str, Any] | None:
        query = self.supabase_client.table("archon_crawled_pages").select("*").eq("url", url)
        success, res = self.execute_query(query, f"Failed to get page by URL {url}")
        if not success:
            return None
        data = res.get("data", [])
        return cast(dict[str, Any], data[0] if data else None)

    async def get_page_by_id(self, page_id: str) -> dict[str, Any] | None:
        query = self.supabase_client.table("archon_crawled_pages").select("*").eq("id", page_id)
        success, res = self.execute_query(query, f"Failed to get page by ID {page_id}")
        if not success:
            return None
        data = res.get("data", [])
        return cast(dict[str, Any], data[0] if data else None)

pages_service = PagesService()
