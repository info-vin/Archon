import uuid

from ...config.logfire_config import get_logger
from ...repositories.knowledge_repository import KnowledgeRepository
from ...services.embeddings.embedding_service import create_embedding
from ...services.source_management_service import update_source_info
from ...utils import get_supabase_client
from ..shared_constants import AgentUUIDs
from .file_archiver import FileArchiver

logger = get_logger(__name__)

class WebArchiver:
    def __init__(self, supabase=None, repo=None, file_archiver=None):
        self.supabase = supabase or get_supabase_client()
        self.repo = repo or KnowledgeRepository(self.supabase)
        self.file_archiver = file_archiver or FileArchiver(self.supabase, self.repo)

    async def archive_any_url(self, url: str, user_role: str = "member", depth: int = 0, max_depth: int = 1) -> str:
        """
        New (Phase 4.7): Dynamically crawls ANY authorized URL and indexes it.
        Supports HTML and recursive Sitemap ingestion.
        """
        if depth > max_depth:
            logger.info(f"Librarian: Max depth reached ({max_depth}) | skipping {url}")
            return "depth-limit-reached"

        try:
            from ..crawler_service import CrawlerService
            from ..threading_service import ProcessingMode, get_threading_service

            crawler = CrawlerService(user_role=user_role)
            threading_service = get_threading_service()

            # 1. Fetch and Analyze
            result = await crawler.fetch_and_analyze(url)
            if result.get("status") == "error":
                raise Exception(result.get("message", "Crawler failed."))

            # 2. Route based on Type (Page vs Sitemap)
            if result.get("type") == "sitemap":
                links = result.get("discovered_links", [])
                logger.info(f"Librarian: Processing Sitemap | discovered={len(links)} links | depth={depth}")

                # Use ThreadingService to process links with rate limiting protection
                # We limit to first 5 links to avoid runaway costs/load
                target_links = links[:5]

                async def process_link(link: str):
                    if not link.endswith(".xml"):
                        return await self.archive_any_url(
                            link, user_role=user_role, depth=depth + 1, max_depth=max_depth
                        )
                    return None

                await threading_service.batch_process(
                    items=target_links, process_func=process_link, mode=ProcessingMode.NETWORK_BOUND
                )

                return f"batch-processed-{len(target_links)}-items"

            # 3. Standard Page Ingestion
            content = result["content"]
            title = result["title"]

            source_id = await self.file_archiver.archive_file(
                file_name=f"External: {title[:50]}", content=content, file_path=url, knowledge_type="external_knowledge"
            )

            logger.info(f"Librarian: Successfully ingested external URL | url={url} | id={source_id}")
            return source_id

        except Exception as e:
            logger.error(f"Librarian: Failed to archive URL {url} | error={str(e)}")
            return ""

    async def archive_web_research(self, query: str, content: str, references: list[str]) -> str:
        """
        Archives web research results into the knowledge base.
        """
        try:
            # 1. Generate unique Source ID
            safe_query = "".join(c for c in query if c.isalnum())[:20].lower()
            unique_suffix = str(uuid.uuid4())[:8]
            source_id = f"web-{safe_query}-{unique_suffix}"

            # 2. Prepare Metadata
            title = f"Research: {query}"
            summary = f"Web research results for: {query}"
            word_count = len(content.split())
            tags = ["web_research", "external_knowledge", "google_grounding"]

            logger.info(f"Librarian: Archiving web research | source_id={source_id} | query={query}")

            # 3. Create Source Info
            await update_source_info(
                client=self.supabase,
                source_id=source_id,
                summary=summary,
                word_count=word_count,
                content=content,
                knowledge_type="web_research",
                tags=tags,
                source_display_name=title,
            )

            # 4. Insert Content & Embedding
            try:
                embedding_vector = await create_embedding(content[:8000])
            except Exception as e:
                logger.error(f"Librarian: Failed to generate embedding for research {source_id}: {e}")
                embedding_vector = None

            page_data = {
                "source_id": source_id,
                "url": f"generated://research/{source_id}",
                "chunk_number": 0,
                "content": content,
                "embedding": embedding_vector,
                "metadata": {
                    "knowledge_type": "web_research",
                    "tags": tags,
                    "query": query,
                    "references": references,
                    "title": title,
                },
            }

            self.repo.insert_crawled_page(page_data)

            # 5. Record version
            self.repo.insert_document_version(
                document_id=source_id,
                field_name="web_research",
                change_summary=f"Archived research for: {query}",
                content={"source_id": source_id, "query": query, "refs_count": len(references)},
                created_by=AgentUUIDs.LIBRARIAN,
            )

            return source_id

        except Exception as e:
            logger.error(f"Librarian: Failed to archive web research | error={str(e)}")
            return ""
