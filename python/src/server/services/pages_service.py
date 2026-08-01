from typing import Any, NotRequired, TypedDict, cast

from ..repositories.base_repository import BaseRepository


class PageSummaryDTO(TypedDict):
    id: NotRequired[str]
    url: NotRequired[str]
    section_title: NotRequired[str | None]
    section_order: NotRequired[int]
    word_count: NotRequired[int]
    char_count: NotRequired[int]
    chunk_count: NotRequired[int]


class PageDTO(TypedDict):
    id: NotRequired[str]
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
    def __init__(self) -> None:
        super().__init__()

    async def list_pages(self, source_id: str, section: str | None = None) -> list[PageSummaryDTO]:
        query = self.supabase_client.table("archon_crawled_pages").select("id, url, section_title, section_order, word_count, char_count, chunk_count").eq("source_id", source_id)
        if section:
            query = query.eq("section_title", section)
        query = query.order("section_order").order("created_at")

        success, res = self.execute_query(query, f"Failed to list pages for source_id={source_id}", require_data=False)
        return cast(list[PageSummaryDTO], res.get("data", []) if success else [])

    async def get_page_by_url(self, url: str) -> PageDTO | None:
        query = self.supabase_client.table("archon_crawled_pages").select("*").eq("url", url)
        success, res = self.execute_query(query, f"Failed to get page by URL {url}")
        if not success:
            return None
        data = res.get("data", [])
        return cast(PageDTO, data[0] if data else None)

    async def get_page_by_id(self, page_id: str) -> PageDTO | None:
        query = self.supabase_client.table("archon_crawled_pages").select("*").eq("id", page_id)
        success, res = self.execute_query(query, f"Failed to get page by ID {page_id}")
        if not success:
            return None
        data = res.get("data", [])
        return cast(PageDTO, data[0] if data else None)

pages_service = PagesService()
