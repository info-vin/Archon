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

    def _map_to_page_dto(self, item: dict[str, Any]) -> PageDTO:
        meta_val = item.get("metadata")
        meta: dict[str, Any] = meta_val if isinstance(meta_val, dict) else {}
        content_val = item.get("content")
        content: str = content_val if isinstance(content_val, str) else ""
        return cast(
            PageDTO,
            {
                **item,
                "full_content": item.get("full_content") or content,
                "word_count": item.get("word_count") or len(content.split()),
                "char_count": item.get("char_count") or len(content),
                "chunk_count": item.get("chunk_count") or 1,
                "section_title": item.get("section_title") or meta.get("section_title") or item.get("title"),
                "section_order": item.get("section_order") or meta.get("section_order") or item.get("chunk_number", 0),
                "updated_at": item.get("updated_at") or item.get("created_at", ""),
            },
        )

    async def list_pages(self, source_id: str, section: str | None = None) -> list[PageSummaryDTO]:
        query = (
            self.supabase_client.table("archon_crawled_pages")
            .select("id, url, chunk_number, content, metadata, source_id, created_at, title")
            .eq("source_id", source_id)
            .order("chunk_number")
            .order("created_at")
        )

        success, res = await self.execute_query_async(query, f"Failed to list pages for source_id={source_id}", require_data=False)
        if not success or not isinstance(res, dict):
            return []
        data = res.get("data")
        if not isinstance(data, list):
            return []

        results: list[PageSummaryDTO] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            meta_val = item.get("metadata")
            meta: dict[str, Any] = meta_val if isinstance(meta_val, dict) else {}
            sec_title = item.get("section_title") or meta.get("section_title") or item.get("title")
            if section and sec_title != section:
                continue
            content_val = item.get("content")
            content: str = content_val if isinstance(content_val, str) else ""
            char_count = item.get("char_count") or len(content)
            word_count = item.get("word_count") or len(content.split())
            sec_order = item.get("section_order") or meta.get("section_order") or item.get("chunk_number", 0)

            results.append(
                cast(
                    PageSummaryDTO,
                    {
                        "id": item.get("id"),
                        "url": item.get("url", ""),
                        "section_title": sec_title,
                        "section_order": sec_order,
                        "word_count": word_count,
                        "char_count": char_count,
                        "chunk_count": item.get("chunk_count") or 1,
                    },
                )
            )
        return results

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
        return self._map_to_page_dto(first_item)

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
        return self._map_to_page_dto(first_item)


pages_service = PagesService()
