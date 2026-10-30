from typing import Any, NotRequired, TypedDict, cast

from supabase import Client

from ..repositories.base_repository import BaseRepository


class PageSummaryDTO(TypedDict):
    id: NotRequired[str | int]
    url: NotRequired[str]
    section_title: NotRequired[str | None]
    section_order: NotRequired[int]
    word_count: NotRequired[int]
    char_count: NotRequired[int]
    chunk_count: NotRequired[int]


class PageDTO(TypedDict):
    id: NotRequired[str | int]
    url: NotRequired[str]
    chunk_number: NotRequired[int]
    content: NotRequired[str]
    metadata: NotRequired[dict[str, Any]]
    source_id: NotRequired[str]
    embedding: NotRequired[list[float] | None]
    content_search_vector: NotRequired[str | None]
    created_at: NotRequired[str]
    title: NotRequired[str | None]
    section_title: NotRequired[str | None]
    section_order: NotRequired[int]
    word_count: NotRequired[int]
    char_count: NotRequired[int]
    chunk_count: NotRequired[int]
    full_content: NotRequired[str]


class PagesService(BaseRepository):
    def __init__(self, supabase_client: Client | None = None) -> None:
        super().__init__(supabase_client)

    async def list_pages(self, source_id: str, section: str | None = None) -> list[PageSummaryDTO]:
        query = self.supabase_client.table("archon_crawled_pages").select("id, url, section_title, section_order, word_count, char_count, chunk_count").eq("source_id", source_id)
        if section:
            query = query.eq("section_title", section)
        query = query.order("section_order").order("created_at")

        success, res = await self.execute_query_async(query, f"Failed to list pages for source_id={source_id}", require_data=False)
        if not success or not isinstance(res, dict):
            return []
        data = res.get("data")
        if not isinstance(data, list):
            return []
        return [cast(PageSummaryDTO, item) for item in data if isinstance(item, dict)]

    async def get_page_by_url(self, url: str) -> PageDTO | None:
        query = self.supabase_client.table("archon_crawled_pages").select("*").eq("url", url)
        success, res = await self.execute_query_async(query, f"Failed to get page by URL {url}")
        if not success or not isinstance(res, dict):
            return None
        data = res.get("data")
        if not isinstance(data, list) or not data:
            return None
        first_item = data[0]
        if not isinstance(first_item, dict):
            return None
        return cast(PageDTO, first_item)

    async def get_page_by_id(self, page_id: str) -> PageDTO | None:
        query = self.supabase_client.table("archon_crawled_pages").select("*").eq("id", page_id)
        success, res = await self.execute_query_async(query, f"Failed to get page by ID {page_id}")
        if not success or not isinstance(res, dict):
            return None
        data = res.get("data")
        if not isinstance(data, list) or not data:
            return None
        first_item = data[0]
        if not isinstance(first_item, dict):
            return None
        return cast(PageDTO, first_item)


pages_service = PagesService()
